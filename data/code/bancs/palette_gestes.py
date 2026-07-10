"""
SYMBIOSE — bancs/palette_gestes.py
Banc d'essai PALETTE DE GESTES (sprint du même nom, tronçon ⑤, observation F5).

Instrument pour VOIR de ses yeux les gestes savants de la palette (④) et les
MACROS (⑤) à l'œuvre, sans dérouler des années de maîtrise. Une seule tuile
plantée de sujets MÛRS, prêts pour les deux gestes que le sprint a ajoutés :
  · BOUTURE (②) — un massif de LAVANDES adultes (bouturable, au dernier stade,
    vigoureuses) : le joueur clique une lavande puis un plot nu → un clone s'y
    enracine. Le geste `bouturer` est OUVERT d'emblée (post-init force la maîtrise
    `taille`/`semis`, cf. `post_init` ci-dessous).
  · GREFFE (③) — un POMMIER et un CERISIER adultes (tous deux greffables, MÊME
    famille Rosaceae → `species_compatible` vrai) : le joueur clique le cerisier
    (greffon) puis le pommier (porte-greffe) → le pommier adopte l'identité aérienne
    du cerisier en gardant son établissement. `greffer` OUVERT d'emblée (maîtrise
    `greffe` forcée).
  · MACRO (⑤) — le joueur enregistre p. ex. `planter → pailler → arroser` (tous
    de famille de cible « plot », donc COHÉRENTE) et la rejoue d'un clic sur un plot :
    la VUE réémet 3 gestes normaux à la MÊME cible, chacun paie sa Vigueur (philo #1).
    Rien à composer ici pour la macro : elle vit dans l'état joueur `palette`, que la
    vue écrit via la commande `palette` (0.5.26) — le banc offre juste des plots nus
    et une banque garnie pour AVOIR de quoi planter/pailler/arroser.

Pure COMPOSITION de l'état moteur (plantes mûres + banque de graines + forçage de
l'état JOUEUR au post-init) — AUCUNE mécanique nouvelle → golden NEUTRE (cette
fabrique n'est JAMAIS montée pour smoke/full, cf. `cmd_init`). Toutes les espèces
employées sont déjà au catalogue et à l'encyclopédie (règle catalogue/voix).

Deux sujets ligneux fruitiers (pommier/cerisier, `maturity_years`=5) : on démarre
MI-PRINTEMPS (`BANC_WEEK_DEPART`) et on les PRÉ-VIEILLIT à maturité (patron du
verger "full" de `cmd_init` + `vieillir`) pour qu'ils soient greffables tout de
suite, sans dérouler cinq ans en Turbo.
"""
from __future__ import annotations

from plants import Lavender, AppleTree, CherryTree
from sim.seeds import PlayerSeedBank, Seed
from sim import maitrise as M
from sim.actions import deblocage as DEBL
from .base import build_banc_tile, monde, vieillir

# Massif de lavandes bouturables : une petite grille dense laisse de la place aux
# plots nus (bouture cible / macros plant-pailler-arroser). 6×6 = 36 plots.
PAL_ROWS = PAL_COLS = 6

# Graines de départ pour exercer la MACRO plant→paille→arrose (banque garnie du banc,
# ≠ banque smoke vide). Espèces déjà au catalogue, plantables sur un plot nu.
BANQUE_PALETTE = ("tournesol", "basilic", "tomate")


def _adulte(plant, cls, ans: float) -> None:
    """Porte une plante fraîchement posée à son DERNIER stade + son âge de maturité :
    condition du gate de bouture (`clonal._mature` = dernier stade) et âge greffable
    des ligneux. `current_stage` est un attribut simple ; `vieillir` aligne âge en
    années ET semaines (patron du verger "full")."""
    plant.current_stage = len(cls.growth_stages) - 1
    vieillir(plant, ans)


def palette_gestes():
    """Banc « palette de gestes » (⑤, observation F5) : lavandes bouturables + couple
    pommier/cerisier greffable + plots nus et banque garnie pour les macros. Pas
    d'oracle à seuil : instrument d'observation, calibrage à l'œil par Nico."""
    tile, eco = build_banc_tile("PALETTE", "terre", PAL_ROWS, PAL_COLS,
                                humidite=1.2, fertilite=1.1, microbiome=0.6)
    # Massif de lavandes adultes bouturables (colonne de gauche → laisse la moitié
    # droite de la tuile en plots NUS pour poser les boutures et jouer les macros).
    for r in range(PAL_ROWS):
        lav = tile.add_plant(Lavender, r, 0)
        if lav is not None:
            _adulte(lav, Lavender, 2.0)
    # Couple greffable Rosaceae : cerisier = greffon, pommier = porte-greffe (même
    # famille → compatible). Pré-vieillis à `maturity_years` comme le verger "full".
    ap = tile.add_plant(AppleTree, 1, 3)
    if ap is not None:
        _adulte(ap, AppleTree, float(AppleTree.maturity_years))
    ch = tile.add_plant(CherryTree, 3, 3)
    if ch is not None:
        _adulte(ch, CherryTree, float(CherryTree.maturity_years))
    banque = PlayerSeedBank()
    for sp in BANQUE_PALETTE:
        banque.add(Seed(species=sp))
    return monde([tile], {tile.tile_id: eco}, banque=banque)


def post_init(game_state: dict, player: str) -> None:
    """Forçage de l'état JOUEUR APRÈS construction du moteur (le tuple de fabrique ne
    porte pas `game_state`). Ouvre d'emblée les gestes savants du sprint pour que la
    palette Godot les affiche sans jouer jusqu'à la maîtrise réelle :
      · maîtrise `taille`+`semis` ≥ 2 → ouvre `bouturer` (voie savoir composée, ①) ;
      · maîtrise `greffe` ≥ 1        → ouvre `greffer`.
    Puis `evaluer_deblocages` matérialise l'ouverture dans `gestes_debloques`. Écriture
    bornée à l'état joueur (opt-in, hors tick) → golden intact (jamais appelé pour
    smoke/full). C'est du forçage de BANC, assumé — jamais un chemin de jeu normal."""
    st = M.ensure_player_maitrise(game_state, player)
    for objet, palier in (("taille", 2), ("semis", 2), ("greffe", 1)):
        st["objets"][objet] = {"palier": palier, "preuves": 0}
    DEBL.evaluer_deblocages(game_state, player)
