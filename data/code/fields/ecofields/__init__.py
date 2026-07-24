"""
SYMBIOSE — fields/ecofields (paquet)
Conteneur EcoFields : tous les champs écologiques continus d'une tuile
(hydrologie, OM tri-compartiment, microbiome, soil memory, lumière, perturbation,
banque de graines, populations) + constantes de calibration et types de litière.

Éclaté en paquet au Sprint refactor global (SS③, 2026-06-15) ; l'ancien
`fields/ecofields.py` (863 l) devient ce paquet. L'API publique est ré-exportée
ici → tous les imports existants (`from fields.ecofields import EcoFields,
RETOURNE_DUREE…`) et le ré-export en bloc de `fields/__init__.py` marchent sans
changement.

Orientation :
  - `constants.py` — calibration écologique (hydro, OM, mortalité, fruits…)
  - `litiere.py`   — Parcelle & Structure (litière typée, compostage)
  - `container.py` — EcoFields + init_eco / inject_patch (le conteneur & ses ticks)
"""

from .constants import *
from .litiere import *
from .nutriments import bell, dispo
from .inoculum import InoculumField
from .container import EcoFields, init_eco, inject_patch
