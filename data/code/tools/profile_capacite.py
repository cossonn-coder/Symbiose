# SYMBIOSE — tools/profile_capacite.py
# Instrument de CALIBRAGE du tronçon ③ « capacité de charge émergente » (sprint
# perf run éternel). But : observer la trajectoire N(t) PAR TUILE sur plusieurs
# années et vérifier qu'elle SE STABILISE (plateau) au lieu de croître sans fin —
# le signe que les freins écologiques (couverture→germination + self-thinning) sont
# calibrés à l'équilibre recrutement=mortalité. Le plateau VARIE par tuile
# (fertilité/lumière) → philo #7 préservée : c'est ce qu'on lit ici, une colonne
# par tuile, PAS une densité cible arbitraire.
#
# LECTURE SEULE, DÉTERMINISTE — réutilise `build_world_full` (fabrique du serveur)
# tronquée à n_tiles, tickée à l'identique du serveur (log purgé chaque semaine).
# Ne touche ni le tick ni le golden.
#
# Usage (depuis data/code/) : python3 -m tools.profile_capacite [annees] [tuiles]
#   annees : nombre d'années simulées (défaut 15 — assez pour voir le plateau)
#   tuiles : nombre de tuiles du monde full à garder (défaut 3 — tourne en ~3-4 min)

import sys
import time

from main import build_world_full
from sim.engine import Engine


def _build_engine(n_tiles: int):
    tiles, ecos, _aux, house = build_world_full()
    tiles = tiles[:n_tiles]
    ecos = {t.tile_id: ecos[t.tile_id] for t in tiles}
    game_state = {
        "tiles": tiles, "eco": ecos, "scores": {},
        "current_player": "joueur_1", "week": 1, "log": [],
        "house": house, "seed": 0x5AB1057E, "journal": {},
    }
    return Engine(game_state), tiles, ecos


def _n_par_tuile(tiles) -> dict:
    """N plantes VIVANTES par tuile (l'observable du plateau, #7)."""
    return {t.tile_id: sum(1 for p in t.plants if getattr(p, "is_alive", False))
            for t in tiles}


def main():
    annees = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    n_tiles = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    engine, tiles, ecos = _build_engine(n_tiles)
    gs = engine.game_state
    ids = [t.tile_id for t in tiles]
    n_plots = sum(eco.humidite.rows * eco.humidite.cols for eco in ecos.values())

    print(f"=== Capacité de charge — {n_tiles} tuiles, {n_plots} plots, {annees} ans ===")
    entete = f"{'an':>4s} " + " ".join(f"{i:>6s}" for i in ids) + f" {'TOTAL':>7s}"
    print(entete)

    def _ligne(an, dt=None):
        npt = _n_par_tuile(tiles)
        total = sum(npt.values())
        s = f"{an:>4d} " + " ".join(f"{npt[i]:>6d}" for i in ids) + f" {total:>7d}"
        if dt is not None:
            s += f"   [{dt:6.0f}s]"
        print(s)
        sys.stdout.flush()
        return npt

    t0 = time.time()
    hist = [_ligne(0)]
    for annee in range(1, annees + 1):
        for _ in range(52):
            engine.tick_semaine()
            gs["log"].clear()
        hist.append(_ligne(annee, time.time() - t0))

    # Diagnostic PLATEAU : compare les 3 dernières années. Plateau si la variation
    # relative du total est faible (< 8 %) ET non monotone-croissante forte.
    if len(hist) >= 4:
        derniers = [sum(h.values()) for h in hist[-4:]]
        amp = max(derniers) - min(derniers)
        base = max(1, sum(derniers) / len(derniers))
        print(f"\n=== Diagnostic plateau (4 dernières années) ===")
        print(f"  Totaux : {derniers}  amplitude={amp}  ({100*amp/base:.1f}% de la moyenne)")
        croissance = derniers[-1] - derniers[0]
        if amp / base < 0.10 and abs(croissance) / base < 0.10:
            print("  ==> PLATEAU : N stabilisé (recrutement ≈ mortalité).")
        else:
            print(f"  ==> PAS de plateau : dérive {croissance:+d} sur 3 ans "
                  f"→ resserrer les vis A/B.")


if __name__ == "__main__":
    main()
