"""
SYMBIOSE — bancs/acces_gestes.py
Banc « accès aux gestes » (sprint ACCÈS AUX GESTES ④, observation F5).

Le banc de bout en bout de la refonte de l'accès aux gestes
(`docs/joueur/gestes/conception_refonte_palette.md` §3) : un petit jardin où CHAQUE
porte de technique peut être franchie en jouant, sans dérouler des saisons. À
l'inverse du banc `palette_gestes`, **rien n'est ouvert d'avance** : la palette
démarre aux gestes de base, et c'est le joueur qui ouvre le reste.

Ce que le jardin offre, porte par porte :
  • GESTE DE BASE VOISIN — un coin de feuilles mortes à GLANER (trois glanages →
    compostage ; le stock de feuilles → paillage) ; des lavandes à PINCER et une
    banque de graines à SEMER (taille et semis au palier 2 → bouturer) ; n'importe
    quel plot à CREUSER (→ endiguer, dériver).
  • ATELIER — une Vigueur large : tous les outils sont payables d'emblée.
  • COURRIER — départ en fin d'été (`BANC_WEEK_DEPART`), quand les jalons de saison
    des lettres sont passés. Le jardin comble déjà trois désirs : un pommier bien en
    tige (Augustin → greffe), trois haricots (Gaston → palissage), des phacélies en
    fleur (Bertrand → essaim). Basilics et tomates sont semés pour les désirs à récolte (pas mûrs à
    l'ouverture).
  • OBSERVATION — un jasmin de trois ans pousse SANS APPUI (`grimpante_sans_appui`,
    dès la semaine qui suit son survol) ; un cerisier mûr pour le merle
    (`merle_seme`). Le perchoir s'ouvre aussi par le premier tuteur planté.
    ⚠ Les haricots, semés à l'ouverture, ne servent PAS cette porte : en fin d'été
    ils mettent 32 semaines à dépasser leur hauteur autoportante [seed 42, n=1 run].
  • PAYSAGE — une ceinture posée (forêt de charmes à l'est, contre la tuile) :
    sans elle, recéper n'aurait pas de cible et `eteter` ne s'ouvrirait jamais.
  • De quoi EXÉCUTER les gestes une fois ouverts : un squelette à broyer, un couple
    pommier/cerisier greffable (Rosaceae), le jasmin à palisser, des plots nus.

Les portes qui passent par le TEMPS ne sont pas instantanées : les phacélies sont
semées à l'ouverture et le merle attend les cerises. Mesuré par l'oracle, en
semaines après l'ouverture : phacélies en fleur ~10, merle ~12 [seed 42, n=1 run].
Au rythme du jeu c'est une dizaine de minutes ; en Turbo, quelques secondes.

Deux forçages, tous deux HORS TICK et étrangers au déblocage : la ceinture et la
Vigueur. Aucune maîtrise, aucun marqueur, aucun geste n'est posé ici.
Pure COMPOSITION de l'état moteur → golden NEUTRE (jamais monté pour smoke/full).
Oracle : `tests/bancs/test_acces_gestes.py`.
"""
from __future__ import annotations

from constants import PLOT_CM
from fields.peripherie import COTES, EST, MONDE_CM, secteur_neutre
from plants import AppleTree, Basil, Bean, CherryTree, Lavender, Phacelia, Tomato
from plants.catalogue import PLANT_CATALOGUE
from sim import vigueur as V
from sim.effects.perturbations import deposer_mort
from .base import banque_de, build_banc_tile, monde, sans_herbivorie, vieillir

NOM = "ACCES"
COTE_PLOTS = 12                     # 6×6 m
# Coin SUD-EST du monde : devant la maison à l'écran (au nord-ouest, le toit la cache).
ORIGINE_CM = MONDE_CM - COTE_PLOTS * PLOT_CM
COTE_FORET = EST                    # le bord que la tuile touche, lu par l'oracle

# (ligne, colonne) des sujets. Lus par l'oracle : une seule source.
LAVANDES = tuple((r, 0) for r in range(6))          # à pincer, couper, bouturer
POMMIER = (2, 4)                                    # porte-greffe, « bien en tige »
CERISIER = (8, 8)                                   # greffon, et cerises du merle
HARICOTS = tuple((r, 3) for r in (5, 6, 7))         # désir de Gaston
PHACELIES = tuple((10, c) for c in range(2, 7))     # en fleur → essaim
BASILICS = tuple((4, c) for c in range(6, 10))      # désir d'Amélie
TOMATES = tuple((6, c) for c in range(6, 11))       # désir d'Odette
SQUELETTE = (11, 0)                                 # bois mort à broyer
LITIERE = tuple((r, c) for r in (6, 7) for c in (0, 1, 2))     # feuilles à glaner
JASMIN = (0, 6)                                     # sarmenteux LIBRE : observation, puis palissage
PLOT_NU = (9, 1)                                    # creuser, poser, semer

AGE_POMMIER = 6.0
AGE_CERISIER = 15.0
AGE_JASMIN = 3.0
MASSE_FEUILLES = 1.5                # par plot de litière : une dose de mulch au moins
RONDELLES_POLLINISATEUR = 3         # sans butineurs, pas de cerises (cf. `nucleation`)
VIGUEUR_BANC = 3000.0               # tout l'Atelier d'un coup, et les gestes ensuite
GRAINES_PAR_ESPECE = 8              # semis au palier 2 = six semis réussis ; on en laisse
BANQUE = ("tournesol", "basilic", "tomate", "haricot", "phacelie")
# Forêt de charmes à l'est : le charme rejette de souche, il se recèpe.
FORET = {"type": "foret", "essence": "charme",
               "hauteur_canopee": 1800.0, "densite_ligneuse": 0.9}


def acces_gestes():
    tuile, eco = build_banc_tile(NOM, "terre", COTE_PLOTS, COTE_PLOTS,
                                 ORIGINE_CM, ORIGINE_CM,
                                 humidite=1.2, fertilite=1.1, microbiome=0.6)
    for r, c in LAVANDES:
        lav = tuile.add_plant(Lavender, r, c)
        lav.current_stage = len(Lavender.growth_stages) - 1
        vieillir(lav, 2.0)
    vieillir(tuile.add_plant(AppleTree, *POMMIER), AGE_POMMIER)
    vieillir(tuile.add_plant(CherryTree, *CERISIER), AGE_CERISIER)
    for cls, plots in ((Bean, HARICOTS), (Phacelia, PHACELIES),
                       (Basil, BASILICS), (Tomato, TOMATES)):
        for r, c in plots:
            tuile.add_plant(cls, r, c)
    vieillir(tuile.add_plant(PLANT_CATALOGUE["jasmin"], *JASMIN), AGE_JASMIN)
    # Un vieux pommier mort, debout : le bois que `broyer` réclame.
    mort = tuile.add_plant(AppleTree, *SQUELETTE)
    vieillir(mort, AGE_POMMIER)
    mort.vitalite = 0.0
    deposer_mort(mort, eco)
    # Le coin de feuilles mortes : litière TENDRE, celle que `glaner` ramasse.
    for r, c in LITIERE:
        eco.deposer_litiere(r, c, "feuille", MASSE_FEUILLES)
    for _ in range(RONDELLES_POLLINISATEUR):
        tuile.stakes[0].add("pollinisateur")
    # Comme `nucleation` : sans ce garde l'herbivorie tue le cerisier en quelques
    # semaines (D127). Les bêtes restent là, seule leur morsure est coupée.
    sans_herbivorie(eco)
    return monde([tuile], {tuile.tile_id: eco}, banque=banque_de(*BANQUE, par_espece=GRAINES_PAR_ESPECE))


def ceinture_foret() -> list[dict]:
    """Ceinture neutre partout, sauf une charmaie à l'est. Pure, sans tirage."""
    ceinture = [secteur_neutre(cote) for cote in COTES]
    ceinture[COTES.index(COTE_FORET)].update(FORET)
    return ceinture


def post_init(game_state: dict, player: str) -> None:
    """POSE la ceinture (la fabrique ne porte pas `game_state`) et élargit la
    Vigueur du joueur. Rien d'autre : ni maîtrise, ni marqueur, ni geste — c'est
    tout l'objet du banc. Hors tick → golden intact (jamais appelé pour smoke/full)."""
    game_state["ceinture"] = ceinture_foret()
    etat = V.ensure_player(game_state, player)
    etat["max_base"] = etat["courante"] = VIGUEUR_BANC
