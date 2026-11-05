"""
SYMBIOSE — bancs/verger_mur.py
Banc « verger_mur » (sprint HOUPPIER ③) : les 4 arbres fruitiers MÛRS, chacun dans sa
fenêtre de fruits. Sert à dire si chaque espèce porte, à quelle date, et où vont ses fruits
non cueillis. Absents de `full` ou trop jeunes pour y fructifier (noyer : 15 ans), le
figuier et le noyer ne se mesurent que là.

La bande est de la carte, à l'est de la maison (x ≥ 1400) : la maison ne gêne ni le
cadre ni la lumière. Un seul noyer, isolé : il ne compte que sur son propre panache.
Pure COMPOSITION de l'état moteur → golden NEUTRE (jamais monté pour smoke/full).
Lecture : `tests/bancs/test_verger_mur.py`.
"""
from __future__ import annotations

from plants import AppleTree, CherryTree, Fig, WalnutTree
from .base import build_banc_tile, monde, vieillir, sans_herbivorie

ORIGINE_X, ORIGINE_Y = 1400.0, 0.0
# Espèce, plot (ligne, colonne) dans la bande, âge. Mûrs, et assez vieux pour une couronne :
# à 6 ans un pommier n'a que 8 segments, donc une poignée de sites de fruits.
ARBRES = ((CherryTree, 3, 6, 15.0), (AppleTree, 11, 6, 15.0),
          (Fig, 19, 6, 15.0), (WalnutTree, 28, 6, 16.0), (WalnutTree, 37, 6, 16.0))
RONDELLES_POLLINISATEUR = 3   # habitat au maximum : sans lui les abeilles meurent avant les fleurs


def verger_mur():
    tuile, eco = build_banc_tile("VERGER_MUR", "terre", 40, 12, ORIGINE_X, ORIGINE_Y,
                                 humidite=1.2, fertilite=1.5, microbiome=0.5)
    for classe, ligne, colonne, age in ARBRES:
        vieillir(tuile.add_plant(classe, ligne, colonne), age)
    for _ in range(RONDELLES_POLLINISATEUR):
        tuile.stakes[0].add("pollinisateur")
    eco.seed_bank.germination_candidates = lambda *a, **k: []   # verger seul, sans levées
    sans_herbivorie(eco)
    return monde([tuile], {tuile.tile_id: eco})
