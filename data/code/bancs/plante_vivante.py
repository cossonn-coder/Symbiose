"""
SYMBIOSE — bancs/plante_vivante.py
Banc d'essai PLANTE VIVANTE (D140 G, sprint plante vivante ⑥, observation F5).

Une plante n'a plus de points de vie : elle vit de son BILAN CARBONE, porte un
`feuillage` et des `reserves` (`docs/vegetal/sante/conception_plante_vivante.md`).
Ce banc met côte à côte, sous les yeux de Nico, quatre scènes qui se lisent sans
chiffre (philo #5) — moins de feuilles dessinées, un vert qui se ternit, une phrase
d'info-bulle :

  (a) LIMACES (au sud, plein soleil) — la même densité de limaces partout sur la
      tuile : un SEMIS de chêne à l'est, un CHÊNE de 25 ans à l'ouest. La limace ne
      mange que ce qu'elle atteint (sous 40 cm) et la perte se partage sur tout le
      feuillage d'une plante : le semis se dégarnit puis s'épuise, le chêne ne bronche
      pas.
  (b) OMBRE (au pied du mur nord de la maison) — trois poivrons repiqués, héliophiles,
      dans l'ombre portée : leur bilan glisse sous zéro (facteur limitant `ombre`), ils
      puisent dans leurs réserves, ternissent (« à bout de forces » en s17) et meurent
      de faim en s17-s19 [seed 42, n=1] ; le même poivron au soleil tient (bilan +1,5
      à +2 sem/sem). Leur nécromasse reste au pied du mur : un tas de tiges paille
      (~1,9-2,2 de litière `herbace` par plot, ~0,6 après 12 semaines [seed 42, n=1])
      que le geste `composter` ramasse vers un bac posé sur la tuile.
  (c) REFEUILLAISON (au sud-est, sans ravageur) — trois consoudes, d'ouest en est :
      un témoin intact ; une broutée (80 % des feuilles perdues avant l'ouverture) à
      réserves pleines, qui refait ses feuilles (0,2 → 0,97 en 6 semaines) ; une
      broutée à réserves basses (0,10), qui les refait en 7 semaines et reste ternie
      11 semaines [seed 42, n=1]. La vue ouvre SANS warmup (`BANC_WARMUP`) : on voit
      bien 0,2 au premier dessin (une semaine de warmup les montrait déjà à 0,35).
  (d) SOUCHE (à l'est) — un chêne de 12 ans coupé à l'ouverture : sa souche a mis de
      la réserve de côté, elle rejette au premier tick hors hiver, un nombre FINI de
      rejets (réserve // coût d'un rejet), pas une cascade.

📖 Pourquoi la consoude et pas une laitue (kickoff) : le catalogue n'a pas de laitue,
et la mâche — sa seule salade — meurt en plein été au lieu de refeuiller (petite
réserve de rosette, chaleur hors de sa niche ; mesuré). La consoude est une vivace à
grandes feuilles basses qui a de quoi les refaire : la scène se lit.

📖 Pourquoi le poivron à l'ombre : c'est l'espèce que le ⑤ a vue mourir de faim à
l'ombre dans le monde `full` (limitant `ombre`) ; tournesol et basilic, eux, gardent
un bilan positif au pied du mur (mesuré).

Pure COMPOSITION d'un état (sol, faune, plantes, mort d'un arbre) : golden NEUTRE (une
fabrique de banc n'est jamais montée pour smoke/full). Zéro RNG (philo #3).
"""
from __future__ import annotations

from plants import Comfrey, OakTree, Pepper
from sim.effects import deposer_mort
from .base import build_banc_tile, monde, banque_de, force_faune, sans_herbivorie, vieillir

# Origines (cm, monde 20 m, maison au centre 600-1400). Le SUD (y > 1400) est devant
# la maison à l'écran et au soleil ; le NORD (y < 600) est dans son ombre.
OX_LIMACES, OY_SUD = 50.0, 1450.0          # 16 × 10 plots = 8 × 5 m
OX_REFEUILLE = 900.0                       # 8 × 8 plots, à l'est des limaces
OX_SOUCHE = 1400.0                         # 8 × 8 plots, au bout du rang sud
OX_OMBRE, OY_OMBRE = 800.0, 200.0          # rangée 7 = pied du mur nord (y 550-600)

LIMACE_DENSITE = 0.15      # forte et uniforme : « les mêmes limaces » pour les deux chênes
AGE_CHENE = 25.0           # ans — couronne de ~6 m, des dizaines de plots de feuillage
AGE_CHENE_COUPE = 12.0     # ans — souche lignifiée (≥ AGE_SOUCHE_PROPRE), réserve pleine
FEUILLAGE_BROUTE = 0.2     # part des feuilles laissée aux consoudes « broutées »
# Réserves de la consoude broutée « à bout » (③) : juste au-dessus du seuil où elle ne
# peut plus payer la repousse — sous ~0,45 de feuillage son bilan est négatif, la
# repousse est payée sur les seules réserves ; à 0,08 elle meurt de faim à 0,40 de
# feuillage [seed 42, n=1]. À 0,10 : feuilles refaites en 7 semaines (6 pour la broutée
# riche), vert terni (réserves < R_CONFORT) 11 semaines. La repousse ne peut pas
# s'étaler davantage : au-dessus du seuil, elle file à REFEUIL_MAX (0,15/sem).
RESERVES_A_BOUT = 0.10


def _limaces():
    """(a) Semis de chêne et chêne de 25 ans sous la même densité de limaces."""
    tile, eco = build_banc_tile("LIMACES", "terre", 10, 16, OX_LIMACES, OY_SUD,
                                humidite=1.2, fertilite=1.0, microbiome=0.4)
    force_faune(eco, "limace", LIMACE_DENSITE)
    chene = tile.add_plant(OakTree, 5, 3)
    vieillir(chene, AGE_CHENE)
    tile.add_plant(OakTree, 5, 13)                       # le semis, à 5 m du chêne
    return tile, eco


def _ombre():
    """(b) Trois poivrons au pied du mur nord, dans l'ombre de la maison."""
    tile, eco = build_banc_tile("OMBRE", "terre", 8, 8, OX_OMBRE, OY_OMBRE,
                                humidite=1.2, fertilite=1.0, microbiome=0.4)
    sans_herbivorie(eco)          # l'ombre seule : aucune feuille mangée
    for c in (2, 4, 6):
        p = tile.add_plant(Pepper, 7, c)
        p.advance_stage()         # plant repiqué : une vraie feuille à voir ternir
    return tile, eco


def _refeuille():
    """(c) Consoudes, d'ouest en est : un témoin intact ; une broutée à réserves
    pleines (« refait ses feuilles ») ; une broutée à réserves basses (« à bout de
    forces » : repousse plus lente, vert terni)."""
    tile, eco = build_banc_tile("REFEUILLE", "terre", 8, 8, OX_REFEUILLE, OY_SUD,
                                humidite=1.2, fertilite=1.0, microbiome=0.4)
    sans_herbivorie(eco)          # rien ne les remange : on ne voit que la repousse
    for c in (2, 4, 6):
        p = tile.add_plant(Comfrey, 4, c)
        p.advance_stage()         # pied installé : de vraies feuilles à voir repousser
        if c != 2:
            p.feuillage = FEUILLAGE_BROUTE
        if c == 6:
            p.reserves = RESERVES_A_BOUT
    return tile, eco


def _souche():
    """(d) Un chêne de 12 ans coupé à l'ouverture : souche à réserve finie."""
    tile, eco = build_banc_tile("SOUCHE", "terre", 8, 8, OX_SOUCHE, OY_SUD,
                                humidite=1.2, fertilite=1.0, microbiome=0.4)
    sans_herbivorie(eco)          # les rejets ne sont pas l'objet des limaces ici
    chene = tile.add_plant(OakTree, 4, 4)
    vieillir(chene, AGE_CHENE_COUPE)
    chene.vitalite = 0.0          # coupe = destruction (la réserve racinaire reste)
    deposer_mort(chene, eco)
    return tile, eco


def plante_vivante():
    """Banc « plante vivante » (⑥) : limaces (semis/chêne), ombre (famine),
    refeuillaison (consoudes), souche (rejets finis)."""
    tiles, ecos = [], {}
    for fabrique in (_limaces, _ombre, _refeuille, _souche):
        tile, eco = fabrique()
        tiles.append(tile)
        ecos[tile.tile_id] = eco
    return monde(tiles, ecos, banque=banque_de("chene", "poivron", "consoude", par_espece=3))


def post_init(game_state: dict, player: str) -> None:
    """Coupe la germination FÉRALE (patron `niche_thermique`) : des levées spontanées
    couvriraient les scènes et brouilleraient la lecture des pieds posés. Hors tick →
    golden intact (jamais appelé pour smoke/full)."""
    game_state["feral_off"] = True
