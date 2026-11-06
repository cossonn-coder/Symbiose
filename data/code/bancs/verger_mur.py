"""
SYMBIOSE — bancs/verger_mur.py
Banc « verger_mur » (sprint HOUPPIER ③) : les 4 arbres fruitiers MÛRS, chacun dans sa
fenêtre de fruits. Sert à dire si chaque espèce porte, à quelle date, et où vont ses fruits
non cueillis. Absents de `full` ou trop jeunes pour y fructifier (noyer : 15 ans), le
figuier et le noyer ne se mesurent que là.

Le monde entier est le cadre (D129 ① : banc espacé). Dans l'ancienne bande à l'est de la
maison, 5 arbres à 4-4,5 m se faisaient de l'ombre : le pommier recevait 0,23 à 0,35 de
lumière en saison feuillée et mourait en an 4 [seed 42, n=1 run, VM]. Ici les trois fruitiers
à insectes sont au SUD de la maison (y = Sud : l'ombre de la maison part vers le nord, loin
d'eux), à 8 m les uns des autres. Les deux noyers sont au nord-est, côte à côte d'est en ouest
(un noyer au sud de l'autre lui faisait de l'ombre : 0,64-0,75 de lumière [seed 42, n=1 run,
VM]), hors de l'ombre de la maison, à 4,5 m l'un de l'autre, sous la portée de leur pollen
(`pollination_radius_cm` 600) : ils se pollinisent par le vent.
Pure COMPOSITION de l'état moteur → golden NEUTRE (jamais monté pour smoke/full).
Lecture : `tests/bancs/test_verger_mur.py`.
"""
from __future__ import annotations

from plants import AppleTree, CherryTree, Fig, WalnutTree
from .base import build_banc_tile, monde, vieillir, sans_herbivorie

COTE_PLOTS = 40   # 20×20 m, le monde entier : la maison reste au centre (600-1400 cm)
# Espèce, plot (ligne = y Sud, colonne = x Est), âge. Mûrs, et assez vieux pour une couronne :
# à 6 ans un pommier n'a que 8 segments, donc une poignée de sites de fruits.
ARBRES = ((CherryTree, 36, 4, 15.0), (AppleTree, 36, 20, 15.0),
          (Fig, 36, 35, 15.0), (WalnutTree, 3, 29, 16.0), (WalnutTree, 3, 38, 16.0))
RONDELLES_POLLINISATEUR = 3   # habitat au maximum : sans lui les abeilles meurent avant les fleurs


def verger_mur():
    tuile, eco = build_banc_tile("VERGER_MUR", "terre", COTE_PLOTS, COTE_PLOTS,
                                 humidite=1.2, fertilite=1.5, microbiome=0.5)
    for classe, ligne, colonne, age in ARBRES:
        vieillir(tuile.add_plant(classe, ligne, colonne), age)
    for _ in range(RONDELLES_POLLINISATEUR):
        tuile.stakes[0].add("pollinisateur")
    eco.seed_bank.germination_candidates = lambda *a, **k: []   # verger seul, sans levées
    sans_herbivorie(eco)
    return monde([tuile], {tuile.tile_id: eco})
