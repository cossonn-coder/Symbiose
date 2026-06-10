"""
SYMBIOSE — tools/sim_server.py
Serveur de simulation : le moteur Python derrière un pont JSON stdin/stdout.

Sprint Intégration Godot ↔ Python, tranche 1 (Option B actée : Python = moteur,
Godot = vue). Godot lance ce script en SOUS-PROCESS et lui parle par les pipes —
schéma UART logiciel : stdin = Godot→Python, stdout = Python→Godot, framing par
délimiteur `\n` (1 ligne = 1 message JSON complet, JSON compact n'émet jamais de
`\n` littéral). Maître/esclave strict : Godot envoie une commande, ce serveur
répond UNE ligne, jamais de message spontané → pas de concurrence, déterminisme
préservé.

ADAPTATEUR, pas moteur : on importe le moteur comme le font main.py et
tests/test_golden.py, on ne modifie RIEN de sa logique → golden intact par
construction. Si Godot a besoin d'une donnée absente, on l'ajoute au SNAPSHOT
(lecture seule), jamais au tick.

Protocole v0 (requête → réponse, champ `cmd` obligatoire) :
  → {"cmd": "init", "seed": 42, "config": "smoke"}   # ou "full" (monde 20×20 m)
  ← {"ok": true, "engine_version": "...", "world": {tuiles + maison, statique}}
  → {"cmd": "step_week"}
  ← {"ok": true, "snapshot": {...}}
  → {"cmd": "snapshot"}
  ← {"ok": true, "snapshot": {...}}
  → {"cmd": "quit"}
  ← {"ok": true}
Erreur : {"ok": false, "error": "message lisible"} — le serveur ne crashe
jamais sur une commande malformée (il répond et continue). EOF sur stdin
(Godot mort sans `quit`) → sortie propre.

Usage (depuis data/code/, ou n'importe où — bootstrap sys.path ci-dessous) :
  python3 tools/sim_server.py     # puis taper les commandes JSON à la main
  python3 -m tools.sim_server
Test : python3 -m tests.test_sim_server
"""
from __future__ import annotations
import contextlib
import json
import os
import sys

# Bootstrap : lancé en script direct (`python3 tools/sim_server.py`), sys.path[0]
# est tools/ → les imports absolus du moteur (plants, sim, …) échoueraient. On
# remonte à data/code/ comme racine d'import (sans effet en mode -m).
_CODE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from world import House
from sim.engine import Engine, saison_de

# Version du protocole/moteur exposée dès le v0 (même philosophie que le futur
# save JSON : casse explicite si schéma incompatible). Locale au serveur pour
# l'instant — le « sprint save global » décidera où la centraliser.
ENGINE_VERSION = "0.1.0"


class SimServer:
    """État du serveur : un Engine (ou None avant `init`). Dispatch des commandes."""

    def __init__(self):
        self.engine = None

    # ------------------------------------------------------------------ cmds

    def cmd_init(self, msg: dict) -> dict:
        seed = msg.get("seed", 0x5AB1057E)
        config = msg.get("config", "smoke")
        if not isinstance(seed, int):
            return {"ok": False, "error": f"seed doit être un entier (reçu {seed!r})"}
        if config == "smoke":
            # Réutilise la fabrique du golden smoke test (2 tuiles terre/argile +
            # maison centrée) — même monde, même déterminisme, zéro duplication.
            from tests.test_golden import build_world
            tiles, ecos = build_world()
            house = House()
        elif config == "full":
            # Monde COMPLET 20×20 m (tranche 2) : fabrique de main.py (8 tuiles
            # SECTORS plantées + maison) — import, pas de copie, même principe.
            from main import build_world_full
            tiles, ecos, _aux_tiles, house = build_world_full()
        else:
            return {"ok": False,
                    "error": f"config inconnue : {config!r} ('smoke' ou 'full')"}
        game_state = {
            "tiles": tiles, "eco": ecos, "scores": {},
            "current_player": "joueur_1", "week": 1, "log": [],
            "house": house, "seed": seed,
        }
        self.engine = Engine(game_state)
        return {"ok": True, "engine_version": ENGINE_VERSION,
                "world": self._world_static()}

    def cmd_step_week(self, msg: dict) -> dict:
        if self.engine is None:
            return {"ok": False, "error": "step_week avant init"}
        # stdout est RÉSERVÉ au protocole : tick_semaine() ne print pas (vérifié
        # — seul run_years(verbose=True) le fait), mais on blinde contre une
        # évolution future du moteur en déviant tout print vers stderr.
        with contextlib.redirect_stdout(sys.stderr):
            self.engine.tick_semaine()
        self.engine.game_state["log"].clear()   # borne la mémoire (cf. golden)
        return {"ok": True, "snapshot": self._snapshot()}

    def cmd_snapshot(self, msg: dict) -> dict:
        if self.engine is None:
            return {"ok": False, "error": "snapshot avant init"}
        return {"ok": True, "snapshot": self._snapshot()}

    # ------------------------------------------------------- sérialisation

    def _world_static(self) -> dict:
        """Partie STATIQUE du monde (renvoyée une fois, au init) : layout des
        tuiles + maison. Tout ce qui bouge chaque semaine va dans le snapshot."""
        gs = self.engine.game_state
        house = gs["house"]
        hx0, hy0, hx1, hy1 = house.footprint_bounds
        return {
            "tiles": [
                {"id": t.tile_id, "soil": t.soil_type,
                 "rows": t.grid_rows, "cols": t.grid_cols,
                 "origin_x_cm": t.origin_x_cm, "origin_y_cm": t.origin_y_cm}
                for t in gs["tiles"]
            ],
            "house": {"footprint_cm": [hx0, hy0, hx1, hy1],
                      "height_cm": house.height_cm},
        }

    def _snapshot(self) -> dict:
        """Snapshot v0 minimal (kickoff tranche 1) : horloge + plantes vivantes.
        `week` = compteur moteur (prochaine semaine à simuler, 1 = rien simulé) ;
        year/season en sont dérivés. Par plante : position continue LOCALE à sa
        tuile (x_cm/y_cm + tile pour replacer en monde via origin_*_cm) et la
        structure de segments via structure_to_dict() (format Croissance·6, le
        même que tools/export_structure.py → PlantStructure.cs sait déjà lire)."""
        gs = self.engine.game_state
        week = gs["week"]
        week_in_year = ((week - 1) % 52) + 1
        plants = []
        for tile in gs["tiles"]:
            for p in tile.plants:
                if not p.is_alive:
                    continue
                plants.append({
                    "tile": tile.tile_id,
                    "species": p.plant_class.__name__,
                    "name": p.name,
                    "x_cm": p.x_cm, "y_cm": p.y_cm,
                    "stage": p.current_stage,
                    "stage_name": p.stage.name,
                    "height_cm": p.current_height,
                    "segments": p.structure_to_dict(),
                })
        return {"week": week, "week_in_year": week_in_year,
                "year": (week - 1) // 52 + 1, "season": saison_de(week_in_year),
                "plants": plants}


def main() -> int:
    server = SimServer()
    dispatch = {"init": server.cmd_init,
                "step_week": server.cmd_step_week,
                "snapshot": server.cmd_snapshot}
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


if __name__ == "__main__":
    sys.exit(main())
