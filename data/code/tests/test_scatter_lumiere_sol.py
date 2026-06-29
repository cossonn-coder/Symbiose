"""
SYMBIOSE — tests/test_scatter_lumiere_sol.py
VERROU D32 (sprint vent, tronçon ⓪) : la boucle lumière-sol de `light.compute`
est passée d'un GATHER (chaque plot × chaque plante, aucun élagage) à un SCATTER
(chaque ombre ne visite que les plots de sa bounding-box de capsule).

Un plot hors de la bbox d'une capsule renvoie FORCÉMENT False dans
`_point_in_capsule` → l'élaguer ne change AUCUN résultat. Ce test reconstruit
l'ANCIENNE boucle gather, ligne à ligne, et compare sa grille lumière-sol à
celle produite par `compute` (scatter) en ÉGALITÉ BIT-À-BIT (`==` sur les floats,
pas de tolérance). Sans ce vert, D32 n'est pas soldée : un off-by-one sur
l'indexation plot→bbox dériverait le golden EN SILENCE.

Scénarios couverts : monde smoke réel grandi (plantes + squelettes éventuels),
les 4 saisons, avec ET sans maison (ombre + albédo).

Lancement (depuis data/code/) : python3 -m tests.test_scatter_lumiere_sol
"""

import sys

from constants import PLOT_CM
from fields.light import (LightField, LIGHT_FLOOR, SILHOUETTE_SECHE,
                          _point_in_capsule, _point_in_swept_rect,
                          _wall_albedo_bonus, WALL_ALBEDO_RADIUS_CM)
from world import House
from tests.test_golden import build_world, TILE_ORIGINS
from sim.engine import Engine


def _infos(plants, saison):
    """Réplique EXACTE de la construction `infos` de light.compute
    (plantes vivantes + squelettes secs debout), dans le même ordre."""
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
    return infos


def _gather_ground(lf, infos, slices, house, origin):
    """ANCIENNE boucle lumière-sol (gather), copiée ligne à ligne depuis la
    version pré-D32 de light.compute (L266-291). Renvoie la grille rows×cols."""
    ox, oy = origin
    hx0 = hy0 = hx1 = hy1 = h_height = wall_albedo = 0.0
    if house is not None:
        hx0, hy0, hx1, hy1 = house.footprint_bounds
        h_height = house.height_cm
        wall_albedo = house.wall_albedo
    total_w = sum(w for _, _, _, w in slices)
    out = [[0.0] * lf.cols for _ in range(lf.rows)]
    for r in range(lf.rows):
        cy = r * PLOT_CM + PLOT_CM / 2
        wy = cy + oy
        for c in range(lf.cols):
            cx = c * PLOT_CM + PLOT_CM / 2
            wx = cx + ox
            acc = 0.0
            for sdx, sdy, inv_tan, w in slices:
                if house is not None and _point_in_swept_rect(
                        wx, wy, hx0, hy0, hx1, hy1, sdx, sdy, h_height * inv_tan):
                    att = 0.0
                else:
                    att = 1.0
                    for qx, qy, qh, qr, qd in infos:
                        if qd <= 0.0:
                            continue
                        if _point_in_capsule(cx, cy, qx, qy, sdx, sdy, qh * inv_tan, qr):
                            att *= (1.0 - qd)
                if house is not None and wall_albedo > 0.0:
                    att += _wall_albedo_bonus(wx, wy, hx0, hy0, hx1, hy1,
                                              wall_albedo, WALL_ALBEDO_RADIUS_CM,
                                              -sdx, -sdy)
                acc += att * w
            out[r][c] = min(1.0, max(LIGHT_FLOOR, acc / total_w))
    return out


def _compare(label, lf, plants, saison, house, origin):
    """Calcule la grille scatter (compute) et la grille gather, exige l'identité
    bit-à-bit. Retourne (ok, nb_plots, nb_ombres)."""
    infos = _infos(plants, saison)
    slices = lf._sun_slices(saison)
    lf.compute(plants, saison, house=house, tile_origin=origin)
    scatter = [row[:] for row in lf.data]
    gather = _gather_ground(lf, infos, slices, house, origin)
    ok = True
    for r in range(lf.rows):
        for c in range(lf.cols):
            if scatter[r][c] != gather[r][c]:   # ÉGALITÉ STRICTE (pas de tolérance)
                ok = False
                print(f"  ✗ {label} [{r},{c}] scatter={scatter[r][c]!r} "
                      f"!= gather={gather[r][c]!r}")
                return ok, lf.rows * lf.cols, len(infos)
    print(f"  ✓ {label} : {lf.rows*lf.cols} plots × {len(infos)} ombres, "
          f"saison={saison} → identité bit-à-bit")
    return ok, lf.rows * lf.cols, len(infos)


def main():
    tiles, ecos = build_world()
    game_state = {"tiles": tiles, "eco": ecos, "scores": {},
                  "current_player": "joueur_1", "week": 1, "log": [],
                  "house": House()}
    engine = Engine(game_state)
    for _ in range(60):                          # faire pousser des ombres réelles
        engine.tick_semaine()
    house = game_state["house"]

    all_ok = True
    seasons = ("printemps", "ete", "automne", "hiver")
    # 1. Monde smoke grandi, par tuile, 4 saisons, AVEC maison (ombre + albédo).
    for tile in tiles:
        lf = ecos[tile.tile_id].lumiere
        origin = TILE_ORIGINS.get(tile.tile_id, (0.0, 0.0))
        for saison in seasons:
            ok, _, _ = _compare(f"T{tile.tile_id}+maison", lf, tile.plants,
                                saison, house, origin)
            all_ok = all_ok and ok
    # 2. Même monde SANS maison (chemin historique : house=None).
    for tile in tiles:
        lf = ecos[tile.tile_id].lumiere
        for saison in seasons:
            ok, _, _ = _compare(f"T{tile.tile_id}+sans-maison", lf, tile.plants,
                                saison, None, (0.0, 0.0))
            all_ok = all_ok and ok

    if all_ok:
        print("\n[scatter] PASS — lumière-sol scatter == gather bit-à-bit (D32 soldée)")
        return 0
    print("\n[scatter] FAIL — divergence scatter/gather (RÉGRESSION, ne pas figer)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
