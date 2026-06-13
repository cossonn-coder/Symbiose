"""
SYMBIOSE — fields/seedbank.py
Banque de graines latente par plot (mémoire biologique invisible) : couche
archétypes de succession + couche espèce/génétique (D22, moyenne+variance).
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field

from fields.noise import _hash_noise, hash_gauss
from plants.genetics import clamp_gene

# ---------------------------------------------------------------------------
# CONSTANTES — archétypes & pool génétique
# ---------------------------------------------------------------------------

SEED_ARCHETYPES = ["pioneer", "nitrogen_fixer", "grass", "competitor"]

SEED_VIABILITY_LOSS = 0.998   # vieillissement hebdomadaire des graines
SEED_DISTURBANCE_GAIN = 0.002 # enrichissement par perturbation (pioneer surtout)
SEED_LATE_GAIN = 0.0008       # propagules vivaces tardives ∝ maturité (dispersion lente)
SEED_LATE_MIN_MATURITY = 0.2  # pas de propagules tardives sur sol jeune
SEED_COMPETITOR_MATURITY = 0.4 # competitor (le plus tardif) : sol déjà bien établi

# Pool génétique par espèce (D22) — couche posée PAR-DESSUS les archétypes.
SPECIES_SEED_VIABILITY_LOSS = 0.997   # vieillissement (densité) du pool génétique
SPECIES_POOL_MIN_DENSITY    = 0.005   # en-deçà : pool négligeable → gènes neutres


@dataclass
class GrainEnAttente:
    """
    Graine DÉPOSÉE par le joueur (geste `planter`), en attente de germination —
    structure DISTINCTE de la banque-sol agrégée (`SeedBank.species`). On ne la
    mélange PAS au pool moyenne/variance : ses gènes restent PROPRES (non
    moyennés), pour que semer une belle graine sélectionnée (D17/D22) ait un sens.

    Germination DIFFÉRÉE (conception §2.1, Q1) : la succession ordinaire la lève
    quand le plot est libre ET la niche favorable — on enseigne ainsi « le bon
    moment ». Levée telle quelle (pas de `sample_genes`).

    - `cultive` : tag « replanté » (B/Q5), posé au dépôt, transmis à la plante à
      la germination (`maitrise_detection.marquer_replante`) → cultivé vs féral.
    - `player`  : l'avatar qui a planté — la détection « replanté » est PAR
      AVATAR ; le grain porte son auteur pour créditer le bon joueur à la levée.
    - `semaine_depot` : trace du dépôt (FIFO sur plot : on lève le plus ancien).
    """
    species: str
    genes: dict = field(default_factory=dict)   # gènes PROPRES (de la Seed jouée)
    cultive: bool = True
    player: str = ""
    semaine_depot: int = 0


class GeneStat:
    """
    Distribution d'un gène en banque-sol pour une espèce × plot : moyenne +
    variance, mise à jour par Welford pondéré (poids = densité de graines
    déposées). La granularité « moyenne+variance par plot » a été actée le
    2026-06-03 (pas d'échantillons stockés).

    Le vieillissement décroît le poids uniformément (moyenne/variance
    inchangées) → les dépôts récents pèsent davantage : la lignée locale dérive.
    """
    __slots__ = ("mean", "var", "weight")

    def __init__(self, mean: float = 1.0, var: float = 0.0, weight: float = 0.0):
        self.mean = mean
        self.var = var
        self.weight = weight

    def add(self, x: float, w: float) -> None:
        if w <= 0.0:
            return
        S = self.var * self.weight
        nw = self.weight + w
        delta = x - self.mean
        self.mean += (w / nw) * delta
        S += w * delta * (x - self.mean)
        self.var = max(0.0, S / nw)
        self.weight = nw

    def decay(self, factor: float) -> None:
        self.weight *= factor

    def sample(self, seed: int, week: int, r: int, c: int, k: int = 0) -> float:
        return self.mean + hash_gauss(seed, week, r, c, k) * math.sqrt(self.var)


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
        # Couche espèce + génétique (D22), par-dessus les archétypes :
        # species[r][c] = dict classe → {"density": float, "genes": {gène: GeneStat}}
        self.species: list[list[dict]] = [
            [{} for _ in range(cols)] for _ in range(rows)
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

    # --- Couche espèce + génétique (D22) ---

    def add_species(self, r: int, c: int, plant_class: type,
                    density: float, genes: dict) -> None:
        """
        Dépose des graines d'une espèce (avec leur vecteur de gènes) au plot.
        Met à jour la distribution moyenne+variance de chaque gène, pondérée par
        la densité. C'est le pont « chute / mort → banque-sol » (génétique
        féral conservée au terrain).
        """
        cell = self.species[r][c]
        rec = cell.get(plant_class)
        if rec is None:
            rec = {"density": 0.0, "genes": {}}
            cell[plant_class] = rec
        rec["density"] += density
        for g, value in genes.items():
            stat = rec["genes"].get(g)
            if stat is None:
                stat = GeneStat()
                rec["genes"][g] = stat
            stat.add(value, density)

    def species_density(self, r: int, c: int, plant_class: type) -> float:
        rec = self.species[r][c].get(plant_class)
        return rec["density"] if rec else 0.0

    def sample_genes(self, r: int, c: int, plant_class: type,
                     seed: int, week: int) -> dict:
        """
        Tire un vecteur de gènes pour un semis spontané de cette espèce, à partir
        de la distribution locale (moyenne+variance). Pool négligeable → dict
        vide (gènes neutres 1.0, rétro-compatibilité totale).
        """
        rec = self.species[r][c].get(plant_class)
        if not rec or rec["density"] < SPECIES_POOL_MIN_DENSITY:
            return {}
        return {g: clamp_gene(stat.sample(seed, week, r, c, k=2 * i))
                for i, (g, stat) in enumerate(rec["genes"].items())}

    def tick_species_aging(self) -> None:
        """Vieillissement du pool génétique (densité), purge des pools épuisés."""
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.species[r][c]
                dead = []
                for cls, rec in cell.items():
                    rec["density"] *= SPECIES_SEED_VIABILITY_LOSS
                    for stat in rec["genes"].values():
                        stat.decay(SPECIES_SEED_VIABILITY_LOSS)
                    if rec["density"] < 1e-4:
                        dead.append(cls)
                for cls in dead:
                    del cell[cls]

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
