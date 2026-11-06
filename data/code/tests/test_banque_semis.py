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

Climat de LABORATOIRE repris de tests/test_stress_chronique.py (`_lab_tile` :
météo douce constante, germination/ravageurs/campagnol/risée neutralisés) ;
l'ombre est imposée en surchargeant `eco.lumiere.light_received`.

Lancement (depuis data/code/) :
  python3 -m tests.test_banque_semis
"""

import sys

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


if __name__ == "__main__":
    try:
        test_seuil_ombre_bornes()
        test_semis_tient_ombre_moyenne()
        test_semis_meurt_ombre_profonde()
    except AssertionError as e:
        print(f"[banque-semis] FAIL — {e}")
        sys.exit(1)
