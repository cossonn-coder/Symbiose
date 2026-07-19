# SYMBIOSE — tools/jardinier_auto/proposition.py
# Cœur de l'étape 3 (§3.3) : pour un facteur limitant diagnostiqué, choisir le geste
# JOUABLE le plus prioritaire — ou signaler une IMPASSE (§7). C'est ici que vivent :
#   - le CHAÎNAGE de ravitaillement `broyer → pailler` (pailler refuse sans stock de
#     mulch ; on produit d'abord du BRF en broyant un squelette, ou de la paille en
#     récoltant une plante à paille ; sinon impasse `ravitaillement_manquant`) ;
#   - le repli de chaîne (hydrique : pailler indisponible → arroser) ;
#   - la désignation de cible des gestes sur le VIVANT (deraciner la férale
#     diagnostiquée, tailler le voisin ombrageant).
#
# Rien n'est exécuté ici (fonction de DÉCISION) : on renvoie un `Plan` (à exécuter)
# ou une `Impasse` (à consigner). Déterminisme : toute recherche de cible passe par
# un départage stable `(y_cm, x_cm)` (philo #3).

from __future__ import annotations
from dataclasses import dataclass

from sim.actions.paillage import mulch_stock, stock_disponible
from fields.ecofields import NATURES_MULCH
from sim.actions.gestes import PAILLAGE_DOSE
from .regles import regles_pour
from .impasses import Impasse, cause_pour


@dataclass(frozen=True)
class Plan:
    """Un geste décidé, prêt à exécuter (execution.executer).
    `verbe`   : le geste `sim.actions`.
    `cible`   : "milieu" (plot-foyer de `plant`) | "vivant" (`cible_obj`).
    `cible_obj` : la plante visée pour un geste sur le vivant (deraciner/tailler/
                broyer/recolter_paille), ou None (geste de milieu sur `plant`).
    `nature`  : nature de mulch pour `pailler`, sinon None.
    `facteur` / `priorite` : hérités de la règle (trace + tri de l'étape 4)."""

    verbe: str
    cible: str
    cible_obj: object
    nature: object
    facteur: str
    priorite: int


def _nature_disponible(game_state) -> str | None:
    """Une nature de mulch dont le stock couvre une dose de paillage, ou None.
    Ordre déterministe = celui de `NATURES_MULCH` (liste figée)."""
    stock = mulch_stock(game_state)
    for nat in NATURES_MULCH:
        if stock.get(nat, 0.0) >= PAILLAGE_DOSE:
            return nat
    return None


def _prep_ravitaillement(plant, voisins, tile_id, percept):
    """Un geste de RAVITAILLEMENT en mulch à jouer ce tick (le paillage suivra un
    tick plus tard, une fois le stock crédité), ou None si aucune source. Gradient du
    plus BASE au plus spécifique (moyens d'agir ③) :
      1. GLANER la litière tendre du plot-foyer (`percept.litiere_tendre ≥ dose`) →
         feuilles. Canal 1 : geste BASE sur le MILIEU, amorçable dès qu'il y a des
         feuilles au sol → lève l'impasse à la racine (aucun squelette ni culture
         requis). Renvoyé en cible "milieu" (le plot de `plant`), pas "vivant".
      2. BROYER un squelette ligneux au sol (`bois_restant > 0`) → BRF ;
      3. RÉCOLTER une plante à paille mûre (`plant_class.mulch_source`) → paille.
    2/3 cherchent parmi les `voisins` de la tuile (départage stable). Ne consomme
    rien — c'est une DÉCISION ; l'exécution suit. Renvoie (verbe, cible, kind) où
    `kind` ∈ {"milieu", "vivant"} indique la forme de cible."""
    if percept.litiere_tendre >= PAILLAGE_DOSE:
        return ("glaner", None, "milieu")     # canal 1 : ramasse la litière du plot de `plant`
    squelettes = [v for v in voisins
                  if getattr(v, "bois_restant", 0.0) > 0.0]
    if squelettes:
        cible = min(squelettes, key=lambda v: (v.y_cm, v.x_cm))
        return ("broyer", cible, "vivant")
    pailles = [v for v in voisins
               if v.is_alive
               and getattr(v.plant_class, "mulch_source", None) is not None]
    if pailles:
        cible = min(pailles, key=lambda v: (v.y_cm, v.x_cm))
        return ("recolter_paille", cible, "vivant")
    return None


def _plan_pailler(game_state, plant, voisins, tile_id, regle, percept):
    """Décide comment servir un besoin de `pailler` (facteurs `hydrique`/`sol_nu`) :
    pailler direct si stock, sinon un geste de ravitaillement, sinon None (→ la
    chaîne de repli ou l'impasse est gérée par l'appelant)."""
    nat = _nature_disponible(game_state)
    if nat is not None:
        return Plan("pailler", "milieu", None, nat, regle.facteur, regle.priorite)
    prep = _prep_ravitaillement(plant, voisins, tile_id, percept)
    if prep is not None:
        verbe, cible, kind = prep
        return Plan(verbe, kind, cible, None, regle.facteur, regle.priorite)
    return None


def proposer(game_state, plant, voisins, tile_id, facteur, percept):
    """Renvoie un `Plan` jouable ou une `Impasse`. Parcourt les règles du facteur par
    priorité décroissante et retient la PREMIÈRE applicable (chaîne de repli)."""
    regles = regles_pour(facteur)
    for regle in regles:
        v = regle.verbe
        if v == "pailler":
            plan = _plan_pailler(game_state, plant, voisins, tile_id, regle, percept)
            if plan is not None:
                return plan
            continue                    # mulch introuvable → règle suivante (repli)
        if v == "deraciner":
            if percept.ferale_cible is not None:
                return Plan(v, "vivant", percept.ferale_cible, None,
                            facteur, regle.priorite)
            continue
        if v == "tailler":
            if percept.voisin_ombrageant is not None:
                return Plan(v, "vivant", percept.voisin_ombrageant, None,
                            facteur, regle.priorite)
            continue
        # arroser, grelinette, recolter — toujours applicables (sur `plant`/son plot).
        obj = plant if regle.cible == "vivant" else None
        return Plan(v, regle.cible, obj, None, facteur, regle.priorite)
    # Aucune règle applicable → impasse typée (§7).
    cible = f"{plant.name}@{plant.position}"
    return Impasse(facteur, cause_pour(facteur, regles), cible)
