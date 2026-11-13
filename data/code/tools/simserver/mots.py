"""
SYMBIOSE — tools/simserver/mots.py
Des MOTS au lieu des chiffres dans les messages de geste (sprint GESTES LISIBLES ①,
conception §5 ; philo #5 : pas de chiffre en HUD primaire).

Le pont fabrique les phrases de retour d'un geste ; ce module leur prête deux
traductions partagées :
  - `quantite_en_mots` : une masse de matière (paillis, BRF, feuilles, compost) dite
    par paliers exprimés en DOSES de paillis (`PAILLAGE_DOSE`, ce qu'un geste
    `pailler` consomme) — l'unité que le joueur sent : « de quoi couvrir un plot » ;
  - `vigueur_en_mots` : un gain de Vigueur dit en ressenti.

Les champs numériques du bilan (`cost`, `gain`, `vigueur`) restent au result pour la
vue : seule la PHRASE change. Lecture pure, aucune règle de jeu ici.
"""
from __future__ import annotations

from fields.ecofields import PAILLAGE_DOSE

# Paliers de quantité, en doses de paillis (borne haute exclue → mot). Le dernier
# mot couvre tout ce qui dépasse. Calibrage F5 (ressenti).
_PALIERS_DOSES = ((0.25, "une pincée"), (0.75, "une poignée"),
                  (2.0, "une brassée"), (5.0, "un panier plein"))
_AU_DELA = "une pleine charretée"

# Paliers de Vigueur (régénération passive ≈ 10 par semaine : « la force revient »
# vaut à peu près une semaine de repos).
_PALIERS_VIGUEUR = ((1.0, "à peine un frisson de force"),
                    (5.0, "un peu de force revient"),
                    (15.0, "la force revient"))
_VIGUEUR_AU_DELA = "une vague de force"


def quantite_en_mots(q: float) -> str:
    """Une quantité de matière dite en mots (paliers en doses de `PAILLAGE_DOSE`)."""
    doses = q / PAILLAGE_DOSE
    for borne, mot in _PALIERS_DOSES:
        if doses < borne:
            return mot
    return _AU_DELA


def vigueur_en_mots(g: float) -> str:
    """Un gain de Vigueur dit en ressenti."""
    for borne, mot in _PALIERS_VIGUEUR:
        if g < borne:
            return mot
    return _VIGUEUR_AU_DELA
