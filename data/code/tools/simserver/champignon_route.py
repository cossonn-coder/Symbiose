"""
SYMBIOSE — tools/simserver/champignon_route.py
Routage de `manger` sur un CARPOPHORE (sprint « le sol qui respire » ⑥, 0.5.54).

Le verbe `manger` garde sa famille de cible « plante » (palette, macros) ; c'est la
FORME de la cible qui aiguille, comme `ecraser`/`creuser` : un target qui porte
`carpophore: [r, c, slot]` (les 2 premiers champs du carpophore du snapshot + son
rang dans le plot) désigne un champignon, sinon une plante. Validation de la
désignation ICI (refus → ne coûte rien) ; la façade `sim/champignon_manger` fait
foi (carpophore encore visible ? comestibilité, Vigueur, vision).
"""
from __future__ import annotations

from sim.champignon_manger import manger_carpophore


def route_carpophore(gs: dict, player: str, target: dict, bilan) -> dict:
    """`manger` un carpophore. Réponse = `bilan` + `vision` / `espece_nommee`."""
    tile = next((t for t in gs["tiles"] if t.tile_id == target.get("tile")), None)
    if tile is None:
        return bilan(False, 0.0, 0.0, f"tuile introuvable : {target.get('tile')!r}")
    k = target.get("carpophore")
    if (not isinstance(k, list) or len(k) != 3
            or not all(isinstance(v, int) and not isinstance(v, bool) for v in k)):
        return bilan(False, 0.0, 0.0, f"carpophore mal désigné : {k!r} (attendu [r, c, slot])")
    res = manger_carpophore(gs, player, tile, *k)
    b = bilan(res["applied"], res["perte"], res["gain"], res["message"])
    b["vision"] = res["vision"]
    b["espece_nommee"] = res["espece_nommee"]
    return b
