"""
SYMBIOSE — tests/test_banque_semis.py
Test ciblé, lancé À LA DEMANDE (hors smoke test). Sprint RELÈVE LIGNEUSE ① (D130).

Couvre la « banque de semis » : un JEUNE ligneux ombragé VÉGÈTE au lieu de mourir.
Le seuil de `shade_memory` au-delà duquel `shade_stress_damage` abîme une plante
monte avec la petitesse d'un ligneux (`seuil_ombre`) : point de compensation
lumineux bas d'un semis (peu de tissus à entretenir). Mais une ombre PROFONDE
tue quand même — le seuil monte, il ne disparaît pas.

  (a) petit pommier (âge 0) à lumière reçue 0,35 → SURVIT 5 ans ;
  (b) le même à lumière 0,10                     → MEURT ;
  (c) `seuil_ombre` d'un ligneux haut (≥ H_GAULE) et d'une herbacée = 0,55.

Tronçon ② (pose cohérente, recrutement direct `_reproduction`) :
  (d) arbre mûr isolé, couronne 400 cm : la recrue tombe SOUS la couronne (au-delà
      de l'ancien rayon fixe 150 cm, à distance ≤ couronne + 1 plot) ;
  (e) tuile entière à lumière < 1 − SEUIL_SEMIS → AUCUNE recrue.

Climat de LABORATOIRE repris de tests/test_stress_chronique.py (`_lab_tile` :
météo douce constante, germination/ravageurs/campagnol/risée neutralisés) ;
l'ombre est imposée en surchargeant `eco.lumiere.light_received`.

Lancement (depuis data/code/) :
  python3 -m tests.test_banque_semis
"""

import math
import sys

from world import Tile
from fields import init_eco
from plants import AppleTree, Zucchini
from sim.engine import Engine
from sim.effects.perturbations import (seuil_ombre, H_GAULE, SEUIL_SEMIS,
                                       SHADE_DAMAGE_THRESHOLD)
from tests.test_stress_chronique import _lab_tile, _mort

ANS = 5
SEMAINES = 52 * ANS


def run_semis(light: float, weeks: int = SEMAINES):
    """Un pommier semé (âge 0) sous une lumière reçue constante `light`.
    Renvoie (semaine_de_mort | None, vitalité, shade_memory MAX, seuil final).
    shade_memory MAX : la dormance hivernale la fait redescendre (mortalite.py),
    l'état final (fin d'année) ne dit donc pas l'ombre vécue en saison."""
    tile, eco = _lab_tile()
    plant = tile.add_plant(AppleTree, 3, 3)
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "j1", "week": 1, "log": []}
    engine = Engine(gs)
    sm_max = 0.0
    for wk in range(weeks):
        # tick_light mute l'objet en place : on reforce la lecture à chaque tick.
        eco.lumiere.light_received = lambda p, _l=light: _l
        engine.tick_semaine()
        sm_max = max(sm_max, plant.shade_memory)
        if _mort(plant):
            return wk + 1, plant.vitalite, sm_max, seuil_ombre(plant)
        gs["log"].clear()
    return None, plant.vitalite, sm_max, seuil_ombre(plant)


def test_semis_tient_ombre_moyenne():
    """(a) Lumière 0,35 : shade_memory ~0,65 > 0,55 (un adulte souffrirait) mais
    < seuil d'un semis → le petit pommier attend, vivant."""
    mort, vit, sm, seuil = run_semis(0.35)
    assert sm > SHADE_DAMAGE_THRESHOLD, (
        f"l'ombre ne s'installe pas (shade_memory {sm:.2f} ≤ {SHADE_DAMAGE_THRESHOLD})")
    assert mort is None, (
        f"le semis meurt S{mort} à lumière 0,35 (vitalité {vit:.2f}, "
        f"shade_memory {sm:.2f}, seuil {seuil:.2f}) — pas de banque de semis")
    print(f"[banque-semis (a)] PASS — pommier vivant après {ANS} ans à lumière 0,35 "
          f"(shade_memory {sm:.2f}, seuil {seuil:.2f}, vitalité {vit:.2f})")


def test_semis_meurt_ombre_profonde():
    """(b) Lumière 0,10 : shade_memory → 0,90 > SEUIL_SEMIS → le semis meurt."""
    mort, vit, sm, seuil = run_semis(0.10)
    assert mort is not None, (
        f"le semis SURVIT à l'ombre profonde (vitalité {vit:.2f}, shade_memory "
        f"{sm:.2f}, seuil {seuil:.2f}) — la voie ombre ne mord plus")
    print(f"[banque-semis (b)] PASS — pommier mort S{mort} à lumière 0,10 "
          f"(shade_memory {sm:.2f}, seuil {seuil:.2f})")


def test_seuil_ombre_bornes():
    """(c) Gaule haute et herbacée : seuil inchangé 0,55 ; semis : SEUIL_SEMIS."""
    tile, _eco = _lab_tile()
    arbre = tile.add_plant(AppleTree, 3, 3)
    herbe = tile.add_plant(Zucchini, 1, 1)
    assert abs(seuil_ombre(herbe) - SHADE_DAMAGE_THRESHOLD) < 1e-9, seuil_ombre(herbe)
    h0 = AppleTree.height_at(arbre)
    attendu = SHADE_DAMAGE_THRESHOLD + (SEUIL_SEMIS - SHADE_DAMAGE_THRESHOLD) \
        * (1.0 - h0 / H_GAULE)
    assert abs(seuil_ombre(arbre) - attendu) < 1e-9, (seuil_ombre(arbre), attendu)
    # Ligneux haut : on impose la hauteur (classe surchargée le temps du test).
    orig = AppleTree.height_at
    try:
        AppleTree.height_at = classmethod(lambda cls, inst: H_GAULE * 1.5)
        assert abs(seuil_ombre(arbre) - SHADE_DAMAGE_THRESHOLD) < 1e-9, seuil_ombre(arbre)
    finally:
        AppleTree.height_at = orig
    print(f"[banque-semis (c)] PASS — seuil herbacée/gaule {SHADE_DAMAGE_THRESHOLD}, "
          f"semis {seuil_ombre(arbre):.3f} (hauteur {h0:.1f} cm)")


COURONNE_CM = 400.0   # couronne imposée du parent (tests d/e)


def run_pose(lumiere_de):
    """Un pommier MÛR isolé au centre d'une tuile 20×20, couronne imposée à
    COURONNE_CM, fructification forcée (reproduction_rate 1) ; la lumière au sol
    est imposée par plot (`lumiere_de(r, c)`). Un seul appel à `_reproduction`.
    Renvoie (parent, liste des recrues)."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=20, grid_cols=20)
    eco = init_eco("T0", 20, 20, humidite=1.0, fertilite=1.0, microbiome=0.3)
    parent = tile.add_plant(AppleTree, 10, 10)
    parent.age_years = AppleTree.maturity_years + 1.0
    eco.lumiere.at_plot = lumiere_de
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "j1", "week": 1, "log": []}
    engine = Engine(gs)
    orig_r, orig_rate = AppleTree.canopy_radius_at, AppleTree.reproduction_rate
    try:
        AppleTree.canopy_radius_at = classmethod(lambda cls, inst: COURONNE_CM)
        AppleTree.reproduction_rate = 1.0
        engine._reproduction(tile, eco, week=1)
    finally:
        AppleTree.canopy_radius_at, AppleTree.reproduction_rate = orig_r, orig_rate
    return parent, [p for p in tile.plants if p is not parent]


def _dist_cm(a, b) -> float:
    (ar, ac), (br, bc) = a.position, b.position
    return 50.0 * math.hypot(ar - br, ac - bc)


def test_pose_sous_couronne():
    """(d) Seul plot vivable : à 7 plots (350 cm) du parent — hors de l'ancien
    rayon fixe (150 cm + 1 plot), sous la couronne de 400 cm → la recrue y naît."""
    cible = (10, 17)
    parent, recrues = run_pose(lambda r, c: 0.9 if (r, c) == cible else 0.05)
    assert len(recrues) == 1, f"{len(recrues)} recrue(s) au lieu d'une"
    d = _dist_cm(parent, recrues[0])
    assert recrues[0].position == cible, recrues[0].position
    assert d <= COURONNE_CM + 50.0, f"recrue à {d:.0f} cm > couronne {COURONNE_CM}"
    print(f"[banque-semis (d)] PASS — recrue @{recrues[0].position} à {d:.0f} cm "
          f"(couronne {COURONNE_CM:.0f} cm)")


def test_pas_de_pose_a_l_ombre():
    """(e) Toute la tuile sous la lumière de survie d'un semis → aucune recrue."""
    seuil = 1.0 - SEUIL_SEMIS
    _parent, recrues = run_pose(lambda r, c: seuil - 0.01)
    assert not recrues, f"{len(recrues)} recrue(s) posée(s) à lumière < {seuil:.2f}"
    print(f"[banque-semis (e)] PASS — aucune recrue à lumière < {seuil:.2f}")


if __name__ == "__main__":
    try:
        test_seuil_ombre_bornes()
        test_semis_tient_ombre_moyenne()
        test_semis_meurt_ombre_profonde()
        test_pose_sous_couronne()
        test_pas_de_pose_a_l_ombre()
    except AssertionError as e:
        print(f"[banque-semis] FAIL — {e}")
        sys.exit(1)
