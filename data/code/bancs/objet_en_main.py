"""
SYMBIOSE — bancs/objet_en_main.py
Banc « objet en main » (sprint GESTES LISIBLES ④, capture VM + observation F5).

Une tuile où chaque geste du tronçon ④ a de quoi s'exercer dès l'ouverture
(conception `docs/joueur/gestes/conception_gestes_lisibles.md` §6) :
  • une colonne de LAVANDES adultes : la plante-mère de `bouturer` (et une plante sans
    fruit, que `recolter` cueille entière) ;
  • un POMMIER et un CERISIER adultes : le greffon et le porte-greffe de `greffer` ; le
    pommier porte des fruits MÛRS et des fruits VERTS (`recolter` vise le fruit mûr) ;
  • un FRAISIER adulte qui porte des fraises mûres (fruit de port, herbacée) ;
  • un BAC de compost mûr : la source d'`epandre` ;
  • un POT posé : `deplacer_pot` le saisit, `planter` y sème d'un clic ;
  • deux rondelles `auxiliaire` sur une tige : l'habitat de `favoriser_auxiliaire`
    dessiné ;
  • une banque de graines dans le désordre (le catalogue doit la trier).

Pure COMPOSITION de l'état moteur (plantes pré-vieillies, cohortes de fruits nouées par
`nouer` puis mûries, structure, pot posé par sa façade) au post-init, hors tick → golden
NEUTRE (jamais monté pour smoke/full). Capture : `-b objet_en_main -w 0 -z 4 -c 1600,1600`.
"""
from __future__ import annotations

from fields.ecofields.litiere import Structure
from plants import AppleTree, CherryTree, Lavender
from plants.catalogue import Strawberry
from sim import vigueur as V
from sim import maitrise as M
from sim.actions import conteneurs as CONT
from sim.actions import deblocage as DEBL
from sim.engine.decompo import nouer
from sim.seeds import PlayerSeedBank, Seed
from .base import build_banc_tile, monde, sans_herbivorie, vieillir

NOM = "MAIN"
COTE = 8                        # 4×4 m
ORIGINE = (1450.0, 1450.0)
VIGUEUR_BANC = 3000.0
BANQUE = ("tournesol", "basilic", "tomate", "ail", "carotte", "bourse_pasteur")
POMMIER, CERISIER, FRAISIER = (2, 4), (5, 4), (6, 1)
BAC = (1, 7)
POT_CM = (1450.0 + 6.5 * 50.0, 1450.0 + 6.5 * 50.0)   # monde absolu, plot (6, 6)
MUR, VERT = 1.05, 0.5           # maturité d'un fruit mûr / encore vert
RONDELLES_AUX = 2


def _adulte(tuile, cls, rc, ans: float):
    pied = tuile.add_plant(cls, *rc)
    pied.current_stage = len(cls.growth_stages) - 1
    vieillir(pied, ans)
    return pied


def objet_en_main():
    tuile, eco = build_banc_tile(NOM, "terre", COTE, COTE, *ORIGINE,
                                 humidite=1.0, fertilite=1.2, microbiome=0.5)
    for r in range(0, COTE, 2):
        _adulte(tuile, Lavender, (r, 0), 2.0)
    _adulte(tuile, AppleTree, POMMIER, float(AppleTree.maturity_years) + 3.0)
    _adulte(tuile, CherryTree, CERISIER, float(CherryTree.maturity_years))
    _adulte(tuile, Strawberry, FRAISIER, 1.0)
    eco.structures.append(Structure(kind="bac", plot=BAC, compost_mur=6.0))
    for _ in range(RONDELLES_AUX):
        tuile.stakes[3].add("auxiliaire")
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    sans_herbivorie(eco)
    banque = PlayerSeedBank()
    for sp in BANQUE:
        banque.add(Seed(species=sp))
    return monde([tuile], {NOM: eco}, banque=banque)


def _murir(pied) -> None:
    """Noue toutes les fleurs, puis une cohorte sur deux mûre, l'autre verte."""
    pied.fruits = nouer(pied, 1.0)
    for k, f in enumerate(pied.fruits):
        f.maturite = MUR if k % 2 == 0 else VERT


def post_init(game_state: dict, player: str) -> None:
    """Vigueur large, gestes savants ouverts (patron `palette_gestes`), fruits mûris,
    pot posé par sa façade. Forçage de BANC hors tick → golden intact."""
    etat = V.ensure_player(game_state, player)
    etat["max_base"] = etat["courante"] = VIGUEUR_BANC
    st = M.ensure_player_maitrise(game_state, player)
    for objet, palier in (("taille", 2), ("semis", 2), ("greffe", 1)):
        st["objets"][objet] = {"palier": palier, "preuves": 0}
    DEBL.evaluer_deblocages(game_state, player)
    tuile = next(t for t in game_state["tiles"] if t.tile_id == NOM)
    for pied in tuile.plants:
        if pied.position in (POMMIER, FRAISIER):
            _murir(pied)
    if CONT.poser_pot(game_state, player, "terreau", 75.0, *POT_CM) is None:
        raise RuntimeError("banc objet_en_main : pot non posé")
