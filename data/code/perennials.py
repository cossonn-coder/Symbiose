"""
SYMBIOSE — perennials.py
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
from models import PlantBase, GrowthStage


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

    @classmethod
    def height_at(cls, inst) -> float:
        h, _ = cls._interp(inst.age_years)
        return h * inst.growth_factor * inst.gene("hauteur")

    @classmethod
    def canopy_radius_at(cls, inst) -> float:
        _, r = cls._interp(inst.age_years)
        return r

    @classmethod
    def root_radius_at(cls, inst) -> float:
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


PERENNIAL_CATALOGUE: dict[str, type] = {
    "figuier":  Fig,
    "pommier":  AppleTree,
    "cerisier": CherryTree,
    "noyer":    WalnutTree,
    "chene":    OakTree,
}
