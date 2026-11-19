"""
SYMBIOSE — tests/test_banc_stress_au_bilan.py
Oracle du banc `stress_au_bilan` (D140 G, sprint stress au bilan ⑤), lancé À LA DEMANDE.

Monte le banc par le SERVEUR (chemin de la vue au F5 : seed 42, s12, sans warmup),
simule 8 semaines (s12 → s20) et vérifie qu'une plante meurt de chaque cause, par
son mécanisme, et que le carnet le DIT (cause amont d'une famine, ⑤) :
  destruction  — le jeune chêne « meurt annelé » (carnet : herbivorie) ;
  hydraulique  — le chêne sensible « meurt de dessèchement », réserves encore hautes ;
                 le tolérant vit, flétri, « desséchée » (`cause_bilan`) ;
  racines      — le pommier noyé meurt de faim, carnet : asphyxie ;
  fin de cycle — la phacélie ; vieillesse — la consoude « meurt de sénescence » ;
  famine       — le poivron à l'ombre, carnet : ombre (et non « famine »).
Mesuré [seed 42, n=1] : morts en s12, s14, s14, s15, s15, s19.

Lancement (depuis data/code/) : python3 -m tests.test_banc_stress_au_bilan
"""

import sys

from tools.sim_server import SimServer
from bancs.stress_au_bilan import SENSIBLE, TOLERANT

SEMAINES = 8


def _tuile(gs, nom):
    return next(t for t in gs["tiles"] if t.tile_id == nom)


def main():
    srv = SimServer()
    rep = srv.cmd_init({"config": "stress_au_bilan", "seed": 42})
    assert rep["ok"] and rep.get("warmup") == 0, rep.get("warmup")
    gs = srv.engine.game_state
    assert gs["week"] == 12, gs["week"]
    hydro = _tuile(gs, "HYDRAULIQUE")
    sensible, tolerant = (next(p for p in hydro.plants if p.position == (2, c))
                          for c in (SENSIBLE, TOLERANT))
    reserves_sensible = None
    for _ in range(SEMAINES):
        if sensible.is_alive:
            reserves_sensible = sensible.reserves
        assert srv.cmd_step_week({}).get("ok", True)
    j = gs["journal"][gs["current_player"]]["entries"]
    morts = {(e["zone"][0], e["espece"]): e["cause"] for e in j if e["kind"] == "mort"}
    print(" morts au carnet :", morts)

    assert morts.get(("DESTRUCTION", "chene")) == "herbivorie", morts
    print("[destruction] PASS — chêne annelé (herbivorie)")
    assert not sensible.is_alive and reserves_sensible > 0.5, reserves_sensible
    assert morts.get(("HYDRAULIQUE", "chene")) == "secheresse", morts
    assert tolerant.is_alive
    print(f"[hydraulique] PASS — sensible desséché (réserves {reserves_sensible:.2f}), "
          f"tolérant vivant")
    assert morts.get(("RACINES", "pommier")) == "asphyxie", morts
    print("[racines] PASS — pommier noyé (asphyxie)")
    assert morts.get(("FIN_DE_CYCLE", "phacelie")) == "fin_de_cycle", morts
    assert morts.get(("VIEILLESSE", "consoude")) == "sénescence", morts
    print("[cycle, âge] PASS — phacélie fin de cycle, consoude sénescence")
    assert morts.get(("FAMINE", "poivron")) == "ombre", morts
    print("[famine] PASS — poivron à l'ombre, le carnet dit l'ombre")

    snap = srv._snapshot()
    vivantes = [p for p in snap["plants"] if not p.get("dead")]
    assert vivantes and all("cause_bilan" in p for p in vivantes)
    assert any(p["cause_bilan"] == "dessechee" for p in vivantes), \
        [p["cause_bilan"] for p in vivantes]
    print("[pont] PASS — `cause_bilan` sur chaque vivante, le chêne tolérant « desséchée »")
    return 0


if __name__ == "__main__":
    sys.exit(main())
