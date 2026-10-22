"""
SYMBIOSE — sim/vision.py
La VISION du jardinier (sprint « le sol qui respire » ⑥, D111 §4) : manger un
champignon psychédélique ouvre une semaine où le jardin se LIT comme au palier
transcendant, où les êtres disent leurs besoins, et dont il reste un peu de savoir.

📖 Pédagogie — une LENTILLE, pas une maîtrise. La vision ne touche JAMAIS l'état de
maîtrise pendant l'effet : elle change ce que les lecteurs (carnet, encyclopédie,
info-bulle) VOIENT, via `palier_lu`, et rien d'autre. Ainsi la Vigueur max
(`maitrise.palier_bonus`), l'extension de terrain et le magazine, qui lisent
`maitrise.palier` directement, sont isolés par construction. Ce qui reste APRÈS
l'effet passe, lui, par la vraie voie (`maitrise.enregistrer_preuve`), borné.

État joueur : `game_state["vision"][player] = {debut, fin, overdose, survols}`
(dict JSON pur → futur save tel quel) ; absent = pas de vision. Calendrier :
mangé quand `week == w` (la semaine qu'on va simuler), la vision dure tant que
`week ≤ w + DUREE_VISION` → le reste de la semaine affichée PLUS une semaine
pleine (au moins 60 s de jeu, quel que soit le moment où l'on mange). Elle se
CLÔT au premier `step_week` qui dépasse `fin` (`clore_si_echue`, hors tick).

Couche `sim`, HORS TICK : le moteur ne l'importe jamais → golden NEUTRE. Zéro RNG.
"""
from __future__ import annotations

from sim import maitrise

DUREE_VISION = 1         # semaines pleines de vision après la semaine où l'on mange
SEUIL_SURVOLS = 3        # survols cumulés d'une espèce pendant la vision pour qu'il en reste un palier
# Plafond du palier DURABLE gagné : jamais jusqu'au transcendant (le savoir né d'une
# vision s'arrête à l'expertise — la non-action se mérite, elle ne s'avale pas).
PALIER_PLAFOND_VISION = maitrise.PALIER_MAX - 1


def etat(game_state: dict, player: str) -> dict | None:
    """Tranche vision du joueur (lecture pure), ou None."""
    return (game_state.get("vision") or {}).get(player)


def vision_active(game_state: dict, player: str) -> bool:
    """Vrai pendant l'effet (`week ≤ fin`). Lecture pure."""
    st = etat(game_state, player)
    return st is not None and game_state.get("week", 0) <= st["fin"]


def overdose_active(game_state: dict, player: str) -> bool:
    """Vrai si un 2ᵉ psychédélique a été avalé pendant l'effet en cours."""
    return vision_active(game_state, player) and etat(game_state, player)["overdose"]


def palier_lu(game_state: dict, player: str, objet: str) -> int:
    """Palier tel que le LISENT les voix (carnet, encyclopédie, info-bulle) :
    transcendant pendant la vision, le vrai palier sinon. À n'utiliser QUE pour
    afficher — tout ce qui fait gagner ou ouvre quelque chose lit `maitrise.palier`."""
    if vision_active(game_state, player):
        return maitrise.PALIER_MAX
    return maitrise.palier(game_state, player, objet)


def commencer(game_state: dict, player: str) -> str:
    """Avaler un psychédélique. Hors effet → nouvelle vision (« vision ») ; pendant
    l'effet → OVERDOSE jusqu'à la même fin, sans prolonger (« overdose »)."""
    if vision_active(game_state, player):
        game_state["vision"][player]["overdose"] = True
        return "overdose"
    w = game_state.get("week", 1)
    game_state.setdefault("vision", {})[player] = {
        "debut": w, "fin": w + DUREE_VISION, "overdose": False, "survols": {}}
    return "vision"


def noter_survol(game_state: dict, player: str, cle: str) -> None:
    """Un survol d'une espèce pendant la vision (+1). No-op hors effet."""
    if not vision_active(game_state, player) or not cle:
        return
    survols = game_state["vision"][player]["survols"]
    survols[cle] = survols.get(cle, 0) + 1


def _plus_un_palier(game_state: dict, player: str, cle: str) -> bool:
    """Exactement +1 palier sur `cle`, borné à PALIER_PLAFOND_VISION. Inconnue →
    découverte (0→1 est un palier). Le crédit est divisé par le spillover de
    famille pour qu'une espèce aux sœurs maîtrisées ne saute pas deux paliers."""
    p = maitrise.palier(game_state, player, cle)
    if p == 0:
        return maitrise.decouvrir(game_state, player, cle)
    if p >= PALIER_PLAFOND_VISION:
        return False
    st = maitrise.ensure_player_maitrise(game_state, player)
    manque = maitrise.preuves_requises(p) - st["objets"][cle]["preuves"]
    poids = manque / maitrise._facteur_spillover(st, cle)
    return maitrise.enregistrer_preuve(game_state, player, cle, poids=poids) > p


def clore_si_echue(game_state: dict, player: str) -> list[str]:
    """Fin de l'effet (appelé par le pont APRÈS un tick) : si `week > fin`, chaque
    espèce survolée au moins SEUIL_SURVOLS fois gagne UN palier durable (ordre trié
    → déterministe), puis la tranche est retirée. Renvoie les clés créditées ;
    [] si pas de vision ou effet en cours."""
    st = etat(game_state, player)
    if st is None or game_state.get("week", 0) <= st["fin"]:
        return []
    gagnees = [cle for cle in sorted(st["survols"])
               if st["survols"][cle] >= SEUIL_SURVOLS
               and _plus_un_palier(game_state, player, cle)]
    del game_state["vision"][player]
    if gagnees:   # mémorisé pour la notification de la vue (consommé au snapshot)
        game_state.setdefault("vision_reste", {})[player] = gagnees
    return gagnees


def reste_recent(game_state: dict, player: str) -> list[str]:
    """Clés gagnées à la dernière clôture, CONSOMMÉES à la lecture (signalées une
    fois, patron de `gestes_debloques_recents`)."""
    return game_state.get("vision_reste", {}).pop(player, [])


def bloc_joueur(game_state: dict, player: str) -> dict:
    """État lisible par la vue (`player.vision` du snapshot) — lecture pure."""
    st = etat(game_state, player)
    active = vision_active(game_state, player)
    return {"active": active, "overdose": bool(active and st["overdose"]),
            "fin": st["fin"] if active else None}
