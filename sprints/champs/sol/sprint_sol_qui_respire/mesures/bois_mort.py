"""Bois mort (D111 ② + ②bis + ②ter) — lecture seule. Usage (depuis data/code/) :
  python3 ../../sprints/champs/sol/sprint_sol_qui_respire/mesures/bois_mort.py seed semaines [--sans]
Rapporte, à la semaine 0 puis chaque fin d'année : plots avec litière `bois` > 0,
masse de bois au sol, mycélium max/médian, branches tombées par cause (élagage ②,
ombre, tempête, neige, arbuste), tick moyen. `--sans` neutralise TOUS les dépôts
de bois tombé (témoin ≈ état après ②, le bois initial reste posé)."""
import sys, os, time, inspect, collections, statistics as st
sys.path.insert(0, os.getcwd())
import sim.engine.boucle as B
import sim.engine.branches as BR
from tools.simserver.server import SimServer
SANS = "--sans" in sys.argv
nb = collections.Counter(); masse = collections.Counter()
_dep = B.deposer_bois_tombe
def dep(plant, tombes, eco):
    if SANS or not tombes:
        return 0.0
    m = _dep(plant, tombes, eco)
    if m > 0:
        cause = inspect.stack()[1].frame.f_locals.get("cause", "élagage")
        cause = f"{cause}/{plant.name}"          # ②ter : par cause ET par arbre
        nb[cause] += 1; masse[cause] += m
    return m
B.deposer_bois_tombe = dep; BR.deposer_bois_tombe = dep
_arb = BR._chute_arbuste
def arb(plant, eco, wiy):
    if SANS:
        return 0.0
    m = _arb(plant, eco, wiy)
    if m > 0:
        nb["arbuste"] += 1; masse["arbuste"] += m
    return m
BR._chute_arbuste = arb
seed, N = int(sys.argv[1]), int(sys.argv[2])
srv = SimServer(); srv.cmd_init({"config": "full", "seed": seed})
gs = srv.engine.game_state
def bilan(label, t_an=None):
    ecos = list(gs["eco"].values())
    bois = [p.masse for e in ecos for r in range(e.rows) for c in range(e.cols)
            for p in e.litiere[r][c] if p.tissu == "bois" and p.masse > 0]
    myc = [v for e in ecos for row in e.mycelium.data for v in row]
    npl = sum(1 for t in gs["tiles"] for p in t.plants if p.is_alive)
    nlig = sum(1 for t in gs["tiles"] for p in t.plants
               if p.is_alive and p.plant_class.ligneux)
    print(f"{label}: plots bois>0 {len(bois)}/{len(myc)} (masse {sum(bois):.2f}) | "
          f"mycélium max {max(myc):.3f} méd {st.median(myc):.4f} | plantes {npl} "
          f"(ligneux {nlig}) | tombées {dict(nb)} masse {{{', '.join(f'{k}: {v:.3f}' for k, v in masse.items())}}}"
          + (f" | tick moy {1000 * st.mean(t_an):.0f} ms" if t_an else ""))
bilan("sem 0")
print("  structure des ligneux :", [(p.name, len(p.segments), round(p.plant_class.height_at(p)))
      for t in gs["tiles"] for p in t.plants if p.plant_class.ligneux])
t_an = {}
for w in range(N):
    t0 = time.perf_counter(); srv.cmd_step_week({}); dt = time.perf_counter() - t0
    t_an.setdefault(w // 52, []).append(dt)
    if w % 52 == 51 or w == N - 1:
        bilan(f"sem {w + 1}", t_an[w // 52])
