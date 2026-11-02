"""
SYMBIOSE — tests/test_fleurs_lisiere.py
Colonies de fleurs des bords (LISIÈRE NUE ①, D124) : géométrie déterministe, floraison
par couleur, nourriture des butineurs, bloc du pont.

Usage (depuis data/code/) : python3 -m tests.test_fleurs_lisiere
"""
import sys

from fields import init_eco
from fields.fleurs_lisiere import (BUTINEURS_MAX, COLONIES_PAR_TYPE, COULEURS,
                                   colonies_secteur, floraison_couleur)
from fields.peripherie import generer_ceinture
from fields.population import _ATTRACT_DEFAUT, _ATTRACT_SYRPHE, _make_nectar_grid
from sim.engine import Engine
from tools.simserver.peripherie_route import ceinture_block
from tools.simserver.server import SimServer
from world import Tile

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'OK ' if cond else 'XX '} {name}" + (f" — {detail}" if detail else ""))


def _ceinture(nord="prairie", sud="foret"):
    """Ceinture contrastée : prairie au nord, rien qui fleurisse ailleurs."""
    base = generer_ceinture(7)
    for s, typ in zip(base, (nord, "falaise", sud, "falaise")):
        s["type"] = typ
    return base


def _monde(origin_y):
    tile = Tile(tile_id="T", soil_type="terre", grid_rows=8, grid_cols=8,
                origin_x_cm=800.0, origin_y_cm=origin_y)
    eco = init_eco("T", 8, 8, humidite=1.5, fertilite=1.2, microbiome=0.3)
    return tile, eco


def _nectar(tile, eco):
    return _make_nectar_grid(_ATTRACT_SYRPHE, _ATTRACT_DEFAUT)(eco, tile, tile.plants)


def test_geometrie():
    print("\n[1] géométrie")
    check("déterministe", colonies_secteur(42, 0, "prairie") == colonies_secteur(42, 0, "prairie"))
    check("change avec la graine", colonies_secteur(42, 0, "prairie") != colonies_secteur(43, 0, "prairie"))
    for typ in ("foret", "falaise"):
        check(f"aucune colonie en {typ}",
              all(not colonies_secteur(s, c, typ) for s in range(50) for c in range(4)))
    for typ, (nmin, nmax) in COLONIES_PAR_TYPE.items():
        ns = {len(colonies_secteur(s, c, typ)) for s in range(200) for c in range(4)}
        check(f"{typ} : {nmin} à {nmax} colonies", ns == set(range(nmin, nmax + 1)), str(sorted(ns)))
    disjointes = True
    for s in range(100):
        cols = colonies_secteur(s, 2, "prairie")
        for a, b in zip(cols, cols[1:]):
            disjointes &= a.u_cm + a.rayon_u_cm < b.u_cm - b.rayon_u_cm
    check("des vides entre les taches, le long du bord", disjointes)


def test_floraison():
    print("\n[2] floraison")
    for coul in COULEURS:
        hors = [w for w in range(1, 53) if floraison_couleur(coul, w) > 0.0]
        check(f"{coul} : fleurit au printemps seulement", hors and max(hors) < 22 and min(hors) >= 3,
              f"wiy {min(hors)}-{max(hors)}")
    check("le bouton d'or précède la marguerite",
          floraison_couleur("jaune", 5) > floraison_couleur("blanc", 5))


def test_nourriture():
    print("\n[3] nourriture")
    tile, eco = _monde(0.0)
    check("sans ceinture : rien", eco.fleurs_bord is None)
    eco.maj_fleurs_bord(None, 7, 10, (800.0, 0.0))
    check("sans ceinture : maj reste None", eco.fleurs_bord is None)
    check("sans ceinture : ressource nulle",
          all(v == 0.0 for row in _nectar(tile, eco) for v in row))

    eco.maj_fleurs_bord(_ceinture(), 7, 30, (800.0, 0.0))
    check("hors saison : None", eco.fleurs_bord is None)
    check("hors saison : ressource nulle",
          all(v == 0.0 for row in _nectar(tile, eco) for v in row))

    eco.maj_fleurs_bord(_ceinture(), 7, 10, (800.0, 0.0))
    plots = eco._fleurs_plots
    g = _nectar(tile, eco)
    check("en fleur, au bord d'une prairie : ressource > 0", max(max(r) for r in g) > 0.0,
          f"{max(max(r) for r in g):.3f}")
    check("plafond existant respecté", max(max(r) for r in g) <= 1.0)
    eco.maj_fleurs_bord(_ceinture(), 7, 11, (800.0, 0.0))
    check("mémoïsé : la carte n'est pas recalculée la semaine suivante", eco._fleurs_plots is plots)

    t_sud, e_sud = _monde(1600.0)
    e_sud.maj_fleurs_bord(_ceinture(), 7, 10, (800.0, 1600.0))
    check("au bord d'une forêt, loin de toute colonie : rien", e_sud.fleurs_bord is None)


def _butineurs(origin_y, ceinture):
    """Moyenne de butineurs après une saison de fleurs, sans aucune plante."""
    tile, eco = _monde(origin_y)
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    gs = {"tiles": [tile], "eco": {"T": eco}, "scores": {}, "seed": 7, "ceinture": ceinture,
          "current_player": "joueur_1", "week": 1, "log": []}
    engine = Engine(gs)
    pic = 0.0
    for _ in range(20):
        engine.tick_semaine()
        gs["log"].clear()
        pic = max(pic, sum(eco.pollinator_density(r, c) for r in range(8) for c in range(8)) / 64)
    return pic


def test_butineurs():
    print("\n[4] butineurs nourris, sans plante ni population de départ")
    pres, loin = _butineurs(0.0, _ceinture()), _butineurs(1600.0, _ceinture())
    check("près d'une colonie : butineurs présents", pres > 0.05, f"{pres:.3f}")
    # Pas 0 : le syrphe répond déjà à l'effet de lisière (`lisiere_w`), sans fleurs.
    check("au bord sans colonie : presque rien", loin < pres * 0.1, f"{loin:.3f}")
    check("déterministe", pres == _butineurs(0.0, _ceinture()))


def test_pont():
    print("\n[5] pont")
    srv = SimServer()
    srv.cmd_init({"config": "full", "seed": 42})
    bloc = srv.cmd_step_week({})["snapshot"]["ceinture"]
    check("colonies par secteur", all("colonies" in s and "floraison" in s for s in bloc))
    gs = srv.engine.game_state
    for _ in range(14):
        rep = srv.cmd_step_week({})
    bloc = rep["snapshot"]["ceinture"]
    comptes = [k["butineurs"] for s in bloc for k in s["colonies"]]
    check("en mai-juin, des butineurs sur les colonies", max(comptes) > 0, str(comptes))
    check("compte borné", max(comptes) <= BUTINEURS_MAX)
    check("lecture pure : deux blocs de suite identiques",
          ceinture_block(gs) == ceinture_block(gs))
    for _ in range(20):                 # automne : plus une fleur
        rep = srv.cmd_step_week({})
    bloc = rep["snapshot"]["ceinture"]
    check("hors saison : aucun insecte",
          all(k["butineurs"] == 0 for s in bloc for k in s["colonies"]))
    check("hors saison : floraison nulle",
          all(v == 0.0 for s in bloc for v in s["floraison"].values()))


def main():
    test_geometrie()
    test_floraison()
    test_nourriture()
    test_butineurs()
    test_pont()
    n_ok = sum(1 for _, ok in _results if ok)
    print(f"\n[test_fleurs_lisiere] {n_ok}/{len(_results)} OK")
    if n_ok != len(_results):
        print("ÉCHECS : " + ", ".join(name for name, ok in _results if not ok))
        sys.exit(1)
    print("[test_fleurs_lisiere] PASS")


if __name__ == "__main__":
    main()
