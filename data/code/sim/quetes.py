"""
SYMBIOSE — sim/quetes.py
Le SYSTÈME DE QUÊTES côté JOUEUR (D79, tronçon ①).
Spec de référence : `docs/joueur/automate/conception_quetes.md`.

Une quête est un DÉSIR posé par une voix (une lettre), et une LECTURE passive de
l'état du monde pour savoir s'il est comblé — jamais un ordre, jamais un pilote
(conception §1). La quête OBSERVE, elle ne pousse aucune plante (philo #1/#2).

DISTINCT DU HARNAIS AUTOMATE (F1) : `tools/jardinier_auto/objectifs.py` est le
cœur objectif de l'AUTOMATE (branché derrière `automate on`, ignoré par les gestes
du joueur humain). D79 est un module MOTEUR joueur NEUF : il PARTAGE la forme de
données `(geste, quantite, cible)` mais possède son propre état (sauvegardé) et
son propre point de comptage — un HOOK sur le dispatch des gestes joueur, pas la
boucle automate. Le code est indépendant (aucun import croisé).

GARDE-FOU DE COUCHE : `quetes` est au niveau `sim`, jamais importé par `engine` /
`fields` / `plants`. Il n'importe que `plants.catalogue` (résolution des cibles),
comme `objectifs.py`. OPT-IN STRICT : `game_state["quetes"]` n'existe qu'après un
`ajouter_quete()`. Le golden écologique tourne SANS joueur ni quête → aucune clé
→ `notifier_geste()` est un no-op total → **golden intact**.

FAMILLES DE CONDITIONS (conception §4, mini-catalogue déclaratif FERMÉ) :
  - ① ICI : `("recolte_cumulee", geste, quantite, cible)` — comptée par HOOK geste.
  - ② (à venir) : `hauteur_min` / `floraison_min` / `nombre_vivant_min` — lues sur
    le snapshot hors tick.
L'aiguillage se fait sur le TAG (1er élément de la condition) → ② ajoute ses types
sans toucher l'existant.

État (miroir du pattern `objectifs.py`, philo #3 — la progression vit HORS du
frozen) :
    game_state["quetes"][id] = {
        "quete": Quete, "progression": int,
        "semaine_debut": int, "semaine_fin": int|None,  # None tant qu'active
    }
Le dict garde l'ordre d'insertion (add piloté par l'appelant) ; toute LISTE
produite est triée par `id` (déterminisme).
"""
from __future__ import annotations
from dataclasses import dataclass

from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE

CLE_QUETES = "quetes"


@dataclass(frozen=True)
class Quete:
    """Une quête posée par une lettre (voix épistolaire, conception §7). Frozen :
    une quête est une CONSTANTE de contenu ; sa PROGRESSION vit à part dans
    `game_state` (philo #3). Champs :
      - `id` : identifiant stable et unique (clé d'état + tri déterministe) ;
      - `donneur` : prénom qui signe la lettre (« Marcel »), pas un PNJ (V1) ;
      - `condition` : tuple déclaratif `(tag, ...)` — pour ① le seul tag actif est
        `"recolte_cumulee"` : `("recolte_cumulee", geste, quantite, cible)` ;
      - `recompense` : POSÉ ici, traité aux tronçons ③/④ (opaque pour ①) ;
      - `declencheur` : POSÉ ici, traité au tronçon ③ (opaque pour ①).
    `recompense`/`declencheur` sont typés `object` (catalogue déclaratif ouvert,
    V3) : ① ne les interprète pas, il les transporte."""

    id: str
    donneur: str
    condition: tuple
    recompense: object = None
    declencheur: object = None


def _catalogue() -> dict:
    """Fusion des catalogues d'espèces nommées (cultivées + pérennes). Une cible de
    condition est une CLÉ de ce dict ; la valeur est la `plant_class` à comparer."""
    return {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}


def _classe_cible(cible: str):
    """La `plant_class` correspondant à une clé d'espèce, ou None si la clé est
    inconnue du catalogue (→ cible inatteignable, gérée au tronçon ③)."""
    return _catalogue().get(cible)


def _etat(game_state: dict) -> dict:
    """Le registre de quêtes dans `game_state` (créé à la volée, opt-in strict :
    aucune clé tant qu'aucune quête n'a été ajoutée → golden intact)."""
    return game_state.setdefault(CLE_QUETES, {})


# --- API d'écriture ----------------------------------------------------------
def ajouter_quete(game_state: dict, quete: Quete) -> None:
    """Pose une quête (arrivée d'une lettre). `semaine_debut` = semaine courante lue
    dans `game_state`. Idempotent sur l'`id` : un ré-ajout écrase le record (repart
    de zéro). C'est le SEUL geste d'opt-in : avant lui, `game_state` n'a pas de clé
    `quetes` et `notifier_geste` est un no-op strict."""
    _etat(game_state)[quete.id] = {
        "quete": quete,
        "progression": 0,
        "semaine_debut": game_state.get("week", 0),
        "semaine_fin": None,
    }


# --- API de lecture ----------------------------------------------------------
def quetes_actives(game_state: dict) -> list:
    """Les `Quete` encore actives (non accomplies), triées par `id` (déterminisme)."""
    reg = game_state.get(CLE_QUETES, {})
    return [reg[qid]["quete"] for qid in sorted(reg)
            if reg[qid]["semaine_fin"] is None]


def progression(game_state: dict, quete_id: str) -> int:
    """Compteur courant d'une quête (0 si inconnue)."""
    rec = game_state.get(CLE_QUETES, {}).get(quete_id)
    return rec["progression"] if rec else 0


def est_accomplie(game_state: dict, quete_id: str) -> bool:
    """Vrai si la quête est comblée (fenêtre close). La progression vit hors du
    `Quete` frozen → on prend `game_state`, pas la quête."""
    rec = game_state.get(CLE_QUETES, {}).get(quete_id)
    return bool(rec) and rec["semaine_fin"] is not None


# --- Matching d'une condition cumulée ---------------------------------------
def _sert_recolte_cumulee(condition: tuple, verbe: str, plant) -> bool:
    """Ce geste (`verbe` sur `plant`) fait-il avancer une condition
    `("recolte_cumulee", geste, quantite, cible)` ? Vrai ssi le verbe est le geste
    visé ET l'espèce de `plant` est la cible. Miroir de `objectifs.sert`."""
    _tag, geste, _quantite, cible = condition
    if geste != verbe:
        return False
    cls = _classe_cible(cible)
    return cls is not None and getattr(plant, "plant_class", None) is cls


# --- Le HOOK : comptage sur le geste joueur (F2) -----------------------------
def notifier_geste(game_state: dict, player: str, verbe: str, plant) -> None:
    """HOOK appelé APRÈS un geste JOUEUR RÉUSSI (depuis le dispatch du pont,
    `tools/simserver/plante_route.py`). Pour chaque quête `recolte_cumulee` ACTIVE
    servie par ce geste : +1 sur la progression ; à l'atteinte de la `quantite`, la
    quête se CLÔT (`semaine_fin`) et un événement est ÉMIS au ledger (`_consigner`).

    Comptage par hook, PAS par re-parse du ledger (F2). No-op strict si aucune quête
    (opt-in) → golden intact. `player` est accepté pour la symétrie avec les hooks
    joueur (`detecter`/`tick_player_vigueur`) et l'évolution multi-avatar ; l'état
    des quêtes est mono-joueur pour l'instant (comme `objectifs.py`), non indexé par
    `player`. Itère les `id` TRIÉS (déterminisme, philo #3)."""
    reg = game_state.get(CLE_QUETES)
    if not reg:
        return
    for qid in sorted(reg):
        rec = reg[qid]
        if rec["semaine_fin"] is not None:
            continue
        cond = rec["quete"].condition
        if cond[0] != "recolte_cumulee":
            continue                       # ② branchera ses tags ici
        if not _sert_recolte_cumulee(cond, verbe, plant):
            continue
        rec["progression"] += 1
        if rec["progression"] >= cond[2]:
            rec["semaine_fin"] = game_state.get("week", 0)
            _consigner_accomplissement(game_state, rec["quete"])


def _consigner_accomplissement(game_state: dict, quete: Quete) -> None:
    """Émet une ligne de log PARSABLE à l'accomplissement (conception §6) — le
    canal EXISTANT `game_state["log"]`, consigné au ledger des voix au tick suivant
    (`journal.consigner`, qui vide le log). Une entrée carnet « j'ai porté … au
    voisin » pourra en NAÎTRE (câblage du parseur : tronçon ③, non fait ici — une
    ligne non reconnue est ignorée sans dommage). Marqueur ✉ (lettre), style des
    autres marqueurs du tick. Sans clé `log` (hors serveur) → no-op silencieux."""
    log = game_state.get("log")
    if log is None:
        return
    _tag, geste, quantite, cible = quete.condition
    log.append(f"✉ Quête accomplie ({quete.donneur}) : "
               f"{geste} ×{quantite} {cible}")
