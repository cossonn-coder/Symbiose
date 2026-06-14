"""
SYMBIOSE — plants/base.py
Hiérarchie de plantes : empreintes métriques, registre d'effets, stade de
croissance, instance de plante, notification de conflit, PlantBase abstrait +
5 familles botaniques.

Sprint éclairement (D20-D21) :
  - Empreintes métriques : hauteur + rayon de canopée + rayon racinaire par
    stade (cm), opacité d'ombre `foliage_density` par espèce. Les anciens
    `foliar_offsets`/`root_offsets` (dessinés à la main) sont REMPLACÉS par une
    dérivation rayon → plots (cf. _plots_in_radius).
  - Position continue `x_cm, y_cm` (cadrage hybride : lue par le LightField ;
    le sous-sol reste indexé au plot via plot_foyer).
  - Interface lumière polymorphe (height_at / canopy_radius_at / root_radius_at /
    foliage_density_at) partagée avec les pérennes ligneuses (perennials.py).
"""

from __future__ import annotations
import math
from abc import ABC
from dataclasses import dataclass, field
from typing import Callable

from constants import PLOT_CM


def _plots_in_radius(x_cm: float, y_cm: float, radius_cm: float) -> list[tuple]:
    """
    Plots (row, col) dont le centre cartésien tombe dans un disque de rayon
    `radius_cm` centré sur la position continue (x_cm, y_cm).

    Embedding cartésien orthogonal : centre du plot (r, c) = (c·50+25, r·50+25).
    Le plot-foyer est toujours inclus. Peut renvoyer des plots hors grille — les
    consommateurs (uptake, conflits…) filtrent via is_valid_plot.

    Échelle de référence (plante au centre de son plot) :
        rayon ≤ 35      → 1 plot (foyer)
        rayon 50–70     → 5 plots (croix)
        rayon 71–99     → 9 plots (bloc 3×3)
    """
    fr = int(y_cm // PLOT_CM)
    fc = int(x_cm // PLOT_CM)
    k = int(radius_cm // PLOT_CM) + 1
    r2 = radius_cm * radius_cm
    out = []
    for dr in range(-k, k + 1):
        for dc in range(-k, k + 1):
            r = fr + dr
            c = fc + dc
            cx = c * PLOT_CM + PLOT_CM / 2
            cy = r * PLOT_CM + PLOT_CM / 2
            if (cx - x_cm) ** 2 + (cy - y_cm) ** 2 <= r2:
                out.append((r, c))
    if (fr, fc) not in out:
        out.append((fr, fc))
    return out

# ---------------------------------------------------------------------------
# DÉFAUTS PAR STRATE — extensibilité du catalogue
# ---------------------------------------------------------------------------
#
# Une espèce hérite GRATUITEMENT de ces valeurs via sa strate par stade. Elle
# ne renseigne explicitement (override sur GrowthStage / classe) que ce qui
# dévie (rosette large, racines traçantes, feuillage opaque…). Ajouter une
# espèce « standard » ne demande donc qu'une hauteur par stade et sa strate.
#
#   height   : hauteur potentielle de repli (cm) si canopy_height non précisé
#   canopy_r : rayon de canopée par défaut (cm)
#   root_r   : rayon racinaire par défaut (cm)
#   density  : opacité d'ombre par défaut [0–1]

STRATE_DEFAULTS = {
    "sol":       {"height": 10,  "canopy_r": 25, "root_r": 30, "density": 0.40},
    "basse":     {"height": 30,  "canopy_r": 30, "root_r": 30, "density": 0.50},
    "moyenne":   {"height": 80,  "canopy_r": 50, "root_r": 55, "density": 0.55},
    "haute":     {"height": 180, "canopy_r": 55, "root_r": 60, "density": 0.65},
    "grimpante": {"height": 150, "canopy_r": 25, "root_r": 55, "density": 0.50},
}

# Tolérance à l'ombre de RÉFÉRENCE par strate (compétition intra-plot, Q6).
# >1 = sciaphile (prospère/lève à l'ombre), <1 = héliophile (pénalisé dès
# l'ombrage). Défaut écologique : les strates basses du sous-bois tolèrent
# l'ombre, les hautes la fuient. Valeur de DÉPART (calibrage §4), modulée
# individuellement par le gène `tolerance_ombre`. La base d'espèce est dérivée
# de la strate du stade MATURE (cf. PlantBase.shade_tolerance_base).
STRATE_SHADE_TOLERANCE = {
    "sol":       1.25,
    "basse":     1.25,
    "moyenne":   1.00,
    "haute":     0.90,
    "grimpante": 1.00,
}

# Empreinte procédurale (D29 réorienté, tronçon 2) — rayon racinaire dérivé de la
# couronne (§G, §8 acté : pas de structure souterraine). k calibré : la tomate
# veut root ≈ canopy (drip-line). Module-level (1 espèce migrée) → per-espèce plus tard.
PROC_ROOT_RATIO = 1.0   # root_radius = PROC_ROOT_RATIO · canopy_radius

# ---------------------------------------------------------------------------
# REGISTRE D'EFFETS (callbacks complexes)
# ---------------------------------------------------------------------------

EFFECT_REGISTRY: dict[str, Callable] = {}

def register_effect(name: str):
    """Décorateur pour enregistrer un callback d'effet complexe."""
    def decorator(fn: Callable) -> Callable:
        EFFECT_REGISTRY[name] = fn
        return fn
    return decorator

# ---------------------------------------------------------------------------
# STADE DE CROISSANCE
# ---------------------------------------------------------------------------

@dataclass
class GrowthStage:
    name: str                        # "semis", "jeune", "adulte", "mature"
    duration_weeks: int              # durée minimale avant passage au stade suivant (0 = vivace)
    strate: str                      # "haute","moyenne","basse","sol","grimpante"
    vigueur_cost: int = 0            # coût Vigueur pour atteindre ce stade
    effects: list[dict] = field(default_factory=list)  # effets data-driven du stade
    callback: str | None = None      # clé dans EFFECT_REGISTRY si effet complexe
    # Empreintes métriques (cm) — None ⇒ défaut de la strate (STRATE_DEFAULTS)
    canopy_height: float | None = None   # hauteur potentielle de la canopée
    canopy_radius: float | None = None   # rayon de la canopée (ombre + foliar_plots)
    root_radius:   float | None = None   # rayon racinaire (uptake + root_plots)

# ---------------------------------------------------------------------------
# SEGMENT — unité de la structure morphologique (croissance procédurale)
# ---------------------------------------------------------------------------
#
# D29 réorienté (croissance procédurale, tronçon 1). Une plante n'est plus
# décrite par son seul stade : elle porte un ARBRE de segments enraciné au
# collet (CONCEPTION_CROISSANCE.md §C). Pour CE tronçon la structure est
# INERTE — elle pousse à côté (sim/growth.py) mais n'est PAS encore lue par
# l'empreinte (height_at vient toujours des stades). Le câblage = tronçon 2.
#
# Représentation actée : base + direction + longueur (l'extrémité = base +
# dir·length_cm). `has_bud` (bourgeon axillaire dormant) matérialise le §D.3 :
# un segment porte un bourgeon qui peut débourrer une fois quand l'auxine
# locale tombe sous le seuil. `organs` reste vide ici (tronçon 5).

@dataclass
class Segment:
    parent: int | None               # index du segment porteur (None = collet)
    base: tuple                      # (x_cm, y_cm, z_cm) — origine
    dir: tuple                       # vecteur directeur unitaire 3D
    length_cm: float                 # longueur courante
    thickness_cm: float              # épaisseur (épaissit avec l'âge → vieux bois)
    age_weeks: int                   # âge du segment
    auxin: float                     # niveau d'auxine local [0,1] (cf. growth §D.1)
    is_apex: bool                    # True si extrémité de croissance active
    has_bud: bool = True             # bourgeon axillaire dormant (consommé au débourrement)
    organs: list = field(default_factory=list)  # feuilles/fleurs/fruits (tronçon 5)

    # --- Sérialisation (croissance procédurale, tronçon 6 — §J) ---
    # Contrat borné : on ne sérialise QUE le bois (les 9 champs structurels). Les
    # `organs` (feuilles/fleurs/fruits) sont régénérés à la volée par le rendu
    # (tronçon 5) → JAMAIS stockés = l'« option d'allègement » §J, satisfaite par
    # construction. JSON-friendly : `base`/`dir` deviennent des listes, restituées
    # en tuples au chargement (round-trip fidèle, cf. tests/test_croissance.py).
    def to_dict(self) -> dict:
        return {
            "parent": self.parent,
            "base": list(self.base),
            "dir": list(self.dir),
            "length_cm": self.length_cm,
            "thickness_cm": self.thickness_cm,
            "age_weeks": self.age_weeks,
            "auxin": self.auxin,
            "is_apex": self.is_apex,
            "has_bud": self.has_bud,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Segment":
        return cls(
            parent=d["parent"],
            base=tuple(d["base"]),
            dir=tuple(d["dir"]),
            length_cm=d["length_cm"],
            thickness_cm=d["thickness_cm"],
            age_weeks=d["age_weeks"],
            auxin=d["auxin"],
            is_apex=d["is_apex"],
            has_bud=d.get("has_bud", True),
        )

# ---------------------------------------------------------------------------
# INSTANCE DE PLANTE (avant PlantBase pour la forward ref)
# ---------------------------------------------------------------------------

@dataclass
class PlantInstance:
    plant_class: type                # ex: Tomato
    position: tuple                  # (row, col) du plot-foyer sur la tuile
    current_stage: int = 0          # index dans plant_class.growth_stages
    age_weeks: int = 0              # âge dans le stade courant
    age_years: float = 0.0         # âge total (pérennes ligneuses : courbe d'âge)
    health: int = 3                 # 3=sain, 2=affaibli, 1=malade, 0=mort
    growth_factor: float = 1.0      # intégration de la lumière reçue → module la hauteur
    # Position continue (cadrage hybride : lue par le LightField). Initialisée au
    # centre du plot-foyer si non fournie (cf. __post_init__).
    x_cm: float | None = None
    y_cm: float | None = None
    # Mémoire physiologique
    shade_memory: float = 0.0       # intégration lente de l'ombre vécue [0-1]
    drought_memory: float = 0.0     # intégration lente du stress hydrique [0-1]
    asphyxie_memory: float = 0.0    # intégration lente de l'excès d'eau [0-1]
                                    # miroir HAUT de drought_memory (même lerp, anoxie soutenue → santé↓)
    stress_memory: float = 0.0      # intégration des perturbations subies [0-1]
                                    # stress↑ → croissance↓ mais résistance↑
    # Vecteur de gènes héréditaire (D22). Vide ⇒ tous neutres (1.0). Rempli à la
    # naissance (semis génétique : succession, renouvellement, semis joueur).
    genes: dict = field(default_factory=dict)
    # Structure morphologique (croissance procédurale, D29 réorienté, tronçon 1).
    # Vide à la déclaration ⇒ une plante naît avec UN segment apex au collet
    # (cf. __post_init__). INERTE à ce tronçon : poussée par sim/growth.py mais
    # pas encore lue par l'empreinte (height_at vient des stades — câblage = t.2).
    segments: list = field(default_factory=list)
    # Cache d'empreinte dérivée de la structure (croissance procédurale, tronçon 2).
    # None ⇒ pas encore calculé (avant le 1er tick de grow_plant) ; recalculé une
    # fois par tick en fin de grow_plant pour les espèces `procedural_growth`. Les
    # classmethods d'empreinte le lisent ; repli à la volée si None (update_footprint).
    footprint: dict | None = None
    # État post-mortem (décompo·compost ②, phase B). Defaults → plante vivante
    # strictement inchangée (golden de structure intact). À la mort, le sujet n'est
    # plus retiré : `sim.effects.deposer_mort` le marque squelette, puis
    # `engine._tick_skeletons` fait sèche→couchée→fragmentation du `bois_restant`
    # avant le retrait final (seul point de retrait des morts).
    morte: bool = False          # True dès la mort (skip biologie via is_alive)
    stade_mort: str = ""         # "" vivant · "seche" debout · "couchee" au sol
    bois_restant: float = 0.0    # réservoir de bois à fragmenter en litière `bois`
    semaines_mort: int = 0       # compteur sèche→couchée

    def __post_init__(self):
        if self.x_cm is None or self.y_cm is None:
            r, c = self.position
            self.x_cm = c * PLOT_CM + PLOT_CM / 2
            self.y_cm = r * PLOT_CM + PLOT_CM / 2
        if not self.segments:
            # Collet : un seul segment apex, vertical, au point sol (x,y,z=0).
            # auxin=1.0 (plein) — recalculé chaque tick par growth.py de toute
            # façon ; la valeur initiale n'influe pas la dynamique.
            self.segments = [Segment(
                parent=None, base=(self.x_cm, self.y_cm, 0.0),
                dir=(0.0, 0.0, 1.0), length_cm=1.0, thickness_cm=0.5,
                age_weeks=0, auxin=1.0, is_apex=True,
            )]

    def gene(self, name: str) -> float:
        """Facteur génétique pour un gène (1.0 = neutre si absent du vecteur)."""
        return self.genes.get(name, 1.0)

    def update_footprint(self) -> None:
        """
        Recalcule l'empreinte dérivée de la structure (CONCEPTION_CROISSANCE §G).
        Pure géométrie sur `segments` + leviers de profil de l'espèce — aucun import
        de sim (respect des couches : plants ne dépend pas de growth). Appelée en fin
        de grow_plant (structure à jour) ; repli à la volée si lue avant le 1er tick.

          height   ← max(z) des extrémités de segments (la flèche la plus haute) ;
          canopy_r ← extension horizontale max + foliage_halfwidth (couronne non
                     nulle même en flèche droite, point dur §C : feuilles absentes
                     avant le tronçon 5) ;
          root_r   ← PROC_ROOT_RATIO · canopy_r (rayon dérivé, §8 — pas de racine réelle).
        """
        segs = self.segments
        cx, cy = segs[0].base[0], segs[0].base[1]
        max_z = 0.0
        max_horiz = 0.0
        for s in segs:
            tx = s.base[0] + s.dir[0] * s.length_cm
            ty = s.base[1] + s.dir[1] * s.length_cm
            tz = s.base[2] + s.dir[2] * s.length_cm
            if tz > max_z:
                max_z = tz
            h = math.hypot(tx - cx, ty - cy)
            if h > max_horiz:
                max_horiz = h
        canopy_r = max_horiz + self.plant_class.foliage_halfwidth
        self.footprint = {"height": max_z, "canopy_r": canopy_r,
                          "root_r": canopy_r * PROC_ROOT_RATIO}

    def footprint_value(self, key: str) -> float:
        """Lecture du cache d'empreinte, avec repli (recalcul si pas encore peuplé)."""
        if self.footprint is None:
            self.update_footprint()
        return self.footprint[key]

    # --- Sérialisation de la STRUCTURE (croissance procédurale, tronçon 6 — §J) ---
    # La structure de segments fait partie de l'état → sérialisée dans le futur save
    # JSON. Bornée (§D.6 : `MAX_SEGMENTS`) → taille maîtrisée. On ne stocke QUE les
    # segments (le bois) ; l'empreinte (`footprint`) et les organes sont REGÉNÉRÉS
    # (cache recalculé au 1er grow_plant / organes par le rendu) → exclus du save.
    def structure_to_dict(self) -> list:
        """Sérialise la structure = liste de segments (champs §C.1). JSON-friendly."""
        return [s.to_dict() for s in self.segments]

    def restore_structure(self, data: list) -> None:
        """Restaure la structure depuis une liste de dicts (cf. structure_to_dict).
        Invalide le cache d'empreinte (recalculé au prochain grow_plant / à la volée
        via footprint_value)."""
        self.segments = [Segment.from_dict(d) for d in data]
        self.footprint = None

    @property
    def stage(self) -> GrowthStage:
        return self.plant_class.growth_stages[self.current_stage]

    @property
    def name(self) -> str:
        return self.plant_class.name

    @property
    def plot_foyer(self) -> tuple:
        """Plot de rattachement au sous-sol = floor(position continue / 50 cm)."""
        return (int(self.y_cm // PLOT_CM), int(self.x_cm // PLOT_CM))

    @property
    def current_height(self) -> float:
        """Hauteur effective (cm) = potentiel du stade/âge × growth_factor."""
        return self.plant_class.height_at(self)

    @property
    def canopy_radius(self) -> float:
        return self.plant_class.canopy_radius_at(self)

    @property
    def root_radius(self) -> float:
        return self.plant_class.root_radius_at(self)

    @property
    def foliar_plots(self) -> list[tuple]:
        """Plots occupés en aérien — dérivés du rayon de canopée."""
        return _plots_in_radius(self.x_cm, self.y_cm,
                                self.plant_class.canopy_radius_at(self))

    @property
    def root_plots(self) -> list[tuple]:
        """Plots exploités en souterrain — dérivés du rayon racinaire."""
        return _plots_in_radius(self.x_cm, self.y_cm,
                                self.plant_class.root_radius_at(self))

    @property
    def is_alive(self) -> bool:
        return self.health > 0

    def regress(self) -> bool:
        """
        Régresse d'un stade suite à un conflit spatial non résolu.
        Retourne True si la plante meurt (déjà au stade 0).
        """
        if self.current_stage > 0:
            self.current_stage -= 1
            self.age_weeks = 0
            return False
        else:
            self.health = 0
            return True  # mort

    def advance_stage(self) -> bool:
        """
        Tente de passer au stade suivant.
        Retourne True si un nouveau stade est atteint.
        """
        stages = self.plant_class.growth_stages
        if self.current_stage < len(stages) - 1:
            self.current_stage += 1
            self.age_weeks = 0
            return True
        return False

    def __repr__(self) -> str:
        return (
            f"{self.name}@{self.position} "
            f"[{self.stage.name}] age={self.age_weeks}w santé={self.health}/3"
        )

# ---------------------------------------------------------------------------
# NOTIFICATION DE CONFLIT SPATIAL
# ---------------------------------------------------------------------------

@dataclass
class ConflictNotification:
    plants: list[PlantInstance]      # plantes en conflit (2 ou plus)
    plots: list[tuple]               # plots (row, col) litigieux
    conflict_type: str               # "foliar" ou "root"
    weeks_active: int = 0           # auto-incrémenté chaque semaine
    resolved: bool = False

    def tick(self) -> None:
        """Incrémente le compteur hebdomadaire."""
        if not self.resolved:
            self.weeks_active += 1

    def loser(self) -> PlantInstance:
        """
        La plante la plus jeune (âge_weeks le plus bas) perd.
        En cas d'égalité, la dernière dans la liste.
        """
        return min(self.plants, key=lambda p: p.age_weeks)

    def __repr__(self) -> str:
        noms = " vs ".join(p.name for p in self.plants)
        return (
            f"CONFLIT [{self.conflict_type}] {noms} "
            f"plots={self.plots} semaines={self.weeks_active}"
        )

# ---------------------------------------------------------------------------
# HIÉRARCHIE DES PLANTES — Niveau 1 : PlantBase (abstrait)
# ---------------------------------------------------------------------------

class PlantBase(ABC):
    """
    Classe abstraite racine.
    Les sous-classes définissent family, genus, name, growth_stages, etc.

    Interface lumière polymorphe (height_at / canopy_radius_at / root_radius_at /
    foliage_density_at) : implémentation par défaut = lecture des stades, avec
    repli sur STRATE_DEFAULTS. Les pérennes ligneuses (perennials.py) la
    surchargent pour interpoler des courbes d'âge. Le LightField n'appelle QUE
    ces méthodes → annuelles et arbres traités uniformément, zéro duplication.
    """
    family: str = ""
    genus: str = ""
    name: str = ""
    rarity: str = "Établie"              # Pionnière · Établie · Climacique · Ancienne · Sentinelle
    keywords: list[str] = []
    space_tolerance_weeks: int = 3       # délai avant régression en cas de conflit non résolu
    growth_stages: list[GrowthStage] = []
    family_effects: list[dict] = []      # effets partagés au niveau famille
    # Cycle de vie saisonnier
    life_cycle: str = "perennial"        # "annual" | "biennial" | "perennial"
    winter_strategy: str = "dormant"     # "die" | "dormant" | "evergreen"
    deciduous: bool = False              # perd son feuillage l'hiver (ombre nulle)
    archetype: str | None = None         # archétype succession écologique
    reproduction_rate: float = 0.02      # production graines par semaine
    # Pollinisation (D22) — pilote l'appariement biparental (reproduction.py)
    pollination_mode: str = "insect"     # "wind" | "insect" | "self"
    pollination_radius_cm: float = 150.0 # portée de croisement (distance euclidienne)
    foliage_density: float | None = None # opacité d'ombre [0-1] ; None ⇒ défaut strate
    # Mortalité réaliste (D27) — longévité + âge de fructification
    longevity_years: float | None = None # longévité (ans) ; None ⇒ défaut par life_cycle
    maturity_years: float = 0.0          # âge de 1re fructification (renouvellement arbres)
    fungal_susceptibility: float = 0.5   # sensibilité aux maladies fongiques [0-1]
    temp_min_growth: float = 5.0         # °C — seuil de croissance (météo 02) ; en deçà, stagnation. Extensible par espèce.
    # Tolérance à l'ombre de référence (compétition intra-plot, Q6). None ⇒ dérivée
    # de la strate du stade mature (STRATE_SHADE_TOLERANCE) ; override explicite si
    # l'espèce dévie de sa strate (ex. annuelle héliophile en strate basse).
    shade_tolerance: float | None = None

    # --- Profil de croissance procédurale (D29 réorienté, tronçon 2) ---
    # Leviers PAR ESPÈCE lus par sim/growth.py (CONCEPTION_CROISSANCE §E.1). Les
    # DÉFAUTS reproduisent les anciennes constantes de module de growth.py → une
    # espèce non migrée pousse exactement comme au tronçon 1 (golden de structure
    # intact). Une espèce migrée (procedural_growth=True) règle ces leviers sur ses
    # growth_stages/age_curve (« reproduire l'allure d'abord », §E.3).
    growth_speed:          float = 2.0    # cm/tick d'allongement de l'apex (≡ GROWTH_SPEED)
    port_archetype:        str   = "fleche"   # stratégie de port (§E.2) — descriptif ici
    apical_dominance_base: float = 1.0    # FORCE de dominance = production d'auxine d'un apex au repos (1.0 = nominal ≡ AUXIN_SOURCE ; >1 = flèche tenue plus longtemps, cf. Tomato)
    branch_angle:          float = 50.0   # angle d'insertion des latéraux (degrés, ≡ BRANCH_ANGLE)
    phototropism_strength: float = 0.30   # sensibilité au gradient de lumière (MARQUÉ par défaut, Q3 — l'apex se penche vers le clair ; 0 = tout droit ; Nico tranche la valeur finale à la maquette, tronçon 4)
    wood_persistence:      int   = 60     # longévité du bois sans apex (semaines, ≡ WOOD_PERSISTENCE)
    max_height_cm:         float = 200.0  # plafond de hauteur de l'apex (≡ MAX_REACH_CM, défaut d'arbre)
    max_extent_cm:         float = 200.0  # plafond d'extension horizontale de la couronne
    emit_length_cm:        float = 8.0    # cm : granularité de segment émis par l'apex (≡ EMIT_LENGTH)
    max_segments:          int   = 40     # plafond dur de segments (≡ MAX_SEGMENTS ; haut pour un arbre)
    organ_site:            str   = "terminal"  # "terminal"|"lateral" — naissance fleurs/fruits (tronçon 5)
    foliage_halfwidth:     float = 0.0    # demi-largeur de feuillage autour d'un segment (couronne non nulle)
    # Bascule vers la voie procédurale (empreinte dérivée de la structure §G). OFF par
    # défaut : l'espèce garde l'ancien chemin (stades). True = migrée (ici : Tomato).
    procedural_growth:     bool  = False

    # --- Réponse à l'écrasement (volet 2, CONCEPTION_ECRASEMENT §5) ---
    # DEUX axes indépendants, LUS UNIQUEMENT par sim.actions.ecraser_plante (geste
    # joueur event-driven, hors tick) → défauts NEUTRES = golden intact (au repos
    # rien ne les lit). Calibrage de DÉPART par espèce dans species.py/perennials.py.
    resistance_ecrasement:  float = 0.5   # ∈ [0,1] — résistance STRUCTURELLE : pilote
                                          # l'intensité au seam (haute → reste DOUX/plie ;
                                          # basse → NET/casse). Modulée par l'âge (Q4).
    stimulation_ecrasement: float = 0.0   # ∈ [0,1] — BÉNÉFICE de repousse : seuil qui
                                          # ÉPARGNE la santé en régime NET (basilic 0.85
                                          # → écimé mais repart ; tournesol 0.05 → décapité).

    # --- Interface lumière (polymorphe) ---

    @classmethod
    def height_at(cls, inst: "PlantInstance") -> float:
        """Hauteur effective (cm). Voie procédurale (§G) : max(z) de la structure ×
        génétique (growth_factor déjà intégré dans la croissance). Sinon : potentiel
        du stade × growth_factor × génétique."""
        if cls.procedural_growth:
            return inst.footprint_value("height") * inst.gene("hauteur")
        st = inst.stage
        h = st.canopy_height if st.canopy_height is not None \
            else STRATE_DEFAULTS[st.strate]["height"]
        return h * inst.growth_factor * inst.gene("hauteur")

    @classmethod
    def canopy_radius_at(cls, inst: "PlantInstance") -> float:
        if cls.procedural_growth:
            return inst.footprint_value("canopy_r")
        st = inst.stage
        return st.canopy_radius if st.canopy_radius is not None \
            else STRATE_DEFAULTS[st.strate]["canopy_r"]

    @classmethod
    def root_radius_at(cls, inst: "PlantInstance") -> float:
        if cls.procedural_growth:
            return inst.footprint_value("root_r")
        st = inst.stage
        return st.root_radius if st.root_radius is not None \
            else STRATE_DEFAULTS[st.strate]["root_r"]

    @classmethod
    def foliage_density_at(cls, inst: "PlantInstance", saison: str | None = None) -> float:
        """Opacité d'ombre. Les caducs renvoient 0 l'hiver (cf. pérennes)."""
        if cls.deciduous and saison == "hiver":
            return 0.0
        return cls.foliage_density if cls.foliage_density is not None \
            else STRATE_DEFAULTS[inst.stage.strate]["density"]

    @classmethod
    def shade_tolerance_base(cls) -> float:
        """Tolérance à l'ombre de RÉFÉRENCE de l'espèce (sciaphile >1, héliophile
        <1). Override explicite via `shade_tolerance`, sinon dérivée de la strate
        du stade MATURE (dernier `growth_stages`). Modulée individuellement par le
        gène `tolerance_ombre` : tolérance effective = base × gene("tolerance_ombre").
        Lue en germination (lumière effective) et en croissance (growth_factor)."""
        if cls.shade_tolerance is not None:
            return cls.shade_tolerance
        strate = cls.growth_stages[-1].strate if cls.growth_stages else "moyenne"
        return STRATE_SHADE_TOLERANCE.get(strate, 1.0)

    @classmethod
    def longevity(cls) -> float:
        """
        Longévité (ans). Override explicite (longevity_years) sinon défaut par
        cycle de vie : annuelle = ∞ (meurt à l'hiver, sénescence sans objet),
        bisannuelle = 2, vivace herbacée = 5.
        """
        if cls.longevity_years is not None:
            return cls.longevity_years
        return {"annual": math.inf, "biennial": 2.0,
                "perennial": 5.0}.get(cls.life_cycle, 5.0)

    def get_all_effects(self, stage_index: int) -> list[dict]:
        """Fusionne les effets famille + les effets du stade courant."""
        if stage_index >= len(self.growth_stages):
            return self.family_effects[:]
        return self.family_effects + self.growth_stages[stage_index].effects

    @classmethod
    def describe(cls) -> str:
        return f"{cls.name} ({cls.family} › {cls.genus}) — {cls.rarity}"

# ---------------------------------------------------------------------------
# NIVEAU 2 : FAMILLES BOTANIQUES
# ---------------------------------------------------------------------------

class Solanaceae(PlantBase):
    """
    Famille : Solanacées.
    Sensibilité familiale au mildiou : chaque rondelle Maladie active
    dégrade la santé une fois par semaine.
    """
    family = "Solanaceae"
    space_tolerance_weeks = 2  # réagissent vite à la compétition
    fungal_susceptibility = 1.0  # mildiou — la plus sensible
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "condition": {"rondelle": "maladie", "min": 1},
            "action": "reduce_health",
            "amount": 1,
            "description": "Sensibilité familiale au mildiou"
        }
    ]


class Fabaceae(PlantBase):
    """
    Famille : Légumineuses.
    Fixation N₂ active en permanence — enrichit la rondelle Lombric du sol.
    """
    family = "Fabaceae"
    space_tolerance_weeks = 4  # très tolérantes à la compétition
    # Bonus spécifique légumineuses : fixation N₂ → fertilité. L'enrichissement
    # du microbiome n'est plus scripté ici — il émerge des exsudats universels
    # (boucle rhizosphère, _apply_exudates).
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "action": "inject_field",
            "variable": "fertilite",
            "amount": 0.03,
            "cible": "local",
            "description": "Fixation N₂ — enrichit la fertilité du sol"
        }
    ]


class Asteraceae(PlantBase):
    """
    Famille : Astéracées.
    Floraison mellifère familiale — ajoute un pollinisateur à chaque floraison.
    """
    family = "Asteraceae"
    space_tolerance_weeks = 3
    fungal_susceptibility = 0.4
    family_effects = [
        {
            "type": "floraison",
            "action": "add_rondelle",
            "variable": "pollinisateur",
            "amount": 1,
            "max": 3,
            "description": "Floraison mellifère familiale"
        }
    ]


class Lamiaceae(PlantBase):
    """
    Famille : Lamiacées (aromatiques).
    Répulsion naturelle des nuisibles pour les plantes adjacentes.
    """
    family = "Lamiaceae"
    space_tolerance_weeks = 4  # très tolérantes
    fungal_susceptibility = 0.2  # aromatiques — peu sensibles
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "action": "adjacency_bonus",
            "bonus": "reduce_maladie_rondelle",
            "amount": 1,
            "description": "Aromatiques — répulsion naturelle des nuisibles au voisinage"
        }
    ]

class Poaceae(PlantBase):
    """
    Famille : Graminées.
    Compétition hydrique intense — racines fibreuses épuisent l'humidité locale.
    """
    family = "Poaceae"
    space_tolerance_weeks = 6   # très tolérantes à la compétition
    fungal_susceptibility = 0.4
    pollination_mode = "wind"        # graminées anémophiles
    pollination_radius_cm = 300.0    # le pollen voyage loin au vent
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "action": "inject_field",
            "variable": "humidite",
            "amount": -0.06,
            "cible": "local",
            "description": "Racines fibreuses — compétition hydrique intense"
        }
    ]
