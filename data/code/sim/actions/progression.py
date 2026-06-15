"""
SYMBIOSE — sim/actions/progression.py
Ponts maîtrise → Vigueur (CONCEPTION_MAITRISE §4.3) : la couche d'orchestration
qui traduit un événement de maîtrise (découverte, franchissement de palier) en
gain de Vigueur. `sim/maitrise.py` reste PUR (il ne crédite pas la Vigueur
lui-même) — exactement comme `manger`/`recolter` orchestrent déjà `gain`.
"""
from __future__ import annotations

from sim.vigueur import gain
from sim import maitrise as M
from .couts import FAIBLE, MODERE

# Sources PONCTUELLES de Vigueur liées à la maîtrise (CONCEPTION_MAITRISE §4.3) —
# placeholders nommés, *calibrage D12.4*. La découverte motive (petit +), le
# franchissement de palier récompense l'effort (+ plus net). Event-driven, hors
# tick (comme toute la couche Vigueur).
GAIN_DECOUVERTE = FAIBLE    # « chaque découverte donne envie d'en savoir plus » (§4.3)
GAIN_SUCCES     = MODERE    # « un jardinier actif est un jardinier vigoureux » (§4.3)


# --- Ponts maîtrise → Vigueur (§4.3) : orchestration au-dessus des deux couches
# `sim/maitrise.py` reste PUR (il ne crédite pas la Vigueur lui-même) ; c'est ICI,
# la couche d'orchestration, qu'un événement de maîtrise se traduit en gain de
# Vigueur — exactement comme `manger`/`recolter` orchestrent déjà `gain`. La
# détection AUTOMATIQUE de ce qui déclenche ces gains (lecture des signaux du tick,
# §9) est branchée au tronçon i4 ; ici les appels restent explicites (injection).
def observer(game_state: dict, player: str, objet: str) -> bool:
    """Observer un objet → le DÉCOUVRE (§2.1, palier 0→1) et, si c'est une
    NOUVELLE découverte, crédite un petit gain de Vigueur (la motivation, §4.3).
    Idempotent : ré-observer un objet déjà connu ne re-crédite rien. Renvoie True
    ssi une nouvelle découverte a eu lieu."""
    nouveau = M.decouvrir(game_state, player, objet)
    if nouveau:
        gain(game_state, player, GAIN_DECOUVERTE)
    return nouveau


def crediter_succes(game_state: dict, player: str, objet: str) -> int:
    """Enregistre une preuve de maîtrise sur un objet (§2.2) et, à CHAQUE palier
    franchi, crédite la récompense de Vigueur (§4.3) — proportionnelle au nombre de
    paliers gagnés (une fournée qui franchit deux paliers récompense double).
    Renvoie le palier après mise à jour."""
    avant = M.palier(game_state, player, objet)
    apres = M.enregistrer_preuve(game_state, player, objet)
    if apres > avant:
        gain(game_state, player, GAIN_SUCCES * (apres - avant))
    return apres
