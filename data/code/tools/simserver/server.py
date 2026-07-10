"""
SYMBIOSE — tools/simserver/server.py
Assemblage de `SimServer` (les trois mixins) + la boucle stdin/stdout qui
applique le framing du protocole (1 ligne = 1 message JSON). Cœur d'orchestration
du pont — la logique des commandes vit dans commands/actions/serialize.
"""
from __future__ import annotations
import json
import sys

from .commands import CommandsMixin
from .actions import ActionsMixin
from .actions_cibles import CiblesMixin
from .serialize import SerializeMixin
from .voix import VoixMixin
from .maitrise_cmds import MaitriseCmdsMixin
from .palette_cmd import PaletteCmdMixin


class SimServer(CommandsMixin, ActionsMixin, CiblesMixin, SerializeMixin, VoixMixin,
                MaitriseCmdsMixin, PaletteCmdMixin):
    """État du serveur : un Engine (ou None avant `init`). Dispatch des commandes."""

    def __init__(self):
        self.engine = None


def main() -> int:
    server = SimServer()
    dispatch = {"init": server.cmd_init,
                "step_week": server.cmd_step_week,
                "snapshot": server.cmd_snapshot,
                # Rapport perf enrichi (demande Nico) : top-K pires ticks + état
                # courant, lu par le presse-papier Godot (touche C). Read-only.
                "perf_report": server.cmd_perf_report,
                "action": server.cmd_action,
                "fields": server.cmd_fields,
                "list_bancs": server.cmd_list_bancs,
                # Voix narratives (read-only, sprint UI voix ①) : consultation des
                # 4 dispositifs. LECTURE seule — l'achat magazine passe par `action`.
                "carnet": server.cmd_carnet,
                "encyclopedie": server.cmd_encyclopedie,
                "pages": server.cmd_pages,
                "magazine": server.cmd_magazine,
                # Aide au jardinier (retour F5, debug d'abord) : remèdes des
                # problèmes récents d'une espèce, gatables par la maîtrise.
                "aide": server.cmd_aide,
                # Observation par SURVOL (retour F5 : voir une plante ≠ l'observer)
                # + raccourcis DEBUG (forcer palier / observer tout / reset).
                "observer": server.cmd_observer,
                # Palette de gestes ⑤ (write) : persiste le layout curé + les
                # macros de l'avatar (bornée à l'état joueur, opt-in → golden intact).
                "palette": server.cmd_palette,
                "debug": server.cmd_debug}
    # 1 ligne lue = 1 réponse écrite. EOF (Godot mort sans quit) → fin de boucle.
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        quit_after = False
        try:
            msg = json.loads(line)
            if not isinstance(msg, dict):
                resp = {"ok": False, "error": "message JSON non-objet"}
            else:
                cmd = msg.get("cmd")
                if cmd == "quit":
                    resp, quit_after = {"ok": True}, True
                elif cmd in dispatch:
                    resp = dispatch[cmd](msg)
                else:
                    resp = {"ok": False, "error": f"commande inconnue : {cmd!r}"}
        except Exception as e:                       # le serveur survit à tout
            resp = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        # Compact (1 ligne) + sort_keys (stable entre runs → déterminisme
        # vérifiable byte-à-byte). flush OBLIGATOIRE : sans lui la réponse
        # reste dans le buffer et Godot attend indéfiniment (piège n°1 des pipes).
        print(json.dumps(resp, sort_keys=True, separators=(",", ":")), flush=True)
        if quit_after:
            break
    return 0
