# SYMBIOSE — tools/jardinier_auto/diagnostic.py
# Étape 2 de la boucle (§3.2) : identifier le FACTEUR LIMITANT dominant d'une
# plante, au sens de la loi du minimum de Liebig (§1) — la croissance est bornée
# par la ressource la plus déficitaire, pas par la somme. L'automate lève CE
# facteur-là et lui seul.
#
# Tronçon ① : deux facteurs suffisent à valider la boucle.
#   - "hydrique"    : le sol est trop sec sous la plante → arroser (②B pailler).
#   - "organe_mur"  : le cycle est mûr → récolter (opportunité, non un manque).
# La table complète (lumière, compaction, concurrence férale…) arrive au ②.
#
# Les SEUILS sont des constantes nommées en tête de fichier, à CALIBRER après les
# premiers bancs (§5) — ce ne sont pas des vérités écologiques figées.

from __future__ import annotations

from .perception import Perception

# Humidité de sol [0,3] sous laquelle on juge la plante en déficit hydrique.
# 0.8 = repère provisoire (sol franc modérément sec) ; à affiner au banc ⑤.
HUMIDITE_BASSE = 0.8

# Maturité [0,1] à partir de laquelle un organe est jugé récoltable.
MATURITE_MUR = 0.95


def facteur_limitant(percept: Perception) -> str | None:
    """Renvoie le nom du facteur limitant dominant, ou None si rien à faire.
    Ordre de dominance (Liebig) : le déficit hydrique BRIDE la croissance et
    passe avant l'opportunité de récolte ; une plante bien arrosée et mûre bascule
    sur `organe_mur`. Fonction pure d'une perception."""
    if percept.humidite < HUMIDITE_BASSE:
        return "hydrique"
    if percept.maturite >= MATURITE_MUR:
        return "organe_mur"
    return None
