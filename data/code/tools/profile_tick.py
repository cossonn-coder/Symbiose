# SYMBIOSE — tools/profile_tick.py
# Référence PERF du tick complet (pré-sprint VENT, tronçon ⓪). Mesure, sur le
# monde déterministe réel (`build_world` du golden) grandi N semaines, le coût
# moyen `ms/tick` et la part de LightField (`tick_light`→`light.compute`).
#
# But : poser une BASE de référence avant/après le passage gather→scatter de la
# boucle lumière-sol (D32) et fixer le budget +X %/tronçon du sprint vent.
#
# LECTURE SEULE — n'altère rien, ne touche pas le golden. Déterministe (mêmes
# chiffres relatifs à matériel constant).
#
# Usage (depuis data/code/) : python3 -m tools.profile_tick [semaines] [ticks_mesures]

import sys
import time

from sim.engine import Engine
from tests.test_golden import build_world
from world.building import House


def _build_engine():
    """Monde complet du golden (2 tuiles) + maison, prêt à ticker."""
    tiles, ecos = build_world()
    game_state = {"tiles": tiles, "eco": ecos, "scores": {},
                  "current_player": "joueur_1", "week": 1, "log": [],
                  "house": House()}
    return Engine(game_state), tiles, ecos


def main():
    warm = int(sys.argv[1]) if len(sys.argv) > 1 else 52
    measured = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    engine, tiles, ecos = _build_engine()
    house = engine.game_state["house"]

    # Échauffement : faire pousser le monde (ombres réelles, plantes installées).
    for _ in range(warm):
        engine.tick_semaine()

    # Mesure du tick complet.
    t0 = time.perf_counter()
    for _ in range(measured):
        engine.tick_semaine()
    dt_tick = (time.perf_counter() - t0) / measured * 1000.0

    # Mesure ISOLÉE de la boucle lumière (compute par tuile), à snapshot figé.
    from sim.engine.calendrier import saison_de
    saison = saison_de(((warm + measured - 1) % 52) + 1)
    t0 = time.perf_counter()
    reps = 5
    for _ in range(reps):
        for tile in tiles:
            eco = ecos[tile.tile_id]
            origin = engine.game_state.get("tile_origins", {}).get(tile.tile_id, (0.0, 0.0)) \
                if isinstance(engine.game_state.get("tile_origins"), dict) else (0.0, 0.0)
            eco.lumiere.compute(tile.plants, saison, house=house, tile_origin=origin)
    dt_light = (time.perf_counter() - t0) / reps * 1000.0

    n_plants = sum(len(t.plants) for t in tiles)
    n_plots = sum(eco.lumiere.rows * eco.lumiere.cols for eco in ecos.values())
    print(f"=== Profil tick — {warm} sem échauffement, {measured} ticks mesurés ===")
    print(f"  monde : {len(tiles)} tuiles, {n_plots} plots, {n_plants} plantes")
    print(f"  tick complet      : {dt_tick:7.2f} ms/tick")
    print(f"  LightField.compute: {dt_light:7.2f} ms/tick "
          f"({100*dt_light/dt_tick:4.1f} % du tick)")


if __name__ == "__main__":
    main()
