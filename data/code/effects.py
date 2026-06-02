"""
SYMBIOSE — effects.py v2
Système hybride probabiliste.

Effets discrets (maladie, pollinisateur) : probabilité modulée par les champs.
Effets flux (microbiome, fertilité) : injection directe dans les champs continus.

Philosophie : jamais bonus/malus directs sur les plantes.
  → flux → contrainte écologique → réponse biologique émergente.
"""

from __future__ import annotations
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from models import PlantInstance, Tile, EFFECT_REGISTRY, register_effect, RONDELLE_TYPES
from fields import _hash_noise, HERBIVORY_BASE, MORTALITY_RATE, climate_stress

if TYPE_CHECKING:
    from fields import EcoFields

# ---------------------------------------------------------------------------
# MUTATIONS
# ---------------------------------------------------------------------------

@dataclass
class AddRondelle:
    tile_id: str; variable: str; amount: int; source: str = ""
    def __repr__(self): return f"+{self.amount} {self.variable} [{self.source}]"

@dataclass
class RemoveRondelle:
    tile_id: str; variable: str; amount: int; source: str = ""
    def __repr__(self): return f"-{self.amount} {self.variable} [{self.source}]"

@dataclass
class ReduceHealth:
    plant: PlantInstance; amount: int; reason: str = ""
    def __repr__(self): return f"Santé {self.plant.name}@{self.plant.position} -{self.amount} [{self.reason}]"

@dataclass
class AddScore:
    player_id: str; axis: str; amount: int; source: str = ""
    def __repr__(self): return f"+{self.amount} {self.axis} [{self.source}]"

@dataclass
class InjectField:
    """Injection directe dans un champ continu."""
    tile_id: str; variable: str; amount: float
    row: int | None = None; col: int | None = None
    source: str = ""
    def __repr__(self):
        loc = f"@({self.row},{self.col})" if self.row is not None else "global"
        return f"~{self.amount:+.3f} {self.variable} {loc} [{self.source}]"

@dataclass
class PropagateDisease:
    source_plant: PlantInstance; target_plant: PlantInstance
    disease_name: str = "pathogène"
    probability: float = 1.0
    def __repr__(self):
        return (f"Propagation {self.disease_name} "
                f"{self.source_plant.name}→{self.target_plant.name} "
                f"p={self.probability:.2f}")

@dataclass
class Notification:
    message: str; severity: str = "info"; plant: PlantInstance | None = None
    def __repr__(self): return f"[{self.severity.upper()}] {self.message}"

Mutation = (AddRondelle | RemoveRondelle | ReduceHealth |
            AddScore | InjectField | PropagateDisease | Notification)

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _get_tile(game_state, tile_id):
    return next((t for t in game_state["tiles"] if t.tile_id == tile_id), None)

def _get_eco(game_state, tile_id):
    return game_state.get("eco", {}).get(tile_id)

def _alive_in_radius(tile, plant, radius):
    nearby = set(tile.plots_within_radius(*plant.position, radius))
    return [p for p in tile.plants
            if p is not plant and p.is_alive
            and (p.position in nearby or any(fp in nearby for fp in p.foliar_plots))]

def _clamp_rondelle(tile, variable, delta, max_val=3):
    current = tile.get_rondelle_count(variable)
    if delta > 0: return min(delta, max_val - current)
    return max(delta, -current)

# ---------------------------------------------------------------------------
# RÉSOLUTION PRINCIPALE
# ---------------------------------------------------------------------------

def resolve(effect: dict, plant: PlantInstance, tile: Tile,
            game_state: dict, trigger: str) -> list[Mutation]:
    mutations = []
    effect_type = effect.get("type", "")

    # Filtre temporel
    if effect_type == "permanent":
        if trigger != "weekly": return []
        if effect.get("trigger", "weekly") != "weekly": return []
    elif effect_type != trigger:
        return []

    # Callback complexe prioritaire
    stage_idx = plant.current_stage
    callback_name = (effect.get("callback") or
                     (plant.plant_class.growth_stages[stage_idx].callback
                      if stage_idx < len(plant.plant_class.growth_stages) else None))
    if callback_name and callback_name in EFFECT_REGISTRY:
        return EFFECT_REGISTRY[callback_name](effect, plant, tile, game_state)

    action = effect.get("action", "")
    eco = _get_eco(game_state, tile.tile_id)
    r, c = plant.position

    # --- inject_field : flux écologique direct ---
    if action == "inject_field":
        variable = effect["variable"]
        amount   = effect.get("amount", 0.0)
        cible    = effect.get("cible", "local")
        if cible == "local" and eco:
            # Enrichissement spatial (chantier B) : réparti sur l'empreinte
            # racinaire, pas sur le seul plot central. On répartit (share),
            # sans dupliquer la quantité totale.
            plots = [(rr, cc) for (rr, cc) in plant.root_plots
                     if 0 <= rr < eco.rows and 0 <= cc < eco.cols]
            if not plots:
                plots = [(r, c)]
            share = amount / len(plots)
            for rr, cc in plots:
                mutations.append(InjectField(tile.tile_id, variable, share, rr, cc,
                                             source=f"{plant.name}"))
        elif cible == "global" and eco:
            mutations.append(InjectField(tile.tile_id, variable, amount,
                                         source=f"{plant.name}"))

    # --- add_rondelle : discret probabiliste ---
    elif action == "add_rondelle":
        variable = effect["variable"]
        amount   = effect.get("amount", 1)
        max_val  = effect.get("max", 3)
        # Probabilité modulée par champ si disponible
        proba = effect.get("probability", 1.0)
        if eco and variable == "pollinisateur":
            # Les pollinisateurs sont attirés par la lumière locale
            light = eco.lumiere.at_plot(r, c)
            proba *= (0.5 + light * 0.5)
        if random.random() <= proba:
            real = _clamp_rondelle(tile, variable, amount, max_val)
            if real > 0:
                mutations.append(AddRondelle(tile.tile_id, variable, real,
                                             source=plant.name))

    # --- reduce_rondelle ---
    elif action == "reduce_rondelle":
        variable = effect["variable"]
        amount   = effect.get("amount", 1)
        real = _clamp_rondelle(tile, variable, -amount)
        if real < 0:
            mutations.append(RemoveRondelle(tile.tile_id, variable, -real,
                                            source=plant.name))

    # --- reduce_health : probabiliste via microbiome ---
    elif action == "reduce_health":
        condition = effect.get("condition")
        if condition:
            cond_var = condition.get("rondelle")
            if tile.get_rondelle_count(cond_var) < condition.get("min", 1):
                return []
        amount = effect.get("amount", 1)
        # Probabilité de dégât réduite par microbiome local
        base_p = effect.get("probability", 0.8)
        if eco:
            p = eco.disease_probability(r, c, base_rate=base_p)
        else:
            p = base_p
        if random.random() <= p:
            mutations.append(ReduceHealth(plant, amount,
                                          reason=effect.get("description", "")))

    # --- score ---
    elif action == "score":
        axis   = effect["axis"]
        amount = effect.get("amount", 1)
        player_id = game_state.get("current_player", "joueur_1")
        mutations.append(AddScore(player_id, axis, amount, source=plant.name))

    # --- adjacency_bonus : devient injection microbiome ---
    elif action == "adjacency_bonus":
        bonus  = effect.get("bonus", "")
        radius = effect.get("radius", 1)
        if bonus == "reduce_maladie_rondelle" and eco:
            # Lamiaceae : booste le microbiome local plutôt que supprimer maladie directement
            micro_boost = effect.get("amount", 1) * 0.15
            mutations.append(InjectField(tile.tile_id, "microbiome",
                                         micro_boost, r, c,
                                         source=f"{plant.name}/aromatique"))
            nearby = _alive_in_radius(tile, plant, radius)
            if nearby:
                mutations.append(Notification(
                    message=(f"{plant.name} enrichit le microbiome local "
                             f"(protection {len(nearby)} voisine(s))."),
                    severity="info", plant=plant))

    return mutations

# ---------------------------------------------------------------------------
# CALLBACKS COMPLEXES
# ---------------------------------------------------------------------------

@register_effect("basil_companion_check")
def basil_companion_check(effect, plant, tile, game_state):
    """
    Basilic : boost microbiome ciblé sur les Solanacées voisines.
    Le microbiome élevé réduit probabilistiquement la maladie — pas d'annulation directe.
    """
    mutations = []
    eco = _get_eco(game_state, tile.tile_id)
    radius  = effect.get("radius", 2)
    nearby  = _alive_in_radius(tile, plant, radius)
    solanacees = [p for p in nearby if p.plant_class.family == "Solanaceae"]

    if not solanacees:
        return []

    # Boost microbiome proportionnel au nombre de solanacées protégées
    boost = min(len(solanacees) * 0.12, 0.35)
    r, c = plant.position
    if eco:
        mutations.append(InjectField(tile.tile_id, "microbiome",
                                     boost, r, c,
                                     source="basilic/compagnonnage"))
        # Diffusion légère vers les solanacées voisines
        for sol in solanacees:
            sr, sc = sol.position
            mutations.append(InjectField(tile.tile_id, "microbiome",
                                         boost * 0.4, sr, sc,
                                         source="basilic→solanacée"))

    noms = ", ".join(p.name for p in solanacees)
    mutations.append(Notification(
        message=f"Basilic → microbiome +{boost:.2f} (protège {noms}).",
        severity="info", plant=plant))

    return mutations

# ---------------------------------------------------------------------------
# APPLICATION DES MUTATIONS
# ---------------------------------------------------------------------------

def apply_mutations(mutations: list, game_state: dict) -> list[str]:
    log = []
    for m in mutations:

        if isinstance(m, AddRondelle):
            tile = _get_tile(game_state, m.tile_id)
            if not tile: continue
            added = 0
            for stake in tile.stakes:
                if added >= m.amount: break
                if stake.variable is None or stake.variable == m.variable:
                    if stake.add(m.variable): added += 1
            if added: log.append(f"  ✓ {m}")

        elif isinstance(m, RemoveRondelle):
            tile = _get_tile(game_state, m.tile_id)
            if not tile: continue
            removed = 0
            for stake in reversed(tile.stakes):
                if removed >= m.amount: break
                if stake.variable == m.variable:
                    stake.remove_top(); removed += 1
            if removed: log.append(f"  ✓ {m}")

        elif isinstance(m, ReduceHealth):
            m.plant.health = max(0, m.plant.health - m.amount)
            status = "meurt" if m.plant.health == 0 else f"santé={m.plant.health}"
            log.append(f"  {'✗' if m.plant.health==0 else '!'} {m} → {status}")

        elif isinstance(m, AddScore):
            scores = game_state.setdefault("scores", {})
            player = scores.setdefault(m.player_id,
                                       {"recolte": 0, "luxuriance": 0, "biodiversite": 0})
            player[m.axis] = player.get(m.axis, 0) + m.amount
            log.append(f"  ✓ {m}")

        elif isinstance(m, InjectField):
            eco = _get_eco(game_state, m.tile_id)
            if not eco: continue
            f = eco.get_field(m.variable)
            if not f: continue
            if m.row is not None:
                f.add(m.row, m.col, m.amount)
            else:
                for r in range(f.rows):
                    for c in range(f.cols):
                        f.add(r, c, m.amount)
            log.append(f"  ~ {m}")

        elif isinstance(m, PropagateDisease):
            eco = _get_eco(game_state, m.source_plant.position[0])
            # Tirage probabiliste
            if random.random() <= m.probability:
                m.target_plant.health = max(0, m.target_plant.health - 1)
                log.append(f"  ✓ {m}")
            else:
                log.append(f"  ○ {m} (bloqué par microbiome)")

        elif isinstance(m, Notification):
            icon = {"info":"ℹ","warning":"⚠","danger":"🔴"}.get(m.severity,"ℹ")
            log.append(f"  {icon} {m.message}")

    return log

# ---------------------------------------------------------------------------
# PERTURBATIONS ÉCOLOGIQUES
# ---------------------------------------------------------------------------

def herbivory_pressure(plant: PlantInstance, tile: Tile,
                       game_state: dict, eco) -> list[Mutation]:
    """
    Pression herbivore diffuse — pas de ravageur visible.
    Dépend de la biomasse locale, de la diversité et du microbiome.

    pressure = biomasse * HERBIVORY_BASE * (1 - biodiversite) * (1 - microbiome)

    Polyculture et microbiome élevé → pression faible.
    Monoculture → pression forte → instabilité émergente.
    """
    if not plant.is_alive:
        return []

    r, c = plant.position
    # Biomasse locale = nombre de plantes adultes/matures sur les plots voisins + soi
    nearby = [p for p in tile.plants
              if p.is_alive and p.current_stage >= 2
              and p.position in tile.plots_within_radius(r, c, 1) + [plant.position]]
    biomass_local = len(nearby) / 6.0  # normalisé [0, 1] sur 6 voisins max

    # Index de biodiversité : proportion de familles différentes dans le voisinage
    families = {p.plant_class.family for p in nearby}
    biodiversity_index = min(1.0, len(families) / 4.0)  # 4 familles = max

    # Microbiome local normalisé
    micro_norm = min(1.0, eco.microbiome.at_plot(r, c) / 3.0) if eco else 0.3

    # Pression nette
    pressure = (biomass_local * HERBIVORY_BASE
                * max(0.0, 1.0 - biodiversity_index)
                * max(0.0, 1.0 - micro_norm))

    if pressure < 0.005:
        return []

    # Application probabiliste sur la santé (pas de mort brutale)
    mutations = []
    if pressure > plant.stress_memory * 0.5:
        # La plante stressée résiste mieux (paradoxe biologique)
        effective_pressure = pressure * max(0.3, 1.0 - plant.stress_memory * 0.5)
        if effective_pressure > 0.015:
            mutations.append(ReduceHealth(
                plant, 1,
                reason=f"herbivorie p={pressure:.3f}"
            ))
    return mutations


def background_mortality(plant: PlantInstance, eco,
                         seed: int, week: int) -> list[Mutation]:
    """
    Micro-mortalité aléatoire déterministe.
    Bruit spatial → affaiblissement spontané (pas de mort brutale).

    noise = hash(seed, week, r, c)
    if noise < MORTALITY_RATE → health *= 0.7 (arrondi à l'entier inférieur)

    Prevents perfect optimization — le jardin reste imprévisible.
    """
    if not plant.is_alive:
        return []

    r, c = plant.position
    noise = _hash_noise(seed, week, r, c)

    # Le stress mémorisé réduit la mortalité (plante endurcie)
    adjusted_rate = MORTALITY_RATE * max(0.2, 1.0 - plant.stress_memory * 0.6)

    if noise < adjusted_rate:
        # Affaiblissement — pas de mort directe
        new_health = max(1, int(plant.health * 0.7))
        if new_health < plant.health:
            return [ReduceHealth(
                plant,
                plant.health - new_health,
                reason=f"mortalité de fond (noise={noise:.3f})"
            )]
    return []


def apply_disturbances(tile, eco, game_state: dict,
                       seed: int, week: int,
                       year_fraction: float) -> list[str]:
    """
    Applique toutes les perturbations de fond pour un tick.
    Appelée après la croissance et les effets biotiques.

    Order :
      1. Oscillation climatique (modifie evaporation in-tick via growth_modifier)
      2. Herbivorie diffuse
      3. Micro-mortalité déterministe
      4. Mise à jour stress_memory des plantes
    """
    log = []

    # 1. Stress climatique de fond (influence affichée si notable)
    c_stress = climate_stress(year_fraction)
    if abs(c_stress) > 0.04:
        sign = "↑" if c_stress > 0 else "↓"
        log.append(f"    🌡 Oscillation climatique : {c_stress:+.3f} "
                   f"(croissance {sign})")

    # 2 & 3. Perturbations par plante
    all_mutations = []
    for plant in list(tile.plants):
        if not plant.is_alive:
            continue
        # Herbivorie
        all_mutations += herbivory_pressure(plant, tile, game_state, eco)
        # Mortalité de fond
        all_mutations += background_mortality(plant, eco, seed, week)

    log += apply_mutations(all_mutations, game_state)

    # 4. Mise à jour stress_memory (intégration lente)
    for plant in tile.plants:
        if not plant.is_alive:
            continue
        r, c = plant.position
        disturbance_local = eco.disturbance.local(r, c) if eco else 0.1
        # Paradoxe biologique : stress↑ → résistance↑ à terme
        plant.stress_memory += (disturbance_local - plant.stress_memory) * 0.08
        plant.stress_memory = max(0.0, min(1.0, plant.stress_memory))

    # Nettoyer les plantes mortes
    tile.plants = [p for p in tile.plants if p.is_alive]

    return log


# ---------------------------------------------------------------------------
# RÉSOLUTION D'UN TOUR PLANTE
# ---------------------------------------------------------------------------

def resolve_plant_turn(plant, tile, game_state, trigger):
    all_effects = plant.plant_class.get_all_effects(plant.plant_class, plant.current_stage)
    all_mutations = []
    for effect in all_effects:
        all_mutations.extend(resolve(effect, plant, tile, game_state, trigger))
    log = apply_mutations(all_mutations, game_state)
    return all_mutations, log
