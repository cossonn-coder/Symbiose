# SYMBIOSE — tools/jardinier_auto/regles.py
# Étape 3 de la boucle (§3.3 / table §5) : à un facteur limitant, associer le
# GESTE candidat qui le relâche. Format retenu (Q2) = liste ORDONNÉE de règles
# priorisées dans ce module Python, lisible et éditable à la main — PAS de fichier
# de données externe (simplicité #2 : pas de config spéculative pour un outil de
# dev).
#
# Tronçon ① : deux règles seulement (arroser, recolter). La table complète
# (pailler, tailler, deraciner, grelinette…) et le détecteur d'impasses arrivent
# au ②. Ce sprint ne crée AUCUN geste — chaque `verbe` renvoie à une fonction
# existante de `sim.actions`.

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
# la priorité chiffrée pilote le tri de l'étape 4 (prioriser).
REGLES: list[Regle] = [
    # Récolter est FAIBLE en coût, apporte de la Vigueur et est time-sensitive
    # (un organe mûr non cueilli se dégrade) → priorité haute.
    Regle(facteur="organe_mur", verbe="recolter", cible="vivant", priorite=20),
    # Arroser lève le facteur hydrique — geste de MILIEU (philo #1), coût modéré.
    Regle(facteur="hydrique", verbe="arroser", cible="milieu", priorite=10),
]


def regle_pour(facteur: str) -> Regle | None:
    """Première règle dont le prédicat correspond au facteur, ou None (→ impasse
    au tronçon ②, quand un facteur diagnostiqué n'a aucune réponse applicable)."""
    for regle in REGLES:
        if regle.facteur == facteur:
            return regle
    return None
