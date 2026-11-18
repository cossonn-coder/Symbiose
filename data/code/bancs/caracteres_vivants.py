"""
SYMBIOSE — bancs/caracteres_vivants.py
Banc d'essai CARACTÈRES VIVANTS (D139, sprint caractères vivants ⑥, observation F5).

Ce que Nico doit VOIR sur une seule tuile, une rangée par caractère, chaque rangée
RANGÉE de gauche à droite par la valeur du caractère qu'elle montre :
  0  BOURRACHES par couleur de fleur : du bleu (gauche) au rose (droite) ;
  1  BOURRACHES par guides à nectar : œil pâle (gauche) → œil sombre et lignes (droite) ;
  3  PHACÉLIES par couleur de fleur : du lavande au blanc ;
  4  TOMATES par taille de fruit : nombreux petits (gauche) → peu de gros (droite) ;
  5  BASILICS par dominance apicale : port en buisson (gauche) → en flèche (droite) ;
  7  FRAISIERS par vigueur clonale : peu de rejets (gauche) → colonie dense (droite).
La matité des feuilles (coriacité) varie d'un pied à l'autre dans toutes les rangées.
Le survol G (debug) s'ouvre au montage (WorldView.Genes.cs) : pointer un pied montre
ses caractères dans leur unité.

📖 Pourquoi TRIER des fondateurs et pas les fabriquer. Chaque rangée tire `CANDIDATS`
fondateurs sauvages par la vraie loi du moteur (`founder_genes`, σ_A de l'espèce), puis
garde huit pieds aux quantiles du caractère montré. Aucun gène n'est écrit à la main :
on choisit dans la diversité réelle d'une population, comme un sélectionneur qui
aligne ses pieds. Pure COMPOSITION d'un état → golden NEUTRE (une fabrique de banc
n'est jamais montée pour smoke/full). Zéro RNG (philo #3).
"""
from __future__ import annotations

from plants import Borage, Phacelia, Tomato, Basil
from plants.catalogue import Strawberry
from fields import founder_genes
from .base import build_banc_tile, monde, banque_de, sans_herbivorie

ROWS, COLS = 8, 8
SEED = 0xCA2AC7          # seed LOCAL du banc : seule sa constance compte (philo #3)
CANDIDATS = 64           # fondateurs tirés par rangée, dont 8 gardés aux quantiles
ORIGINE_CM = 1450.0      # coin de tuile devant la maison (patron `lignees`)

# (rang, espèce, caractère qui ordonne la rangée)
RANGEES = (
    (0, Borage, "couleur_fleur"),
    (1, Borage, "guide_nectar"),
    (3, Phacelia, "couleur_fleur"),
    (4, Tomato, "taille_fruit"),
    (5, Basil, "dominance_apicale"),
    (7, Strawberry, "vigueur_clonale"),
)


def _alignes(cls, rang: int, caractere: str) -> list[dict]:
    """Huit vecteurs fondateurs de `cls`, du plus bas au plus haut `caractere`, pris
    aux quantiles (extrêmes compris) de `CANDIDATS` tirages déterministes."""
    tires = [founder_genes(cls, SEED, 1 + rang, rang, k % COLS, 25.0 + 7.0 * k, 25.0)
             for k in range(CANDIDATS)]
    tires.sort(key=lambda g: g[caractere])
    return [tires[round(i * (CANDIDATS - 1) / (COLS - 1))] for i in range(COLS)]


def caracteres_vivants():
    """Banc « caractères vivants » (⑥) : une rangée par signe visible."""
    tile, eco = build_banc_tile("CARACTERES", "terre", ROWS, COLS, ORIGINE_CM, ORIGINE_CM,
                                humidite=1.4, fertilite=1.3, microbiome=0.5)
    # Instrument d'observation : sans ce garde, l'herbivorie emporte les pieds isolés
    # avant la fin du warmup (patron `lignees`, D127).
    sans_herbivorie(eco)
    for rang, cls, caractere in RANGEES:
        for c, genes in enumerate(_alignes(cls, rang, caractere)):
            p = tile.add_plant(cls, rang, c)
            if p is not None:
                p.genes = dict(genes)
    return monde([tile], {tile.tile_id: eco},
                 banque=banque_de("bourrache", "phacelie", "tomate", "basilic", par_espece=3))
