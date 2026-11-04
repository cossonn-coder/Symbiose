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

from sim.actions.taille_herbacee import RABATTU_SEMAINES, decroissant

# Semaines pour que le pied dessiné retrouve sa forme [choix, conception §4.4].
PINCE_SEMAINES = 12


def marquer_taille(base: dict, plant, semaine: int) -> None:
    """Ajoute à `base` les hints non nuls de ce pied."""
    rabattu = decroissant(plant.semaine_coupe, semaine, RABATTU_SEMAINES)
    if rabattu > 0.0:
        base["rabattu"] = rabattu
    pince = decroissant(plant.semaine_pince, semaine, PINCE_SEMAINES)
    if pince > 0.0:
        base["pince"] = pince
