"""
SYMBIOSE — fields/seedbank.py
Banque de graines latente par plot (mémoire biologique invisible) : couche
archétypes de succession + couche espèce/génétique (D22, moyenne+variance).
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field

from fields.noise import _hash_noise, hash_gauss, stable_str_hash
from plants.genetics import clamp_gene, GENE_NAMES, GENE_INIT_SIGMA

# ---------------------------------------------------------------------------
# CONSTANTES — archétypes & pool génétique
# ---------------------------------------------------------------------------

SEED_ARCHETYPES = ["pioneer", "nitrogen_fixer", "grass", "competitor"]

SEED_VIABILITY_LOSS = 0.998   # vieillissement hebdomadaire des graines
SEED_DISTURBANCE_GAIN = 0.002 # enrichissement par perturbation (pioneer surtout)

# Accélération du vieillissement des graines ENFOUIES sous le mulch (sprint
# équilibre invasion ③, D69). Miroir de `PAILLAGE_AGING_BOOST` d'ecofields, mais
# défini ICI en littéral : la couche `fields/seedbank` n'importe pas `fields.ecofields`
# (règle de couches — c'est ecofields qui importe seedbank). Sous un mulch plein, la
# viabilité chute selon `SEED_VIABILITY_LOSS ** (1 + SEED_AGING_BOOST · paillage)` →
# épuisement DURABLE de la banque locale (mulcher longtemps vide le stock enfoui,
# philo #2 : flux mulch → contrainte → moins de recrutement féral). Paillage=0
# (golden) → exposant 1 → vieillissement STRICTEMENT inchangé. PLACEHOLDER, calibrage.
SEED_AGING_BOOST = 1.0

# --- Facilitation OM des tardifs (tronçon ②, déverrouillage S3) --------------
# Les propagules vivaces tardives (fixatrice/graminée/competitor) n'entraient en
# banque QUE via un gate `soil_memory_deep ≥ 0.2` (dynamique DÉCENNALE, jamais
# atteinte avant ~15 ans) → seul pioneer alimentait la banque → monoculture
# Capsella qui « bloque la germination » (S3). On remplace ce gate par un indice
# de matière organique RÉACTIF, réellement bâti par les pionnières (humus + MO
# active), qui monte en QUELQUES saisons. C'est la facilitation écologique
# (philo #2 : flux OM → contrainte → réponse), pas un script de bascule.
#
#   om_index = clamp((om_active + om_stable) / OM_FACILITATION_REF, 0, 1)
#
# REF = 2.0 : om_active+om_stable démarre ~0.15 (humus de fond D56) → om_index
# ~0.075 (>SEED_OM_FIXER_GRASS_MIN dès le départ sur la plupart des plots, plus
# tard sur les secteurs pauvres — hétérogénéité D56, philo #7) ; il atteint ~0.55
# en 2 ans sous couvert → om_index ~0.27 (>SEED_OM_COMPETITOR_MIN) et jusqu'à
# 2-4 sur les plots riches (plafond 1.0). Calibré pour une bascule en ~5-15 ans
# selon le secteur (placeholder, calibrage F5/banc `succession_bascule`).
SEED_LATE_GAIN = 0.01         # apport vivaces tardives ∝ om_index (accumulation réelle)
SEED_OM_FACILITATION_REF = 2.0 # dénominateur de l'indice OM (échelle om_active+om_stable)
SEED_OM_FIXER_GRASS_MIN = 0.05 # om_index minimal pour amorcer fixatrice + graminée
SEED_OM_COMPETITOR_MIN = 0.20  # om_index minimal pour amorcer competitor (le plus tardif)

# Pool génétique par espèce (D22) — couche posée PAR-DESSUS les archétypes.
SPECIES_SEED_VIABILITY_LOSS = 0.997   # vieillissement (densité) du pool génétique
SPECIES_POOL_MIN_DENSITY    = 0.005   # en-deçà : pool négligeable → gènes neutres

# Densité d'ensemencement du pool FONDATEUR (sprint DIVERSITÉ FONDATRICE ①). Posée
# à l'init des tuiles-monde (`seed_founder_pool`) pour chaque espèce d'adventice ×
# plot : un peu AU-DESSUS de SPECIES_POOL_MIN_DENSITY → `sample_genes` mord dès le
# départ (une vraie banque de graines du sol n'est jamais génétiquement uniforme,
# philo #4). La `var` posée (= GENE_INIT_SIGMA²) donne à la sélection darwinienne
# (germ. thermique, désynchro florale) de quoi dériver sans attendre N générations.
FOUNDER_POOL_DENSITY = 0.02


def founder_genes(plant_class: type, seed: int, week: int,
                  r: int, c: int, x_cm: float, y_cm: float) -> dict:
    """
    Vecteur de gènes FONDATEUR d'une plante née SANS lignée (semis direct de démo,
    graine `planter` sans hérédité, germination férale sur pool vide) — sprint
    DIVERSITÉ FONDATRICE ①. Active enfin `GENE_INIT_SIGMA` (défini mais jamais
    utilisé) : chaque gène est tiré ~ N(1.0, GENE_INIT_SIGMA²) de façon DÉTERMINISTE
    (philo #3, zéro RNG), de sorte que deux plantes fondatrices ne soient plus des
    CLONES neutres. La mutation par génération (`sim.reproduction.child_genes`)
    prend ensuite le relais — on ne touche pas à celle-ci.

    Canal de hash DÉCORRÉLÉ par (espèce, gène, POSITION CONTINUE, semaine) : le nom
    de classe (`stable_str_hash`) sépare deux espèces au même plot ; `x_cm/y_cm`
    séparent deux individus de MÊME espèce partageant un plot (compétition
    intra-plot, positions continues — correctif B) ; l'index de gène et `week`
    décorrèlent gènes et cohortes. Vit en couche `fields` (accès `hash_gauss`), pas
    en `genetics.py` (fondation pure, sans accès au bruit).
    """
    base = stable_str_hash(plant_class.__name__)
    genes = {}
    for i, g in enumerate(GENE_NAMES):
        z = hash_gauss(seed, week * 31 + i, r, c,
                       k=base + i * 7 + int(x_cm) + int(y_cm) * 13)
        genes[g] = clamp_gene(1.0 + z * GENE_INIT_SIGMA)
    return genes


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
    expression: dict = field(default_factory=dict)  # priming hérité (④) — voyage avec la graine
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

    def tick_aging(self, paillage_field: "GridField | None" = None) -> None:
        """Vieillissement hebdomadaire — perte lente de viabilité.

        `paillage_field` (sprint équilibre invasion ③, D69) : si fourni, le mulch du
        plot ACCÉLÈRE le vieillissement des graines enfouies — la banque locale
        s'épuise là où l'on maintient un paillage (`SEED_VIABILITY_LOSS ** (1 +
        SEED_AGING_BOOST · paillage)`). Paillage=0 (ou champ absent, appels legacy) →
        exposant 1 → vieillissement STRICTEMENT inchangé → golden INTACT. On ne calcule
        l'exposant que sur les plots RÉELLEMENT mulchés (court-circuit au repos)."""
        for r in range(self.rows):
            for c in range(self.cols):
                loss = SEED_VIABILITY_LOSS
                if paillage_field is not None:
                    mulch = paillage_field.at_plot(r, c)
                    if mulch > 0.0:
                        loss = SEED_VIABILITY_LOSS ** (1.0 + SEED_AGING_BOOST * mulch)
                for a in SEED_ARCHETYPES:
                    self.data[r][c][a] *= loss

    def tick_disturbance_enrichment(self,
                                    disturbance_field: "DisturbanceField",
                                    om_index_field: "GridField") -> None:
        """Sol perturbé → enrichissement en graines pionnières, BRIDÉ par la
        maturité OM du plot (tronçon ②, fix (b) de S3).

            pioneer_gain = disturbance · SEED_DISTURBANCE_GAIN · (1 − om_index)

        Sur sol nu (`om_index ≈ 0`) le pioneer afflue comme avant ; sur sol bâti
        par les pionnières (`om_index → 1`) il se tarit → le tapis Capsella cesse
        de se sur-alimenter et laisse la place aux tardifs. La bascule ÉMERGE de
        ce flux OM (philo #2), rien n'est scripté."""
        for r in range(self.rows):
            for c in range(self.cols):
                d = disturbance_field.at_plot(r, c)
                om = om_index_field.at_plot(r, c)
                self.add(r, c, "pioneer",
                         d * SEED_DISTURBANCE_GAIN * max(0.0, 1.0 - om))

    def tick_late_succession_enrichment(self,
                                        om_index_field: "GridField") -> None:
        """
        Sol bâti → arrivée de propagules vivaces (dispersion vent/oiseaux qui
        n'aboutit que quand le milieu est prêt). Symétrique de
        tick_disturbance_enrichment (qui n'amorce que pioneer).

        Facilitation écologique (tronçon ②, fix (a) de S3) : l'amorçage suit un
        indice de MATIÈRE ORGANIQUE réactif (`om_index`, bâti en quelques saisons
        par les pionnières), et non plus `soil_memory_deep` (décennal, jamais
        atteint → verrou). Apport ∝ om_index (les tardifs affluent d'autant plus
        que le sol est riche) :
          - fixatrice + graminée dès `om_index ≥ SEED_OM_FIXER_GRASS_MIN` ;
          - competitor (le plus tardif) dès `om_index ≥ SEED_OM_COMPETITOR_MIN`.
        Sans cet amorçage, les vivaces n'ont aucune source de départ dans la
        banque et le gradient de choix n'a rien à choisir (cf. S3).
        """
        for r in range(self.rows):
            for c in range(self.cols):
                om = om_index_field.at_plot(r, c)
                if om < SEED_OM_FIXER_GRASS_MIN:
                    continue
                self.add(r, c, "nitrogen_fixer", om * SEED_LATE_GAIN)
                self.add(r, c, "grass",          om * SEED_LATE_GAIN)
                if om >= SEED_OM_COMPETITOR_MIN:
                    self.add(r, c, "competitor", om * SEED_LATE_GAIN)

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
                    density: float, genes: dict, expression: dict | None = None) -> None:
        """
        Dépose des graines d'une espèce (avec leur vecteur de gènes) au plot.
        Met à jour la distribution moyenne+variance de chaque gène, pondérée par
        la densité. C'est le pont « chute / mort → banque-sol » (génétique
        féral conservée au terrain).

        Priming transgénérationnel (plasticité ④) : `expression` porte l'état
        d'alerte HÉRITÉ de la mère (`child_expression`, déjà atténué par
        `PRIMING_FRAC`). On l'agrège en MOYENNE pondérée par densité, à côté des
        gènes (réutilise `GeneStat`, variance ignorée — un état d'expression n'est
        pas un tirage). C'est ainsi que « l'expression voyage avec la graine » :
        le plot se souvient du niveau d'endurcissement moyen des mères qui y ont
        grené (philo #4). Absent (None / mortes d'avant le ④) ⇒ rien stocké ⇒
        germination au neutre (rétro-compatible).
        """
        cell = self.species[r][c]
        rec = cell.get(plant_class)
        if rec is None:
            rec = {"density": 0.0, "genes": {}, "expression": {}}
            cell[plant_class] = rec
        rec.setdefault("expression", {})       # rec d'avant ④ (save legacy)
        rec["density"] += density
        for g, value in genes.items():
            stat = rec["genes"].get(g)
            if stat is None:
                stat = GeneStat()
                rec["genes"][g] = stat
            stat.add(value, density)
        if expression:
            for g, value in expression.items():
                stat = rec["expression"].get(g)
                if stat is None:
                    stat = GeneStat()
                    rec["expression"][g] = stat
                stat.add(value, density)

    def seed_founder_pool(self, r: int, c: int, plant_class: type,
                          sigma: float, density: float) -> None:
        """
        ENSEMENCE la banque-sol fondatrice (sprint DIVERSITÉ FONDATRICE ①, option A)
        d'une espèce sur un plot : pose directement, pour CHAQUE gène de GENE_NAMES,
        un `GeneStat(mean=1.0, var=sigma², weight=density)`. Aucune moyenne à faire
        (banque vierge) → on écrit la distribution voulue en une passe.

        Effet : dès le tick 0, `sample_genes` tire avec une VARIANCE immédiate
        (`density > SPECIES_POOL_MIN_DENSITY`) — la germination férale n'est plus
        clonale, et la sélection darwinienne (`_germ_gene_mean`) a de quoi mordre
        sans attendre N générations. `mean=1.0` : le pool part CENTRÉ (pas de biais),
        seule la variance est fondatrice. Idempotent au sens où deux appels
        cumuleraient la densité (on n'appelle qu'une fois, à l'init).
        """
        cell = self.species[r][c]
        rec = cell.get(plant_class)
        if rec is None:
            rec = {"density": 0.0, "genes": {}, "expression": {}}
            cell[plant_class] = rec
        rec["density"] += density
        var = sigma * sigma
        for g in GENE_NAMES:
            rec["genes"][g] = GeneStat(mean=1.0, var=var, weight=density)

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

    def sample_expression(self, r: int, c: int, plant_class: type) -> dict:
        """
        État d'EXPRESSION initial d'un semis spontané (priming transgénérationnel,
        plasticité ④). Lit la MOYENNE primée stockée par `add_species` — lecture
        DÉTERMINISTE sans bruit (un priming est un état hérité, pas un tirage
        génotypique). Pool négligeable ou aucune expression déposée (mères d'avant
        le ④) ⇒ dict vide ⇒ la plante garde son expression neutre par défaut.
        """
        rec = self.species[r][c].get(plant_class)
        if not rec or rec["density"] < SPECIES_POOL_MIN_DENSITY:
            return {}
        return {g: stat.mean for g, stat in rec.get("expression", {}).items()}

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
                    for stat in rec.get("expression", {}).values():
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
                               niche: float,
                               light: float = 0.0,
                               arch_tolerance: dict | None = None,
                               arch_ph: dict | None = None,
                               arch_temp: dict | None = None,
                               arch_allelo: dict | None = None) -> list[str]:
        """
        Tirage déterministe des archétypes qui germent sur ce plot.
        hash(seed, week, r, c) < niche * seed_density → germination.
        Retourne la liste des archétypes qui passent le seuil.

        Compétition intra-plot (Q6) : si `arch_tolerance` est fourni (map
        archétype → tolérance à l'ombre de l'espèce), la lumière requise est
        ESCOMPTÉE par espèce. La niche varie ∝ lumière (`niche_index`) ; on
        substitue la lumière effective `light_eff = min(1, light × tolérance)` :
        un sciaphile « voit » plus de lumière qu'il n'y en a (lève à l'ombre),
        un héliophile en voit moins (ne lève pas sous canopée). `arch_tolerance`
        absent ⇒ comportement historique (rétro-compatible).

        Fenêtre pH (tronçon ⑤) : si `arch_ph` est fourni (map archétype → cloche
        `bell(ph_local, ph_opt, ph_tol)` ∈ ]0,1] de l'espèce au pH du plot), la
        niche est multipliée par ce facteur — une espèce HORS fenêtre ne s'installe
        pas (porte). Défaut d'espèce NEUTRE (`ph_tol` large) ⇒ facteur ≈ 1.0 ⇒
        quasi rétro-compatible. `arch_ph` absent ⇒ comportement historique.

        Fenêtre thermique (tronçon ②) : si `arch_temp` est fourni (map archétype →
        cloche `bell(T_sol_local, t_germ_opt, t_germ_tol)` ∈ ]0,1] de l'espèce), la niche
        est multipliée par ce facteur — patron symétrique à `arch_ph`. Défaut d'espèce
        NEUTRE (`t_germ_tol` large) ⇒ facteur ≈ 1.0 ⇒ golden INTACT au ②. Absent ⇒
        comportement historique.

        Inhibition ALLÉLOPATHIQUE (sprint ALLÉLOPATHIE ②) : si `arch_allelo` est fourni
        (map archétype → `f_allelo ∈ [0,1]` de l'espèce, = `1 − sensibilité · rampe`
        déjà calculé côté appelant à partir de la concentration `allelopathie` du plot),
        la niche est multipliée par ce facteur — patron symétrique à `arch_ph`/`arch_temp`.
        Un fort chargement d'allélochimiques referme la niche des candidats sensibles
        (pas de levée) ; champ nul ⇒ `f_allelo = 1` (rampe(0)=0) ⇒ golden INTACT tant
        qu'aucun émetteur ne charge le champ (tronçon ⑤). Absent ⇒ comportement historique.
        """
        candidates = []
        for archetype in SEED_ARCHETYPES:
            density = self.get(r, c, archetype)
            if density < 0.001:
                continue
            niche_eff = niche
            if arch_tolerance and light > 0.0:
                tol = arch_tolerance.get(archetype, 1.0)
                niche_eff = niche * (min(1.0, light * tol) / light)
            if arch_ph:
                niche_eff *= arch_ph.get(archetype, 1.0)
            if arch_temp:
                niche_eff *= arch_temp.get(archetype, 1.0)
            if arch_allelo:
                niche_eff *= arch_allelo.get(archetype, 1.0)
            threshold = niche_eff * density
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
