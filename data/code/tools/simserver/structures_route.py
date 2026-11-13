"""
SYMBIOSE — tools/simserver/structures_route.py
Routage des STRUCTURES POSABLES & du COMPOSTAGE (⑤, protocole 0.3.5 ; ruche ⑥
§H/§I) — extrait du routeur `actions.py` pour le garder court (un fichier = une
responsabilité). Huit verbes ciblant tous une tuile :

  - `poser_bac` / `poser_pile` / `poser_ruche` désignent un PLOT {r,c} (pose) ;
  - `composter` / `empiler_bois` / `retourner` / `epandre` / `recolter_miel`
    désignent une structure existante par INDEX dans `eco.structures`
    (= ordre du snapshot).

Validation des bornes ICI (refus de désignation → ne coûte rien) ; les façades
`sim/actions` font foi (validité, coût, effet). `bilan(applied, cost, gain,
message)` → dict est la fabrique de réponse JSON commune à tous les gestes.
"""
from __future__ import annotations

from sim import actions as A      # façades structures/compostage/ruche (foi métier)

from .mots import quantite_en_mots, vigueur_en_mots   # mots, pas chiffres (0.6.14)

VERBES = ("poser_bac", "poser_pile", "composter", "empiler_bois",
          "retourner", "epandre", "poser_ruche", "recolter_miel")


def route_structure(gs: dict, player: str, verb: str,
                    target: dict, params: dict, bilan):
    """Aiguille un geste de structure/compostage. Résout la tuile, délègue aux façades."""
    tiles = {t.tile_id: t for t in gs["tiles"]}
    tile = tiles.get(target.get("tile"))
    if tile is None:
        return bilan(False, 0.0, 0.0,
                     f"tuile introuvable : {target.get('tile')!r}")
    eco = gs["eco"][tile.tile_id]

    def plot_rc():
        """(r, c) entier dans la grille, ou (None, message)."""
        r, c = target.get("r"), target.get("c")
        if (not isinstance(r, int) or isinstance(r, bool)
                or not isinstance(c, int) or isinstance(c, bool)
                or not (0 <= r < tile.grid_rows)
                or not (0 <= c < tile.grid_cols)):
            return None, f"plot hors tuile : r={r!r}, c={c!r}"
        return (r, c), None

    def struct_cible():
        """La Structure désignée par `target.structure`, ou (None, message)."""
        idx = target.get("structure")
        if not isinstance(idx, int) or isinstance(idx, bool):
            return None, f"structure non entier : {idx!r}"
        if not 0 <= idx < len(eco.structures):
            return None, (f"structure hors liste : {idx} "
                          f"({len(eco.structures)} posées sur {tile.tile_id})")
        return eco.structures[idx], None

    cost = A.cout_action(gs, player, verb, A.OBJETS_TOUCHES[verb])

    if verb in ("poser_bac", "poser_pile", "poser_ruche"):
        rc, err = plot_rc()
        if rc is None:
            return bilan(False, 0.0, 0.0, err)
        r, c = rc
        if verb == "poser_bac":
            s = A.poser_bac(gs, player, eco, r, c)
            quoi = "bac à compost"
        elif verb == "poser_pile":
            s = A.poser_pile(gs, player, eco, tile, r, c)
            quoi = "pile à bois"
        else:
            s = A.poser_ruche(gs, player, eco, r, c)   # ⑥ §H.1
            quoi = "ruche"
        return bilan(s is not None, cost, 0.0,
                     f"{quoi} posé{'e' if verb == 'poser_ruche' else ''}"
                     if s is not None
                     else "Vigueur insuffisante — rien posé")

    struct, err = struct_cible()
    if struct is None:
        return bilan(False, 0.0, 0.0, err)
    # Récolte du miel (⑥ §I.2) : geste sur une ruche (par index), gain Vigueur
    # ∝ miel transféré, gaté par l'équipement (maîtrise §I.3). Refus de
    # désignation (pas une ruche) → ne coûte rien.
    if verb == "recolter_miel":
        if struct.kind != "ruche":
            return bilan(False, 0.0, 0.0, "cette structure n'est pas une ruche")
        g = A.recolter_miel(gs, player, struct, eco)   # eco → alarme §J si nu
        equipe = A.equipe(gs, player)
        return bilan(g > 0.0, cost, g,
                     f"miel récolté : {vigueur_en_mots(g)}"
                     f"{'' if equipe else ' (récolte partielle, sans équipement)'}"
                     if g > 0.0
                     else "rien récolté (réserve vide ou Vigueur insuffisante)")
    # Cohérence kind/geste : composter→bac, empiler→pile (refus de
    # désignation, ne coûte rien). retourner/epandre marchent sur les deux.
    if verb == "composter" and struct.kind != "bac":
        return bilan(False, 0.0, 0.0, "cette structure n'est pas un bac à compost")
    if verb == "empiler_bois" and struct.kind != "pile":
        return bilan(False, 0.0, 0.0, "cette structure n'est pas une pile à bois")

    if verb == "retourner":
        ok = A.retourner(gs, player, struct)
        return bilan(ok, cost, 0.0,
                     "compost retourné (maturation accélérée)" if ok
                     else "Vigueur insuffisante — rien retourné")

    rc, err = plot_rc()
    if rc is None:
        return bilan(False, 0.0, 0.0, err)
    r, c = rc
    if verb == "composter":
        ok = A.composter(gs, player, eco, r, c, struct)
        return bilan(ok, cost, 0.0,
                     "litière tendre versée au bac" if ok
                     else "Vigueur insuffisante — rien composté")
    if verb == "empiler_bois":
        ok = A.empiler_bois(gs, player, eco, r, c, struct)
        return bilan(ok, cost, 0.0,
                     "bois empilé sur la pile" if ok
                     else "Vigueur insuffisante — rien empilé")
    # epandre : params.q optionnel (None ⇒ tout le disponible).
    q = params.get("q")
    if q is not None and (not isinstance(q, (int, float))
                          or isinstance(q, bool)):
        return bilan(False, 0.0, 0.0, f"quantité non numérique : {q!r}")
    epandu = A.epandre(gs, player, eco, r, c, struct, q=q)
    return bilan(epandu > 0.0, cost, 0.0,
                 f"compost épandu : {quantite_en_mots(epandu)}"
                 + (" — il en reste" if struct.compost_mur > 0.0 else " — le tas est vide")
                 if epandu > 0.0
                 else "rien épandu (jauge vide ou Vigueur insuffisante)")
