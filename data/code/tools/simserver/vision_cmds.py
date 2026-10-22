"""
SYMBIOSE — tools/simserver/vision_cmds.py
La VISION au pont (sprint « le sol qui respire » ⑥, protocole 0.5.54) :

  1. `cmd_parler` — au SURVOL d'un être pendant la vision, ses 1 à 3 phrases
     (`sim/voix_etres`). Hors vision → `phrases: []` (les êtres se taisent, rien
     n'est calculé). Lecture du monde ; seule écriture : +1 survol de l'espèce dans
     la tranche vision du joueur (ce qui en RESTE à la fin, `sim/vision`).
     Cibles : plante `{tile, x_cm, y_cm}` ; bête ou champignon `{espece, tile, r, c}`.
  2. `bloc_vision` — `player.vision` du snapshot `{active, overdose, fin, reste}`.
  3. `bloc_voix` — OVERDOSE seulement : les phrases de TOUS les êtres du snapshot
     (plantes vivantes, bêtes peintes, butineurs, carpophores), recalculées à chaque
     snapshot jusqu'à la fin de l'effet. Absent hors overdose (coût nul).

« Godot bête » : la vue envoie ce qu'elle survole, Python résout et parle. Hors tick
→ golden NEUTRE.
"""
from __future__ import annotations

from sim import vision
from sim import voix_etres as VE
from sim.engine import saison_de
from sim.champignon_role import plots_racines, role_carpophore
from fields.fongique import REGISTRE_FONGIQUE
from .maitrise_pont import _CLE_DE_NOM


def _semaine(gs: dict) -> tuple:
    week = gs["week"]
    return week, saison_de(((week - 1) % 52) + 1)


class VisionCmdsMixin:
    """Commande `parler` (survol sous vision)."""

    def cmd_parler(self, msg: dict) -> dict:
        if self.engine is None:
            return {"ok": False, "error": "parler avant init"}
        gs = self.engine.game_state
        player = gs["current_player"]
        tile = next((t for t in gs["tiles"] if t.tile_id == msg.get("tile")), None)
        if tile is None:
            return {"ok": False, "error": f"tuile introuvable : {msg.get('tile')!r}"}
        if not vision.vision_active(gs, player):
            return {"ok": True, "vision": False, "phrases": []}
        eco = gs["eco"][tile.tile_id]
        week, saison = _semaine(gs)
        espece = msg.get("espece")
        if espece is None:   # plante par position
            plant = self._plant_at(tile, msg.get("x_cm"), msg.get("y_cm"))
            if plant is None:
                return {"ok": False, "error": "aucune plante vivante à cette position"}
            vision.noter_survol(gs, player, _CLE_DE_NOM.get(plant.plant_class.__name__, ""))
            return {"ok": True, "vision": True,
                    "phrases": VE.phrases_plante(plant, tile, eco, saison, gs["seed"], week)}
        r, c = msg.get("r"), msg.get("c")
        if not (isinstance(r, int) and isinstance(c, int)
                and 0 <= r < eco.rows and 0 <= c < eco.cols):
            return {"ok": False, "error": f"plot invalide : ({r!r}, {c!r})"}
        if espece in REGISTRE_FONGIQUE:
            role = role_carpophore(eco, plots_racines(tile.plants), r, c)
            phrases = VE.phrases_champignon(role, tile, r, c, gs["seed"], week)
        elif espece in (eco.populations or {}):
            phrases = VE.phrases_bete(espece, tile, eco, r, c, gs["seed"], week)
        else:
            return {"ok": False, "error": f"être inconnu : {espece!r}"}
        vision.noter_survol(gs, player, espece)
        return {"ok": True, "vision": True, "phrases": phrases}


def bloc_vision(gs: dict, player: str) -> dict:
    """`player.vision` : état lisible + espèces gagnées à la dernière clôture
    (`reste`, consommé à la lecture → signalé une fois)."""
    return {**vision.bloc_joueur(gs, player), "reste": vision.reste_recent(gs, player)}


def bloc_voix(gs: dict, player: str, sprites: dict, foragers: dict,
              carpophores: dict) -> dict | None:
    """Phrases de tous les êtres du snapshot, par tuile, SEULEMENT en overdose :
    `{tuile: {plantes: [[x_cm, y_cm, [..]]], betes: [[espece, r, c, [..]]],
    champignons: [[espece, r, c, [..]]]}}`. None hors overdose."""
    if not vision.overdose_active(gs, player):
        return None
    week, saison = _semaine(gs)
    seed = gs["seed"]
    cache: dict = {}
    out = {}
    for tile in gs["tiles"]:
        tid = tile.tile_id
        eco = gs["eco"][tid]
        ctx = VE.contexte_tuile(tile)   # voisinage indexé une fois par tuile
        plantes = [[p.x_cm, p.y_cm, VE.phrases_plante(p, tile, eco, saison, seed, week, ctx)]
                   for p in tile.plants if p.is_alive]
        vus = sorted({(esp, s[0], s[1]) for esp, lst in sprites.get(tid, {}).items()
                      for s in lst}
                     | {(a[0], a[1], a[2]) for a in foragers.get(tid, [])})
        betes = [[esp, r, c, VE.phrases_bete(esp, tile, eco, r, c, seed, week, cache)]
                 for esp, r, c in vus]
        champis = sorted({(k[6], k[0], k[1], k[5]) for k in carpophores.get(tid, [])})
        out[tid] = {"plantes": plantes, "betes": betes,
                    "champignons": [[e, r, c, VE.phrases_champignon(role, tile, r, c, seed, week)]
                                    for e, r, c, role in champis]}
    return out
