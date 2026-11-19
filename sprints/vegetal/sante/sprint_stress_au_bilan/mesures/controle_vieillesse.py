"""Contrôle ④ stress au bilan : monde `full` (seed 42) s10→s62 — morts par cause,
exsudats déposés (lignes 🦠), microbiome moyen final, réserves des annuelles à
l'entrée en fin de cycle, durée. Lancer depuis data/code (HEAD ou arbre de travail) :
    python3 <chemin>/controle_vieillesse.py [nb_semaines]"""
import re, sys, time
from collections import Counter
sys.path.insert(0, ".")
from tools.sim_server import SimServer
from sim.evenements import evenements
from sim.engine.fin_de_cycle import fin_de_cycle
import sim.engine.mortalite as _mort

_semis = []                 # remplissage de chaque semis de fin de cycle (④ ; HEAD : 1,0)
_semer = _mort.semer_fin_de_cycle
def _espion(plant, tile, eco, seed, week, remplissage=1.0):
    _semis.append(remplissage)
    return _semer(plant, tile, eco, seed, week, remplissage=remplissage) \
        if "remplissage" in _semer.__code__.co_varnames else _semer(plant, tile, eco, seed, week)
_mort.semer_fin_de_cycle = _espion

N = int(sys.argv[1]) if len(sys.argv) > 1 else 52
srv = SimServer()
srv.cmd_init({"config": "full", "seed": 42})
eng = srv.engine
debut = eng.week
causes, par_esp = Counter(), Counter()
exsud = 0.0
entree_fdc = {}          # id plante → réserves à la 1re semaine de fin de cycle
t0 = time.time()
while eng.week < debut + N:
    for t in eng.tiles:
        for p in t.plants:
            if p.is_alive and id(p) not in entree_fdc and fin_de_cycle(p, eng.week):
                entree_fdc[id(p)] = p.reserves
    log = eng.tick_semaine()
    for l in log:
        m = re.search(r"Exsudats → microbiome/om \+([0-9.]+)", l)
        if m:
            exsud += float(m.group(1))
    for l in log:
        if "sénescence" in l and "🪦" in l:
            print("   ", eng.week, l.strip())
    for e in evenements(log):
        if e.kind == "mort":
            causes[e.cause or "?"] += 1
            par_esp[(e.cause or "?", e.espece)] += 1
dt = time.time() - t0
vivantes = sum(p.is_alive for t in eng.tiles for p in t.plants)
micro = [eng.game_state["eco"][t.tile_id].microbiome for t in eng.tiles]
mm = sum(sum(sum(r) for r in g.data) / (g.rows * g.cols) for g in micro) / len(micro)
r = sorted(entree_fdc.values())
print(f"durée {dt:.1f} s ; vivantes s{eng.week} {vivantes} ; exsudats Σ {exsud:.2f} ; "
      f"microbiome moyen {mm:.3f}")
print("MORTS", " ".join(f"{c}:{n}" for c, n in causes.most_common()))
print("PAR ESPÈCE", " ".join(f"{c}/{e}:{n}" for (c, e), n in par_esp.most_common(25)))
if r:
    print(f"fin de cycle : n={len(r)} réserves à l'entrée min {r[0]:.2f} "
          f"méd {r[len(r)//2]:.2f} max {r[-1]:.2f} ; < 0,5 : {sum(x < 0.5 for x in r)}")
if _semis:
    print(f"semis fin de cycle : n={len(_semis)} remplissage moyen "
          f"{sum(min(1.0, x) for x in _semis) / len(_semis):.2f}")
