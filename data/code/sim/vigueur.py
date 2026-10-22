"""
SYMBIOSE — sim/vigueur.py
Couche Vigueur JOUEUR (D11, sous-sprint 1) — le seul *vrai nouvel état* de la
conception Vigueur (cf. `docs/joueur/vigueur/conception_vigueur.md` §2).

Deux strates distinctes (spec §0) :
  1. Cœur écologique déterministe (le tick `engine`) — INCHANGÉ. La Vigueur des
     plantes y sera une façade dérivée read-only (sous-sprint 3), pas un état.
  2. Couche gameplay joueur (CE module) — event-driven, vit dans
     `game_state["vigueur"]` PAR joueur, AU-DESSUS du tick. C'est le seul système
     réellement nouveau.

Principe directeur (spec §0/§5) : cette couche ne fait JAMAIS avancer la
simulation écologique par elle-même. Le golden écologique (`tests/test_golden.py`)
ne contient aucun joueur — donc aucune clé `vigueur` — et reste un no-op strict :
le hook côté `engine` est gardé par `if "vigueur" in game_state`. Si le golden
bouge, c'est un bug (quelque chose a fui dans le tick).

Interface paliers (D12, tronçon i2) : `palier_bonus(game_state, player)` délègue
désormais à `sim/maitrise.py` (accumulation-log §4.1). Le stub neutre 1.0 a vécu ;
la *forme* du pont (plafond/régen × `palier_bonus`, déjà câblés ci-dessous) est
INCHANGÉE — D12 ne fait que remplir la valeur. Seule retouche assumée vs le plan
§4.1 (point ouvert i2, défaut (a) acté) : la signature gagne `game_state`, car
l'accumulation vit PAR JOUEUR dans `game_state["maitrise"]` (pas d'état caché
module-level → déterminisme préservé). Sens de dépendance : Vigueur → Maîtrise
(la capacité de Vigueur dérive de la maîtrise), jamais l'inverse.
"""
from __future__ import annotations

from sim import maitrise

# Modèle de base (chiffres CLAUDE.md / spec §2, *à calibrer post-test*).
MAX_BASE   = 100.0   # plafond de Vigueur joueur avant bonus paliers
REGEN_BASE = 10.0    # régen passive par semaine simulée


# --- Interface paliers (D12) — remplie par la couche Maîtrise (§4.1) --------
def palier_bonus(game_state: dict, player: str) -> float:
    """Multiplicateur de maîtrise (D12, §4.1), délégué à `maitrise.palier_bonus`.
    Vaut 1.0 tant qu'aucune maîtrise n'est acquise (accumulation 0) → la couche
    Vigueur sans maîtrise reste à l'identique (golden intact)."""
    return maitrise.palier_bonus(game_state, player)


# --- État joueur -----------------------------------------------------------
def ensure_player(game_state: dict, player: str) -> dict:
    """Crée (si besoin) et renvoie la tranche Vigueur d'un joueur. C'est le geste
    d'OPT-IN : tant qu'aucun joueur n'est enregistré, `game_state` n'a pas de clé
    `vigueur` et le tick écologique reste un no-op strict (golden intact)."""
    vig = game_state.setdefault("vigueur", {})
    return vig.setdefault(player, {"courante": MAX_BASE, "max_base": MAX_BASE})


def vigueur_max(game_state: dict, player: str) -> float:
    """Plafond courant = max_base du joueur × bonus de maîtrise (spec §2.3)."""
    st = ensure_player(game_state, player)
    return st["max_base"] * palier_bonus(game_state, player)


def regen_rate(game_state: dict, player: str) -> float:
    """Vitesse de régen passive = base × bonus de maîtrise (spec §2.3) — la
    compréhension écologique fait se ressourcer plus vite (CLAUDE.md)."""
    return REGEN_BASE * palier_bonus(game_state, player)


# --- Primitives de transaction (D11, sous-sprint 2) ------------------------
def spend(game_state: dict, player: str, cost: float) -> float:
    """Débite la Vigueur du joueur et renvoie le RATIO d'effort réalisé : 1.0 si
    le coût est entièrement payé, sinon `courante / cost` ∈ [0, 1[. Draine
    `min(cost, courante)` — plancher 0, jamais de dette (spec §2/§3 : on dépense
    ce qu'on a). Le sens du ratio < 1 appartient à l'appelant (cf. `sim/actions.py`)
    : action graduée tronquée (récolte partielle) ou action binaire échouée
    (déracinage/écrasement à vide).

    Réglage de TEST « Vigueur infinie » (Paramètres du launcher, demande Nico
    2026-10-22) : flag OPTIONNEL `game_state["options"][player]["vigueur_infinie"]`
    → tout geste est payé en entier SANS débit (ratio 1.0, courante intacte). C'est
    le SEUL point de débit de la Vigueur joueur : un seul garde suffit. Absent →
    comportement normal (golden : aucun joueur, aucune option)."""
    if cost <= 0:
        return 1.0
    if game_state.get("options", {}).get(player, {}).get("vigueur_infinie", False):
        return 1.0
    st = ensure_player(game_state, player)
    courante = st["courante"]
    ratio = 1.0 if courante >= cost else courante / cost
    st["courante"] = max(0.0, courante - cost)
    return ratio


def gain(game_state: dict, player: str, amount: float) -> None:
    """Crédite la Vigueur du joueur, plafonnée à `vigueur_max` (spec §2.1/§2.3).
    No-op si `amount <= 0`."""
    if amount <= 0:
        return
    st = ensure_player(game_state, player)
    cap = st["max_base"] * palier_bonus(game_state, player)
    st["courante"] = min(cap, st["courante"] + amount)


# --- Cycle (appelé par le tick, GARDÉ côté engine) -------------------------
def tick_player_vigueur(game_state: dict) -> None:
    """Régen passive hebdomadaire, plafonnée (spec §2.1). No-op si aucune couche
    joueur. Modifie `game_state["vigueur"]` en place ; ne touche à rien d'écolo."""
    vig = game_state.get("vigueur")
    if not vig:
        return
    for player, st in vig.items():
        cap = st["max_base"] * palier_bonus(game_state, player)
        st["courante"] = min(cap, st["courante"] + REGEN_BASE * palier_bonus(game_state, player))


def refill_saison(game_state: dict) -> None:
    """Plein au passage de saison (spec §2.1) : `courante = vigueur_max`. No-op
    si aucune couche joueur."""
    vig = game_state.get("vigueur")
    if not vig:
        return
    for player, st in vig.items():
        st["courante"] = st["max_base"] * palier_bonus(game_state, player)
