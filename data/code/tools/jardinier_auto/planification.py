# SYMBIOSE — tools/jardinier_auto/planification.py
# Le PLANIFICATEUR moyens-fins de l'automate (D87 tronçon ②, §4). À partir d'un
# objectif actif `Objectif("recolter", quantite, sp)`, il produit — par CHAÎNAGE
# ARRIÈRE déterministe borné sur le catalogue d'opérateurs (operateurs.py) — le
# PROCHAIN geste créatif faisable pour faire ADVENIR la cible, PUIS on attend la
# biologie (aucune simulation temporelle en avant, §Q4).
#
# La chaîne est courte et quasi-linéaire (§recadrage `00_etat.md`) :
#   recolter ← cultivée présente ← planter ← graine ← magazine.
# Une cultivée `fruitier` ajoute une SOUS-CHAÎNE pollinisation (`favoriser_auxiliaire`,
# C2/C4). On raisonne en CULTURE PERMANENTE (C1) : on vise `nb_cible = min(quantite,
# 3)` cultivées vivantes TANT QUE la progression n'atteint pas `quantite`.
#
# CE TRONÇON PRODUIT les plans et les TRACE (lignes `plan`/`diagnostic`) ; il ne les
# BRANCHE PAS dans la boucle (③). Fonctions de DÉCISION : aucune écriture moteur, on
# ne touche QUE le journal et l'état persistant `automate_plans`. Déterminisme total
# (objectifs triés par id, placement canonique, zéro RNG → golden INTACT, opt-in).

from __future__ import annotations

from .proposition import Plan
from .objectifs import classe_cible, progression as _progression
from .tutelle import zones_cultivees
from .operateurs import (
    PRIO_CREATIF, FACTEUR_ADVENIR, CibleCreative,
    cultivees_vivantes, pre_planter, pre_acheter_magazine,
    zone_fruitiere_sans_habitat,
)
from . import trace as T

CLE_PLANS = "automate_plans"

# Garde-fou de récursion du chaînage arrière (T4/§Q4). La chaîne réelle est courte
# (profondeur ≤ 3) → ce plafond n'est JAMAIS atteint : il BORNE le raisonnement par
# principe (pas de boucle non bornée, pas de plan spéculatif en avant).
PROFONDEUR_MAX = 4

# Plafond de cultivées vivantes visées par défaut (C1/Q9) : `nb_cible = min(quantite,
# 3)` — « assez pour espérer la quantité », on ne force pas le rendement (le réel
# émerge via `incrementer`). Surchargeable au banc (⑤) ; ici, défaut de lecture.
NB_CIBLE_PLAFOND = 3


def _etat_plan(gs: dict, obj_id: str) -> dict:
    """Le record de planification d'un objectif sous `game_state["automate_plans"]`
    (créé à la volée, opt-in strict). Structure posée dès ② pour que ④ (veille +
    re-sonde armée C3) n'ait qu'à la LIRE/écrire, sans changer sa forme :
      - `tentatives_semaille` : garde-fou dur de re-semis (`≤ 2`, exploité en ④) ;
      - `essai_precedent`     : signature `(saison, plot)` du dernier essai (④, C3) ;
      - `en_veille` / `chainon` : l'objectif attend un déclencheur, sur quel chaînon.
    L'ordre n'importe pas (on itère les objectifs triés par id ailleurs)."""
    reg = gs.setdefault(CLE_PLANS, {})
    return reg.setdefault(obj_id, {
        "tentatives_semaille": 0,
        "essai_precedent": None,
        "en_veille": False,
        "chainon": None,
    })


def avancer_plans(engine, actifs: list, profil):
    """Produit le prochain geste créatif faisable pour chaque objectif `recolter`
    actif. Renvoie `(plans_creatifs, veilles)` :
      - `plans_creatifs` : liste de `Plan` (facteur=`advenir`, priorité PRIO_CREATIF),
        dans l'ordre des objectifs DÉJÀ triés par id (déterminisme) ;
      - `veilles` : liste de `(obj_id, chainon, source)` — objectifs sans geste
        faisable maintenant (④ y armera la veille/re-sonde ; ② se contente de les
        remonter + tracer un `diagnostic` de chaînon manquant).
    N'écrit QUE le journal (`plan`/`diagnostic`) et l'état `automate_plans` — aucune
    exécution, aucun champ écolo touché (fonction de DÉCISION). `profil` est reçu
    pour signature stable (④/⑤ le liront : verbosité, nb_cible du banc)."""
    gs = engine.game_state
    player = gs["current_player"]
    semaine = engine.week
    cultivees = zones_cultivees(gs, player)
    plans, veilles = [], []

    for obj in actifs:
        if obj.geste != "recolter":
            continue                       # seul `recolter` porte une chaîne d'advenue
        sp = obj.cible
        if classe_cible(sp) is None:
            continue                       # cible hors catalogue → inatteignable (objectifs.py)
        etat = _etat_plan(gs, obj.id)

        # C4 — SOUS-CHAÎNE pollinisation « au plus tôt » : une cultivée `fruitier`
        # sans habitat auxiliaire → poser l'habitat AVANT floraison. Indépendante du
        # compte de cultivées (une fruitière existe déjà) → évaluée d'abord.
        tuile_aux = zone_fruitiere_sans_habitat(engine, sp, cultivees)
        if tuile_aux is not None:
            plans.append(_plan_favoriser(sp, tuile_aux))
            T.consigner(gs, T.entree_plan(
                semaine, objectif_id=obj.id, espece=sp,
                zone=(tuile_aux.tile_id, None, None),
                detail={"sous_but": "favoriser_auxiliaire",
                        "raison": "cultivee_fruitiere_sans_habitat"}))

        # CHAÎNE PRINCIPALE — obtenir une NOUVELLE cultivée si le compte manque et la
        # quantité n'est pas atteinte (C1 : culture permanente jusqu'à `quantite`).
        prog = _progression(gs, obj.id)
        nb_cible = min(obj.quantite, NB_CIBLE_PLAFOND)
        if prog < obj.quantite and len(cultivees_vivantes(engine, sp, cultivees)) < nb_cible:
            plan, chainon = _obtenir_cultivee(engine, sp, player)
            if plan is not None:
                etat["en_veille"] = False
                etat["chainon"] = None
                plans.append(plan)
                _tracer_plan_principal(gs, semaine, obj.id, sp, plan)
            else:                          # ni graine ni offre → chaînon manquant
                etat["chainon"] = chainon
                veilles.append((obj.id, chainon, "aucune"))
                T.consigner(gs, T.entree_diagnostic(
                    semaine, objectif_id=obj.id, espece=sp,
                    detail={"sous_but": "cultivee_presente", "manque": chainon}))

    return plans, veilles


def _obtenir_cultivee(engine, sp: str, player: str):
    """Chaînage arrière (borné PROFONDEUR_MAX) pour faire advenir une cultivée de
    `sp` : d'abord SEMER si graine+plot libre, sinon ACHETER la graine si offerte,
    sinon signaler le chaînon manquant. Renvoie `(Plan|None, chainon|None)` — UN seul
    geste créatif par tick (puis on attend la biologie, §Q4). La chaîne est ≤ 3
    niveaux (planter ← graine ← magazine) : pas de récursion non bornée."""
    placement = pre_planter(engine, sp)          # (tile, r, c) | None
    if placement is not None:
        tile, r, c = placement
        return _plan_planter(sp, tile, r, c), None
    if pre_acheter_magazine(engine.game_state, sp, player):
        return _plan_acheter(sp), None
    return None, "graine"


# --- Fabriques de Plan créatif (dataclass Plan réutilisé, facteur=advenir) --------

def _plan_planter(sp, tile, r, c) -> Plan:
    return Plan("planter", "milieu", CibleCreative(sp, tile, r, c),
                None, FACTEUR_ADVENIR, PRIO_CREATIF)


def _plan_acheter(sp) -> Plan:
    return Plan("acheter_magazine", "magazine", CibleCreative(sp, None, None, None),
                None, FACTEUR_ADVENIR, PRIO_CREATIF)


def _plan_favoriser(sp, tile) -> Plan:
    return Plan("favoriser_auxiliaire", "tuile", CibleCreative(sp, tile, None, None),
                None, FACTEUR_ADVENIR, PRIO_CREATIF)


def _tracer_plan_principal(gs, semaine, obj_id, sp, plan) -> None:
    """Journalise un plan de la chaîne principale (ligne `plan`, niveau 0). Le
    sous-but et la raison DÉRIVENT du verbe (dérivation de champs — trace.py : jamais
    de texte libre, le rendu se dérive des champs)."""
    if plan.verbe == "planter":
        cible = plan.cible_obj
        zone = (cible.tile.tile_id, cible.r, cible.c)
        detail = {"sous_but": "semer",
                  "raison": "n_vivantes<nb_cible & graine_en_banque"}
    else:                                  # acheter_magazine
        zone = None
        detail = {"sous_but": "acheter", "raison": "pas_de_graine & offre_magazine"}
    T.consigner(gs, T.entree_plan(semaine, objectif_id=obj_id, espece=sp,
                                  zone=zone, detail=detail))
