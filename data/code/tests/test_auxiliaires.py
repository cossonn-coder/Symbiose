"""
SYMBIOSE — test_auxiliaires.py
Scénario de STRESS CHRONIQUE pour isoler l'effet des plantes attire-auxiliaires
(achillée / phacélie) sur la régulation des ravageurs (M6).

Deux tuiles jumelles, sol sableux pauvre + microbiome bas, MONOCULTURE de tomates
maintenue (faible biodiversité → ravageurs actifs). Seule différence :
  - tuile AUX   : 4 attire-auxiliaires (posent la rondelle `auxiliaire`)
  - tuile TÉMOIN: aucune

Le stress est maintenu : à chaque début d'année, les plots de monoculture vidés
(plantes mortes/parties) sont RE-semés en tomates, et la succession spontanée
n'a pas le temps de diversifier. On compte les dégâts/morts d'herbivorie par
tuile sur N années.

Hypothèse : la tuile TÉMOIN accumule plus de dégâts ravageurs que la tuile AUX.

Usage (depuis data/code/) : python3 -m tests.test_auxiliaires [n_years]   (défaut 30)
"""

import sys
import random
from sim import effects   # module (le patch ci-dessous doit cibler sim.effects)
from world import Tile
from plants import Tomato, Yarrow, Phacelia
from fields import init_eco
from sim.engine import Engine

random.seed(42)

# Instrumentation : on enveloppe herbivory_pressure pour compter les dégâts
# d'herbivorie par tuile, à la source (robuste, indépendant du log texte).
herbiv_damage = {"AUX": 0, "CTL": 0}
_orig_herbivory = effects.herbivory_pressure

def _counting_herbivory(plant, tile, game_state, eco):
    muts = _orig_herbivory(plant, tile, game_state, eco)
    for m in muts:
        if isinstance(m, effects.ReduceHealth) and "herbivorie" in m.reason:
            herbiv_damage[tile.tile_id] = herbiv_damage.get(tile.tile_id, 0) + m.amount
    return muts

effects.herbivory_pressure = _counting_herbivory

MONO_PLOTS = [(r, c) for r in range(1, 5) for c in range(1, 6)]  # 20 plots tomate
AUX_PLOTS  = [(0, 0), (0, 7), (5, 0), (5, 7)]                     # coins : achillée/phacélie


def build(tid, with_aux):
    tile = Tile(tile_id=tid, soil_type="sable")
    eco = init_eco(tid, 6, 8, humidite=1.2, fertilite=0.5, microbiome=0.15)  # pauvre
    for (r, c) in MONO_PLOTS:
        tile.add_plant(Tomato, r, c)
    if with_aux:
        for i, (r, c) in enumerate(AUX_PLOTS):
            tile.add_plant(Yarrow if i % 2 == 0 else Phacelia, r, c)
    return tile, eco


def reseed_monoculture(tile, with_aux):
    """Maintient le stress : re-sème en tomate les plots de monoculture vidés."""
    occupied = {p.position for p in tile.plants if p.is_alive}
    for (r, c) in MONO_PLOTS:
        if (r, c) not in occupied:
            tile.add_plant(Tomato, r, c)
    if with_aux:
        for i, (r, c) in enumerate(AUX_PLOTS):
            if (r, c) not in occupied:
                tile.add_plant(Yarrow if i % 2 == 0 else Phacelia, r, c)


tile_aux, eco_aux = build("AUX", True)
tile_ctl, eco_ctl = build("CTL", False)

game_state = {
    "tiles":  [tile_aux, tile_ctl],
    "eco":    {"AUX": eco_aux, "CTL": eco_ctl},
    "scores": {},
    "current_player": "joueur_1",
    "week": 1,
    "log":  [],
}
engine = Engine(game_state)

N_YEARS = int(sys.argv[1]) if len(sys.argv) > 1 else 30

print("╔══════════════════════════════════════════════════════╗")
print("║  Test attire-auxiliaires — stress chronique          ║")
print("║  Monoculture tomate, sol pauvre, 2 tuiles jumelles   ║")
print("╚══════════════════════════════════════════════════════╝")
print(f"  AUX    : monoculture + 4 attire-auxiliaires")
print(f"  TÉMOIN : monoculture seule")
print(f"\n{'année':>6} {'AUX dégâts':>11} {'TÉMOIN dégâts':>14} {'AUX aux●':>9} {'écart cumul':>12}")

for y in range(1, N_YEARS + 1):
    # Maintien du stress en début d'année
    reseed_monoculture(tile_aux, True)
    reseed_monoculture(tile_ctl, False)
    for _ in range(52):
        engine.tick_semaine()
        game_state["log"].clear()
    if y % 5 == 0 or y == 1:
        ecart = herbiv_damage["CTL"] - herbiv_damage["AUX"]
        print(f"{y:>6} {herbiv_damage['AUX']:>11} {herbiv_damage['CTL']:>14} "
              f"{tile_aux.get_rondelle_count('auxiliaire'):>9} {ecart:>12}")

print("\nRÉSULTAT")
print(f"  dégâts herbivorie cumulés — AUX : {herbiv_damage['AUX']}")
print(f"  dégâts herbivorie cumulés — TÉMOIN : {herbiv_damage['CTL']}")
