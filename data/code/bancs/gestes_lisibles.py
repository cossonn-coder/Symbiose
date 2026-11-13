"""
SYMBIOSE — bancs/gestes_lisibles.py
Banc « gestes lisibles » (sprint GESTES LISIBLES ⑥, banc d'observation + recette F5).

UNE tuile où chacun des gestes de D136 (a)-(f) trouve une cible valide dès l'ouverture,
et un PLAN DE TEST (format `plan_test.py`, touche B) qui les joue l'un après l'autre par
le chemin du clic joueur : on regarde l'outil bouger au curseur, la trace naître au sol
et la phrase s'afficher, sans rien cliquer soi-même.

Disposition (tuile 10×10 plots = 5×5 m, coin sud-est du monde, devant la maison) :
  • colonne 0 — trois TOURNESOLS adultes : pincer, arracher, déraciner ;
  • colonne 2 — deux LAVANDES : la mère de `bouturer` (et de quoi glaner autour) ;
  • (2, 5)    — un POMMIER adulte à fruits MÛRS et VERTS : tailler, couper, récolter ;
  • rangée 0  — litière tendre (glaner, composter), bois mort (empiler) ;
  • colonne 9 — un BAC de compost mûr, une PILE, une RUCHE peuplée pleine de miel ;
  • (7, 2)    — des LIMACES (le rampant à écraser) ; (7, 4) des MOUSTIQUES seuls (le
    volant : le pied ne l'attrape pas, refus attendu). Pas l'abeille : les butineurs
    sont des agents des fleurs (`ForagerLayer`), pas des sprites de plot que la vue
    désigne sous le pied ;
  • (8, 7)    — un plot HAUT (creuser) et un plot détrempé (drainer) ; le coin (9, 0)
    est SEC (craquelé) ;
  • (5, 8)    — un POT de terreau ; une banque de graines pour `planter`.

Gestes gatés (couper, tailler, bouturer, pailler, composter…) : OUVERTS par forçage de
banc au post-init (patron `palette_gestes`/`objet_en_main`) — jamais un chemin de jeu.
Pure COMPOSITION de l'état moteur, hors tick → golden NEUTRE (jamais monté pour
smoke/full). Capture : `tools/capture_vm.sh -b gestes_lisibles -w 0 -z 2 -c 1700,1700 -R`.
"""
from __future__ import annotations

from fields.ecofields.litiere import Parcelle, Structure
from plants import AppleTree, Lavender, Sunflower
from sim import vigueur as V
from sim import maitrise as M
from sim.actions import conteneurs as CONT
from sim.actions import deblocage as DEBL
from sim.actions.paillage import mulch_stock
from sim.engine.decompo import nouer
from .base import banque_de, build_banc_tile, force_faune, monde, sans_herbivorie, vieillir
from .plan_test import bete, plante_en, plot, pot, structure

NOM = "GESTES"
COTE = 10                       # 5×5 m
ORIGINE = (1450.0, 1450.0)
VIGUEUR_BANC = 5000.0
TOURNESOLS = ((1, 0), (3, 0), (5, 0))      # pincer, arracher, déraciner
LAVANDES = ((1, 2), (3, 2))
POMMIER = (2, 5)
FEUILLES = ((0, 1), (0, 3))                 # glaner, composter
BOIS = (0, 5)                               # empiler_bois
BAC, PILE, RUCHE = (1, 9), (3, 9), (5, 9)
LIMACES, MOUSTIQUES = (7, 2), (7, 4)
SEC = {(9, 0): 0.12, (9, 1): 0.25, (8, 0): 0.30}
DETREMPE = (8, 9)
POT_RC = (5, 7)
POT_CM = (ORIGINE[0] + (POT_RC[1] + 0.5) * 50.0, ORIGINE[1] + (POT_RC[0] + 0.5) * 50.0)
MUR, VERT = 1.05, 0.5
OUVERTS = ("couper", "tailler", "bouturer", "pailler", "composter", "empiler_bois",
           "retourner", "epandre", "recolter_miel", "planter_conteneur", "deplacer_pot")

# Le PLAN DE TEST — l'ordre lisible du kickoff ⑥ : d'abord la plante, puis le sol, puis
# les tas, puis la récolte et le semis. `plante_en` vise le pied d'une plante à son plot
# (trois tournesols, chacun son geste) ; `bete` vise un plot et nomme la bête que la vue
# y voit (sprite sous la souris).
PLAN_TEST = (
    ("arroser", plot(NOM, 4, 4)),
    ("pincer", plante_en(NOM, *TOURNESOLS[0])),
    ("couper", plante_en(NOM, *POMMIER)),
    ("tailler", plante_en(NOM, *POMMIER)),
    ("glaner", plot(NOM, *FEUILLES[0])),
    ("drainer", plot(NOM, *DETREMPE)),
    ("bouturer", plante_en(NOM, *LAVANDES[0]), plot(NOM, 6, 3)),
    ("arracher", plante_en(NOM, *TOURNESOLS[1])),
    ("deraciner", plante_en(NOM, *TOURNESOLS[2])),
    ("retourner", structure(NOM, "bac")),
    ("ecraser", bete(NOM, *LIMACES, "limace")),
    ("ecraser", bete(NOM, *MOUSTIQUES, "moustique")),  # volant → refus attendu
    ("favoriser_auxiliaire", plot(NOM, 4, 6)),
    ("becher", plot(NOM, 6, 5)),
    ("grelinette", plot(NOM, 6, 6)),
    ("creuser", plot(NOM, 8, 7)),
    ("epandre", structure(NOM, "bac"), plot(NOM, 6, 7)),
    ("empiler_bois", plot(NOM, *BOIS)),
    ("pailler", plot(NOM, 8, 4)),
    ("composter", plot(NOM, *FEUILLES[1])),
    ("recolter", plante_en(NOM, *POMMIER)),
    ("recolter_miel", structure(NOM, "ruche")),
    ("planter", plot(NOM, 8, 2)),
    ("planter_conteneur", pot(0)),
    ("deplacer_pot", pot(0), plot(NOM, 4, 8)),
)


def _adulte(tuile, cls, rc, ans: float):
    pied = tuile.add_plant(cls, *rc)
    pied.current_stage = len(cls.growth_stages) - 1
    vieillir(pied, ans)
    return pied


def gestes_lisibles():
    tuile, eco = build_banc_tile(NOM, "terre", COTE, COTE, *ORIGINE,
                                 humidite=0.8, fertilite=1.2, microbiome=0.5)
    for rc in TOURNESOLS:
        _adulte(tuile, Sunflower, rc, 0.4)
    for rc in LAVANDES:
        _adulte(tuile, Lavender, rc, 2.0)
    _adulte(tuile, AppleTree, POMMIER, float(AppleTree.maturity_years) + 3.0)
    for r, c in FEUILLES:
        eco.deposer_litiere(r, c, "feuille", 2.0)
    eco.deposer_litiere(*BOIS, "bois", 2.0)
    eco.structures.append(Structure(kind="bac", plot=BAC, compost_mur=8.0,
                                    contenu=[Parcelle("feuille", 2.0)]))
    eco.structures.append(Structure(kind="pile", plot=PILE, contenu=[Parcelle("bois", 1.0)]))
    eco.structures.append(Structure(kind="ruche", plot=RUCHE, essaim=1.0, miel=3.0))
    for (r, c), h in SEC.items():
        eco.humidite.set(r, c, h)
    eco.humidite.set(*DETREMPE, 1.0)
    for espece in ("limace", "moustique"):
        force_faune(eco, espece, 0.0)
    eco.populations["limace"].set(*LIMACES, 0.6)
    eco.populations["moustique"].set(*MOUSTIQUES, 0.6)
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    sans_herbivorie(eco)
    return monde([tuile], {NOM: eco}, banque=banque_de("tournesol", "basilic", "ail"))


def post_init(game_state: dict, player: str) -> None:
    """Vigueur large, gestes gatés ouverts, fruits du pommier mûris, paille en stock, pot
    posé par sa façade. Forçage de BANC hors tick → golden intact."""
    etat = V.ensure_player(game_state, player)
    etat["max_base"] = etat["courante"] = VIGUEUR_BANC
    st = M.ensure_player_maitrise(game_state, player)
    for objet, palier in (("taille", 2), ("semis", 2), ("greffe", 1)):
        st["objets"][objet] = {"palier": palier, "preuves": 0}
    DEBL.init_gestes_debloques(game_state, player).update(OUVERTS)
    mulch_stock(game_state).update(paille=5.0, feuilles=5.0)
    tuile = next(t for t in game_state["tiles"] if t.tile_id == NOM)
    pommier = next(p for p in tuile.plants if p.position == POMMIER)
    pommier.fruits = nouer(pommier, 1.0)
    for k, f in enumerate(pommier.fruits):
        f.maturite = MUR if k % 2 == 0 else VERT
    if CONT.poser_pot(game_state, player, "terreau", 75.0, *POT_CM) is None:
        raise RuntimeError("banc gestes_lisibles : pot non posé")
