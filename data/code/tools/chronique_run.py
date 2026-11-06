# SYMBIOSE — tools/chronique_run.py
# Run LONG sans écran + CHRONIQUE DES ESPÈCES (D127, sprint chronique des espèces ③).
#
# But : lancer sur la VM, sans Godot ni Nico, un run de N années sur n'importe quel
# monde ou banc, et lire QUAND chaque espèce disparaît et DE QUOI meurent les plantes.
#
# 📖 Pourquoi passer par le SERVEUR (et pas `engine.tick_semaine()` en direct comme
# `diag_population.py`) ? Parce que la chronique est alimentée par `cmd_step_week`
# (recensement avant le tick, lecture du log après) : en avançant par le MÊME chemin,
# la chronique écrite ici est exactement celle du rapport C (touche C) d'un run PC.
# Aucun comptage dupliqué — on affiche `cmd_perf_report()["chronique"]` tel quel.
# Le snapshot que `cmd_step_week` construit à chaque semaine est jeté : mesuré à
# 6,4 % du temps d'un pas [verger_mur an 1, n=1, VM] → pas de chemin dédié.
#
# Régime HORS-LIGNE, lecture seule : golden INTACT (le golden tourne hors serveur).
#
# Usage (depuis data/code/) :
#   python3 -m tools.chronique_run --config verger_mur --annees 200 [--seed S] [--sortie DIR]
# Sorties : DIR/chronique.txt (le texte du rapport C), DIR/chronique.json (le brut) ;
# progression sur stderr tous les 10 ans (année, plantes vivantes, temps écoulé).

from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

PAS_PROGRESSION = 10      # une ligne stderr tous les 10 ans


def _vivants(engine) -> int:
    return sum(1 for t in engine.game_state["tiles"] for p in t.plants if p.is_alive)


def lancer(config: str, annees: int, seed: int | None, sortie: Path) -> dict:
    """Monte `config` par `SimServer.cmd_init`, avance `annees` × 52 semaines par
    `cmd_step_week`, écrit les deux fichiers et renvoie la chronique du rapport C."""
    from tools.simserver.server import SimServer
    srv = SimServer()
    msg = {"config": config} if seed is None else {"config": config, "seed": seed}
    rep = srv.cmd_init(msg)
    if not rep.get("ok"):
        raise RuntimeError(f"cmd_init a échoué : {rep}")
    t0 = time.perf_counter()
    for semaine in range(1, annees * 52 + 1):
        rep = srv.cmd_step_week({})
        if not rep.get("ok"):
            raise RuntimeError(f"step_week a échoué semaine {semaine} : {rep}")
        if semaine % (52 * PAS_PROGRESSION) == 0:
            print(f"[chronique_run] an {semaine // 52} : {_vivants(srv.engine)} vivants, "
                  f"{(time.perf_counter() - t0) / 60:.1f} min", file=sys.stderr, flush=True)
    chronique = srv.cmd_perf_report({})["chronique"]
    sortie.mkdir(parents=True, exist_ok=True)
    (sortie / "chronique.txt").write_text(chronique["texte"] + "\n", encoding="utf-8")
    with open(sortie / "chronique.json", "w", encoding="utf-8") as f:
        json.dump(chronique["brut"], f, ensure_ascii=False, indent=1)
    return chronique


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run long sans écran + chronique des espèces (disparitions, causes).")
    ap.add_argument("--config", default="smoke",
                    help="monde ou banc monté par le serveur (défaut 'smoke')")
    ap.add_argument("--annees", type=int, default=10, help="durée en années (défaut 10)")
    ap.add_argument("--seed", type=lambda s: int(s, 0), default=None,
                    help="seed global (défaut = celui du serveur)")
    ap.add_argument("--sortie", type=Path, default=Path("."),
                    help="dossier de chronique.txt / chronique.json (défaut '.')")
    args = ap.parse_args()
    chronique = lancer(args.config, args.annees, args.seed, args.sortie)
    print(chronique["texte"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
