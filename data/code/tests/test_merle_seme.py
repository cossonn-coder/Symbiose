"""
SYMBIOSE — tests/test_merle_seme.py
Test ciblé, lancé À LA DEMANDE (hors smoke test). Sprint ZOOCHORIE ④ (D42).

Le merle cueille les fruits mûrs sur la plante et sème sous les perchoirs.

  (a) cerisier mûr + champ merle imposé : des cerises sont prises, la chute en
      litière `fruit` diminue d'autant (contre-factuel sans merle) ;
  (b) les grains `merle` tombent sous un perchoir (arbre haut, mort debout,
      support) et nulle part ailleurs ;
  (c) sans perchoir : aucun grain ;
  (d) un perchoir posé (geste `poser_perchoir`) loin du cerisier reçoit des grains ;
  (e) dépôt sur une autre tuile via le tampon (deux tuiles), indépendant de l'ordre ;
  (f) appétit : doubler les fruits ne double pas la prise (Holling II).

Lancement (depuis data/code/) :
  python3 -m tests.test_merle_seme
"""

import sys

from world import Tile
from fields import init_eco
from plants import Fruit, CherryTree, AppleTree
from sim import vigueur as V
from sim.actions import poser_perchoir, poser_tuteur
from sim.engine import Engine
from sim.precroissance import pre_croitre
from sim.zoochorie import (merle_prend, merle_seme, grille_perchoirs, TAMPON,
                           TAUX_PRISE, APPETIT)

SEED = 42
WEEK = 30
_res = []


def check(nom, ok, info=""):
    _res.append((nom, ok))
    print(f"  [{'OK' if ok else 'ÉCHEC'}] {nom}" + (f" — {info}" if info else ""))


def _tuile(tid, ox=0.0):
    tile = Tile(tile_id=tid, soil_type="terre", grid_rows=20, grid_cols=20,
                origin_x_cm=ox)
    eco = init_eco(tid, 20, 20, humidite=1.0, fertilite=1.0, microbiome=0.3)
    return tile, eco


def _gs(*paires):
    gs = {"tiles": [t for t, _e in paires], "eco": {t.tile_id: e for t, e in paires},
          "scores": {}, "seed": SEED, "current_player": "j1", "week": WEEK, "log": []}
    V.ensure_player(gs, "j1")
    return gs


def _cerisier(tile, r, c, nombre, haut=False):
    a = tile.add_plant(CherryTree, r, c)
    a.age_years = CherryTree.maturity_years + 1.0
    if haut:
        pre_croitre(a, SEED, 8)
    a.fruits = [Fruit(0, 1.0, CherryTree.fruit_masse or 0.01, nombre)]
    return a


def _grains(tile, origine="merle"):
    return [(rc, g) for rc, gs in tile.grains_en_attente.items()
            for g in gs if g.origine == origine]


def _litiere_fruit(eco):
    return sum(p.masse for row in eco.litiere for cell in row for p in cell
               if p.tissu == "fruit")


def test_a_prise_et_chute():
    resultats = {}
    for avec_merle in (False, True):
        tile, eco = _tuile("T0")
        gs = _gs((tile, eco))
        a = _cerisier(tile, 10, 10, 400)
        eco.populations["merle"].fill(0.5 if avec_merle else 0.0)
        merle_prend(gs, tile, eco, SEED, WEEK)
        restant = sum(f.nombre for f in a.fruits)
        for f in a.fruits:
            f.maturite = 1.29
        Engine(gs)._tick_fruits(tile, eco, WEEK)
        resultats[avec_merle] = (restant, _litiere_fruit(eco))
    pris = 400 - resultats[True][0]
    attendu = 400 * TAUX_PRISE * 0.5
    check("(a) des cerises sont prises (≈ nombre × TAUX_PRISE × d̄)",
          abs(pris - attendu) <= 1, f"pris {pris}, attendu {attendu:.1f}")
    check("(a) sans merle rien n'est pris", resultats[False][0] == 400)
    masse = CherryTree.fruit_masse or 0.01
    delta = resultats[False][1] - resultats[True][1]
    check("(a) la chute diminue d'autant", abs(delta - pris * masse) < 1e-9,
          f"Δ litière {delta:.4f} = {pris} × {masse}")


def test_b_sous_perchoirs():
    tile, eco = _tuile("T0")
    gs = _gs((tile, eco))
    arbre = _cerisier(tile, 4, 4, 0, haut=True)
    arbre.fruits = []
    mort = tile.add_plant(AppleTree, 15, 4)
    pre_croitre(mort, SEED, 3)
    mort.vitalite, mort.morte, mort.stade_mort = 0.0, True, "seche"
    poser_tuteur(gs, "j1", tile, 16 * 50 + 25, 15 * 50 + 25)
    perch = {(r, c) for t, r, c, _w in grille_perchoirs(gs)}
    couronne = {rc for rc in arbre.foliar_plots if tile.is_valid_plot(*rc)}
    check("(b) l'arbre haut est un perchoir", arbre.current_height >= 150
          and couronne <= perch, f"h={arbre.current_height:.0f} cm")
    check("(b) le mort debout et le tuteur sont des perchoirs",
          (15, 16) in perch and any(rc in perch for rc in mort.foliar_plots
                                    if tile.is_valid_plot(*rc)))
    gs[TAMPON] = [(CherryTree, dict(arbre.genes), {}, 60, 1)]
    merle_seme(gs, SEED, WEEK)
    gr = _grains(tile)
    check("(b) des grains merle sont posés", len(gr) > 0, f"{len(gr)} grains")
    check("(b) tous sous un perchoir", all(rc in perch for rc, _g in gr))
    check("(b) grain sauvage en dormance", all(g.levee_des > WEEK and not g.cultive
                                               for _rc, g in gr))


def test_c_sans_perchoir():
    tile, eco = _tuile("T0")
    gs = _gs((tile, eco))
    _cerisier(tile, 10, 10, 4000)          # jeune : 1 cm, pas un perchoir
    eco.populations["merle"].fill(1.0)
    merle_prend(gs, tile, eco, SEED, WEEK)
    check("(c) des graines partent au tampon", sum(n for *_x, n, _s in gs[TAMPON]) > 0)
    merle_seme(gs, SEED, WEEK)
    check("(c) sans perchoir : aucun grain", not _grains(tile))
    check("(c) tampon vidé", TAMPON not in gs)


def test_d_perchoir_pose_loin():
    tile, eco = _tuile("T0")
    gs = _gs((tile, eco))
    _cerisier(tile, 2, 2, 4000)
    sup = poser_perchoir(gs, "j1", tile, 17 * 50 + 25, 17 * 50 + 25)
    check("(d) le perchoir est posé", sup is not None and sup.support_type == "perchoir"
          and sup.height_cm == 200.0)
    eco.populations["merle"].fill(1.0)
    log = merle_prend(gs, tile, eco, SEED, WEEK)
    merle_seme(gs, SEED, WEEK)
    gr = _grains(tile)
    check("(d) le perchoir lointain reçoit des grains",
          gr and all(rc == (17, 17) for rc, _g in gr),
          f"{len(gr)} grains (plafond 3), log {log}")


def _deux_tuiles(ordre):
    t0, e0 = _tuile("T0")
    t1, e1 = _tuile("T1", ox=1050.0)
    gs = _gs(*((t0, e0), (t1, e1))[::ordre])
    _cerisier(t0, 10, 10, 4000)
    poser_perchoir(gs, "j1", t1, 5 * 50 + 25, 5 * 50 + 25)
    e0.populations["merle"].fill(1.0)
    merle_prend(gs, t0, e0, SEED, WEEK)
    merle_seme(gs, SEED, WEEK)
    return t0, t1


def test_e_autre_tuile():
    t0, t1 = _deux_tuiles(1)
    check("(e) aucun grain sur la tuile de la mère", not _grains(t0))
    check("(e) grains sur la tuile voisine", bool(_grains(t1)), f"{len(_grains(t1))}")
    t0b, t1b = _deux_tuiles(-1)
    check("(e) ordre des tuiles indifférent",
          sorted(rc for rc, _g in _grains(t1)) == sorted(rc for rc, _g in _grains(t1b)))


def _prise(nombre):
    tile, eco = _tuile("T0")
    gs = _gs((tile, eco))
    a = _cerisier(tile, 10, 10, nombre)
    for r, c in a.foliar_plots:
        eco.populations["merle"].set(r, c, 1.0)
    merle_prend(gs, tile, eco, SEED, WEEK)
    return nombre - sum(f.nombre for f in a.fruits), eco.populations["merle"].total()


def test_f_appetit():
    p1, dens = _prise(4000)
    p2, _ = _prise(8000)
    check("(f) prise bornée par l'appétit", abs(p1 - APPETIT * dens) <= 1,
          f"{p1} ≈ {APPETIT} × {dens:.1f}")
    check("(f) doubler les fruits ne double pas la prise", p2 < 1.5 * p1, f"{p1} → {p2}")


if __name__ == "__main__":
    for t in (test_a_prise_et_chute, test_b_sous_perchoirs, test_c_sans_perchoir,
              test_d_perchoir_pose_loin, test_e_autre_tuile, test_f_appetit):
        print(t.__name__)
        t()
    ok = sum(1 for _n, v in _res if v)
    print(f"\n{ok}/{len(_res)} vérifications OK")
    sys.exit(0 if ok == len(_res) else 1)
