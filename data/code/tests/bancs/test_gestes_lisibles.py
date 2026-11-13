"""
SYMBIOSE — tests/bancs/test_gestes_lisibles.py
Oracle du banc `gestes_lisibles` (sprint GESTES LISIBLES ⑥) : le PLAN DE TEST du banc,
joué au pont geste par geste, dans la FORME DE CIBLE que la vue envoie après un clic
au point du plan (`world/WorldView.ActionDispatch.cs` + `WorldView.DeuxTemps.cs`).

C'est l'instrument de tri de la recette F5 : si l'oracle dit « appliqué, une trace,
une phrase sans chiffre » mais que l'écran reste muet, le défaut est dans la VUE.

Vérifie, par geste :
  A. le verdict attendu (appliqué ; refus pour le moustique — un volant s'envole) ;
  B. une trace au sol pour chaque geste qui en laisse une (`SORTE_DU_VERBE`), aucune
     pour les autres ni pour un refus ;
  C. aucune phrase de geste appliqué ne porte de chiffre (§5).

Usage (depuis data/code/) : python3 -m tests.bancs.test_gestes_lisibles
"""
import contextlib
import re
import sys

from bancs import gestes_lisibles as B
from bancs.plan_test import resoudre_plan
from constants import PLOT_CM
from sim.traces_sol import SORTE_DU_VERBE
from tools.simserver.server import SimServer

_res = []
# N° (1-based) des gestes REFUSÉS attendus : écraser un VOLANT (le pied ne l'attrape pas).
REFUS_ATTENDUS = {i for i, (_, *cibles) in enumerate(B.PLAN_TEST, start=1)
                  if getattr(cibles[0], "espece", None) == "moustique"}
GRAINE_VUE = "ail"              # 1ʳᵉ graine du catalogue trié de la vue (④)
NATURE_VUE = "feuilles"         # 1ʳᵉ nature du cycle N de la vue (`Natures[0]`)

# Désignation de la vue par verbe (Kinds de `WorldView.Actions.cs`).
_PLANTE = {"pincer", "couper", "tailler", "arracher", "deraciner", "recolter"}
_PLOT = {"becher", "grelinette", "creuser", "drainer", "glaner", "pailler"}


def check(nom, cond, detail=""):
    _res.append((nom, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {nom}" + (f" — {detail}" if detail else ""))


def _localiser(gs, x, y):
    """Point MONDE → (tuile, r, c, x local, y local), comme `FindPlot` de la vue."""
    for t in gs["tiles"]:
        lx, ly = x - t.origin_x_cm, y - t.origin_y_cm
        r, c = int(ly // PLOT_CM), int(lx // PLOT_CM)
        if 0 <= r < t.grid_rows and 0 <= c < t.grid_cols:
            return t.tile_id, r, c, lx, ly
    raise AssertionError(f"point hors tuile : {x}, {y}")


def _structure(gs, tuile, kind=None, r=None, c=None):
    """Index (dans sa tuile) du bac/pile le plus proche (`kind`) ou de la structure du
    plot (`r`, `c`) — `FindNearestStructure` / `FindStructureIndex` de la vue."""
    structs = gs["eco"][tuile].structures
    if kind is not None:
        return next(i for i, s in enumerate(structs) if s.kind == kind)
    return next(i for i, s in enumerate(structs) if s.plot == (r, c))


def cible_vue(gs, entree, espece):
    """`(verbe, target, params)` que la vue envoie pour une entrée du plan résolu."""
    verbe = entree["verbe"]
    pts = [_localiser(gs, x, y) for x, y in entree["clics"]]
    tuile, r, c, lx, ly = pts[-1]
    if verbe in _PLANTE:
        prms = {"cible": "apex"} if verbe == "tailler" else {}
        return verbe, {"tile": tuile, "x_cm": lx, "y_cm": ly}, prms
    if verbe in _PLOT:
        prms = {"nature": NATURE_VUE} if verbe == "pailler" else {}
        return verbe, {"tile": tuile, "r": r, "c": c}, prms
    if verbe == "ecraser":
        return verbe, {"tile": tuile, "r": r, "c": c, "espece": espece}, {"urgence": False}
    if verbe == "arroser":
        return verbe, {"tile": tuile, "x_cm": lx, "y_cm": ly}, {"urgence": False}
    if verbe == "planter":
        return verbe, {"tile": tuile, "x_cm": lx, "y_cm": ly}, {"species": GRAINE_VUE}
    if verbe == "favoriser_auxiliaire":
        return verbe, {"tile": tuile}, {}
    if verbe in ("composter", "empiler_bois"):
        kind = "bac" if verbe == "composter" else "pile"
        return verbe, {"tile": tuile, "structure": _structure(gs, tuile, kind),
                       "r": r, "c": c}, {}
    if verbe in ("retourner", "recolter_miel"):
        return verbe, {"tile": tuile, "structure": _structure(gs, tuile, r=r, c=c)}, {}
    if verbe == "epandre":
        t0, r0, c0, _, _ = pts[0]
        return verbe, {"tile": tuile, "structure": _structure(gs, t0, r=r0, c=c0),
                       "r": r, "c": c}, {}
    if verbe == "bouturer":
        t0, _, _, mx, my = pts[0]
        return verbe, {"tile": t0, "x_cm": mx, "y_cm": my}, {"r": r, "c": c}
    if verbe == "planter_conteneur":
        return verbe, {"container": 0}, {"species": GRAINE_VUE}
    if verbe == "deplacer_pot":
        x, y = entree["clics"][-1]
        return verbe, {"container": 0, "x_cm": x, "y_cm": y}, {}
    raise AssertionError(f"verbe sans désignation connue : {verbe}")


def main():
    srv = SimServer()
    with contextlib.redirect_stdout(sys.stderr):
        srv.cmd_init({"config": "gestes_lisibles"})
    gs = srv.engine.game_state
    rep = srv.cmd_plan_test({"banc": "gestes_lisibles"})
    plan = rep["plan"]
    print(f"\n[plan] {len(plan)} gestes")
    check("plan complet, toutes les cibles résolues",
          len(plan) == len(B.PLAN_TEST) and all(e["clics"] for e in plan),
          str([e["verbe"] for e in plan if not e["clics"]]))
    for i, (entree, brut) in enumerate(zip(plan, B.PLAN_TEST), start=1):
        espece = getattr(brut[1], "espece", None)
        verbe, target, params = cible_vue(gs, entree, espece)
        n0 = len(gs.get("traces_sol") or [])
        res = srv.cmd_action({"verb": verbe, "target": target, "params": params})["result"]
        n1 = len(gs.get("traces_sol") or [])
        attendu = i not in REFUS_ATTENDUS
        trace = 1 if res["applied"] and verbe in SORTE_DU_VERBE else 0
        check(f"{i:2d}. {verbe} → {entree['cible']} : "
              f"{'appliqué' if attendu else 'refus'} « {res['message']} »",
              bool(res["applied"]) == attendu
              and n1 - n0 == trace
              and (not res["applied"] or not re.search(r"\d", res["message"])),
              f"traces +{n1 - n0}")
    ok = sum(1 for _, r in _res if r)
    print(f"\n{ok}/{len(_res)} checks OK")
    return 0 if ok == len(_res) else 1


if __name__ == "__main__":
    sys.exit(main())
