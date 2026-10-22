"""Bois mort (D111 ② + ②bis + ②ter) — lecture seule. Usage (depuis data/code/) :
  python3 ../../sprints/champs/sol/sprint_sol_qui_respire/mesures/bois_mort.py seed semaines [--sans]
Rapporte, à la semaine 0 puis chaque fin d'année : plots avec litière `bois` > 0,
masse de bois au sol, mycélium max/médian, branches tombées par cause (élagage ②,
ombre, tempête, neige, arbuste), tick moyen. `--sans` neutralise TOUS les dépôts
de bois tombé (témoin ≈ état après ②, le bois initial reste posé).
⑦bis : + bois de LISIÈRE (ceinture) déposé, masse lisière (≤ 4 m d'un secteur
ligneux) vs centre, masse par classe de grosseur, et (`--carpo`) fructifications
des saprophytes du BOIS lues dans le vrai snapshot (plot-semaines, lisière/centre)."""
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
CARPO = "--carpo" in sys.argv
try:
    import sim.engine.ceinture_bois as CB
    _lis = CB.bois_de_lisiere
    def lis(tile, eco, *a, **k):
        if SANS:
            return []
        m0 = sum(p.masse for row in eco.litiere for cell in row for p in cell if p.tissu == "bois")
        out = _lis(tile, eco, *a, **k)
        m1 = sum(p.masse for row in eco.litiere for cell in row for p in cell if p.tissu == "bois")
        if m1 > m0:
            nb["lisière"] += 1; masse["lisière"] += m1 - m0
        return out
    B.bois_de_lisiere = lis
except ImportError:
    CB = None
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
from fields.peripherie import plots_de_bord
from fields.fongique import REGISTRE_FONGIQUE
LISIERE = set()
for t in gs["tiles"]:
    e = gs["eco"][t.tile_id]
    for s in gs.get("ceinture") or ():
        if s["densite_ligneuse"] > 0 and s["type"] != "falaise":
            for r, c, _ in plots_de_bord(s["cote"], e.rows, e.cols,
                                         (t.origin_x_cm, t.origin_y_cm), 400.0):
                LISIERE.add((t.tile_id, r, c))
SAPRO_BOIS = {k for k, esp in REGISTRE_FONGIQUE.items() if "bois" in esp.substrats}
fruits = collections.Counter()
CLASSES = ((1.0, "<1cm"), (10.0, "1-10cm"), (1e9, ">10cm"))
def bilan(label, t_an=None):
    lis_m = cen_m = 0.0; cls = collections.Counter(); n_lis = n_cen = 0
    for t in gs["tiles"]:
        e = gs["eco"][t.tile_id]
        for r in range(e.rows):
            for c in range(e.cols):
                for p in e.litiere[r][c]:
                    if p.tissu != "bois" or p.masse <= 0:
                        continue
                    if (t.tile_id, r, c) in LISIERE:
                        lis_m += p.masse; n_lis += 1
                    else:
                        cen_m += p.masse; n_cen += 1
                    cls[next(n for b, n in CLASSES if getattr(p, "diam_cm", 0.5) < b)] += p.masse
    print(f"   lisière ({len(LISIERE)} plots) : {n_lis} plots, masse {lis_m:.2f} | centre : "
          f"{n_cen} plots, masse {cen_m:.2f} | par grosseur {{{', '.join(f'{k}: {v:.2f}' for k, v in cls.items())}}}"
          + (f" | fructif. saprophytes du bois (plot-sem.) {dict(fruits)}" if CARPO else ""))
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
    if CARPO:
        for tid, ks in srv._snapshot()["carpophores"].items():
            for (r, c) in {(k[0], k[1]) for k in ks if k[6] in SAPRO_BOIS}:
                fruits[("lisière" if (tid, r, c) in LISIERE else "centre", w // 52)] += 1
    if w % 52 == 51 or w == N - 1:
        bilan(f"sem {w + 1}", t_an[w // 52])
