"""
SYMBIOSE — tests/test_lod_ombre.py
VERROU D67 (sprint perf « LOD des émetteurs d'ombre », tronçon ①).

Le LOD asymétrique de `fields/light.py:LightField.compute` découple RÉCEPTEURS
(toutes les plantes reçoivent toujours la lumière) et ÉMETTEURS (seules celles
dont le POUVOIR OMBRAGEANT — hauteur × rayon canopée × densité — atteint
`SHADING_POWER_MIN` projettent une ombre). Deux garanties à verrouiller :

  1. INVARIANT DORMANT (D3) — à `SHADING_POWER_MIN = 0.0` (défaut), `emitters ==
     infos` dans l'ordre exact → lumière reçue ET lumière-sol BIT-IDENTIQUES à un
     seuil MINUSCULE (qui ne coupe personne) → golden intact garanti localement.
  2. MÉCANISME ACTIF — à seuil ÉLEVÉ (coupe les semis), `emitters < receivers`
     ET la lumière reçue/sol des petits récepteurs AUGMENTE (ombre voisine
     retirée) → valeurs DIFFÉRENTES → le LOD agit réellement.

On monkeypatche `light.SHADING_POWER_MIN` (global de module relu à chaque
`compute`) et on le RESTAURE en fin de test (pas de fuite d'état).

Scène = le monde smoke réel grandi 30 semaines (déterministe, spread de pouvoir
de ~20 pour un semis de trèfle à ~9000 pour un tournesol mûr).

Lancement (depuis data/code/) : python3 -m tests.test_lod_ombre
"""

import sys

from fields import light
from world import House
from tests.test_golden import build_world, TILE_ORIGINS
from sim.engine import Engine


def _scene():
    """Monde smoke grandi 30 semaines : plantes réelles de tailles très variées."""
    tiles, ecos = build_world()
    gs = {"tiles": tiles, "eco": ecos, "scores": {}, "current_player": "j",
          "week": 1, "log": [], "house": House()}
    engine = Engine(gs)
    for _ in range(30):
        engine.tick_semaine()
    return tiles, ecos, gs["house"]


def _compute_at(lf, plants, saison, house, origin, seuil):
    """Recompute la scène à un seuil de LOD donné, renvoie (received_par_id,
    grille lumière-sol). Force un MISS de cache géométrique (le seuil ne fait pas
    partie de `geom_key`) en réinitialisant `_geom_key`."""
    light.SHADING_POWER_MIN = seuil
    lf._geom_key = None
    lf.compute(plants, saison, house=house, tile_origin=origin)
    received = dict(lf.received)
    grid = [row[:] for row in lf.data]
    return received, grid


def _emitter_power(p, saison):
    cls = p.plant_class
    return p.current_height * cls.canopy_radius_at(p) * cls.foliage_density_at(p, saison)


def main():
    saved = light.SHADING_POWER_MIN
    try:
        tiles, ecos, house = _scene()
        saison = "ete"
        all_ok = True
        # Preuve GLOBALE que le LOD agit sur les DEUX voies (reçue + sol). Agrégée
        # sur la scène : sur une tuile donnée, les semis coupés peuvent n'ombrer que
        # le sol (leur ombre n'atteint la canopée d'aucun voisin) → la reçue n'y
        # bouge pas, sans que le mécanisme soit en défaut. On exige donc que CHAQUE
        # voie remonte AU MOINS quelque part, et qu'AU MOINS une coupe ait eu lieu.
        recv_monte_global = False
        sol_monte_global = False
        coupes_global = 0

        for tile in tiles:
            lf = ecos[tile.tile_id].lumiere
            origin = TILE_ORIGINS.get(tile.tile_id, (0.0, 0.0))
            plants = tile.plants

            # --- 1. Invariant dormant : seuil 0 ≡ seuil minuscule (coupe personne).
            r0, g0 = _compute_at(lf, plants, saison, house, origin, 0.0)
            rtiny, gtiny = _compute_at(lf, plants, saison, house, origin, 1e-9)
            same_recv = (r0 == rtiny)
            same_grid = (g0 == gtiny)
            ok = same_recv and same_grid
            all_ok = all_ok and ok
            print(f"  [{tile.tile_id}] invariant dormant (0.0 ≡ 1e-9) : "
                  f"received={'=' if same_recv else '≠'} sol={'=' if same_grid else '≠'} "
                  f"→ {'OK' if ok else 'FAIL'}")

            # --- 2. Mécanisme actif : seuil ÉLEVÉ coupe les semis sous-seuil.
            SEUIL = 500.0
            alive = [p for p in plants if p.is_alive]
            n_cut = sum(1 for p in alive if _emitter_power(p, saison) < SEUIL)
            if n_cut == 0:
                print(f"  [{tile.tile_id}] mécanisme : aucune plante sous {SEUIL} "
                      f"(scène sans semis, skip)")
                continue
            coupes_global += n_cut
            rhi, ghi = _compute_at(lf, plants, saison, house, origin, SEUIL)

            # `emitters` a rétréci : la lumière-sol remonte là où un semis a quitté
            # le scatter ; la lumière reçue remonte là où l'ombre d'un semis touchait
            # la canopée d'un voisin (pas garanti sur CHAQUE tuile — cf. agrégat).
            monte_recv = any(rhi[k] > r0[k] + 1e-12 for k in r0)
            monte_sol = any(ghi[r][c] > g0[r][c] + 1e-12
                            for r in range(lf.rows) for c in range(lf.cols))
            recv_monte_global = recv_monte_global or monte_recv
            sol_monte_global = sol_monte_global or monte_sol
            print(f"  [{tile.tile_id}] mécanisme (seuil {SEUIL}, {n_cut} coupés) : "
                  f"reçue↑={monte_recv} sol↑={monte_sol}")

        meca_ok = coupes_global > 0 and recv_monte_global and sol_monte_global
        all_ok = all_ok and meca_ok
        print(f"\n  [scène] mécanisme actif GLOBAL : {coupes_global} coupés, "
              f"reçue↑={recv_monte_global} sol↑={sol_monte_global} "
              f"→ {'OK' if meca_ok else 'FAIL'}")

        if all_ok:
            print("\n[lod-ombre] PASS — invariant dormant + LOD actif vérifiés (D67 ①)")
            return 0
        print("\n[lod-ombre] FAIL — voir divergences ci-dessus")
        return 1
    finally:
        light.SHADING_POWER_MIN = saved   # pas de fuite d'état entre tests


if __name__ == "__main__":
    sys.exit(main())
