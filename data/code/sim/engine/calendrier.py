"""
SYMBIOSE — sim/engine/calendrier.py
Ré-export du calendrier UNIQUE (`data/code/calendrier.py`, D122) : la source
vit en couche basse pour que `fields`/`sim` la lisent sans cycle d'import ;
ce module garde l'API historique (`from sim.engine.calendrier import …`)
pour ses importeurs (boucle, croissance, tools/, bancs/).
"""

from __future__ import annotations

from calendrier import (SAISONS, PHASES_ACTIVES, FRUIT_NOUAISON_WEEK,   # noqa: F401
                        SEMAINE_HIVER, W_T_MIN, W_SOLSTICE_ETE, wiy_de,
                        saison_de, est_debut_saison, est_fin_saison,
                        est_phase_floraison, est_phase_recolte)
