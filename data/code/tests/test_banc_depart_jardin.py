"""
SYMBIOSE — tests/test_banc_depart_jardin.py
Oracle du banc `depart_jardin` (D140 C, sprint départ du jardin ⑥), lancé À LA DEMANDE.

Monte le banc par le SERVEUR (chemin de la vue au F5 : seed 42, s3, sans warmup) et
vérifie, semaine après semaine, ce que la recette F5 annonce :
  ouverture  — 3 godets (2 dedans, 1 dehors), `repiquer` ouvert, la tomate repiquée
               trop tôt porte son choc (`memoires.racines_coupees` au pont) ;
  trop tôt   — elle meurt de la gelée tardive, et le carnet ET la chronique disent
               `froid` (pas `non_consignee`) ;
  graines    — les haricots semés lèvent en terre ;
  témoin     — le godet resté dans la maison est vivant à la fin ;
  après      — le godet (2) repiqué par le pont en s15 (nuits douces) vit encore en s19.
Mesuré [seed 42, n=1] : tomate morte `froid` en s5 ; haricots levés en s5 et s8.

Lancement (depuis data/code/) : python3 -m tests.test_banc_depart_jardin
"""

import sys

from tools.sim_server import SimServer
from bancs.depart_jardin import NOM, TROP_TOT, GRAINES, CIBLE_REPIQUAGE

SEMAINE_REPIQUAGE = 15
SEMAINE_FIN = 19


def main():
    srv = SimServer()
    rep = srv.cmd_init({"config": "depart_jardin", "seed": 42})
    assert rep["ok"] and rep.get("warmup") == 0, rep
    gs = srv.engine.game_state
    assert gs["week"] == 3, gs["week"]
    snap = srv._snapshot()
    pots = snap["containers"]
    assert [c["interieur"] for c in pots] == [True, True, False], pots
    assert all(len(c["plants"]) == 1 for c in pots)
    assert "repiquer" in snap["player"]["gestes_debloques"]
    choc = [p["memoires"]["racines_coupees"] for p in snap["plants"]]
    assert choc and choc[0] > 0.0, choc
    print(f"[ouverture] PASS — 2 godets dedans, 1 dehors, repiquer ouvert, choc {choc[0]}")

    tuile = next(t for t in gs["tiles"] if t.tile_id == NOM)
    tomate = next(p for p in tuile.plants if p.position == TROP_TOT)
    while gs["week"] < SEMAINE_REPIQUAGE:
        srv.cmd_step_week({})
    assert not tomate.is_alive
    j = gs["journal"][gs["current_player"]]["entries"]
    morts = [(e["espece"], e["cause"]) for e in j if e["kind"] == "mort"]
    assert ("tomate", "froid") in morts, morts
    chron = [(e["espece"], e["cause"]) for e in srv._chronique.brut()["registre"]]
    assert ("tomate", "froid") in chron, chron
    print(f"[trop tôt] PASS — carnet {morts}, chronique {chron}")
    levees = [p for p in tuile.plants if p.position in GRAINES]
    assert levees, "aucun haricot levé"
    print(f"[graines] PASS — {len(levees)} haricot(s) levé(s)")

    r, c = CIBLE_REPIQUAGE
    rr = srv.cmd_action({"cmd": "action", "verb": "repiquer",
                         "target": {"container": 1, "tile": NOM, "r": r, "c": c}})
    assert rr["result"]["applied"], rr["result"]
    repiquee = next(p for p in tuile.plants if p.position == CIBLE_REPIQUAGE)
    while gs["week"] < SEMAINE_FIN:
        srv.cmd_step_week({})
    assert repiquee.is_alive
    assert gs["containers"][0].plants[0].is_alive
    print(f"[après] PASS — tomate repiquée en s{SEMAINE_REPIQUAGE} vivante en "
          f"s{SEMAINE_FIN} ; le témoin de la maison aussi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
