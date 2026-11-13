"""
SYMBIOSE — tests/test_gestes_lisibles.py
Tests ciblés du sprint GESTES LISIBLES ① (moteur + pont). Spec :
`docs/joueur/gestes/conception_gestes_lisibles.md` §3, §5, §6 ; kickoff
`sprints/joueur/gestes/sprint_gestes_lisibles/01_moteur_pont.md`.

Suites :
  A. TRACES   — écrite au geste payé, pas au refus ; expiration ; plafond FIFO ;
                absente du `game_state` sans geste ; exportée au snapshot ;
  B. RÈGLES   — `ecraser` sur un volant refusé sans dépense ; déraciné couché ;
                pot hors du jardin refusé sans dépense ;
  C. MOTS     — les phrases des gestes appliqués ne portent aucun chiffre ;
  D. EXPORT   — `sol_sec`, `volants` et `habitats_auxiliaires` (④) au snapshot.

Usage (depuis data/code/) :
  python3 -m tests.test_gestes_lisibles
"""
import contextlib
import re
import sys

from sim import vigueur as V
from sim.traces_sol import DUREE_SEMAINES, PLAFOND_TRACES, ecrire_trace, traces_par_tuile
from tools.simserver.server import SimServer

_results = []
J = "joueur_1"


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _serveur():
    srv = SimServer()
    with contextlib.redirect_stdout(sys.stderr):
        srv.cmd_init({"config": "full", "seed": 42})
    return srv


def _plein(srv):
    """Vigueur au plein, au-delà du coût de tout geste."""
    V.ensure_player(srv.engine.game_state, J)["courante"] = 1e6


def _act(srv, verb, target, params=None, plein=True):
    if plein:
        _plein(srv)
    return srv.cmd_action({"verb": verb, "target": target, "params": params or {}})


def _tuile(srv):
    return srv.engine.game_state["tiles"][0]


# --- A. traces ---------------------------------------------------------------
def test_traces():
    print("\n[A] registre des traces de gestes")
    srv = _serveur()
    gs = srv.engine.game_state
    with contextlib.redirect_stdout(sys.stderr):
        for _ in range(3):
            srv.engine.tick_semaine()
    check("aucune trace sans geste (clé absente du game_state)", "traces_sol" not in gs)
    snap = srv._snapshot()
    check("le snapshot ne crée pas le registre en le lisant",
          snap["traces_sol"] == {} and "traces_sol" not in gs)

    t = _tuile(srv)
    V.ensure_player(gs, J)["courante"] = 0.0
    r = srv.cmd_action({"verb": "becher", "target": {"tile": t.tile_id, "r": 2, "c": 3}})
    check("bêcher refusé (Vigueur vide) → aucune trace",
          not r["result"]["applied"] and "traces_sol" not in gs, r["result"]["message"])

    r = _act(srv, "becher", {"tile": t.tile_id, "r": 2, "c": 3})
    traces = gs.get("traces_sol") or []
    check("bêcher payé → une trace `becher` au centre du plot",
          r["result"]["applied"] and len(traces) == 1
          and traces[0]["sorte"] == "becher" and (traces[0]["r"], traces[0]["c"]) == (2, 3)
          and traces[0]["x_cm"] == 175.0 and traces[0]["y_cm"] == 125.0, traces)
    r = _act(srv, "arroser", {"tile": t.tile_id, "x_cm": 61.0, "y_cm": 33.0})
    derniere = gs["traces_sol"][-1]
    check("arroser → trace au POINT cliqué (plot résolu)",
          derniere["sorte"] == "arroser" and (derniere["x_cm"], derniere["y_cm"]) == (61.0, 33.0)
          and (derniere["r"], derniere["c"]) == (0, 1), derniere)
    snap = r["snapshot"]
    exp = snap["traces_sol"].get(t.tile_id, [])
    check("export : liste par tuile [r, c, x, y, sorte, age]",
          [2, 3, 175.0, 125.0, "becher", 0] in exp, exp)
    r = _act(srv, "pincer", {"tile": t.tile_id, "x_cm": 0.0, "y_cm": 0.0})
    check("un geste sans sorte de trace n'en écrit pas", len(gs["traces_sol"]) == 2)

    # Expiration : l'arrosage (1 semaine) part, le bêchage (6) reste.
    gs["week"] += 1
    exp = traces_par_tuile(gs).get(t.tile_id, [])
    check("expiration : l'auréole d'arrosage s'efface après sa durée",
          [e[4] for e in exp] == ["becher"] and exp[0][5] == 1, exp)
    gs["week"] += DUREE_SEMAINES["becher"]
    check("expiration : plus rien après 6 semaines", traces_par_tuile(gs) == {})

    # Plafond FIFO.
    for i in range(PLAFOND_TRACES + 10):
        ecrire_trace(gs, t.tile_id, 0, 0, float(i), 0.0, "pas")
    check("plafond FIFO : registre borné, les plus anciennes parties",
          len(gs["traces_sol"]) == PLAFOND_TRACES
          and gs["traces_sol"][0]["x_cm"] == 10.0, len(gs["traces_sol"]))


# --- B. règles ---------------------------------------------------------------
def test_regles():
    print("\n[B] volants, déraciné couché, pot hors du jardin")
    srv = _serveur()
    gs = srv.engine.game_state
    t = _tuile(srv)
    V.ensure_player(gs, J)["courante"] = 50.0
    r = srv.cmd_action({"verb": "ecraser",
                        "target": {"tile": t.tile_id, "r": 1, "c": 1, "espece": "abeille"}})
    check("ecraser une abeille → refusé, rien dépensé",
          not r["result"]["applied"] and r["result"]["cost"] == 0.0
          and V.ensure_player(gs, J)["courante"] == 50.0, r["result"]["message"])
    check("ecraser un volant ne laisse pas de pas", "traces_sol" not in gs)
    r = _act(srv, "ecraser", {"tile": t.tile_id, "r": 1, "c": 1, "espece": "puceron"})
    check("ecraser un puceron → appliqué, un pas au sol",
          r["result"]["applied"] and gs["traces_sol"][-1]["sorte"] == "pas")

    t, arbre = next((x, p) for x in gs["tiles"] for p in x.plants
                    if p.is_alive and getattr(p.plant_class, "ligneux", False))
    r = _act(srv, "deraciner", {"tile": t.tile_id, "x_cm": arbre.x_cm, "y_cm": arbre.y_cm})
    check("déraciné → cadavre couché d'emblée",
          r["result"]["applied"] and arbre.stade_mort == "couchee", arbre.stade_mort)

    V.ensure_player(gs, J)["courante"] = 50.0
    n0 = len(gs.get("containers", []))
    for x, y in ((-10.0, 500.0), (500.0, 2500.0)):
        r = srv.cmd_action({"verb": "poser_pot", "target": {"x_cm": x, "y_cm": y},
                            "params": {"substrat": "terreau", "volume": 5.0}})
        check(f"poser_pot hors du jardin ({x:.0f}, {y:.0f}) → refusé sans dépense",
              not r["result"]["applied"] and r["result"]["cost"] == 0.0
              and len(gs.get("containers", [])) == n0, r["result"]["message"])
    r = _act(srv, "poser_pot", {"x_cm": 300.0, "y_cm": 300.0},
             {"substrat": "terreau", "volume": 5.0})
    check("poser_pot dans le jardin → appliqué", r["result"]["applied"])
    idx = len(gs["containers"]) - 1
    r = _act(srv, "deplacer_pot", {"container": idx, "x_cm": 2100.0, "y_cm": 300.0})
    check("deplacer_pot hors du jardin → refusé", not r["result"]["applied"]
          and gs["containers"][idx].x_cm == 300.0, r["result"]["message"])


# --- C. mots -----------------------------------------------------------------
def test_mots():
    print("\n[C] phrases sans chiffre")
    srv = _serveur()
    gs = srv.engine.game_state
    t = _tuile(srv)
    eco = gs["eco"][t.tile_id]
    tid = t.tile_id
    eco.deposer_litiere(4, 4, "feuille", 1.0)
    from sim.actions.paillage import mulch_stock
    mulch_stock(gs)["paille"] = 5.0
    gestes = [
        ("arroser", {"tile": tid, "x_cm": 30.0, "y_cm": 30.0}, {}),
        ("becher", {"tile": tid, "r": 1, "c": 2}, {}),
        ("grelinette", {"tile": tid, "r": 1, "c": 3}, {}),
        ("glaner", {"tile": tid, "r": 4, "c": 4}, {}),
        ("pailler", {"tile": tid, "r": 4, "c": 4}, {"nature": "paille"}),
        ("creuser", {"tile": tid, "r": 5, "c": 5}, {}),
        ("drainer", {"tile": tid, "r": 5, "c": 5}, {}),
        ("ecraser", {"tile": tid, "r": 2, "c": 2, "espece": "puceron"}, {}),
        ("poser_bac", {"tile": tid, "r": 0, "c": 0}, {}),
        ("poser_ruche", {"tile": tid, "r": 0, "c": 1}, {}),
        ("poser_pot", {"x_cm": 300.0, "y_cm": 300.0}, {"substrat": "terreau", "volume": 5.0}),
    ]
    messages = []
    for verb, target, params in gestes:
        r = _act(srv, verb, target, params)
        messages.append((verb, r["result"]["applied"], r["result"]["message"]))
    bac = next(s for s in eco.structures if s.kind == "bac")
    ruche = next(s for s in eco.structures if s.kind == "ruche")
    bac.compost_mur = 1.0
    ruche.miel = 3.0
    i_bac, i_ruche = eco.structures.index(bac), eco.structures.index(ruche)
    for verb, target in (("epandre", {"tile": tid, "structure": i_bac, "r": 3, "c": 3}),
                         ("recolter_miel", {"tile": tid, "structure": i_ruche})):
        r = _act(srv, verb, target)
        messages.append((verb, r["result"]["applied"], r["result"]["message"]))
    for verb, applied, msg in messages:
        check(f"{verb} : appliqué, phrase sans chiffre",
              applied and not re.search(r"\d", msg), msg)


# --- D. export ---------------------------------------------------------------
def test_export():
    print("\n[D] sol sec et volants au snapshot")
    srv = _serveur()
    gs = srv.engine.game_state
    t = _tuile(srv)
    eco = gs["eco"][t.tile_id]
    eco.humidite.data[0][0] = 0.1
    snap = srv._snapshot()
    sec = snap["sol_sec"]
    check("sol_sec : une entrée par tuile", set(sec) == {x.tile_id for x in gs["tiles"]})
    check("sol_sec : le plot asséché y figure, valeur brute arrondie",
          [0, 0, 0.1] in sec[t.tile_id], sec[t.tile_id][:3])
    check("volants : abeille, merle, libellule ; pas le puceron ni le lombric",
          {"abeille", "merle", "libellule"} <= set(snap["volants"])
          and not {"puceron", "lombric"} & set(snap["volants"]), snap["volants"])
    hab = snap["habitats_auxiliaires"]
    check("habitats : une entrée par tuile", set(hab) == {x.tile_id for x in gs["tiles"]})
    avant = len(hab[t.tile_id])
    r = _act(srv, "favoriser_auxiliaire", {"tile": t.tile_id})
    apres = srv._snapshot()["habitats_auxiliaires"][t.tile_id]
    check("favoriser_auxiliaire → une tige porte une rondelle de plus",
          r["result"]["applied"] and sum(n for _, n in apres) == sum(
              n for _, n in hab[t.tile_id]) + 1 and len(apres) >= avant, apres)


def main():
    test_traces()
    test_regles()
    test_mots()
    test_export()
    n_ok = sum(1 for _, ok in _results if ok)
    print(f"\n{n_ok}/{len(_results)} checks OK")
    return 0 if n_ok == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
