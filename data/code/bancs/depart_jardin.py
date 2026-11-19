"""
SYMBIOSE — bancs/depart_jardin.py
Banc d'essai DÉPART DU JARDIN (D140 C, sprint départ du jardin ⑥, observation F5).

Le calendrier des tendres s'apprend par le froid, pas par une règle (philo #6). Ce banc
pose côte à côte, au sud de la maison, ce qu'un jardinier vit au printemps :

  (1) POT DANS LA MAISON (témoin) — un godet de tomate au rebord de la façade sud, à
      l'intérieur : au chaud jour et nuit, à la lumière d'une fenêtre (`world/interieur`).
      Il y reste : il pousse lentement, ne gèle jamais.
  (2) POT À REPIQUER — un second godet de tomate, à côté du premier : c'est celui que
      Nico repique LUI-MÊME (geste `repiquer`) une fois les nuits douces (mi-juin au
      seed 42, ⑤), au plot marqué `CIBLE_REPIQUAGE`.
  (3) POT DEHORS — un godet de tomate posé sur la tuile, hors de la maison.
  (4) TOMATE REPIQUÉE TROP TÔT — sortie de son godet à l'ouverture (début avril),
      mise en pleine terre par la façade `repiquer` : les nuits de la gelée tardive
      la tuent, et le carnet le DIT (cause `gel` ou `froid`, mesuré par l'oracle).
  (5) GRAINES SEMÉES — deux graines de haricot déposées en terre à l'ouverture : elles
      attendent, sans lever, que le sol se réchauffe (`bell(T_sol)`), puis lèvent.

📖 Le banc ne s'accélère PAS : il ouvre au début de la gelée tardive (s3) et laisse la
météo seedée faire. C'est le scénario du jeu, en petit.
⚠ (3) Le pot dehors n'a pas de météo (`Container.tick` n'écrit ni T_air ni pluie hors
de la maison, constat ④ c, pré-existant) : il ne gèle pas non plus. Le banc le montre
tel quel — c'est une limite connue, pas une scène truquée.

Pure COMPOSITION d'un état : golden NEUTRE (une fabrique de banc n'est jamais montée
pour smoke/full). Zéro RNG (philo #3).
"""
from __future__ import annotations

from plants import PLANT_CATALOGUE
from fields.seedbank import GrainEnAttente
from sim.actions.conteneurs import repiquer
from sim.actions.deblocage import marquer_action, evaluer_deblocages
from sim.monde_complet import SEMAINES_EN_POT, STADE_PLANT, VOLUME_GODET
from world import make_container, planter_dans
from .base import build_banc_tile, monde, banque_de, sans_herbivorie

NOM = "DEPART"
# Tuile au sud de la maison (emprise 600..1400, mur sud à y = 1400 ; chemin de 50 cm).
OX, OY = 600.0, 1450.0
RANGS, COLS = 5, 16
SEMAINE_OUVERTURE = 3          # début avril : la gelée tardive est devant (fenêtre 2-9)
# Godets dans la maison (rebord de la façade sud, comme `monde_complet.POTS_INTERIEUR`).
POT_TEMOIN = (900.0, 1375.0)
POT_A_REPIQUER = (1000.0, 1375.0)
# Pot dehors : sur la tuile, côté est (plot (2, 14) → centre monde).
POT_DEHORS = (OX + 14 * 50 + 25, OY + 2 * 50 + 25)
TROP_TOT = (2, 2)              # plot de la tomate repiquée à l'ouverture
CIBLE_REPIQUAGE = (2, 6)       # plot libre où Nico repique le godet (2)
GRAINES = ((2, 10), (2, 11))   # haricots semés à l'ouverture
ESPECE_GRAINE = "haricot"


def depart_jardin():
    """Banc « départ du jardin » (⑥) : la tuile seule ; les pots et la tomate repiquée
    trop tôt sont posés au `post_init` (il faut l'état joueur pour la façade)."""
    tile, eco = build_banc_tile(NOM, "terre", RANGS, COLS, OX, OY,
                                humidite=1.2, fertilite=1.0, microbiome=0.4)
    sans_herbivorie(eco)          # le froid seul
    for r, c in GRAINES:
        tile.grains_en_attente.setdefault((r, c), []).append(
            GrainEnAttente(species=ESPECE_GRAINE, cultive=True, player="joueur_1",
                           semaine_depot=SEMAINE_OUVERTURE - 1))
    return monde([tile], {NOM: eco}, banque=banque_de("tomate", "haricot", par_espece=3))


def _godet(game_state: dict, x: float, y: float, cle: str):
    """Un godet de 2 L de terreau, semé au chaud `SEMAINES_EN_POT` semaines avant
    l'ouverture (même pousse tickée que les godets du monde `full`, ④)."""
    ctn = make_container("pot", "terreau", VOLUME_GODET, x, y,
                         container_id=f"banc_{cle}_{int(x)}_{int(y)}")
    plant = planter_dans(ctn, PLANT_CATALOGUE[cle])
    plant.current_stage = STADE_PLANT
    debut = SEMAINE_OUVERTURE - SEMAINES_EN_POT
    for w in range(debut, SEMAINE_OUVERTURE):
        ctn.tick("printemps", game_state["seed"], w, house=game_state["house"])
    return ctn


def post_init(game_state: dict, player: str) -> None:
    """Pose les trois godets (témoin, à repiquer, dehors), repique trop tôt une
    quatrième tomate par la façade `repiquer`, ouvre les gestes de pot (« posséder
    vaut avoir posé », patron de `cmd_init`) et coupe la germination férale. Hors
    tick → golden intact."""
    game_state["feral_off"] = True
    pots = [_godet(game_state, *POT_TEMOIN, "tomate"),
            _godet(game_state, *POT_A_REPIQUER, "tomate"),
            _godet(game_state, *POT_DEHORS, "tomate")]
    trop_tot = _godet(game_state, *POT_DEHORS, "tomate")
    tile = next(t for t in game_state["tiles"] if t.tile_id == NOM)
    if repiquer(game_state, player, trop_tot, tile, *TROP_TOT) is None:
        raise RuntimeError("banc depart_jardin : tomate trop tôt non repiquée")
    game_state["containers"] = pots      # le godet vidé n'est pas gardé
    marquer_action(game_state, player, "poser_pot")
    evaluer_deblocages(game_state, player)
