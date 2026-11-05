"""
SYMBIOSE — bancs/lianes.py
Banc « liane_relais » (sprint HOUPPIER ②) : ce que fait une liane au sommet de son appui.
Quatre situations, lierre et jasmin palissés dès la pose, séparées pour rester lisibles :

  treillis + arbre haut   elle passe sur l'arbre (lierre et jasmin) ;
  treillis + mur          le lierre passe sur le mur ; le jasmin ne le peut pas ;
  treillis seul           elle plie au-dessus du treillis, et sa partie pendante tombe ;
  sans appui              elle plie à faible hauteur, le lierre comme le jasmin.

Pure COMPOSITION de l'état moteur → golden NEUTRE (jamais monté pour smoke/full).
La tuile touche le mur est de la maison (x = 1400) : son bord ouest est le mur.
Lecture : `tests/bancs/test_liane_relais.py`, capture après 3 ans de turbo.
"""
from __future__ import annotations

from plants import AppleTree
from plants.catalogue import PLANT_CATALOGUE
from world import Support, House
from .base import build_banc_tile, monde, vieillir, sans_herbivorie, banque_de
from .planche_especes import _poser_adulte

ORIGINE_X, ORIGINE_Y = 1400.0, 600.0
HAUTEUR_TREILLIS = 180.0
ANS_ARBRE = 10.0     # un pommier nettement plus haut que le treillis


def _poser_liane(tuile, nom: str, x: float, y: float, treillis: Support | None = None):
    plante = _poser_adulte(tuile, PLANT_CATALOGUE[nom], int(ORIGINE_X + x), int(ORIGINE_Y + y))
    if treillis is not None:
        tuile.supports.append(treillis)
        plante.support = (treillis, treillis.height_cm)
    return plante


def _treillis(x: float, y: float) -> Support:
    return Support(support_type="treillis", x_cm=x, y_cm=y,
                   height_cm=HAUTEUR_TREILLIS, finesse="surface")


def _poser_arbre(tuile, x: float, y: float):
    arbre = tuile.add_plant(AppleTree, int(y // 50), int(x // 50))
    arbre.current_stage = len(AppleTree.growth_stages) - 1
    vieillir(arbre, ANS_ARBRE)
    return arbre


def liane_relais():
    tuile, eco = build_banc_tile("LIANES", "terre", 28, 12, ORIGINE_X, ORIGINE_Y,
                                 humidite=1.2, fertilite=1.2, microbiome=0.6)
    # Treillis + arbre haut : le tronc à 50 cm du treillis, dans le rayon de relais, et du
    # côté où pousse chaque liane (sinon sa pointe s'en écarte et ne l'atteint pas).
    _poser_arbre(tuile, 325.0, 125.0)
    _poser_liane(tuile, "lierre", 275.0, 125.0, _treillis(275.0, 125.0))
    _poser_arbre(tuile, 225.0, 475.0)
    _poser_liane(tuile, "jasmin", 275.0, 475.0, _treillis(275.0, 475.0))
    # Treillis + mur : pied au centre du premier plot, à 25 cm du mur.
    _poser_liane(tuile, "lierre", 45.0, 325.0, _treillis(45.0, 325.0))
    _poser_liane(tuile, "jasmin", 45.0, 625.0, _treillis(45.0, 625.0))
    # Treillis seul, loin de tout.
    _poser_liane(tuile, "lierre", 525.0, 825.0, _treillis(525.0, 825.0))
    _poser_liane(tuile, "jasmin", 225.0, 825.0, _treillis(225.0, 825.0))
    # Sans appui.
    _poser_liane(tuile, "lierre", 225.0, 1175.0)
    _poser_liane(tuile, "jasmin", 525.0, 1175.0)
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    sans_herbivorie(eco)
    return monde([tuile], {tuile.tile_id: eco}, house=House(),
                 banque=banque_de("lierre", "jasmin"))
