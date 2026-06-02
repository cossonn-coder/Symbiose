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

# Cycle biogéochimique — OM v4 tri-compartiment (cascade fresh → active → stable)
# Taux de décomposition hebdomadaire par compartiment (avant modulation microbiome).
OM_FRESH_DECAY   = 0.080   # débris récents / sucres : rapide (semaines)
OM_ACTIVE_DECAY  = 0.018   # MO partiellement digérée : vitesse moyenne (mois)
OM_STABLE_DECAY  = 0.0006  # humus : très lent (décennies)

# Devenir de la masse décomposée de chaque compartiment.
# Trois destinations : humification (→ compartiment suivant), minéralisation
# (→ fertilite), respiration (→ CO₂, perte nette). Les trois somment à 1.0 :
# aucune création de matière, le reste est respiré.
OM_FRESH_HUMIF   = 0.45    # fresh → active
OM_FRESH_MINER   = 0.25    # fresh → fertilite
OM_ACTIVE_HUMIF  = 0.25    # active → stable
OM_ACTIVE_MINER  = 0.45    # active → fertilite (minéralisation principale)
OM_STABLE_MINER  = 0.40    # stable → fertilite (minéralisation lente)

LEACHING_LOSS    = 0.999   # lessivage nutriments (perte fertilite/semaine)
BIOMASS_EXPORT   = 0.20    # fraction exportée à la récolte (le reste = nécromasse)

# Puits microbien — mortalité modulée par la disponibilité de carbone frais.
# Sans nourriture (om_fresh bas), les microbes respirent leurs réserves et
# meurent : le microbiome devient un solde apports (exsudats/OM) − pertes.
MICROBE_FOOD_REF  = 1.0    # om_fresh au-dessus duquel les microbes sont rassasiés
MICROBE_DECAY_MAX = 0.006  # déclin hebdomadaire max du microbiome à famine totale

# Boucle rhizosphère — exsudats racinaires (chantier A)
EXUDATE_BASE     = 0.060   # dépôt total à pleine photosynthèse (microbiome + om_fresh)
EXUDATE_OM_SHARE = 0.15    # part de l'exsudat versée à om_fresh (le reste → microbiome)
UPTAKE_MICRO_BONUS = 0.40  # bonus d'uptake fertilité à microbiome saturé (rétroaction)

# Vitalité dérivée — pondérations (cf. vitalite()), somme des positifs = 1.0
VIT_W_MICRO     = 0.35
VIT_W_ACTIVE    = 0.25
VIT_W_FERT      = 0.20
VIT_W_STRUCTURE = 0.20
VIT_W_DISTURB   = 0.15     # pénalité (soustraite)

# Soil memory
SOIL_FAST_RATE   = 0.15    # intégration rapide (annuelle)
SOIL_DEEP_RATE   = 0.02    # intégration lente (décennale)

# Perturbations écologiques
MORTALITY_RATE      = 0.010   # probabilité d'affaiblissement spontané/semaine
HERBIVORY_BASE      = 0.020   # pression herbivore de base
DISTURBANCE_INERTIA = 0.900   # inertie du champ de perturbation spatial
CLIMATE_AMPLITUDE   = 0.080   # amplitude oscillation climatique de fond

# Mortalité réaliste (D27) — sénescence + santé dynamique
SENESCENCE_ONSET = 0.70   # début du déclin (× longévité)
SEN_RATE         = 0.04   # pente de la pression de sénescence (proba/sem à sen=1)
HEAL_RATE        = 0.06   # proba de remontée de santé/sem en bon milieu (Q=1)
HEAL_SEN_CUTOFF  = 0.50   # au-delà de cette sénescence, la guérison se coupe

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

# --- Éclairement astronomique (LightField v2 — ombres-capsules analytiques) ---
PLOT_CM      = 50.0          # 1 plot = 50 cm (aligné models.PLOT_CM)
LATITUDE_DEG = 49.0          # ~Normandie / 49°N
LIGHT_FLOOR  = 0.15          # plancher de lumière diffuse (rien ne descend à 0)

# Déclinaison solaire par saison (équinoxes ≈ 0°, solstices ≈ ±23.4°)
SOLAR_DECLINATION = {"printemps": 0.0, "ete": 23.4, "automne": 0.0, "hiver": -23.4}

# Trois tranches diurnes éclairées (la nuit n'apporte que le plancher diffus).
# Angle horaire H : 0 = midi solaire, négatif le matin, positif le soir.
SOLAR_HOUR_ANGLES = (-45.0, 0.0, 45.0)   # matin · midi · soir

# Échantillons sous la canopée d'une plante pour moyenner sa lumière reçue
# (centre + 4 points à 0.6·rayon) — capte l'ombrage partiel d'un voisin plus haut.
CANOPY_SAMPLE_FRAC = 0.6

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
# LIGHTFIELD v2 — ombres-capsules astronomiques (analytique, pixel-libre)
# ---------------------------------------------------------------------------

def solar_slice(decl_deg: float, hour_angle_deg: float,
                lat_deg: float = LATITUDE_DEG):
    """
    Position solaire pour une (déclinaison, angle horaire) → caractéristiques de
    l'ombre projetée, dans le repère sol top-down (x = Est, y = Sud, Nord en haut).

    Retourne (shadow_dx, shadow_dy, inv_tan, weight) où (shadow_dx, shadow_dy)
    est la direction unitaire de l'ombre, inv_tan = 1/tan(élévation) (longueur
    d'ombre = hauteur × inv_tan), weight = sin(élévation) (intensité solaire).
    Retourne None si le soleil est sous l'horizon (tranche non éclairée).
    """
    phi = math.radians(lat_deg)
    dec = math.radians(decl_deg)
    H   = math.radians(hour_angle_deg)

    sin_elev = math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(H)
    if sin_elev <= 1e-3:
        return None                      # soleil sous l'horizon
    elev = math.asin(max(-1.0, min(1.0, sin_elev)))
    cos_elev = math.cos(elev)

    # Azimut depuis le Nord, sens horaire (90°=Est, 180°=Sud, 270°=Ouest).
    cos_az = (math.sin(dec) - sin_elev * math.sin(phi)) / (cos_elev * math.cos(phi))
    az = math.acos(max(-1.0, min(1.0, cos_az)))
    if hour_angle_deg > 0.0:             # après-midi → soleil à l'Ouest
        az = 2.0 * math.pi - az

    # L'ombre pointe à l'opposé du soleil. Sol : x=Est, y=Sud (donc Nord = -y).
    shadow_dx = -math.sin(az)
    shadow_dy =  math.cos(az)            # midi (az=π) → (0,-1) = vers le Nord (haut)
    inv_tan = cos_elev / sin_elev
    return (shadow_dx, shadow_dy, inv_tan, sin_elev)


def _point_in_capsule(px: float, py: float,
                      cx: float, cy: float,
                      dx: float, dy: float, length: float, radius: float) -> bool:
    """Le point (px,py) est-il dans la capsule = disque de rayon `radius` glissé
    du centre C=(cx,cy) le long de (dx,dy)·length ? (distance au segment ≤ rayon)"""
    bx = cx + dx * length
    by = cy + dy * length
    abx = bx - cx
    aby = by - cy
    ab2 = abx * abx + aby * aby
    if ab2 <= 1e-9:
        t = 0.0
    else:
        t = (px - cx) * abx + (py - cy) * aby
        t = 0.0 if t < 0.0 else (ab2 if t > ab2 else t) / ab2
    qx = cx + abx * t
    qy = cy + aby * t
    return (px - qx) ** 2 + (py - qy) ** 2 <= radius * radius


class LightField(GridField):
    """
    Champ de lumière v2 — ombres-capsules astronomiques calculées analytiquement
    (pas de raster pixel : on évalue la lumière aux seuls points utiles).

    Deux produits par tick :
      • lumière-sol par plot (grille héritée, lue via at_plot) → germination, niche,
        banque de graines ; subit TOUTES les ombres + plancher diffus.
      • lumière reçue par plante (self.received, via light_received) → photosynthèse
        et avancement de stade ; filtrée par les seuls voisins PLUS HAUTS (l'algo
        tri-hauteur-décroissante exclut l'auto-ombrage).

    Cumul multiplicatif des opacités (foliage_density), intégrale journalière =
    moyenne des tranches éclairées pondérée par l'intensité solaire (sin élévation).
    """

    def __init__(self, rows: int, cols: int):
        super().__init__(rows, cols, initial=1.0, max_val=1.0)
        self.received: dict[int, float] = {}
        self._sun_cache: dict[str, list] = {}

    def _sun_slices(self, saison: str) -> list:
        """Tranches éclairées (cachées) pour la saison : liste de
        (shadow_dx, shadow_dy, inv_tan, weight)."""
        slices = self._sun_cache.get(saison)
        if slices is None:
            decl = SOLAR_DECLINATION.get(saison, 0.0)
            slices = [s for H in SOLAR_HOUR_ANGLES
                      if (s := solar_slice(decl, H)) is not None]
            self._sun_cache[saison] = slices
        return slices

    def light_received(self, plant) -> float:
        """Intégrale journalière de lumière reçue par la plante (défaut plein soleil)."""
        return self.received.get(id(plant), 1.0)

    def compute(self, plants: list, saison: str) -> list[str]:
        """Recalcule lumière-sol (grille) + lumière reçue par plante pour ce tick."""
        slices = self._sun_slices(saison)
        alive = [p for p in plants if p.is_alive]

        # Snapshot géométrique de chaque plante : (plante, x, y, hauteur, rayon, densité)
        infos = []
        for p in alive:
            cls = p.plant_class
            infos.append((p, p.x_cm, p.y_cm, p.current_height,
                          cls.canopy_radius_at(p), cls.foliage_density_at(p, saison)))

        self.received = {}
        if not slices:                       # nuit polaire théorique : plancher partout
            for r in range(self.rows):
                for c in range(self.cols):
                    self.data[r][c] = LIGHT_FLOOR
            for p, *_ in infos:
                self.received[id(p)] = LIGHT_FLOOR
            return []

        total_w = sum(w for _, _, _, w in slices)

        # --- Lumière reçue par plante (ombres des seuls voisins plus hauts) ---
        order = sorted(infos, key=lambda t: t[3], reverse=True)  # plus haut → plus bas
        for p, px, py, ph, pr, pd in infos:
            d = pr * CANOPY_SAMPLE_FRAC
            samples = ((px, py), (px + d, py), (px - d, py), (px, py + d), (px, py - d))
            acc = 0.0
            for sdx, sdy, inv_tan, w in slices:
                att_sum = 0.0
                for sx, sy in samples:
                    att = 1.0
                    for q, qx, qy, qh, qr, qd in order:
                        if qh <= ph:
                            break            # le reste est plus court ou égal → pas d'ombre
                        if qd <= 0.0:
                            continue
                        if _point_in_capsule(sx, sy, qx, qy, sdx, sdy, qh * inv_tan, qr):
                            att *= (1.0 - qd)
                    att_sum += att
                light_slice = max(LIGHT_FLOOR, att_sum / len(samples))
                acc += light_slice * w
            self.received[id(p)] = acc / total_w

        # --- Lumière-sol par plot (toutes les ombres + plancher) ---
        for r in range(self.rows):
            cy = r * PLOT_CM + PLOT_CM / 2
            for c in range(self.cols):
                cx = c * PLOT_CM + PLOT_CM / 2
                acc = 0.0
                for sdx, sdy, inv_tan, w in slices:
                    att = 1.0
                    for q, qx, qy, qh, qr, qd in infos:
                        if qd <= 0.0:
                            continue
                        if _point_in_capsule(cx, cy, qx, qy, sdx, sdy, qh * inv_tan, qr):
                            att *= (1.0 - qd)
                    acc += att * w
                self.data[r][c] = max(LIGHT_FLOOR, acc / total_w)
        return []

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
SEED_LATE_GAIN = 0.0008       # propagules vivaces tardives ∝ maturité (dispersion lente)
SEED_LATE_MIN_MATURITY = 0.2  # pas de propagules tardives sur sol jeune
SEED_COMPETITOR_MATURITY = 0.4 # competitor (le plus tardif) : sol déjà bien établi


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

    def tick_late_succession_enrichment(self,
                                        soil_deep_field: "GridField") -> None:
        """
        Sol mûr → arrivée lente de propagules vivaces (dispersion vent/oiseaux
        qui n'aboutit que quand le milieu est prêt). Symétrique de
        tick_disturbance_enrichment (qui n'amorce que pioneer).

        Trickle faible ∝ maturité (soil_memory_deep) :
          - fixatrice + graminée dès qu'un sol commence à s'établir
          - competitor (archétype le plus tardif) seulement sur sol bien mûr
        Sans cet amorçage, les vivaces n'ont aucune source de départ dans la
        banque et le gradient de choix n'a rien à choisir.
        """
        for r in range(self.rows):
            for c in range(self.cols):
                m = soil_deep_field.at_plot(r, c)
                if m < SEED_LATE_MIN_MATURITY:
                    continue
                self.add(r, c, "nitrogen_fixer", m * SEED_LATE_GAIN)
                self.add(r, c, "grass",          m * SEED_LATE_GAIN)
                self.add(r, c, "competitor",
                         max(0.0, m - SEED_COMPETITOR_MATURITY) * SEED_LATE_GAIN)

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
    om_fresh:         GridField = field(default=None)   # débris récents / exsudats (rapide)
    om_active:        GridField = field(default=None)   # MO partiellement digérée (réserve)
    om_stable:        GridField = field(default=None)   # humus (structure, rétention, mémoire)
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
        if self.om_fresh is None:
            self.om_fresh  = GridField(self.rows, self.cols, initial=0.0, max_val=10.0)
        if self.om_active is None:
            self.om_active = GridField(self.rows, self.cols, initial=0.0, max_val=10.0)
        if self.om_stable is None:
            self.om_stable = GridField(self.rows, self.cols, initial=0.0, max_val=10.0)
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
            "om_fresh":         self.om_fresh,
            "om_active":        self.om_active,
            "om_stable":        self.om_stable,
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
        self.seed_bank.tick_late_succession_enrichment(self.soil_memory_deep)
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
                om    = min(1.0, (self.om_fresh.at_plot(r, c) +
                                  self.om_active.at_plot(r, c) +
                                  self.om_stable.at_plot(r, c)) / 5.0)

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
        Cycle biogéochimique hebdomadaire — cascade OM v4 (fresh → active → stable).

        Chaque compartiment se décompose à son propre rythme, modulé par le
        microbiome (sol vivant = recyclage rapide). La masse décomposée se
        répartit en trois : humification (compartiment suivant), minéralisation
        (→ fertilite), respiration (CO₂, perte nette). Aucune création de matière.

          fresh  ──décompose──┬─ humifie → active
                              ├─ minéralise → fertilite
                              └─ respire (perdu)
          active ──décompose──┬─ humifie → stable
                              ├─ minéralise → fertilite (∝ microbiome)
                              └─ respire (perdu)
          stable ──décompose──┬─ minéralise → fertilite
                              └─ respire (perdu)

        Puis lessivage lent de la fertilité.
        """
        for r in range(self.rows):
            for c in range(self.cols):
                micro = self.microbiome.at_plot(r, c) / 3.0
                speed = 0.5 + micro * 0.5   # sol vivant décompose jusqu'à 2× plus vite

                fresh  = self.om_fresh.data[r][c]
                active = self.om_active.data[r][c]
                stable = self.om_stable.data[r][c]

                # 1. Fresh
                d_fresh = fresh * OM_FRESH_DECAY * speed
                # 2. Active
                d_active = active * OM_ACTIVE_DECAY * speed
                # 3. Stable
                d_stable = stable * OM_STABLE_DECAY * speed

                self.om_fresh.add(r, c, -d_fresh)
                self.om_active.add(r, c, -d_active + d_fresh * OM_FRESH_HUMIF)
                self.om_stable.add(r, c, -d_stable + d_active * OM_ACTIVE_HUMIF)

                released = (d_fresh  * OM_FRESH_MINER +
                            d_active * OM_ACTIVE_MINER +
                            d_stable * OM_STABLE_MINER)
                self.fertilite.add(r, c, released)

                # Puits microbien : sans carbone frais, les microbes meurent.
                # famine ∈ [0,1] : nulle si om_fresh abondant, maximale si épuisé.
                famine = 1.0 - min(1.0, fresh / MICROBE_FOOD_REF)
                if famine > 0.0:
                    self.microbiome.data[r][c] *= (1.0 - MICROBE_DECAY_MAX * famine)

                # Lessivage nutriments
                self.fertilite.data[r][c] *= LEACHING_LOSS

    def add_necromass(self, r: int, c: int,
                      biomass: float, harvested: bool = False) -> float:
        """
        Ajoute de la nécromasse au plot lors d'une mort ou récolte.
        harvested=True : une fraction est exportée (récolte) → moins de retour sol.
        Retourne la quantité effectivement déposée.
        """
        # Récolte exporte BIOMASS_EXPORT, mort laisse tout sur place.
        # La nécromasse fraîche entre par le compartiment fresh (cascade ensuite).
        export_fraction = BIOMASS_EXPORT if harvested else 0.0
        deposited = biomass * (1.0 - export_fraction)
        self.om_fresh.add(r, c, deposited)
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
                      drought_memory: float = 0.0,
                      share: float = 1.0) -> dict[str, float]:
        """
        Consommation racinaire modulée par la mémoire physiologique.

        shade_memory  → réduit la transpiration (plante étiolée, moins de surface foliaire)
        drought_memory → réduit la consommation d'eau (racines adaptées, stomates fermés)
        share         → fraction prélevée sur CE plot (1/nb plots de l'empreinte
                        racinaire), pour répartir l'uptake sur root_plots sans
                        multiplier la quantité totale (chantier B).

        Rétroaction rhizosphère : un microbiome riche améliore l'assimilation des
        nutriments (bonus borné UPTAKE_MICRO_BONUS) — la boucle vertueuse côté plante.
        """
        micro_norm = min(1.0, self.microbiome.at_plot(r, c) / 3.0)
        consumed = {}
        for var, by_stage in UPTAKE.items():
            amount = by_stage.get(stage_index, 0.0) * share
            if amount <= 0:
                continue
            if var == "humidite":
                # Ombre réduit la transpiration
                light = self.lumiere.at_plot(r, c)
                shade_factor = 1.0 - shade_memory * 0.2
                amount *= (0.5 + light * 0.5) * shade_factor
                # Stress hydrique adaptatif (plante économise l'eau)
                amount *= max(0.5, 1.0 - drought_memory * 0.3)
            elif var == "fertilite":
                # Microbiome riche → meilleure assimilation des nutriments
                amount *= 1.0 + micro_norm * UPTAKE_MICRO_BONUS
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

    # --- Vitalité (grandeur dérivée, non stockée) ---

    def vitalite(self, r: int, c: int) -> float:
        """
        Vitalité du sol en un plot — grandeur DÉRIVÉE calculée à la demande,
        jamais stockée (décision #2 : le Qi territorial = les champs existants).

        Synthèse lisible de la santé du sol vivant : vie microbienne, réserve de
        fertilité (om_active + fertilite), structure (humus), moins la perturbation.
        Bornée [0, 1]. Préfigure la Vigueur (D11) que plantes et joueur puiseront.
        """
        micro     = min(1.0, self.microbiome.at_plot(r, c) / 3.0)
        active    = min(1.0, self.om_active.at_plot(r, c) / 5.0)
        fert      = min(1.0, self.fertilite.at_plot(r, c) / 3.0)
        structure = min(1.0, self.om_stable.at_plot(r, c) / 5.0)
        disturb   = self.disturbance.at_plot(r, c)
        v = (micro     * VIT_W_MICRO +
             active    * VIT_W_ACTIVE +
             fert      * VIT_W_FERT +
             structure * VIT_W_STRUCTURE -
             disturb   * VIT_W_DISTURB)
        return max(0.0, min(1.0, v))

    def vitalite_average(self) -> float:
        n = self.rows * self.cols
        if not n:
            return 0.0
        total = sum(self.vitalite(r, c)
                    for r in range(self.rows) for c in range(self.cols))
        return total / n

    # --- Résumé ---

    def summary(self) -> dict:
        om_total = (self.om_fresh.average() +
                    self.om_active.average() +
                    self.om_stable.average())
        return {
            "humidite":    round(self.humidite.average(),         3),
            "fertilite":   round(self.fertilite.average(),        3),
            "microbiome":  round(self.microbiome.average(),       3),
            "om_fresh":    round(self.om_fresh.average(),         3),
            "om_active":   round(self.om_active.average(),        3),
            "om_stable":   round(self.om_stable.average(),        3),
            "organic_mat": round(om_total,                        3),
            "lumiere_moy": round(self.lumiere.average(),          3),
            "soil_fast":   round(self.soil_memory_fast.average(), 3),
            "soil_deep":   round(self.soil_memory_deep.average(), 3),
            "soil_memory": round(self.soil_memory.average(),      3),
            "disturbance": round(self.disturbance.average(),      3),
            "vitalite":    round(self.vitalite_average(),         3),
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
