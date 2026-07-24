"""
SYMBIOSE — bancs/courrier.py
Banc d'essai COURRIER (système de quêtes D79, tronçon ⑤, observation F5).

Instrument pour VOIR le panneau « courrier » peuplé de lettres SANS jouer des
saisons entières : on monte un petit monde portant au moins un sujet de chaque
FAMILLE de cible (tomate cumulée, tournesol/hauteur, lavande & trèfle/floraison,
pommier/nombre-vivant), et le `post_init` OUVRE d'emblée les lettres du corpus —
une de chaque famille de condition active en même temps — en forçant les paliers
de maîtrise que leurs déclencheurs réclament et en démarrant en fin de saison
(`BANC_WEEK_DEPART`) pour que les jalons calendaires soient franchis.

Pure COMPOSITION de l'état moteur (plantes au catalogue + forçage de l'état JOUEUR
au post-init + ouverture des lettres via l'API existante `evaluer_declencheurs`) —
AUCUNE mécanique nouvelle → golden NEUTRE (jamais monté pour smoke/full, cf.
`cmd_init`). Toutes les espèces sont déjà au catalogue et à l'encyclopédie.
"""
from __future__ import annotations

from plants import Sunflower, Lavender, Clover, AppleTree
from sim import quetes
from sim.quetes_corpus import QUETES_CORPUS
from .base import build_banc_tile, monde, vieillir

# Une tuile large et fertile : de quoi porter quelques sujets de chaque famille
# tout en laissant des plots nus (le panneau observe des lettres, pas un jardin
# dense). 8×8 = 64 plots.
COU_ROWS = COU_COLS = 8

# Une lettre CURÉE par famille de condition (+ le rêve de kiwi INATTEIGNABLE, pour
# voir le signalement F3 à l'écran), ouvertes d'emblée au post_init. On CURE au lieu
# de dérouler `evaluer_declencheurs` : ce dernier est plafonné + trié par id et
# laisserait tomber la famille `nombre_vivant_min` (7ᵉ id) hors des 6 premières —
# le banc, lui, veut EXACTEMENT une de chaque famille sous les yeux.
COU_LETTRES = (
    "lettre_cageot_tomates",    # recolte_cumulee
    "lettre_tournesol_geant",   # hauteur_min
    "lettre_lavande_amelie",    # floraison_min
    "lettre_verger_pommiers",   # nombre_vivant_min
    "lettre_kiwi_reve",         # hauteur_min sur cible ABSENTE (F3, rêve ouvert)
)


def courrier():
    """Banc « courrier » (⑤, observation F5) : un sujet de chaque famille de cible
    pour que les avancements DIÉGÉTIQUES varient à l'écran. Pas d'oracle à seuil :
    instrument d'observation, lecture à l'œil par Nico du panneau peuplé."""
    tile, eco = build_banc_tile("COURRIER", "terre", COU_ROWS, COU_COLS,
                                humidite=1.2, fertilite=1.1, microbiome=0.6)
    # Tournesol (cible hauteur_min) : un plant, avancement « il prend de la hauteur ».
    tile.add_plant(Sunflower, 0, 0)
    # Lavandes (cible floraison_min×6) : un petit massif adulte.
    for r in range(4):
        lav = tile.add_plant(Lavender, r, 2)
        if lav is not None:
            lav.current_stage = len(Lavender.growth_stages) - 1
            vieillir(lav, 2.0)
    # Trèfles (cible floraison_min×5) : quelques stolons.
    for r in range(4):
        tile.add_plant(Clover, r, 4)
    # Pommiers (cible nombre_vivant_min×3 et ×2) : deux sujets → avancement partiel.
    for r in (0, 3):
        ap = tile.add_plant(AppleTree, r, 6)
        if ap is not None:
            vieillir(ap, float(AppleTree.maturity_years))
    return monde([tile], {tile.tile_id: eco})


def post_init(game_state: dict, player: str) -> None:
    """Forçage de l'état JOUEUR APRÈS construction du moteur (la fabrique ne porte
    pas `game_state`) : POSE directement les lettres curées (`COU_LETTRES`, une par
    famille) via l'API existante `ajouter_quete` — court-circuit assumé du
    déclenchement, pour peupler le panneau courrier dès l'ouverture sans dérouler de
    semaines. Écriture bornée à l'état joueur (opt-in, hors tick) → golden intact
    (jamais appelé pour smoke/full). C'est du forçage de BANC, jamais un chemin de
    jeu normal (en jeu, les lettres arrivent par `evaluer_declencheurs` au fil des
    semaines, câblé dans `step_week`)."""
    for lettre_id in COU_LETTRES:
        quetes.ajouter_quete(game_state, QUETES_CORPUS[lettre_id])
