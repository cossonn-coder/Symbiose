"""
SYMBIOSE — bancs/peripherie.py
Banc d'essai PÉRIPHÉRIE (sprint D73, tronçon ⑦, observation F5).

Instrument pour VOIR la ceinture et la manipuler tout de suite, sans attendre qu'un
seed distribue les quatre motifs (ils sont rares ensemble, philo #7) ni jouer des
heures pour s'outiller. Deux forçages, tous deux HORS TICK :

  • une ceinture **contrastée** posée à la main — falaise au NORD, rivière à l'EST,
    forêt dense au SUD, friche à l'OUEST. Un motif par bord, donc les quatre rendus
    du décor d'un seul regard (ce que le banc F10 du C# faisait en aveugle, mais
    cette fois c'est la VÉRITÉ MOTEUR qu'on regarde) ;
  • les trois outils de paysage **déjà en poche** + l'expérience que les gestes du ⑤
    réclament, pour que les sept gestes soient cliquables immédiatement.

Le SUD porte la forêt parce que c'est le seul bord dont l'ombre entre dans le
jardin (49°N : longue en hiver, courte en été) et le seul où l'on sente l'abri et
la turbulence de rafale. Une tuile est posée CONTRE chaque bord : sans contact, les
flux de bordure (pluie de graines, nappe de berge, bois tombé, colluvions
d'érosion) ne touchent rien — `plots_de_bord` ne rend RIEN à une tuile lointaine, et
on croirait à un bug alors que c'est la géométrie.

Pure COMPOSITION de l'état moteur (tuiles + état de ceinture + état joueur au
post-init) — AUCUNE mécanique nouvelle → golden NEUTRE : cette fabrique n'est
jamais montée pour smoke/full (cf. `cmd_init`).
"""
from __future__ import annotations

from fields.peripherie import COTES, MONDE_CM, secteur_neutre
from sim.actions import deblocage as DEBL
from .base import build_banc_tile, monde

# Une tuile par bord, petite (6×6 = 36 plots, 300 cm de côté) : on observe des
# BORDS, pas une luxuriance. 4 × 36 = 144 plots — léger, le tick reste rapide.
PER_ROWS = PER_COLS = 6
_COTE_CM = PER_COLS * 50.0                     # 6 plots × PLOT_CM
_MILIEU = (MONDE_CM - _COTE_CM) / 2.0          # centrée le long du bord

# Chaque tuile est COLLÉE à son bord (origine 0 ou `MONDE_CM − côté`) : c'est la
# condition pour que les flux de bordure l'atteignent (portées de 100 à 400 cm).
# La maison par défaut occupe le carré central 600→1400 cm : aucune collision.
_TUILES = (
    ("BORD_NORD",  "terre",  _MILIEU, 0.0),
    ("BORD_EST",   "argile", MONDE_CM - _COTE_CM, _MILIEU),
    ("BORD_SUD",   "terre",  _MILIEU, MONDE_CM - _COTE_CM),
    ("BORD_OUEST", "sable",  0.0, _MILIEU),
)

# La ceinture contrastée, secteur par secteur. Valeurs prises dans les plages du
# générateur (`fields/peripherie.py`) — on ne sort pas de ce que le terrain sait
# produire, on choisit juste un tirage lisible.
#   · NORD falaise 9 m  → ombre du matin/soir, et de quoi `entailler` six fois.
#   · EST rivière +40   → ligne d'eau HAUTE (max du générateur) : la berge se gorge,
#                         `deriver` doit se sentir tout de suite.
#   · SUD forêt 18 m à 0.90 de densité, essence CHARME → dense (ombre d'hiver franche,
#                         turbulence de mur) ET qui REJETTE de souche : `receper` y
#                         est un flux renouvelable, quand `abattre` y est 30 ans.
#                         (Le contre-exemple pédagogique — hêtre/bouleau, dont
#                         recéper EST abattre — se teste en changeant cette chaîne.)
#   · OUEST friche 0.20 → semencière (pluie de graines pionnière), sans hauteur.
_CEINTURE = (
    {"type": "falaise", "altitude_relative": 900.0},
    {"type": "riviere", "ligne_eau": 40.0},
    {"type": "foret", "essence": "charme",
     "hauteur_canopee": 1800.0, "densite_ligneuse": 0.90},
    {"type": "friche", "densite_ligneuse": 0.20},
)

# Marqueurs d'action POSÉS d'emblée. Trois sont des outils (`sim/outils.py`) ; les
# deux autres sont de l'EXPÉRIENCE (`GESTE_UNLOCK` ouvre `eteter` à qui a recépé et
# `endiguer`/`deriver` à qui a creusé — la bêche n'a pas de marqueur d'outil). On
# POSE les marqueurs au lieu d'acheter : les trois outils coûtent 180 de Vigueur à
# eux seuls, pour un plafond de départ de 100.
_MARQUEURS = ("posseder_hache", "posseder_serpe", "posseder_pioche",
              "receper", "creuser")


def ceinture_contrastee() -> list[dict]:
    """Les 4 secteurs du banc (un motif par bord). Fonction PURE et déterministe :
    aucun tirage, aucune dépendance au seed — le banc doit montrer LA MÊME chose à
    chaque lancement (c'est un instrument de mesure, pas un terrain de jeu)."""
    ceinture = [secteur_neutre(cote) for cote in COTES]
    for secteur, forcage in zip(ceinture, _CEINTURE):
        secteur.update(forcage)
    return ceinture


def peripherie():
    """Banc « périphérie » (⑦, observation F5) : les 4 motifs de ceinture autour de
    4 tuiles collées aux bords. Pas d'oracle à seuil — instrument d'observation :
    Nico juge à l'œil le décor consommé du pont, l'ombre du sud, et l'effet des sept
    gestes de paysage (clairière, trogne, ligne d'eau, entaille, éboulis)."""
    tiles, ecos = [], {}
    for nom, sol, ox, oy in _TUILES:
        tile, eco = build_banc_tile(nom, sol, PER_ROWS, PER_COLS, ox, oy,
                                    humidite=1.2, fertilite=1.0, microbiome=0.6)
        tiles.append(tile)
        ecos[tile.tile_id] = eco
    return monde(tiles, ecos)


def post_init(game_state: dict, player: str) -> None:
    """Forçage APRÈS construction du moteur (la fabrique ne porte pas `game_state`) :
    POSE la ceinture contrastée dans `game_state["ceinture"]` — la clé que le tick lit
    aux étapes 1c/1c-bis/2/2a/2a-bis/2e/2e-bis/14 — et ouvre les sept gestes de
    paysage en posant leurs marqueurs. Écriture bornée à l'init (hors tick) → golden
    intact (jamais appelé pour smoke/full). Forçage de BANC assumé : en jeu, les
    outils s'achètent à l'Atelier et la ceinture vient du seed."""
    game_state["ceinture"] = ceinture_contrastee()
    for marqueur in _MARQUEURS:
        DEBL.marquer_action(game_state, player, marqueur)
    DEBL.evaluer_deblocages(game_state, player)
