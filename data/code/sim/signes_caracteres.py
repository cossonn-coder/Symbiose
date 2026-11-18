"""
SYMBIOSE — sim/signes_caracteres.py
Les SIGNES VISIBLES des caractères héritables (D139 caractères vivants ⑤,
conception §4). Ce que la vue doit dessiner, déjà traduit : jamais un gène brut.

Chaque caractère qui se voit a sa fonction PURE, bornée, qui ne lit que la plante
(ses gènes et des traits d'espèce) :

  | signe              | caractère           | valeur                                 |
  |--------------------|---------------------|----------------------------------------|
  | `teinte_fleur`     | couleur_fleur       | [teinte °, saturation] sur l'axe d'espèce |
  | `echelle_fleur`    | taille_fleur        | rayon de la fleur, × [0,63 ; 1,26]      |
  | `contraste_guides` | guide_nectar        | lignes / œil central, ∈ [0, 1]          |
  | `echelle_fruit`    | taille_fruit        | rayon du fruit, × [0,74 ; 1,17]         |
  | `matite_feuille`   | coriacite_feuille   | feuille mate et sombre, ∈ [0, 1]        |
  | `port`             | dominance_apicale   | −1 buisson … +1 flèche                  |
  | `rejets`           | vigueur_clonale     | rejets au pied, ∈ [0, 1] (0 = aucun)    |

Le NOMBRE de fruits n'est pas ici : c'est un état moteur réel, déjà exporté
(`fruits[].nombre`). Les autres caractères n'ont pas de signe sur la plante
(nectar, pollen, goût, fixation, mycorhization : on les voit aux butineurs, en
mangeant, aux voisines plus vertes) — conception §4.

📖 Pourquoi une racine carrée pour la fleur et cubique pour le fruit ? Le gène
`taille_fleur` multiplie l'ATTRAIT, porté par la surface vue de loin : le rayon
dessiné suit √g. `taille_fruit` multiplie la MASSE, portée par le volume : le
rayon suit ∛g. Le signe ne ment pas sur la grandeur qu'il montre.

Couche `sim` : lit `plants` (registre, couleurs) et `sim.clonal` (même critère
de maturité que l'émission des rejets). Aucun RNG, aucune écriture : le pont
l'appelle, le tick jamais → golden intact.
"""
from __future__ import annotations

import math

from plants.caracteres import CARACTERES
from plants.couleurs import couleur_sur_axe
from sim.clonal import _mature        # MÊME critère que l'émission (le signe ne ment pas)


def _position(plant, nom: str) -> float:
    """Gène ramené à [0, 1] entre ses bornes physiologiques (0,5 = neutre facteur)."""
    lo, hi = CARACTERES[nom].bornes
    return min(1.0, max(0.0, (plant.gene(nom) - lo) / (hi - lo)))


def teinte_fleur(plant) -> list | None:
    """[teinte °, saturation] de la fleur, ou None sans axe de couleur (anémophile,
    fleur non dessinée). Saturation 0 = blanc."""
    axe = plant.plant_class.axe_couleur
    if axe is None:
        return None
    h, s = couleur_sur_axe(axe, plant.gene("couleur_fleur"))
    return [round(h, 1), round(s, 3)]


def echelle_fleur(plant) -> float:
    return round(math.sqrt(plant.gene("taille_fleur")), 3)


def contraste_guides(plant) -> float:
    return round(_position(plant, "guide_nectar"), 3)


def echelle_fruit(plant) -> float:
    return round(plant.gene("taille_fruit") ** (1.0 / 3.0), 3)


def matite_feuille(plant) -> float:
    return round(_position(plant, "coriacite_feuille"), 3)


def port(plant) -> float:
    return round(2.0 * _position(plant, "dominance_apicale") - 1.0, 3) + 0.0   # pas de « −0,0 »


def rejets(plant) -> float:
    """0 tant que la plante ne peut pas émettre (non clonale ou immature), sinon
    l'intensité de sa vigueur clonale (une colonie neutre montre des rejets : 0,5)."""
    if plant.plant_class.clonal_mode == "none" or not _mature(plant):
        return 0.0
    return round(_position(plant, "vigueur_clonale"), 3)


def signes_constants(plant) -> dict:
    """Signes qui ne dépendent QUE des gènes (constants pour la vie de la plante :
    envoyés une fois, comme `genes`). Les signes de fleur seulement si l'espèce a
    une fleur colorée, celui du fruit seulement chez un fruitier."""
    cls = plant.plant_class
    d = {"matite_feuille": matite_feuille(plant), "port": port(plant)}
    teinte = teinte_fleur(plant)
    if teinte is not None:
        d["teinte_fleur"] = teinte
        d["echelle_fleur"] = echelle_fleur(plant)
        d["contraste_guides"] = contraste_guides(plant)
    if getattr(cls, "fruitier", False):
        d["echelle_fruit"] = echelle_fruit(plant)
    return d
