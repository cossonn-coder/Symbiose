# SYMBIOSE — tools/jardinier_auto/diagnostic.py
# Étape 2 de la boucle (§3.2) : identifier le FACTEUR LIMITANT dominant d'une
# plante, au sens de la loi du minimum de Liebig (§1) — la croissance est bornée
# par la ressource la plus déficitaire, pas par la somme. L'automate lève CE
# facteur-là et lui seul.
#
# Table complète (§5), du plus au moins prioritaire (l'ORDRE des tests EST la
# dominance de Liebig — première contrainte rencontrée = facteur retenu) :
#   - "hydrique"            : sol trop sec           → arroser / pailler
#   - "exces_eau"           : sol détrempé           → (AUCUN geste → impasse §7)
#   - "ombrage"             : lumière basse + voisin → tailler le voisin
#   - "concurrence_ferale"  : férales dans les racines → deraciner (désherbage §4)
#   - "sol_compacte"        : structure basse        → grelinette
#   - "sol_nu"              : couverture basse        → pailler (ravitaillement §5)
#   - "organe_mur"          : cycle mûr (opportunité) → recolter
#
# Les SEUILS sont des constantes nommées, à CALIBRER après les premiers bancs (§5,
# banc ⑤) — ce ne sont PAS des vérités écologiques figées.

from __future__ import annotations

from .perception import Perception

# Humidité de sol [0,3] : sous ce seuil = déficit hydrique ; au-dessus de HAUTE =
# excès d'eau (asphyxie racinaire). 0.8 / 2.7 = repères provisoires (sol franc).
HUMIDITE_BASSE = 0.8
HUMIDITE_HAUTE = 2.7

# Lumière reçue [0,1] (1 = plein soleil) sous laquelle on juge la plante ombragée.
LUMIERE_BASSE = 0.5

# Structure du sol [0,1] sous laquelle le sol est jugé compacté (racines bridées).
STRUCTURE_BASSE = 0.35

# Paillage [0,1] sous lequel le sol est jugé NU (évaporation, levée férale libre).
PAILLAGE_BAS = 0.15

# Maturité [0,1] à partir de laquelle un organe est jugé récoltable.
MATURITE_MUR = 0.95


def facteur_limitant(percept: Perception) -> str | None:
    """Renvoie le nom du facteur limitant dominant, ou None si rien à faire.
    Ordre de dominance (Liebig, §5) : l'eau (déficit ou excès) bride la croissance
    en premier ; vient ensuite la lumière (ombrage), puis la concurrence, puis
    l'état du sol (compaction, couverture), et enfin l'OPPORTUNITÉ de récolte —
    une plante saine et mûre bascule sur `organe_mur`. Fonction PURE d'une
    perception (aucun effet de bord, aucun accès au monde)."""
    if percept.humidite < HUMIDITE_BASSE:
        return "hydrique"
    if percept.humidite > HUMIDITE_HAUTE:
        return "exces_eau"
    if percept.lumiere < LUMIERE_BASSE and percept.voisin_ombrageant is not None:
        return "ombrage"
    if percept.ferale_cible is not None:
        return "concurrence_ferale"
    if percept.structure < STRUCTURE_BASSE:
        return "sol_compacte"
    if percept.paillage < PAILLAGE_BAS:
        return "sol_nu"
    if percept.maturite >= MATURITE_MUR:
        return "organe_mur"
    return None
