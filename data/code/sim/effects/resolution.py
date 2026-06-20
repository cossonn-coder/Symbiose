"""
SYMBIOSE — sim/effects/resolution.py
Pipeline de résolution des effets : `resolve` (un effet déclaratif → mutations),
les callbacks complexes enregistrés (`basil_companion_check`), `apply_mutations`
(mutations → effet réel sur tuiles/champs + log) et `resolve_plant_turn` (tous
les effets d'une plante pour un trigger).

Philosophie : jamais bonus/malus directs sur les plantes — flux → contrainte
écologique → réponse émergente. Déterminisme (philo #3) : les tirages discrets
passent par `_hash_noise(seed, week·K, r, c)`, jamais de RNG live (canaux
week·19 / week·23 / week·29). Identique à l'ancien effects.py.
"""

from __future__ import annotations

from plants import PlantInstance, EFFECT_REGISTRY, register_effect
from world import Tile
from fields import _hash_noise
from .mutations import (AddRondelle, RemoveRondelle, ReduceHealth, AddScore,
                        InjectField, PropagateDisease, Notification, Mutation)

# Sémiologie ② (CONCEPTION_SEMIOLOGIE_FOLIAIRE.md §2.5) — gain de marque foliaire :
# convertit le coup de santé d'un ReduceHealth à cause typée en intensité [0,1]
# cumulable. Couplé à SYMPTOM_DECAY (croissance.py) : à GAIN 0.5 / DECAY 0.8, un
# coup unique laisse une marque ~0.5, de demi-vie ~3 semaines (0.8³≈0.5) → la
# plante soignée s'éclaircit nettement en ~3-4 semaines, purge sous epsilon ensuite.
SYMPTOM_MARK_GAIN = 0.5

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
    seed = game_state.get("seed", 42)
    week = game_state.get("week", 0)

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
        if _hash_noise(seed, week * 19, r, c) <= proba:
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
        if _hash_noise(seed, week * 23, r, c) <= p:
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
            # Sémiologie ② : une cause typée (maladie/gel/grêle) laisse une marque
            # foliaire décroissante. `* SYMPTOM_MARK_GAIN` (knob) convertit le coup de
            # santé en intensité [0,1] cumulable, plafonnée. Marque PURE cosmétique :
            # lue par sim.semiologie au snapshot, jamais reboucle sur la santé.
            if m.cause:
                marks = m.plant.symptom_marks
                marks[m.cause] = min(1.0, marks.get(m.cause, 0.0) + m.amount * SYMPTOM_MARK_GAIN)
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
            # `om_fresh` n'est plus un GridField : les injections d'espèces
            # (paillage / engrais vert, plants/species.py) déposent une parcelle
            # `herbace` (tissu générique en ① ; ② raffinera). Intercepté AVANT
            # get_field, qui renverrait None (le champ n'existe plus).
            if m.variable == "om_fresh":
                if m.row is not None:
                    eco.deposer_litiere(m.row, m.col, "herbace", m.amount)
                else:
                    for r in range(eco.rows):
                        for c in range(eco.cols):
                            eco.deposer_litiere(r, c, "herbace", m.amount)
                log.append(f"  ~ {m}")
                continue
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
            # Tirage déterministe (philo #3) : hash spatial sur la cible, canal
            # week·29 décorrélé. game_state porte seed/week pendant le tick.
            seed = game_state.get("seed", 42)
            week = game_state.get("week", 0)
            tr, tc = m.target_plant.position
            if _hash_noise(seed, week * 29, tr, tc) <= m.probability:
                m.target_plant.health = max(0, m.target_plant.health - 1)
                log.append(f"  ✓ {m}")
            else:
                log.append(f"  ○ {m} (bloqué par microbiome)")

        elif isinstance(m, Notification):
            icon = {"info":"ℹ","warning":"⚠","danger":"🔴"}.get(m.severity,"ℹ")
            log.append(f"  {icon} {m.message}")

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
