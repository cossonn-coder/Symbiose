# SYMBIOSE — tools/jardinier_auto/regles.py
# Étape 3 de la boucle (§3.3 / table §5) : à un facteur limitant, associer le/les
# GESTE(S) candidat(s) qui le relâchent. Format retenu (Q2) = liste ORDONNÉE de
# règles priorisées dans ce module Python, lisible et éditable à la main — PAS de
# fichier de données externe (simplicité #2).
#
# Ce sprint ne crée AUCUN geste : chaque `verbe` renvoie à une fonction existante
# de `sim.actions` (mappée dans execution.py). Un facteur peut avoir PLUSIEURS
# règles (chaîne de repli) — `regles_pour` les renvoie triées par priorité
# décroissante, et `proposition.proposer` prend la PREMIÈRE APPLICABLE.
#
# BIAIS PERMACOLE (H7, §5) : à facteur égal, on préfère le geste DURABLE sur le
# milieu (pailler) au geste RÉPÉTITIF (arroser). Non par idéologie mais parce que
# ça économise la Vigueur sur la durée. D'où, pour `hydrique`, `pailler` (12) AVANT
# `arroser` (10) : l'automate redécouvre le paillage par nécessité, et ne retombe
# sur l'arrosage que si le mulch manque (ravitaillement impossible).

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Regle:
    """Une ligne de la table facteur→geste.
    `facteur`  : nom renvoyé par diagnostic.facteur_limitant.
    `verbe`    : geste `sim.actions` à jouer (mappé dans execution.py).
    `cible`    : "milieu" (geste sur un plot) | "vivant" (geste sur une plante).
    `priorite` : entier ; plus grand = joué plus tôt quand le budget serre (③)."""

    facteur: str
    verbe: str
    cible: str
    priorite: int


# Liste ORDONNÉE (priorité décroissante). L'ordre littéral documente l'intention ;
# la priorité chiffrée pilote le tri de l'étape 4 (prioriser) ET le repli de la
# chaîne (proposer prend la 1re règle applicable dans cet ordre).
REGLES: list[Regle] = [
    # Récolter — FAIBLE coût, apporte de la Vigueur, time-sensitive (un organe mûr
    # non cueilli se dégrade) → priorité haute.
    Regle(facteur="organe_mur",         verbe="recolter",   cible="vivant", priorite=20),
    # Hydrique — pailler (durable) EN PREMIER (biais permacole), arroser en repli.
    Regle(facteur="hydrique",           verbe="pailler",    cible="milieu", priorite=12),
    Regle(facteur="hydrique",           verbe="arroser",    cible="milieu", priorite=10),
    # Concurrence férale — désherbage curatif/systématique (§4), geste sur le VIVANT.
    Regle(facteur="concurrence_ferale", verbe="deraciner",  cible="vivant", priorite=9),
    # Sol nu — couvrir (durable). Un seul recours ; sans mulch → impasse (§7).
    Regle(facteur="sol_nu",             verbe="pailler",    cible="milieu", priorite=8),
    # Sol compacté — grelinette (aère SANS retourner, no-dig), geste de milieu.
    Regle(facteur="sol_compacte",       verbe="grelinette", cible="milieu", priorite=6),
    # Ombrage — tailler le voisin ombrageant. Geste sur le VIVANT (philo #1 :
    # permis mais coûteux) → priorité BASSE (dernier recours).
    Regle(facteur="ombrage",            verbe="tailler",    cible="vivant", priorite=4),
    # `exces_eau` : AUCUNE règle (drainer/creuser n'existent pas) → impasse §7.
]


def regles_pour(facteur: str) -> list[Regle]:
    """Toutes les règles du facteur, triées par priorité DÉCROISSANTE (stable).
    Liste VIDE = facteur sans réponse dans la table → impasse `geste_inexistant`
    (§7 : « il manque au joueur aussi », pas une porte de service)."""
    return sorted((r for r in REGLES if r.facteur == facteur),
                  key=lambda r: -r.priorite)
