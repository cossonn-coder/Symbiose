"""
SYMBIOSE — tests/bancs/oracle.py
Cadre d'ORACLE des bancs d'essai (sprint dédié, tronçon ①).

Un oracle monte un banc via SA fabrique (`bancs.BANCS`), fait tourner N semaines,
puis lit les SIGNES foliaires EXACTEMENT comme la vue les reçoit — via
`sim.semiologie.leaf_symptoms`, la même fonction que `serialize._snapshot` appelle
(serialize.py:117). Lire au même endroit que la vue, c'est ce qui fait de l'oracle
un INSTRUMENT DE TRI pour D47 : si l'oracle voit le signe mais que l'écran reste
muet, le bug est dans le RENDU C#, pas dans la carte ni le moteur.

Déterministe (seed fixe du serveur). Lecture pure : aucune écriture moteur.
"""
from __future__ import annotations

from bancs import BANCS
from sim.engine import Engine, saison_de
from sim import semiologie

# Seed déterministe par défaut du serveur (cf. cmd_init / golden) : le banc doit
# donner le MÊME résultat que ce que verra Godot à `init config="<banc>"`.
SEED = 0x5AB1057E


def run_banc(nom: str, semaines: int):
    """Monte le banc `nom`, simule `semaines` ticks, renvoie `(game_state, engine)`.
    Reproduit le câblage minimal de `cmd_init` (mêmes clés `game_state`) pour que
    l'état soit bit-identique à celui du serveur."""
    if nom not in BANCS:
        raise KeyError(f"banc inconnu : {nom!r} (connus : {', '.join(sorted(BANCS))})")
    tiles, ecos, house, banque = BANCS[nom]()
    game_state = {
        "tiles": tiles, "eco": ecos, "scores": {},
        "current_player": "joueur_1", "week": 1, "log": [],
        "house": house, "seed": SEED, "player_seed_bank": banque,
    }
    engine = Engine(game_state)
    for _ in range(semaines):
        engine.tick_semaine()
        game_state["log"].clear()
    return game_state, engine


def signes_du_plot(game_state, plant) -> set[str]:
    """Set des CAUSES de symptômes foliaires d'une plante, lues comme la vue.
    Retrouve l'`eco` de la tuile portant la plante (la position est locale à la
    tuile), recalcule la saison de la semaine COURANTE, et délègue à
    `semiologie.leaf_symptoms` (source unique partagée avec le snapshot)."""
    eco = _eco_de(game_state, plant)
    week_in_year = ((game_state["week"] - 1) % 52) + 1
    saison = saison_de(week_in_year)
    return {s["cause"] for s in semiologie.leaf_symptoms(plant, eco, saison)}


def premiere_plante(game_state):
    """La 1ʳᵉ plante du monde (les bancs en posent en général une seule — le sujet
    d'observation). Pratique pour les oracles mono-plante."""
    for tile in game_state["tiles"]:
        for p in tile.plants:
            return p
    raise AssertionError("le banc n'a posé aucune plante")


def _eco_de(game_state, plant):
    """Retrouve l'EcoFields de la tuile qui contient `plant`."""
    for tile in game_state["tiles"]:
        if plant in tile.plants:
            return game_state["eco"][tile.tile_id]
    raise AssertionError("plante introuvable dans les tuiles du banc")
