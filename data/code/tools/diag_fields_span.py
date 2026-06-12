# SYMBIOSE — tools/diag_fields_span.py
# Diagnostic LECTURE SEULE (t6·C3, retour F5 « température identique partout »,
# « OM/microbiome aléatoires ») : simule le monde smoke N semaines et imprime
# min/max/span de chaque champ écologique — dit si un champ est uniforme PAR
# CONSTRUCTION (temperature : engine.py fill() hebdo → span 0) ou s'il a un
# vrai gradient que la normalisation auto de la heatmap écrasait/étalait.
#
# Constat du 2026-06-12 (20 semaines, tuile T0 du smoke) :
#   temperature      span 0.0000  → uniforme (air hebdo, fill) — HONNÊTE en
#                                    échelle fixe ; temp. du sol = backlog
#   om_stable        span 0.0010  → bruit microscopique : le min/max AUTO
#   soil_memory_deep span 0.0014    l'étalait sur toute la palette = le
#                                    rendu « binaire/aléatoire » vu au F5
#   humidite/microbiome/om_fresh/lumiere : gradients réels (0.45..0.92)
#
# Usage (depuis data/code/) : python3 -m tools.diag_fields_span [semaines]

import itertools
import sys

from tests.test_golden import build_world
from sim.engine import Engine
from world.building import House

FIELDS = ("temperature", "humidite", "microbiome", "om_fresh", "om_active",
          "om_stable", "fertilite", "soil_memory", "soil_memory_fast",
          "soil_memory_deep", "disturbance", "lumiere")


def main():
    weeks = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    tiles, ecos = build_world()
    game_state = {"tiles": tiles, "eco": ecos, "scores": {},
                  "current_player": "joueur_1", "week": 1, "log": [],
                  "house": House()}
    engine = Engine(game_state)
    for _ in range(weeks):
        engine.tick_semaine()
    for tile in tiles:
        print(f"--- {tile.tile_id} ({tile.soil_type}) après {weeks} semaines ---")
        for name in FIELDS:
            grid = getattr(ecos[tile.tile_id], name)
            vals = list(itertools.chain.from_iterable(grid.data))
            mn, mx = min(vals), max(vals)
            print(f"  {name:16s} min={mn:8.4f} max={mx:8.4f} span={mx - mn:8.4f}")


if __name__ == "__main__":
    main()
