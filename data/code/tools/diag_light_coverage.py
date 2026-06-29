# SYMBIOSE — tools/diag_light_coverage.py
# Diagnostic LECTURE SEULE (pré-sprint VENT, question Nico « peut-on réduire le
# coût de LightField ? »). Mesure, sur le monde déterministe réel (`build_world`)
# grandi N semaines, le gain attendu d'un passage GATHER → SCATTER de la boucle
# lumière-sol de `light.compute` (§ ground-light, light.py L266-291).
#
# La boucle actuelle teste CHAQUE plot contre CHAQUE plante (gather, aucun élagage
# spatial). L'ombre d'une plante est une capsule de bounding-box minuscule devant
# la grille : un plot hors de cette bbox retourne forcément False dans
# `_point_in_capsule`. L'élaguer est donc BIT-IDENTIQUE (golden préservé).
#
# On chiffre : tests gather (plots×tranches×plantes) vs tests scatter (somme des
# plots réellement dans la bbox de chaque capsule). Ratio = accélération attendue
# de cette boucle. On imprime aussi la couverture d'ombre réelle (contexte).
#
# Usage (depuis data/code/) : python3 -m tools.diag_light_coverage [semaines]

import sys

from constants import PLOT_CM
from fields.light import _point_in_capsule, SILHOUETTE_SECHE
from sim.engine import Engine
from sim.engine.calendrier import saison_de
from tests.test_golden import build_world
from world.building import House


def _infos_for(eco, plants, saison):
    """Réplique la construction `infos` de light.compute (plantes vivantes +
    squelettes secs debout) et les tranches solaires cachées de la saison."""
    alive = [p for p in plants if p.is_alive]
    infos = []
    for p in alive:
        cls = p.plant_class
        infos.append((p.x_cm, p.y_cm, p.current_height,
                      cls.canopy_radius_at(p), cls.foliage_density_at(p, saison)))
    for p in plants:
        if getattr(p, "morte", False) and getattr(p, "stade_mort", None) == "seche":
            cls = p.plant_class
            infos.append((p.x_cm, p.y_cm, p.current_height,
                          cls.canopy_radius_at(p), SILHOUETTE_SECHE))
    slices = eco.lumiere._sun_slices(saison)
    return infos, slices


def _measure_tile(eco, plants, saison):
    rows, cols = eco.lumiere.rows, eco.lumiere.cols
    infos, slices = _infos_for(eco, plants, saison)
    n_plots = rows * cols

    gather_tests = 0          # plots × tranches × plantes (boucle actuelle)
    scatter_tests = 0         # somme des plots dans la bbox de chaque capsule
    covered = [[False] * cols for _ in range(rows)]   # plot sous ≥1 ombre réelle

    for sdx, sdy, inv_tan, _w in slices:
        gather_tests += n_plots * len(infos)
        for qx, qy, qh, qr, qd in infos:
            if qd <= 0.0:
                continue
            length = qh * inv_tan
            bx, by = qx + sdx * length, qy + sdy * length
            xmin, xmax = min(qx, bx) - qr, max(qx, bx) + qr
            ymin, ymax = min(qy, by) - qr, max(qy, by) + qr
            c0 = max(0, int(xmin // PLOT_CM)); c1 = min(cols - 1, int(xmax // PLOT_CM))
            r0 = max(0, int(ymin // PLOT_CM)); r1 = min(rows - 1, int(ymax // PLOT_CM))
            for r in range(r0, r1 + 1):
                cy = r * PLOT_CM + PLOT_CM / 2
                for c in range(c0, c1 + 1):
                    cx = c * PLOT_CM + PLOT_CM / 2
                    scatter_tests += 1
                    if _point_in_capsule(cx, cy, qx, qy, sdx, sdy, length, qr):
                        covered[r][c] = True

    n_covered = sum(1 for row in covered for v in row if v)
    return n_plots, len(infos), len(slices), gather_tests, scatter_tests, n_covered


def main():
    weeks = int(sys.argv[1]) if len(sys.argv) > 1 else 156
    tiles, ecos = build_world()
    game_state = {"tiles": tiles, "eco": ecos, "scores": {},
                  "current_player": "joueur_1", "week": 1, "log": [],
                  "house": House()}
    engine = Engine(game_state)
    for _ in range(weeks):
        engine.tick_semaine()
    saison = saison_de(((weeks - 1) % 52) + 1)

    print(f"=== Couverture d'ombre LightField — {weeks} semaines, saison={saison} ===")
    tot_g = tot_s = tot_p = tot_cov = 0
    for tile in tiles:
        eco = ecos[tile.tile_id]
        plants = tile.plants
        np_, ninf, nsl, g, s, cov = _measure_tile(eco, plants, saison)
        tot_g += g; tot_s += s; tot_p += np_; tot_cov += cov
        ratio = g / s if s else float("inf")
        print(f"  {tile.tile_id:>6s}: {np_:4d} plots, {ninf:2d} ombres, {nsl} tranches | "
              f"couverts {cov:4d} ({100*cov/np_:4.1f}%) | "
              f"gather {g:7d} vs scatter {s:6d} tests → ×{ratio:4.1f}")
    ratio = tot_g / tot_s if tot_s else float("inf")
    print(f"  TOTAL : {tot_p} plots, couverts {tot_cov} ({100*tot_cov/tot_p:.1f}%) | "
          f"gather {tot_g} vs scatter {tot_s} → accélération boucle sol ×{ratio:.1f}")


if __name__ == "__main__":
    main()
