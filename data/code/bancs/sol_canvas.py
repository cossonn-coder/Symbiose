"""
SYMBIOSE — bancs/sol_canvas.py
Banc « sol-canvas » (sprint GESTES LISIBLES ③, observation F5 + capture VM).

Un petit jardin où CHAQUE conséquence au sol du tronçon ③ est déjà là, à l'œil,
dès l'ouverture (conception `docs/joueur/gestes/conception_gestes_lisibles.md` §3) :
  • rangée 1 — mottes du BÊCHAGE puis raies de GRELINETTE, à trois âges (la trace
    s'estompe avec les semaines) ;
  • rangée 3 — EMPREINTES de botte (deux pas récents, un ancien), AURÉOLES d'arrosage,
    VOILES de compost épandu ;
  • rangée 5 — deux CUVETTES de `creuser` (altitude baissée par la façade + rebord
    de terre rejetée), un tournesol DÉRACINÉ (couché, fait moteur) à côté d'un
    tournesol mort SUR PIED (debout) pour comparer ;
  • rangée 7 — PAILLIS des quatre natures, plein et mince ;
  • coin sud-ouest — un sol SEC en dégradé (craquelé, avec hystérésis à la vue) ;
  • un bac et une pile PEU remplis ; une seconde tuile porte un bac et une pile
    PLEINS (la structure grossit avec sa quantité).

Les gestes qui ont une façade sont joués PAR LA FAÇADE au post-init (Vigueur large,
même chemin que le jeu), et leur trace est écrite au registre moteur
(`sim.traces_sol.ecrire_trace`, celui qu'emploie le pont). L'ÂGE des traces est
ensuite antidaté (forçage de banc, assumé) pour voir l'estompage. Le pas (`ecraser`)
n'a pas de cible ici : sa trace seule est posée.

Pure COMPOSITION de l'état moteur, hors tick → golden NEUTRE (jamais monté pour
smoke/full). Capture conseillée : `-b sol_canvas -w 0 -z 4 -c 1700,1650`.
"""
from __future__ import annotations

from fields.ecofields.litiere import Parcelle, Structure
from plants import Sunflower
from sim import vigueur as V
from sim.actions import compost as COMPOST
from sim.actions import gestes as G
from sim.effects.perturbations import deposer_mort
from sim.traces_sol import ecrire_trace
from constants import PLOT_CM
from .base import build_banc_tile, monde, sans_herbivorie, vieillir

NOM = "SOLCANVAS"
NOM_PLEIN = "SOLPLEIN"
COTE = 10                      # 5×5 m
COTE_PLEIN = 4                 # 2×2 m, au nord de la première
# Coin sud-est du monde : devant la maison à l'écran (orientation 0), rien ne la masque.
ORIGINE = (1450.0, 1450.0)
ORIGINE_PLEIN = (1450.0, 1200.0)
VIGUEUR_BANC = 3000.0
HUMIDITE = 0.9                 # sol frais partout…
SEC = {(8, 0): 0.10, (8, 1): 0.20, (9, 0): 0.15, (9, 1): 0.30, (8, 2): 0.42,
       (9, 2): 0.48}           # … sauf ce coin (craquelé sous le seuil d'apparition)

# (verbe, (r, c), âge en semaines) — joués par la façade puis antidatés.
GESTES = (("becher", (1, 1), 0), ("becher", (1, 2), 3), ("becher", (1, 3), 5),
          ("grelinette", (1, 5), 0), ("grelinette", (1, 6), 2),
          ("grelinette", (1, 7), 3),
          ("arroser", (3, 4), 0), ("arroser", (3, 5), 0),
          ("epandre", (3, 7), 0), ("epandre", (3, 8), 3),
          ("creuser", (5, 2), 0), ("creuser", (5, 4), 4))
# Pas de botte : (x_cm, y_cm) tuile-locaux, âge.
PAS = ((60.0, 160.0, 0), (85.0, 180.0, 0), (130.0, 165.0, 1))
PAILLIS = (((7, 1), "paille", 1.0), ((7, 2), "paille", 0.35),
           ((7, 3), "brf", 1.0), ((7, 4), "brf", 0.35),
           ((7, 5), "aiguilles", 1.0), ((7, 6), "feuilles", 1.0))
DERACINE, DEBOUT = (5, 6), (5, 8)
# Les cuvettes visent des plots HAUTS (altitude ≥ 15 cm, seed du banc) : sur un plot
# déjà à 0 le moteur borne à 0, il n'y a pas de creux à voir.
BAC, PILE = (8, 6), (8, 8)
MASSE_PEU, MASSE_PLEIN = 1.0, 8.0


def _structure(kind: str, plot, masse: float) -> Structure:
    """Un bac (compost mûr) ou une pile (bois) déjà remplis de `masse`."""
    if kind == "bac":
        return Structure(kind="bac", plot=plot, compost_mur=masse)
    return Structure(kind="pile", plot=plot, contenu=[Parcelle("bois", masse)])


def sol_canvas():
    tuile, eco = build_banc_tile(NOM, "terre", COTE, COTE, *ORIGINE,
                                 humidite=HUMIDITE, fertilite=1.0, microbiome=0.5)
    for (r, c), h in SEC.items():
        eco.humidite.set(r, c, h)
    for (r, c), nature, prof in PAILLIS:
        eco.poser_mulch(r, c, nature, prof)
    for rc in (DERACINE, DEBOUT):
        pied = tuile.add_plant(Sunflower, *rc)
        pied.current_stage = len(Sunflower.growth_stages) - 1   # adulte, bien en tige
        vieillir(pied, 0.4)
    mort = next(p for p in tuile.plants if p.position == DEBOUT)
    mort.vitalite = 0.0
    deposer_mort(mort, eco)            # mort sur pied : squelette DEBOUT ("seche")
    eco.structures.append(_structure("bac", BAC, MASSE_PEU))
    eco.structures.append(_structure("pile", PILE, MASSE_PEU))
    sans_herbivorie(eco)
    plein, eco_plein = build_banc_tile(NOM_PLEIN, "terre", COTE_PLEIN, COTE_PLEIN,
                                       *ORIGINE_PLEIN,
                                       humidite=HUMIDITE, fertilite=1.0)
    eco_plein.structures.append(_structure("bac", (1, 0), MASSE_PLEIN))
    eco_plein.structures.append(_structure("pile", (1, 2), MASSE_PLEIN))
    return monde([tuile, plein], {NOM: eco, NOM_PLEIN: eco_plein})


def _jouer(gs: dict, player: str, verbe: str, eco, r: int, c: int) -> bool:
    """Le geste par sa façade (même chemin que le pont)."""
    if verbe == "epandre":
        bac = next(s for s in eco.structures if s.kind == "bac")
        return COMPOST.epandre(gs, player, eco, r, c, bac, q=2.0) > 0.0
    return bool(getattr(G, verbe)(gs, player, eco, r, c))


def post_init(game_state: dict, player: str) -> None:
    """Vigueur large, gestes joués par leur façade, traces écrites puis antidatées.
    Hors tick → golden intact (jamais appelé pour smoke/full)."""
    etat = V.ensure_player(game_state, player)
    etat["max_base"] = etat["courante"] = VIGUEUR_BANC
    eco = game_state["eco"][NOM]
    bac = next(s for s in eco.structures if s.kind == "bac")
    bac.compost_mur += 4.0             # de quoi épandre deux fois, sans vider le bac
    tuile = next(t for t in game_state["tiles"] if t.tile_id == NOM)
    plante = next(p for p in tuile.plants if p.position == DERACINE)
    G.deraciner(game_state, player, plante, eco)
    semaine = game_state.get("week", 0)
    for verbe, (r, c), age in GESTES:
        if not _jouer(game_state, player, verbe, eco, r, c):
            raise RuntimeError(f"banc sol_canvas : {verbe} refusé en ({r}, {c})")
        ecrire_trace(game_state, NOM, r, c, (c + 0.5) * PLOT_CM, (r + 0.5) * PLOT_CM,
                     verbe)       # ces six verbes laissent la sorte de leur nom
        game_state["traces_sol"][-1]["semaine"] = semaine - age
    for x, y, age in PAS:
        ecrire_trace(game_state, NOM, int(y // PLOT_CM), int(x // PLOT_CM), x, y, "pas")
        game_state["traces_sol"][-1]["semaine"] = semaine - age
