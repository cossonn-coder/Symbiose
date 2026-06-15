"""
SYMBIOSE — sim/engine (paquet)
Moteur de simulation écologique — 52 semaines, 4 saisons.

Éclaté en paquet au Sprint refactor global (SS③, 2026-06-15) ; l'ancien
`sim/engine.py` (967 l) devient ce paquet. L'API publique est ré-exportée
ici → tous les imports existants (`from sim.engine import Engine, saison_de`,
`FRUIT_NOUAISON_WEEK`…) marchent sans changement.

Orientation :
  - `calendrier.py` — saisons, semaines, prédicats de phase (helpers purs)
  - `aleas.py`      — météo & ravageurs, dégât médié (Alea, appliquer_alea)
  - `croissance.py` — CroissanceMixin : échanges sol↔plante hebdo
  - `mortalite.py`  — MortaliteMixin : mort, reproduction, conflits, hiver
  - `decompo.py`    — DecompoMixin : litière (squelettes, abscission, fruits)
  - `boucle.py`     — Engine : l'orchestrateur tick_semaine + runners

Tick order : voir la docstring de `boucle.py`.
"""

from .calendrier import (SAISONS, PHASES_ACTIVES, FRUIT_NOUAISON_WEEK,
                         saison_de, est_debut_saison, est_fin_saison,
                         est_phase_floraison, est_phase_recolte)
from .aleas import (Alea, ALEAS_METEO, WEATHER_ALEA, ALEAS_RAVAGEURS,
                    appliquer_alea, TEMP_FROST_DAMAGE, FROST_SEVERITY_REF,
                    HAIL_SEVERITY_REF, PAILLAGE_PROTECT, DAMAGE_STEP)
from .boucle import Engine

__all__ = [
    "Engine",
    "SAISONS", "PHASES_ACTIVES", "FRUIT_NOUAISON_WEEK",
    "saison_de", "est_debut_saison", "est_fin_saison",
    "est_phase_floraison", "est_phase_recolte",
    "Alea", "ALEAS_METEO", "WEATHER_ALEA", "ALEAS_RAVAGEURS",
    "appliquer_alea", "TEMP_FROST_DAMAGE", "FROST_SEVERITY_REF",
    "HAIL_SEVERITY_REF", "PAILLAGE_PROTECT", "DAMAGE_STEP",
]
