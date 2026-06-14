"""
SYMBIOSE — plants/perennials.py
Pérennes ligneuses (D21) — base commune polymorphe avec les annuelles.

Les arbres exposent la MÊME interface lumière que les annuelles
(height_at / canopy_radius_at / root_radius_at / foliage_density_at), si bien
que le LightField les traite à l'identique — zéro duplication. Seule la logique
de croissance diffère : annuelles = stades discrets, arbres = courbe d'âge
interpolée (`age_years` accumulé +1/52 par tick dans engine).

`foliage_density` est saisonnière : un arbre caduc ne projette aucune ombre
l'hiver (soleil d'hiver au sol sous un fruitier — levier permaculture majeur).

genetic_factor reste neutre (1.0) — l'héritage génétique est le Sprint
génétique/reproduction, pas ici.
"""

from __future__ import annotations
from plants.base import PlantBase, GrowthStage


class PerennialWoody(PlantBase):
    """
    Base des pérennes ligneuses. Surcharge l'interface lumière pour lire une
    courbe d'âge `age_curve` = liste triée de (age_years, hauteur_cm, rayon_cm).
    Hauteur et rayon interpolés linéairement entre points tabulés ; plateau aux
    extrémités. root_radius = canopy_radius × root_ratio.

    Un stade unique perpétuel garde la compatibilité avec les sous-systèmes
    indexés par stade (effets, strate, conflits) sans leur imposer la notion d'âge.
    """
    life_cycle = "perennial"
    winter_strategy = "dormant"
    deciduous = True
    root_ratio = 1.0
    age_curve: list[tuple] = []   # [(age_years, height_cm, canopy_radius_cm), ...]

    # --- Réponse à l'écrasement (volet 2, CONCEPTION_ECRASEMENT §4, Q4) ---
    # NB calibrage : la table §4 notait « base 0.1 × âge » pour les arbres, mais avec
    # la formule FIGÉE `intensité = INTENSITE_PIED·(1 − resistance·f_lignification(âge))`
    # une résistance de 0.1 laisse un tronc établi (f→1) à intensité 0.9 ≥ COUPE_NETTE :
    # toujours NET, donc écimable/tuable — ce qui CONTREDIT « tronc inécrasable ». On porte
    # donc une résistance HAUTE et on laisse la RAMPE d'âge (`f_lignification`) réaliser
    # l'intention : un SEMIS d'arbre (âge ≈ 0 → f ≈ 0 → résistance effective ≈ 0) s'écrase,
    # le TRONC établi (f → 1 → résistance pleine) plie (DOUX) — exactement Q4.
    resistance_ecrasement  = 0.9   # tronc établi inécrasable ; semis s'écrase via l'âge
    stimulation_ecrasement = 0.3

    # Stade unique : l'arbre ne « change pas de stade », il grandit avec l'âge.
    growth_stages = [GrowthStage(name="arbre", duration_weeks=0, strate="haute")]

    @classmethod
    def _interp(cls, age: float) -> tuple[float, float]:
        curve = cls.age_curve
        if age <= curve[0][0]:
            return curve[0][1], curve[0][2]
        if age >= curve[-1][0]:
            return curve[-1][1], curve[-1][2]
        for (a0, h0, r0), (a1, h1, r1) in zip(curve, curve[1:]):
            if a0 <= age <= a1:
                t = (age - a0) / (a1 - a0)
                return h0 + (h1 - h0) * t, r0 + (r1 - r0) * t
        return curve[-1][1], curve[-1][2]

    # Migration procédurale (tronçon 3bis) : un arbre `procedural_growth` (pommier)
    # dérive son empreinte de la STRUCTURE de segments comme les annuelles migrées —
    # on délègue alors à PlantBase (voie procédurale §G, qui lit inst.footprint). Les
    # arbres NON migrés (flag False, défaut) gardent l'age_curve interpolée au mot près.
    @classmethod
    def height_at(cls, inst) -> float:
        if cls.procedural_growth:
            return super().height_at(inst)
        h, _ = cls._interp(inst.age_years)
        return h * inst.growth_factor * inst.gene("hauteur")

    @classmethod
    def canopy_radius_at(cls, inst) -> float:
        if cls.procedural_growth:
            return super().canopy_radius_at(inst)
        _, r = cls._interp(inst.age_years)
        return r

    @classmethod
    def root_radius_at(cls, inst) -> float:
        if cls.procedural_growth:
            return super().root_radius_at(inst)
        _, r = cls._interp(inst.age_years)
        return r * cls.root_ratio

    @classmethod
    def foliage_density_at(cls, inst, saison: str | None = None) -> float:
        if cls.deciduous and saison == "hiver":
            return 0.0
        return cls.foliage_density if cls.foliage_density is not None else 0.6

    @classmethod
    def longevity(cls) -> float:
        """Override explicite par arbre ; repli = dernier point d'âge × 1,5."""
        if cls.longevity_years is not None:
            return cls.longevity_years
        return cls.age_curve[-1][0] * 1.5


# ---------------------------------------------------------------------------
# 5 ARBRES PREMIERS (D21) — courbe d'âge (age_years, hauteur_cm, rayon_cm)
# ---------------------------------------------------------------------------

class Fig(PerennialWoody):
    family = "Moraceae"
    genus  = "Ficus"
    name   = "Figuier"
    rarity = "Établie"
    keywords = ["Fruitier", "Jardin", "Ombre dense"]
    foliage_density = 0.75
    reproduction_rate = 0.15   # dispersion (M7) — gated par la lumière
    longevity_years = 80
    maturity_years = 5
    age_curve = [(0, 30, 20), (5, 200, 150), (10, 400, 250), (20, 500, 300)]


class AppleTree(PerennialWoody):
    family = "Rosaceae"
    genus  = "Malus"
    name   = "Pommier"
    rarity = "Établie"
    keywords = ["Fruitier", "Jardin", "Mellifère"]
    foliage_density = 0.60
    reproduction_rate = 0.15
    longevity_years = 70
    maturity_years = 5
    age_curve = [(0, 30, 20), (5, 200, 120), (10, 350, 200),
                 (20, 500, 280), (50, 700, 350)]
    # --- Profil de croissance procédurale (tronçon 3bis) ---
    # 1re LIGNEUSE migrée : l'empreinte (height/canopy/root) est dérivée de la
    # STRUCTURE de segments (§G), plus de l'age_curve. Cible de calibration =
    # l'allure dans la fenêtre du golden (10 ans → ~350 cm de haut, ~200 cm de
    # couronne, §E.3 « reproduire l'allure d'abord »). Le point 50 ans (700/350)
    # et la sénescence (~70 ans) sont HORS fenêtre golden → non exercés.
    # Valeurs CALIBRÉES via la sonde §C (growth_factor=1.0, cycle saisonnier réel,
    # 520 ticks) pour approcher ~350/~200 à l'an 10, montée monotone et bornée :
    #   • growth_speed=0.83 : l'apex monte ~0.83 cm/tick d'été → ~351 cm à l'an 10
    #     (et non vers l'an 5 comme à 1.5) sans atteindre le plafond max_height_cm ;
    #   • emit_length_cm=50 : une flèche de 350 cm en ~7 segments → dominance facile
    #     à tenir (≠ 44 segments à 8 cm, physiquement hors plafond) ;
    #   • max_segments=70 : flèche + charpentières dans le plafond ; à l'an 10 ~55
    #     segments → marge confortable (le filet dur n'ampute jamais la flèche) ;
    #   • wood_persistence=4000 sem. (~la vie de l'arbre) : sans ça les charpentières
    #     d'un arbre sans apex actif mourraient en ~1 an → couronne effondrée ;
    #   • apical_dominance_base=2.0 : flèche tenue ~7 segments puis relâchée avec l'âge
    #     (AUXIN_RELEASE_SCALE) → l'étalement `etale` (couronne large) ÉMERGE vers l'an 7 ;
    #   • branch_angle=70° : insertion latérale assez horizontale → étalement marqué ;
    #   • foliage_halfwidth=50 : couronne isolée ~197 cm à l'an 10 (cible 200, -1,5 %).
    #     CRITIQUE pour la SURVIE : root_r = PROC_ROOT_RATIO·canopy_r (k=1.0) et la
    #     jeune flèche n'a quasi pas de latéraux avant l'an 7 → à 30 la couronne ET
    #     les racines tiennent dans 1 plot ; tout le prélèvement d'eau (_apply_uptake,
    #     share=1/nplots) se concentre sur le plot-foyer qui s'assèche → drought_memory
    #     > 0.6 → mort par stress hydrique vers l'an 3. À 50 les racines couvrent
    #     plusieurs plots → prélèvement dilué → l'arbre survit sain les 10 ans (≠
    #     l'age_curve qui tabulait une couronne large dès l'an 5). Levier existant,
    #     scope minimal — pas de PROC_ROOT_RATIO par espèce.
    procedural_growth     = True
    port_archetype        = "etale"   # decurrent : dominance relâchée avec l'âge → couronne large
    growth_speed          = 0.83
    apical_dominance_base = 2.0
    branch_angle          = 70.0
    max_height_cm         = 700.0     # plafond (point 50 ans) — non atteint à l'an 10
    max_extent_cm         = 350.0     # plafond d'extension (point 50 ans) — non atteint à l'an 10
    emit_length_cm        = 50.0
    max_segments          = 70
    wood_persistence      = 4000
    foliage_halfwidth     = 50.0      # couronne non nulle + racines viables (cf. ci-dessus)
    organ_site            = "lateral" # fructification latérale (lu au tronçon 5)
    fruitier              = True      # porte des fruits traçables (③ ; 1re fructif. à maturity_years=5)


class CherryTree(PerennialWoody):
    family = "Rosaceae"
    genus  = "Prunus"
    name   = "Cerisier"
    rarity = "Établie"
    keywords = ["Fruitier", "Intermédiaire", "Mellifère"]
    foliage_density = 0.60
    reproduction_rate = 0.15
    longevity_years = 60
    maturity_years = 5
    age_curve = [(0, 40, 25), (5, 250, 150), (10, 500, 280),
                 (20, 700, 380), (50, 900, 450), (100, 1000, 500)]


class WalnutTree(PerennialWoody):
    family = "Juglandaceae"
    genus  = "Juglans"
    name   = "Noyer"
    rarity = "Climacique"
    keywords = ["Lisière", "Ombre dense", "Structurant"]
    foliage_density = 0.80
    pollination_mode = "wind"        # anémophile (chatons)
    pollination_radius_cm = 600.0
    reproduction_rate = 0.10   # glandée (mast) plus rare
    longevity_years = 200
    maturity_years = 15
    age_curve = [(0, 40, 25), (5, 300, 200), (10, 600, 350),
                 (20, 1000, 550), (50, 1500, 750), (100, 2500, 1000)]


class OakTree(PerennialWoody):
    family = "Fagaceae"
    genus  = "Quercus"
    name   = "Chêne"
    rarity = "Sentinelle"
    keywords = ["Lisière", "Sujet structurant", "Centenaire"]
    foliage_density = 0.75
    pollination_mode = "wind"        # anémophile (chatons)
    pollination_radius_cm = 800.0
    reproduction_rate = 0.08   # glandée (mast) rare
    longevity_years = 500
    maturity_years = 25
    age_curve = [(0, 30, 20), (5, 200, 150), (10, 400, 300),
                 (20, 700, 450), (50, 1500, 800), (100, 3000, 1200)]
