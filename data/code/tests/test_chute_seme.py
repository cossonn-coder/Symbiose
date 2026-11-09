"""
SYMBIOSE — tests/test_chute_seme.py
Test ciblé, lancé À LA DEMANDE (hors smoke test). Sprint ZOOCHORIE ② (D42).

La relève des fruitiers pérennes passe par leurs VRAIS fruits : une cohorte qui
tombe dépose sa chair en litière ET des grains sauvages `chute` sous la couronne.

  (a) cerisier mûr dont une cohorte de 400 cerises sur-mûres tombe (`_tick_fruits`)
      → 400 × P_GRAIN_CHUTE grains `chute` sur ses plots foliaires, aux gènes
      `child_genes(mère, père)`, en dormance jusqu'au printemps suivant ;
  (b) `_reproduction` ne pose plus de recrue directe pour lui ; contre-factuel :
      prédicat `recrue_par_fruits` forcé à faux (ancien code) → recrue directe ;
  (c) figuier (graine stérile) : sa cohorte tombe, 0 grain ;
  (d) glandée : deux chênes la même année → même facteur ; sur 40 ans la part des
      années fortes ≈ 1/4 (période 4), hêtre et pommier sans masting → 1,0.

Lancement (depuis data/code/) :
  python3 -m tests.test_chute_seme
"""

import sys

from world import Tile
from fields import init_eco
from plants import Fruit, CherryTree, Fig
from plants.perennials.forestiers import OakTree, BeechTree
from plants import AppleTree
from sim.engine import Engine
import sim.engine.mortalite as mortalite
from sim.engine.decompo import P_GRAIN_CHUTE
from sim.reproduction import (child_genes, recrue_par_fruits, facteur_glandee,
                              GLANDEE_MAIGRE)

SEED = 42
WEEK = 30


def _monde(cls):
    """Une tuile 20×20, un arbre MÛR de `cls` au centre. Renvoie (engine, tile, eco, arbre)."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=20, grid_cols=20)
    eco = init_eco("T0", 20, 20, humidite=1.0, fertilite=1.0, microbiome=0.3)
    arbre = tile.add_plant(cls, 10, 10)
    arbre.age_years = cls.maturity_years + 1.0
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {}, "seed": SEED,
          "current_player": "j1", "week": WEEK, "log": []}
    engine = Engine(gs)
    return engine, tile, eco, arbre


def _faire_tomber(engine, tile, eco, arbre, nombre=400):
    """Une cohorte sur-mûre (juste sous le seuil de chute) : un pas de maturation la fait tomber."""
    arbre.fruits = [Fruit(0, 1.29, arbre.plant_class.fruit_masse or 0.01, nombre)]
    engine._tick_fruits(tile, eco, WEEK)
    assert not arbre.fruits, "la cohorte n'est pas tombée"


def _grains(tile):
    return [(rc, g) for rc, gs in tile.grains_en_attente.items() for g in gs]


def test_cerisier_seme_sous_couronne():
    engine, tile, eco, arbre = _monde(CherryTree)
    assert recrue_par_fruits(CherryTree)
    _faire_tomber(engine, tile, eco, arbre)
    grains = _grains(tile)
    attendu = round(400 * P_GRAIN_CHUTE)
    assert len(grains) == attendu, f"{len(grains)} grain(s) au lieu de {attendu}"
    couronne = set(arbre.foliar_plots) | {arbre.position}
    genes = child_genes(arbre, None, SEED, WEEK)   # cerisier isolé → autofécondation
    for rc, g in grains:
        assert g.origine == "chute" and g.species == "cerisier", (g.origine, g.species)
        assert rc in couronne, f"grain hors couronne @{rc}"
        assert g.genes == genes, "gènes ≠ héritage child_genes(mère, père)"
        assert g.levee_des > WEEK and not g.cultive
    print(f"[chute-seme (a)] PASS — {len(grains)} grains `chute` sous la couronne, "
          f"gènes hérités, dormants jusqu'à S{grains[0][1].levee_des}")


def _recrues_directes(forcer_ancien: bool) -> int:
    engine, tile, eco, arbre = _monde(CherryTree)
    eco.lumiere.at_plot = lambda r, c: 0.9
    orig_rate, orig_pred = CherryTree.reproduction_rate, mortalite.recrue_par_fruits
    try:
        CherryTree.reproduction_rate = 1.0
        if forcer_ancien:
            mortalite.recrue_par_fruits = lambda cls: False
        engine._reproduction(tile, eco, week=WEEK)
    finally:
        CherryTree.reproduction_rate = orig_rate
        mortalite.recrue_par_fruits = orig_pred
    return sum(1 for p in tile.plants if p is not arbre)


def test_plus_de_recrue_directe():
    nouveau, ancien = _recrues_directes(False), _recrues_directes(True)
    assert nouveau == 0, f"{nouveau} recrue(s) directe(s) du cerisier"
    assert ancien >= 1, "contre-factuel : l'ancien chemin aurait dû poser une recrue"
    print(f"[chute-seme (b)] PASS — 0 recrue directe (ancien chemin : {ancien})")


def test_figuier_ne_seme_pas():
    engine, tile, eco, arbre = _monde(Fig)
    assert not recrue_par_fruits(Fig)
    _faire_tomber(engine, tile, eco, arbre)
    assert not _grains(tile), "un figuier stérile a semé"
    print("[chute-seme (c)] PASS — figuier : cohorte tombée, 0 grain")


def test_glandee_synchrone():
    # Le facteur ne dépend que de (seed, année, espèce) : deux pieds = même valeur.
    for annee in range(40):
        assert facteur_glandee(OakTree, annee, SEED) == facteur_glandee(OakTree, annee, SEED)
    fortes = sum(facteur_glandee(OakTree, a, SEED) == 1.0 for a in range(40))
    assert all(facteur_glandee(OakTree, a, SEED) in (1.0, GLANDEE_MAIGRE) for a in range(40))
    assert 5 <= fortes <= 16, f"{fortes}/40 années fortes (attendu ≈ 10)"
    assert facteur_glandee(AppleTree, 3, SEED) == 1.0
    hetre = sum(facteur_glandee(BeechTree, a, SEED) == 1.0 for a in range(40))
    meme = sum(facteur_glandee(OakTree, a, SEED) == facteur_glandee(BeechTree, a, SEED)
               for a in range(40))
    print(f"[chute-seme (d)] PASS — chêne {fortes}/40 années fortes, hêtre {hetre}/40, "
          f"chêne=hêtre {meme}/40 ans [n=1 seed]")


if __name__ == "__main__":
    try:
        test_cerisier_seme_sous_couronne()
        test_plus_de_recrue_directe()
        test_figuier_ne_seme_pas()
        test_glandee_synchrone()
    except AssertionError as e:
        print(f"[chute-seme] FAIL — {e}")
        sys.exit(1)
