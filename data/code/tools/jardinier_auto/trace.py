# SYMBIOSE — tools/jardinier_auto/trace.py
# Le JOURNAL déterministe de l'automate (§6 jardinier + §6 automate-but D87). C'est
# le canal TECHNIQUE de débogage — JAMAIS diégétique (le carnet du joueur vit dans
# `sim/journal.py`, voix « je », gaté par `ecrit_carnet` ; les deux ne fusionnent
# jamais, sinon philo #5/#6 violées).
#
# D87 ① — LOG EXHAUSTIF STRUCTURÉ. On enrichit le journal pour qu'il rende TOUT le
# raisonnement moyens-fins inspectable (perception → diagnostic → plan → geste →
# veille/impasse/conséquence/résultat) et serve d'ORACLE de déterminisme : deux runs
# à entrées égales → journal identique ligne à ligne. Le log est TOUJOURS complet
# (tous niveaux écrits) ; verbosité et filtre sont des vues LECTURE SEULE (filtre.py).
#
# Schéma de ligne (dict JSON-sérialisable). CHAMPS COMMUNS à toutes les catégories :
#   - `categorie` : perception|diagnostic|plan|geste|geste_coupe|veille|impasse|
#     consequence|resultat ;
#   - `semaine` (int) ;
#   - `niveau` (int : 0=décision · 1=détail · 2=perception fine) — clé de la
#     verbosité de LECTURE, jamais d'écriture ;
#   - localisation : `objectif_id` (str|None), `espece` (str|None),
#     `zone` (tuple `(tile_id, r, c)`|None — plot d'un geste créatif) ;
#   - `detail` (dict) : charge utile spécifique à la catégorie.
# Les constructeurs LEGACY (entree/entree_impasse/entree_consequence, sprint D78)
# gardent EN PLUS leurs clés à plat historiques (tile_id, cible, facteur_limitant,
# geste, resultat, cause, type) — lues par onglet.py / rapport.py / automate_cmd.py :
# on ne CASSE rien, on AJOUTE les champs communs manquants.
#
# Le journal vit sous `game_state["automate_journal"]` (liste, opt-in). Il n'est
# JAMAIS lu par le tick → golden intact (H2). Chaque entrée est un dict de types
# simples → sérialisable JSON tel quel. Append déterministe (aucun horodatage
# horloge, aucun id non déterministe).

from __future__ import annotations

CLE_JOURNAL = "automate_journal"

# Ordre CANONIQUE des catégories pour une VUE triée (filtre.trier). C'est l'ordre
# du raisonnement : ce que je perçois → ce que je diagnostique → ce que je planifie
# → ce que je fais → ce qui en résulte. N'affecte JAMAIS l'ordre d'append (qui reste
# chronologique) ; sert uniquement à présenter un tick lisiblement.
_RANG_CATEGORIE = {
    "perception": 0,
    "diagnostic": 1,
    "plan": 2,
    "geste": 3,
    "geste_coupe": 4,
    "veille": 5,
    "impasse": 6,
    "consequence": 7,
    "resultat": 8,
}


def journal(game_state: dict) -> list:
    """Le journal de l'automate dans `game_state` (créé à la volée, opt-in)."""
    return game_state.setdefault(CLE_JOURNAL, [])


def _commun(categorie: str, semaine: int, niveau: int, *,
            objectif_id: str | None = None, espece: str | None = None,
            zone: tuple | None = None, detail: dict | None = None) -> dict:
    """Squelette d'une ligne au SCHÉMA COMMUN (champs dans un ordre stable). Les
    catégories NEUVES (D87 ②-④) portent toute leur charge dans `detail` — jamais du
    texte libre : le rendu texte se DÉRIVE des champs (filtre.rendre)."""
    return {
        "categorie": categorie,
        "semaine": semaine,
        "niveau": niveau,
        "objectif_id": objectif_id,
        "espece": espece,
        "zone": zone,
        "detail": detail if detail is not None else {},
    }


# ---------------------------------------------------------------------------------
# Constructeurs LEGACY (D78) — clés à plat conservées, champs communs AJOUTÉS.
# ---------------------------------------------------------------------------------

def entree(semaine: int, tile_id: str, cible: str, facteur: str,
           geste: str, resultat: str, objectif_id: str | None = None) -> dict:
    """Entrée de journal pour un GESTE joué (dict JSON-sérialisable, ordre stable).
    `categorie="geste"` (niveau 0 = décision). `objectif_id` (④, §8) = l'objectif
    servi par ce geste, ou None — clé de filtrage de l'onglet (onglet.py). Les
    champs communs `niveau/espece/zone` sont ajoutés (espece/zone=None pour le
    legacy : la position vivante est déjà encodée dans `cible`)."""
    return {
        "categorie": "geste",
        "semaine": semaine,
        "niveau": 0,
        "espece": None,
        "zone": None,
        "tile_id": tile_id,
        "cible": cible,
        "facteur_limitant": facteur,
        "geste": geste,
        "resultat": resultat,
        "objectif_id": objectif_id,
    }


def entree_impasse(semaine: int, tile_id: str, cible: str, facteur: str,
                   cause: str) -> dict:
    """Entrée de journal pour une IMPASSE (§7) — un facteur limitant diagnostiqué
    sans geste-réponse applicable (« trou de gameplay »). `categorie="impasse"`
    (niveau 0) ; `cause` = type d'impasse (impasses.py). rapport.py agrège sur
    `(cause, facteur_limitant, tile_id)` → clés à plat conservées."""
    return {
        "categorie": "impasse",
        "semaine": semaine,
        "niveau": 0,
        "objectif_id": None,
        "espece": None,
        "zone": None,
        "tile_id": tile_id,
        "cible": cible,
        "facteur_limitant": facteur,
        "cause": cause,
    }


def entree_consequence(semaine: int, type_: str, detail: str) -> dict:
    """Entrée de journal pour une CONSÉQUENCE d'un geste (§6) : `type ∈ {deblocage,
    palier, mort, objectif}` ; `detail` = le verbe ouvert, le franchissement
    `objet:avant->après`, l'identité de la plante morte, ou `id:accompli`.
    `categorie="consequence"` (niveau 1 = détail). NB : ici `detail` est un STR
    historique (D78), distinct du `detail` dict des catégories neuves — les deux
    coexistent sans se marcher dessus (clés/catégories disjointes)."""
    return {
        "categorie": "consequence",
        "semaine": semaine,
        "niveau": 1,
        "objectif_id": None,
        "espece": None,
        "zone": None,
        "type": type_,
        "detail": detail,
    }


# ---------------------------------------------------------------------------------
# Constructeurs NEUFS (D87) — schéma commun, charge dans `detail`. AUCUN n'est encore
# APPELÉ par la boucle au tronçon ① : les tronçons ②-④ les brancheront.
# ---------------------------------------------------------------------------------

def entree_perception(semaine: int, *, espece: str | None = None,
                      zone: tuple | None = None, objectif_id: str | None = None,
                      detail: dict | None = None) -> dict:
    """PERCEPTION fine (niveau 2) : ce que l'automate SAIT d'un acteur/plot au moment
    de décider (état vivant sondé, disponibilité graine/plot…). `detail` porte les
    faits observés (ex. `{graine_banque: True, plot_libre: (t,r,c)}`)."""
    return _commun("perception", semaine, 2, objectif_id=objectif_id,
                   espece=espece, zone=zone, detail=detail)


def entree_diagnostic(semaine: int, *, espece: str | None = None,
                      zone: tuple | None = None, objectif_id: str | None = None,
                      detail: dict | None = None) -> dict:
    """DIAGNOSTIC (niveau 1) : facteur limitant retenu ou sous-but manquant identifié
    (ex. `{sous_but: "adulte_present", manque: "graine"}`)."""
    return _commun("diagnostic", semaine, 1, objectif_id=objectif_id,
                   espece=espece, zone=zone, detail=detail)


def entree_plan(semaine: int, *, objectif_id: str | None = None,
                espece: str | None = None, zone: tuple | None = None,
                detail: dict | None = None) -> dict:
    """PLAN (niveau 0 = décision) : le prochain geste créatif retenu par le chaînage
    arrière (ex. `{sous_but: "graine_en_banque", raison: "chainon_manquant"}`)."""
    return _commun("plan", semaine, 0, objectif_id=objectif_id,
                   espece=espece, zone=zone, detail=detail)


def entree_geste_coupe(semaine: int, *, espece: str | None = None,
                       zone: tuple | None = None, objectif_id: str | None = None,
                       detail: dict | None = None) -> dict:
    """GESTE COUPÉ (niveau 1) : un geste candidat NON exécuté ce tick, et pourquoi
    (`detail = {verbe, cause: budget|survie|veille}`). Rend visible la préemption
    survie > créatif (③) et le budget-cut de Vigueur — sans quoi le raisonnement
    serait muet sur ce qu'il a renoncé à faire."""
    return _commun("geste_coupe", semaine, 1, objectif_id=objectif_id,
                   espece=espece, zone=zone, detail=detail)


def entree_veille(semaine: int, *, objectif_id: str | None = None,
                  espece: str | None = None, zone: tuple | None = None,
                  detail: dict | None = None) -> dict:
    """VEILLE (niveau 0) : l'objectif reste ACTIF mais aucun geste créatif n'est
    faisable maintenant → on attend un DÉCLENCHEUR (`detail = {chainon, source}`,
    ex. `{chainon: "graine", source: "magazine_verrouille"}`). Émise 1× par chaînon
    (④), pas à chaque tick."""
    return _commun("veille", semaine, 0, objectif_id=objectif_id,
                   espece=espece, zone=zone, detail=detail)


def entree_resultat(semaine: int, *, objectif_id: str | None = None,
                    espece: str | None = None, zone: tuple | None = None,
                    detail: dict | None = None) -> dict:
    """RÉSULTAT (niveau 1) : issue d'un sous-but ou d'un objectif (levée constatée,
    progression, objectif accompli — `detail = {issue, ...}`). Trace le bouclage du
    moyens-fins côté effets observés (④)."""
    return _commun("resultat", semaine, 1, objectif_id=objectif_id,
                   espece=espece, zone=zone, detail=detail)


def consigner(game_state: dict, entry: dict) -> None:
    """Ajoute une entrée au journal (append → ordre chronologique déterministe)."""
    journal(game_state).append(entry)
