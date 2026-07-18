# SYMBIOSE — tools/bancs/automate_demo.py
# Banc de démonstration HEADLESS du jardinier automate (tronçon ①). Monte un petit
# monde via le SERVEUR (même fabrique que le F5, cf. diag_population), branche un
# JardinierAutomate(LIBRE) ENTRE deux ticks, et imprime le journal minimal.
#
# EXTERNE au moteur : `engine.tick_semaine()` puis `automate.jouer_tick(engine)` —
# l'automate n'est jamais dans le tick (invariant H2) → golden intact. On ne
# simule QU'UNE poignée d'années (jamais 500 ans).
#
# Usage (depuis data/code/) :
#   python3 -m tools.bancs.automate_demo [--weeks N] [--config full|propre] [--seed S]

from __future__ import annotations
import argparse

from tools.jardinier_auto import JardinierAutomate, LIBRE
from tools.jardinier_auto.trace import journal


def _build_engine(config: str, seed: int):
    """Monte le monde `config` via `SimServer.cmd_init` (fabrique du F5) et renvoie
    son Engine, prêt à ticker (patron repris de diag_population.py)."""
    from tools.simserver.server import SimServer
    srv = SimServer()
    rep = srv.cmd_init({"config": config, "seed": seed})
    if not rep.get("ok"):
        raise RuntimeError(f"cmd_init a échoué : {rep}")
    return srv.engine


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Démo headless du jardinier automate (tronçon ①).")
    ap.add_argument("--weeks", type=int, default=104,
                    help="nombre de semaines simulées (défaut 104 ≈ 2 ans)")
    ap.add_argument("--config", default="full", choices=["full", "propre"],
                    help="preset de monde (défaut 'full')")
    ap.add_argument("--seed", type=lambda s: int(s, 0), default=0x5AB1057E,
                    help="seed global déterministe")
    args = ap.parse_args()

    print(f"=== Démo jardinier automate — profil=LIBRE, config={args.config}, "
          f"seed={args.seed:#x}, weeks={args.weeks} ===")
    engine = _build_engine(args.config, args.seed)
    automate = JardinierAutomate(LIBRE)

    for _ in range(args.weeks):
        engine.tick_semaine()
        automate.jouer_tick(engine)

    jr = journal(engine.game_state)
    print(f"  {len(jr)} gestes consignés sur {args.weeks} semaines.")
    # Répartition par (geste, résultat) — vue synthétique déterministe.
    compo: dict[tuple, int] = {}
    for e in jr:
        cle = (e["geste"], e["resultat"])
        compo[cle] = compo.get(cle, 0) + 1
    for (geste, res), n in sorted(compo.items()):
        print(f"    {geste:<10} {res:<8} ×{n}")
    print("  dernières entrées :")
    for e in jr[-8:]:
        print(f"    s{e['semaine']:>3} {e['tile_id']:<10} {e['facteur_limitant']:<11} "
              f"{e['geste']:<9} {e['resultat']:<8} {e['cible']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
