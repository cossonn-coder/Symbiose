"""
SYMBIOSE — plants/perennials/base.py
PerennialWoody : la base commune des pérennes ligneuses (D21).
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
    # Constitution S (sprint SANTÉ & RÉSILIENCE ②) : les ligneuses établies sont
    # l'archétype slow-tough — bois pérenne, réserves profondes, elles PLIENT là où
    # une annuelle CASSE. Base commune aux 9 arbres du catalogue (un coup encaissé
    # est divisé par 1.25 dans `erode`) ; aucun arbre ne reste au défaut silencieux.
    resilience_base = 1.25
    # Niche herbivorie racinaire (③) : pivots profonds + fort partenariat mycorhizien
    # → le campagnol ronge le chevelu de surface mais l'arbre garde des racines
    # d'ancrage hors d'atteinte → il ENCAISSE mieux la perte d'uptake (÷1.3).
    root_loss_tolerance_base = 1.3
    age_curve: list[tuple] = []   # [(age_years, height_cm, canopy_radius_cm), ...]
    ligneux = True                # D111 ②bis : bois mort (squelette + branches qui tombent)

    # --- Défauts procéduraux communs aux ligneux migrés (D91, §4 mutualisation) ---
    # Profil d'ÉCHELLE ARBRE répliqué du pommier (perennials.py AppleTree) : flèche en
    # peu de segments, bois quasi pérenne, insertion latérale horizontale (étalement),
    # feuillage assez large pour que les racines couvrent plusieurs plots (SURVIE
    # hydrique, cf. commentaire d'AppleTree). `procedural_growth` reste False sur la base :
    # la migration se fait PAR ESPÈCE (chaque arbre migré flippe le flag + surcharge son
    # gabarit `max_height_cm`/`max_extent_cm`/`growth_speed`/`auxin_release_scale`). Un
    # arbre NON migré garde son age_curve interpolée ; ces défauts ne sont alors lus par
    # personne (structure de segments inerte). Golden NEUTRE (seul AppleTree est ligneux
    # dans le smoke, et il surcharge tous ces champs).
    emit_length_cm        = 50.0    # flèche en peu de segments
    max_segments          = 70
    wood_persistence      = 4000    # ~la vie de l'arbre (sinon charpentières meurent en 1 an)
    branch_angle          = 70.0    # insertion assez horizontale → étalement
    foliage_halfwidth     = 50.0    # SURVIE hydrique (racines multi-plots) — départ, à ajuster F5
    port_archetype        = "etale"
    apical_dominance_base = 2.0
    # PORT par espèce (AUTOMNE VISIBLE ②) : cibles = docs/vegetal/croissance/fiches_arbres.md,
    # grille de réglage et chiffres = mesures/apres_port.md du sprint. `port_archetype` n'est
    # lu par aucun code : le port naît de dominance × release_scale × angle × vitesse. Vitesse
    # ≈ H(10 ans) / 422 (cm/tick : 10 ans valent ~422 ticks pleins, hiver à ×0,25).

    # Fenêtre thermique de levée (sprint germination thermique ③) : défaut LIGNEUX
    # TEMPÉRÉ — un arbre de climat tempéré (pommier, cerisier, noyer, chêne) lève sur
    # sol frais de printemps. Le figuier méditerranéen surcharge vers plus chaud.
    # NB : les arbres ont `archetype=None` → ils ne sont PAS tirés par la succession
    # spontanée (WEED_CATALOGUE) ; cette fenêtre type le catalogue (③ « type TOUT »)
    # et servira la levée d'un grain planté/disséminé, pas un chemin du golden.
    t_germ_opt = 14.0             # ligneux tempéré : lève au frais du printemps
    t_germ_tol = 11.0             # large

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
