"""D121 ① : glace + marnage de la mare NE (monde full). Lecture seule.
Usage (depuis data/code/) : PYTHONPATH=. python3 <ce fichier> <seed> [semaines=104]"""
import sys
from tools.simserver.server import SimServer
from sim.mare_initiale import MARE_FOND
from sim.engine import saison_de
from sim.weather import weather_state
from fields.ecofields.constants import SEUIL_FLAQUE

seed = int(sys.argv[1]); W = int(sys.argv[2]) if len(sys.argv) > 2 else 104
srv = SimServer(); srv.cmd_init({"config": "full", "seed": seed})
gs = srv.engine.game_state; eco = gs["eco"]["NE"]
CENTRE = (8, 5)
prise, centre_sec, decouv = [], 0, {}
for w in range(W):
    srv.cmd_step_week({})
    week = gs["week"]; sais = saison_de(((week - 1) % 52) + 1)
    _, t, _ = weather_state(seed, week, False)
    g = eco.glace.data[CENTRE[0]][CENTRE[1]]
    if g >= 0.5:
        prise.append((week, sais, round(t, 1), round(g, 2)))
    if eco.eau_surface.data[CENTRE[0]][CENTRE[1]] <= SEUIL_FLAQUE:
        centre_sec += 1
    n_sec = sum(eco.eau_surface.data[r][c] <= SEUIL_FLAQUE for r, c in MARE_FOND)
    if n_sec:
        decouv.setdefault(sais, []).append(n_sec)
    if w % 13 == 0:
        print(w, sais, "T", round(t, 1), "lames", [round(eco.eau_surface.data[r][c], 2) for r, c in MARE_FOND],
              "glace", [round(eco.glace.data[r][c], 2) for r, c in MARE_FOND])
print(f"seed {seed} : semaines mare prise (centre ≥0,5) = {len(prise)}/{W}")
for p in prise: print("  prise", p)
print(f"centre sous SEUIL_FLAQUE : {centre_sec}/{W}")
print("bords découverts par saison (sem. avec ≥1 plot sec, moy. plots secs) :",
      {s: (len(v), round(sum(v) / len(v), 1)) for s, v in decouv.items()})
