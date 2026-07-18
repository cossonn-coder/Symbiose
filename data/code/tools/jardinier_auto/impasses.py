# SYMBIOSE — tools/jardinier_auto/impasses.py
# DÉTECTEUR D'IMPASSES (§7) — objectif important du sprint (exigence Nico). Quand
# l'étape « proposer » diagnostique un facteur limitant mais qu'AUCUN geste-réponse
# n'est APPLICABLE, on consigne une impasse TYPÉE = « trou de gameplay » : un
# problème que le joueur ne pourrait pas résoudre non plus, dans l'état actuel du
# jeu. L'automate devient un instrument de découverte de ces impasses.
#
# NE BLOQUE JAMAIS la boucle — c'est un SIGNALEMENT, on continue (§7). Les impasses
# sont des dicts JSON-sérialisables consignés au même journal que les gestes, sous
# une catégorie `impasse` distincte (trace.entree_impasse).

from __future__ import annotations
from dataclasses import dataclass

# Les quatre types d'impasse du §7.
GESTE_INEXISTANT = "geste_inexistant"          # le facteur n'a aucune ligne dans la table
GESTE_VERROUILLE = "geste_verrouille"          # règle GATED non débloquée (mode payé, ③)
RAVITAILLEMENT_MANQUANT = "ravitaillement_manquant"  # pailler sans mulch ni moyen d'en produire
OBJECTIF_INATTEIGNABLE = "objectif_inatteignable"    # cible absente ET sans moyen de l'obtenir (④, §8)


@dataclass(frozen=True)
class Impasse:
    """Un trou de gameplay signalé. `facteur` = le facteur limitant non résolu ;
    `cause` = l'un des trois types ci-dessus ; `cible` = la plante/plot concerné."""

    facteur: str
    cause: str
    cible: str


def cause_pour(facteur: str, regles: list) -> str:
    """Détermine la CAUSE d'une impasse quand aucune règle du facteur n'a produit un
    geste jouable :
      - aucune règle du tout           → `geste_inexistant` (ex. `exces_eau`) ;
      - une règle `pailler` non servie → `ravitaillement_manquant` (mulch introuvable) ;
      - sinon (règle présente mais inapplicable pour une autre raison, p. ex. GATED
        au ③) → `geste_verrouille`.
    Fonction PURE ; ne consigne rien (la boucle s'en charge via trace)."""
    if not regles:
        return GESTE_INEXISTANT
    if any(r.verbe == "pailler" for r in regles):
        return RAVITAILLEMENT_MANQUANT
    return GESTE_VERROUILLE
