"""
SYMBIOSE — fields/population.py
Vie macroscopique observable (D31.1) — champs de population déterministes +
règle d'échantillonnage des sprites.

Modèle TRANCHÉ (CONCEPTION_VIE_MACRO.md §2, hybride) :
  - DYNAMIQUE = un `PopulationField` générique (sous-classe `GridField`),
    instancié une fois par guilde (ravageur / auxiliaire / pollinisateur /
    vers_de_terre), borné aux 432 plots → ~gratuit (D32).
  - PERCEPTION = sprites ÉCHANTILLONNÉS depuis le champ (`sample_sprites`),
    fonction PURE déterministe densité → entités.

Périmètre D31.1 : les champs sont CALCULÉS mais RIEN dans la santé / la
croissance / la reproduction ne les LIT encore (le câblage écologique est
D31.2). → le golden reste INTACT. Aucune écriture sur les champs existants,
aucun log : pur effet de bord sur les champs de population.

Couche `fields` (patron `DisturbanceField` de grids.py). N'importe que
`fields.grids` et `fields.noise` — aucun cycle avec `ecofields` (qui détient les
champs et les ticke).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable

from fields.grids import GridField
from fields.noise import _hash_noise


# ---------------------------------------------------------------------------
# CONSTANTES DE DYNAMIQUE (placeholders — calibrage post-test, hors D31.1)
# ---------------------------------------------------------------------------

POP_MAX = 1.0          # densité normalisée par plot ∈ [0, POP_MAX]
POP_INERTIA = 0.85     # inertie du champ (le décalage temporel proie↔prédateur)

# Couplage température → vitalité de la guilde (chaud = naissances, froid = mort).
T_COLD_ZERO = 6.0      # °C : en dessous, plus aucune chaleur utile (warmth = 0)
T_WARM_FULL = 24.0     # °C : au-dessus, chaleur maximale (warmth = 1)

# Références de normalisation des ressources trophiques → [0, 1].
FOLIAGE_REF = 2.0      # somme de feuillage (santé/3 × densité) saturant la ressource
FLOWER_REF  = 1.5      # somme de "fleurs" (plantes matures) saturant le nectar
OM_REF      = 4.0      # om_fresh + om_active saturant la ressource des vers
MONO_REF    = 3.0      # nb de familles voisines au-delà duquel la monoculture cesse

# Pondérations par défaut (surchargées par TrophicSpec).
#
# Forme MULTIPLICATIVE (capacité de charge × survie) — choisie pour que la
# population puisse COLONISER depuis zéro (la cible ne dépend pas de la pop
# courante) et OSCILLER (la prédation/perturbation rabotent la survie). Une
# forme additive « naissance − mort » plafonnerait tout à zéro dès que la
# population est basse (les morts absolues l'emportent), d'où densités nulles.
#
#   capacité = clamp(resource_w·ressource + habitat_w·habitat, 0, 1)
#   survie   = chaleur · (1 − min(1, pred_w·prédation)) · (1 − min(1, disturb_w·perturbation))
#   cible    = capacité · survie
#
# Le froid (hiver) et la famine sont IMPLICITES : chaleur=0 en hiver annule la
# cible (déclin saisonnier visible) ; si pop > capacité, la cible < pop → déclin.
DEF_RESOURCE_W = 0.80  # poids de la ressource trophique dans la capacité de charge
DEF_HABITAT_W  = 0.45  # poids du plancher d'habitat/nectar dans la capacité
DEF_PRED_W     = 1.20  # sensibilité de la survie à la prédation locale
DEF_DISTURB_W  = 0.60  # sensibilité de la survie à la perturbation locale


# ---------------------------------------------------------------------------
# ATTRACTION ANIMALE PAR LE FRUIT TOMBÉ (décompo·compost ④, CONCEPTION §4)
# ---------------------------------------------------------------------------
# Une parcelle `fruit` (déposée par engine._tick_fruits à la chute des sur-mûrs)
# émet un signal selon son `age_sem` (succession sur le fruit), AJOUTÉ à la
# capacité de charge des guildes via `signal_fn` (terme additif, clampé) :
#   - FRAIS (age bas) → nourrit l'`auxiliaire` (frugivores, oiseaux) ;
#   - POURRI (age élevé) → appelle le `ravageur` DOMINANT (charognards, mouches)
#     + une PETITE fraction `auxiliaire` (décomposeurs : la décompo n'est jamais
#     pur déchet). Pas de 5ᵉ guilde (tranché Nico).
# Invariant golden : à ZÉRO parcelle `fruit`, sig=0 partout → capacité inchangée.
# Knobs CONSERVATIFS (un tas de fruits ne sature pas la guilde), calibrage post-test.
FRUIT_FRAIS_SEM  = 3.0   # semaines : durée de la fenêtre « frais » (frais→0 au-delà)
FRUIT_POURRI_SEM = 6.0   # semaines au-delà de FRUIT_FRAIS_SEM pour atteindre « pourri » plein
FRUIT_SIGNAL_REF = 0.45  # masse de litière `fruit` saturant l'intensité du signal (≈ 3 fruits)
FRUIT_AUX_GAIN   = 0.50  # boost max de capacité `auxiliaire` d'un tas frais plein
FRUIT_RAV_GAIN   = 0.60  # boost max de capacité `ravageur` d'un tas pourri plein
FRAC_AUX_POURRI  = 0.25  # part du signal pourri qui va AUSSI à l'auxiliaire (décomposeurs)


# ---------------------------------------------------------------------------
# CONSTANTES DE PERCEPTION (échantillonnage sprite — §3)
# ---------------------------------------------------------------------------

# Un sprite = un quantum de densité. Calé sur la plage de densité ÉMERGENTE en
# climat tempéré (pic saisonnier observé ~0.2 ; cf. trace de calibrage) : un
# quantum de 0.06 fait apparaître les sprites un à un au fil de la montée
# estivale (0→4 sur la saison) et disparaître l'hiver. Knob de calibrage (§8).
DENSITE_PAR_SPRITE = 0.06
SPRITES_PAR_PLOT_MAX = 4    # cap par plot (les sprites saturent, le champ garde le vrai nombre)

# Décalage du canal _hash_noise pour la coordonnée Y (décorrèle X et Y).
_SLOT_Y_OFFSET = 0x40


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


# ---------------------------------------------------------------------------
# SPEC TROPHIQUE — la donnée qui paramètre le mécanisme générique
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TrophicSpec:
    """
    Décrit UNE guilde de façon data-driven (CONCEPTION_VIE_MACRO.md §2.1) :
      - resource_fn : (eco, tile, plants) → grille [rows][cols] ∈ [0,1]
                      = le `qi_local` trophique (ce dont la guilde se nourrit).
      - habitat_fn  : (eco, tile, plants) → grille [rows][cols] ∈ [0,1]
                      = plancher persistant (nectar, refuge, sol non perturbé…).
      - predators   : noms des champs de population qui PRÉDATENT cette guilde
                      (lus dans eco.populations au tick — puits biotique).
      - salt        : canal _hash_noise DÉDIÉ pour les positions de sprites
                      (décorrélé des autres guildes et des tirages du tick).
      - signal_fn   : (eco, tile, plants) → grille [rows][cols] ≥ 0, terme ADDITIF
                      optionnel à la capacité (attraction par le fruit tombé, ④).
                      None (défaut) = pas de signal → capacité inchangée (golden
                      neutre pour les guildes sans fruit : pollinisateur, vers).
    Les pondérations ont des défauts de module, surchargeables par guilde.
    """
    name: str
    salt: int
    resource_fn: Callable
    habitat_fn: Callable
    predators: tuple[str, ...] = ()
    signal_fn: Callable | None = None
    resource_w: float = DEF_RESOURCE_W
    habitat_w: float = DEF_HABITAT_W
    pred_w: float = DEF_PRED_W
    disturb_w: float = DEF_DISTURB_W
    inertia: float = POP_INERTIA


# ---------------------------------------------------------------------------
# POPULATIONFIELD — le mécanisme générique (sous-classe GridField)
# ---------------------------------------------------------------------------

class PopulationField(GridField):
    """
    Champ de densité d'une guilde macroscopique. Persistant (mémoire/inertie),
    à la différence du scalaire `herbivory_pressure` recalculé sans mémoire.

    Tick (relaxation vers une cible, patron `DisturbanceField`) :
        capacité = clamp(resource_w·ressource + habitat_w·habitat, 0, 1)
        survie   = chaleur · (1 − min(1, pred_w·prédation))
                           · (1 − min(1, disturb_w·perturbation))
        cible    = capacité · survie
        champ'   = clamp(champ·inertie + cible·(1−inertie), 0, MAX)

    Forme MULTIPLICATIVE : la cible ne dépend pas de la pop courante → la guilde
    colonise depuis zéro là où ressource+habitat existent. L'inertie introduit le
    DÉCALAGE temporel proie↔prédateur → cycles boom-bust visibles (§2.1). Le
    froid (chaleur→0 l'hiver) et la famine (pop>capacité) sont implicites.
    """

    def __init__(self, spec: TrophicSpec, rows: int, cols: int):
        super().__init__(rows, cols, initial=0.0, max_val=POP_MAX)
        self.spec = spec
        # Dernière grille de ressource — sert au scalaire `activite` (pur rendu).
        self.activite_grid: list[list[float]] = [
            [0.0] * cols for _ in range(rows)
        ]

    def tick(self, eco, tile, plants, predator_fields: list["PopulationField"]) -> None:
        """
        Intègre un tick de dynamique. Lit eco (température, perturbation), les
        plantes (via resource_fn/habitat_fn) et les champs prédateurs ; n'écrit
        QUE sur soi-même. Aucun log, aucune écriture sur les champs existants
        → golden-neutre (D31.1).
        """
        spec = self.spec
        res = spec.resource_fn(eco, tile, plants)
        hab = spec.habitat_fn(eco, tile, plants)
        # Terme additif optionnel (attraction par le fruit tombé, ④). None → 0
        # partout → capacité strictement inchangée (golden neutre sans fruit).
        sig = spec.signal_fn(eco, tile, plants) if spec.signal_fn else None
        self.activite_grid = res   # mémorise la ressource pour `activite()`
        for r in range(self.rows):
            for c in range(self.cols):
                temp = eco.temperature.at_plot(r, c)
                warmth = _clamp01((temp - T_COLD_ZERO) / (T_WARM_FULL - T_COLD_ZERO))
                disturb = eco.disturbance.at_plot(r, c)
                predation = sum(pf.at_plot(r, c) for pf in predator_fields)
                pop = self.data[r][c]

                capacite = _clamp01(spec.resource_w * res[r][c]
                                    + spec.habitat_w * hab[r][c]
                                    + (sig[r][c] if sig else 0.0))
                survie = (warmth
                          * (1.0 - min(1.0, spec.pred_w * predation))
                          * (1.0 - min(1.0, spec.disturb_w * disturb)))
                cible = capacite * survie
                self.data[r][c] = max(0.0, min(
                    self.max_val,
                    pop * spec.inertia + cible * (1.0 - spec.inertia)
                ))

    def activite(self, r: int, c: int) -> float:
        """
        Scalaire d'ACTIVITÉ [0,1] — la ressource locale disponible (« en nombre
        ET en activité » de l'intention). Pilote la vitesse d'animation / le
        rayon d'errance côté Godot. PUR rendu, zéro impact simulation.
        """
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return self.activite_grid[r][c]
        return 0.0


# ---------------------------------------------------------------------------
# RÉSOLUTION DES RESSOURCES / HABITATS (grilles [rows][cols] ∈ [0,1])
# ---------------------------------------------------------------------------
# Toutes ces fonctions sont PURES en lecture : elles ne modifient aucun champ.
# Elles reçoivent `eco` (EcoFields, qui détient les champs ET eco.populations),
# `tile` (rondelles) et `plants`. Pas d'import de world/ecofields → pas de cycle.

def _zero_grid(rows: int, cols: int) -> list[list[float]]:
    return [[0.0] * cols for _ in range(rows)]


def _foliage_grid(eco, tile, plants) -> list[list[float]]:
    """Feuillage hôte local (ressource du ravageur) — santé × couverture canopée."""
    g = _zero_grid(eco.rows, eco.cols)
    for p in plants:
        if not p.is_alive or p.current_stage < 1:
            continue
        w = p.health / 3.0
        for (r, c) in p.foliar_plots:
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                g[r][c] += w
    for r in range(eco.rows):
        for c in range(eco.cols):
            g[r][c] = min(1.0, g[r][c] / FOLIAGE_REF)
    return g


def _monoculture_grid(eco, tile, plants) -> list[list[float]]:
    """
    Plancher d'habitat du ravageur = monoculture (faible biodiversité locale).
    1 famille → monoculture forte ; 3+ familles → régulée par la diversité.
    """
    fams: list[list[set]] = [[set() for _ in range(eco.cols)] for _ in range(eco.rows)]
    for p in plants:
        if not p.is_alive:
            continue
        fam = p.plant_class.family
        for (r, c) in p.foliar_plots:
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                fams[r][c].add(fam)
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            n = len(fams[r][c])
            g[r][c] = 1.0 - min(1.0, n / MONO_REF)
    return g


def _flower_grid(eco, tile, plants) -> list[list[float]]:
    """Fleurs en floraison (ressource du pollinisateur) — plantes matures vivantes."""
    g = _zero_grid(eco.rows, eco.cols)
    for p in plants:
        if not p.is_alive or p.current_stage < 2:
            continue
        w = p.health / 3.0
        for (r, c) in p.foliar_plots:
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                g[r][c] += w
    for r in range(eco.rows):
        for c in range(eco.cols):
            g[r][c] = min(1.0, g[r][c] / FLOWER_REF)
    return g


def _soil_food_grid(eco, tile, plants) -> list[list[float]]:
    """
    Ressource des vers de terre = microbiome + matière organique en décomposition
    (om_fresh + om_active, part fongique incluse — cf. §6.1, pas un 5ᵉ champ).
    """
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            micro = min(1.0, eco.microbiome.at_plot(r, c) / 3.0)
            om = min(1.0, (eco.om_fresh_at(r, c)
                           + eco.om_active.at_plot(r, c)) / OM_REF)
            g[r][c] = _clamp01(0.5 * micro + 0.5 * om)
    return g


def _ravageur_grid(eco, tile, plants) -> list[list[float]]:
    """Ressource de l'auxiliaire = la proie animale, i.e. le champ ravageur."""
    rav = eco.populations["ravageur"]
    return [[rav.at_plot(r, c) for c in range(eco.cols)] for r in range(eco.rows)]


def _stability_grid(eco, tile, plants) -> list[list[float]]:
    """Refuge de l'auxiliaire = nectar (rondelle auxiliaire) + stabilité (1−perturbation)."""
    nectar = min(1.0, tile.get_rondelle_count("auxiliaire") / 3.0)
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            stability = 1.0 - eco.disturbance.at_plot(r, c)
            g[r][c] = _clamp01(0.5 * nectar + 0.5 * stability)
    return g


def _pollinisateur_habitat_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat du pollinisateur = rondelle pollinisateur (terme-source uniforme)."""
    val = min(1.0, tile.get_rondelle_count("pollinisateur") / 3.0)
    return [[val] * eco.cols for _ in range(eco.rows)]


def _undisturbed_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat des vers = sol NON perturbé (1 − perturbation)."""
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            g[r][c] = 1.0 - eco.disturbance.at_plot(r, c)
    return g


# --- Signal d'attraction par le fruit tombé (④, CONCEPTION §4) --------------
# Terme ADDITIF à la capacité (≠ ressource/habitat) : il APPELLE la faune sans
# rien retirer à la plante (philo #2). Lit la parcelle `fruit` du plot — unique
# par plot (fusion par tissu, acquis ①) → lecture déterministe, pas d'ordre.

def _fruit_litter(eco, r: int, c: int) -> tuple[float, float]:
    """(masse, age_sem) de la parcelle `fruit` du plot, (0, 0) si aucune."""
    for p in eco.litiere[r][c]:
        if p.tissu == "fruit":
            return p.masse, p.age_sem
    return 0.0, 0.0


def _fruit_weights(age_sem: float) -> tuple[float, float]:
    """Poids (frais, pourri) ∈ [0,1] selon l'âge : frais décroît, pourri croît."""
    frais  = _clamp01(1.0 - age_sem / FRUIT_FRAIS_SEM)
    pourri = _clamp01((age_sem - FRUIT_FRAIS_SEM) / FRUIT_POURRI_SEM)
    return frais, pourri


def _aux_fruit_signal(eco, tile, plants) -> list[list[float]]:
    """Attraction `auxiliaire` : fruit frais (frugivores) + fraction du pourri
    (décomposeurs). Borné par FRUIT_AUX_GAIN (un tas plein ne sature pas)."""
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            masse, age = _fruit_litter(eco, r, c)
            if masse <= 0.0:
                continue
            sig = min(1.0, masse / FRUIT_SIGNAL_REF)
            frais, pourri = _fruit_weights(age)
            g[r][c] = FRUIT_AUX_GAIN * sig * (frais + FRAC_AUX_POURRI * pourri)
    return g


def _rav_fruit_signal(eco, tile, plants) -> list[list[float]]:
    """Attraction `ravageur` : fruit pourri (charognards, mouches), DOMINANT.
    Borné par FRUIT_RAV_GAIN."""
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            masse, age = _fruit_litter(eco, r, c)
            if masse <= 0.0:
                continue
            sig = min(1.0, masse / FRUIT_SIGNAL_REF)
            _, pourri = _fruit_weights(age)
            g[r][c] = FRUIT_RAV_GAIN * sig * pourri
    return g


# ---------------------------------------------------------------------------
# LES 4 INSTANCES (chaîne trophique — CONCEPTION_VIE_MACRO.md §2.2)
# ---------------------------------------------------------------------------
# Canaux _hash_noise dédiés (décorrélés) par guilde pour les positions sprites.
_SALT_RAVAGEUR      = 0x2A0001
_SALT_AUXILIAIRE    = 0x2A1001
_SALT_POLLINISATEUR = 0x2A2001
_SALT_VERS          = 0x2A3001


def build_population_specs() -> list[TrophicSpec]:
    """
    Construit les 4 specs dans l'ORDRE DE TICK (chaîne trophique). Le ravageur
    tick en premier (il lit l'auxiliaire de la semaine PRÉCÉDENTE → décalage),
    puis l'auxiliaire lit le ravageur fraîchement mis à jour.
    """
    return [
        TrophicSpec(
            name="ravageur", salt=_SALT_RAVAGEUR,
            resource_fn=_foliage_grid, habitat_fn=_monoculture_grid,
            predators=("auxiliaire",),
            signal_fn=_rav_fruit_signal,   # fruit pourri → charognards (④)
        ),
        TrophicSpec(
            name="auxiliaire", salt=_SALT_AUXILIAIRE,
            resource_fn=_ravageur_grid, habitat_fn=_stability_grid,
            predators=(),
            signal_fn=_aux_fruit_signal,   # fruit frais → frugivores (④)
        ),
        TrophicSpec(
            name="pollinisateur", salt=_SALT_POLLINISATEUR,
            resource_fn=_flower_grid, habitat_fn=_pollinisateur_habitat_grid,
            predators=(),
        ),
        TrophicSpec(
            name="vers_de_terre", salt=_SALT_VERS,
            resource_fn=_soil_food_grid, habitat_fn=_undisturbed_grid,
            predators=(),
        ),
    ]


# ---------------------------------------------------------------------------
# PERCEPTION — échantillonnage sprite (fonction PURE, §3)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SpriteSample:
    """Un sprite échantillonné — donnée de rendu, ne porte AUCUNE Vigueur."""
    guild: str
    row: int
    col: int
    slot: int          # index du quantum dans le plot (0..cap-1)
    x_frac: float      # position dans le plot ∈ [0,1], INDÉPENDANTE de la semaine
    y_frac: float
    activite: float    # vitesse d'animation / errance (pur rendu)


def sample_sprites(field: PopulationField, seed: int,
                   densite_par_sprite: float = DENSITE_PAR_SPRITE,
                   cap: int = SPRITES_PAR_PLOT_MAX) -> list[SpriteSample]:
    """
    Règle d'échantillonnage densité → entités (CONCEPTION_VIE_MACRO.md §3).
    PURE & déterministe : aucun spawn par RNG vivant, aucun feedback vers la sim
    → golden-neutre (les sprites lisent le champ, ne le modifient pas).

      nombre   = min(cap, floor(densité / densite_par_sprite))
      position = _hash_noise(seed, salt+slot, r, c) — INDÉPENDANTE de la semaine
                 → un slot occupe TOUJOURS le même point ; il bascule seulement
                   visible/caché quand la densité franchit son seuil.
      activite = field.activite(r, c) (pur rendu).
    """
    spec = field.spec
    sprites: list[SpriteSample] = []
    for r in range(field.rows):
        for c in range(field.cols):
            d = field.at_plot(r, c)
            n = min(cap, int(d / densite_par_sprite))
            if n <= 0:
                continue
            act = field.activite(r, c)
            for slot in range(n):
                x = _hash_noise(seed, spec.salt + slot, r, c)
                y = _hash_noise(seed, spec.salt + _SLOT_Y_OFFSET + slot, r, c)
                sprites.append(SpriteSample(
                    guild=spec.name, row=r, col=c, slot=slot,
                    x_frac=x, y_frac=y, activite=act,
                ))
    return sprites
