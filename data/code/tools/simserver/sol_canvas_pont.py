"""
SYMBIOSE — tools/simserver/sol_canvas_pont.py
Le SOL-CANVAS au pont (sprint GESTES LISIBLES ①, conception §3) : tout ce que la
vue devra dessiner sur le sol, sans rien inventer (D3).

Trois responsabilités de pont, toutes HORS tick (golden neutre) :
  - `noter_trace_geste` : après un geste APPLIQUÉ, résout la tuile, le plot et le
    point cliqué depuis le `target` de la commande, puis écrit la trace au registre
    moteur (`sim/traces_sol`). Écrite ICI, à la route, et non dans les façades
    `sim/actions` : c'est le pont qui connaît la tuile et le point cliqué, et les
    signatures des gestes restent intactes ;
  - `sol_sec_par_tuile` : liste CREUSE des plots secs (craquelé, §3.2), lecture pure ;
  - `volants` : les espèces de faune qui volent (`TrophicSpec.vole`), pour que la vue
    ne propose pas un sprite volant comme cible d'`ecraser` (tronçon ④).
"""
from __future__ import annotations

from constants import PLOT_CM
from sim.traces_sol import SORTE_DU_VERBE, ecrire_trace

# Seuil du sol SEC (craquelé, §3.2) : l'humidité sous laquelle le moteur commence à
# compter un stress hydrique (`drought_stress` naît à `hum < 0.5`, sim/engine/
# croissance.py). La vue ne dessine pas une sécheresse que les plantes ne sentent pas.
SEUIL_SOL_SEC = 0.5


def _entier(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _nombre(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def noter_trace_geste(gs: dict, verb: str, target: dict, plot_at) -> None:
    """Écrit la trace d'un geste APPLIQUÉ. No-op si le verbe ne laisse pas de trace,
    si la cible est un secteur de ceinture (`creuser` hors jardin) ou si la tuile/le
    plot ne se résolvent pas. Point = clic (`x_cm`/`y_cm` tuile-locaux) s'il est
    fourni, sinon le centre du plot désigné par `r`/`c`."""
    sorte = SORTE_DU_VERBE.get(verb)
    if sorte is None or "cote" in target:
        return
    tile = next((t for t in gs["tiles"] if t.tile_id == target.get("tile")), None)
    if tile is None:
        return
    x, y = target.get("x_cm"), target.get("y_cm")
    r, c = target.get("r"), target.get("c")
    if not (_entier(r) and _entier(c)
            and 0 <= r < tile.grid_rows and 0 <= c < tile.grid_cols):
        rc = plot_at(tile, x, y)
        if rc is None:
            return
        r, c = rc
    if not (_nombre(x) and _nombre(y)):
        x, y = (c + 0.5) * PLOT_CM, (r + 0.5) * PLOT_CM
    ecrire_trace(gs, tile.tile_id, r, c, x, y, sorte)


def sol_sec_par_tuile(gs: dict) -> dict:
    """`{tuile: [[r, c, humidite], …]}` des plots sous `SEUIL_SOL_SEC` (valeur brute
    arrondie, la vue applique son hystérésis). Toutes les tuiles présentes, listes
    vides comprises (patron `paillage`). Lecture pure."""
    out = {}
    for tile in gs["tiles"]:
        hum = gs["eco"][tile.tile_id].humidite
        out[tile.tile_id] = [[r, c, round(hum.data[r][c], 3)]
                             for r in range(hum.rows) for c in range(hum.cols)
                             if hum.data[r][c] < SEUIL_SOL_SEC]
    return out


def volants(gs: dict) -> list:
    """Clés d'espèce de faune qui VOLENT (triées), lues sur les champs de population
    du monde. Lecture pure de la donnée d'espèce."""
    return sorted({nom for eco in gs["eco"].values()
                   for nom, champ in eco.populations.items()
                   if getattr(champ.spec, "vole", False)})
