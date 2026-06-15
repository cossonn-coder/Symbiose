"""
SYMBIOSE — tests/vigueur/harness.py
Harness partagé des suites Vigueur : compteur de résultats `check`/`_results`,
graine déterministe et fabriques de mondes minimaux. Importé par tous les modules
de thème (contrats, gestes, façades, manger, macro, maitrise_seam, golden_traj) →
ils écrivent dans le MÊME accumulateur, que l'entrée `test_vigueur.py` agrège.
"""
from world import Tile
from plants import Tomato, Basil, Bean
from fields import init_eco
from sim.growth import grow_plant

SEED = 0x5AB1057E
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _minimal_state(week=1):
    """Monde minimal (1 tuile, 3 plantes) — assez pour tourner le tick à coût
    négligeable. Sert de support à l'intégration de la couche Vigueur."""
    tile = Tile(tile_id="T0", soil_type="terre")
    eco = init_eco("T0", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
    tile.add_plant(Tomato, 2, 2)
    tile.add_plant(Basil, 2, 4)
    tile.add_plant(Bean, 4, 2)
    return {
        "tiles": [tile], "eco": {"T0": eco}, "scores": {},
        "current_player": "joueur_1", "week": week, "log": [], "seed": SEED,
    }


def _gs_with(*especes):
    """game_state minimal portant les espèces voulues (pour calibrer l'écrasement
    espèce par espèce). `especes` = liste de (classe, r, c)."""
    tile = Tile(tile_id="T0", soil_type="terre")
    eco = init_eco("T0", 10, 12, humidite=1.5, fertilite=1.0, microbiome=0.3)
    for cls, r, c in especes:
        tile.add_plant(cls, r, c)
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "joueur_1", "week": 1, "log": [], "seed": SEED}
    return gs, tile, eco


def _construire(plant, n_ticks):
    """Fait pousser la STRUCTURE de `plant` n_ticks (chaîne de segments + auxine)."""
    for w in range(1, n_ticks + 1):
        grow_plant(plant, SEED, w)
    return plant


def _mature(plant):
    """Place une plante à son dernier stade (maturité = 1)."""
    plant.current_stage = len(plant.plant_class.growth_stages) - 1
    return plant
