"""
SYMBIOSE — tools/simserver/quatre_feuilles_pont.py
Hint `quatre_feuilles` d'une plante au snapshot (TRÈFLE DOMINANT ③, 0.6.5). Module à
part : `serialize.py` est au bord de la bande de taille.
Clé présente seulement quand elle est vraie : ~1 trèfle sur 200 la porte, et l'absence
de clé ne coûte rien sur le tube. La vue dessine, elle n'affiche rien au HUD (philo #5).
Lecture pure → golden neutre (le golden tourne hors serveur).
"""
from __future__ import annotations

from sim.quatre_feuilles import est_quatre_feuilles


def marquer_quatre_feuilles(base: dict, plant, seed: int) -> None:
    """Ajoute le hint au dict de plante `base` si ce pied porte quatre feuilles."""
    if est_quatre_feuilles(plant, seed):
        base["quatre_feuilles"] = True
