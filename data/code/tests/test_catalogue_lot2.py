"""
SYMBIOSE — tests/test_catalogue_lot2.py
Catalogue enrichi, tronçon ③ — validations « lot 2 » NON couvertes par le gate
bisannuel (test_biennial.py) : sanity du catalogue, attractivité des familles
neuves et profil fruitier de la courgette.

Trois vérifications :
  1. SANITY CATALOGUE — les 5 nouvelles clés (carotte, courgette, mâche, ortie,
     ail) sont présentes/correctes dans PLANT_CATALOGUE, s'instancient, germent
     et dépassent le stade semis (jumeau de test_evergreen pour le lot 2).
  2. ATTRACTIVITÉ FAMILLES NEUVES — une carotte (Apiaceae) en pleine floraison
     nourrit le SYRPHE plus que l'abeille et le papillon (Apiaceae=1.0 dans
     `_ATTRACT_SYRPHE` vs 0.45 / 0.50) — preuve que la table famille→préférence
     est bien câblée. L'ortie (Urticaceae, anémophile) ne nourrit AUCUN type
     (0.0 partout) : pas de nectar émis par une plante au vent.
  3. COURGETTE FRUITIER — Cucurbitaceae entomophile (`fruitier=True`,
     `pollination_mode="insect"`) : noue ≥1 fruit traçable POLLINISÉE, et ZÉRO
     fruit sans pollen (philo #2 : flux de pollinisation → contrainte → fruit).

Lancement (depuis data/code/) :
  python3 -m tests.test_catalogue_lot2
"""

import sys

from world import Tile
from plants import Carrot, Zucchini, CornSalad, Nettle, Garlic, organ_sites
from plants.base import Segment
from plants.catalogue import PLANT_CATALOGUE
from fields import init_eco
from fields.population import (
    _make_nectar_grid, _ATTRACT_SYRPHE, _ATTRACT_ABEILLE, _ATTRACT_PAPILLON,
    _ATTRACT_DEFAUT,
)
from sim.engine import Engine

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _engine_with(tile, eco):
    """Engine sur une tuile + eco, germination spontanée NEUTRALISÉE (on isole les
    plantes posées, pas la succession)."""
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    game_state = {
        "tiles": [tile], "eco": {tile.tile_id: eco}, "scores": {},
        "current_player": "joueur_1", "week": 1, "log": [],
    }
    return Engine(game_state)


# ---------------------------------------------------------------------------
# 1. Sanity catalogue (5 nouvelles clés)
# ---------------------------------------------------------------------------
def test_catalogue_germination_lot2():
    print("\n[1] sanity catalogue : les 5 clés du lot 2 germent et dépassent le semis")
    especes = {"carotte": Carrot, "courgette": Zucchini, "mache": CornSalad,
               "ortie": Nettle, "ail": Garlic}
    for cle, klass in especes.items():
        check(f"{cle} présent/correct dans PLANT_CATALOGUE",
              PLANT_CATALOGUE.get(cle) is klass)

    tile = Tile(tile_id="L2", soil_type="terre", grid_rows=6, grid_cols=10)
    eco = init_eco("L2", 6, 10, humidite=1.5, fertilite=1.2, microbiome=0.3)
    engine = _engine_with(tile, eco)
    posees = {cle: tile.add_plant(klass, 1 + i, 1 + i)
              for i, (cle, klass) in enumerate(especes.items())}

    for _ in range(12):   # > durée des stades semis (2-3 sem) avec marge
        engine.tick_semaine()

    for cle, inst in posees.items():
        check(f"{cle} vivante et au-delà du semis",
              inst.is_alive and inst.current_stage >= 1,
              f"stade {inst.stage.name}")


# ---------------------------------------------------------------------------
# 2. Attractivité des familles neuves (table famille → préférence)
# ---------------------------------------------------------------------------
def _nectar_at_plots(grid, plots):
    """Nectar perçu cumulé sur l'empreinte foliaire d'une plante."""
    return sum(grid[r][c] for (r, c) in plots
               if 0 <= r < len(grid) and 0 <= c < len(grid[0]))


def test_attractivite_familles_neuves():
    print("\n[2] attractivité : carotte (Apiaceae) → syrphe dominant ; ortie (Urticaceae) → nul")
    tile = Tile(tile_id="AT", soil_type="terre", grid_rows=8, grid_cols=8)
    eco = init_eco("AT", 8, 8, humidite=1.5, fertilite=1.2, microbiome=0.3)
    carotte = tile.add_plant(Carrot, 3, 3)
    carotte.current_stage = 2          # ombelle (canopée présente → foliar_plots)
    carotte.floraison = 1.0            # pleine floraison (force le signal nectar)

    g_syrphe = _make_nectar_grid(_ATTRACT_SYRPHE, _ATTRACT_DEFAUT)(eco, tile, tile.plants)
    g_abeille = _make_nectar_grid(_ATTRACT_ABEILLE, _ATTRACT_DEFAUT)(eco, tile, tile.plants)
    g_papillon = _make_nectar_grid(_ATTRACT_PAPILLON, _ATTRACT_DEFAUT)(eco, tile, tile.plants)

    plots = carotte.foliar_plots
    n_syrphe = _nectar_at_plots(g_syrphe, plots)
    n_abeille = _nectar_at_plots(g_abeille, plots)
    n_papillon = _nectar_at_plots(g_papillon, plots)
    check("carotte → nectar syrphe > 0", n_syrphe > 0.0, f"{n_syrphe:.3f}")
    check("carotte → syrphe DOMINE l'abeille (Apiaceae 1.0 > 0.45)",
          n_syrphe > n_abeille, f"syrphe {n_syrphe:.3f} > abeille {n_abeille:.3f}")
    check("carotte → syrphe DOMINE le papillon (1.0 > 0.50)",
          n_syrphe > n_papillon, f"syrphe {n_syrphe:.3f} > papillon {n_papillon:.3f}")

    # Ortie (Urticaceae anémophile) : aucun nectar, quel que soit le type.
    tile2 = Tile(tile_id="AU", soil_type="terre", grid_rows=8, grid_cols=8)
    eco2 = init_eco("AU", 8, 8, humidite=1.5, fertilite=1.2, microbiome=0.3)
    ortie = tile2.add_plant(Nettle, 3, 3)
    ortie.current_stage = 1
    ortie.floraison = 1.0
    plots2 = ortie.foliar_plots
    nul = all(_nectar_at_plots(_make_nectar_grid(t, _ATTRACT_DEFAUT)(eco2, tile2, tile2.plants),
                               plots2) == 0.0
              for t in (_ATTRACT_SYRPHE, _ATTRACT_ABEILLE, _ATTRACT_PAPILLON))
    check("ortie (anémophile) → nectar nul pour tous les types", nul)


# ---------------------------------------------------------------------------
# 3. Courgette fruitier (nouaison entomophile, philo #2)
# ---------------------------------------------------------------------------
def _apex(z, x=0.0):
    """Segment-apex synthétique dressé (dir +z) — site reproducteur déterministe."""
    return Segment(parent=None, base=(x, 0.0, z), dir=(0.0, 0.0, 1.0),
                   length_cm=40.0, thickness_cm=2.0, age_weeks=8,
                   auxin=0.5, is_apex=True)


def _monde_courgette():
    tile = Tile(tile_id="CG", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("CG", 6, 6, humidite=1.5, fertilite=1.2, microbiome=0.3)
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    cg = tile.add_plant(Zucchini, 3, 3)
    cg.segments = [_apex(z=40.0 + 10.0 * i, x=8.0 * i) for i in range(3)]
    gs = {"tiles": [tile], "eco": {"CG": eco}, "scores": {},
          "current_player": "joueur_1", "week": 1, "log": []}
    return gs, tile, eco, cg, Engine(gs)


def _nouer(eng, tile, eco, plant, pollen):
    """Force une nouaison en fin de floraison (patron test_fruits) : pleine
    floraison (arme a_fleuri) puis fanaison avec la dose `pollen` (insect →
    frac = g(pollen))."""
    plant.floraison = 1.0
    eng._tick_fruits(tile, eco, 1)
    plant.floraison = 0.0
    plant.pollen_recu = pollen
    eng._tick_fruits(tile, eco, 1)


def test_courgette_fruitier():
    print("\n[3] courgette fruitier : pollinisée → ≥1 fruit ; sans pollen → 0 (philo #2)")
    # Pollinisée (dose forte) : noue des fruits traçables.
    gs, tile, eco, cg, eng = _monde_courgette()
    attendu = len(organ_sites(cg))
    _nouer(eng, tile, eco, cg, pollen=100.0)
    check("pollinisée → ≥1 fruit traçable", len(cg.fruits) >= 1,
          f"{len(cg.fruits)} fruits / {attendu} sites")
    # Sans pollen : aucune nouaison (entomophile sans plancher).
    gs, tile, eco, cg, eng = _monde_courgette()
    _nouer(eng, tile, eco, cg, pollen=0.0)
    check("sans pollen → 0 fruit (entomophile, philo #2)", cg.fruits == [])


def main():
    test_catalogue_germination_lot2()
    test_attractivite_familles_neuves()
    test_courgette_fruitier()

    print("\n" + "=" * 60)
    total = len(_results)
    ok = sum(1 for _, c in _results if c)
    for name, cond in _results:
        if not cond:
            print(f"  ÉCHEC : {name}")
    print(f"RÉSULTAT : {ok}/{total} vérifications passées")
    if ok == total:
        print("[catalogue_lot2] PASS")
        return 0
    print("[catalogue_lot2] FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
