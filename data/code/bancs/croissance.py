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
from sim.growth import grow_plant
from fields import init_eco
from plants import AppleTree
from plants.perennials import (Fig, CherryTree, WalnutTree, OakTree, BeechTree,
                               BirchTree, HornbeamTree, FirTree, Alder, Willow,
                               HazelTree)
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


# ---------------------------------------------------------------------------
# BANC « forêt de ports » (D91, tronçon ④) — les 10 arbres procéduraux côte à
# côte pour valider CHAQUE PORT à l'œil : flèche du sapin, étalé du chêne/hêtre/
# noyer, ovoïde du cerisier/charme, bas-ramifié du figuier, élancé de l'aulne,
# pleureur du bouleau. Après la migration D91, les 9 arbres sortent du snapshot
# en SEGMENTS (comme le pommier) → le rendu C# les dessine en branches sans code
# par espèce ; ce banc est l'instrument F5 qui donne à voir les 10 silhouettes.
#
# POURQUOI une morphogénèse PURE (grow_plant direct), pas le déroulé Engine de
# `vieux_pommier` : sur UNE tuile, les 10 espèces ont des EXIGENCES HYDRIQUES
# INCONCILIABLES — l'aulne est une essence de BERGE (D61, veut le sol gorgé) et
# le figuier MÉDITERRANÉEN pourrit les pieds dans l'eau. Aucune nappe forcée
# unique ne les garde tous vivants sous le moteur écologique complet (constaté :
# aulne+figuier meurent < an 2 quelle que soit la valeur). Or ce banc observe
# l'ARCHITECTURE, pas l'équilibre écologique. On DÉROULE donc la seule
# morphogénèse — `grow_plant`, EXACTEMENT l'oracle de calibrage des sondes T1-T3
# (tests/test_croissance.py `_grow_tree`) — sur `WARMUP_ANS` ans de cycle
# saisonnier réel : chaque arbre bâtit sa charpente sans jamais subir la mort
# hydrique (ni volontaires spontanés, puisqu'aucun tick d'écosystème n'est joué).
# Déterministe (graine de forme fixe, positions fixes → même forêt à chaque
# lancement, philo #3), et sans mécanique neuve (grow_plant est le tick de
# croissance existant, appelé sans champ de lumière → apex droit, gravitropisme
# du bouleau appliqué). Golden NEUTRE : `croissance.py` n'est monté que par
# `init config="foret_ports"`, jamais pour smoke/full.
#
# Les 10 ports, dans l'ordre de lecture (grille 5×2) : rangée haute = feuillus
# étalés migrés en T1 + pommier témoin ; rangée basse = atypiques T2/T3.
FORET_PORTS = [AppleTree, CherryTree, HornbeamTree, BeechTree, WalnutTree,
               OakTree, Alder, Fig, FirTree, BirchTree, Willow, HazelTree]
# Graine de forme FIXE : la ramification hash-based (form_seed) en dérive → forêt
# reproductible d'un lancement à l'autre (philo #3).
FORET_SEED = 20260724
# An 10 = fenêtre de calibrage des sondes T1-T3 (les gabarits h10/cr10 y sont
# calés). Coût d'init modeste : morphogénèse pure O(segments), pas de LightField.
FORET_WARMUP_ANS = 10
# Disposition en grille 5 colonnes × 2 rangées, ~5 m entre arbres (couronnes
# ~2,5-3,5 m de rayon → silhouettes lisibles, léger recouvrement au bord assumé
# — le F5 zoome/panne pour isoler un port). Marge de bord pour cadrer.
FORET_NC = 5             # arbres par rangée
FORET_ESPACEMENT = 10    # plots (× 50 cm = 5 m) entre centres d'arbres
FORET_MARGE = 5          # plots de marge sur les bords


def foret_ports():
    """Banc « forêt de ports » (D91 ④) : les 12 ligneux procéduraux (pommier + noisetier + les
    10 migrés) déroulés `FORET_WARMUP_ANS` ans de morphogénèse PURE, espacés en
    grille sur une tuile fertile, pour observer chaque PORT à maturité. Instrument
    F5 : oracle visuel = l'œil de Nico (flèche, étalé, pleureur, buissonnant…).
    Monté par `init config="foret_ports"`."""
    rows = FORET_MARGE * 2 + ((len(FORET_PORTS) - 1) // FORET_NC) * FORET_ESPACEMENT
    cols = FORET_MARGE * 2 + (FORET_NC - 1) * FORET_ESPACEMENT
    tile = Tile(tile_id="FORET_PORTS", soil_type="terre",
                grid_rows=rows, grid_cols=cols)
    eco = init_eco("FORET_PORTS", rows, cols, humidite=1.2, fertilite=1.5,
                   microbiome=0.5, soil_type="terre", heterogene=True)
    for k, cls in enumerate(FORET_PORTS):
        row = FORET_MARGE + (k // FORET_NC) * FORET_ESPACEMENT
        col = FORET_MARGE + (k % FORET_NC) * FORET_ESPACEMENT
        arbre = tile.add_plant(cls, row, col)
        arbre.growth_factor = 1.0            # croissance favorable (banc)
        # Morphogénèse pure : un tick de croissance par semaine, cycle saisonnier
        # réel (1+kk) comme la sonde de calibrage. Aucun tick d'écosystème → ni
        # mort hydrique, ni volontaires (cf. docstring module).
        for kk in range(FORET_WARMUP_ANS * 52):
            grow_plant(arbre, FORET_SEED, 1 + kk)
    return monde([tile], {tile.tile_id: eco})
