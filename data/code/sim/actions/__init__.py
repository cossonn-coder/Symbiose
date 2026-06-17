"""
SYMBIOSE — sim/actions (paquet)
Actions JOUEUR sur le vivant et le milieu (D11) — coûts/gains de Vigueur.
Spec de référence : `docs/conception/CONCEPTION_VIGUEUR.md` §3 (catalogue d'actions),
§3.5 (HARVEST_VIGUEUR_COST réel), §4 (Qi territorial, flag `harvested`).

Découpage des responsabilités (décision actée 2026-06-04) :
  - `sim/vigueur.py` : l'ÉTAT joueur + les primitives `spend`/`gain` + le cycle.
  - CE paquet : les CONSTANTES de coût + les ACTIONS. « Ce que les gestes coûtent
    et font. » Il orchestre spend/gain et les mutations écologiques (nécromasse).

Éclaté en paquet au Sprint refactor global (SS④, 2026-06-15) ; l'ancien
`sim/actions.py` (775 l) devient ce paquet. L'API publique (constantes + fonctions)
est ré-exportée ici → tous les accès existants (`from sim import actions as ACT ;
ACT.planter`, `ACT.MODERE`, `ACT.maturite`…) marchent sans changement.

Orientation :
  - `couts.py`       — paliers de coût + seam « coût d'action » (maîtrise)
  - `progression.py` — ponts maîtrise → Vigueur (observer, crediter_succes)
  - `gestes.py`      — les gestes sur le vivant/milieu (manger…grelinette)
  - `compost.py`     — structures posables & compostage (décompo·compost ⑤)
"""

from sim.vigueur_plante import maturite   # ré-exporté pour compat (ACT.maturite, tests vigueur)

from .couts import (
    NUL, FAIBLE, MODERE, ELEVE, URGENCE_MULT, HARVEST_VIGUEUR_COST,
    COUTS, OBJETS_TOUCHES, ATT_GLOBALE_MAX, ATT_OBJET_MAX,
    _CLE_DE_CLASSE, _cle_espece, _objets_action, f_globale, f_objets, cout_action,
)
from .progression import GAIN_DECOUVERTE, GAIN_SUCCES, observer, crediter_succes
from .gestes import (
    DOSE_ARROSAGE, BECHAGE_MICROBIOME_MALUS, HARVEST_GAIN_FULL, GAIN_TAILLE_RATIO,
    manger, planter, arroser, recolter, deraciner, tailler,
    ecraser, ecraser_plante, favoriser_auxiliaire, becher, grelinette,
)
from .compost import (
    EPANDRE_W, poser_bac, poser_pile, composter, empiler_bois, retourner, epandre,
)
from .ruche import (
    CONCEPT_ABEILLES, SEUIL_EQUIPEMENT, MIEL_VIGUEUR_RATIO, RECOLTE_SANS_EQUIP,
    poser_ruche, equipe, recolter_miel,
)

__all__ = [
    "maturite",
    "NUL", "FAIBLE", "MODERE", "ELEVE", "URGENCE_MULT", "HARVEST_VIGUEUR_COST",
    "COUTS", "OBJETS_TOUCHES", "ATT_GLOBALE_MAX", "ATT_OBJET_MAX",
    "_cle_espece", "_objets_action", "f_globale", "f_objets", "cout_action",
    "GAIN_DECOUVERTE", "GAIN_SUCCES", "observer", "crediter_succes",
    "DOSE_ARROSAGE", "BECHAGE_MICROBIOME_MALUS", "HARVEST_GAIN_FULL", "GAIN_TAILLE_RATIO",
    "manger", "planter", "arroser", "recolter", "deraciner", "tailler",
    "ecraser", "ecraser_plante", "favoriser_auxiliaire", "becher", "grelinette",
    "EPANDRE_W", "poser_bac", "poser_pile", "composter", "empiler_bois",
    "retourner", "epandre",
    "CONCEPT_ABEILLES", "SEUIL_EQUIPEMENT", "MIEL_VIGUEUR_RATIO", "RECOLTE_SANS_EQUIP",
    "poser_ruche", "equipe", "recolter_miel",
]
