"""
SYMBIOSE — tests/test_scatter_lumiere_recue.py
VERROU (sprint perf run éternel, tronçon ②) : la boucle « lumière REÇUE par
plante » de `light.compute` est passée d'un GATHER (chaque échantillon × chaque
émetteur plus haut, via `ObstacleIndex.covering` dimensionné par l'ombre la plus
longue de la tuile) à un SCATTER (chaque émetteur ne visite que les échantillons
de la bbox de sa capsule, via `ReceiverIndex`).

Un échantillon hors de la bbox d'une capsule renvoie FORCÉMENT False dans
`_point_in_capsule` → l'élaguer ne change AUCUN résultat. Ce test reconstruit
l'ANCIENNE boucle gather, ligne à ligne, et compare son `received` (lumière reçue
par plante) à celui produit par `compute` (scatter) en ÉGALITÉ BIT-À-BIT (`==`
sur les floats, pas de tolérance). Sans ce vert, le scatter n'est pas soldé : un
off-by-one sur l'indexation échantillon→bbox dériverait le golden EN SILENCE.

Scénarios couverts : monde smoke réel grandi (plantes + squelettes éventuels),
les 4 saisons, avec ET sans maison (ombre + albédo).

Lancement (depuis data/code/) : python3 -m tests.test_scatter_lumiere_recue
"""

import sys

from fields.light import (LightField, LIGHT_FLOOR, SILHOUETTE_SECHE,
                          SHADING_POWER_MIN, CANOPY_SAMPLE_FRAC,
                          _point_in_capsule, _point_in_swept_rect)
from fields.light_index import ObstacleIndex
from world import House
from tests.test_golden import build_world, TILE_ORIGINS
from sim.engine import Engine


def _infos(plants, saison):
    """Réplique EXACTE de la construction `infos` de light.compute
    (plantes vivantes + squelettes secs debout), dans le même ordre.
    Garde la plante en tête de tuple (id(p) = clé de `received`)."""
    alive = [p for p in plants if p.is_alive]
    infos = []
    for p in alive:
        cls = p.plant_class
        infos.append((p, p.x_cm, p.y_cm, p.current_height,
                      cls.canopy_radius_at(p), cls.foliage_density_at(p, saison)))
    for p in plants:
        if getattr(p, "morte", False) and getattr(p, "stade_mort", None) == "seche":
            cls = p.plant_class
            infos.append((p, p.x_cm, p.y_cm, p.current_height,
                          cls.canopy_radius_at(p), SILHOUETTE_SECHE))
    return infos


def _gather_received(lf, infos, slices, house, origin):
    """ANCIENNE boucle lumière-reçue (gather), copiée ligne à ligne depuis la
    version pré-scatter de light.compute. Renvoie un dict {id(p): valeur}."""
    ox, oy = origin
    hx0 = hy0 = hx1 = hy1 = h_height = 0.0
    if house is not None:
        hx0, hy0, hx1, hy1 = house.footprint_bounds
        h_height = house.height_cm
    receivers = infos
    emitters = [t for t in infos if t[3] * t[4] * t[5] >= SHADING_POWER_MIN]
    total_w = sum(w for _, _, _, w in slices)
    order = sorted(emitters, key=lambda t: t[3], reverse=True)
    index = ObstacleIndex(order)
    out = {}
    for p, px, py, ph, pr, pd in receivers:
        d = pr * CANOPY_SAMPLE_FRAC
        samples = ((px, py), (px + d, py), (px - d, py), (px, py + d), (px, py - d))
        acc = 0.0
        for sdx, sdy, inv_tan, w in slices:
            h_len = h_height * inv_tan
            max_len = index.max_height * inv_tan
            att_sum = 0.0
            for sx, sy in samples:
                if house is not None and _point_in_swept_rect(
                        sx + ox, sy + oy, hx0, hy0, hx1, hy1, sdx, sdy, h_len):
                    continue
                cands = index.covering(sx, sy, max_len)
                cands.sort(key=lambda rc: rc[0])
                att = 1.0
                for _rank, (q, qx, qy, qh, qr, qd) in cands:
                    if qh <= ph:
                        continue
                    if qd <= 0.0:
                        continue
                    if _point_in_capsule(sx, sy, qx, qy, sdx, sdy, qh * inv_tan, qr):
                        att *= (1.0 - qd)
                att_sum += att
            light_slice = max(LIGHT_FLOOR, att_sum / len(samples))
            acc += light_slice * w
        out[id(p)] = acc / total_w
    return out


def _compare(label, lf, plants, saison, house, origin):
    """Calcule le `received` scatter (compute) et le `received` gather, exige
    l'identité bit-à-bit. Retourne (ok, nb_recepteurs)."""
    infos = _infos(plants, saison)
    slices = lf._sun_slices(saison)
    lf.compute(plants, saison, house=house, tile_origin=origin)
    scatter = dict(lf.received)
    gather = _gather_received(lf, infos, slices, house, origin)
    ok = True
    if set(scatter.keys()) != set(gather.keys()):
        print(f"  ✗ {label} : clés différentes scatter={len(scatter)} gather={len(gather)}")
        return False, len(gather)
    for ref, gv in gather.items():
        sv = scatter[ref]
        if sv != gv:                            # ÉGALITÉ STRICTE (pas de tolérance)
            ok = False
            print(f"  ✗ {label} [{ref}] scatter={sv!r} != gather={gv!r}")
            return ok, len(gather)
    print(f"  ✓ {label} : {len(gather)} récepteurs, saison={saison} → identité bit-à-bit")
    return ok, len(gather)


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
            ok, _ = _compare(f"T{tile.tile_id}+maison", lf, tile.plants,
                             saison, house, origin)
            all_ok = all_ok and ok
    # 2. Même monde SANS maison (chemin historique : house=None).
    for tile in tiles:
        lf = ecos[tile.tile_id].lumiere
        for saison in seasons:
            ok, _ = _compare(f"T{tile.tile_id}+sans-maison", lf, tile.plants,
                             saison, None, (0.0, 0.0))
            all_ok = all_ok and ok

    if all_ok:
        print("\n[scatter-reçue] PASS — lumière reçue scatter == gather bit-à-bit")
        return 0
    print("\n[scatter-reçue] FAIL — divergence scatter/gather (RÉGRESSION, ne pas figer)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
