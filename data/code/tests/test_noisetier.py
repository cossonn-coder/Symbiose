"""
SYMBIOSE — tests/test_noisetier.py
Test ciblé, lancé À LA DEMANDE (hors smoke test). Sprint ZOOCHORIE ③ (D42).

Le noisetier (*Corylus avellana*) entre au catalogue, fruitier unifié dès sa naissance,
avec ses voix :

  (a) chatons PRÉCOCES : deux pieds mûrs fleurissent dans les 4 premières semaines du
      printemps du moteur (wiy 1 = équinoxe ; le forçage floral repart à 0 à wiy 1,
      aucune espèce ne peut fleurir avant — février n'est pas atteignable), AVANT le saule ;
  (b) nouaison PAR LE VENT : deux pieds à 2,5 m nouent ; un pied isolé noue moins
      (contre-factuel : la dose anémophile vient des AUTRES pieds) ;
  (c) chute → grains `chute` sous la couronne (unifié ② : `recrue_par_fruits`) ;
  (d) voix : fiche encyclopédique 3 niveaux, fiche magazine, page secrète, et le log de
      nouaison produit bien un `Evenement("nouaison", espece="noisetier")`.

Lancement (depuis data/code/) :
  python3 -m tests.test_noisetier
"""

import sys

from world import Tile
from fields import init_eco
from plants import Fruit
from plants.catalogue import PERENNIAL_CATALOGUE
from plants.perennials import HazelTree, Willow
from sim.engine import Engine
from sim.engine.decompo import P_GRAIN_CHUTE
from sim.reproduction import recrue_par_fruits
from sim import evenements, magazine
from sim.encyclopedie_corpus import FICHES
from sim.pages_corpus import PAGES

SEED = 42
SEMAINES = 8          # floraison wiy 1-4, nouaison à la fanaison (~wiy 5)


def _monde(pieds, autre=None):
    """Tuile 20×20, des noisetiers MÛRS aux positions `pieds` (+ un pied `autre` de
    comparaison). Germination coupée : seuls les pieds posés vivent. Semaine 1 = wiy 1."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=20, grid_cols=20)
    eco = init_eco("T0", 20, 20, humidite=1.0, fertilite=1.0, microbiome=0.3)
    plantes = [tile.add_plant(HazelTree, r, c) for r, c in pieds]
    if autre is not None:
        cls, (r, c) = autre
        plantes.append(tile.add_plant(cls, r, c))
    for p in plantes:
        p.age_years = p.plant_class.maturity_years + 1.0
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {}, "seed": SEED,
          "current_player": "j1", "week": 1, "log": []}
    return Engine(gs), tile, eco, plantes


def _derouler(engine, semaines):
    log = []
    for _ in range(semaines):
        log += engine.tick_semaine() or []
    return log


def test_chatons_precoces():
    engine, _t, _e, plantes = _monde([(8, 8), (8, 13)], autre=(Willow, (15, 15)))
    _derouler(engine, SEMAINES)
    *noisetiers, saule = plantes
    semaines = [p.bloom_week for p in noisetiers]
    assert all(1 <= w <= 4 for w in semaines), f"chatons hors wiy 1-4 : {semaines}"
    assert all(w <= saule.bloom_week for w in semaines), \
        f"noisetier {semaines} après le saule {saule.bloom_week}"
    print(f"[noisetier (a)] PASS — chatons wiy {semaines}, saule wiy {saule.bloom_week} [seed 42]")


def _fruits_noues(pieds):
    engine, _t, _e, plantes = _monde(pieds)
    log = _derouler(engine, SEMAINES)
    return sum(f.nombre for f in plantes[0].fruits), log


def test_nouaison_par_le_vent():
    paire, log = _fruits_noues([(8, 8), (8, 13)])
    seul, _ = _fruits_noues([(8, 8)])
    assert paire > 0, "deux noisetiers à 2,5 m n'ont rien noué"
    assert seul < paire, f"pied isolé {seul} ≥ pied accompagné {paire}"
    evs = [e for e in evenements.evenements(log) if e.kind == "nouaison"]
    assert any(e.espece == "noisetier" for e in evs), f"aucun événement nouaison : {evs}"
    print(f"[noisetier (b)] PASS — nouaison {paire} fruits (isolé : {seul}) ; "
          f"événement `nouaison` noisetier émis [seed 42, année maigre]")


def test_chute_seme():
    engine, tile, eco, (arbre,) = _monde([(10, 10)])
    assert recrue_par_fruits(HazelTree), "le noisetier doit semer par ses fruits"
    arbre.fruits = [Fruit(0, 1.29, HazelTree.fruit_masse, 400)]
    engine._tick_fruits(tile, eco, 28)
    assert not arbre.fruits, "la cohorte n'est pas tombée"
    grains = [(rc, g) for rc, gs in tile.grains_en_attente.items() for g in gs]
    assert len(grains) == round(400 * P_GRAIN_CHUTE), f"{len(grains)} grain(s)"
    couronne = set(arbre.foliar_plots) | {arbre.position}
    assert all(g.origine == "chute" and g.species == "noisetier" and rc in couronne
               for rc, g in grains), grains
    print(f"[noisetier (c)] PASS — {len(grains)} grains `chute` noisetier sous la couronne")


def test_voix():
    assert PERENNIAL_CATALOGUE.get("noisetier") is HazelTree
    fiche = FICHES.get("noisetier")
    assert fiche and set(fiche) == {1, 2, 3} and all(fiche[n].strip() for n in fiche)
    assert magazine.magazine_fiche("noisetier") is not None, "pas de fiche magazine"
    assert HazelTree.family == "Betulaceae", "rattachement magazine par famille"
    pages = [p for p in PAGES.values() if "coudrier" in p["texte"]]
    assert pages, "pas de page secrète du coudrier"
    print(f"[noisetier (d)] PASS — encyclopédie 3 niveaux, magazine (Betulaceae), "
          f"page {pages[0]['id']} « {pages[0]['titre']} »")


if __name__ == "__main__":
    try:
        test_chatons_precoces()
        test_nouaison_par_le_vent()
        test_chute_seme()
        test_voix()
    except AssertionError as e:
        print(f"[noisetier] FAIL — {e}")
        sys.exit(1)
