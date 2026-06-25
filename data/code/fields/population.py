"""
SYMBIOSE — fields/population.py
Vie macroscopique observable (D31.1) — champs de population déterministes +
règle d'échantillonnage des sprites.

Modèle TRANCHÉ (CONCEPTION_VIE_MACRO.md §2, hybride) :
  - DYNAMIQUE = un `PopulationField` générique (sous-classe `GridField`),
    instancié une fois par ESPÈCE nommée (scission ④b/c/d), regroupée en catégorie
    (ravageur / auxiliaire / detritivore) + pollinisateurs par type, borné aux
    432 plots → ~gratuit (D32).
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
import math
from dataclasses import dataclass, field
from typing import Callable

from fields.grids import GridField
from fields.noise import _hash_noise
from fields.foragers import ForagerParams   # spec d'agent butineur (§F, tronçon ③)
from fields.lifecycle import LifeCycleBridge  # pont de cycle de vie (§D, tronçon ⑤)
from fields.faune_encyclo import encyclo_meta  # blurb + interconnexions (④e, donnée pure)


# ---------------------------------------------------------------------------
# CONSTANTES DE DYNAMIQUE (placeholders — calibrage post-test, hors D31.1)
# ---------------------------------------------------------------------------

POP_MAX = 1.0          # densité normalisée par plot ∈ [0, POP_MAX]
POP_INERTIA = 0.85     # inertie de MONTÉE (la pop croît vers sa cible à ce rythme)
# Inertie de DÉCRUE (CONCEPTION_SAISONNALITE_VIE_MACRO.md §4) : quand la cible
# tombe sous la pop courante, la relaxation est PLUS RAPIDE → la dormance
# automnale ne traîne plus 13 semaines (0.55⁴ ≈ 0.09, extinction en ~4 sem).
# Asymétrie écologique : « meurt vite quand le milieu se dégrade, recolonise
# lentement quand il s'améliore ». Knob de recours → remonter vers 0.70 si les
# bust estivaux deviennent trop pointus (sprites qui clignotent).
POP_INERTIA_DECAY = 0.55

# Couplage température → vitalité de la guilde (chaud = naissances, froid = mort).
# C'est le signal d'INTENSITÉ (« combien » la guilde prospère quand elle est
# active), distinct de la porte saisonnière `phenology` (« quand », ci-dessous).
T_COLD_ZERO = 6.0      # °C : en dessous, plus aucune chaleur utile (warmth = 0)
T_WARM_FULL = 24.0     # °C : au-dessus, chaleur maximale (warmth = 1)

# --- Saisonnalité photopériodique (CONCEPTION_SAISONNALITE_VIE_MACRO.md §2-3) ---
# La DORMANCE/le RÉVEIL des guildes se pilotent par la LONGUEUR DU JOUR, pas par
# la température seule : un signal anticipateur fiable et déterministe (le jour
# court ne ment pas, un redoux si). `daylength(wiy)` est une sinusoïde 8 h↔16 h
# à ~49°N, pic au solstice d'été (wiy≈25, qui PRÉCÈDE le pic thermique wiy≈30 —
# le déphasage saisonnier réel). Chaque guilde a ensuite sa propre FENÊTRE
# d'activité (seuils en heures de jour) — voir TrophicSpec.daylen_min/full.
W_SOLSTICE_ETE = 25    # semaine du jour le plus long
DAYLEN_MOY_H   = 12.0  # longueur de jour moyenne (équinoxes), heures
DAYLEN_AMP_H   = 4.0   # demi-amplitude → 8 h (solstice hiver) ↔ 16 h (solstice été)
# Fenêtre phénologique PAR DÉFAUT (heures de jour) — surchargée par guilde.
DEF_DAYLEN_MIN  = 10.0  # en dessous → dormance (phenology = 0)
DEF_DAYLEN_FULL = 13.0  # au-dessus → pleine activité (phenology = 1)

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
# ATTRACTION FONGIVORE PAR LE MYCÉLIUM (sprint mycélium ④, CONCEPTION §1.1)
# ---------------------------------------------------------------------------
# Le champ `mycelium ∈ [0,1]` (réseau fongique, acteur ① du sprint) NOURRIT une
# fraction de la faune fongivore (collemboles/détritivores qui broutent les
# hyphes) : terme ADDITIF à la capacité de charge du `lombric` (détritivore du
# sol, là où vit le réseau), via `signal_fn` — exactement le patron du fruit
# tombé (`_aux_fruit_signal`), pas un retour de la faune sur le champ (philo #2).
# Invariant golden : `mycelium = 0` partout (repos du smoke) ⇒ signal nul ⇒
# capacité strictement inchangée → golden de champ NEUTRE hors mycélium réel.
# Knob CONSERVATIF (un réseau saturé ne dépasse pas le boost du fruit frais),
# calibrage post-test.
FONGIVORE_GAIN = 0.35    # boost max de capacité `detritivore` d'un réseau plein


def _mycelium_signal(eco, tile, plants) -> list[list[float]]:
    """Attraction fongivore : le réseau `mycelium` dense gonfle la capacité du
    détritivore du sol (collemboles brouteurs d'hyphes). Borné par FONGIVORE_GAIN.
    Lecture PURE du champ (la faune ne touche pas le mycélium — c'est le CHAMP qui
    fait tout, piège du kickoff §pièges)."""
    mycel = getattr(eco, "mycelium", None)
    if mycel is None:                       # robustesse pré-① (jamais en prod)
        return _zero_grid(eco.rows, eco.cols)
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            g[r][c] = FONGIVORE_GAIN * mycel.at_plot(r, c)
    return g


# ---------------------------------------------------------------------------
# CONSTANTES DE SCISSION DU RAVAGEUR (faune nommée ④b, CONCEPTION_FAUNE_DEDIEE §2)
# ---------------------------------------------------------------------------
# Le champ unique `ravageur` se scinde en puceron / limace / doryphore. Chacun a
# SA triade (resource_fn/habitat_fn/predators) ; la catégorie `ravageur` reste la
# somme (pression herbivore subie par les plantes, C1). Placeholders, calibrage
# post-test (comme les guildes — décision §5.6).
LITTER_REF       = 2.0   # masse de litière de surface (hors `fruit`) saturant la ressource détritivore
LIMACE_LITTER_W  = 1.0   # ressource limace : litière DOMINANTE (détritivore d'abord, §2)
LIMACE_FOLIAGE_W = 0.30  # + grignotage opportuniste du feuillage tendre (secondaire)
DORY_AIL_REPULSE = 0.6   # l'ail (Amaryllidaceae) rogne l'habitat doryphore (répulsif §4.4)


# ---------------------------------------------------------------------------
# CONSTANTES DE SCISSION DE L'AUXILIAIRE (faune nommée ④c, CONCEPTION_FAUNE_DEDIEE §2)
# ---------------------------------------------------------------------------
# Le champ unique `auxiliaire` se scinde en coccinelle / chrysope / carabe / merle /
# hérisson. Chacun chasse SA proie nommée (coccinelle/chrysope→puceron,
# carabe/hérisson→limace) → les `predators` posés en ④b S'ACTIVENT, les boucles
# proie↔prédateur deviennent réelles. Habitats neufs ancrés sur les STRUCTURES
# (piles ⑤) : poser une pile de bois attire carabe + hérisson (faune↔structures §3).
PILE_HABITAT_W     = 0.40  # bump d'habitat des structures `pile` (carabe/hérisson)
MERLE_BASE_HABITAT = 0.20  # plancher d'habitat ubiquiste du merle (oiseau résident)


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


def _smoothstep(x: float, a: float, b: float) -> float:
    """Rampe LISSE [0,1] entre les seuils a (→0) et b (→1) — Hermite 3t²−2t³.
    Plus douce qu'une rampe linéaire (dérivée nulle aux bornes) → pas de
    cassure d'activité quand le jour franchit un seuil."""
    if a == b:
        return 0.0 if x < a else 1.0
    t = _clamp01((x - a) / (b - a))
    return t * t * (3.0 - 2.0 * t)


def daylength(week_in_year: int) -> float:
    """
    Longueur du jour (heures) à ~49°N — sinusoïde 8 h↔16 h, pic au solstice d'été
    (CONCEPTION_SAISONNALITE_VIE_MACRO.md §2). Fonction PURE de la semaine (philo
    #3) : le forecast et la phénologie florale (arc pollinisation) pourront s'y
    appuyer. NON-monotone → une simple rampe sur cette grandeur donne du même
    coup le réveil printanier ET la dormance automnale, des deux côtés du solstice.
    """
    return DAYLEN_MOY_H + DAYLEN_AMP_H * math.cos(
        2.0 * math.pi * (week_in_year - W_SOLSTICE_ETE) / 52.0)


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

    `category` (modèle B, CONCEPTION_FAUNE_DEDIEE.md §1) : la GUILDE rétrogradée en
    ÉTIQUETTE. Plusieurs espèces nommées partageront une même catégorie
    (ravageur / auxiliaire / detritivore) ; les consommateurs qui raisonnaient
    « par guilde » (santé des plantes, vigueur macro) lisent désormais l'AGRÉGAT
    de la catégorie (`EcoFields.category_density` / `category_fields`). Tant qu'une
    catégorie n'a qu'un membre (état ④a), l'agrégat == le champ → golden NEUTRE.
    """
    name: str
    category: str
    salt: int
    resource_fn: Callable
    habitat_fn: Callable
    predators: tuple[str, ...] = ()
    signal_fn: Callable | None = None
    resource_w: float = DEF_RESOURCE_W
    habitat_w: float = DEF_HABITAT_W
    pred_w: float = DEF_PRED_W
    disturb_w: float = DEF_DISTURB_W
    inertia: float = POP_INERTIA               # inertie de MONTÉE
    inertia_decay: float = POP_INERTIA_DECAY   # inertie de DÉCRUE (§4)
    # Fenêtre phénologique de la guilde (heures de jour) : porte saisonnière §3.
    daylen_min: float = DEF_DAYLEN_MIN
    daylen_full: float = DEF_DAYLEN_FULL
    # Métadonnée d'ENCYCLOPÉDIE (④e, CONCEPTION_FAUNE_DEDIEE §1.1) — DONNÉE PURE,
    # jamais lue par `tick` → golden NEUTRE. `blurb` = texte naturaliste ; rendu = ⑥.
    # `interconnexions` = graphe relationnel §3 (source : fields/faune_encyclo.py).
    blurb: str = ""
    interconnexions: tuple[str, ...] = ()


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

    def tick(self, eco, tile, plants, predator_fields: list["PopulationField"],
             week_in_year: int = W_SOLSTICE_ETE) -> None:
        """
        Intègre un tick de dynamique. Lit eco (température, perturbation), les
        plantes (via resource_fn/habitat_fn) et les champs prédateurs ; n'écrit
        QUE sur soi-même. Aucun log, aucune écriture sur les champs existants.

        `week_in_year` ∈ [1,52] pilote la PORTE saisonnière photopériodique
        (`phenology`, §3) — défaut = plein été (réveil maximal) pour que d'anciens
        appels de test sans saison restent neutres ; l'engine passe toujours la
        vraie semaine. `survie = phenology · warmth · (1−préd) · (1−perturb)` :
        phenology dit QUAND la guilde est active, warmth COMBIEN.
        """
        spec = self.spec
        res = spec.resource_fn(eco, tile, plants)
        hab = spec.habitat_fn(eco, tile, plants)
        # Terme additif optionnel (attraction par le fruit tombé, ④). None → 0
        # partout → capacité strictement inchangée (golden neutre sans fruit).
        sig = spec.signal_fn(eco, tile, plants) if spec.signal_fn else None
        self.activite_grid = res   # mémorise la ressource pour `activite()`
        # Porte saisonnière : scalaire GLOBAL à la tuile (la photopériode ne varie
        # pas d'un plot à l'autre) → calculé UNE fois hors de la boucle r×c.
        phenology = _smoothstep(daylength(week_in_year),
                                spec.daylen_min, spec.daylen_full)
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
                survie = (phenology * warmth
                          * (1.0 - min(1.0, spec.pred_w * predation))
                          * (1.0 - min(1.0, spec.disturb_w * disturb)))
                cible = capacite * survie
                # Inertie ASYMÉTRIQUE (§4) : décrue rapide / montée au rythme calibré.
                inertie = spec.inertia_decay if cible < pop else spec.inertia
                self.data[r][c] = max(0.0, min(
                    self.max_val,
                    pop * inertie + cible * (1.0 - inertie)
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
    """SUPPLANTÉ (arc pollinisation ② — voir `_make_nectar_grid`) : proxy
    historique « fleurs = plantes matures (stade ≥ 2) ». Remplacé par la VRAIE
    floraison (tronçon ①) pondérée par type. Conservé pour mémoire / repli.
    Fleurs en floraison (ressource du pollinisateur) — plantes matures vivantes."""
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


# --- Ressources/habitats des 3 ravageurs nommés (scission ④b, doc §2) ---------

def _litter_grid(eco, tile, plants) -> list[list[float]]:
    """Litière de SURFACE en décompo d'un plot (doc §2) = Σ masses des parcelles
    HORS `fruit` (le fruit a son propre signal d'attraction), normalisée. Ressource
    détritivore : nourrit la limace (préférence) — réutilisée par le cloporte (④d)."""
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            masse = sum(p.masse for p in eco.litiere[r][c] if p.tissu != "fruit")
            g[r][c] = min(1.0, masse / LITTER_REF)
    return g


def _limace_food_grid(eco, tile, plants) -> list[list[float]]:
    """Ressource MIXTE de la limace (④b) : litière DOMINANTE (détritivore d'abord)
    + grignotage opportuniste du feuillage tendre. Clé du modèle B : `resource_fn`
    pilote la POPULATION (ce qui la nourrit), la catégorie `ravageur` pilote le
    DÉGÂT (ce qu'elle abîme, C1) — deux choses séparées (doc §2 « Cas limace »)."""
    litter = _litter_grid(eco, tile, plants)
    foliage = _foliage_grid(eco, tile, plants)
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            g[r][c] = _clamp01(LIMACE_LITTER_W * litter[r][c]
                               + LIMACE_FOLIAGE_W * foliage[r][c])
    return g


def _humide_litiere_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat de la limace (④b ; partagé avec le cloporte ④d) : sol HUMIDE +
    sous-litière. `humide` devient une VRAIE ressource (lecture de `eco.humidite`,
    qui existe) — gain du modèle B sur le A : la niche est réelle, pas une porte."""
    litter = _litter_grid(eco, tile, plants)
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            hum = min(1.0, eco.humidite.at_plot(r, c) / 3.0)
            g[r][c] = _clamp01(0.5 * hum + 0.5 * litter[r][c])
    return g


def _foliage_solanaceae_grid(eco, tile, plants) -> list[list[float]]:
    """Feuillage des seules Solanaceae (ressource du doryphore, ④b) — `_foliage_grid`
    filtré par famille : la pression doryphore est NULLE là où aucune Solanaceae ne
    pousse (interconnexion plante-hôte ↔ ravageur spécialiste)."""
    g = _zero_grid(eco.rows, eco.cols)
    for p in plants:
        if not p.is_alive or p.current_stage < 1:
            continue
        if p.plant_class.family != "Solanaceae":
            continue
        w = p.health / 3.0
        for (r, c) in p.foliar_plots:
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                g[r][c] += w
    for r in range(eco.rows):
        for c in range(eco.cols):
            g[r][c] = min(1.0, g[r][c] / FOLIAGE_REF)
    return g


def _solanaceae_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat du doryphore (④b) = présence locale de Solanaceae, RÉDUITE par la
    présence d'ail (Amaryllidaceae répulsif, doc §4.4). L'ail n'a PAS de rondelle
    dédiée (son effet ③ est une injection microbiome) → on lit ici sa présence
    foliaire pour rogner l'habitat du ravageur de la pomme de terre."""
    solana = _zero_grid(eco.rows, eco.cols)
    ail    = _zero_grid(eco.rows, eco.cols)
    for p in plants:
        if not p.is_alive or p.current_stage < 1:
            continue
        fam = p.plant_class.family
        cible = (solana if fam == "Solanaceae"
                 else ail if fam == "Amaryllidaceae" else None)
        if cible is None:
            continue
        for (r, c) in p.foliar_plots:
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                cible[r][c] += p.health / 3.0
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            s = min(1.0, solana[r][c] / FOLIAGE_REF)
            a = min(1.0, ail[r][c] / FOLIAGE_REF)
            g[r][c] = _clamp01(s * (1.0 - DORY_AIL_REPULSE * a))
    return g


def _ravageur_grid(eco, tile, plants) -> list[list[float]]:
    """Proie animale = AGRÉGAT de la catégorie `ravageur` (puceron + limace +
    doryphore, modèle B). Depuis ④c, les auxiliaires NOMMÉS chassent chacun UNE
    proie précise (`_espece_grid`, ci-dessous) et ne lisent plus cet agrégat. Seule
    la syrphe_larve (pont ⑤) le réutilise comme proie : généraliste, elle prédate
    l'ensemble des ravageurs (doc §4 « ponts inchangés »)."""
    return [[eco.category_density("ravageur", r, c) for c in range(eco.cols)]
            for r in range(eco.rows)]


def _espece_grid(name: str) -> Callable:
    """Fabrique une resource_fn lisant le champ de population d'UNE espèce nommée
    (généralise `_ravageur_grid` à un membre unique, scission ④c). Câble chaque
    prédateur sur SA proie (coccinelle/chrysope→puceron, carabe/hérisson→limace) au
    lieu de l'agrégat de guilde → les boucles proie↔prédateur deviennent réelles.

    ROBUSTE à l'ordre des scissions : si `name` n'existe pas encore comme champ
    (catégorie pas encore scindée), la grille est NULLE — le merle/hérisson pourront
    ainsi viser `lombric` (④d) sans casser tant qu'il n'existe pas."""
    def _grid(eco, tile, plants) -> list[list[float]]:
        f = eco.populations.get(name)
        if f is None:
            return _zero_grid(eco.rows, eco.cols)
        return [[f.at_plot(r, c) for c in range(eco.cols)]
                for r in range(eco.rows)]
    return _grid


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
    """Habitat du pollinisateur = rondelle pollinisateur (terme-source uniforme).
    Habitat de l'abeille ET du papillon (arc pollinisation §E.2 ; la ruche §H, hub
    abeille, viendra en Partie II)."""
    val = min(1.0, tile.get_rondelle_count("pollinisateur") / 3.0)
    return [[val] * eco.cols for _ in range(eco.rows)]


def _auxiliaire_habitat_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat du syrphe = rondelle auxiliaire (terme-source uniforme), miroir de
    `_pollinisateur_habitat_grid` (§E.2 : le syrphe niche côté auxiliaires)."""
    val = min(1.0, tile.get_rondelle_count("auxiliaire") / 3.0)
    return [[val] * eco.cols for _ in range(eco.rows)]


# Bump d'habitat abeille des RUCHES peuplées (⑥, §H.2 — placeholder calibrage). Une
# ruche peuplée devient un terme-source d'habitat LOCAL pour l'abeille → renforce la
# population qui l'a remplie (boucle vertueuse, interconnexion §H.2). Lu DIRECTEMENT
# sur `eco.structures` (duck-typé, pas d'import de l'apiculture → pas de cycle).
RUCHE_HABITAT_W = 0.40


def _abeille_habitat_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat de l'abeille = `_pollinisateur_habitat_grid` (rondelle) + bump LOCAL
    des ruches peuplées (§H.2). Sans ruche posée → identique au générique partagé
    avec le papillon → **golden NEUTRE** (le smoke n'instancie aucune ruche)."""
    g = _pollinisateur_habitat_grid(eco, tile, plants)
    for st in getattr(eco, "structures", ()):
        if getattr(st, "kind", None) == "ruche" and st.essaim > 0.0:
            r, c = st.plot
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                g[r][c] = _clamp01(g[r][c] + RUCHE_HABITAT_W * st.essaim)
    return g


def _undisturbed_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat des vers = sol NON perturbé (1 − perturbation)."""
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            g[r][c] = 1.0 - eco.disturbance.at_plot(r, c)
    return g


# --- Habitats neufs des auxiliaires nommés (scission ④c, doc §2) -------------
# Ancrés sur les STRUCTURES `pile` (⑤) : lecture DIRECTE d'`eco.structures`,
# duck-typée comme `_abeille_habitat_grid` lit les ruches (pas d'import de
# l'apiculture/compost → pas de cycle de couche). À ZÉRO structure posée (cas du
# smoke golden), ces termes-sources sont nuls → golden NEUTRE pour leur part.

def _undisturbed_structure_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat du carabe (④c) = sol NON perturbé + bump des structures `pile` à bois
    (faune↔structures §3 : un carabe se réfugie sous le bois mort). Sans pile posée
    → identique à `_undisturbed_grid` (le carabe vit déjà du sol stable)."""
    g = _undisturbed_grid(eco, tile, plants)
    for st in getattr(eco, "structures", ()):
        if getattr(st, "kind", None) == "pile":
            r, c = st.plot
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                g[r][c] = _clamp01(g[r][c] + PILE_HABITAT_W)
    return g


def _pile_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat du hérisson (④c) = présence de structures `pile`/tas (refuge nocturne).
    Terme-source NUL sans pile posée → le hérisson dépend ENTIÈREMENT d'un aménagement
    joueur (poser une pile attire carabe + hérisson, synergie de cartes §8). Golden
    NEUTRE : le smoke n'instancie aucune structure."""
    g = _zero_grid(eco.rows, eco.cols)
    for st in getattr(eco, "structures", ()):
        if getattr(st, "kind", None) == "pile":
            r, c = st.plot
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                g[r][c] = _clamp01(g[r][c] + PILE_HABITAT_W)
    return g


def _osmie_habitat_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat de l'osmie (⑤) = rondelle pollinisateur (nichoirs posés) + bump des
    structures `pile` à bois mort : l'abeille solitaire NICHE dans les cavités du
    bois (faune↔structures §5.3 — une pile de bois lui offre des galeries). Sans
    pile ni rondelle → habitat nul (mais le nectar Rosacées/Apiacées suffit à la
    capacité additive). Golden NEUTRE pour la part `pile` : le smoke n'en pose aucune."""
    g = _pollinisateur_habitat_grid(eco, tile, plants)
    for st in getattr(eco, "structures", ()):
        if getattr(st, "kind", None) == "pile":
            r, c = st.plot
            if 0 <= r < eco.rows and 0 <= c < eco.cols:
                g[r][c] = _clamp01(g[r][c] + PILE_HABITAT_W)
    return g


def _base_habitat_grid(eco, tile, plants) -> list[list[float]]:
    """Habitat du merle (④c) = plancher constant léger (oiseau ubiquiste, présent
    toute saison ; haies/structures hautes = placeholder différé). UNIFORME → c'est
    sa NOURRITURE (fruit frais + vers) qui le concentre spatialement, pas l'habitat."""
    return [[MERLE_BASE_HABITAT] * eco.cols for _ in range(eco.rows)]


_lombric_grid = _espece_grid("lombric")


def _merle_food_grid(eco, tile, plants) -> list[list[float]]:
    """Nourriture du merle (④c) : fruit FRAIS (frugivore — `_aux_fruit_signal` repromu
    de signal additif en RESSOURCE, C13) + LOMBRIC (④d : le merle mange le ver, pas
    le cloporte prioritairement → `_espece_grid("lombric")`, non l'agrégat de
    catégorie). Borné [0,1]."""
    fruit = _aux_fruit_signal(eco, tile, plants)
    vers  = _lombric_grid(eco, tile, plants)
    g = _zero_grid(eco.rows, eco.cols)
    for r in range(eco.rows):
        for c in range(eco.cols):
            g[r][c] = _clamp01(fruit[r][c] + vers[r][c])
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
# INSTANCES NON-POLLINISATRICES (chaîne trophique — CONCEPTION_VIE_MACRO.md §2.2)
# ---------------------------------------------------------------------------
# Canaux _hash_noise dédiés (décorrélés) par guilde pour les positions sprites.
_SALT_RAVAGEUR      = 0x2A0001
_SALT_PUCERON       = _SALT_RAVAGEUR   # puceron = héritier du champ ravageur (④b, continuité sprites)
_SALT_LIMACE        = 0x2A6001
_SALT_DORYPHORE     = 0x2A7001
_SALT_AUXILIAIRE    = 0x2A1001
_SALT_COCCINELLE    = _SALT_AUXILIAIRE   # coccinelle = héritière du champ auxiliaire (④c, continuité sprites)
_SALT_CHRYSOPE      = 0x2A8001
_SALT_CARABE        = 0x2A9001
_SALT_MERLE         = 0x2AA001
_SALT_HERISSON      = 0x2AB001
_SALT_POLLINISATEUR = 0x2A2001   # réutilisé par l'abeille (héritière du champ historique)
_SALT_VERS          = 0x2A3001
_SALT_LOMBRIC       = _SALT_VERS   # lombric = héritier du champ vers_de_terre (④d, continuité sprites)
_SALT_CLOPORTE      = 0x2AC001
_SALT_SYRPHE        = 0x2A4001
_SALT_PAPILLON      = 0x2A5001
_SALT_BOURDON       = 0x2AD001   # pollinisateur B précoce/frais (⑤ catalogue enrichi)
_SALT_OSMIE         = 0x2AE001   # abeille solitaire niche-bois (⑤ catalogue enrichi)


def build_population_specs() -> list[TrophicSpec]:
    """
    Construit les specs NON pollinisatrices dans l'ORDRE DE TICK = **toutes les
    PROIES avant tous les PRÉDATEURS**. Ravageurs (puceron/limace/doryphore, ④b) et
    détritivores (lombric/cloporte, ④d) tickent d'abord ; ensuite les auxiliaires
    (coccinelle/chrysope/carabe/merle/hérisson, ④c) chassent chacun SA proie
    fraîchement mise à jour (`_espece_grid`). Chaque proie lit, elle, ses prédateurs
    de la semaine PRÉCÉDENTE (ils tickent après) → décalage d'inertie proie↔prédateur
    cohérent sur TOUTE la chaîne (boom-bust). Les pollinisateurs (registre §E) sont
    ajoutés à part par `build_pollinator_specs` (le conteneur concatène) — ni
    prédateur ni proie ici, donc leur ordre de tick est golden-neutre.

    SCISSION ④d (CONCEPTION_FAUNE_DEDIEE §2) : `vers_de_terre` devient lombric +
    cloporte (`category="detritivore"`). Le détritivore n'est plus un puits isolé :
    le lombric est proie du merle/hérisson, le cloporte du carabe/hérisson → ils
    PASSENT en position proie (avant les auxiliaires) pour que leurs prédateurs les
    lisent frais, comme la chaîne ravageur→auxiliaire (④c). C'est la cause du
    re-figeage golden MAÎTRISÉ #3.
    """
    return [
        TrophicSpec(
            name="puceron", category="ravageur", salt=_SALT_PUCERON,
            resource_fn=_foliage_grid, habitat_fn=_monoculture_grid,
            # Prédateurs nommés (④c) + syrphe_larve (pont ⑤, déjà résolu).
            predators=("coccinelle", "chrysope", "syrphe_larve"),
            daylen_min=10.0, daylen_full=13.0,   # fenêtre estivale
            **encyclo_meta("puceron"),
        ),
        TrophicSpec(
            name="limace", category="ravageur", salt=_SALT_LIMACE,
            resource_fn=_limace_food_grid, habitat_fn=_humide_litiere_grid,
            predators=("carabe", "herisson"),    # ④c
            # ④d : le signal fruit pourri (`_rav_fruit_signal`), porté TRANSITOIREMENT
            # par la limace en ④b, passe au CLOPORTE (détritivore dédié, doc §C13,
            # défaut « cloporte seul »). La limace n'a plus de terme-source fruit.
            daylen_min=9.0, daylen_full=12.0,    # humide/frais : fenêtre plus large/précoce
            **encyclo_meta("limace"),
        ),
        TrophicSpec(
            name="doryphore", category="ravageur", salt=_SALT_DORYPHORE,
            resource_fn=_foliage_solanaceae_grid, habitat_fn=_solanaceae_grid,
            predators=("carabe",),               # ④c (inactif jusque-là)
            daylen_min=10.0, daylen_full=13.0,   # fenêtre estivale
            **encyclo_meta("doryphore"),
        ),
        # --- Catégorie `detritivore` : 2 espèces nommées (scission ④d, doc §2) ----
        # Position PROIE (avant les auxiliaires) : lombric/cloporte sont mangés par
        # merle/hérisson/carabe → ils doivent ticker AVANT pour être lus frais.
        TrophicSpec(
            # lombric = héritier du champ `vers_de_terre` (salt identique → continuité
            # sprites) ; ressource = MO+microbiome du sol (pas la litière de surface).
            name="lombric", category="detritivore", salt=_SALT_LOMBRIC,
            resource_fn=_soil_food_grid, habitat_fn=_undisturbed_grid,
            predators=("merle", "herisson"),     # ④d : le ver n'est plus un puits isolé
            # Attraction fongivore (sprint mycélium ④) : le réseau mycélien dense
            # gonfle le détritivore du sol (collemboles brouteurs d'hyphes) — terme
            # ADDITIF, mycelium=0 ⇒ neutre. Interconnexion champignon ↔ faune (§1.1).
            signal_fn=_mycelium_signal,
            daylen_min=8.5, daylen_full=10.0,    # LARGE : sol tamponné, quasi toute l'année
            **encyclo_meta("lombric"),
        ),
        TrophicSpec(
            # cloporte = détritivore de LITIÈRE (≠ lombric, qui fait l'humus du sol).
            # Partage la ressource litière avec la limace (compétition implicite) et
            # son habitat humide. Reçoit le signal fruit POURRI (charognard, doc §C13).
            name="cloporte", category="detritivore", salt=_SALT_CLOPORTE,
            resource_fn=_litter_grid, habitat_fn=_humide_litiere_grid,
            predators=("carabe", "herisson"),    # ④d
            signal_fn=_rav_fruit_signal,         # fruit pourri → cloporte (repris de la limace)
            daylen_min=9.0, daylen_full=12.0,    # humide : fenêtre large/précoce (comme la limace)
            **encyclo_meta("cloporte"),
        ),
        # --- Catégorie `auxiliaire` : 5 espèces nommées (scission ④c, doc §2) ----
        # Chacune chasse SA proie nommée (`_espece_grid`) avec SON habitat propre.
        # Sans prédateur (sommets de chaîne de jardin, doc §5.5) ; leur frein est la
        # fenêtre + l'habitat. Le fruit frais (ex-signal de l'auxiliaire) devient la
        # RESSOURCE du merle (`_merle_food_grid`, C13).
        TrophicSpec(
            name="coccinelle", category="auxiliaire", salt=_SALT_COCCINELLE,
            resource_fn=_espece_grid("puceron"), habitat_fn=_stability_grid,
            predators=(),
            daylen_min=10.0, daylen_full=13.0,   # estivale (suit le puceron)
            **encyclo_meta("coccinelle"),
        ),
        TrophicSpec(
            name="chrysope", category="auxiliaire", salt=_SALT_CHRYSOPE,
            resource_fn=_espece_grid("puceron"), habitat_fn=_auxiliaire_habitat_grid,
            predators=(),
            daylen_min=10.0, daylen_full=13.0,   # estivale
            **encyclo_meta("chrysope"),
        ),
        TrophicSpec(
            name="carabe", category="auxiliaire", salt=_SALT_CARABE,
            resource_fn=_espece_grid("limace"), habitat_fn=_undisturbed_structure_grid,
            predators=(),
            daylen_min=9.0, daylen_full=12.0,    # nocturne→large (élargie comme la limace, sa proie)
            **encyclo_meta("carabe"),
        ),
        TrophicSpec(
            name="merle", category="auxiliaire", salt=_SALT_MERLE,
            resource_fn=_merle_food_grid, habitat_fn=_base_habitat_grid,
            predators=(),
            daylen_min=8.5, daylen_full=10.0,    # toute saison (oiseau résident, fenêtre LARGE)
            **encyclo_meta("merle"),
        ),
        TrophicSpec(
            name="herisson", category="auxiliaire", salt=_SALT_HERISSON,
            resource_fn=_espece_grid("limace"), habitat_fn=_pile_grid,
            predators=(),
            daylen_min=9.0, daylen_full=12.0,    # nocturne→large
            **encyclo_meta("herisson"),
        ),
    ]


# ---------------------------------------------------------------------------
# REGISTRE DATA-DRIVEN DES POLLINISATEURS (arc pollinisation §C/§E)
# ---------------------------------------------------------------------------
# Le champ unique `pollinisateur` (proxy `_flower_grid`, stade ≥ 2) est REMPLACÉ
# par N champs PAR TYPE. Chaque type est déclaré par DONNÉE (`PollinatorSpec`) :
# sa ressource = nectar = Σ_plantes (floraison × préférence_florale[famille]) —
# la VRAIE floraison (tronçon ①) pondérée par le type (§C.1). Ajouter un type
# (bourdon, abeille solitaire…) = ajouter une entrée, sans recoder le mécanisme.
# La densité TOTALE (somme des types) est ce que lisent `pollinator_reach`
# (brassage) et la Vigueur macro — cf. EcoFields.pollinator_density.
POLLINATOR_NAMES = ("abeille", "syrphe", "papillon", "bourdon", "osmie")

# Préférences florales PAR TYPE (placeholders, calibrage post-test §E.2). Familles
# absentes → `_ATTRACT_DEFAUT`. Anémophiles (Poaceae/Fagaceae/Juglandaceae) ≈ 0.
_ATTRACT_DEFAUT  = 0.30   # fleur « générique » d'une famille non cataloguée
_ATTRACT_ABEILLE = {      # mellifères profondes / nectarifères
    "Lamiaceae": 1.0, "Boraginaceae": 1.0, "Fabaceae": 0.85, "Rosaceae": 0.80,
    "Cucurbitaceae": 0.70, "Asteraceae": 0.60, "Brassicaceae": 0.50,
    "Apiaceae": 0.45, "Solanaceae": 0.40, "Caprifoliaceae": 0.40,
    "Amaryllidaceae": 0.30, "Urticaceae": 0.0,
    "Poaceae": 0.0, "Fagaceae": 0.10, "Juglandaceae": 0.10,
}
_ATTRACT_SYRPHE = {       # fleurs ouvertes (composées, ombellifères)
    "Apiaceae": 1.0, "Asteraceae": 1.0, "Brassicaceae": 0.90, "Boraginaceae": 0.60,
    "Rosaceae": 0.60, "Caprifoliaceae": 0.50, "Lamiaceae": 0.40,
    "Cucurbitaceae": 0.40, "Fabaceae": 0.30, "Solanaceae": 0.30,
    "Amaryllidaceae": 0.20, "Urticaceae": 0.0,
    "Poaceae": 0.0, "Fagaceae": 0.0, "Juglandaceae": 0.0,
}
_ATTRACT_PAPILLON = {     # fleurs tubulaires / composées riches en nectar
    "Lamiaceae": 1.0, "Asteraceae": 0.90, "Boraginaceae": 0.70, "Apiaceae": 0.50,
    "Fabaceae": 0.50, "Cucurbitaceae": 0.40, "Rosaceae": 0.40,
    "Brassicaceae": 0.30, "Solanaceae": 0.30, "Caprifoliaceae": 0.30,
    "Amaryllidaceae": 0.20, "Urticaceae": 0.0,
    "Poaceae": 0.0, "Fagaceae": 0.0, "Juglandaceae": 0.0,
}
_ATTRACT_BOURDON = {      # langue longue : Fabacées/Lamiacées + BUZZ Solanacées (⑤)
    "Fabaceae": 1.0, "Lamiaceae": 1.0, "Boraginaceae": 0.90, "Rosaceae": 0.70,
    "Cucurbitaceae": 0.70, "Solanaceae": 0.65, "Asteraceae": 0.55,
    "Brassicaceae": 0.45, "Apiaceae": 0.40, "Caprifoliaceae": 0.40,
    "Amaryllidaceae": 0.30, "Urticaceae": 0.0,
    "Poaceae": 0.0, "Fagaceae": 0.10, "Juglandaceae": 0.10,
}
_ATTRACT_OSMIE = {        # abeille des vergers : Rosacées (arbres fruitiers) + Apiacées (⑤)
    "Rosaceae": 1.0, "Apiaceae": 0.85, "Brassicaceae": 0.75, "Boraginaceae": 0.65,
    "Fabaceae": 0.55, "Lamiaceae": 0.50, "Asteraceae": 0.50,
    "Cucurbitaceae": 0.40, "Caprifoliaceae": 0.40, "Solanaceae": 0.35,
    "Amaryllidaceae": 0.25, "Urticaceae": 0.0,
    "Poaceae": 0.0, "Fagaceae": 0.10, "Juglandaceae": 0.10,
}


@dataclass(frozen=True)
class PollinatorSpec:
    """Type de pollinisateur, déclaré PAR DONNÉE (§E.1). Le `PopulationField`
    générique le ticke comme une guilde ordinaire : on n'expose ici que ce qui
    DIFFÈRE d'une guilde trophique.

      - attractivite        : préférence florale PAR FAMILLE botanique (le nectar
                              perçu par CE type) ; alimente la resource_fn (§C.1).
      - attractivite_defaut : préférence d'une famille non listée (fleur générique).
      - habitat_fn          : terme-source d'habitat (rondelle dédiée).
      - daylen_min/full     : fenêtre d'activité photopériodique (porte des guildes).
      - forager             : paramètres d'agent butineur (§F, tronçon ③).
      - bridge              : pont de cycle de vie larvaire optionnel (§D, tronçon
                              ⑤) — `None` pour l'abeille (nid hors sol, pas de larve
                              au sol). Source UNIQUE des ponts (build_lifecycle_bridges).
    """
    name: str
    salt: int
    attractivite: dict
    attractivite_defaut: float
    habitat_fn: Callable
    daylen_min: float
    daylen_full: float
    forager: ForagerParams
    bridge: LifeCycleBridge | None = None


def _make_nectar_grid(attractivite: dict, defaut: float) -> Callable:
    """Fabrique la resource_fn d'un type de pollinisateur (§C.1) : nectar perçu =
    Σ_plantes vivantes en floraison (floraison × préférence[famille]) réparti sur
    l'empreinte canopée, normalisé par FLOWER_REF. REMPLACE `_flower_grid` : la
    ressource suit la VRAIE floraison (①) au lieu du proxy stade ≥ 2.

    Invariant golden : floraison = 0 partout (aucune plante en fleur) ⇒ grille
    nulle ⇒ champ pollinisateur nul (comme une absence de fleur)."""
    def _grid(eco, tile, plants) -> list[list[float]]:
        g = _zero_grid(eco.rows, eco.cols)
        for p in plants:
            if not p.is_alive or p.floraison <= 0.0:
                continue
            w = p.floraison * attractivite.get(p.plant_class.family, defaut)
            if w <= 0.0:
                continue
            for (r, c) in p.foliar_plots:
                if 0 <= r < eco.rows and 0 <= c < eco.cols:
                    g[r][c] += w
        for r in range(eco.rows):
            for c in range(eco.cols):
                g[r][c] = min(1.0, g[r][c] / FLOWER_REF)
        return g
    return _grid


# Paramètres d'agent butineur PAR TYPE (§F, tronçon ③ — placeholders calibrage).
# L'abeille : nombreuse, tournée longue, large perception (forte porteuse de pollen).
# Le syrphe : moins nombreux, tournée courte, perception serrée. Le papillon :
# peu nombreux mais bonne perception (vol large). deposit/recharge homogènes.
_FORAGER_ABEILLE  = ForagerParams(n_max=12, substeps=6, perception=2, deposit=0.5, recharge=0.5)
_FORAGER_SYRPHE   = ForagerParams(n_max=8,  substeps=4, perception=1, deposit=0.4, recharge=0.5)
_FORAGER_PAPILLON = ForagerParams(n_max=6,  substeps=5, perception=2, deposit=0.4, recharge=0.5)
# Le bourdon : peu nombreux mais TRAPU, fort porteur de pollen (dépôt élevé), longue
# tournée. L'osmie : solitaire (effectif faible) mais très efficace par fleur (scopa
# pileuse → dépôt élevé), tournée courte. Placeholders §E.2, calibrage post-test.
_FORAGER_BOURDON  = ForagerParams(n_max=8,  substeps=6, perception=2, deposit=0.6, recharge=0.5)
_FORAGER_OSMIE    = ForagerParams(n_max=5,  substeps=4, perception=2, deposit=0.6, recharge=0.5)

# Ponts de cycle de vie PAR TYPE (§D, tronçon ⑤). La chenille (→ papillon) mange le
# FEUILLAGE (`_foliage_grid`, même ressource que le ravageur — elle s'ajoute à la
# pression d'herbivorie) ; la syrphe_larve (→ syrphe) prédate le RAVAGEUR
# (`_ravageur_grid` — elle est le symétrique bénéfique). Fenêtres de PONTE estivales
# (placeholders §D.5). L'abeille n'a pas de pont (nid hors sol).
_BRIDGE_PAPILLON = LifeCycleBridge(
    larva="chenille", larva_nourrie="chenille_nourrie", adult="papillon",
    resource_fn=_foliage_grid, daylen_min=11.0, daylen_full=13.0)
_BRIDGE_SYRPHE = LifeCycleBridge(
    larva="syrphe_larve", larva_nourrie="syrphe_larve_nourrie", adult="syrphe",
    resource_fn=_ravageur_grid, daylen_min=10.5, daylen_full=12.5)


def build_pollinator_registry() -> list[PollinatorSpec]:
    """Registre §E des types de pollinisateurs (donnée pure). Trois types au
    démarrage (abeille/syrphe/papillon, §E.2), extensible par données. Source
    UNIQUE de l'attractivité florale, des fenêtres photopériodiques et des
    paramètres butineurs — lue à la fois par `build_pollinator_specs` (champs) et
    par `engine._tick_butineurs` (agents §F, qui a besoin de l'attractivité)."""
    return [
        PollinatorSpec(
            name="abeille", salt=_SALT_POLLINISATEUR,
            attractivite=_ATTRACT_ABEILLE, attractivite_defaut=_ATTRACT_DEFAUT,
            habitat_fn=_abeille_habitat_grid,    # rondelle + bump ruche peuplée (§H.2)
            daylen_min=11.5, daylen_full=14.0,   # été LARGE
            forager=_FORAGER_ABEILLE,
        ),
        PollinatorSpec(
            name="syrphe", salt=_SALT_SYRPHE,
            attractivite=_ATTRACT_SYRPHE, attractivite_defaut=_ATTRACT_DEFAUT,
            habitat_fn=_auxiliaire_habitat_grid,
            daylen_min=10.5, daylen_full=13.0,   # printemps → été (précoce)
            forager=_FORAGER_SYRPHE, bridge=_BRIDGE_SYRPHE,
        ),
        PollinatorSpec(
            name="papillon", salt=_SALT_PAPILLON,
            attractivite=_ATTRACT_PAPILLON, attractivite_defaut=_ATTRACT_DEFAUT,
            habitat_fn=_pollinisateur_habitat_grid,
            daylen_min=12.5, daylen_full=14.5,   # été
            forager=_FORAGER_PAPILLON, bridge=_BRIDGE_PAPILLON,
        ),
        # --- pollinisateurs B (catalogue enrichi ⑤) — sans pont larvaire --------
        PollinatorSpec(
            name="bourdon", salt=_SALT_BOURDON,
            attractivite=_ATTRACT_BOURDON, attractivite_defaut=_ATTRACT_DEFAUT,
            habitat_fn=_pollinisateur_habitat_grid,
            daylen_min=9.5, daylen_full=12.0,    # PRÉCOCE/frais : jours courts tolérés
            forager=_FORAGER_BOURDON,            # comble la fenêtre où l'abeille n'est pas
        ),
        PollinatorSpec(
            name="osmie", salt=_SALT_OSMIE,
            attractivite=_ATTRACT_OSMIE, attractivite_defaut=_ATTRACT_DEFAUT,
            habitat_fn=_osmie_habitat_grid,      # rondelle + niche-bois (pile, §5.3)
            daylen_min=10.0, daylen_full=12.5,   # printanier (abeille des vergers)
            forager=_FORAGER_OSMIE,
        ),
    ]


def build_lifecycle_bridges() -> list[LifeCycleBridge]:
    """Ponts de cycle de vie (§D) extraits du registre §E — source UNIQUE. Deux
    au démarrage (chenille→papillon, syrphe_larve→syrphe) ; l'abeille (bridge=None)
    est écartée. Lu par EcoFields (instanciation des champs larvaires + tick)."""
    return [ps.bridge for ps in build_pollinator_registry() if ps.bridge is not None]


def build_pollinator_specs() -> list[TrophicSpec]:
    """Registre §E → TrophicSpec prêts pour le `PopulationField` générique.
    Ressource = nectar (floraison × attractivite), habitat = rondelle dédiée, ni
    prédateur ni signal fruit. Les fenêtres photopériodiques diffèrent par type
    (l'abeille large, le syrphe précoce, le papillon estival) — placeholders §E.2.
    `**encyclo_meta` splat le blurb/graphe d'encyclopédie (⑥) — DONNÉE PURE jamais
    lue par le tick, comme pour les trophiques (golden NEUTRE)."""
    return [
        TrophicSpec(
            name=ps.name, category="pollinisateur", salt=ps.salt,
            resource_fn=_make_nectar_grid(ps.attractivite, ps.attractivite_defaut),
            habitat_fn=ps.habitat_fn, predators=(),
            daylen_min=ps.daylen_min, daylen_full=ps.daylen_full,
            **encyclo_meta(ps.name),
        )
        for ps in build_pollinator_registry()
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


# ---------------------------------------------------------------------------
# PERCEPTION — carpophores échantillonnés (sprint mycélium ④, CONCEPTION §1.1)
# ---------------------------------------------------------------------------
# Les carpophores (champignons VISIBLES) sont de la PERCEPTION PURE, dérivée du
# champ `mycelium` — AUCUN état propre, recalculés à chaque snapshot (comme la vie
# macro). Ils apparaissent là où le réseau est DENSE + le sol HUMIDE (après pluie)
# + en SAISON favorable (automne). Zéro RNG (hash spatial déterministe), zéro
# retour sur la simulation → golden-NEUTRES (le CHAMP fait tout, le carpophore ne
# nourrit ni ne décompose — piège du kickoff §pièges).

_SALT_CARPOPHORE = 0x2AF001       # canal _hash_noise dédié (décorrélé des guildes)
CARPO_MYCEL_MIN  = 0.30           # seuil de densité mycélienne sous lequel rien ne fructifie
CARPO_HUMIDE_MIN = 1.5            # humidité (échelle [0,3]) sous laquelle pas de fructification
CARPO_PAR_PLOT   = 3              # nb max de carpophores par plot (saturation visuelle)
CARPO_DENS_REF   = 0.70           # densité mycélienne au-delà de laquelle le plot est plein
# Fenêtre AUTOMNE (semaines dans l'année) — dupliquée ici plutôt qu'importée de
# `sim.engine.calendrier` (couche `fields` n'importe JAMAIS `sim`, règle de couches).
# Miroir de SAISONS["automne"] = range(27, 40) ; constante simple, pas de cycle.
_CARPO_AUTOMNE = range(27, 40)


@dataclass(frozen=True)
class Carpophore:
    """Un carpophore échantillonné — donnée de RENDU pure (aucun état moteur)."""
    row: int
    col: int
    slot: int          # index dans le plot (0..n-1)
    x_frac: float      # position dans le plot ∈ [0,1], INDÉPENDANTE de la semaine
    y_frac: float
    densite: float     # densité mycélienne locale [0,1] (pilote la taille du sprite)


def sample_carpophores(eco, seed: int, week_in_year: int) -> list[Carpophore]:
    """
    Échantillonne les carpophores VISIBLES du champ `mycelium` (perception §1.1).
    PURE & déterministe : lecture seule du champ, positions par hash spatial
    indépendant de la semaine → golden-NEUTRE.

    Conditions de fructification, par plot :
      - réseau DENSE          : mycelium ≥ CARPO_MYCEL_MIN ;
      - sol HUMIDE (pluie)    : humidite ≥ CARPO_HUMIDE_MIN ;
      - SAISON favorable      : automne (saison_de(week_in_year) == "automne").
    Nombre de carpophores = floor(CARPO_PAR_PLOT × min(1, mycelium / CARPO_DENS_REF)).
    Liste VIDE si mycélium nul / sol sec / hors automne → pont neutre.
    """
    mycel = getattr(eco, "mycelium", None)
    # Saison non favorable ou pas de champ → aucun carpophore (perception muette).
    if mycel is None or week_in_year not in _CARPO_AUTOMNE:
        return []
    carpos: list[Carpophore] = []
    for r in range(eco.rows):
        for c in range(eco.cols):
            d = mycel.at_plot(r, c)
            if d < CARPO_MYCEL_MIN:
                continue
            if eco.humidite.at_plot(r, c) < CARPO_HUMIDE_MIN:
                continue
            n = int(CARPO_PAR_PLOT * min(1.0, d / CARPO_DENS_REF))
            for slot in range(n):
                x = _hash_noise(seed, _SALT_CARPOPHORE + slot, r, c)
                y = _hash_noise(seed, _SALT_CARPOPHORE + _SLOT_Y_OFFSET + slot, r, c)
                carpos.append(Carpophore(
                    row=r, col=c, slot=slot, x_frac=x, y_frac=y, densite=d))
    return carpos
