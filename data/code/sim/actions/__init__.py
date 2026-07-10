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
    BECHAGE_MALUS, GRELINETTE_GAIN, PAILLAGE_DOSE,
    manger, planter, arroser, recolter, deraciner, tailler,
    ecraser, ecraser_plante, favoriser_auxiliaire, becher, grelinette, pailler,
)
from .compost import (
    EPANDRE_W, structure_de_tuile, poser_bac, poser_pile,
    composter, empiler_bois, retourner, epandre,
)
# Matériau du paillage (équilibre invasion ④) : stock de mulch par nature +
# approvisionnement (broyer bois → BRF, récolte de plantes à paille).
from .paillage import (
    mulch_stock, stock_disponible, prelever_stock, broyer, recolter_paille,
)
# Couplage planter+pailler par maîtrise (équilibre invasion ⑦) : auto-paillage à la
# plantation au-dessus du palier, nature du mulch selon l'espèce.
from .autopaillage import (
    SEUIL_AUTOPAILLAGE, nature_autopaillage, auto_pailler,
)
from .ruche import (
    CONCEPT_ABEILLES, SEUIL_EQUIPEMENT, MIEL_VIGUEUR_RATIO, RECOLTE_SANS_EQUIP,
    poser_ruche, equipe, recolter_miel,
)
# Conteneurs (pots/bacs ④) : la façade `conteneurs.poser_bac` (BAC DE CULTURE) est
# ré-exportée sous `poser_bac_culture` pour ne PAS écraser `compost.poser_bac` (BAC
# À COMPOST) — deux objets distincts, un seul espace de noms `ACT.*`.
from .conteneurs import (
    poser_pot, poser_bac as poser_bac_culture, deplacer_pot,
)
# Supports de grimpe (grimpantes ④) : pose de structures + palissage manuel.
from .supports import (
    poser_tuteur, poser_treillis, poser_pergola, palisser,
)
# Déblocage des gestes (palette de gestes ①) : ÉTAT/DONNÉES par avatar (BASE +
# table `GESTE_UNLOCK` + hook `evaluer_deblocages`) — aucune logique de sim.
from .deblocage import (
    GESTES_BASE, GESTE_UNLOCK, DECLENCHEURS, init_gestes_debloques, est_debloque,
    marquer_action, marquer_evenement, evaluer_deblocages, gestes_debloques,
)
# Bouture (palette de gestes ②) : geste `bouturer` — clone génétique event-driven,
# réutilise le patron de `sim/clonal.py`. Pose le marqueur `bouture_spontanee` (③ voie).
from .bouture import (
    BOUTURE_STRESS_COST, BOUTURE_VIGUEUR_SEUIL, peut_bouturer, bouturer,
)

__all__ = [
    "maturite",
    "NUL", "FAIBLE", "MODERE", "ELEVE", "URGENCE_MULT", "HARVEST_VIGUEUR_COST",
    "COUTS", "OBJETS_TOUCHES", "ATT_GLOBALE_MAX", "ATT_OBJET_MAX",
    "_cle_espece", "_objets_action", "f_globale", "f_objets", "cout_action",
    "GAIN_DECOUVERTE", "GAIN_SUCCES", "observer", "crediter_succes",
    "DOSE_ARROSAGE", "BECHAGE_MICROBIOME_MALUS", "HARVEST_GAIN_FULL", "GAIN_TAILLE_RATIO",
    "BECHAGE_MALUS", "GRELINETTE_GAIN", "PAILLAGE_DOSE",
    "manger", "planter", "arroser", "recolter", "deraciner", "tailler",
    "ecraser", "ecraser_plante", "favoriser_auxiliaire", "becher", "grelinette", "pailler",
    "EPANDRE_W", "structure_de_tuile", "poser_bac", "poser_pile",
    "composter", "empiler_bois", "retourner", "epandre",
    "mulch_stock", "stock_disponible", "prelever_stock", "broyer", "recolter_paille",
    "SEUIL_AUTOPAILLAGE", "nature_autopaillage", "auto_pailler",
    "CONCEPT_ABEILLES", "SEUIL_EQUIPEMENT", "MIEL_VIGUEUR_RATIO", "RECOLTE_SANS_EQUIP",
    "poser_ruche", "equipe", "recolter_miel",
    "poser_pot", "poser_bac_culture", "deplacer_pot",
    "poser_tuteur", "poser_treillis", "poser_pergola", "palisser",
    "GESTES_BASE", "GESTE_UNLOCK", "DECLENCHEURS", "init_gestes_debloques", "est_debloque",
    "marquer_action", "marquer_evenement", "evaluer_deblocages", "gestes_debloques",
    "BOUTURE_STRESS_COST", "BOUTURE_VIGUEUR_SEUIL", "peut_bouturer", "bouturer",
]
