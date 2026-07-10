"""
SYMBIOSE — tools/simserver/palette_cmd.py
Commande pont de PERSISTANCE du LAYOUT de palette (palette de gestes ⑤, D1/D5/D10).
Mixin de `SimServer`, sœur d'écriture de `MaitriseCmdsMixin` : bornée à l'état
JOUEUR (les slots curés + les macros de l'avatar courant), jamais le cœur écolo.

INVARIANT « Godot bête » : la VUE possède le layout affiché (la colonne de palette
④ + les macros enregistrées) et le RENVOIE ENTIER quand le joueur le change (curation
complète, pas un patch incrémental). Toute la VALIDATION (cohérence de cible d'une
macro) vit en Python, source de vérité — `sim.actions.definir_palette` fait foi et
refuse EN BLOC une macro incohérente (transaction : rien n'est écrit si un refus).
Le MOTEUR ne « connaît » pas les macros : la vue les REJOUE comme N gestes `action`
normaux sur la même cible (chacun paie sa Vigueur, philo #1). Golden intact (pont
opt-in, hors tick, aucune clé `palette` créée pour le golden qui tourne hors serveur).
"""
from __future__ import annotations

from sim.actions import palette as PAL


class PaletteCmdMixin:
    """Commande `palette` : persiste le layout curé + les macros de l'avatar."""

    def cmd_palette(self, msg: dict) -> dict:
        """Persiste un changement de LAYOUT envoyé par la vue. `msg.slots` (liste de
        verbes curés) et/ou `msg.macros` (liste de {nom, sequence}) — chaque champ
        FOURNI remplace la clé correspondante ; un champ absent laisse l'existant.
        Valide les macros (cohérence de cible) AVANT d'écrire (refus en bloc). Écrit
        dans l'état joueur (opt-in → golden intact)."""
        if self.engine is None:
            return {"ok": False, "error": "palette avant init"}
        gs = self.engine.game_state
        player = gs["current_player"]
        ok, message = PAL.definir_palette(
            gs, player, slots=msg.get("slots"), macros=msg.get("macros"))
        if not ok:
            return {"ok": False, "error": message}
        # On renvoie le layout écrit (miroir) — la vue peut resynchroniser sans
        # attendre le prochain snapshot.
        return {"ok": True, "palette": PAL.palette_layout(gs, player)}
