"""
SYMBIOSE — tools/simserver/accroche_pont.py
Clé `support` d'une plante au snapshot (D49 volet A, 0.5.18 ; point d'appui, FORMES DES
PLANTES ⑥, 0.6.8). Absente si la plante est libre ou n'est pas une grimpante, sinon
{type, height_cm} et, sauf pour le mur, {dx_cm, dy_cm} : où est l'appui par rapport au pied.

`plant.support = (ref, height_appui)`, où `ref` est un `Support` posé (son `support_type`),
la sentinelle MUR (str) ou une `PlantInstance` hôte vivante. Duck-typing local, sans importer
`sim/grimpe`. Le pied d'une grimpante peut être à 75 cm de son appui (`RAYON_ACCROCHE_CM`) :
la vue a besoin de cet écart pour dessiner le haricot AUTOUR de son tuteur.

Lecture pure → golden neutre (aucune grimpante accrochée dans le smoke → clé absente).
"""
from __future__ import annotations


def marquer_accroche(base: dict, plant) -> None:
    """Ajoute à `base` l'accroche de ce pied, s'il en a une."""
    if plant.support is None:
        return
    ref, h_appui = plant.support
    if isinstance(ref, str):
        base["support"] = {"type": "mur", "height_cm": round(h_appui, 2)}
        return
    base["support"] = {"type": getattr(ref, "support_type", "hote"),
                       "height_cm": round(h_appui, 2),
                       "dx_cm": round(ref.x_cm - plant.x_cm, 1),
                       "dy_cm": round(ref.y_cm - plant.y_cm, 1)}
