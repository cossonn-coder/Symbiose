"""
SYMBIOSE — sim/engine/branches.py
Les branches MEURENT (D111 ②bis) : quatre causes qui font tomber du bois mort au
sol, toutes passées par le MÊME relais que l'élagage de ② (`deposer_bois_tombe` →
litière `bois` à la verticale du segment). Objectif : nourrir les champignons du
bois (③④) d'un flux CONTINU, pas seulement à la mort des arbres.

  1. OMBRE (cladoptose) — en saison feuillée, une branche latérale dont aucune
     pointe ne reçoit assez de lumière (voisins + propre couronne) meurt. Seuil et
     âge dérivés de la tolérance à l'ombre (`sim/growth/cladoptose.py`).
  2. TEMPÊTE — vent LOCAL (abri D104) × pic de rafale × turbulence de lisière :
     au-delà d'un seuil, k branches cassent, k ∝ sévérité × fragilité du bois ×
     taille de la couronne. Patron de `mortalite._wind_damage` (qui ne vise que les
     semis) : l'arbre abrité casse moins que l'exposé.
  3. NEIGE — semaine de neige sur un manteau déjà posé : la charge casse surtout
     les PERSISTANTS (sapin, lierre : le feuillage gardé retient la neige).
  4. ARBUSTES non procéduraux (framboisier, thym, lavande, myrtille) — bois mort
     largué une fois l'an à la semaine d'espèce (`bois_chute_*`), au plot du pied.

La coupe structurelle est PURE (`sim/growth`) ; ici on lit le milieu (lumière,
vent, neige) et on dépose. Zéro RNG : k arrondi par `_hash_noise`.
"""

from __future__ import annotations

from fields import _hash_noise
from fields.ecofields.constants import BOIS_MORT_PAR_CM3
from sim.growth import (shade_tolerance_effective, branches_ombragees,
                        branches_a_casser, couper_branches, seuil_et_age,
                        fenetre_ouverte)
from sim.growth.constantes import CLADO_PAR_FENETRE
from .decompo import deposer_bois_tombe

# --- Tempête (vent local × rafale × turbulence, même lecture que _wind_damage) ---
# Mesuré sur le pommier exposé du monde full [graine 1521550718, 104 sem., n=1 arbre] :
# brise 0,1-0,3, orage 0,3-0,56, tempête 0,6-0,66. Le seuil laisse passer les
# orages forts et les tempêtes, pas la brise.
CASSE_VENT_SEUIL = 0.45
CASSE_VENT_REF   = 0.30   # surcroît au-dessus du seuil → sévérité ≈ 1
CASSE_K          = 2.0    # branches cassées par unité de sévérité × fragilité (couronne pleine)
COURONNE_PLEINE  = 30     # segments : au-delà, la couronne prend tout le vent
FRAC_MAX_CASSE   = 0.25   # une casse emporte au plus ce quart de la structure
# --- Neige (manteau `eco.snow` ∈ [0,1] de la tuile, lu une semaine de Neige) ---
NEIGE_SEUIL      = 0.30   # manteau sous lequel la charge ne casse rien
NEIGE_K          = 2.0    # branches cassées par unité de charge × fragilité
NEIGE_CADUC      = 0.30   # un caduc défeuillé retient peu de neige


def _k_arrondi(x: float, seed: int, week: int, plant, canal: int) -> int:
    """Arrondi stochastique DÉTERMINISTE : partie entière + 1 si le hachage tombe
    sous la partie fractionnaire (espérance = x, zéro RNG)."""
    if x <= 0.0:
        return 0
    n = int(x)
    h = _hash_noise(seed ^ (plant.form_seed or 0), week, canal, 3)
    return n + (1 if h < x - n else 0)


def _taille(plant) -> float:
    return min(1.0, len(plant.segments) / COURONNE_PLEINE)


def _cladoptose(plant, eco, saison: str, seed: int, week: int) -> list:
    """Rythme BORNÉ (②ter) : une semaine sur CLADO_FENETRE par arbre, au plus
    CLADO_PAR_FENETRE branche (la plus sombre)."""
    if not fenetre_ouverte(plant, seed, week):
        return []
    cls = plant.plant_class
    densite = cls.foliage_density_at(plant, saison)
    if densite <= 0.0:
        return []          # défeuillé : pas de signal d'ombre (l'arbre dort)
    lf = getattr(eco, "lumiere", None)
    l_plante = lf.light_received(plant) if lf is not None else 1.0
    seuil, age_min = seuil_et_age(shade_tolerance_effective(plant))
    roots = branches_ombragees(plant, l_plante, densite, seuil, age_min,
                               n_max=CLADO_PAR_FENETRE)
    return couper_branches(plant, roots)


def _casse_vent(plant, eco, gust_peak: float, seed: int, week: int) -> list:
    vent = getattr(eco, "vent", None)
    if vent is None or gust_peak <= 0.0:
        return []
    v = vent.at_plot(*plant.position) * gust_peak
    turb = getattr(eco, "turbulence", None)
    if turb is not None:
        v *= turb.at_plot(*plant.position)
    sev = max(0.0, v - CASSE_VENT_SEUIL) / CASSE_VENT_REF
    if sev <= 0.0:
        return []
    x = sev * plant.plant_class.fragilite_bois * CASSE_K * _taille(plant)
    k = _k_arrondi(x, seed, week, plant, 1)
    return couper_branches(plant, branches_a_casser(plant, k, seed, week, FRAC_MAX_CASSE))


def _casse_neige(plant, eco, seed: int, week: int) -> list:
    snow = getattr(eco, "snow", 0.0)
    if snow < NEIGE_SEUIL:
        return []
    cls = plant.plant_class
    charge = snow * (NEIGE_CADUC if cls.deciduous else 1.0)
    x = charge * cls.fragilite_bois * NEIGE_K * _taille(plant)
    k = _k_arrondi(x, seed, week, plant, 2)
    return couper_branches(plant, branches_a_casser(plant, k, seed + 1, week, FRAC_MAX_CASSE))


def _chute_arbuste(plant, eco, week_in_year: int) -> float:
    """Ligneux sans structure : bois mort largué une fois l'an, ∝ maturité du pied
    (stade courant / dernier stade), seulement après sa première année."""
    cls = plant.plant_class
    if (cls.bois_chute_cm3 <= 0.0 or week_in_year != cls.bois_chute_semaine
            or plant.age_weeks < 52):
        return 0.0
    n = len(cls.growth_stages)
    maturite = (plant.current_stage / (n - 1)) if n > 1 else 1.0
    masse = cls.bois_chute_cm3 * BOIS_MORT_PAR_CM3 * maturite
    if masse <= 0.0:
        return 0.0
    eco.deposer_litiere(*plant.position, "bois", masse)
    return masse


def mort_des_branches(tile, eco, saison: str, week: int, week_in_year: int,
                      seed: int, gust_peak: float, is_neige: bool) -> list:
    """Point d'entrée du tick (étape 9c-ter, APRÈS la croissance : la structure du
    tick est à jour). Renvoie les lignes de log (🪵 par plante et par cause)."""
    log = []
    for plant in tile.plants:
        cls = plant.plant_class
        if not plant.is_alive or not cls.ligneux:
            continue
        if not cls.procedural_growth:
            if _chute_arbuste(plant, eco, week_in_year) > 1e-4:
                log.append(f"    🪵 Bois sec largué {plant.name}@{plant.position}")
            continue
        causes = (("ombre", _cladoptose(plant, eco, saison, seed, week)),
                  ("tempête", _casse_vent(plant, eco, gust_peak, seed, week)),
                  ("neige", _casse_neige(plant, eco, seed, week) if is_neige else []))
        for cause, tombes in causes:
            if deposer_bois_tombe(plant, tombes, eco) > 1e-4:
                log.append(f"    🪵 Branche morte ({cause}) {plant.name}@{plant.position}")
        if any(t for _, t in causes):
            plant.update_footprint()      # couronne amputée → empreinte à jour
    return log
