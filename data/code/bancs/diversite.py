"""
SYMBIOSE — bancs/diversite.py
Banc d'essai DIVERSITÉ FONDATRICE (sprint du même nom, tronçon ③, observation F5).

Instrument pour VOIR de ses yeux les deux acquis du sprint, sur une seule tuile :
  ① RYTHMES PROPRES — un lot DENSE de LA MÊME espèce (tournesol) semé côte à côte,
     chaque pied avec un patrimoine génétique FONDATEUR propre (`semer_fondateur`,
     tronçon ①) : les gènes de rythme (`vigueur`, `germination_thermique`,
     `phenologie_florale`) diffèrent d'un individu à l'autre → la levée / la
     croissance / la floraison se DÉSYNCHRONISENT ligne à ligne (déjà rendu par
     PlantRenderer — le banc ne fait que l'EXPOSER).
  ② MOSAÏQUE ÉDAPHIQUE — la tuile est montée `heterogene=True` (via `build_banc_tile`,
     défaut du banc) → sol en CATENA (tronçon ②) : NPK/microbiome riches en bas de
     pente, pauvres en haut, pH ~homogène. Se LIT aux heatmaps `FieldOverlay` (F6).
     On NE FORCE aucun champ à la main : tout l'intérêt est l'hétérogénéité NATURELLE.

Pure COMPOSITION de l'état moteur (plantes + semis fondateur + catena de `init_eco`) —
AUCUNE mécanique nouvelle → golden NEUTRE (cette fabrique n'est JAMAIS montée pour
smoke/full, cf. `cmd_init`). Le tournesol est déjà au catalogue et à l'encyclopédie
(règle catalogue/voix respectée).

Le tournesol (`t_germ_opt=20`) exige un SOL CHAUD : le banc démarre MI-PRINTEMPS
(`BANC_WEEK_DEPART["diversite_fondatrice"]`, patron `grimpantes`/`luxuriance`) pour
que la levée et la croissance soient LISIBLES tout de suite au F5.
"""
from __future__ import annotations

from plants import Sunflower
from sim.seeds import semer_fondateur
from .base import build_banc_tile, monde

# Lot mono-espèce DENSE : 8×8 = 64 pieds → échantillon LISIBLE de la variance de
# rythme (comme le damier de `etalement_floraison`, mais ici la variance vient du
# VRAI tirage fondateur, pas d'un gène forcé — c'est ce qu'on veut donner à voir).
DIV_ROWS = DIV_COLS = 8

# Seed LOCAL du banc (déterministe, philo #3). La fabrique de banc ne reçoit pas le
# seed runtime du serveur (elle ne compose qu'un état) : on fige un seed propre pour
# que `founder_genes` tire une variance REPRODUCTIBLE d'un F5 à l'autre. La valeur
# n'a pas de sens en soi, seule sa CONSTANCE compte.
DIV_SEED = 0xD1F0FEED


def diversite_fondatrice():
    """Banc « diversité fondatrice » (③, observation F5) : un tapis dense de 64
    tournesols d'une MÊME espèce, chacun avec un patrimoine fondateur propre, sur un
    sol en catena. On REGARDE la désynchronisation des rythmes (levée/croissance/
    floraison étalées) et on LIT la mosaïque édaphique aux heatmaps F6. Pas d'oracle
    à seuil : instrument d'observation, calibrage à l'œil par Nico."""
    # `build_banc_tile` monte la tuile avec `heterogene=True` → sol catena + banque-sol
    # ensemencée fondatrice. On NE passe AUCUN `**champs` uniforme : l'hétérogénéité
    # naturelle de la catena est justement l'objet de l'observation.
    tile, eco = build_banc_tile("DIVERSITE", "terre", DIV_ROWS, DIV_COLS,
                                humidite=1.4, fertilite=1.2, microbiome=0.5)
    # Un tournesol par plot, chacun NATURALISÉ (`semer_fondateur`) : patrimoine
    # fondateur tiré sur sa position continue → 64 lignées distinctes déterministes.
    for r in range(DIV_ROWS):
        for c in range(DIV_COLS):
            semer_fondateur(tile, Sunflower, r, c, DIV_SEED)
    return monde([tile], {tile.tile_id: eco})
