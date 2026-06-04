"""
SYMBIOSE — sim/maitrise.py
Couche MAÎTRISE JOUEUR (D12, tronçon i1) — le *cœur* de la maîtrise, miroir
structurel de la couche Vigueur (`sim/vigueur.py`).

Spec de référence : `data/code/CONCEPTION_MAITRISE.md`.
  §1   l'objet de maîtrise = unité atomique, paliers 0..5, catalogue-agnostique.
  §2.1 découverte (0→1) gratuite, par simple observation.
  §2.3 courbe de difficulté logarithmique : preuves(k) ≈ ceil(BASE·R**(k-1)).
  §2.4 réversibilité MONOTONE : un palier ne se perd jamais.
  §6   méta-état PAR AVATAR, vivant AU-DESSUS du tick écologique déterministe.

Principe directeur (§6, identique à la Vigueur) : cette couche ne fait JAMAIS
avancer la simulation écologique. Le golden écologique (`tests/test_golden.py`)
est une succession spontanée *sans joueur* → aucune clé `maitrise` → no-op
strict. Si le golden bouge, c'est un BUG (fuite dans le tick), pas un re-figeage.

Périmètre i1 (le reste est gated, cf. `sprints/sprint_D12_impl/00_etat.md`) :
  - PAS d'agrégats (complétude-ratio / accumulation-log)       → i2
  - PAS de spillover famille                                   → i2
  - PAS de remplissage de `palier_bonus`                       → i2
  - PAS de seam `cout_action`                                  → i3
  - PAS de détection automatique de succès (zéro hook tick)    → i4
Ici, les preuves arrivent UNIQUEMENT par appel direct d'API (injection).
"""
from __future__ import annotations

import math

# --- Courbe de difficulté (§2.3) -------------------------------------------
# Nombre de preuves pour franchir k → k+1 : ceil(BASE * R**(k-1)).
# PLACEHOLDERS NOMMÉS — *à calibrer post-test (D12.4)*. Valeurs choisies pour
# rendre la courbe visible et croissante dans les golden (2, 4, 8, 16).
PREUVES_BASE = 2     # BASE — preuves pour le premier franchissement (1→2)
PREUVES_R    = 2     # R    — facteur géométrique (croissance des paliers)
PALIER_MAX   = 5     # transcendant (CLAUDE.md) — on ne franchit jamais au-delà


# --- État joueur (miroir de vigueur.ensure_player) -------------------------
def ensure_player_maitrise(game_state: dict, player: str) -> dict:
    """Crée (si besoin) et renvoie la tranche maîtrise d'un joueur. C'est le
    geste d'OPT-IN (§6) : tant qu'aucun joueur n'est enregistré, `game_state`
    n'a pas de clé `maitrise` et le tick reste un no-op strict (golden intact).

    Invariant : un objet n'entre dans `objets` qu'au palier ≥ 1 (découvert).
    L'absence d'un objet du dict EST son palier 0 (inconnu)."""
    mait = game_state.setdefault("maitrise", {})
    return mait.setdefault(player, {"objets": {}})


def palier(game_state: dict, player: str, objet: str) -> int:
    """Lecture pure du palier d'un objet ; `0` si l'objet est inconnu (jamais
    découvert). Ne crée RIEN (lecture d'un inconnu = 0, sans opt-in)."""
    mait = game_state.get("maitrise")
    if not mait:
        return 0
    st = mait.get(player)
    if not st:
        return 0
    o = st["objets"].get(objet)
    return o["palier"] if o else 0


# --- Découverte (§2.1, gratuite) -------------------------------------------
def decouvrir(game_state: dict, player: str, objet: str) -> bool:
    """Passage `0 → 1` par simple observation (§2.1) : gratuit, aucun succès
    requis. Idempotent : ne fait rien si l'objet est déjà découvert (palier ≥ 1).
    Renvoie `True` ssi une *nouvelle* découverte a eu lieu (i2 s'en servira pour
    le gain ponctuel de Vigueur, §4.3 ; ici on renvoie juste le booléen)."""
    st = ensure_player_maitrise(game_state, player)
    if objet in st["objets"]:               # déjà au palier ≥ 1 (invariant)
        return False
    st["objets"][objet] = {"palier": 1, "preuves": 0}
    return True


# --- Progression par preuves (§2.2/§2.3, monotone §2.4) --------------------
def preuves_requises(k: int) -> int:
    """Preuves pour franchir `k → k+1` (§2.3), `k ∈ {1,2,3,4}` (pas de
    franchissement au-delà de PALIER_MAX). Courbe géométrique ⇒ début rapide,
    haut paliers lents (un joueur qui sait enchaîne le début, ralentit vers
    l'expertise — cf. spec §2.3)."""
    return math.ceil(PREUVES_BASE * PREUVES_R ** (k - 1))


def enregistrer_preuve(game_state: dict, player: str, objet: str) -> int:
    """Le cœur. Crédite UNE preuve à l'objet, puis franchit autant de paliers
    que le crédit le permet (consommation CUMULATIVE : le reliquat reste au
    crédit du palier suivant). Renvoie le palier courant après mise à jour.

    Auto-découverte (défaut acté §i1) : enregistrer une preuve sur un objet
    inconnu le découvre d'abord (0→1) — une preuve implique qu'on l'a observé.

    MONOTONE (§2.4) : un palier ne redescend jamais ; il n'existe aucune
    fonction de décrément. Plafonné à PALIER_MAX (§1)."""
    st = ensure_player_maitrise(game_state, player)
    o = st["objets"].get(objet)
    if o is None:                           # auto-découverte (0→1) puis crédit
        o = {"palier": 1, "preuves": 0}
        st["objets"][objet] = o
    o["preuves"] += 1
    while o["palier"] < PALIER_MAX and o["preuves"] >= preuves_requises(o["palier"]):
        o["preuves"] -= preuves_requises(o["palier"])
        o["palier"] += 1
    return o["palier"]
