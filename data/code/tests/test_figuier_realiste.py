"""
SYMBIOSE — tests/test_figuier_realiste.py
Test ciblé, lancé À LA DEMANDE (hors smoke test). Sprint RELÈVE LIGNEUSE ③ (D130).

Le figuier ne fait de graine FERTILE que là où son pollinisateur obligatoire, le
blastophage, passe l'hiver (condition climatique `graine_si_hiver_min_c`) ; sinon
il se propage par REJETS DE SOUCHE (`clonal_mode = "drageon"`).

  (a) `graine_fertile(Fig)` faux sous les normales actuelles (`sim.weather`),
      vrai sous un climat doux (T_MOY/T_AMP surchargés) ; pommier toujours vrai ;
  (b) figuier mûr qui fructifie : RIEN en banque-sol, aucune recrue directe ;
  (c) figuier de 1 an : aucun rejet ; figuier mûr : au moins un rejet en
      200 semaines (déterministe, `emettre_ramets`).

Lancement (depuis data/code/) :
  python3 -m tests.test_figuier_realiste
"""

import sys

from world import Tile
from fields import init_eco
from plants import Fig, AppleTree
from sim import weather
from sim.reproduction import graine_fertile
from sim.clonal import emettre_ramets
from sim.engine import Engine

SEMAINES_RAMET = 200


def _tuile_figuier(age_years: float):
    """Un figuier d'âge donné au centre d'une tuile 20×20, plein soleil imposé."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=20, grid_cols=20)
    eco = init_eco("T0", 20, 20, humidite=1.0, fertilite=1.0, microbiome=0.3)
    fig = tile.add_plant(Fig, 10, 10)
    fig.age_years = age_years
    eco.lumiere.at_plot = lambda r, c: 0.9
    return tile, eco, fig


def test_graine_fertile_climat():
    """(a) Normandie (mois le plus froid ≈ 4 °C) : stérile ; climat doux : fertile."""
    froid = weather.T_MOY - weather.T_AMP
    assert not graine_fertile(Fig), f"figuier fertile à {froid} °C (seuil {Fig.graine_si_hiver_min_c})"
    assert graine_fertile(AppleTree), "pommier stérile : la condition fuit hors figuier"
    orig = weather.T_MOY, weather.T_AMP
    try:
        weather.T_MOY, weather.T_AMP = 16.0, 7.0      # hiver doux ≈ 9 °C
        assert graine_fertile(Fig), "figuier stérile sous climat doux"
    finally:
        weather.T_MOY, weather.T_AMP = orig
    print(f"[figuier (a)] PASS — stérile à {froid:.0f} °C, fertile à 9 °C")


def test_pas_de_graine_en_banque():
    """(b) Figuier mûr, fructification forcée : banque-sol vide, aucune recrue."""
    tile, eco, fig = _tuile_figuier(Fig.maturity_years + 2.0)
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "j1", "week": 1, "log": []}
    engine = Engine(gs)
    orig = Fig.reproduction_rate
    try:
        Fig.reproduction_rate = 1.0
        engine._reproduction(tile, eco, week=1)
    finally:
        Fig.reproduction_rate = orig
    depot = sum(eco.seed_bank.species_density(r, c, Fig)
                for r in range(20) for c in range(20))
    autres = [p for p in tile.plants if p is not fig]
    assert depot == 0.0, f"figuier dépose {depot} en banque-sol"
    assert not autres, f"{len(autres)} recrue(s) directe(s) de figuier"
    print("[figuier (b)] PASS — figuier mûr : 0 graine en banque, 0 recrue")


def _rejets(age_years: float) -> int:
    tile, eco, fig = _tuile_figuier(age_years)
    n = 0
    for wk in range(1, SEMAINES_RAMET + 1):
        n += len(emettre_ramets(tile, eco, 42, wk))
    return n


def test_rejets_de_souche():
    """(c) Jeune figuier (1 an) : pas de rejet ; figuier mûr : au moins un."""
    jeune = _rejets(1.0)
    mur = _rejets(Fig.maturity_years + 2.0)
    assert jeune == 0, f"figuier de 1 an émet {jeune} rejet(s)"
    assert mur >= 1, "figuier mûr n'émet aucun rejet en 200 semaines"
    print(f"[figuier (c)] PASS — 1 an : 0 rejet ; mûr : {mur} rejet(s) "
          f"en {SEMAINES_RAMET} semaines")


if __name__ == "__main__":
    tests = [test_graine_fertile_climat, test_pas_de_graine_en_banque,
             test_rejets_de_souche]
    echecs = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            echecs += 1
            print(f"[figuier] FAIL {t.__name__} : {e}")
    sys.exit(1 if echecs else 0)
