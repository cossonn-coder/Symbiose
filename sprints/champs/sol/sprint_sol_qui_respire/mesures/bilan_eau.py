"""Bilan hydrique par an (lecture seule, monkeypatch mémoire). Usage : bilan_eau.py seed semaines"""
import sys, time, statistics as st
from tools.simserver.server import SimServer
from fields.ecofields import container as C
from sim.weather import weather_state
EF = C.EcoFields
acc = {"upt": 0.0, "drain": 0.0, "hydro": 0.0, "rosee": 0.0}
from fields.ecofields import rosee as R
_ro = R.tick_rosee
_up, _hy = EF.plant_uptake, EF.tick_hydrology
def up(self, *a, **k):
    r = _up(self, *a, **k); acc["upt"] += r.get("humidite", 0.0); return r
def hy(self, *a, **k):
    s0 = sum(map(sum, self.humidite.data)); p = _hy(self, *a, **k)
    acc["drain"] += sum(x[2] for x in p); acc["hydro"] += sum(map(sum, self.humidite.data)) - s0; return p
def ro(eco, *a, **k):
    s0 = sum(map(sum, eco.humidite.data)); out = _ro(eco, *a, **k)
    acc["rosee"] += sum(map(sum, eco.humidite.data)) - s0; return out
EF.plant_uptake, EF.tick_hydrology = up, hy
import fields.ecofields.ticks as T
for mod in (R, T):
    pass
T._tick_rosee = ro
seed, N = int(sys.argv[1]), int(sys.argv[2])
srv = SimServer(); srv.cmd_init({"config": "full", "seed": seed})
gs = srv.game_state if hasattr(srv, "game_state") else srv.engine.game_state
def ecos():
    e = srv.engine.game_state["eco"] if hasattr(srv, "engine") else gs["eco"]
    return [x for x in e.values()]
yr = {}
for w in range(N):
    acc.update(upt=0.0, drain=0.0, hydro=0.0, rosee=0.0)
    t0 = time.perf_counter(); srv.cmd_step_week({}); dt = time.perf_counter() - t0
    es = ecos(); nplots = sum(e.rows * e.cols for e in es)
    hs = [v for e in es for row in e.humidite.data for v in row]
    ev = weather_state(seed, w + 1)[0].kind   # semaine simulée = w+1 (moteur démarre à 1)
    y = yr.setdefault(w // 52, {"h": [], "u": 0, "d": 0, "hy": 0, "rain": 0, "n": [], "w": 0, "ro": 0,
                                "t": 0.0, "h10": None, "h35": None})
    y["t"] += dt
    if w % 52 == 9: y["h10"] = st.median(hs)
    if w % 52 == 34: y["h35"] = st.median(hs)
    y["h"].append(st.median(hs)); y["u"] += acc["upt"] / nplots; y["d"] += acc["drain"] / nplots
    y["hy"] += acc["hydro"] / nplots; y["ro"] += acc["rosee"] / nplots; y["w"] += 1
    y["rain"] += ev in ("Pluie prolongée", "Orage")
    y["n"].append(sum(1 for p in srv._snapshot()["plants"] if not p.get("dead")) if w % 13 == 0 else None)
for k, y in yr.items():
    n = [x for x in y["n"] if x is not None]
    print(f"an {k}: hum méd {st.median(y['h']):.2f} (fin {y['h'][-1]:.2f}) | /plot/sem : uptake {y['u']/y['w']:.4f} "
          f"drain {y['d']/y['w']:.4f} net_hydro {y['hy']/y['w']:+.4f} rosee {y['ro']/y['w']:.4f} | sem pluie {y['rain']} | plantes {n}"
          f" | h10 {y['h10']} h35 {y['h35']} | tick moy {1000*y['t']/y['w']:.0f} ms")
