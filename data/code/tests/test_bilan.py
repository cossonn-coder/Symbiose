"""
SYMBIOSE — tests/test_bilan.py
Banc de calibration du BILAN CARBONE (D140 G, sprint plante vivante ①).

Le bilan tourne EN OMBRE (personne ne lit encore `feuillage`/`reserves`) : ce banc
vérifie que ses ordres de grandeur sont sains AVANT qu'on le branche (②) :
  (a) chaque espèce du monde `full` (PLACEMENTS), adulte à sa niche en été
      (plein soleil, ou mi-ombre 0,3 pour une sciaphile), a un bilan > 0 ;
  (b) une plantule héliophile sous ombre dense a un bilan < 0 ;
  (c) un chêne adulte maintenu défeuillé en juin, réserves pleines, survit
      ≥ 20 semaines ; un semis de chêne au même régime est vide en ≤ 3 semaines ;
      un chêne défeuillé UNE fois refait son feuillage en le payant ;
  (d) un caduc qui dort l'hiver perd ≤ 30 % de sa capacité de réserve.
Plus (e) : le tick du moteur tient bien les états (une semaine d'été réelle).

Simulation de bilan ISOLÉE (fonctions pures de `sim/bilan.py`), sans monde : rapide
et déterministe. Lancement (depuis data/code/) : python3 -m tests.test_bilan
"""

import sys

from plants import PlantInstance
from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from plants.physiologie import capacite_reserve, SEUIL_SCIAPHILE
from sim.bilan import semaine_bilan
from sim.monde_complet import PLACEMENTS

ETE = dict(saison="ete", presence=1.0, hum_percue=0.8, temp=18.0, t_feuille=27.0,
           t_air=18.0, f_nut=1.0, f_allelo=1.0)


def _plante(cle, adulte=True, ans=0.0):
    cls = PLANT_CATALOGUE.get(cle) or PERENNIAL_CATALOGUE[cle]
    p = PlantInstance(cls, (0, 0))
    if adulte:
        p.current_stage = len(cls.growth_stages) - 1
        p.age_years = max(ans, float(getattr(cls, "maturity_years", 0.0)))
    else:
        p.age_years = ans
    return p


def _niche(p):
    """Lumière effective à la niche : plein soleil, mi-ombre (0,3) pour une sciaphile."""
    tol = p.plant_class.shade_tolerance_base()
    light = 0.3 if tol >= SEUIL_SCIAPHILE else 1.0
    return min(1.0, light * tol)


def test_niche_ete():
    negatifs = []
    for cle in sorted({c for c, *_ in PLACEMENTS}):
        p = _plante(cle)
        semaine_bilan(p, light_eff=_niche(p), **ETE)
        if p.bilan_net <= 0.0:
            negatifs.append((cle, round(p.bilan_net, 2)))
    assert not negatifs, f"bilan d'été ≤ 0 à la niche : {negatifs}"


def test_plantule_ombre_dense():
    p = _plante("tournesol", adulte=False)
    semaine_bilan(p, light_eff=0.1 * p.plant_class.shade_tolerance_base(), **ETE)
    assert p.bilan_net < 0.0, p.bilan_net


def _defoliation_maintenue(p, semaines):
    """Feuillage remis à 0 chaque semaine (défoliation répétée) ; renvoie la semaine
    où les réserves tombent à 0, ou None si elles tiennent."""
    for w in range(1, semaines + 1):
        p.feuillage = 0.0
        semaine_bilan(p, light_eff=1.0, **ETE)
        if p.reserves <= 0.0:
            return w
    return None


def test_chene_defeuille():
    adulte = _plante("chene")
    assert _defoliation_maintenue(adulte, 20) is None, adulte.reserves
    semis = _plante("chene", adulte=False, ans=0.2)
    w = _defoliation_maintenue(semis, 10)
    assert w is not None and w <= 3, (w, capacite_reserve(semis))
    # Défeuillé UNE fois : il refait son feuillage en le payant sur ses réserves.
    chene = _plante("chene")
    chene.feuillage = 0.0
    for _ in range(10):
        semaine_bilan(chene, light_eff=1.0, **ETE)
    assert chene.feuillage >= 0.99 and 0.5 < chene.reserves <= 1.0, \
        (chene.feuillage, chene.reserves)


def test_caduc_hiver():
    hiver = dict(ETE, saison="hiver", presence=0.0, temp=4.0, t_feuille=6.0, t_air=4.0)
    for cle, ans in (("pommier", 0.0), ("pommier", 2.0), ("chene", 0.0)):
        p = _plante(cle, ans=ans)
        cap = capacite_reserve(p)
        for _ in range(26):                # abscission → débourrement (~6 mois)
            semaine_bilan(p, light_eff=0.0, **hiver)
        perte = 1.0 - p.reserves
        assert perte <= 0.30, (cle, ans, perte, cap)
        assert perte > 0.0, (cle, ans)     # il respire quand même


def test_tick_tient_les_etats():
    """Une semaine d'été du vrai moteur : le bilan est posé sur chaque plante vivante."""
    from tools.sim_server import SimServer
    srv = SimServer()
    srv.cmd_init({"config": "full", "seed": 42})
    eng = srv.engine
    while eng.week < 16:
        eng.tick_semaine()
    vivantes = [p for t in eng.tiles for p in t.plants if p.is_alive]
    assert vivantes
    assert all(0.0 <= p.reserves <= 1.0 and 0.0 <= p.feuillage <= 1.0 for p in vivantes)
    assert any(p.bilan_net != 0.0 for p in vivantes)


if __name__ == "__main__":
    for t in (test_niche_ete, test_plantule_ombre_dense, test_chene_defeuille,
              test_caduc_hiver, test_tick_tient_les_etats):
        t()
        print(f"[bilan] OK — {t.__name__}")
    sys.exit(0)
