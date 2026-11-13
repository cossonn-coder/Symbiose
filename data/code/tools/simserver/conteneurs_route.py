"""
SYMBIOSE — tools/simserver/conteneurs_route.py
Routage des gestes CONTENEURS (pots/bacs ④, protocole 0.5.7) — extrait du routeur
`actions.py` pour le garder court (un fichier = une responsabilité). Les pots/bacs
vivent dans la liste MONDE `game_state["containers"]` (≠ structures de tuile) :

  - `poser_pot` / `poser_bac_culture` : pose par POSITION MONDE (x_cm/y_cm) ;
  - `deplacer_pot` / `planter_conteneur` : désignés par INDEX `target.container`
    (= ordre du snapshot `containers`).

Validation des bornes ICI (refus de désignation → ne coûte rien) ; les façades
`sim/actions` font foi pour la Vigueur et l'effet. `bilan` est la fabrique de réponse
JSON du routeur (état Vigueur APRÈS le geste), passée par l'appelant — on garde la
même forme de retour que tous les autres gestes.
"""
from __future__ import annotations

from plants import PLANT_CATALOGUE     # validation d'espèce plantable
from sim import actions as A           # façades conteneurs (poser/deplacer)
from sim import vigueur as V           # spend (planter_conteneur)
from world import planter_dans         # place directe dans le mini-sol
from world.substrat import SUBSTRATS   # validation du substrat
from fields.peripherie import MONDE_CM # côté du jardin (cm) : un pot se pose DEDANS

VERBES = ("poser_pot", "poser_bac_culture", "deplacer_pot", "planter_conteneur")


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _dans_jardin(x, y) -> bool:
    """Le point MONDE (cm) est-il dans le jardin `[0, MONDE_CM]²` ? Un pot posé ou
    déplacé au-delà (dans la ceinture, hors de la carte) est un refus de
    DÉSIGNATION, qui ne coûte rien (GESTES LISIBLES ①, bug « pot hors du jardin » :
    le pont acceptait n'importe quelle coordonnée)."""
    return 0.0 <= x <= MONDE_CM and 0.0 <= y <= MONDE_CM


def route_conteneur(gs: dict, player: str, verb: str,
                    target: dict, params: dict, bilan):
    """Aiguille un verbe conteneur. `bilan(applied, cost, gain, message)` → dict."""
    if verb in ("poser_pot", "poser_bac_culture"):
        substrat = params.get("substrat")
        if substrat not in SUBSTRATS:
            return bilan(False, 0.0, 0.0, f"substrat inconnu : {substrat!r}")
        # `terre_jardin` (hérite_tuile) n'est PAS désignable par le pont en ④ (il
        # faudrait pointer un plot de tuile source) → refus clair, sans coût.
        # Disponible en API Python ; branché au pont si besoin plus tard.
        if substrat == "terre_jardin":
            return bilan(False, 0.0, 0.0,
                         "substrat terre_jardin non posable par le pont (④)")
        vol = params.get("volume")
        x, y = target.get("x_cm"), target.get("y_cm")
        if not _num(vol) or vol <= 0.0 or not _num(x) or not _num(y):
            return bilan(False, 0.0, 0.0,
                         "volume/position invalides (volume>0, x_cm, y_cm requis)")
        if not _dans_jardin(x, y):
            return bilan(False, 0.0, 0.0, "hors du jardin — rien posé")
        cost = A.cout_action(gs, player, verb, A.OBJETS_TOUCHES[verb])
        if verb == "poser_pot":
            ctn = A.poser_pot(gs, player, substrat, float(vol), float(x), float(y))
            quoi = "pot"
        else:
            rows, cols = params.get("rows", 2), params.get("cols", 2)
            if (not isinstance(rows, int) or isinstance(rows, bool) or rows < 1
                    or not isinstance(cols, int) or isinstance(cols, bool) or cols < 1):
                return bilan(False, 0.0, 0.0,
                             f"grille bac invalide : rows={rows!r}, cols={cols!r}")
            ctn = A.poser_bac_culture(gs, player, substrat, float(vol),
                                      float(x), float(y), rows=rows, cols=cols)
            quoi = "bac"
        return bilan(ctn is not None, cost, 0.0,
                     f"{quoi} de {substrat} posé"
                     if ctn is not None else "Vigueur insuffisante — rien posé")

    # deplacer_pot / planter_conteneur : cible par INDEX dans la liste monde.
    lst = gs.get("containers", [])
    idx = target.get("container")
    if not isinstance(idx, int) or isinstance(idx, bool):
        return bilan(False, 0.0, 0.0, f"container non entier : {idx!r}")
    if not 0 <= idx < len(lst):
        return bilan(False, 0.0, 0.0,
                     f"container hors liste : {idx} ({len(lst)} posé(s))")
    ctn = lst[idx]

    if verb == "deplacer_pot":
        # Un bac ne se déplace pas : refus EN AMONT (façade), AUCUNE Vigueur (le
        # mini-sol/plante voyagent intacts — philo #2, pas de choc plante).
        if not ctn.mobile:
            return bilan(False, 0.0, 0.0,
                         "ce conteneur est immobile (bac) — rien déplacé")
        x, y = target.get("x_cm"), target.get("y_cm")
        if not _num(x) or not _num(y):
            return bilan(False, 0.0, 0.0, f"position invalide : x={x!r}, y={y!r}")
        if not _dans_jardin(x, y):
            return bilan(False, 0.0, 0.0, "hors du jardin — pot non déplacé")
        cost = A.cout_action(gs, player, "deplacer_pot",
                             A.OBJETS_TOUCHES["deplacer_pot"])
        ok = A.deplacer_pot(gs, player, ctn, float(x), float(y))
        return bilan(ok, cost, 0.0,
                     "pot déplacé, sa terre et ses plantes avec lui"
                     if ok else "Vigueur insuffisante — pot non déplacé")

    # planter_conteneur : place DIRECTEMENT une plante dans le mini-sol (un conteneur
    # n'a pas de succession spontanée — la plante est posée, pas semée en attente comme
    # sur une tuile). Source = banque-joueur (symétrie avec `planter` tuile), coût
    # FAIBLE. Refus lot vide / espèce inconnue EN AMONT (sans coût).
    species = params.get("species")
    if not isinstance(species, str) or species not in PLANT_CATALOGUE:
        return bilan(False, 0.0, 0.0, f"espèce non plantable : {species!r}")
    bank = gs.get("player_seed_bank")
    if bank is None or bank.count(species) == 0:
        return bilan(False, 0.0, 0.0,
                     f"lot vide — aucune graine de {species} en banque")
    cost = A.cout_action(gs, player, "planter", A._objets_action("planter"))
    if V.spend(gs, player, cost) < 1.0:
        return bilan(False, cost, 0.0, "Vigueur insuffisante — graine conservée")
    bank.take(species)
    planter_dans(ctn, PLANT_CATALOGUE[species])
    return bilan(True, cost, 0.0, f"{species} planté dans le {ctn.kind}")
