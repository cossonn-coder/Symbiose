# SYMBIOSE — tools/jardinier_auto/trace.py
# Le JOURNAL déterministe (§6) — livrable central du sprint, réutilisé partout
# (banc, onglet objectifs, vue F5). Tronçon ① = version MINIMALE : une entrée par
# geste joué, {semaine, tile_id, cible, facteur_limitant, geste, resultat}.
# Les CONSÉQUENCES (déverrouillages, paliers, morts) s'ajoutent au ③, le rapport
# agrégé au ⑤.
#
# Le journal vit sous `game_state["automate_journal"]` (liste, opt-in). Il n'est
# JAMAIS lu par le tick → golden intact (H2). Chaque entrée est un dict de types
# simples → sérialisable JSON tel quel.

from __future__ import annotations

CLE_JOURNAL = "automate_journal"


def journal(game_state: dict) -> list:
    """Le journal de l'automate dans `game_state` (créé à la volée, opt-in)."""
    return game_state.setdefault(CLE_JOURNAL, [])


def entree(semaine: int, tile_id: str, cible: str, facteur: str,
           geste: str, resultat: str) -> dict:
    """Construit une entrée de journal pour un GESTE (dict JSON-sérialisable, ordre
    stable). `categorie="geste"` distingue les gestes des impasses au même journal."""
    return {
        "categorie": "geste",
        "semaine": semaine,
        "tile_id": tile_id,
        "cible": cible,
        "facteur_limitant": facteur,
        "geste": geste,
        "resultat": resultat,
    }


def entree_impasse(semaine: int, tile_id: str, cible: str, facteur: str,
                   cause: str) -> dict:
    """Construit une entrée de journal pour une IMPASSE (§7) — un facteur limitant
    diagnostiqué sans geste-réponse applicable (« trou de gameplay »). `categorie=
    "impasse"` la sépare des gestes ; `cause` = type d'impasse (impasses.py)."""
    return {
        "categorie": "impasse",
        "semaine": semaine,
        "tile_id": tile_id,
        "cible": cible,
        "facteur_limitant": facteur,
        "cause": cause,
    }


def consigner(game_state: dict, entry: dict) -> None:
    """Ajoute une entrée au journal (append → ordre chronologique déterministe)."""
    journal(game_state).append(entry)
