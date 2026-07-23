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

from sim.engine.calendrier import saison_de

from .proposition import Plan
from .objectifs import classe_cible, progression as _progression
from .tutelle import zones_cultivees
from .operateurs import (
    PRIO_CREATIF, FACTEUR_ADVENIR, CibleCreative,
    cultivees_vivantes, pre_planter, pre_acheter_magazine,
    plot_libre, zone_fruitiere_sans_habitat,
)
from .impasses import CHAINON_MANQUANT, NICHE_DEFAVORABLE
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

# T1 — un `planter` dépose un grain qui LÈVE plus tard (ou jamais). On lui laisse
# `FENETRE_LEVEE` semaines pour donner une cultivée vivante avant de conclure à un
# ÉCHEC de levée (④, §Suivi de germination). Constante nommée, déterministe.
FENETRE_LEVEE = 4

# C3 — garde-fou dur du re-semis : au-delà de ce nombre de tentatives, on n'arme plus
# de nouveau semis même si une condition a bougé → impasse `niche_defavorable`.
MAX_TENTATIVES = 2


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
        "essai_precedent": None,       # signature (saison, (tile_id, r, c)) du dernier semis
        "en_veille": False,
        "chainon": None,
        "semaine_semaille": None,      # semaine du dernier semis en attente de levée (T1)
        "n_au_semis": 0,               # n_vivantes au moment du semis (détection de levée)
        "impasse_signalee": None,      # cause d'impasse déjà tracée (dédup, une fois par cause)
    })


def marquer_veille_signalee(gs: dict, obj_id: str, chainon: str) -> bool:
    """Patron `marquer_inatteignable_signale` (objectifs.py) pour la VEILLE (③) :
    renvoie True au PREMIER passage en veille sur ce chaînon (→ l'appelant consigne
    une ligne `veille`), False tant que l'objectif reste en veille sur le MÊME
    chaînon → le log n'est pas noyé tick après tick. `avancer_plans` remet
    `en_veille=False` dès qu'un geste redevient faisable → une reprise puis rechute
    re-signale (transition, pas spam). ④ raffinera la re-sonde armée sur DÉCLENCHEUR."""
    etat = _etat_plan(gs, obj_id)
    if etat["en_veille"] and etat["chainon"] == chainon:
        return False
    etat["en_veille"] = True
    etat["chainon"] = chainon
    return True


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
    saison = saison_de(semaine)
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
        n_vivantes = len(cultivees_vivantes(engine, sp, cultivees))

        # Compte suffisant / quantité atteinte : si un semis pendait, il a LEVÉ (une
        # cultivée est apparue et fait le compte) → on clôt le suivi, relais Liebig.
        if prog >= obj.quantite or n_vivantes >= nb_cible:
            _resoudre_levee(gs, etat, semaine, obj.id, sp)
            continue

        # Un semis pend-il en attente de levée (T1) ? On gère germination / échec AVANT
        # d'émettre un nouveau geste (sinon on re-sème un grain à chaque tick).
        if etat["semaine_semaille"] is not None:
            if n_vivantes > etat["n_au_semis"]:
                _resoudre_levee(gs, etat, semaine, obj.id, sp)   # une cultivée est apparue
                continue
            if semaine - etat["semaine_semaille"] < FENETRE_LEVEE:
                continue                                          # fenêtre ouverte : on attend
            # Fenêtre écoulée SANS levée → échec ; re-semis armé seulement si une
            # condition a bougé (C3), sinon impasse `niche_defavorable` directe.
            plot = plot_libre(engine)
            arme = (etat["tentatives_semaille"] <= MAX_TENTATIVES
                    and plot is not None
                    and (saison, _sig_plot(plot)) != etat["essai_precedent"])
            if not arme:
                _mettre_en_veille(gs, etat, semaine, obj, sp, NICHE_DEFAVORABLE, veilles)
                continue
            etat["semaine_semaille"] = None                       # armé : on retente ce tick

        # Obtenir une cultivée : semis / achat / chaînon manquant.
        etait_veille = etat["en_veille"]
        plan, chainon = _obtenir_cultivee(engine, sp, player)
        if plan is not None:
            if plan.verbe == "planter":
                _enregistrer_semaille(etat, semaine, saison, plan, n_vivantes)
            etat["en_veille"] = False
            etat["chainon"] = None
            etat["impasse_signalee"] = None      # sortie d'impasse → une rechute re-signalera
            plans.append(plan)
            _tracer_plan_principal(gs, semaine, obj.id, sp, plan, etait_veille)
        else:                                    # ni graine ni offre → chaînon manquant
            _mettre_en_veille(gs, etat, semaine, obj, sp, CHAINON_MANQUANT,
                              veilles, chainon)

    return plans, veilles


# --- Suivi de germination, re-semis armé et veille (④, §5) ------------------------

def _sig_plot(plot):
    """Identité canonique d'un plot pour la signature d'essai C3 : `(tile_id, r, c)`,
    ou None si le monde est saturé. `plot` est le triplet `(tile, r, c)` de plot_libre."""
    return None if plot is None else (plot[0].tile_id, plot[1], plot[2])


def _enregistrer_semaille(etat: dict, semaine: int, saison: str, plan, n_vivantes: int) -> None:
    """Mémorise l'essai de semis (T1/C3) : fenêtre de levée (`semaine_semaille`),
    signature `(saison, plot)` pour armer un futur re-semis, compteur de tentatives
    (garde-fou dur) et `n_vivantes` de départ (détection de levée = le compte monte)."""
    cr = plan.cible_obj
    etat["semaine_semaille"] = semaine
    etat["essai_precedent"] = (saison, (cr.tile.tile_id, cr.r, cr.c))
    etat["tentatives_semaille"] += 1
    etat["n_au_semis"] = n_vivantes


def _resoudre_levee(gs: dict, etat: dict, semaine: int, obj_id: str, sp: str) -> None:
    """Un semis en attente a LEVÉ (une cultivée vivante est apparue) → sous-but atteint :
    on réinitialise le suivi (le relais passe à Liebig) et on trace le `resultat`. No-op
    strict si aucun semis ne pendait (pas de ligne parasite → oracle préservé)."""
    if etat["semaine_semaille"] is None:
        return
    T.consigner(gs, T.entree_resultat(semaine, objectif_id=obj_id, espece=sp,
                                      detail={"sous_but": "semer", "issue": "leve"}))
    etat["semaine_semaille"] = None
    etat["n_au_semis"] = 0
    etat["tentatives_semaille"] = 0
    etat["essai_precedent"] = None


def _mettre_en_veille(gs: dict, etat: dict, semaine: int, obj, sp: str,
                      cause: str, veilles: list, chainon: str | None = None) -> None:
    """Met l'objectif en VEILLE sur une impasse TYPÉE (`chainon_manquant` /
    `niche_defavorable`) — l'objectif RESTE actif (jamais retiré). Remonte le tuple
    veille à la boucle (ligne `veille`, dédup par chaînon) et trace `diagnostic` +
    `impasse` UNE fois par cause (dédup `impasse_signalee`) → le journal n'est pas noyé
    tick après tick. La re-sonde armée (saison/plot changé, offre ouverte) est gérée
    par le flux principal : l'impasse se lève d'elle-même dès qu'un geste redevient
    faisable (`impasse_signalee` remis à None), une rechute re-signalera."""
    lien = chainon if cause == CHAINON_MANQUANT else cause
    source = "aucune" if cause == CHAINON_MANQUANT else "niche"
    etat["chainon"] = lien
    veilles.append((obj.id, lien, source))
    if etat.get("impasse_signalee") == cause:
        return
    etat["impasse_signalee"] = cause
    T.consigner(gs, T.entree_diagnostic(
        semaine, objectif_id=obj.id, espece=sp,
        detail={"sous_but": "cultivee_presente", "manque": lien}))
    T.consigner(gs, T.entree_impasse(semaine, "-", f"{sp}#{obj.id}", lien, cause))


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


def _tracer_plan_principal(gs, semaine, obj_id, sp, plan, reveil=False) -> None:
    """Journalise un plan de la chaîne principale (ligne `plan`, niveau 0). Le
    sous-but et la raison DÉRIVENT du verbe (dérivation de champs — trace.py : jamais
    de texte libre, le rendu se dérive des champs). `reveil=True` (④) → l'objectif
    SORT de veille : la raison porte le DÉCLENCHEUR qui l'a réveillé."""
    if plan.verbe == "planter":
        cible = plan.cible_obj
        zone = (cible.tile.tile_id, cible.r, cible.c)
        detail = {"sous_but": "semer",
                  "raison": "n_vivantes<nb_cible & graine_en_banque"}
    else:                                  # acheter_magazine
        zone = None
        detail = {"sous_but": "acheter", "raison": "pas_de_graine & offre_magazine"}
    if reveil:
        decl = "magazine_ouvert" if plan.verbe == "acheter_magazine" else "plot_ou_graine"
        detail["raison"] = f"reveil:{decl}"
    T.consigner(gs, T.entree_plan(semaine, objectif_id=obj_id, espece=sp,
                                  zone=zone, detail=detail))
