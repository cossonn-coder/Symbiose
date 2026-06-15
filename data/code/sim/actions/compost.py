"""
SYMBIOSE — sim/actions/compost.py
Structures posables & compostage (décompo·compost ⑤, CONCEPTION §5).
Le CANAL VERTUEUX bon marché (philo #1) : poser une structure (planification,
MODÉRÉ) puis y déplacer la litière du sol (courant, FAIBLE), la laisser mûrir
(phase B), enfin l'ÉPANDRE (phase C) — restitution au sol. Phases A/B ne
touchaient AUCUN champ écolo (déplacement + maturation confinée) ; `epandre`
(phase C) est le SEUL geste de la famille qui écrit le sol — comme `becher`/
`arroser`, un geste joueur qui amende un champ au plot ciblé.
"""
from __future__ import annotations

from sim.vigueur import spend
from fields.ecofields import Structure, RETOURNE_DUREE   # structures posables (⑤) + durée retournement (⑤B)
from .couts import cout_action, OBJETS_TOUCHES

# Trio humus de l'épandage (⑤ phase C, §5.3 — décision #3 volet trio, figée avec
# les placeholders du kickoff, calibrage post-test). `epandre` puise dans
# `compost_mur` (borné) et le restitue au plot ciblé en TROIS voies : `om_stable`
# (structure/rétention/mémoire), `microbiome` (ENSEMENCÉ via `add` borné — pas un
# `set`, philo #4 : le sol grandit, il ne se télécharge pas), `fertilite`.
# Amendement COMPLET, pas un engrais. Le BAC (tendre) est ≈ équilibré ; la PILE
# (bois, humus forestier) BIAISE la structure et nourrit peu — pile = bac ×
# (1.3, 0.5, 0.4) sur (om_stable, microbiome, fertilite).
EPANDRE_W = {
    "bac":  {"om_stable": 0.6,  "microbiome": 0.3,  "fertilite": 0.3},
    "pile": {"om_stable": 0.78, "microbiome": 0.15, "fertilite": 0.12},
}

def _ramasser_vers_structure(eco, r: int, c: int, struct: Structure) -> float:
    """Déplace du plot (r,c) vers `struct` toutes les parcelles que la structure
    ACCEPTE (§5) : retire de la litière, fusionne dans le contenu. **Conserve la
    masse** (déplacement, jamais de création). La parcelle `diffus` (exsudats) n'est
    acceptée par aucune structure → reste au sol (décision ⑤A). Déterministe :
    parcourt la litière dans son ordre courant, aucun RNG. Renvoie la masse
    transférée (diagnostic/test)."""
    transfere = 0.0
    restant = []
    for p in eco.litiere[r][c]:
        if p.masse > 0.0 and struct.accepte(p.tissu):
            eco.deposer_dans_structure(struct, p.tissu, p.masse)
            transfere += p.masse
        else:
            restant.append(p)            # diffus, bois (pour un bac), parcelles vides
    eco.litiere[r][c] = restant
    return transfere


def poser_bac(game_state: dict, player: str, eco, r: int, c: int) -> Structure | None:
    """Poser un bac à compost (§5.1) au plot (r,c) — phase PLANIFICATION, coût
    MODÉRÉ. Crée une structure VIDE et l'ajoute à `eco.structures`. Binaire (modèle
    `deraciner`/`planter`) : la structure n'est posée QUE si le coût est
    intégralement payé — un geste à vide draine la Vigueur sans rien poser.
    Renvoie la `Structure` posée, ou None si la Vigueur est insuffisante."""
    cost = cout_action(game_state, player, "poser_bac", OBJETS_TOUCHES["poser_bac"])
    if spend(game_state, player, cost) < 1.0:
        return None
    struct = Structure(kind="bac", plot=(r, c))
    eco.structures.append(struct)
    return struct


def poser_pile(game_state: dict, player: str, eco, tile, r: int, c: int) -> Structure | None:
    """Poser une pile à bois (§5.1) au plot (r,c) — phase PLANIFICATION, coût
    MODÉRÉ. Symétrique de `poser_bac` (kind=`pile`), MAIS prend aussi `tile` car la
    pile a un BONUS ANNEXE que le bac n'a pas : elle est un **habitat `auxiliaire`**
    (§4.1). Décision #3 volet habitat (figée, sobre) : on réutilise le patron
    rondelle de `favoriser_auxiliaire` — la pile pose une rondelle `auxiliaire` sur
    la tuile (déjà lue par `_stability_grid` comme nectar/refuge persistant), zéro
    machinerie neuve. L'habitat est donc au niveau TUILE (uniforme), comme la
    rondelle ; le placement LOCAL au plot de la pile demanderait un champ habitat
    par plot → différé (D30, comme pour `favoriser_auxiliaire`).
    Binaire : la pile n'est posée QUE si le coût est intégralement payé. La rondelle
    est un BONUS best-effort — si toutes les tiges sont saturées (cas-bord), la pile
    est tout de même posée (sa raison d'être reste de recevoir du bois).
    Renvoie la `Structure` posée, ou None si la Vigueur est insuffisante."""
    cost = cout_action(game_state, player, "poser_pile", OBJETS_TOUCHES["poser_pile"])
    if spend(game_state, player, cost) < 1.0:
        return None
    struct = Structure(kind="pile", plot=(r, c))
    eco.structures.append(struct)
    for slot in tile.stakes:                  # pile → habitat auxiliaire (§4.1, patron favoriser_auxiliaire)
        if slot.add("auxiliaire"):
            break
    return struct


def composter(game_state: dict, player: str, eco, r: int, c: int,
              struct: Structure) -> bool:
    """Composter (§5.1) — ramasser la litière de SURFACE tendre du plot (r,c) vers
    le bac `struct`. Action sur le MILIEU, canal vertueux bon marché (philo #1) :
    coût FAIBLE. Binaire : le transfert n'a lieu que si le coût est payé. La parcelle
    `diffus` reste au sol (décision ⑤A) ; le bac refuse aussi le `bois`. No-op
    silencieux si rien à ramasser (plot propre) — on paie le geste, comme `becher`.
    Renvoie True si le geste a été pleinement payé (et donc appliqué)."""
    cost = cout_action(game_state, player, "composter", OBJETS_TOUCHES["composter"])
    if spend(game_state, player, cost) < 1.0:
        return False
    _ramasser_vers_structure(eco, r, c, struct)
    return True


def empiler_bois(game_state: dict, player: str, eco, r: int, c: int,
                 struct: Structure) -> bool:
    """Empiler du bois (§5.1) — déplacer les parcelles `bois` du plot (r,c) vers la
    pile `struct`. Jumeau de `composter` pour la matière ligneuse (BRF / hügelkultur).
    Coût FAIBLE, binaire, philo #1. La pile n'accepte QUE le `bois` (§5).
    Renvoie True si le geste a été pleinement payé (et donc appliqué)."""
    cost = cout_action(game_state, player, "empiler_bois", OBJETS_TOUCHES["empiler_bois"])
    if spend(game_state, player, cost) < 1.0:
        return False
    _ramasser_vers_structure(eco, r, c, struct)
    return True


def retourner(game_state: dict, player: str, struct: Structure) -> bool:
    """Retourner le compost (§5.1/§5.2) — geste d'entretien : arme le drapeau
    `retourne_restant` qui, pendant `RETOURNE_DUREE` semaines, MULTIPLIE la vitesse
    de maturation et LISSE les âges du contenu (tick_structures). C'est un **BONUS**,
    jamais une obligation (philo : le bac mûrit seul, aucune corvée bloquante).
    Coût FAIBLE, binaire (canal vertueux §5.1). N'écrit aucun champ écolo (philo #2)
    — ne touche que la structure. Pensé pour le bac ; sur une pile, accélère
    marginalement le bois (pas interdit). Renvoie True si le geste a été payé."""
    cost = cout_action(game_state, player, "retourner", OBJETS_TOUCHES["retourner"])
    if spend(game_state, player, cost) < 1.0:
        return False
    struct.retourne_restant = RETOURNE_DUREE
    return True


def epandre(game_state: dict, player: str, eco, r: int, c: int,
            struct: Structure, q: float | None = None) -> float:
    """Épandre du compost mûr (§5.3) — ferme la boucle vertueuse : restitue au plot
    (r,c) ciblé la jauge `compost_mur` accumulée par la maturation (phase B). C'est
    le SEUL geste ⑤ qui écrit le sol (philo #2 OK : un geste joueur amende un champ,
    exactement comme `becher`/`arroser` ; ce n'est pas un bonus DIRECT sur une
    plante — c'est le sol qui change, la réponse biologique émerge au tick).

    BORNÉ par la jauge (piège #5) : `q` = quantité demandée (None ⇒ tout le
    disponible) ; on n'épand JAMAIS plus que `compost_mur`. **Refus EN AMONT si rien
    à épandre** (jauge vide ou demande ≤ 0) — aucune Vigueur dépensée (modèle
    `planter`/lot vide : on ne paie pas un épandage qu'on ne peut pas faire).

    Effet = **trio humus** (§5.3, `EPANDRE_W[struct.kind]`) : `om_stable` (structure),
    `microbiome` ENSEMENCÉ (`add` borné par le champ, pas un `set` — philo #4),
    `fertilite`. Le BAC est équilibré, la PILE biaise la structure (humus forestier,
    peu nourrissant). Binaire : appliqué seulement si le coût (FAIBLE) est payé.
    Renvoie la quantité réellement épandue (0.0 = rien fait / non payé)."""
    dispo = struct.compost_mur
    quantite = dispo if q is None else min(q, dispo)
    if quantite <= 0.0:
        return 0.0                            # jauge vide ou demande nulle → aucune Vigueur dépensée
    cost = cout_action(game_state, player, "epandre", OBJETS_TOUCHES["epandre"])
    if spend(game_state, player, cost) < 1.0:
        return 0.0                            # Vigueur insuffisante → jauge intacte
    struct.compost_mur -= quantite
    w = EPANDRE_W[struct.kind]
    eco.om_stable.add(r, c, quantite * w["om_stable"])
    eco.microbiome.add(r, c, quantite * w["microbiome"])   # add borné (ensemence, philo #4)
    eco.fertilite.add(r, c, quantite * w["fertilite"])
    return quantite
