# SYMBIOSE — tools/jardinier_auto/objectifs.py
# OBJECTIFS de l'automate (§8) — germe du système de quêtes (le système complet =
# DETTE D79, HORS SCOPE). Un objectif = `(geste, quantite, cible)` : ex.
# `Objectif("recolter", 3, "tomate")`. Injectable au DÉBUT de la sim ou à tout tick
# (« phase de planification » = temps figé côté automate). Effet double :
#   1. BIAIS de priorisation — un geste servant un objectif actif passe devant les
#      soins de routine (biais, PAS exclusivité : le jardin reste tenu, cf. boucle).
#   2. COMPTAGE de progression — chaque geste-cible réussi incrémente l'objectif ;
#      à `quantite` atteinte → accompli (consigné en conséquence, §6).
#
# État opt-in sous `game_state["automate_objectifs"]` : un dict `{id: record}` où
# `record = {objectif, progression, semaine_debut, semaine_fin}`. `semaine_fin` reste
# None tant que l'objectif est actif ; renseignée au tick d'accomplissement (sert la
# FENÊTRE de l'onglet, §8/onglet.py). Le dict garde l'ordre d'insertion (déterministe,
# add piloté par l'appelant) ; toute LISTE produite est triée par `id` (philo #3).
#
# ATTEIGNABILITÉ (§7) : une cible absente du monde ET sans moyen de l'obtenir (pas de
# graine en banque-joueur, pas d'espèce de succession) → impasse `objectif_inatteignable`
# (détectée une seule fois par la boucle, cf. `est_atteignable`).

from __future__ import annotations
from dataclasses import dataclass

from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE, WEED_CATALOGUE

CLE_OBJECTIFS = "automate_objectifs"

# Bonus de priorité appliqué (dans la boucle) à un geste servant un objectif actif.
# Grand devant les priorités de la table (10-14) → l'objectif passe en tête du tri
# ET du budget de Vigueur. Reste un BIAIS : les autres soins s'exécutent ensuite si
# le budget le permet (mode libre : tout passe de toute façon).
BONUS_OBJECTIF = 100


@dataclass(frozen=True)
class Objectif:
    """Un objectif donné à l'automate. `geste` = verbe visé (ex. "recolter") ;
    `quantite` = nombre de gestes-cible réussis à atteindre ; `cible` = clé d'espèce
    du catalogue (ou, à terme, type de structure — D79) ; `id` = identifiant stable
    et unique (clé d'état + filtre de l'onglet). Frozen : un objectif est une
    constante ; sa PROGRESSION vit à part dans `game_state` (philo #3)."""

    geste: str
    quantite: int
    cible: str
    id: str


def _catalogue() -> dict:
    """Fusion des catalogues d'espèces nommées (cultivées + pérennes). Une cible
    d'objectif est une CLÉ de ce dict ; la valeur est la `plant_class` à comparer."""
    return {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}


def classe_cible(cible: str):
    """La `plant_class` correspondant à une clé d'espèce, ou None si la clé est
    inconnue du catalogue (→ objectif d'emblée inatteignable, §7)."""
    return _catalogue().get(cible)


def _etat(game_state: dict) -> dict:
    """Le registre d'objectifs dans `game_state` (créé à la volée, opt-in strict :
    aucune clé tant qu'aucun objectif n'a été ajouté)."""
    return game_state.setdefault(CLE_OBJECTIFS, {})


def ajouter_objectif(game_state: dict, obj: Objectif) -> None:
    """Injecte un objectif (début de sim OU entre deux ticks). `semaine_debut` = la
    semaine courante lue dans `game_state` — borne basse de la fenêtre de l'onglet.
    Idempotent sur l'`id` : un ré-ajout écrase le record (repart de zéro)."""
    _etat(game_state)[obj.id] = {
        "objectif": obj,
        "progression": 0,
        "semaine_debut": game_state.get("week", 0),
        "semaine_fin": None,
    }


def objectifs_actifs(game_state: dict) -> list:
    """Les `Objectif` encore actifs (non accomplis), triés par `id` (déterminisme)."""
    reg = game_state.get(CLE_OBJECTIFS, {})
    return [reg[oid]["objectif"] for oid in sorted(reg)
            if reg[oid]["semaine_fin"] is None]


def progression(game_state: dict, obj_id: str) -> int:
    """Compteur courant d'un objectif (0 si inconnu)."""
    rec = game_state.get(CLE_OBJECTIFS, {}).get(obj_id)
    return rec["progression"] if rec else 0


def est_accompli(game_state: dict, obj_id: str) -> bool:
    """Vrai si l'objectif a atteint sa quantité (fenêtre close). Prend `game_state`
    car la progression vit hors de l'`Objectif` (frozen) — déviation assumée de la
    signature `est_accompli(obj)` du kickoff : l'état ne peut PAS vivre sur un frozen."""
    rec = game_state.get(CLE_OBJECTIFS, {}).get(obj_id)
    return bool(rec) and rec["semaine_fin"] is not None


def incrementer(game_state: dict, obj_id: str) -> bool:
    """+1 sur la progression d'un objectif actif. Renvoie True SSI ce geste vient de
    l'ACCOMPLIR (franchit `quantite`) — l'appelant consigne alors la conséquence.
    No-op (False) sur un objectif inconnu ou déjà accompli."""
    rec = game_state.get(CLE_OBJECTIFS, {}).get(obj_id)
    if rec is None or rec["semaine_fin"] is not None:
        return False
    rec["progression"] += 1
    if rec["progression"] >= rec["objectif"].quantite:
        rec["semaine_fin"] = game_state.get("week", 0)
        return True
    return False


def marquer_inatteignable_signale(game_state: dict, obj_id: str) -> bool:
    """Marque (une seule fois) qu'un objectif a été signalé inatteignable. Renvoie True
    au PREMIER signalement (→ l'appelant consigne l'impasse), False ensuite : évite de
    noyer le journal d'un même trou de gameplay à chaque tick (§7)."""
    rec = game_state.get(CLE_OBJECTIFS, {}).get(obj_id)
    if rec is None or rec.get("inatteignable_signale"):
        return False
    rec["inatteignable_signale"] = True
    return True


def sert(obj: Objectif, verbe: str, plant) -> bool:
    """Ce geste (`verbe` sur `plant`) sert-il `obj` ? Vrai ssi le verbe correspond ET
    l'espèce de `plant` est la cible. Base du biais de priorisation et du comptage."""
    if obj.geste != verbe:
        return False
    cls = classe_cible(obj.cible)
    return cls is not None and getattr(plant, "plant_class", None) is cls


def objectifs_servis(actifs: list, verbe: str, plant) -> list:
    """Sous-liste (ordre d'entrée conservé) des objectifs actifs servis par ce geste.
    `actifs` est déjà trié (objectifs_actifs) → résultat déterministe."""
    return [o for o in actifs if sert(o, verbe, plant)]


def est_atteignable(game_state: dict, obj: Objectif) -> bool:
    """La cible de `obj` peut-elle exister dans l'état courant du monde (§7) ? Vraie si
    l'une des voies est ouverte :
      - une plante VIVANTE de l'espèce est déjà présente (donc récoltable/atteignable) ;
      - une graine de l'espèce dort en banque-joueur (l'automate pourrait la semer) ;
      - l'espèce fait partie de la succession spontanée (elle peut lever seule).
    Sinon → inatteignable (impasse). Lecture PURE (itère les listes `tiles`)."""
    cls = classe_cible(obj.cible)
    if cls is None:
        return False                                  # cible hors catalogue
    for tile in game_state.get("tiles", []):
        for plant in tile.plants:
            if plant.is_alive and plant.plant_class is cls:
                return True
    bank = game_state.get("player_seed_bank")
    if bank is not None and bank.count(obj.cible) > 0:
        return True
    return cls in WEED_CATALOGUE.values()
