"""
SYMBIOSE — tools/banc_calibration.py
Banc de mesure de CALIBRATION du sol vivant (sprint CALIBRATION RÉALISTE, P1).

But : lire, année par année, les grandeurs qui pilotent la lisibilité et le
fonctionnement du sol — pour caler les normalisateurs d'échelle (microbiome,
om_active…) sur leur plage d'OPÉRATION réelle plutôt que sur leur saturation.

Deux mondes, MÊMES semis fondateurs (miroir de `tests/test_golden.py:build_world`,
seed 42, maison centrée) mais deux résolutions de tuile :
  • DENSE  (2 tuiles 6×8)   → canopée fermée, ombrage fort, sol à l'ombre.
  • LÂCHE  (2 tuiles 12×16) → même nombre de plantes étalées → sol plus éclairé.
Le contraste isole ce qui vient de la DENSITÉ (lumière) de ce qui vient de la
CALIBRATION.

Grandeurs mesurées (tuile T0, terre) :
  vivantes · plant.vitalite moy/médiane · eco.vitalite (métrique SOL) ·
  microbiome moy · om_active moy/max · om_stable moy/max · lumiere_moy.

Lancement (depuis data/code/) :
  python3 -m tools.banc_calibration           # 10 ans dense + 10 ans lâche
  python3 -m tools.banc_calibration 20        # 20 ans (⚠ NE JAMAIS 500 ans, interdit)
"""

import sys
import statistics

from world import Tile, House
from sim.engine import Engine
from fields import init_eco
from plants import (Tomato, Basil, Bean, Sunflower, Pepper, Yarrow, Phacelia,
                    Clover, AppleTree)
from sim.seeds import semer_fondateur

# Seed du terrain — IDENTIQUE au golden (déterminisme, philo #3).
SEED = 42
SOILS = ["terre", "argile"]
# Offsets monde vs maison centrée — mêmes que le golden (T0 nord ombragée, T1 sud).
TILE_ORIGINS = {0: (700.0, 0.0), 1: (700.0, 1500.0)}


def build_world(dense: bool = True):
    """Miroir de `tests/test_golden.py:build_world`, à résolution variable.
    dense=True → tuiles 6×8 (smoke) ; dense=False → 12×16 (mêmes plantes, étalées)."""
    rows, cols = (6, 8) if dense else (12, 16)
    tiles, ecos = [], {}
    for i, soil in enumerate(SOILS):
        tid = f"T{i}"
        ox, oy = TILE_ORIGINS[i]
        tile = Tile(tile_id=tid, soil_type=soil, origin_x_cm=ox, origin_y_cm=oy)
        if soil == "argile":
            eco = init_eco(tid, rows, cols, humidite=2.0, fertilite=1.2,
                           microbiome=0.3, soil_type=soil, heterogene=True)
        else:
            eco = init_eco(tid, rows, cols, humidite=1.5, fertilite=1.0,
                           microbiome=0.3, soil_type=soil, heterogene=True)
        semer_fondateur(tile, Tomato,    2, 2, SEED)
        semer_fondateur(tile, Basil,     2, 4, SEED)
        semer_fondateur(tile, Bean,      4, 2, SEED)
        semer_fondateur(tile, Sunflower, 0, 1, SEED)
        semer_fondateur(tile, Pepper,    4, 6, SEED)
        if i % 2 == 0:
            semer_fondateur(tile, Yarrow,   3, 5, SEED)
            semer_fondateur(tile, Phacelia, 1, 6, SEED)
            semer_fondateur(tile, Clover,   5, 4, SEED)
        tiles.append(tile)
        ecos[tid] = eco
    semer_fondateur(tiles[0], AppleTree, 0, 7, SEED)
    return tiles, ecos


def _field_max(field) -> float:
    """Max sur les plots d'un GridField (pas de méthode dédiée côté champ)."""
    return max((v for row in field.data for v in row), default=0.0)


def run(dense: bool, years: int) -> None:
    tiles, ecos = build_world(dense)
    game_state = {"tiles": tiles, "eco": ecos, "scores": {},
                  "current_player": "joueur_1", "week": 1, "log": [],
                  "house": House()}
    engine = Engine(game_state)
    label = "DENSE (2×6×8)" if dense else "LÂCHE (2×12×16)"
    print(f"\n===== {label} — {years} ans, seed {SEED} =====")
    print(f"{'an':>3} | {'viv':>3} | {'p.vit moy':>9} | {'p.vit med':>9} | "
          f"{'sol.vit':>7} | {'micro':>6} | {'omA moy':>7} | {'omA max':>7} | "
          f"{'omS moy':>7} | {'omS max':>7} | {'lum':>6}")
    for y in range(1, years + 1):
        for _ in range(52):
            engine.tick_semaine()
            game_state["log"].clear()   # borne la mémoire
        vits = [p.vitalite for t in tiles for p in t.plants if p.is_alive]
        n = len(vits)
        moy = statistics.mean(vits) if vits else 0.0
        med = statistics.median(vits) if vits else 0.0
        eco0 = ecos["T0"]
        s0 = eco0.summary()
        print(f"{y:>3} | {n:>3} | {moy:>9.3f} | {med:>9.3f} | "
              f"{s0['vitalite']:>7.3f} | {s0['microbiome']:>6.3f} | "
              f"{s0['om_active']:>7.3f} | {_field_max(eco0.om_active):>7.3f} | "
              f"{s0['om_stable']:>7.3f} | {_field_max(eco0.om_stable):>7.3f} | "
              f"{s0['lumiere_moy']:>6.3f}")


def main() -> int:
    years = 10
    if len(sys.argv) > 1:
        years = int(sys.argv[1])
    if years > 100:
        print("⚠ banc bridé à 100 ans (les runs longs sont interdits, cf. 00_etat.md)")
        years = 100
    run(dense=True, years=years)
    run(dense=False, years=years)
    print("\nAncres de lecture (sol.vit) : jeune/pauvre ~0.1-0.2, mûr/riche ~0.5+, "
          "dégradé ~0.05.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
