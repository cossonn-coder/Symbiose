"""
SYMBIOSE — sim/vigueur.py
Couche Vigueur JOUEUR (D11, sous-sprint 1) — le seul *vrai nouvel état* de la
conception Vigueur (cf. `data/code/CONCEPTION_VIGUEUR.md` §2).

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

Interface paliers STUBBÉE (spec §2.3, décision actée) : `palier_bonus()` renvoie
1.0 tant que D12 (paliers de maîtrise) n'existe pas. Quand les paliers arriveront,
ils rempliront cette fonction SANS retoucher cette couche.
"""
from __future__ import annotations

# Modèle de base (chiffres CLAUDE.md / spec §2, *à calibrer post-test*).
MAX_BASE   = 100.0   # plafond de Vigueur joueur avant bonus paliers
REGEN_BASE = 10.0    # régen passive par semaine simulée


# --- Interface paliers (D12) — stubbée -------------------------------------
def palier_bonus(player: str) -> float:
    """Multiplicateur de maîtrise (D12). Stub : 1.0 tant que les paliers
    n'existent pas. Quand D12 arrivera, il remplit cette fonction SANS toucher
    au reste de la couche Vigueur (même découplage que météo↔paliers)."""
    return 1.0


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
    return st["max_base"] * palier_bonus(player)


def regen_rate(game_state: dict, player: str) -> float:
    """Vitesse de régen passive = base × bonus de maîtrise (spec §2.3) — la
    compréhension écologique fait se ressourcer plus vite (CLAUDE.md)."""
    return REGEN_BASE * palier_bonus(player)


# --- Cycle (appelé par le tick, GARDÉ côté engine) -------------------------
def tick_player_vigueur(game_state: dict) -> None:
    """Régen passive hebdomadaire, plafonnée (spec §2.1). No-op si aucune couche
    joueur. Modifie `game_state["vigueur"]` en place ; ne touche à rien d'écolo."""
    vig = game_state.get("vigueur")
    if not vig:
        return
    for player, st in vig.items():
        cap = st["max_base"] * palier_bonus(player)
        st["courante"] = min(cap, st["courante"] + REGEN_BASE * palier_bonus(player))


def refill_saison(game_state: dict) -> None:
    """Plein au passage de saison (spec §2.1) : `courante = vigueur_max`. No-op
    si aucune couche joueur."""
    vig = game_state.get("vigueur")
    if not vig:
        return
    for player, st in vig.items():
        st["courante"] = st["max_base"] * palier_bonus(player)
