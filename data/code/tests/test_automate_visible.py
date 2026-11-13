"""
SYMBIOSE — tests/test_automate_visible.py
Tests ciblés du sprint GESTES LISIBLES ⑤ (automate visible + mode testeur). Spec :
`docs/joueur/gestes/conception_gestes_lisibles.md` §7 ; kickoff
`sprints/joueur/gestes/sprint_gestes_lisibles/05_automate.md`.

Suites :
  A. JOURNAL — chaque ligne `geste` de l'automate porte `point` (tuile-local) ;
               son arrosage écrit sa trace au sol à ce point ;
  B. PLAN    — `plan_test` du banc `sol_canvas` résolu en points MONDE ; banc sans
               plan → liste vide ; cible introuvable → aucun clic.

Usage (depuis data/code/) :
  python3 -m tests.test_automate_visible
"""
import contextlib
import sys

from bancs.plan_test import plot, resoudre_plan
from sim import vigueur as V
from sim.traces_sol import SORTE_DU_VERBE
from tools.jardinier_auto.execution import executer, point_vise
from tools.jardinier_auto.proposition import Plan
from tools.simserver.server import SimServer

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _serveur(config):
    srv = SimServer()
    with contextlib.redirect_stdout(sys.stderr):
        srv.cmd_init({"config": config, "seed": 42})
    return srv


def test_journal():
    print("\n[A] journal de l'automate : point visé + trace au sol")
    srv = _serveur("full")
    srv.cmd_automate({"op": "on", "profil": {"desherbage": "curatif"}})
    with contextlib.redirect_stdout(sys.stderr):
        for _ in range(6):
            srv.cmd_step_week({})
    gs = srv.engine.game_state
    gestes = [e for e in gs.get("automate_journal", []) if e["categorie"] == "geste"]
    check("l'automate a joué des gestes", len(gestes) > 0, f"{len(gestes)} gestes")
    check("chaque ligne geste porte la clé `point`", all("point" in e for e in gestes))
    places = [e for e in gestes if e["point"] is not None]
    check("les gestes situés ont un point tuile-local dans [0, 2000]",
          places and all(0 <= v <= 2000 for e in places for v in e["point"]),
          f"{len(places)} situés")
    # Un arrosage de l'automate (rare au monde full : on le joue par `executer`, la
    # surface d'exécution de la boucle) laisse sa trace AU POINT que le journal note.
    tile = gs["tiles"][0]
    plant = next(p for p in tile.plants if p.vitalite > 0.0)
    plan = Plan("arroser", "milieu", None, None, "eau", 10)
    V.ensure_player(gs, gs["current_player"])["courante"] = 1e6
    res = executer(gs, gs["current_player"], gs["eco"][tile.tile_id], plant, plan)
    x, y = point_vise(plant, plan)
    derniere = gs.get("traces_sol", [{}])[-1]
    check("l'arrosage de l'automate laisse sa trace au point visé",
          res == "ok" and derniere.get("sorte") == SORTE_DU_VERBE["arroser"]
          and (derniere["tuile"], derniere["x_cm"], derniere["y_cm"]) == (tile.tile_id, x, y),
          str(derniere))
    bloc = srv.automate_block(gs)
    check("le bloc `automate` du snapshot porte le point",
          any(e.get("point") for e in bloc["trace"]))


def test_plan():
    print("\n[B] plan de test d'un banc (commande plan_test)")
    srv = _serveur("sol_canvas")
    rep = srv.cmd_plan_test({"banc": "sol_canvas"})
    plan = rep["plan"]
    check("plan du banc sol_canvas : 4 gestes", rep["ok"] and len(plan) == 4,
          str([p["verbe"] for p in plan]))
    check("chaque geste a ses clics (épandre : deux)",
          [len(p["clics"]) for p in plan] == [1, 1, 2, 1])
    t = next(t for t in srv.engine.game_state["tiles"] if t.tile_id == "SOLCANVAS")
    x, y = plan[0]["clics"][0]
    check("clic en coordonnées MONDE (origine de tuile + centre du plot)",
          (x, y) == (t.origin_x_cm + 75.0, t.origin_y_cm + 125.0), f"{x}, {y}")
    check("banc sans plan → liste vide",
          srv.cmd_plan_test({"banc": "objet_en_main"})["plan"] == [])
    vide = resoudre_plan(srv.engine.game_state,
                         (("grelinette", plot("ABSENTE", 0, 0)),))[0]
    check("cible introuvable → aucun clic ; grelinette = ameublir + Maj",
          vide["clics"] == [] and vide["geste"] == "becher" and vide["maj"])


def main():
    test_journal()
    test_plan()
    ok = sum(1 for _, r in _results if r)
    print(f"\n{ok}/{len(_results)} checks OK")
    return 0 if ok == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
