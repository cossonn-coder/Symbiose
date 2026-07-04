"""
SYMBIOSE — bancs/luxuriance.py
Banc d'observation de la LUXURIANCE PAR STRATIFICATION (sprint D65 ⑥, absorbe D62).

Instrument pour voir au F5 le jardin se REMPLIR et se SUPERPOSER : plusieurs
strates coexistent sur les mêmes plots (couvre-sol clonal + potagère étalée +
buisson drageonnant + grimpante), la couverture au sol se TAPISSE, et les colonies
clonales (stolons/drageons) ÉMERGENT en tapis. À la différence des bancs à seuil
(qui forcent UN signe), c'est un jardin composé où la luxuriance ÉMERGE sur la
saison — Nico calibre à l'œil (empilement lisible, densité du tapis, silhouettes).

Pure COMPOSITION de l'état moteur (plantes du catalogue + champs éco) — AUCUNE
mécanique nouvelle → golden NEUTRE (jamais monté pour smoke/full, cf. `cmd_init`).
Le clonal (`sim/clonal.py`, ②) tourne au tick : trèfle/violette tapissent par
stolons, le framboisier draine un fourré ; la couverture (①) monte et gate.

Comme les autres bancs d'observation (grimpantes), on ISOLE (succession spontanée
coupée : on regarde CES plantes, pas des pionnières) et on PAILLE (anti-gel des
frileuses au démarrage).
"""
from __future__ import annotations

# Les espèces clonales neuves (violette/framboisier…) vivent dans des
# sous-modules d'espèces non ré-exportés par `plants` : on les résout par leur
# CLÉ CATALOGUE (source de vérité data-driven), comme le fait `planter`.
from plants.catalogue import PLANT_CATALOGUE
from .base import build_banc_tile, monde, vieillir

Clover      = PLANT_CATALOGUE["trefle"]
SweetViolet = PLANT_CATALOGUE["violette"]
Zucchini    = PLANT_CATALOGUE["courgette"]
Raspberry   = PLANT_CATALOGUE["framboisier"]
Bean        = PLANT_CATALOGUE["haricot"]
Sunflower   = PLANT_CATALOGUE["tournesol"]

# Un couvre-sol CLAIRSEMÉ au départ (quelques pieds) : le tapissage doit se VOIR
# se densifier par le clonal, pas partir déjà plein. Trèfle (stolon, plein soleil)
# + violette (stolon sciaphile) sur des plots distincts → deux tapis à comparer.
COUVRE_SOL = [(Clover, 1, 1), (Clover, 1, 3), (Clover, 3, 1),
              (SweetViolet, 6, 6), (SweetViolet, 6, 4)]
# La STRATIFICATION verticale sur les MÊMES plots : au-dessus du tapis de trèfle,
# une courge (potagère basse-mais-ÉTALÉE, silhouette « étalée ») et un tournesol
# (dressé, strate haute) → on voit le couvre-sol PASSER SOUS eux (ordre de dessin).
POTAGERE = [(Zucchini, 2, 2), (Sunflower, 2, 4)]
# Un fourré de framboisier (drageon → colonie resserrée, silhouette « buisson »,
# strate moyenne→haute) pré-vieilli pour porter déjà du bois lisible.
FRAMBOISIER = [(Raspberry, 5, 2)]
# Une grimpante (haricot) plantée JUSTE À CÔTÉ du tournesol : elle l'enroulera en
# dépassant sa hauteur autoportante (grimpe émergente, cf. banc grimpantes).
GRIMPANTE = [(Bean, 2, 5)]


def luxuriance():
    """Banc « luxuriance » (D65 ⑥, observation F5) : sur UNE tuile, un couvre-sol
    clonal clairsemé (trèfle + violette), une strate potagère (courge étalée +
    tournesol dressé), un framboisier drageonnant et une grimpante — laissés
    TAPISSER et s'EMPILER sur la saison. Instrument d'observation, pas d'oracle à
    seuil : on REGARDE l'empilement multi-strates, le tapis de couverture et les
    colonies clonales au F5. Isolé (pas de succession) + paillé (anti-gel)."""
    tile, eco = build_banc_tile("LUXURIANCE", "terre", 8, 8,
                                humidite=1.6, fertilite=1.3, microbiome=0.7)
    eco.lumiere.fill(1.0)   # plein soleil (le trèfle stolon a besoin de lumière au sol)

    for cls, r, c in COUVRE_SOL + POTAGERE + GRIMPANTE:
        tile.add_plant(cls, r, c)
    for cls, r, c in FRAMBOISIER:
        # Pré-vieilli d'un an : porte déjà du bois de buisson (silhouette lisible)
        # et est mature → émet des drageons dès l'observation (accélération, base.py).
        vieillir(tile.add_plant(cls, r, c), 1.0)

    # Banc ISOLÉ + anti-gel (patron `grimpantes`/`semis_tempere`) : instrument
    # d'observation, pas jardin de succession. Succession spontanée COUPÉE (sinon des
    # pionnières lèvent de la SeedBank-sol et masquent l'empilement voulu) ; paillage
    # SATURÉ (protège les frileuses des gelées tardives de démarrage).
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    for stake in tile.stakes:
        while stake.add("paillage"):
            pass

    return monde([tile], {tile.tile_id: eco})
