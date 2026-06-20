"""
SYMBIOSE — plants/base/familles.py
PlantBase abstrait (interface lumière polymorphe + profils de croissance/écrasement)
et les 5 familles botaniques de base. S'appuie sur `stades` (GrowthStage) et
`empreintes` (STRATE_DEFAULTS, STRATE_SHADE_TOLERANCE) ; `PlantInstance` n'est
référencé qu'en annotation (forward ref string), donc pas importé.

Sprint éclairement (D20-D21) :
  - Empreintes métriques : hauteur + rayon de canopée + rayon racinaire par
    stade (cm), opacité d'ombre `foliage_density` par espèce. Les anciens
    `foliar_offsets`/`root_offsets` (dessinés à la main) sont REMPLACÉS par une
    dérivation rayon → plots (cf. empreintes._plots_in_radius).
  - Position continue `x_cm, y_cm` (cadrage hybride : lue par le LightField ;
    le sous-sol reste indexé au plot via plot_foyer).
  - Interface lumière polymorphe (height_at / canopy_radius_at / root_radius_at /
    foliage_density_at) partagée avec les pérennes ligneuses (perennials.py).
"""

from __future__ import annotations
import math
from abc import ABC

from .empreintes import STRATE_DEFAULTS, STRATE_SHADE_TOLERANCE
from .stades import GrowthStage

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
    # Organes-fruits traçables (décompo·compost ③, absorbe D19). Critère
    # d'ÉLIGIBILITÉ fruitière : seules les espèces au profil reproducteur fruitier
    # portent des `fruits` (Tomato, AppleTree — périmètre de REPRO_BY_SEASON).
    # Gate complet (engine._tick_fruits) = `fruitier ET age_years >= maturity_years`
    # → un jeune plant (pommier < 5 ans) ne fructifie pas. Défaut False = inerte.
    fruitier: bool = False
    # Phénologie florale (arc pollinisation, tronçon ① — CONCEPTION_POLLINISATION §A.4).
    # Fenêtre de floraison PAR ESPÈCE : double porte GDD (« la plante est prête »)
    # + photopériode (« c'est la saison »). Défauts ESTIVAUX (jours longs) ; calibrage
    # post-test. Une stratégie jours-courts (automne) = un seul couple de seuils à
    # régler. INERTE à ce tronçon (rien ne lit `floraison` → golden NEUTRE).
    gdd_floraison:    float = 200.0   # degrés-jours cumulés requis (base T_BASE_FLORAISON)
    bloom_daylen_min: float = 13.5    # h de jour : borne basse de la fenêtre photopériodique
    bloom_daylen_max: float = 16.5    # h de jour : borne haute (estival → au-delà du pic 16 h)
    fungal_susceptibility: float = 0.5   # sensibilité aux maladies fongiques [0-1]
    temp_min_growth: float = 5.0         # °C — seuil de croissance (météo 02) ; en deçà, stagnation. Extensible par espèce.
    # Fenêtre pH d'espèce (sprint physico-chimie, tronçon ⑤). Cloche d'acidité
    # `bell(ph, ph_opt, ph_tol)` lue en germination/succession (porte) ET en
    # croissance/vigueur (façade `vigueur_plante`). DÉFAUT NEUTRE : `ph_tol` LARGE
    # (≈ 3.0) ⇒ `bell ≈ 1.0` sur toute la plage [4.0, 8.5] → une espèce non
    # spécifiée est INSENSIBLE au pH (golden ~neutre). Override par espèce (myrtille
    # acidophile 4.8/0.8, lavande/thym calciphiles 7.4/1.1). La valeur 3.0 est un
    # LITTÉRAL ici (≡ PH_TOL_DEFAUT de la conception §3) : la couche `plants` est la
    # plus basse et n'importe JAMAIS `fields` (règle de couches) — pas d'import du
    # constants.py d'`ecofields`. Cf. CONCEPTION_SOL_PH.md §2.3.
    ph_opt: float = 6.8                  # pH optimal (défaut ≈ neutre)
    ph_tol: float = 3.0                  # demi-largeur LARGE → cloche plate → insensible au pH
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
            "variable": "n",
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

class Urticaceae(PlantBase):
    """
    Famille : Urticacées (orties).
    Bioindicatrice/améliorante des sols riches en azote : injection locale de
    fertilité, comme une légumineuse mais par minéralisation d'une biomasse
    azotée abondante (patron Fabaceae). Anémophile (fleurs discrètes pollinisées
    par le vent → aucune retombée sur les butineurs, _ATTRACT_* = 0).
    """
    family = "Urticaceae"
    space_tolerance_weeks = 5        # robuste, encaisse bien la compétition
    fungal_susceptibility = 0.3
    pollination_mode = "wind"        # anémophile — fleurs discrètes
    pollination_radius_cm = 300.0    # le pollen voyage loin au vent
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "action": "inject_field",
            "variable": "n",
            "amount": 0.03,
            "cible": "local",
            "description": "Biomasse azotée — enrichit la fertilité du sol"
        }
    ]


class Amaryllidaceae(PlantBase):
    """
    Famille : Amaryllidacées (aulx, oignons).
    Répulsif familial : les composés soufrés éloignent les nuisibles du
    voisinage. Faute d'action moteur qui injecte du NÉGATIF dans le champ
    `ravageur` (cf. note ③), on réutilise le levier défensif data-pur des
    Lamiacées (adjacency_bonus → protège la santé des voisines). Une vraie
    baisse du champ `ravageur` resterait une action moteur à créer (dette).
    """
    family = "Amaryllidaceae"
    space_tolerance_weeks = 4
    fungal_susceptibility = 0.3
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "action": "adjacency_bonus",
            "bonus": "reduce_maladie_rondelle",
            "amount": 1,
            "description": "Répulsif soufré — protège les voisines au voisinage"
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


class Ericaceae(PlantBase):
    """
    Famille : Éricacées (myrtille, bruyère, rhododendron).
    Plantes ACIDOPHILES/calcifuges des landes et sous-bois acides : leur signature
    n'est PAS un family_effect (aucun flux injecté), elle EST leur fenêtre pH basse
    (`ph_opt`/`ph_tol` par espèce, tronçon ⑤) — elles ne lèvent ni ne prospèrent sur
    calcaire, et y subissent la chlorose ferrique (jaunissement). Famille INERTE au
    repos (pas de family_effects) : la fenêtre fait tout le travail diégétique.
    """
    family = "Ericaceae"
    space_tolerance_weeks = 4
    fungal_susceptibility = 0.3
    family_effects = []
