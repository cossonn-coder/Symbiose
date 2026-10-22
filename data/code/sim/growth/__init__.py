"""
SYMBIOSE — sim/growth (paquet)
Croissance procédurale des plantes (D29 réorienté) : une passe par plante et par
tick fait pousser sa structure de segments (plants.base.Segment), pilotée par
l'auxine (dominance apicale émergente) + un bornage. Source de vérité Python,
déterministe (philo #3 : aucun RNG, tout via fields._hash_noise).

Éclaté en paquet au Sprint refactor global (SS④, 2026-06-15) ; l'ancien
`sim/growth.py` (503 l) devient ce paquet. L'API publique (constantes + fonctions)
est ré-exportée ici → tous les accès existants (`import sim.growth as G ; G.X`,
`from sim.growth import grow_plant, est_etiole, atteindre_segment…`) marchent sans
changement.

Orientation :
  - `constantes.py` — leviers de module (auxine, gabarit, phototropisme, écrasement)
  - `geometrie.py`  — géométrie 3D, topologie de l'arbre, biais phototropique (purs)
  - `seam.py`       — f_lignification + atteindre_segment (point d'entrée des perturbations)
  - `phases.py`     — les 4 phases §D + étiolement + grow_plant (point d'entrée du tick)
  - `cladoptose.py` — mort de branches (ombre, casse) : choix + coupe, purs (D111 ②bis)
"""

from .constantes import (
    AUXIN_SOURCE, AUXIN_DECAY, AUXIN_INHIB_THRESHOLD, AUXIN_PROD_FLOOR,
    AUXIN_RELEASE_SCALE, GROWTH_SPEED, EMIT_LENGTH, THICKNESS_INIT, THICKEN_RATE,
    BRANCH_ANGLE, JITTER_RAD, PHOTOTROPISM_STRENGTH, MAX_PHOTOTROPISM_TILT,
    MIN_APEX_Z, ETIOLEMENT_LIGHT_SEUIL, ETIOLEMENT_GAIN, MAX_REACH_CM,
    WOOD_PERSISTENCE, MAX_SEGMENTS, COUPE_NETTE, INTENSITE_PIED, SEUIL_DEGAT,
    LIGNIFICATION_SCALE,
)
from .geometrie import _phototropic_bias
from .seam import f_lignification, atteindre_segment
from .phases import (shade_tolerance_effective, est_etiole, grow_plant)
from .cladoptose import (branches_ombragees, branches_a_casser, couper_branches,
                         seuil_et_age)

__all__ = [
    "AUXIN_SOURCE", "AUXIN_DECAY", "AUXIN_INHIB_THRESHOLD", "AUXIN_PROD_FLOOR",
    "AUXIN_RELEASE_SCALE", "GROWTH_SPEED", "EMIT_LENGTH", "THICKNESS_INIT",
    "THICKEN_RATE", "BRANCH_ANGLE", "JITTER_RAD", "PHOTOTROPISM_STRENGTH",
    "MAX_PHOTOTROPISM_TILT", "MIN_APEX_Z", "ETIOLEMENT_LIGHT_SEUIL",
    "ETIOLEMENT_GAIN", "MAX_REACH_CM", "WOOD_PERSISTENCE", "MAX_SEGMENTS",
    "COUPE_NETTE", "INTENSITE_PIED", "SEUIL_DEGAT", "LIGNIFICATION_SCALE",
    "_phototropic_bias", "f_lignification", "atteindre_segment",
    "shade_tolerance_effective", "est_etiole", "grow_plant",
    "branches_ombragees", "branches_a_casser", "couper_branches", "seuil_et_age",
]
