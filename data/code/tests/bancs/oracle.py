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


def _monter(nom: str, week_depart: int = 1):
    """Monte le banc `nom` et renvoie `(game_state, engine)` AVANT tout tick.
    Reproduit le câblage minimal de `cmd_init` (mêmes clés `game_state`) pour que
    l'état soit bit-identique à celui du serveur.

    `week_depart` (défaut 1 = hiver, comme `cmd_init` — aucun banc existant impacté)
    choisit la SAISON d'observation : certains phénomènes n'ont de fenêtre qu'à une
    saison donnée (p.ex. la levée thermique du semis potager, qui exige un sol chaud
    → observation en plein été). C'est la couche oracle qui décide QUAND observer, le
    banc ne décrivant qu'un monde statique."""
    if nom not in BANCS:
        raise KeyError(f"banc inconnu : {nom!r} (connus : {', '.join(sorted(BANCS))})")
    tiles, ecos, house, banque = BANCS[nom]()
    game_state = {
        "tiles": tiles, "eco": ecos, "scores": {},
        "current_player": "joueur_1", "week": week_depart, "log": [],
        "house": house, "seed": SEED, "player_seed_bank": banque,
    }
    return game_state, Engine(game_state)


def run_banc(nom: str, semaines: int, week_depart: int = 1):
    """Monte le banc `nom`, simule `semaines` ticks, renvoie `(game_state, engine)`.
    `week_depart` (défaut 1) fixe la semaine/saison de départ (cf. `_monter`)."""
    game_state, engine = _monter(nom, week_depart)
    for _ in range(semaines):
        engine.tick_semaine()
        game_state["log"].clear()
    return game_state, engine


def run_banc_trace(nom: str, semaines: int, observe):
    """Comme `run_banc`, mais appelle `observe(game_state, engine)` APRÈS chaque tick
    et collecte les retours. Indispensable aux signes TRANSITOIRES, qu'un snapshot
    final raterait : p.ex. les butineurs ne sont présents que pendant la floraison,
    laquelle est retombée une fois les fruits noués. Renvoie `(game_state, engine,
    traces)`."""
    game_state, engine = _monter(nom)
    traces = []
    for _ in range(semaines):
        engine.tick_semaine()
        game_state["log"].clear()
        traces.append(observe(game_state, engine))
    return game_state, engine, traces


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


def champs_climat(game_state) -> dict:
    """Lecture MOYENNE des champs de microclimat de la 1ʳᵉ tuile : `temperature_air`,
    `temperature_sol`, `humidite`. Pour les bancs-SONDE qui s'observent par le SOL
    (couplages météo→champs) plutôt que par les signes foliaires. Lit `eco.temperature`
    (T_air, rempli uniforme par l'engine), `eco.temperature_sol` (microclimat) et
    `eco.humidite` — les mêmes champs que le snapshot et la thermique. Read-only."""
    tile = game_state["tiles"][0]
    eco = game_state["eco"][tile.tile_id]
    return {
        "temperature_air": eco.temperature.average(),
        "temperature_sol": eco.temperature_sol.average(),
        "humidite": eco.humidite.average(),
    }
