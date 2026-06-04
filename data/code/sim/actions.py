"""
SYMBIOSE — sim/actions.py
Actions JOUEUR sur le vivant (D11, sous-sprint 2) — coûts/gains de Vigueur.
Spec de référence : `data/code/CONCEPTION_VIGUEUR.md` §3 (catalogue d'actions),
§3.5 (HARVEST_VIGUEUR_COST réel), §4 (Qi territorial, flag `harvested`).

Découpage des responsabilités (décision actée 2026-06-04) :
  - `sim/vigueur.py` : l'ÉTAT joueur + les primitives `spend`/`gain` + le cycle.
    « Combien j'ai et comment ça bouge. »
  - CE module : les CONSTANTES de coût + les ACTIONS. « Ce que les gestes coûtent
    et font. » Il orchestre spend/gain et les mutations écologiques (nécromasse).

Principe directeur (spec §0/§5) : ces actions sont event-driven, AU-DESSUS du
tick écologique déterministe. Le golden ÉCOLOGIQUE (`tests/test_golden.py`) est
une succession spontanée pure — il n'appelle JAMAIS ces fonctions, donc son hash
ne peut pas bouger. Si il bouge, c'est un bug (fuite dans le tick).

Solde insuffisant (décision actée) : on « dépense ce qu'on a » via le ratio
d'effort de `vigueur.spend`. Une action GRADUÉE (récolte) en sort tronquée (gain
∝ ratio) ; une action BINAIRE destructrice (déraciner/écraser) ne produit son
effet QUE si le coût est intégralement payé — forcer le vivant à vide draine la
Vigueur et n'accomplit rien (philo #1/#6, sans sermon).
"""
from __future__ import annotations

from sim.vigueur import spend, gain
from sim.effects import necromass_biomass

# Paliers de coût, relatifs à la base 100 / +10 par semaine (spec §3.1, à
# calibrer post-test).
NUL    = 0.0
FAIBLE = 5.0
MODERE = 15.0
ELEVE  = 30.0
URGENCE_MULT = 1.5   # majoration des actions de phase « saison » (urgence, §3.1)

# Le hook de la conception (§3.5) devient réel : le geste de prélèvement de la
# récolte sélective coûte FAIBLE (remplace le `=0` neutre supprimé de l'engine).
HARVEST_VIGUEUR_COST = FAIBLE

# Gain brut d'une récolte d'organe pleinement mûr (× maturité × effort).
HARVEST_GAIN_FULL = 15.0


def maturite(plant) -> float:
    """Avancement de stade ∈ [0, 1] : un semis ≈ 0, un adulte = 1. Helper minimal
    local — la façade complète `vigueur_plante` (santé × maturité × qi × gène,
    spec §1) est le sous-sprint 3."""
    n = len(plant.plant_class.growth_stages)
    if n <= 1:
        return 1.0
    return plant.current_stage / (n - 1)


def recolter(game_state: dict, player: str, plant, eco) -> float:
    """Récolte sélective d'un organe mûr (spec §3.3) — action GRADUÉE.
    Coût FAIBLE ; gain `+ ∝ maturité` ; le Qi est exporté vers le joueur
    (`harvested=True`, §4) tandis qu'une fraction de résidu retourne au sol. La
    plante reste VIVANTE. Si la Vigueur ne couvre pas le coût, l'effort est
    tronqué : gain ET résidu × ratio (récolte partielle). Sur du mûr, net positif
    (gain ≫ coût) — le canal de ressourcement légitime.
    Renvoie le ratio d'effort réalisé ∈ [0, 1]."""
    ratio = spend(game_state, player, HARVEST_VIGUEUR_COST)
    gain(game_state, player, HARVEST_GAIN_FULL * maturite(plant) * ratio)
    biomass = (plant.current_stage + 1.0) * 0.4   # même barème que le tick récolte
    eco.add_necromass(*plant.position, biomass * ratio, harvested=True)
    return ratio


def deraciner(game_state: dict, player: str, plant, eco) -> bool:
    """Déracinage d'une plante vivante (spec §3.3) — action BINAIRE destructrice.
    Coût ÉLEVÉ, aucun gain. À la mort, le Qi retourne AU SOL
    (`harvested=False`, §4 : nécromasse ∝ hauteur, comme toute mort naturelle).
    Tout-ou-rien : la plante ne meurt QUE si le coût est intégralement payé. À
    vide, la Vigueur est drainée et rien n'est accompli — le raccourci destructeur
    échoue quand on est épuisé.
    Renvoie True si la plante a effectivement été déracinée."""
    ratio = spend(game_state, player, ELEVE)
    if ratio < 1.0:
        return False
    plant.health = 0
    eco.add_necromass(*plant.position, necromass_biomass(plant), harvested=False)
    return True


def ecraser(game_state: dict, player: str, urgence: bool = True) -> bool:
    """Écraser un nuisible (spec §3.3) — action BINAIRE. Pour l'instant
    COMPTABILITÉ VIGUEUR SEULE : aucune entité nuisible n'existe encore dans le
    moteur (champ ambiant nuisible/auxiliaire à concevoir, §1). Coût
    MODÉRÉ × URGENCE — ce geste valide le multiplicateur d'urgence ; la
    suppression locale émergente ET le retour de pression viendront avec le champ
    nuisible. Tout-ou-rien (binaire) : effet futur appliqué seulement si payé.
    Renvoie True si le geste a été pleinement payé."""
    cost = MODERE * (URGENCE_MULT if urgence else 1.0)
    return spend(game_state, player, cost) >= 1.0
