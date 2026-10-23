# SYMBIOSE — tools/profile_phases.py (sprint FLUIDITÉ AN 2, tronçon ②)
# PROFIL PAR PHASE DU TICK : quelle part de `tick_semaine` part dans chacune des
# fonctions qu'il appelle DIRECTEMENT (tick_populations, apply_disturbances,
# tick_light…). Complète `profile_monde.py` (temps PROPRE par fonction) : ici on
# lit le temps CUMULÉ de l'appel depuis le tick — la « phase » vue d'en haut.
#
# 📖 Pédagogie : cProfile garde, pour chaque fonction f, un dictionnaire de ses
# appelants → (ncalls, primcalls, tottime, cumtime). Prendre l'entrée dont
# l'appelant est `tick_semaine` donne le coût cumulé de f QUAND le tick l'appelle,
# sans compter les appels venant d'ailleurs. Lecture seule : le moteur n'est pas
# instrumenté, le golden ne peut pas bouger.
#
# Usage (depuis data/code/) :
#   python3 -m tools.profile_phases [--week N] [--seed S] [--profil K] [--top T]

from __future__ import annotations
import argparse
import cProfile
import pstats

from tools.profile_monde import _build_engine_full, _grandir, _compo_monde


def phases(stats: pstats.Stats) -> tuple[float, list[tuple[str, float, int]]]:
    """(cumul total de tick_semaine, [(nom, cumul depuis le tick, appels)])
    triés par cumul décroissant."""
    total = 0.0
    lignes = []
    for f, (_cc, _nc, _tt, ct, appelants) in stats.stats.items():
        if f[2] == "tick_semaine":
            total += ct
        for appelant, val in appelants.items():
            if appelant[2] == "tick_semaine":
                lignes.append((f"{f[2]} ({f[0].rsplit('/', 1)[-1]}:{f[1]})", val[3], val[0]))
    lignes.sort(key=lambda l: -l[1])
    return total, lignes


def main() -> int:
    ap = argparse.ArgumentParser(description="Profil par phase du tick Symbiose.")
    ap.add_argument("--week", type=int, default=130, help="semaine cible (défaut 130, an 2)")
    ap.add_argument("--seed", type=int, default=1521550718)
    ap.add_argument("--profil", type=int, default=3, help="ticks sous cProfile")
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()

    engine = _build_engine_full(args.seed)
    _grandir(engine, args.week)
    print(f"monde semaine {engine.week} : {_compo_monde(engine)['plantes']} plantes")
    prof = cProfile.Profile()
    prof.enable()
    for _ in range(args.profil):
        engine.tick_semaine()
    prof.disable()
    total, lignes = phases(pstats.Stats(prof))
    print(f"tick_semaine cumulé (cProfile, {args.profil} ticks) : {total * 1000:.0f} ms")
    for nom, ct, n in lignes[:args.top]:
        print(f"  {ct / total * 100:5.1f} %  {ct * 1000:8.0f} ms  ×{n:<6} {nom}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
