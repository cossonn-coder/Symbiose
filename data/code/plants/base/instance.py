"""
SYMBIOSE — plants/base/instance.py
Instance vivante de plante (état + empreinte dérivée de la structure) et
notification de conflit spatial. S'appuie sur `stades` (GrowthStage, Segment) et
`empreintes` (_plots_in_radius, PROC_ROOT_RATIO) ; ne connaît pas les familles
(PlantBase n'est référencé que via `plant_class`, en duck-typing).
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field

from constants import PLOT_CM
from ..genetics import (clamp_gene, ADAPTOGENIC_GENES,
                        DEFENSE_COST, DEFENSE_PLANCHER)
from .empreintes import _plots_in_radius, PROC_ROOT_RATIO
from .stades import GrowthStage, Segment

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
    cold_memory: float = 0.0        # intégration lente du froid sub-létal vécu [0-1]
                                    # (plasticité ① — cold hardening : signal température < seuil
                                    #  doux, AU-DELÀ du gel létal). Pilote l'expression de rusticite_froid.
    infection_memory: float = 0.0   # intégration lente de la pression pathogène vécue [0-1]
                                    # (plasticité ① — SAR / priming immunitaire). Pilote l'expression
                                    #  de resistance_pathogene.
    stress_memory: float = 0.0      # intégration des perturbations subies [0-1]
                                    # stress↑ → croissance↓ mais résistance↑
    # Marques de symptômes ÉVÉNEMENTIELS (sémiologie ②) : maladie/gel/grêle n'ont
    # PAS d'état persistant relisible (un coup ponctuel), contrairement aux
    # stresseurs chroniques recalculés à la volée. On les MÉMORISE donc ici, cause
    # → intensité [0-1], et on les fait DÉCROÎTRE chaque tick (decay_symptoms) :
    # une plante frappée puis épargnée retrouve son aspect en ~3-4 semaines.
    # Écrit par la résolution d'un ReduceHealth à cause typée (resolution.py),
    # lu par sim.semiologie.leaf_symptoms. PUR cosmétique : aucune reboucle sur
    # santé/croissance ni présence dans _PLANT_ATTRS → golden NEUTRE.
    symptom_marks: dict = field(default_factory=dict)
    # Vecteur de gènes héréditaire (D22). Vide ⇒ tous neutres (1.0). Rempli à la
    # naissance (semis génétique : succession, renouvellement, semis joueur).
    genes: dict = field(default_factory=dict)
    # État d'EXPRESSION plastique (sprint plasticité ①, patron `symptom_marks`).
    # {gène adaptogène: facteur ∈ [EXPR_MIN, EXPR_MAX]}, défaut 1.0 = phénotype =
    # génotype. Glisse vers une cible pilotée par la mémoire de stress correspondante
    # (_update_physiology, lerp à hystérèse). Lu via expressed_gene() — INERTE au
    # tronçon ① (aucun consommateur ne le lit encore → comportement inchangé) ; hors
    # `_PLANT_ATTRS` du golden. Priming maternel l'initialisera ≠ 1.0 (tronçon ④).
    expression: dict = field(
        default_factory=lambda: {g: 1.0 for g in ADAPTOGENIC_GENES})
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
    # Organes-fruits traçables (décompo·compost ③, absorbe D19). Vide → aucun
    # fruit (défaut : golden inchangé tant que rien ne noue). Peuplé à la nouaison
    # par engine._tick_fruits (espèces `fruitier` parvenues à `maturity_years`),
    # mûri/tombé/mangé ensuite. Cf. dataclass Fruit.
    fruits: list = field(default_factory=list)
    # État floral moteur (arc pollinisation, tronçon ① — CONCEPTION_POLLINISATION §A).
    # `floraison` = intensité de floraison ∈ [0,1] (l'« assiette » que liront la
    # ressource des champs pollinisateurs §C, les butineurs §F et la dose de pollen
    # §B) ; `gdd_accum` = degrés-jours cumulés (forçage thermique, reset annuel).
    # INERTES à ce tronçon : écrits par engine._tick_floraison mais lus par PERSONNE
    # (B/C/F branchés ensuite) → golden NEUTRE. Hors `_PLANT_ATTRS` du golden.
    floraison: float = 0.0
    gdd_accum: float = 0.0
    # Dose de pollen conspécifique reçue (arc pollinisation, tronçon ③ — §B.1/§F.4).
    # Accumulateur PAR plante : incrémenté à CHAQUE dépôt d'un butineur (§F)
    # transportant du pollen de la MÊME espèce (constance florale mécanique), non
    # plus une intégrale `densité × floraison`. Écrit par engine._tick_butineurs ;
    # lu par PERSONNE à ce tronçon (la nouaison §B le lira au tronçon ④, et le
    # remettra à 0 à la nouaison). Hors `_PLANT_ATTRS` du golden → golden NEUTRE.
    pollen_recu: float = 0.0
    # Front de floraison pour la nouaison « en fin de floraison, par plante »
    # (arc pollinisation, tronçon ④ — §B.2). Passe à True quand `floraison`
    # franchit le seuil de pleine floraison ; la nouaison (engine._tick_fruits)
    # la consomme (→ False) quand `floraison` retombe (fleurs fanées), ce qui
    # arme la cohorte suivante. Remplace le rendez-vous global FRUIT_NOUAISON_WEEK.
    # Hors `_PLANT_ATTRS` du golden → golden NEUTRE.
    a_fleuri: bool = False

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

    def expressed_gene(self, name: str) -> float:
        """Phénotype EFFECTIF d'un gène adaptogène = génotype × expression plastique
        (sprint plasticité). `expression[name]` ∈ [EXPR_MIN, EXPR_MAX] traduit le
        durcissement acquis sous stress vécu ; 1.0 (défaut) ⇒ phénotype = génotype.
        Le produit repasse par clamp_gene → jamais hors des limites physiologiques
        dures. Pour un gène NON adaptogène (absent d'`expression`) : == gene(name)."""
        return clamp_gene(self.gene(name) * self.expression.get(name, 1.0))

    def cout_defense(self) -> float:
        """Compromis croissance/défense (plasticité ③, conception §2.4 — philo #2).
        La SUR-expression (part de chaque expression AU-DESSUS de 1.0) re-route la
        vigueur vers la défense au lieu de s'y ajouter : une plante qui a durci ses
        tolérances sous stress croît et convalesce plus lentement → moins de graines
        au final. Facteur ∈ ]0, 1] multiplié sur les lectures de `gene("vigueur")`
        DANS LE TICK (croissance/convalescence) — PAS la façade read-only
        `vigueur_plante`. Désexprimer (expression ≤ 1.0) ne coûte JAMAIS ; borné par
        `DEFENSE_PLANCHER` (> 0) → la défense ne peut pas annuler la vigueur. Neutre
        (toutes expressions à 1.0) ⇒ 1.0 (non-régression du tick non acclimaté)."""
        surexpression = sum(max(0.0, e - 1.0) for e in self.expression.values())
        return max(DEFENSE_PLANCHER, 1.0 - DEFENSE_COST * surexpression)

    def decay_symptoms(self, decay: float, epsilon: float = 0.02) -> None:
        """Estompe les marques de symptômes ÉVÉNEMENTIELS (sémiologie ②).
        Chaque marque est multipliée par `decay` (<1) à chaque tick ; sous `epsilon`
        elle est PURGÉE (la plante a cicatrisé). Appelée une fois par tick de plante,
        à côté des autres mémoires physiologiques (croissance._update_physiology).
        No-op si aucune marque (cas nominal du smoke → golden NEUTRE)."""
        if not self.symptom_marks:
            return
        for cause in list(self.symptom_marks):
            v = self.symptom_marks[cause] * decay
            if v < epsilon:
                del self.symptom_marks[cause]
            else:
                self.symptom_marks[cause] = v

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
