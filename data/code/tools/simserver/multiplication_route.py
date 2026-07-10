"""
SYMBIOSE — tools/simserver/multiplication_route.py
Routage des gestes de MULTIPLICATION VÉGÉTATIVE (palette de gestes ②③, protocoles
0.5.24/0.5.25) — extrait du routeur `actions.py` pour le garder court (un fichier =
une responsabilité). Deux gestes à 2 TEMPS côté VUE (la mémoire des 2 clics vit dans
Godot ; le serveur reste STATELESS, un seul appel porte les DEUX cibles résolues) :

  - `bouturer` : la MÈRE par position continue (x_cm/y_cm) + le PLOT cible par
    `params.r`/`params.c` (2e clic). Clone génétique, stress sur la mère ;
  - `greffer` : le PORTE-GREFFE par position (target.x_cm/y_cm, il RESTE, cible
    primaire) + le GREFFON par `params.scion_x_cm`/`scion_y_cm` (même tuile).
    Recomposition aérien/racinaire (D8), greffon consommé.

Validation des désignations ICI (refus → ne coûte rien) ; les façades `sim/actions`
(`A.bouturer`/`A.greffer`, gates, coûts, effets) font foi. `plant_at` est le résolveur
de plante VIVANTE par position (le `CiblesMixin._plant_at` du serveur), passé par
l'appelant. `bilan(applied, cost, gain, message)` → dict est la fabrique de réponse
JSON commune à tous les gestes.
"""
from __future__ import annotations

from sim import actions as A      # façades multiplication (bouturer/greffer)

VERBES = ("bouturer", "greffer")


def route_multiplication(gs: dict, player: str, verb: str,
                         target: dict, params: dict, bilan, plant_at):
    """Aiguille un verbe de multiplication. Résout la tuile, délègue aux façades."""
    tiles = {t.tile_id: t for t in gs["tiles"]}
    tile = tiles.get(target.get("tile"))
    if tile is None:
        return bilan(False, 0.0, 0.0,
                     f"tuile introuvable : {target.get('tile')!r}")
    eco = gs["eco"][tile.tile_id]

    if verb == "bouturer":
        mother = plant_at(tile, target.get("x_cm"), target.get("y_cm"))
        if mother is None:
            return bilan(False, 0.0, 0.0,
                         "aucune plante-mère vivante à cette position")
        r, c = params.get("r"), params.get("c")
        if (not isinstance(r, int) or isinstance(r, bool)
                or not isinstance(c, int) or isinstance(c, bool)
                or not (0 <= r < tile.grid_rows)
                or not (0 <= c < tile.grid_cols)):
            return bilan(False, 0.0, 0.0,
                         f"plot cible hors tuile : r={r!r}, c={c!r}")
        # Gate d'espèce lu EN AMONT pour un message clair (distinct de la Vigueur
        # insuffisante), sans dépense — la façade retesterait de toute façon.
        if not getattr(mother.plant_class, "bouturable", False):
            return bilan(False, 0.0, 0.0,
                         f"{mother.name} ne se bouture pas")
        cost = A.cout_action(gs, player, "bouturer",
                             A._objets_action("bouturer", mother))
        ok = A.bouturer(gs, player, mother, tile, eco, r, c)
        return bilan(ok, cost, 0.0,
                     f"bouture de {mother.name} enracinée en ({r},{c})" if ok
                     else f"rien bouturé ({mother.name} trop jeune/épuisée "
                          "ou Vigueur insuffisante)")

    # greffer
    rootstock = plant_at(tile, target.get("x_cm"), target.get("y_cm"))
    if rootstock is None:
        return bilan(False, 0.0, 0.0,
                     "aucun porte-greffe vivant à cette position")
    scion = plant_at(tile, params.get("scion_x_cm"), params.get("scion_y_cm"))
    if scion is None:
        return bilan(False, 0.0, 0.0,
                     "aucun greffon vivant à cette position")
    if scion is rootstock:
        return bilan(False, 0.0, 0.0,
                     "greffon et porte-greffe sont la même plante")
    # Gate lu EN AMONT pour un message clair (distinct de la Vigueur
    # insuffisante), sans dépense — la façade retesterait de toute façon.
    if not A.peut_greffer(scion, rootstock):
        return bilan(False, 0.0, 0.0,
                     f"greffe impossible : {scion.name} et {rootstock.name} "
                     "non greffables ou de familles différentes")
    cost = A.cout_action(gs, player, "greffer",
                         A._objets_action("greffer", rootstock))
    nom_greffon = scion.name           # lu AVANT la greffe (scion consommé après)
    ok = A.greffer(gs, player, scion, rootstock, eco)
    return bilan(ok, cost, 0.0,
                 f"greffe prise : {nom_greffon} soudé sur {rootstock.name} "
                 "(couronne du greffon, racines du porte-greffe)" if ok
                 else "Vigueur insuffisante — greffe non faite")
