"""
SYMBIOSE — tests/test_mulot.py
Zoochorie ⑥ (D42) : le mulot mange les grains sauvages, en cache une part sous
couvert, se rassasie d'une glandée, et nourrit le rapace.

  (a) grains sauvages + mulot imposé : une part mangée, une part déplacée sous
      couvert (`origine="mulot"`, dormance et péremption conservées, ≤ 3 m) ;
  (b) satiation : 10× plus de grains → la PART mangée baisse ;
  (c) grains plantés par le joueur : jamais touchés ;
  (d) rapace nourri par le mulot seul (campagnol et merle nuls).

Lancement (depuis data/code/) :
  python3 -m tests.test_mulot
"""
import sys

from world import Tile
from fields import init_eco
from fields.seedbank import GrainEnAttente, grain_sauvage, deposer_grain_sauvage
from plants import OakTree
from sim.mulot import mulot_tuile, R_CACHE_CM
from constants import PLOT_CM

SEED = 42
WEEK = 30
_res = []


def check(nom, ok, info=""):
    _res.append((nom, ok))
    print(f"  [{'OK' if ok else 'ÉCHEC'}] {nom}" + (f" — {info}" if info else ""))


def _tuile(n=20):
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=n, grid_cols=n)
    eco = init_eco("T0", n, n, humidite=1.0, fertilite=1.0, microbiome=0.3)
    return tile, eco


def _semer(tile, plots, par_plot):
    for r, c in plots:
        for _ in range(par_plot):
            deposer_grain_sauvage(tile, r, c, grain_sauvage(OakTree, {}, {}, "chute",
                                                             WEEK, None, None))


def _compte(tile, origine=None):
    return sum(1 for lst in tile.grains_en_attente.values() for g in lst
               if origine is None or g.origine == origine)


def test_a_mange_et_cache():
    tile, eco = _tuile()
    plots = [(r, c) for r in range(5, 15) for c in range(5, 9)]       # 40 plots
    _semer(tile, plots, 2)                                            # 80 grains
    avant = {id(g): (rc, g.levee_des, g.perime_a)
             for rc, lst in tile.grains_en_attente.items() for g in lst}
    # Couvert à l'est des grains (colonnes 9-12), nu ailleurs.
    for r in range(20):
        for c in range(20):
            eco.couverture_sol.data[r][c] = 0.9 if 9 <= c <= 12 else 0.0
    eco.populations["mulot"].fill(1.0)
    mange, cache = mulot_tuile(tile, eco, SEED, WEEK)
    restants = _compte(tile)
    check("(a) une part mangée", mange > 0, f"{mange} mangés")
    check("(a) une part cachée", cache > 0, f"{cache} cachés")
    check("(a) conservation des grains", restants == 80 - mange,
          f"{restants} restants")
    caches = [(rc, g) for rc, lst in tile.grains_en_attente.items() for g in lst
              if g.origine == "mulot"]
    check("(a) caches sous couvert", all(9 <= c <= 12 for (r, c), _g in caches))
    ok_dist = ok_dorm = True
    for (r, c), g in caches:
        (r0, c0), lev, per = avant[id(g)]
        ok_dist &= ((r - r0) ** 2 + (c - c0) ** 2) ** 0.5 * PLOT_CM <= R_CACHE_CM
        ok_dorm &= (g.levee_des, g.perime_a) == (lev, per)
    check("(a) cache à ≤ 3 m", ok_dist)
    check("(a) dormance et péremption conservées", ok_dorm)
    # Déterminisme : même scénario → même résultat.
    tile2, eco2 = _tuile()
    _semer(tile2, plots, 2)
    for r in range(20):
        for c in range(20):
            eco2.couverture_sol.data[r][c] = 0.9 if 9 <= c <= 12 else 0.0
    eco2.populations["mulot"].fill(1.0)
    check("(a) déterministe", mulot_tuile(tile2, eco2, SEED, WEEK) == (mange, cache))


def _part_mangee(n_plots):
    tile, eco = _tuile()
    plots = [(r, c) for r in range(20) for c in range(20)][:n_plots]
    _semer(tile, plots, 2)
    eco.populations["mulot"].fill(0.6)
    offre = _compte(tile)
    mange, cache = mulot_tuile(tile, eco, SEED, WEEK)
    return (mange + cache) / offre, offre


def test_b_satiation():
    maigre, o1 = _part_mangee(20)        # 40 grains
    glandee, o2 = _part_mangee(200)      # 400 grains
    check("(b) glandée : part trouvée plus faible", glandee < maigre,
          f"{o1} grains → {maigre:.2f} ; {o2} grains → {glandee:.2f}")


def test_c_grains_joueur():
    tile, eco = _tuile()
    for r in range(10):
        for c in range(10):
            tile.grains_en_attente.setdefault((r, c), []).append(
                GrainEnAttente(species="pommier", semaine_depot=WEEK))
    _semer(tile, [(r, c) for r in range(10) for c in range(10)], 2)
    eco.populations["mulot"].fill(1.0)
    mange, cache = mulot_tuile(tile, eco, SEED, WEEK)
    check("(c) le mulot a mangé des grains sauvages", mange > 0, f"{mange}")
    check("(c) 100 grains du joueur intacts", _compte(tile, "joueur") == 100)


def test_d_rapace_nourri():
    tile, eco = _tuile(8)
    for nom in ("campagnol", "merle"):
        eco.populations[nom].fill(0.0)
    rapace = eco.populations["rapace"]
    for _ in range(10):
        rapace.tick(eco, tile, tile.plants, [], 20)
    sans = rapace.total()
    for _ in range(10):
        eco.populations["mulot"].fill(0.8)
        rapace.tick(eco, tile, tile.plants, [], 20)
    avec = rapace.total()
    check("(d) rapace nul sans proie", sans == 0.0, f"{sans:.4f}")
    check("(d) rapace > 0 avec le mulot seul", avec > 0.0, f"{avec:.4f}")


def main():
    print("=== test_mulot (zoochorie ⑥) ===")
    test_a_mange_et_cache()
    test_b_satiation()
    test_c_grains_joueur()
    test_d_rapace_nourri()
    ok = sum(1 for _n, v in _res if v)
    print(f"\n{ok}/{len(_res)} OK")
    return 0 if ok == len(_res) else 1


if __name__ == "__main__":
    sys.exit(main())
