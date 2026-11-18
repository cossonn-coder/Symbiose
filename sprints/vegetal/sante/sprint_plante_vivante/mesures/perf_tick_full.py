"""Perf ① plante vivante : durée du tick monde `full` (seed 42), semaines 10 → 30.
Lancer depuis le data/code à mesurer (HEAD de départ ou après) :
    python3 <chemin>/perf_tick_full.py
Imprime la durée totale des 20 ticks (init exclue)."""
import sys
import time
sys.path.insert(0, ".")
from tools.sim_server import SimServer

srv = SimServer()
srv.cmd_init({"config": "full", "seed": 42})
eng = srv.engine
t0 = time.perf_counter()
while eng.week < 30:
    eng.tick_semaine()
print(f"{time.perf_counter() - t0:.2f}")
