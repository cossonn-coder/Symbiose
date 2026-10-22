"""Bois mort qui tombe (D111 ②) — lecture seule. Usage (depuis data/code/) :
  python3 ../../sprints/champs/sol/sprint_sol_qui_respire/mesures/bois_mort.py seed semaines [--sans]
Rapporte : plots avec litière `bois` > 0, mycélium max/médian, masse de bois tombée
(élagage) par an, tick moyen. `--sans` neutralise le dépôt (témoin ≈ état après ①)."""
import sys, os, time, statistics as st
sys.path.insert(0, os.getcwd())
import sim.engine.boucle as B
from tools.simserver.server import SimServer
tombe = {"m": 0.0}
_dep = B.deposer_bois_tombe
def dep(plant, tombes, eco):
    if "--sans" in sys.argv:
        return 0.0
    m = _dep(plant, tombes, eco); tombe["m"] += m; return m
B.deposer_bois_tombe = dep
seed, N = int(sys.argv[1]), int(sys.argv[2])
srv = SimServer(); srv.cmd_init({"config": "full", "seed": seed})
gs = srv.engine.game_state
t_an = {}
for w in range(N):
    t0 = time.perf_counter(); srv.cmd_step_week({}); dt = time.perf_counter() - t0
    t_an.setdefault(w // 52, []).append(dt)
    if w % 52 == 51 or w == N - 1:
        ecos = list(gs["eco"].values())
        bois = sum(1 for e in ecos for r in range(e.rows) for c in range(e.cols)
                   if any(p.tissu == "bois" and p.masse > 0 for p in e.litiere[r][c]))
        myc = [v for e in ecos for row in e.mycelium.data for v in row]
        npl = sum(1 for t in gs["tiles"] for p in t.plants if p.is_alive)
        print(f"sem {w+1}: plots bois>0 {bois}/{len(myc)} | mycélium max {max(myc):.3f} méd {st.median(myc):.4f}"
              f" | bois tombé cumulé {tombe['m']:.4f} | plantes {npl}"
              f" | tick moy an {w//52} {1000*st.mean(t_an[w//52]):.0f} ms")
