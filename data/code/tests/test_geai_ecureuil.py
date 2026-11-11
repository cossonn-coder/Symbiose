"""
SYMBIOSE — tests/test_geai_ecureuil.py
Zoochorie ⑤ (D42) : le geai et l'écureuil cachent des fruits à coque et en oublient.

  (a) chêne mûr + geai : glands pris, grains `geai` en terrain découvert, aucun sous
      la couronne dense ;
  (b) écureuil : pas d'habitat sans couronnes connexes (arbre isolé), présent avec
      un bosquet ;
  (c) grains `ecureuil` dans l'anneau de lisière des couronnes, dans le rayon ;
  (d) ceinture `foret` : grains de chêne à l'automne, rien sans ceinture, rien au
      printemps ;
  (e) glandée : la prise sature, la chute au pied augmente.

Lancement (depuis data/code/) :
  python3 -m tests.test_geai_ecureuil
"""
import sys
from math import hypot

from world import Tile
from fields import init_eco
from fields.peripherie import secteur_neutre
from fields.population.disperseurs import _ecureuil_habitat_grid, couronnes
from plants import Fruit, OakTree
from plants.perennials import HazelTree
from sim import vigueur as V
from sim.caches import (caches_prennent, caches_sement, grille_lisiere_couronnes,
                        TAMPON_CACHES, R_ECUREUIL_CM, LUM_DECOUVERT, DISPERSEURS)
from sim.engine import Engine
from sim.precroissance import pre_croitre

SEED = 42
WEEK = 30          # wiy 30 : automne, glands mûrs
_res = []


def check(nom, ok, info=""):
    _res.append((nom, ok))
    print(f"  [{'OK' if ok else 'ÉCHEC'}] {nom}" + (f" — {info}" if info else ""))


def _tuile(tid="T0", ox=0.0, n=20):
    tile = Tile(tile_id=tid, soil_type="terre", grid_rows=n, grid_cols=n, origin_x_cm=ox)
    eco = init_eco(tid, n, n, humidite=1.0, fertilite=1.0, microbiome=0.3)
    return tile, eco


def _gs(*paires, week=WEEK):
    gs = {"tiles": [t for t, _e in paires], "eco": {t.tile_id: e for t, e in paires},
          "scores": {}, "seed": SEED, "current_player": "j1", "week": week, "log": []}
    V.ensure_player(gs, "j1")
    return gs


def _arbre(tile, cls, r, c, nombre=0, annees=15):
    a = tile.add_plant(cls, r, c)
    a.age_years = cls.maturity_years + 1.0
    pre_croitre(a, SEED, annees)
    a.fruits = [Fruit(0, 1.0, cls.fruit_masse or 0.01, nombre)] if nombre else []
    return a


def _grains(tile, origine):
    return [(rc, g) for rc, gs in tile.grains_en_attente.items()
            for g in gs if g.origine == origine]


def _litiere_fruit(eco):
    return sum(p.masse for row in eco.litiere for cell in row for p in cell
               if p.tissu == "fruit")


def test_a_geai_decouvert():
    tile, eco = _tuile()
    gs = _gs((tile, eco))
    chene = _arbre(tile, OakTree, 10, 10, 4000)
    eco.lumiere.compute(tile.plants, "automne")
    eco.populations["geai"].fill(0.5)
    log = caches_prennent(gs, tile, eco, SEED, WEEK)
    pris = 4000 - sum(f.nombre for f in chene.fruits)
    check("(a) des glands sont pris par le geai", pris > 0 and any("Geai" in l for l in log),
          f"pris {pris}")
    caches_sement(gs, SEED, WEEK)
    grains = _grains(tile, "geai")
    couronne = set(chene.foliar_plots)
    check("(a) des caches oubliées deviennent des grains `geai`", len(grains) > 0,
          f"{len(grains)} grains")
    check("(a) aucun grain sous la couronne dense",
          all(rc not in couronne for rc, _g in grains))
    check("(a) tous en terrain découvert (lumière-sol ≥ seuil)",
          all(eco.lumiere.data[r][c] >= LUM_DECOUVERT for (r, c), _g in grains))
    check("(a) tampon vidé", TAMPON_CACHES not in gs)


def test_b_ecureuil_cimes_connexes():
    tile, eco = _tuile()
    _arbre(tile, OakTree, 10, 10)
    seul = sum(map(sum, _ecureuil_habitat_grid(eco, tile, tile.plants)))
    check("(b) arbre isolé : aucun habitat d'écureuil", seul == 0.0)
    tile2, eco2 = _tuile("T1")
    for r, c in ((6, 6), (6, 13), (13, 9)):
        _arbre(tile2, HazelTree, r, c, annees=12)
    bosquet = sum(map(sum, _ecureuil_habitat_grid(eco2, tile2, tile2.plants)))
    check("(b) bosquet de noisetiers : habitat d'écureuil", bosquet > 0.0,
          f"Σ habitat {bosquet:.2f}")
    for _ in range(20):
        eco.populations["ecureuil"].tick(eco, tile, tile.plants, [], WEEK)
        eco2.populations["ecureuil"].tick(eco2, tile2, tile2.plants, [], WEEK)
    seul_p, bosq_p = eco.populations["ecureuil"].total(), eco2.populations["ecureuil"].total()
    check("(b) l'écureuil s'installe dans le bosquet, pas sur l'arbre isolé",
          seul_p == 0.0 and bosq_p > 0.0, f"isolé {seul_p:.3f} · bosquet {bosq_p:.3f}")


def test_c_ecureuil_anneau():
    tile, eco = _tuile("T0", n=40)
    gs = _gs((tile, eco))
    noisetier = _arbre(tile, HazelTree, 20, 20, annees=12)
    noisetier.fruits = [Fruit(0, 1.0, HazelTree.fruit_masse, 3000)]
    eco.populations["ecureuil"].fill(0.6)
    caches_prennent(gs, tile, eco, SEED, WEEK)
    n_tampon = sum(e[4] for e in gs.get(TAMPON_CACHES, []) if e[0] == "ecureuil")
    caches_sement(gs, SEED, WEEK)
    grains = _grains(tile, "ecureuil")
    anneau = {(r, c) for _t, r, c, _w in grille_lisiere_couronnes(gs)}
    cimes = couronnes(tile.plants, tile.grid_rows, tile.grid_cols)
    check("(c) des noisettes oubliées deviennent des grains `ecureuil`",
          n_tampon > 0 and len(grains) > 0, f"tampon {n_tampon} · posés {len(grains)}")
    check("(c) tous dans l'anneau de lisière (hors cime)",
          all(rc in anneau and rc not in cimes for rc, _g in grains))
    src = (20.5 * 50, 20.5 * 50)
    check("(c) tous dans le rayon de l'écureuil",
          all(hypot((c + 0.5) * 50 - src[0], (r + 0.5) * 50 - src[1]) <= R_ECUREUIL_CM
              for (r, c), _g in grains))


def _ceinture():
    ceinture = [secteur_neutre(k) for k in range(4)]
    ceinture[0].update(type="foret", essence="hetre", hauteur_canopee=1500.0,
                       densite_ligneuse=0.9)
    return ceinture


def test_d_ceinture():
    def run(ceinture, week):
        tile, eco = _tuile()
        gs = _gs((tile, eco), week=week)
        if ceinture:
            gs["ceinture"] = ceinture
        eco.populations["geai"].fill(0.5)
        total = 0
        for w in range(week, week + 6):
            caches_sement(gs, SEED, w)
        for _rc, g in _grains(tile, "ceinture"):
            total += 1
        return total, {g.species for _rc, g in _grains(tile, "ceinture")}
    n_aut, especes = run(_ceinture(), WEEK)
    check("(d) ceinture `foret` : des glands arrivent à l'automne", n_aut > 0,
          f"{n_aut} grains, espèces {sorted(especes)}")
    check("(d) le chêne est toujours du lot", "chene" in especes)
    check("(d) sans ceinture : rien", run(None, WEEK)[0] == 0)
    check("(d) au printemps : rien", run(_ceinture(), 2)[0] == 0)


def test_e_glandee_satiation():
    """Le geai occupe la couronne (densité 1). La demande d'une cohorte vaut
    nombre × TAUX × 1, l'appétit APPETIT × |couronne| : au-delà de ~267 glands par
    plot de couronne, la prise plafonne et le surplus tombe au pied."""
    def run(nombre):
        tile, eco = _tuile()
        gs = _gs((tile, eco))
        chene = _arbre(tile, OakTree, 10, 10, nombre)
        champ = eco.populations["geai"]
        champ.fill(0.0)
        cour = {rc for rc in chene.foliar_plots if tile.is_valid_plot(*rc)}
        for r, c in cour:
            champ.set(r, c, 1.0)
        eco.populations["ecureuil"].fill(0.0)
        caches_prennent(gs, tile, eco, SEED, WEEK)
        restant = sum(f.nombre for f in chene.fruits)
        for f in chene.fruits:
            f.maturite = 1.29
        Engine(gs)._tick_fruits(tile, eco, WEEK)
        return nombre - restant, _litiere_fruit(eco), DISPERSEURS[0][2] * len(cour)
    pris1, chute1, appetit = run(40000)
    pris2, chute2, _a = run(80000)
    check("(e) glandée : la prise atteint l'appétit du geai", abs(pris1 - appetit) <= 1,
          f"{pris1} ≈ {appetit:.0f}")
    check("(e) une glandée double ne double pas la prise", abs(pris2 - pris1) <= 1,
          f"{pris1} → {pris2}")
    check("(e) la chute au pied augmente d'autant",
          chute2 - chute1 > 0.99 * 40000 * OakTree.fruit_masse,
          f"litière fruit {chute1:.1f} → {chute2:.1f}")


if __name__ == "__main__":
    for t in (test_a_geai_decouvert, test_b_ecureuil_cimes_connexes,
              test_c_ecureuil_anneau, test_d_ceinture, test_e_glandee_satiation):
        print(t.__name__)
        t()
    ok = sum(1 for _n, o in _res if o)
    print(f"\n{ok}/{len(_res)} vérifications OK")
    sys.exit(0 if ok == len(_res) else 1)
