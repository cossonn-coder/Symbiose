"""
SYMBIOSE — plants/perennials/
Pérennes ligneuses (D21) — base commune polymorphe avec les annuelles.

Les arbres exposent la MÊME interface lumière que les annuelles
(height_at / canopy_radius_at / root_radius_at / foliage_density_at), si bien
que le LightField les traite à l'identique — zéro duplication. Seule la logique
de croissance diffère : annuelles = stades discrets, arbres = courbe d'âge
interpolée (`age_years` accumulé +1/52 par tick dans engine).

`foliage_density` est saisonnière : un arbre caduc ne projette aucune ombre
l'hiver (soleil d'hiver au sol sous un fruitier — levier permaculture majeur).

genetic_factor reste neutre (1.0) — l'héritage génétique est le Sprint
génétique/reproduction, pas ici.
"""

from plants.perennials.base import PerennialWoody
from plants.perennials.fruitiers import Fig, AppleTree, CherryTree, WalnutTree
from plants.perennials.forestiers import (OakTree, BeechTree, BirchTree,
                                          HornbeamTree, FirTree, HazelTree)
from plants.perennials.rives import Alder, Willow
