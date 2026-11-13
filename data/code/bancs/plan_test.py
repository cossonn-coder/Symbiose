"""
SYMBIOSE — bancs/plan_test.py
PLAN DE TEST d'un banc (sprint GESTES LISIBLES ⑤, conception
`docs/joueur/gestes/conception_gestes_lisibles.md` §7 « mode testeur »).

Un banc peut déclarer une liste ORDONNÉE de gestes `(verbe, cible)` que la vue
déroule PAR LE MÊME CHEMIN QU'UN CLIC DU JOUEUR (dispatch d'action normal :
animation du curseur, réponse du pont, traces au sol). C'est un instrument
d'observation : on regarde les gestes jouer sans les cliquer un à un.

Une CIBLE est décrite par une petite fonction (`plot`, `plante`, `structure`) qui
la RÉSOUT sur l'état courant du monde en un point MONDE `(x_cm, y_cm)` — le point
où la vue « cliquera ». Un geste à deux temps (épandre : le tas, puis le plot)
porte deux cibles, cliquées dans l'ordre. Une cible introuvable rend `None` : la
vue le rapporte comme refusé (« cible introuvable »), sans rien envoyer.

Certains verbes ne sont pas des cases de la palette mais une variante d'une case
(`grelinette` = ameublir + Maj) : `_PALETTE` donne la case et le Maj, pour que la
vue n'ait aucune table à dupliquer. Lecture pure, hors tick → golden NEUTRE.
"""
from __future__ import annotations

from constants import PLOT_CM
from plants.catalogue import PLANT_CATALOGUE

# Verbe moteur → (verbe de la case de palette, Maj enfoncé). Absent = lui-même, sans Maj.
_PALETTE = {"grelinette": ("becher", True)}


def _tuile(gs: dict, tuile: str):
    return next((t for t in gs["tiles"] if t.tile_id == tuile), None)


def _centre(tile, r: int, c: int) -> tuple:
    return (tile.origin_x_cm + (c + 0.5) * PLOT_CM,
            tile.origin_y_cm + (r + 0.5) * PLOT_CM)


def plot(tuile: str, r: int, c: int):
    """Le centre du plot `(r, c)` de la tuile."""
    def resoudre(gs):
        tile = _tuile(gs, tuile)
        return _centre(tile, r, c) if tile is not None else None
    resoudre.libelle = f"plot {tuile}({r},{c})"
    return resoudre


def plante(espece: str, tuile: str | None = None):
    """Le pied de la première plante VIVANTE de l'espèce (ordre des tuiles puis des
    plantes : déterministe), sur `tuile` si elle est donnée."""
    classe = PLANT_CATALOGUE[espece]   # clé du catalogue (« tournesol »)

    def resoudre(gs):
        for tile in gs["tiles"]:
            if tuile is not None and tile.tile_id != tuile:
                continue
            for p in tile.plants:
                if p.plant_class is classe and p.vitalite > 0.0:
                    return (tile.origin_x_cm + p.x_cm, tile.origin_y_cm + p.y_cm)
        return None
    resoudre.libelle = f"plante {espece}"
    return resoudre


def structure(tuile: str, kind: str):
    """Le plot de la première structure `kind` (bac, pile…) de la tuile."""
    def resoudre(gs):
        tile = _tuile(gs, tuile)
        eco = gs["eco"].get(tuile)
        if tile is None or eco is None:
            return None
        s = next((s for s in eco.structures if s.kind == kind), None)
        return _centre(tile, *s.plot) if s is not None else None
    resoudre.libelle = f"{kind} {tuile}"
    return resoudre


def resoudre_plan(gs: dict, plan) -> list:
    """Le plan d'un banc, résolu sur l'état courant : une entrée par geste,
    `{verbe, geste, maj, cible, clics}` (`clics` = points MONDE arrondis au mm, vide
    si une cible est introuvable)."""
    out = []
    for verbe, *cibles in plan:
        geste, maj = _PALETTE.get(verbe, (verbe, False))
        points = [c(gs) for c in cibles]
        clics = ([[round(x, 1), round(y, 1)] for x, y in points]
                 if all(p is not None for p in points) else [])
        out.append({"verbe": verbe, "geste": geste, "maj": maj,
                    "cible": " → ".join(c.libelle for c in cibles), "clics": clics})
    return out
