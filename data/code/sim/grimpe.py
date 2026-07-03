"""
SYMBIOSE — sim/grimpe.py
Recherche d'accroche des plantes grimpantes (D49 volet A, CONCEPTION_GRIMPANTES
§4). Couche `sim` (importe `world` : Support/mur + compatibilité). Appelée par
l'engine JUSTE AVANT la croissance : une grimpante LIBRE, plus haute que sa
`hauteur_autoportante`, cherche dans un rayon BORNÉ un support compatible et s'y
accroche. L'accroche est un ÉTAT PERSISTANT (`plant.support`) → une accrochée
n'est plus jamais scannée (réflexe perf D32 : on élague, on ne balaie pas).

Déterministe, ZÉRO RNG (philo #3) : départage distance PUIS identité stable.
Le biais de grimpe lui-même (relèvement du plancher d'apex quand accroché) vit
dans `sim/growth/geometrie.py` (`_apex_z_floor`), déjà en place depuis ①.
"""

from __future__ import annotations
import math

from constants import PLOT_CM
from world import support_compatible, MUR

# Rayon de recherche d'accroche : plot-foyer + son voisinage immédiat (§4, ~50 cm).
# 1.5 plot couvre le foyer et déborde sur les plots adjacents où un support proche
# peut être posé. Placeholder de calibrage (maquette ⑥).
RAYON_ACCROCHE_CM = 1.5 * PLOT_CM


def _mur_appui(plant, house, tile_origin) -> tuple | None:
    """Point d'appui du MUR maison le plus proche de la plante, s'il tombe dans le
    rayon d'accroche. Renvoie `(dist_cm, height_cm, x_world, y_world)` ou None.
    La plante est en repère TUILE-local ; on la projette en repère MONDE (offset
    `tile_origin`) pour la comparer à `house.footprint_bounds` (repère monde). Le
    point d'appui = le point du RECTANGLE-empreinte le plus proche (clamp)."""
    if house is None:
        return None
    ox, oy = tile_origin
    px, py = plant.x_cm + ox, plant.y_cm + oy
    x0, y0, x1, y1 = house.footprint_bounds
    cx = min(max(px, x0), x1)                        # point du rectangle le plus proche
    cy = min(max(py, y0), y1)
    d = math.hypot(px - cx, py - cy)
    if d > RAYON_ACCROCHE_CM:
        return None
    return (d, house.height_cm, cx, cy)


def chercher_support(plant, tile, house=None) -> None:
    """Tente d'accrocher `plant` à un support proche (structures de la tuile + mur
    maison). No-op sauf pour une grimpante LIBRE au-dessus de sa hauteur
    autoportante — le seul cas qui coûte un scan (borné). Pose
    `plant.support = (ref, height_appui)` sur le compatible le PLUS PROCHE
    (départage déterministe : distance, puis identité stable — zéro RNG).

    `ref` = l'objet `Support` accroché, ou la sentinelle `MUR` pour le mur maison.
    `height_appui` = hauteur d'appui offerte (cm) : le plancher d'apex renforcé
    (`_apex_z_floor`) fera monter la structure jusque-là."""
    cls = plant.plant_class
    mode = cls.mode_grimpe
    hp = cls.hauteur_autoportante
    # Filtre perf : seules les grimpantes LIBRES et déjà trop hautes pour se tenir
    # seules cherchent un appui. Tout le reste (non-grimpantes, accrochées, encore
    # courtes) sort immédiatement → aucun scan.
    if mode is None or hp is None or plant.support is not None:
        return
    max_z = max((s.base[2] + s.dir[2] * s.length_cm for s in plant.segments),
                default=0.0)
    if max_z <= hp:
        return

    # Candidats compatibles dans le rayon : (distance, clé_stable, ref, height).
    # La clé_stable départage à distance égale sans RNG (index de pose du support ;
    # -1 pour le mur, prioritaire à distance strictement égale — cas de bord).
    candidats: list[tuple] = []
    for i, sup in enumerate(tile.supports):
        if not support_compatible(mode, sup.support_type):
            continue
        d = math.hypot(plant.x_cm - sup.x_cm, plant.y_cm - sup.y_cm)
        if d <= RAYON_ACCROCHE_CM:
            candidats.append((d, i, sup, sup.height_cm))

    # Mur maison : comparé en repère MONDE (on passe l'offset de la tuile). Ajouté
    # aux candidats avec la clé stable -1 (prioritaire au départage strictement
    # égal, cas de bord).
    if support_compatible(mode, MUR):
        mur = _mur_appui(plant, house, (tile.origin_x_cm, tile.origin_y_cm))
        if mur is not None:
            d, h, _, _ = mur
            candidats.append((d, -1, MUR, h))

    if not candidats:
        return
    # Le plus proche ; départage déterministe par la clé stable (distance, clé).
    d, _, ref, height_appui = min(candidats, key=lambda t: (t[0], t[1]))
    plant.support = (ref, height_appui)
