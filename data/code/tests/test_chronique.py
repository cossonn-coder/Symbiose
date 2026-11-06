"""
SYMBIOSE — tests/test_chronique.py
Chronique des espèces (D127, tronçon ②) : `tools/simserver/chronique.py`.

1. Logique pure sur un faux monde (rapide, exact) : mort appariée à sa cause du log,
   mort sans ligne de log (`non_consignee`), mort par geste entre deux ticks
   (`hors_tick`), disparition puis retour au registre, levées comptées.
2. Serveur réel, banc `smoke` sur un peu plus d'un an : une annuelle disparaît,
   le texte est rendu, le rapport reste sérialisable, aucune cause « conflit ».

Lancement : `python3 -m tests.test_chronique` depuis `data/code/`.
"""
from __future__ import annotations

import json
from types import SimpleNamespace as NS

from plants.catalogue import PLANT_CATALOGUE
from tools.simserver.chronique import Chronique, HORS_TICK, NON_CONSIGNEE

ECHECS = []


def check(nom, ok, detail=""):
    print(("  ok   " if ok else "  ÉCHEC ") + nom + ("" if ok else f" — {detail}"))
    if not ok:
        ECHECS.append(nom)


TOMATE = PLANT_CATALOGUE["tomate"]


def _plante(r, c, age=10):
    return NS(plant_class=TOMATE, position=(r, c), is_alive=True, age_weeks=age)


def test_logique():
    a, b, c = _plante(1, 1), _plante(2, 2), _plante(3, 3, age=40)
    tuile = NS(tile_id="T0", plants=[a, b, c])
    engine = NS(game_state={"tiles": [tuile], "week": 1})
    ch = Chronique()

    # Tick de la semaine 1 : `a` meurt mangée (log), `b` meurt sans ligne de log.
    ch.avant_tick(engine)
    a.is_alive = b.is_alive = False
    engine.game_state["week"] = 2
    ch.apres_tick(engine, ["  [T0]",
                           f"    ✗ Santé {TOMATE.name}@(1, 1) -1 [herbivorie p=0.40] → meurt"])
    morts = ch._annee["morts"]["tomate"]
    check("mort appariée à sa cause du log", morts.get("herbivorie") == 1, dict(morts))
    check("mort sans log = non_consignee", morts.get(NON_CONSIGNEE) == 1, dict(morts))
    check("pas encore disparue (c vit)", not ch.registre, ch.registre)

    # Entre deux ticks : le joueur arrache `c`, la dernière → disparition hors tick.
    tuile.plants.remove(c)
    ch.avant_tick(engine)
    check("geste entre deux ticks = hors_tick", morts.get(HORS_TICK) == 1, dict(morts))
    r = ch.registre[-1] if ch.registre else {}
    check("disparition au registre (cause, âge, tuile)",
          r.get("quoi") == "disparition" and r.get("cause") == HORS_TICK
          and r.get("age_sem") == 40 and r.get("tuile") == "T0", r)

    # Tick suivant : une tomate lève → levée comptée + retour au registre.
    tuile.plants.append(_plante(4, 4, age=0))
    engine.game_state["week"] = 3
    ch.apres_tick(engine, [])
    check("levée comptée", ch._annee["levees"]["tomate"] == 1, ch._annee["levees"])
    check("retour au registre", ch.registre[-1]["quoi"] == "retour", ch.registre)

    # Lecture seule : le log n'est ni vidé ni modifié (le serveur le vide APRÈS).
    log = ["  [T0]", "    🌱 Tomate@(4, 4) → [PLANTULE]"]
    copie = list(log)
    ch.apres_tick(engine, log)
    check("le log n'est pas touché", log == copie, log)


def test_serveur():
    from tools.simserver.server import SimServer
    srv = SimServer()
    srv.cmd_init({"config": "smoke", "seed": 42})
    for _ in range(60):
        assert srv.cmd_step_week({}).get("ok")
    rep = srv.cmd_perf_report({})
    check("rapport sérialisable pour le pont", bool(json.dumps(rep)))
    ch = rep["chronique"]
    check("texte composé", ch["texte"].startswith("[chronique]") and "Registre" in ch["texte"])
    check("un bilan annuel", len(ch["brut"]["annees"]) == 1, ch["brut"]["annees"])
    disp = [r for r in ch["brut"]["registre"] if r["quoi"] == "disparition"]
    check("une espèce disparaît sur le banc court", len(disp) >= 1, ch["brut"]["registre"])
    causes = {c for b in ch["brut"]["annees"] for cs in b["morts"].values() for c in cs}
    check("aucune cause « conflit »", "conflit" not in causes, causes)
    check("le bilan voit des espèces au-delà du top 3",
          len(ch["brut"]["annees"][0]["vivants"]) > 3, ch["brut"]["annees"][0]["vivants"])


if __name__ == "__main__":
    test_logique()
    test_serveur()
    print("ÉCHECS :", ECHECS if ECHECS else "aucun")
    raise SystemExit(1 if ECHECS else 0)
