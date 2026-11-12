"""
SYMBIOSE — tools/simserver/supports_route.py
Routage des SUPPORTS de grimpe et des COUVERTURES climatiques (sprint ACCÈS AUX
GESTES ③, protocole 0.6.12) — module de route dédié, sur le modèle de
`structures_route.py`, pour garder le routeur `actions.py` court (un fichier = une
responsabilité : « poser quelque chose de léger sur une tuile, ou y attacher une
plante »). Huit verbes, trois façons de désigner :

  - `poser_tuteur` / `poser_treillis` / `poser_pergola` / `poser_perchoir` :
    un POINT tuile-local `{tile, x_cm, y_cm}` (patron `planter`). `poser_perchoir`
    vivait dans `actions.py` (0.6.11) ; il est venu ici avec ses trois frères,
    comme sa note le prévoyait (« même branche »).
  - `palisser` : une PLANTE VIVANTE désignée par position `{tile, x_cm, y_cm}`
    (résolveur `plant_at`, comme tous les gestes sur plante).
  - `poser_voile` / `poser_cloche` / `poser_ombriere` : un PLOT `{tile, r, c}`
    (patron `glaner`/`creuser`).

Validation des désignations ICI (refus → ne coûte RIEN, la façade n'est jamais
appelée) ; les façades `sim/actions` font foi (coût, effet, pose binaire).
`bilan(applied, cost, gain, message)` → dict est la fabrique de réponse commune.

DÉBLOCAGE : comme pour les autres gestes de tuile, le pont ne refuse PAS un geste
fermé (pas de gating dur — `sim/actions/deblocage.py` : « un geste verrouillé
n'existe simplement pas encore dans la palette »). Seuls les gestes de paysage
vérifient `est_debloque`, dans leur façade. On suit ici le chemin commun.
"""
from __future__ import annotations

from sim import actions as A      # façades supports/couvertures (foi métier)

# Verbe → (façade, message de réussite).
_SUPPORTS = {
    "poser_tuteur":   (A.poser_tuteur,   "tuteur planté"),
    "poser_treillis": (A.poser_treillis, "treillis dressé"),
    "poser_pergola":  (A.poser_pergola,  "pergola montée"),
    "poser_perchoir": (A.poser_perchoir,
                       "perchoir planté — les oiseaux viendront s'y poser"),
}
_COUVERTURES = {
    "poser_voile":    (A.poser_voile,    "voile d'hivernage tendu"),
    "poser_cloche":   (A.poser_cloche,   "cloche posée"),
    "poser_ombriere": (A.poser_ombriere, "ombrière tendue"),
}

VERBES = (*_SUPPORTS, "palisser", *_COUVERTURES)


def route_support(gs: dict, player: str, verb: str, target: dict, bilan,
                  plot_at, plant_at):
    """Aiguille un geste de support ou de couverture. `plot_at(tile, x, y)` et
    `plant_at(tile, x, y)` sont les résolveurs du serveur (`CiblesMixin`)."""
    tiles = {t.tile_id: t for t in gs["tiles"]}
    tile = tiles.get(target.get("tile"))
    if tile is None:
        return bilan(False, 0.0, 0.0,
                     f"tuile introuvable : {target.get('tile')!r}")
    cost = A.cout_action(gs, player, verb, A.OBJETS_TOUCHES[verb])

    # --- Supports : un point de la tuile --------------------------------------
    if verb in _SUPPORTS:
        x, y = target.get("x_cm"), target.get("y_cm")
        if plot_at(tile, x, y) is None:
            return bilan(False, 0.0, 0.0,
                         f"position hors tuile : x={x!r}, y={y!r}")
        facade, reussi = _SUPPORTS[verb]
        sup = facade(gs, player, tile, float(x), float(y))
        return bilan(sup is not None, cost, 0.0,
                     reussi if sup is not None
                     else "Vigueur insuffisante — rien posé")

    # --- Palisser : une plante vivante ----------------------------------------
    if verb == "palisser":
        plant = plant_at(tile, target.get("x_cm"), target.get("y_cm"))
        if plant is None:
            return bilan(False, 0.0, 0.0,
                         "aucune plante vivante à cette position")
        # Diagnostic en LECTURE (les deux refus « de nature » de la façade), pour
        # dire POURQUOI sans rien décider : la façade refera les mêmes tests.
        if getattr(plant.plant_class, "mode_grimpe", None) != "sarmenteux":
            return bilan(False, 0.0, 0.0,
                         f"{plant.name} ne se palisse pas (cette plante s'accroche seule, "
                         "ou ne grimpe pas)")
        if plant.support is not None:
            return bilan(False, 0.0, 0.0, f"{plant.name} tient déjà à un support")
        v_avant = bilan(False, 0.0, 0.0, "")["vigueur"]
        ok = A.palisser(gs, player, plant, tile)
        if ok:
            return bilan(True, cost, 0.0, f"{plant.name} : canne nouée à son support")
        # Deux échecs possibles, qu'on distingue par ce que la façade a fait : rien
        # dépensé = aucun support à portée (refus en amont) ; sinon la Vigueur manquait.
        depense = bilan(False, 0.0, 0.0, "")["vigueur"] < v_avant
        return bilan(False, cost if depense else 0.0, 0.0,
                     "Vigueur insuffisante — rien attaché" if depense
                     else "aucun support à portée de cette plante")

    # --- Couvertures : un plot ------------------------------------------------
    r, c = target.get("r"), target.get("c")
    if (not isinstance(r, int) or isinstance(r, bool)
            or not isinstance(c, int) or isinstance(c, bool)
            or not (0 <= r < tile.grid_rows)
            or not (0 <= c < tile.grid_cols)):
        return bilan(False, 0.0, 0.0, f"plot hors tuile : r={r!r}, c={c!r}")
    eco = gs["eco"][tile.tile_id]
    facade, reussi = _COUVERTURES[verb]
    ok = facade(gs, player, eco, r, c)
    return bilan(ok, cost, 0.0,
                 f"{reussi} en ({r},{c}) sur {tile.tile_id}" if ok
                 else "Vigueur insuffisante — rien posé")
