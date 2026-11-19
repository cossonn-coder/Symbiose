"""
SYMBIOSE — bancs/stress_au_bilan.py
Banc d'essai STRESS AU BILAN (D140 G, sprint stress au bilan ⑤, observation F5).

Plus de points de vie (`docs/vegetal/sante/conception_plante_vivante.md` §5) : une
plante meurt de six façons, chacune par son MÉCANISME. Ce banc les met côte à côte,
une scène par cause, pour que Nico les voie mourir et lise ce que l'info-bulle, le
carnet et la chronique en disent (sans chiffre, philo #5) :

  (1) FAMINE (nord, au pied du mur de la maison) — un poivron dans l'ombre portée :
      son bilan reste sous zéro, il ternit, meurt de faim. Le carnet dit « affamée de
      lumière » (cause amont lue sur sa mémoire d'ombre, ⑤), pas un simple « épuisée ».
  (2) DESTRUCTION (sud-ouest) — un jeune chêne sous forte densité de campagnols :
      écorce rongée tout autour du collet, sève coupée, « meurt annelé ».
  (3) DÉFAILLANCE HYDRAULIQUE (sable sec) — deux chênes aux vaisseaux déjà à moitié
      embolisés, tous deux flétris (« desséchée », signe `secheresse` qui ne se
      redresse pas à la pluie) : le pied SENSIBLE (ouest) continue de caviter et meurt
      desséché, réserves encore hautes ; l'autre ferme ses stomates, ne cavite plus,
      et meurt bien plus tard de faim (le carnet dit la soif).
  (4) RACINES PERDUES (argile gorgée) — un pommier aux racines déjà pourries par
      l'eau stagnante : il boit mal (« racines pourries »), s'épuise et meurt ; le
      carnet dit « noyée » (cause amont : asphyxie).
  (5) FIN DE CYCLE — une phacélie qui a déjà fleuri et mûri ses graines : elle
      remobilise ses réserves vers elles, puis sèche sur pied.
  (6) VIEILLESSE — une consoude au bout de sa longévité : l'âge rabote sa production
      et alourdit son entretien, « à bout d'âge », elle meurt de sénescence.

📖 Les scènes sont ACCÉLÉRÉES (mémoires pré-chargées, `force_memoire`/`vieillir`) :
on pose « le stress est déjà installé » pour voir la mort dans la fenêtre d'un F5, au
lieu d'attendre des mois de météo seedée. Le mécanisme, lui, est celui du jeu.

Pure COMPOSITION d'un état : golden NEUTRE (une fabrique de banc n'est jamais montée
pour smoke/full). Zéro RNG (philo #3).
"""
from __future__ import annotations

from plants import Comfrey, OakTree, AppleTree, Pepper, Phacelia
from .base import (build_banc_tile, monde, banque_de, force_faune, force_memoire,
                   sans_herbivorie, vieillir)

# Origines (cm, monde 20 m, maison au centre 600-1400). Le SUD (y > 1400) est au
# soleil ; le pied du mur NORD (y 550-600) est dans l'ombre de la maison.
OY_SUD = 1450.0
X_SCENES = (50.0, 380.0, 710.0, 1040.0, 1370.0)   # 5 tuiles 5 × 5 plots, 2,5 m
OX_OMBRE, OY_OMBRE = 800.0, 200.0                  # rangée 7 = pied du mur nord

CAMPAGNOL = 0.9            # densité ≥ ROOT_HERBIVORY_LETHAL (0,55) : annélation certaine
AGE_CHENE_JEUNE = 3.0      # ans — sous LIGNEUX_ANNELE_CM, écorce annelable
AGE_CHENE_SEC = 8.0        # ans — ligneux installé, réserves pour des mois
EMBOLIE_DEPART = 0.6       # > ½ seuil : « desséchée », flétris dès l'ouverture
# Le sable sec du banc reste au-dessus du seuil EXTRÊME d'un chêne neutre (0,075) : ses
# stomates ferment, il ne cavite pas. Le pied condamné est un individu SENSIBLE (gène
# `tolerance_secheresse` bas, variation individuelle du jeu) : seuil extrême 0,15.
TOLERANCE_SENSIBLE = 0.5
SENSIBLE, TOLERANT = 1, 3  # colonnes des deux chênes (ouest : sensible)
AGE_POMMIER = 6.0          # ans
RACINES_POURRIES = 0.85    # part des racines perdues (pourriture_memory)
ASPHYXIE = 0.9             # mémoire d'engorgement : le sol est gorgé depuis longtemps
RESERVES_BASSES = 0.06     # le pommier noyé a déjà puisé dans ses réserves
PART_LONGEVITE = 0.97      # la consoude a vécu 97 % de sa longévité
RESERVES_VIEILLE = 0.4


def _famine():
    """(1) Un poivron repiqué au pied du mur nord, dans l'ombre portée."""
    tile, eco = build_banc_tile("FAMINE", "terre", 8, 8, OX_OMBRE, OY_OMBRE,
                                humidite=1.2, fertilite=1.0, microbiome=0.4)
    sans_herbivorie(eco)          # l'ombre seule
    tile.add_plant(Pepper, 7, 4).advance_stage()
    return tile, eco


def _destruction():
    """(2) Un jeune chêne sous une forte densité de campagnols."""
    tile, eco = build_banc_tile("DESTRUCTION", "terre", 5, 5, X_SCENES[0], OY_SUD,
                                humidite=1.2, fertilite=1.0, microbiome=0.4)
    sans_herbivorie(eco)
    vieillir(tile.add_plant(OakTree, 2, 2), AGE_CHENE_JEUNE)
    force_faune(eco, "campagnol", CAMPAGNOL)
    return tile, eco


def _hydraulique():
    """(3) Deux chênes sur sable sec, vaisseaux déjà embolisés (mort / flétri)."""
    tile, eco = build_banc_tile("HYDRAULIQUE", "sable", 5, 5, X_SCENES[1], OY_SUD,
                                humidite=0.0, fertilite=0.6, microbiome=0.2)
    sans_herbivorie(eco)
    for c in (SENSIBLE, TOLERANT):
        chene = tile.add_plant(OakTree, 2, c)
        vieillir(chene, AGE_CHENE_SEC)
        force_memoire(chene, "embolie", EMBOLIE_DEPART)
        if c == SENSIBLE:
            chene.genes["tolerance_secheresse"] = TOLERANCE_SENSIBLE
    return tile, eco


def _racines():
    """(4) Un pommier sur argile gorgée, racines déjà pourries, réserves entamées."""
    tile, eco = build_banc_tile("RACINES", "argile", 5, 5, X_SCENES[2], OY_SUD,
                                humidite=3.0, fertilite=1.0, microbiome=0.3)
    sans_herbivorie(eco)
    pommier = tile.add_plant(AppleTree, 2, 2)
    vieillir(pommier, AGE_POMMIER)
    force_memoire(pommier, "pourriture_memory", RACINES_POURRIES)
    force_memoire(pommier, "asphyxie_memory", ASPHYXIE)
    pommier.reserves = RESERVES_BASSES
    return tile, eco


def _fin_de_cycle():
    """(5) Une phacélie dont la floraison et la maturation des graines sont passées."""
    tile, eco = build_banc_tile("FIN_DE_CYCLE", "terre", 5, 5, X_SCENES[3], OY_SUD,
                                humidite=1.2, fertilite=1.0, microbiome=0.4)
    sans_herbivorie(eco)
    p = tile.add_plant(Phacelia, 2, 2)
    while p.current_stage < len(p.plant_class.growth_stages) - 1:
        p.advance_stage()
    p.floraison_abs = 0           # fleurie à l'ouverture du monde : graines mûres
    return tile, eco


def _vieillesse():
    """(6) Une consoude au bout de sa longévité, réserves basses."""
    tile, eco = build_banc_tile("VIEILLESSE", "terre", 5, 5, X_SCENES[4], OY_SUD,
                                humidite=1.2, fertilite=1.0, microbiome=0.4)
    sans_herbivorie(eco)
    p = tile.add_plant(Comfrey, 2, 2)
    p.advance_stage()
    vieillir(p, PART_LONGEVITE * Comfrey.longevity())
    p.reserves = RESERVES_VIEILLE
    return tile, eco


def stress_au_bilan():
    """Banc « stress au bilan » (⑤) : une plante par cause de mort, côte à côte."""
    tiles, ecos = [], {}
    for fabrique in (_famine, _destruction, _hydraulique, _racines, _fin_de_cycle,
                     _vieillesse):
        tile, eco = fabrique()
        tiles.append(tile)
        ecos[tile.tile_id] = eco
    return monde(tiles, ecos, banque=banque_de("chene", "pommier", "poivron", par_espece=3))


def post_init(game_state: dict, player: str) -> None:
    """Coupe la germination FÉRALE (patron `plante_vivante`) : des levées spontanées
    brouilleraient la lecture des pieds posés. Hors tick → golden intact."""
    game_state["feral_off"] = True
