"""
SYMBIOSE — bancs/nucleation.py
Banc « nucleation » (sprint ZOOCHORIE ⑦, D42) : voir les bêtes SEMER.

Une prairie ouverte (aucune levée spontanée : rien ne vient brouiller la lecture), un
cerisier mûr au sud-ouest, et à 8 m de lui deux PERCHOIRS sans feuillage :
  • un piquet `perchoir` (le geste `poser_perchoir`) au nord du cerisier ;
  • un MORT DEBOUT (pommier de 20 ans tué à l'init) à l'est du cerisier.
Au nord, la ceinture est une FORÊT de hêtres : le geai en rapporte glands et faînes
et les enterre en terrain découvert (apport de la ceinture, ⑤).

Attendu (doc `docs/faune/vie_macro/conception_zoochorie.md` §2) : des grains de
cerisier `merle` sous le piquet et sous le mort debout — LOIN de la mère —, des grains
`ceinture`/`geai` de chêne et de hêtre dans la moitié nord, à découvert.

⚠ En jeu, un mort debout ne reste debout que `T_SECHE` (6) semaines avant de se
coucher (`decompo._tick_skeletons`) : tué à l'init, il serait à terre bien avant les
cerises (mûres vers la semaine 23 [seed 42]). FORÇAGE DE BANC : son compteur
`semaines_mort` part à `-SURSIS_DEBOUT` → il tient debout jusqu'à la fin de la
première saison des cerises, puis se couche. C'est l'année 1 qui montre l'effet
« mort debout » ; les années suivantes ne montrent que le piquet et les couronnes.

Géométrie (ligne = y Sud, colonne = x Est ; 1 plot = 50 cm ; la maison occupe
600-1400 cm en x et en y, on la contourne par l'ouest et le sud).
Pure COMPOSITION de l'état moteur → golden NEUTRE (jamais monté pour smoke/full).
Lecture : `tests/bancs/test_nucleation.py`.
"""
from __future__ import annotations

from constants import PLOT_CM
from fields.peripherie import COTES, NORD, secteur_neutre
from plants import AppleTree, CherryTree
from sim.effects.perturbations import deposer_mort
from sim import maitrise as M
from sim.actions import deblocage as DEBL
from world.support import Support
from .base import build_banc_tile, monde, vieillir, sans_herbivorie

COTE_PLOTS = 40                     # 20×20 m, le monde entier
CERISIER = (36, 6, 15.0)            # (ligne, colonne, âge) — mûr, au sud-ouest
PERCHOIR = (20, 6)                  # 16 plots = 8 m au NORD du cerisier
MORT_DEBOUT = (36, 22, 20.0)        # 8 m à l'EST du cerisier
DISTANCE_CM = 800.0
RONDELLES_POLLINISATEUR = 3         # comme `verger_mur` : le cerisier est entomophile
# Sursis du mort debout (semaines) : debout de la semaine 1 à la ~26ᵉ, ce qui couvre
# la prise des cerises par le merle (semaines 23-25 [seed 42]). Cf. docstring.
SURSIS_DEBOUT = 20
# Forêt de hêtres au nord (valeurs dans les plages du banc `peripherie`).
FORET_NORD = {"type": "foret", "essence": "hetre",
              "hauteur_canopee": 2000.0, "densite_ligneuse": 0.9}


def nucleation():
    tuile, eco = build_banc_tile("NUCLEATION", "terre", COTE_PLOTS, COTE_PLOTS,
                                 humidite=1.2, fertilite=1.2, microbiome=0.5)
    ligne, colonne, age = CERISIER
    vieillir(tuile.add_plant(CherryTree, ligne, colonne), age)
    ligne, colonne, age = MORT_DEBOUT
    mort = tuile.add_plant(AppleTree, ligne, colonne)
    vieillir(mort, age)
    mort.vitalite = 0.0
    deposer_mort(mort, eco)           # squelette `seche` : debout, sans feuillage
    mort.semaines_mort = -SURSIS_DEBOUT
    pr, pc = PERCHOIR
    tuile.supports.append(Support(support_type="perchoir", x_cm=(pc + 0.5) * PLOT_CM,
                                  y_cm=(pr + 0.5) * PLOT_CM, height_cm=200.0,
                                  finesse="fin"))
    for _ in range(RONDELLES_POLLINISATEUR):         # sans abeilles, pas de cerises
        tuile.stakes[0].add("pollinisateur")
    eco.seed_bank.germination_candidates = lambda *a, **k: []   # prairie ouverte, lisible
    # Comme `verger_mur` : sans ce garde, l'herbivorie tue le cerisier de 15 ans en
    # 4 semaines [seed 42] (D127). Seule la catégorie `ravageur` est coupée : merle,
    # geai, écureuil, mulot (`auxiliaire`/`disperseur`) restent entiers.
    sans_herbivorie(eco)
    return monde([tuile], {tuile.tile_id: eco})


def ceinture_foret_nord() -> list[dict]:
    """Ceinture neutre partout, sauf une hêtraie au nord. Pure, sans tirage."""
    ceinture = [secteur_neutre(cote) for cote in COTES]
    ceinture[COTES.index(NORD)].update(FORET_NORD)
    return ceinture


def post_init(game_state: dict, player: str) -> None:
    """POSE la ceinture (la fabrique ne porte pas `game_state`) et OUVRE le geste
    `poser_perchoir` (zoochorie ⑧, point F5 « le geste se trouve-t-il ? ») : maîtrise
    `perchoir` 1, puis `evaluer_deblocages` — même forçage de BANC que `palette_gestes`.
    Sans lui le geste reste fermé : en jeu, aucune route ne crédite `perchoir` et
    `poser_tuteur` n'a pas de route au pont (dette D133). Hors tick → golden intact
    (jamais appelé pour smoke/full)."""
    game_state["ceinture"] = ceinture_foret_nord()
    M.ensure_player_maitrise(game_state, player)["objets"]["perchoir"] = {
        "palier": 1, "preuves": 0}
    DEBL.evaluer_deblocages(game_state, player)
