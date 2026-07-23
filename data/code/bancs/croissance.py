"""
SYMBIOSE — bancs/croissance.py
Banc d'observation de l'ARCHITECTURE LIGNEUSE (sprint lisibilité ligneuse, D90).

But : donner à voir la SILHOUETTE d'un vieux pommier — tronc épais net,
charpentières marquées, brindilles fines et feuillues — pour juger à l'œil le
nouveau modèle d'épaisseur (tronçon ① : pipe model + croissance secondaire
saturante bornée par `girth_max_cm`) et caler le rendu (facteur de largeur de
trait, tronçon ②). C'est l'instrument qui remplace l'observation fortuite du
« baobab » sur la carte `full`.

Particularité vs les autres bancs : la silhouette d'un vieil arbre n'est pas un
état FORÇABLE en une passe (comme un signe foliaire pré-chargé). Elle est le
produit de DÉCENNIES de morphogénèse — la TOPOLOGIE de segments (ramification,
nb de terminaux par sous-arbre) se construit tick après tick, et c'est elle que
le pipe model lit pour l'amincissement. On DÉROULE donc un Engine local au moment
de la fabrique (`WARMUP_ANS` ans) pour bâtir la couronne, puis on renvoie le monde
DÉJÀ vieilli. Le pommier isolé mourrait de soif en ~5 ans (racines concentrées,
cf. AppleTree.foliage_halfwidth) : on MAINTIENT la nappe à chaque tick (forçage de
condition, exactement l'esprit d'un banc, cf. base.py) pour qu'il atteigne son
grand âge. Coût d'init ~40 s (one-shot, instrument d'observation — assumé).

Golden NEUTRE : `croissance.py` est au niveau de `main.py`, les couches basses ne
l'importent jamais ; ce banc n'est monté que par `init config="vieux_pommier"`,
jamais pour `smoke`/`full` (cf. cmd_init).

Lancement F5 : côté Godot, `init config="vieux_pommier"`.
"""
from __future__ import annotations

from world import Tile, House
from sim.engine import Engine
from fields import init_eco
from plants import AppleTree
from .base import monde

# Années de morphogénèse déroulées à l'init pour bâtir la couronne. À ~15 ans la
# croissance secondaire saturante est déjà à ~93 % de `girth_max` (collet ~17 cm)
# et l'arbre a atteint son plafond de segments (MAX_SEGMENTS) → silhouette de vieil
# arbre pleinement lisible. Levier de coût d'init (~2,7 s/an) : baisser pour un
# lancement plus rapide, monter pour un tronc au plafond exact de `girth_max`.
WARMUP_ANS = 15
# Nappe maintenue (forçage de banc) : humidité élevée re-posée à chaque tick pour
# que le pommier à racines concentrées survive ses décennies au lieu de mourir de
# soif à ~5 ans. Le sol reste par ailleurs le sol vivant normal (le banc ne truque
# que l'eau, la variable qui tue l'arbre isolé).
NAPPE = 2.0
# Position centrale sur une tuile généreuse : l'arbre a de la place pour étaler sa
# couronne, cadré au centre pour l'observation.
PLOT = (4, 4)


def vieux_pommier():
    """Banc « vieux pommier » (D90) : un unique pommier déroulé WARMUP_ANS ans de
    morphogénèse sur une tuile fertile et humide, pour observer sa silhouette
    ligneuse âgée (tronc borné par girth_max, brindilles fines, taper du pipe
    model). Instrument de calibrage visuel du tronçon ① (moteur) + ② (rendu) —
    aucune mécanique nouvelle, pur déroulé de l'état existant. Oracle visuel = F5."""
    tile, eco = build_and_grow()
    return monde([tile], {tile.tile_id: eco})


def build_and_grow():
    """Compose la tuile + le pommier, puis DÉROULE WARMUP_ANS ans (nappe maintenue).
    Extrait pour être réutilisable par un éventuel oracle / diag hors serveur."""
    tile = Tile(tile_id="POMMIER", soil_type="terre", grid_rows=8, grid_cols=8)
    eco = init_eco("POMMIER", 8, 8, humidite=NAPPE, fertilite=1.5,
                   microbiome=0.5, soil_type="terre", heterogene=True)
    arbre = tile.add_plant(AppleTree, *PLOT)
    game_state = {"tiles": [tile], "eco": {"POMMIER": eco}, "scores": {},
                  "current_player": "joueur_1", "week": 1, "log": [],
                  "house": House()}
    engine = Engine(game_state)
    for _an in range(WARMUP_ANS):
        for _sem in range(52):
            eco.humidite.fill(NAPPE)   # forçage : la nappe ne se vide pas
            engine.tick_semaine()
            game_state["log"].clear()  # borne la mémoire du log pendant le déroulé
            if not arbre.is_alive:      # garde-fou : arrêt propre si l'arbre meurt
                return tile, eco
    return tile, eco
