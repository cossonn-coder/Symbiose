"""
SYMBIOSE — fields.py v3
Champs écologiques continus — modèle hydrologique stable + lumière directionnelle + soil memory.

Hydrologie (ordre du tick) :
  1. evaporation    : humidite *= 0.995
  2. plant_uptake   : consommation racinaire locale
  3. base_rain      : +BASE_RAIN constant (rosée/capillarité)
  4. soil_retention : +soil_memory * 0.01 (sols vivants retiennent l'eau)
  5. drainage       : humidite *= DRAINAGE (évite saturation)

Microbiome : diffusion hebdomadaire active (aura progressive du basilic).
Lumière    : projection directionnelle, pas de diffusion.
Soil memory: intégration saisonnière très lente (lerp 0.05/saison).
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# CONSTANTES ÉCOLOGIQUES
# ---------------------------------------------------------------------------

HUMIDITY_INERTIA  = 0.55

# Hydrologie
FERTILITY_INERTIA = 0.85
MICROBE_INERTIA   = 0.92   # plus diffusif pour aura basilic

BASE_RAIN      = 0.015
EVAPORATION    = 0.997
DRAINAGE       = 0.993
SOIL_RETENTION = 0.010

# Cycle biogéochimique
DECAY_RATE       = 0.012   # minéralisation hebdomadaire organic_matter → fertilite
CARBON_LOSS      = 0.998   # respiration microbienne (perte carbone/semaine)
LEACHING_LOSS    = 0.999   # lessivage nutriments (perte fertilite/semaine)
BIOMASS_EXPORT   = 0.20    # fraction exportée à la récolte (le reste = nécromasse)

# Soil memory
SOIL_FAST_RATE   = 0.15    # intégration rapide (annuelle)
SOIL_DEEP_RATE   = 0.02    # intégration lente (décennale)

# Perturbations écologiques
MORTALITY_RATE      = 0.010   # probabilité d'affaiblissement spontané/semaine
HERBIVORY_BASE      = 0.020   # pression herbivore de base
DISTURBANCE_INERTIA = 0.900   # inertie du champ de perturbation spatial
CLIMATE_AMPLITUDE   = 0.080   # amplitude oscillation climatique de fond

# Uptake racinaire par stade
UPTAKE = {
    "humidite":  {0: 0.05, 1: 0.10, 2: 0.18, 3: 0.12},
    "fertilite": {0: 0.02, 1: 0.05, 2: 0.08, 3: 0.05},
    "microbiome":{0: 0.00, 1: 0.01, 2: 0.02, 3: 0.01},
}

# Signature sol par famille (laissée après chaque saison)
SOIL_SIGNATURE = {
    "Fabaceae":   {"microbiome": +0.15, "fertilite": +0.10},
    "Solanaceae": {"microbiome": -0.05},
    "Asteraceae": {"microbiome": +0.05, "fertilite": +0.05},
    "Lamiaceae":  {"microbiome": +0.08},
}

# Ombres par strate
SHADOW_LENGTH = {"haute": 3, "moyenne": 1, "basse": 0, "sol": 0, "grimpante": 1}
SHADOW_DENSITY = {"printemps": 0.6, "ete": 0.4, "automne": 0.65, "hiver": 0.85}

# Vecteurs d'ombre sur grille quinconce (soleil au Sud)
# Format : (delta_row_pair, delta_col_pair, delta_row_impair, delta_col_impair)
SHADOW_VECTOR = {
    "printemps": ((-1, -1), (-1,  0)),  # NW
    "ete":       ((-1,  0), (-1,  1)),  # N légèrement NE (zénith)
    "automne":   ((-1,  0), (-1,  1)),  # NE
    "hiver":     ((-1,  0), (-1,  0)),  # N pur (soleil très bas)
}

# ---------------------------------------------------------------------------
# GRIDFIELD
# ---------------------------------------------------------------------------

class GridField:
    """Grille 2D de floats avec voisinage hexagonal."""

    def __init__(self, rows: int, cols: int,
                 initial: float = 0.0, max_val: float = 3.0):
        self.rows    = rows
        self.cols    = cols
        self.max_val = max_val
        self.data: list[list[float]] = [
            [float(initial)] * cols for _ in range(rows)
        ]

    def get(self, r: int, c: int) -> float:
        return self.data[r][c]

    def set(self, r: int, c: int, v: float) -> None:
        self.data[r][c] = max(0.0, min(self.max_val, v))

    def add(self, r: int, c: int, delta: float) -> None:
        self.set(r, c, self.data[r][c] + delta)

    def at_plot(self, r: int, c: int) -> float:
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return self.data[r][c]
        return 0.0

    def total(self) -> float:
        return sum(v for row in self.data for v in row)

    def average(self) -> float:
        n = self.rows * self.cols
        return self.total() / n if n else 0.0

    def hex_neighbors(self, r: int, c: int) -> list[tuple[int, int]]:
        if r % 2 == 0:
            deltas = [(-1,-1),(-1,0),(0,-1),(0,1),(1,-1),(1,0)]
        else:
            deltas = [(-1,0),(-1,1),(0,-1),(0,1),(1,0),(1,1)]
        return [(r+dr, c+dc) for dr,dc in deltas
                if 0 <= r+dr < self.rows and 0 <= c+dc < self.cols]

    def diffuse(self, inertia: float = 0.7) -> None:
        """Double buffer — diffusion isotrope stable."""
        old = [row[:] for row in self.data]
        for r in range(self.rows):
            for c in range(self.cols):
                nb = self.hex_neighbors(r, c)
                avg = sum(old[nr][nc] for nr,nc in nb) / len(nb) if nb else old[r][c]
                self.data[r][c] = max(0.0, min(
                    self.max_val,
                    old[r][c] * inertia + avg * (1.0 - inertia)
                ))

    def ascii_map(self, precision: int = 2) -> str:
        lines = []
        for r, row in enumerate(self.data):
            prefix = "  " if r % 2 == 1 else ""
            lines.append(prefix + " ".join(f"{v:.{precision}f}" for v in row))
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"GridField({self.rows}×{self.cols}) avg={self.average():.3f}"

# ---------------------------------------------------------------------------
# LIGHTFIELD — projection directionnelle (pas de diffusion)
# ---------------------------------------------------------------------------

class LightField(GridField):
    """
    Champ de lumière — reset à 1.0 chaque tick,
    puis projection multiplicative des ombres des plantes hautes.
    La lumière ne diffuse PAS.
    """

    def __init__(self, rows: int, cols: int):
        super().__init__(rows, cols, initial=1.0, max_val=1.0)

    def reset(self) -> None:
        for r in range(self.rows):
            for c in range(self.cols):
                self.data[r][c] = 1.0

    def _shadow_plots(self, origin_r: int, origin_c: int,
                      saison: str, length: int) -> list[tuple[int, int]]:
        """
        Calcule les plots ombrés depuis un plot d'origine.
        Suit le vecteur directionnel sur 'length' pas.
        """
        vec_pair, vec_impair = SHADOW_VECTOR.get(saison, ((-1,0),(-1,0)))
        plots = []
        r, c = origin_r, origin_c
        for _ in range(length):
            dr, dc = vec_pair if r % 2 == 0 else vec_impair
            r, c = r + dr, c + dc
            if 0 <= r < self.rows and 0 <= c < self.cols:
                plots.append((r, c))
            else:
                break
        return plots

    def cast_shadow(self, origin_r: int, origin_c: int,
                    strate: str, saison: str) -> list[tuple[int, int]]:
        """
        Projette l'ombre d'une plante. Accumulation multiplicative.
        Retourne la liste des plots affectés (pour le log).
        """
        length = SHADOW_LENGTH.get(strate, 0)
        if length == 0:
            return []
        density = SHADOW_DENSITY.get(saison, 0.6)
        plots = self._shadow_plots(origin_r, origin_c, saison, length)
        for r, c in plots:
            self.data[r][c] *= (1.0 - density)
        return plots

    def compute(self, plants: list, saison: str) -> list[str]:
        """
        Calcule le champ de lumière complet pour un tick.
        1. Reset à 1.0
        2. Chaque plante adulte/mature projette son ombre
        Retourne un log des ombres projetées.
        """
        self.reset()
        log = []
        for plant in plants:
            if not plant.is_alive:
                continue
            # Seules les plantes au stade adulte (2) ou mature (3) font de l'ombre
            if plant.current_stage < 2:
                continue
            strate = plant.stage.strate
            if SHADOW_LENGTH.get(strate, 0) == 0:
                continue
            r, c = plant.position
            affected = self.cast_shadow(r, c, strate, saison)
            if affected:
                log.append(f"    ☀ {plant.name}@{plant.position} "
                           f"ombre → {affected} (strate={strate})")
        return log

# ---------------------------------------------------------------------------
# BRUIT DÉTERMINISTE
# ---------------------------------------------------------------------------

def _hash_noise(seed: int, week: int, r: int, c: int) -> float:
    """
    Bruit spatial déterministe — aucun RNG pendant le tick.
    Combine seed global, semaine et coordonnées → float [0, 1].
    Utilise un hash entier rapide (PCG-inspired).
    """
    h = seed ^ (week * 0x9e3779b9) ^ (r * 0x6c62272e) ^ (c * 0x517cc1b7)
    h = ((h >> 16) ^ h) * 0x45d9f3b
    h = ((h >> 16) ^ h) * 0x45d9f3b
    h = (h >> 16) ^ h
    return (h & 0x7FFFFFFF) / 0x7FFFFFFF


def climate_stress(year_fraction: float, phase: float = 0.0) -> float:
    """
    Oscillation climatique lente — sin(2π * fraction_annuelle + phase).
    Retourne une valeur dans [-CLIMATE_AMPLITUDE, +CLIMATE_AMPLITUDE].
    Le joueur ne voit rien explicitement, mais le jardin change d'humeur.
    """
    return math.sin(year_fraction * 2 * math.pi + phase) * CLIMATE_AMPLITUDE


# ---------------------------------------------------------------------------
# DISTURBANCEFIELD — champ de perturbation spatiale
# ---------------------------------------------------------------------------

class DisturbanceField(GridField):
    """
    Champ de perturbation écologique spatiale.
    Mis à jour hebdomadairement par intégration lente du bruit :
        disturbance[r][c] = disturbance*0.9 + noise*0.1
    Crée des zones chroniquement fragiles et des refuges écologiques stables.
    """

    def __init__(self, rows: int, cols: int):
        super().__init__(rows, cols, initial=0.05, max_val=1.0)

    def tick(self, seed: int, week: int) -> None:
        """Intègre un tick de bruit déterministe dans le champ."""
        for r in range(self.rows):
            for c in range(self.cols):
                noise = _hash_noise(seed, week, r, c)
                current = self.data[r][c]
                self.data[r][c] = (
                    current * DISTURBANCE_INERTIA +
                    noise * (1.0 - DISTURBANCE_INERTIA)
                )

    def local(self, r: int, c: int) -> float:
        """Intensité de perturbation locale normalisée [0, 1]."""
        return self.at_plot(r, c)


# ---------------------------------------------------------------------------
# SEEDBANKFIELD — banque de graines latente
# ---------------------------------------------------------------------------

SEED_ARCHETYPES = ["pioneer", "nitrogen_fixer", "grass", "competitor"]

SEED_VIABILITY_LOSS = 0.998   # vieillissement hebdomadaire des graines
SEED_DISTURBANCE_GAIN = 0.002 # enrichissement par perturbation (pioneer surtout)


class SeedBank:
    """
    Banque de graines latente par plot — mémoire biologique invisible.
    Chaque plot stocke une probabilité de germination par archétype.

    Dynamique :
      - Vieillissement : seed *= 0.998 (perte viabilité lente)
      - Enrichissement : perturbations → +pioneer
      - Production : plantes matures → +archétype correspondant
    """

    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        # data[r][c] = dict archétype → densité [0, 1]
        self.data: list[list[dict]] = [
            [{a: 0.01 for a in SEED_ARCHETYPES} for _ in range(cols)]
            for _ in range(rows)
        ]

    def get(self, r: int, c: int, archetype: str) -> float:
        return self.data[r][c].get(archetype, 0.0)

    def add(self, r: int, c: int, archetype: str, amount: float) -> None:
        d = self.data[r][c]
        d[archetype] = min(1.0, d[archetype] + amount)

    def total_density(self, r: int, c: int) -> float:
        return sum(self.data[r][c].values())

    def tick_aging(self) -> None:
        """Vieillissement hebdomadaire — perte lente de viabilité."""
        for r in range(self.rows):
            for c in range(self.cols):
                for a in SEED_ARCHETYPES:
                    self.data[r][c][a] *= SEED_VIABILITY_LOSS

    def tick_disturbance_enrichment(self,
                                    disturbance_field: "DisturbanceField") -> None:
        """Sol perturbé → enrichissement en graines pionnières."""
        for r in range(self.rows):
            for c in range(self.cols):
                d = disturbance_field.at_plot(r, c)
                self.add(r, c, "pioneer",
                         d * SEED_DISTURBANCE_GAIN)

    def tick_plant_production(self, plants: list) -> None:
        """Plantes matures → production de graines dans la banque locale."""
        for p in plants:
            if not p.is_alive:
                continue
            if p.current_stage < 2:   # seulement adulte/mature
                continue
            archetype = getattr(p.plant_class, "archetype", None)
            rate = getattr(p.plant_class, "reproduction_rate", 0.02)
            if archetype:
                r, c = p.position
                self.add(r, c, archetype, rate * 0.5)

    def niche_index(self, r: int, c: int,
                    light: float, root_density: float,
                    disturbance: float, soil_memory_deep: float) -> float:
        """
        Indice de niche libre [0, 1].

        Une niche ouverte = lumière disponible + espace racinaire libre
                          + perturbation récente + sol encore jeune.

        light         : disponibilité lumineuse [0,1] — plein soleil = 1.0 = bonne niche
        root_density  : fraction de voisins occupés [0,1] — saturé = mauvaise niche
        disturbance   : intensité de perturbation [0,1] — élevé = bonne niche
        soil_memory_deep : mémoire profonde [0,1] — sol établi = moins de place

        niche = light * (1-root_density) * disturbance * (1-soil_memory_deep*0.5)
        """
        return (light *
                max(0.0, 1.0 - root_density) *
                disturbance *
                max(0.0, 1.0 - soil_memory_deep * 0.5))

    def germination_candidates(self, r: int, c: int,
                               seed: int, week: int,
                               niche: float) -> list[str]:
        """
        Tirage déterministe des archétypes qui germent sur ce plot.
        hash(seed, week, r, c) < niche * seed_density → germination.
        Retourne la liste des archétypes qui passent le seuil.
        """
        candidates = []
        for archetype in SEED_ARCHETYPES:
            density = self.get(r, c, archetype)
            if density < 0.001:
                continue
            threshold = niche * density
            noise = _hash_noise(seed, week * 7 + SEED_ARCHETYPES.index(archetype),
                                r, c)
            if noise < threshold:
                candidates.append(archetype)
        return candidates

    def ascii_map(self, archetype: str = "pioneer", precision: int = 3) -> str:
        lines = []
        for r, row in enumerate(self.data):
            prefix = "  " if r % 2 == 1 else ""
            vals = " ".join(f"{d[archetype]:.{precision}f}" for d in row)
            lines.append(prefix + vals)
        return "\n".join(lines)

    def __repr__(self) -> str:
        totals = {a: sum(self.data[r][c][a]
                         for r in range(self.rows)
                         for c in range(self.cols))
                  for a in SEED_ARCHETYPES}
        return "SeedBank " + " ".join(f"{a[:3]}={v:.2f}" for a, v in totals.items())


# ---------------------------------------------------------------------------
# ECOFIELDS — conteneur complet
# ---------------------------------------------------------------------------

@dataclass
class EcoFields:
    tile_id:    str
    rows:       int
    cols:       int

    humidite:         GridField = field(default=None)
    fertilite:        GridField = field(default=None)
    microbiome:       GridField = field(default=None)
    lumiere:          LightField = field(default=None)
    soil_memory:      GridField = field(default=None)   # mémoire effective (composite)
    soil_memory_fast: GridField = field(default=None)   # annuelle (lerp 0.15)
    soil_memory_deep: GridField = field(default=None)   # décennale (lerp 0.02)
    organic_matter:   GridField = field(default=None)   # nécromasse / compost in situ
    disturbance:      DisturbanceField = field(default=None)
    seed_bank:        SeedBank = field(default=None)

    def __post_init__(self):
        if self.humidite    is None: self.humidite    = GridField(self.rows, self.cols)
        if self.fertilite   is None: self.fertilite   = GridField(self.rows, self.cols)
        if self.microbiome  is None: self.microbiome  = GridField(self.rows, self.cols)
        if self.lumiere     is None: self.lumiere     = LightField(self.rows, self.cols)
        if self.soil_memory is None:
            self.soil_memory = GridField(self.rows, self.cols, max_val=1.0)
        if self.soil_memory_fast is None:
            self.soil_memory_fast = GridField(self.rows, self.cols, max_val=1.0)
        if self.soil_memory_deep is None:
            self.soil_memory_deep = GridField(self.rows, self.cols, max_val=1.0)
        if self.organic_matter is None:
            self.organic_matter = GridField(self.rows, self.cols,
                                            initial=0.0, max_val=10.0)
        if self.disturbance is None:
            self.disturbance = DisturbanceField(self.rows, self.cols)
        if self.seed_bank is None:
            self.seed_bank = SeedBank(self.rows, self.cols)

    def get_field(self, name: str) -> GridField | None:
        return {
            "humidite":    self.humidite,
            "fertilite":   self.fertilite,
            "microbiome":  self.microbiome,
            "lumiere":     self.lumiere,
            "soil_memory": self.soil_memory,
            "disturbance":      self.disturbance,
            "organic_matter":   self.organic_matter,
            "soil_memory_fast": self.soil_memory_fast,
            "soil_memory_deep": self.soil_memory_deep,
        }.get(name)

    # --- Tick diffusion ---

    def tick_diffusion(self) -> None:
        """
        Diffusion spatiale des champs continus.
        Microbiome inertie 0.92 → aura progressive des aromatiques.
        """
        self.humidite.diffuse(inertia=HUMIDITY_INERTIA)
        self.fertilite.diffuse(inertia=FERTILITY_INERTIA)
        self.microbiome.diffuse(inertia=MICROBE_INERTIA)

    # --- Hydrologie ---

    def tick_hydrology(self) -> None:
        """
        Cycle hydrologique complet. Ordre strict :
          1. Évaporation atmosphérique
          2. Pluie de fond (apport diffus constant)
          3. Rétention sol (couplage soil_memory)
          4. Drainage naturel
        L'uptake racinaire est géré séparément dans engine.
        """
        for r in range(self.rows):
            for c in range(self.cols):
                h = self.humidite.data[r][c]
                h *= EVAPORATION                                    # 1. évaporation
                h += BASE_RAIN                                      # 2. pluie de fond
                h += self.soil_memory.at_plot(r, c) * SOIL_RETENTION  # 3. rétention
                h *= DRAINAGE                                       # 4. drainage
                self.humidite.set(r, c, h)

    # --- Lumière ---

    def tick_light(self, plants: list, saison: str) -> list[str]:
        """Recalcule le champ de lumière pour ce tick."""
        return self.lumiere.compute(plants, saison)

    # --- Perturbations ---

    def tick_disturbance(self, seed: int, week: int) -> None:
        """Met à jour le champ de perturbation spatiale (bruit déterministe)."""
        self.disturbance.tick(seed, week)

    # --- Banque de graines ---

    def tick_seed_bank(self, plants: list, seed: int = 0, week: int = 0) -> None:
        """Mise à jour hebdomadaire de la banque de graines."""
        self.seed_bank.tick_aging()
        self.seed_bank.tick_disturbance_enrichment(self.disturbance)
        self.seed_bank.tick_plant_production(plants)

    # --- Soil memory ---

    def tick_soil_memory(self, plants: list) -> None:
        """
        Mémoire du sol double temps :
          soil_memory_fast : lerp 0.15 — changements annuels (activité biologique)
          soil_memory_deep : lerp 0.02 — changements décennaux (structure, mycorhizes)
          soil_memory      : 0.7*fast + 0.3*deep (mémoire effective)

        Le sol ne peut pas être réinitialisé instantanément.
        """
        for r in range(self.rows):
            for c in range(self.cols):
                micro = self.microbiome.at_plot(r, c) / 3.0
                fert  = min(1.0, self.fertilite.at_plot(r, c) / 3.0)
                om    = min(1.0, self.organic_matter.at_plot(r, c) / 5.0)

                # Signature des plantes sur ce plot
                sig = 0.0
                for p in plants:
                    if not p.is_alive:
                        continue
                    if (r, c) == p.position or (r, c) in p.root_plots:
                        family_sig = SOIL_SIGNATURE.get(p.plant_class.family, {})
                        sig += family_sig.get("microbiome", 0.0) * 0.5
                sig = max(-0.2, min(0.2, sig))

                # Cible écologique
                target = (micro * 0.4 + fert * 0.2
                          + om * 0.2 + (0.5 + sig) * 0.2)
                target = max(0.0, min(1.0, target))

                # Mémoire rapide (annuelle)
                fast = self.soil_memory_fast.at_plot(r, c)
                fast += (target - fast) * SOIL_FAST_RATE
                self.soil_memory_fast.set(r, c, fast)

                # Mémoire profonde (décennale)
                deep = self.soil_memory_deep.at_plot(r, c)
                deep += (target - deep) * SOIL_DEEP_RATE
                self.soil_memory_deep.set(r, c, deep)

                # Mémoire effective composite
                effective = fast * 0.7 + deep * 0.3
                self.soil_memory.set(r, c, effective)

    def tick_decomposition(self) -> None:
        """
        Cycle biogéochimique hebdomadaire.
        
        1. Minéralisation : organic_matter → fertilite
           vitesse modulée par microbiome (sol vivant = recyclage rapide)
        2. Respiration microbienne : perte carbone (organic_matter)
        3. Lessivage : perte lente fertilite
        """
        for r in range(self.rows):
            for c in range(self.cols):
                om    = self.organic_matter.data[r][c]
                micro = self.microbiome.at_plot(r, c) / 3.0

                # 1. Minéralisation (OM → fertilite)
                # Sol vivant décompose 2x plus vite que sol mort
                decomp_rate = DECAY_RATE * (0.5 + micro * 0.5)
                released = om * decomp_rate
                self.organic_matter.add(r, c, -released)
                self.fertilite.add(r, c, released)

                # 2. Respiration microbienne (perte carbone)
                self.organic_matter.data[r][c] *= CARBON_LOSS

                # 3. Lessivage nutriments
                self.fertilite.data[r][c] *= LEACHING_LOSS

    def add_necromass(self, r: int, c: int,
                      biomass: float, harvested: bool = False) -> float:
        """
        Ajoute de la nécromasse au plot lors d'une mort ou récolte.
        harvested=True : une fraction est exportée (récolte) → moins de retour sol.
        Retourne la quantité effectivement déposée.
        """
        # Récolte exporte BIOMASS_EXPORT, mort laisse tout sur place
        export_fraction = BIOMASS_EXPORT if harvested else 0.0
        deposited = biomass * (1.0 - export_fraction)
        self.organic_matter.add(r, c, deposited)
        return deposited

    # --- Météo ---

    def apply_weather(self, variable: str, delta: float,
                      row: int = None, col: int = None) -> None:
        f = self.get_field(variable)
        if f is None:
            return
        if row is not None:
            f.add(row, col, delta)
        else:
            for r in range(self.rows):
                for c in range(self.cols):
                    f.add(r, c, delta)

    # --- Uptake racinaire ---

    def plant_uptake(self, r: int, c: int, stage_index: int,
                      shade_memory: float = 0.0,
                      drought_memory: float = 0.0) -> dict[str, float]:
        """
        Consommation racinaire modulée par la mémoire physiologique.

        shade_memory  → réduit la transpiration (plante étiolée, moins de surface foliaire)
        drought_memory → réduit la consommation d'eau (racines adaptées, stomates fermés)
        """
        consumed = {}
        for var, by_stage in UPTAKE.items():
            amount = by_stage.get(stage_index, 0.0)
            if amount <= 0:
                continue
            if var == "humidite":
                # Ombre réduit la transpiration
                light = self.lumiere.at_plot(r, c)
                shade_factor = 1.0 - shade_memory * 0.2
                amount *= (0.5 + light * 0.5) * shade_factor
                # Stress hydrique adaptatif (plante économise l'eau)
                amount *= max(0.5, 1.0 - drought_memory * 0.3)
            f = self.get_field(var)
            real = min(amount, f.at_plot(r, c))
            if real > 0:
                f.add(r, c, -real)
                consumed[var] = round(real, 3)
        return consumed

    # --- Probabilité de maladie (hybride probabiliste) ---

    def disease_probability(self, r: int, c: int, base_rate: float = 0.3) -> float:
        """
        Probabilité de propagation maladie — réponse logistique.

        La réponse logistique produit :
          microbiome faible  → presque aucune protection
          microbiome moyen   → phase critique (grande sensibilité)
          microbiome mature  → protection forte et stable

        logistic(x, k=6) = 1 / (1 + exp(-k*(x-0.5)))
        protection = logistic(microbiome_normalisé)
        p = base_rate * (1 - protection)
        """
        micro_norm = min(1.0, self.microbiome.at_plot(r, c) / 3.0)
        protection = 1.0 / (1.0 + math.exp(-6.0 * (micro_norm - 0.5)))
        return base_rate * max(0.02, 1.0 - protection)

    # --- Résumé ---

    def summary(self) -> dict:
        return {
            "humidite":    round(self.humidite.average(),         3),
            "fertilite":   round(self.fertilite.average(),        3),
            "microbiome":  round(self.microbiome.average(),       3),
            "organic_mat": round(self.organic_matter.average(),   3),
            "lumiere_moy": round(self.lumiere.average(),          3),
            "soil_fast":   round(self.soil_memory_fast.average(), 3),
            "soil_deep":   round(self.soil_memory_deep.average(), 3),
            "soil_memory": round(self.soil_memory.average(),      3),
            "disturbance": round(self.disturbance.average(),      3),
        }

    def __repr__(self) -> str:
        s = self.summary()
        return (f"EcoFields[{self.tile_id}] "
                f"hum={s['humidite']} fert={s['fertilite']} "
                f"micro={s['microbiome']} om={s['organic_mat']} "
                f"soil={s['soil_memory']}")

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def init_eco(tile_id: str, rows: int, cols: int,
             humidite: float = 0.0, fertilite: float = 0.0,
             microbiome: float = 0.0) -> EcoFields:
    eco = EcoFields(tile_id=tile_id, rows=rows, cols=cols)
    for r in range(rows):
        for c in range(cols):
            eco.humidite.set(r, c, humidite)
            eco.fertilite.set(r, c, fertilite)
            eco.microbiome.set(r, c, microbiome)
    return eco


def inject_patch(eco: EcoFields, variable: str,
                 center_row: int, center_col: int,
                 value: float, radius: int = 1) -> None:
    f = eco.get_field(variable)
    if f is None:
        return
    f.add(center_row, center_col, value)
    for nr, nc in f.hex_neighbors(center_row, center_col):
        if radius >= 1:
            f.add(nr, nc, value * 0.4)
