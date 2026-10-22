"""Parasite de faiblesse (D111 ④) — lecture seule. Usage (depuis data/code/) :
  python3 ../../sprints/champs/sol/sprint_sol_qui_respire/mesures/parasite.py seed semaines [--sans]
Rapporte par année : hôtes (famille/espèce listée par un parasite du registre), hôtes
ATTAQUÉS (pression > 0 au moins une semaine), pression max, morts d'hôtes, plantes
dont l'eau ressentie < eau du sol (campagnol + parasite), population, tick moyen.
`--sans` = état d'avant ④ (pression nulle, eau ressentie = eau du sol)."""
import sys, os, time, statistics as st
sys.path.insert(0, os.getcwd())
import sim.engine.croissance as CR
import sim.engine.mortalite as MO
import sim.engine.racines as RA
from tools.simserver.server import SimServer

SANS = "--sans" in sys.argv
if SANS:
    CR.pression_parasite = lambda plant, eco: 0.0
    CR.eau_percue = MO.eau_percue = lambda plant, eco, hum: hum
attaque, pmax, ressent = {}, {}, set()
_pp = CR.pression_parasite
def pp(plant, eco):
    v = _pp(plant, eco)
    if v > 0:
        k = id(plant); attaque[k] = attaque.get(k, 0) + 1
        pmax[k] = max(pmax.get(k, 0.0), v)
    return v
CR.pression_parasite = pp
_ep = CR.eau_percue
def ep(plant, eco, hum):
    v = _ep(plant, eco, hum)
    if v < hum:
        ressent.add(id(plant))
    return v
CR.eau_percue = ep

seed, N = int(sys.argv[1]), int(sys.argv[2])
srv = SimServer(); srv.cmd_init({"config": "full", "seed": seed})
gs = srv.engine.game_state
def vivantes():
    return [p for t in gs["tiles"] for p in t.plants if p.is_alive]
hotes_vus, morts_hotes = {}, []
t_an = {}
for w in range(N):
    avant = {id(p): p for p in vivantes() if RA.est_hote(p)}
    hotes_vus.update(avant)
    t0 = time.perf_counter(); srv.cmd_step_week({}); dt = time.perf_counter() - t0
    t_an.setdefault(w // 52, []).append(dt)
    for k, p in avant.items():
        if not p.is_alive:
            morts_hotes.append((w + 1, p.name, k in attaque))
    if w % 52 == 51 or w == N - 1:
        att = [(hotes_vus[k].name, n, round(pmax[k], 3)) for k, n in attaque.items()
               if k in hotes_vus]
        print(f"sem {w + 1}: plantes {len(vivantes())} | hôtes vus {len(hotes_vus)} "
              f"({sorted({p.name for p in hotes_vus.values()})}) | attaqués (nom, sem., pmax) "
              f"{att} | morts d'hôtes {morts_hotes} | eau ressentie < sol : "
              f"{len(ressent)} plantes | tick moy {1000 * st.mean(t_an[w // 52]):.0f} ms")
