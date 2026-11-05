"""
SYMBIOSE — bancs/houppiers.py
Bancs « houppiers » et « houppiers_25 » (sprint HOUPPIER ④) : les 11 arbres, un pied par
espèce, à 10 et à 25 ans, pour juger un houppier et mesurer sa cuisson. `foret_ports` ne s'y
prête pas : la maison et les bords du monde gênent (figuier à 1275,775, arbres à x 2275).

Deux mondes et non un : 22 couronnes de 2 à 3 m de rayon ne tiennent pas côte à côte dans
20×20 m une fois la maison posée. Ici, 11 places en anneau autour de la maison, 5 m entre
voisins, tout dans le monde.

Morphogénèse pré-déroulée (`vieillir`), sans sol qui les départage. Pure COMPOSITION de l'état
moteur → golden NEUTRE (jamais monté pour smoke/full).
"""
from __future__ import annotations

from plants.perennials import (Alder, AppleTree, BeechTree, BirchTree, CherryTree, Fig, FirTree,
                               HornbeamTree, OakTree, WalnutTree, Willow)
from .base import build_banc_tile, monde, vieillir, sans_herbivorie

COTE_PLOTS = 40   # 20×20 m, le monde entier : la maison reste au centre (600-1400 cm)
ARBRES = (AppleTree, CherryTree, WalnutTree, OakTree, BeechTree, BirchTree,
          HornbeamTree, Alder, Willow, Fig, FirTree)
# (ligne, colonne), plots de 50 cm : deux rangées de 4 au nord et au sud, 3 pieds sur les côtés.
PLACES = ((6, 4), (6, 14), (6, 24), (6, 34), (34, 4), (34, 14), (34, 24), (34, 34),
          (16, 5), (25, 5), (20, 35))


def _houppiers(nom: str, ans: float):
    tuile, eco = build_banc_tile(nom, "terre", COTE_PLOTS, COTE_PLOTS,
                                 humidite=1.2, fertilite=1.5, microbiome=0.5)
    for classe, (ligne, colonne) in zip(ARBRES, PLACES):
        vieillir(tuile.add_plant(classe, ligne, colonne), ans)
    eco.seed_bank.germination_candidates = lambda *a, **k: []   # arbres seuls, sans levées
    sans_herbivorie(eco)
    return monde([tuile], {tuile.tile_id: eco})


def houppiers():
    return _houppiers("HOUPPIERS", 10.0)


def houppiers_25():
    return _houppiers("HOUPPIERS_25", 25.0)
