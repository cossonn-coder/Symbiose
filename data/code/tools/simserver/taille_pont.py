"""
SYMBIOSE — tools/simserver/taille_pont.py
Hints `rabattu` et `pince` d'une plante au snapshot (FORMES DES PLANTES ②, 0.6.7). Module à
part : `serialize.py` est au bord de la bande de taille.
La semaine du geste est écrite par `sim/actions/gestes.py` (espèces non migrées). Le hint
décroît de 1 à 0, le pied dessiné se rabat puis repousse (conception §4.4). Il ne fait que
MONTRER le geste : `height_at` ne bouge pas, ombre et lumière restent celles du stade.
Clé présente seulement si non nulle, comme `quatre_feuilles`. Lecture pure → golden neutre.
"""
from __future__ import annotations

# Semaines pour que le pied dessiné retrouve sa forme [choix, conception §4.4].
RABATTU_SEMAINES = 8
PINCE_SEMAINES = 12


def _decroissant(semaine_geste: int, semaine: int, duree: int) -> float:
    """1 la semaine du geste, 0 après `duree` semaines ; 0 si le geste n'a jamais eu lieu."""
    if semaine_geste < 0:
        return 0.0
    return round(max(0.0, 1.0 - (semaine - semaine_geste) / duree), 3)


def marquer_taille(base: dict, plant, semaine: int) -> None:
    """Ajoute à `base` les hints non nuls de ce pied."""
    rabattu = _decroissant(plant.semaine_coupe, semaine, RABATTU_SEMAINES)
    if rabattu > 0.0:
        base["rabattu"] = rabattu
    pince = _decroissant(plant.semaine_pince, semaine, PINCE_SEMAINES)
    if pince > 0.0:
        base["pince"] = pince
