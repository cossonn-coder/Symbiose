"""
SYMBIOSE — sim/actions/paillage.py
MATÉRIAU du paillage (sprint équilibre invasion ④, D9) — l'APPROVISIONNEMENT du
mulch et son STOCK par nature. Le mulch n'est plus abstrait : il VIENT de quelque
part (interconnexion, règle « tout coexiste »).

Deux voies d'approvisionnement, event-driven (philo #1, gestes joueur) :
  • `broyer` — transforme du BOIS (`bois_restant` d'un squelette au sol) en **BRF**
    (Bois Raméal Fragmenté) → stock `brf` ;
  • `recolter_paille` — une plante à paille récoltée (`mulch_source`, ⑤ : blé/
    chanvre → "paille", sapin → "aiguilles") alimente le stock de la nature idoine.

Le STOCK vit dans `game_state["mulch_stock"]` (patron `player_seed_bank` : un état
du profil, pas un champ écolo) — une jauge par nature, dans les mêmes unités que
`PAILLAGE_DOSE` (un geste `pailler` en consomme `PAILLAGE_DOSE`). `pailler`
(`gestes.py`) décrémente la nature demandée et REFUSE en amont si le stock est vide
(aucune Vigueur dépensée, patron `epandre`/`planter`/lot vide).

Aucun champ écolo n'est touché ici (le stock est un compteur ; les EFFETS émergent
quand `pailler` pose le mulch, puis au tick via les lecteurs nature-aware). Zéro RNG
(philo #3). Couches respectées (`fields ← sim` : on lit `BROYAGE_RENDEMENT`… de
`fields.ecofields`, on n'importe jamais l'inverse).
"""
from __future__ import annotations

from sim.vigueur import spend
from fields.ecofields import (NATURES_MULCH, BROYAGE_RENDEMENT,
                              RECOLTE_MULCH_RENDEMENT, STRUCTURE_ACCEPTE)
from .couts import cout_action, OBJETS_TOUCHES, _objets_action

# Tissus de litière TENDRE glanables (acquisition des moyens d'agir ③, canal 1) —
# feuille/fleur/herbace/fruit, EXACTEMENT ce qu'un bac à compost accepte
# (`STRUCTURE_ACCEPTE["bac"]`, source unique) : la feuille morte de surface, tendre
# et ramassable. Exclut le `bois` (ligneux, il va à la pile/au broyage) et le
# `diffus` (exsudats DANS le sol, non ramassables — décision ⑤A du compost).
TISSUS_GLANABLES = STRUCTURE_ACCEPTE["bac"]


def mulch_stock(game_state: dict) -> dict:
    """La jauge de stock de mulch du profil (`game_state["mulch_stock"]`), créée à la
    volée (une entrée par nature de `NATURES_MULCH`, à 0). Point d'accès unique —
    `broyer`/`recolter_paille` créditent, `pailler` débite. Patron `player_seed_bank`
    (un état du profil, pas un champ écolo)."""
    stock = game_state.get("mulch_stock")
    if stock is None:
        stock = {nat: 0.0 for nat in NATURES_MULCH}
        game_state["mulch_stock"] = stock
    return stock


def stock_disponible(game_state: dict, nature: str, dose: float) -> bool:
    """Le stock de `nature` couvre-t-il `dose` ? (lecture PURE, aucun effet de bord).
    Appelé par `pailler` EN AMONT (patron `planter`/lot vide) : un paillage sans
    matière est refusé sans rien coûter ni écrire."""
    stock = mulch_stock(game_state)
    return nature in stock and stock[nature] >= dose


def prelever_stock(game_state: dict, nature: str, dose: float) -> None:
    """Débite `dose` de la nature `nature` — appelé par `pailler` APRÈS que le coût est
    intégralement payé (le stock n'est jamais consommé pour un geste avorté). Suppose la
    disponibilité déjà vérifiée par `stock_disponible`."""
    mulch_stock(game_state)[nature] -= dose


def broyer(game_state: dict, player: str, plant, eco) -> float:
    """Broyer du BOIS en BRF (§3.1) — geste sur le MILIEU (philo #1). Puise dans le
    `bois_restant` d'un SQUELETTE au sol (plante morte, réservoir de bois à fragmenter)
    et le convertit en stock `brf` (`× BROYAGE_RENDEMENT`). C'est la voie ligneuse de
    l'approvisionnement du mulch : on recycle le bois mort du jardin en couverture de
    sol (interconnexion décompo → paillage → germination/humidité/champignons).

    Coût MODÉRÉ (phase planification). GRADUÉ par l'effort (patron `recolter`) : à
    Vigueur insuffisante, on broie une FRACTION du bois (le stock crédité ∝ ratio).
    **Refus EN AMONT** (aucune Vigueur dépensée) si la cible n'a pas de bois à broyer
    (`bois_restant ≤ 0` — plante vivante non ligneuse ou squelette déjà fragmenté) :
    ce n'est pas une maladresse de jeu, il n'y a simplement rien à broyer.
    Renvoie la quantité de BRF créditée au stock (0.0 = rien fait)."""
    reserve = getattr(plant, "bois_restant", 0.0)
    if reserve <= 0.0:
        return 0.0                            # rien à broyer → aucune Vigueur dépensée
    cost = cout_action(game_state, player, "broyer", OBJETS_TOUCHES["broyer"])
    ratio = spend(game_state, player, cost)
    consomme = reserve * ratio                # part du réservoir réellement broyée
    plant.bois_restant = reserve - consomme
    credit = consomme * BROYAGE_RENDEMENT
    mulch_stock(game_state)["brf"] += credit
    return credit


def recolter_paille(game_state: dict, player: str, plant, eco) -> float:
    """Récolter une plante à PAILLE (§3.1) — extension permacole de `recolter` (le geste
    de base reste dans `gestes.py` : ressourcement en Vigueur). Ici on ALIMENTE le
    stock de mulch quand l'espèce est une source (`plant.plant_class.mulch_source` :
    blé/chanvre → "paille", sapin → "aiguilles", tronçon ⑤). Espèce non-source
    (`mulch_source is None`, défaut de TOUTES les espèces existantes) → **refus en
    amont**, aucune Vigueur dépensée, aucun stock crédité → comportement inchangé
    (garde-fou golden : rien ne lit `mulch_source` au repos).

    Coût = celui de `recolter` (FAIBLE), GRADUÉ par l'effort (le stock crédité ∝
    ratio). La biomasse convertie suit le barème `recolter` (`(stade+1)·0.4`) ×
    `RECOLTE_MULCH_RENDEMENT`. NE touche AUCUN champ écolo (pas de nécromasse ici : la
    paille part au STOCK, elle reviendra au sol via `pailler` — c'est le canal
    « récolte pour couvrir », distinct de `recolter` qui laisse un résidu au sol).
    Renvoie la quantité de mulch créditée (0.0 = rien fait / espèce non-source)."""
    nature = getattr(plant.plant_class, "mulch_source", None)
    if nature is None:
        return 0.0                            # pas une plante à paille → rien à récolter en mulch
    cost = cout_action(game_state, player, "recolter", _objets_action("recolter", plant))
    ratio = spend(game_state, player, cost)
    biomass = (plant.current_stage + 1.0) * 0.4   # même barème que le tick récolte
    credit = biomass * ratio * RECOLTE_MULCH_RENDEMENT
    mulch_stock(game_state)[nature] += credit
    return credit


def glaner(game_state: dict, player: str, eco, r: int, c: int) -> float:
    """Glaner la litière de surface TENDRE d'un plot (acquisition des moyens d'agir
    ③, canal 1) — geste BASE sur le MILIEU (philo #1), le mulch d'ENTRÉE de gamme :
    on RAMASSE à même le sol les feuilles/fleurs/herbacées/fruits tombés (`TISSUS_
    GLANABLES`) et on les verse au stock nature **`feuilles`**. C'est la source de
    mulch amorçable dès qu'il y a des feuilles au sol (la décompo en produit toujours
    un peu) → elle lève l'impasse `RAVITAILLEMENT_MANQUANT` à la racine : plus besoin
    d'un squelette à broyer ni d'une plante à paille cultivée pour couvrir un sol nu.

    Interconnexion (règle « tout coexiste ») : le mulch VIENT du plot (patron
    `_ramasser_vers_structure`, mais vers le STOCK au lieu d'une structure — la masse
    est CONSERVÉE, jamais créée), reliant décompo → paillage → germination/humidité.
    Le `bois` (ligneux) et le `diffus` (exsudats, permanent) RESTENT au sol.

    Coût FAIBLE (geste rustique). **Refus EN AMONT** (aucune Vigueur dépensée) si le
    plot n'a rien de tendre à glaner (`total ≤ 0` — sol propre) : ce n'est pas une
    maladresse, il n'y a simplement rien à ramasser (patron `broyer`/`epandre`).
    Renvoie la masse de feuilles créditée au stock (0.0 = rien fait)."""
    cell = eco.litiere[r][c]
    total = sum(p.masse for p in cell if p.masse > 0.0 and p.tissu in TISSUS_GLANABLES)
    if total <= 0.0:
        return 0.0                            # rien de tendre à glaner → aucune Vigueur dépensée
    cost = cout_action(game_state, player, "glaner", OBJETS_TOUCHES["glaner"])
    if spend(game_state, player, cost) < 1.0:
        return 0.0                            # Vigueur insuffisante → litière intacte
    eco.litiere[r][c] = [p for p in cell if p.tissu not in TISSUS_GLANABLES]
    mulch_stock(game_state)["feuilles"] += total
    return total
