"""
SYMBIOSE — tools/simserver/maitrise_cmds.py
Commandes pont d'OBSERVATION (survol) et de DEBUG (retour F5 voix narratives).
Mixin de `SimServer`, sœur de `VoixMixin` mais côté ÉCRITURE (bornée à l'état
JOUEUR : maîtrise, pages, Vigueur de découverte — jamais le cœur écolo).

INVARIANT « Godot bête » : le C# envoie ce qu'il a (le NOM DE CLASSE de la plante
survolée, un `op` de debug) ; toute la logique (résolution nom→clé, forçage de
palier, révélation de page) vit en Python. Golden intact (pont opt-in, hors tick).
"""
from __future__ import annotations

from .maitrise_pont import observer_espece
from . import debug_pont as D


class MaitriseCmdsMixin:
    """Commandes `observer` (survol) et `debug` (raccourcis de test)."""

    def cmd_observer(self, msg: dict) -> dict:
        """Observation par SURVOL (retour F5) : `msg.species` = nom de classe de la
        plante survolée (côté C#). Découvre l'espèce (idempotent). Écriture bornée à
        l'état joueur."""
        if self.engine is None:
            return {"ok": False, "error": "observer avant init"}
        species = msg.get("species")
        if not species:
            return {"ok": False, "error": "observer sans species"}
        gs = self.engine.game_state
        nouveau = observer_espece(gs, gs["current_player"], species)
        return {"ok": True, "observed": bool(nouveau)}

    def cmd_debug(self, msg: dict) -> dict:
        """Raccourcis DEBUG (F5) : `msg.op` ∈ {palier3, observer_tout, reset}.
        Hors golden (pont opt-in). Étiqueté debug côté vue."""
        if self.engine is None:
            return {"ok": False, "error": "debug avant init"}
        gs = self.engine.game_state
        player = gs["current_player"]
        op = msg.get("op")
        if op == "palier3":
            return {"ok": True, "op": op, "objets": D.forcer_palier_3(gs, player)}
        if op == "observer_tout":
            return {"ok": True, "op": op,
                    "decouvertes": D.observer_toutes_presentes(gs, player)}
        if op == "reset":
            D.reset_maitrise(gs, player)
            return {"ok": True, "op": op}
        return {"ok": False, "error": f"op debug inconnue : {op!r}"}
