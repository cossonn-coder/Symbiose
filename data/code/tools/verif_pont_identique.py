# SYMBIOSE — tools/verif_pont_identique.py (sprint FLUIDITÉ PC PARTAGE, tronçon ①)
# EMPREINTE DU MONDE SERVI, semaine par semaine : prouve qu'une optimisation du pont
# (réglage du ramasse-miettes, mémoïsation de `_snapshot`) ne change RIEN à ce que
# la vue reçoit, ni à la simulation elle-même.
#
# Par semaine, une ligne : `semaine  sha_delta  sha_complet  populations`
#   - sha_delta   : SHA-256 de la réponse `step_week {"delta": true}` (format du F5),
#                   sérialisée EXACTEMENT comme le pont (sort_keys, séparateurs compacts),
#                   hors bloc `perf` (durée du tick, pic RSS : mesures d'instrument) ;
#   - sha_complet : SHA-256 de `snapshot {}` (format complet historique) juste après ;
#   - populations : plantes vivantes par espèce (lisible à l'œil si ça diverge).
# On lance l'outil deux fois (deux PROCESSUS séparés : avant/après un changement de
# code, ou réglage GC on/off), puis `diff` des deux fichiers. Identiques = prouvé.
#
# 📖 Pédagogie (côté embarqué) : c'est le test « golden » d'un firmware qu'on
# optimise — on capture la trame de sortie bit à bit avant, on recapture après,
# et on compare octet par octet. Le golden du moteur (`tests/test_golden.py`)
# tourne EN PROCESSUS sans le serveur : il ne voit ni le pont ni le réglage GC.
# Pourquoi deux processus ? Le ramasse-miettes change les ADRESSES mémoire des
# objets (`id()`), et `sim/grimpe.py` départage deux hôtes équidistants par `id()`.
# Seul un vrai second processus fait varier les adresses comme en jeu.
#
# Usage (depuis data/code/) :
#   python3 -m tools.verif_pont_identique --sortie F [--semaines W] [--seed S] [--gc on|off]
#   puis : diff F_avant F_apres

from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter


def _sans_perf(rep: dict) -> dict:
    """La réponse sans le bloc `perf` du snapshot (durée du tick, pic RSS : des
    mesures d'instrument, différentes à chaque processus par nature)."""
    snap = rep.get("snapshot")
    if isinstance(snap, dict) and "perf" in snap:
        rep = dict(rep, snapshot={k: v for k, v in snap.items() if k != "perf"})
    return rep


def _sha(obj) -> str:
    texte = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(texte.encode()).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser(description="Empreinte semaine par semaine du pont.")
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--semaines", type=int, default=100)
    ap.add_argument("--seed", type=int, default=1521550718)
    ap.add_argument("--gc", choices=("on", "off"), default="on",
                    help="réglage du ramasse-miettes du serveur (gc_pont)")
    a = ap.parse_args()

    from tools.simserver import gc_pont
    gc_pont.ACTIF = a.gc == "on"
    from tools.simserver.server import SimServer
    srv = SimServer()
    rep = srv.cmd_init({"config": "full", "seed": a.seed})
    if not rep.get("ok"):
        raise RuntimeError(f"cmd_init a échoué : {rep}")
    with open(a.sortie, "w") as out:
        out.write(f"# init {_sha(rep)} gc={a.gc}\n")
        for _ in range(a.semaines):
            rep = srv.cmd_step_week({"delta": True})
            if not rep.get("ok"):
                raise RuntimeError(f"step_week a échoué : {rep}")
            complet = srv.cmd_snapshot({})
            gs = srv.engine.game_state
            pops = Counter(p.plant_class.__name__ for t in gs["tiles"]
                           for p in t.plants if p.is_alive)
            out.write(f"{gs['week'] - 1} {_sha(_sans_perf(rep))} {_sha(_sans_perf(complet))} "
                      f"{json.dumps(sorted(pops.items()), separators=(',', ':'))}\n")
            out.flush()
    print(f"{a.semaines} semaines écrites dans {a.sortie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
