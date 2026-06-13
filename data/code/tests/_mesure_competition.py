"""
SYMBIOSE — tests/_mesure_competition.py
Instrument de MESURE du sprint compétition intra-plot (CONCEPTION §5, Q3).
Rejoue le scénario golden et compte les événements de germination + la
population vivante finale, par tuile. Sert à isoler la dérive de CHAQUE tronçon
(empilement / gène / étiolement). N'est PAS un test de non-régression.

Lancement (depuis data/code/) : python3 -m tests._mesure_competition
"""

from tests.test_golden import build_world, N_YEARS
from world import House
from sim.engine import Engine


def mesure():
    tiles, ecos = build_world()
    game_state = {
        "tiles": tiles, "eco": ecos, "scores": {},
        "current_player": "joueur_1", "week": 1, "log": [],
        "house": House(),
    }
    engine = Engine(game_state)
    compte = {"germination": 0, "spring_flush": 0, "leve_plante": 0}
    pic_vivantes = 0
    for _ in range(N_YEARS):
        for _ in range(52):
            log = engine.tick_semaine()
            for line in log:
                if "🌿 Germination" in line:
                    compte["germination"] += 1
                elif "🌸 Spring flush" in line:
                    compte["spring_flush"] += 1
                elif "🌱 Levée (planté)" in line:
                    compte["leve_plante"] += 1
            vivantes = sum(sum(1 for p in t.plants if p.is_alive) for t in tiles)
            pic_vivantes = max(pic_vivantes, vivantes)
            game_state["log"].clear()
    vivantes_fin = sum(sum(1 for p in t.plants if p.is_alive) for t in tiles)
    total_inst = sum(len(t.plants) for t in tiles)
    print("=== MESURE compétition intra-plot ===")
    print(f"germinations (succession)   : {compte['germination']}")
    print(f"germinations (spring flush) : {compte['spring_flush']}")
    print(f"levées (graines plantées)   : {compte['leve_plante']}")
    print(f"pic plantes vivantes        : {pic_vivantes}")
    print(f"plantes vivantes (fin)      : {vivantes_fin}")
    print(f"instances totales créées    : {total_inst}")
    for t in tiles:
        viv = sum(1 for p in t.plants if p.is_alive)
        print(f"  {t.tile_id} ({t.soil_type}): {viv} vivantes / {len(t.plants)} instances")


if __name__ == "__main__":
    mesure()
