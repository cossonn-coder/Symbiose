"""
SYMBIOSE — sim/outils.py
L'ATELIER de la maison normande, canal d'acquisition des OUTILS (sprint
Acquisition des moyens d'agir, tronçon ②, dette D82).
Spec de référence : `docs/conception/CONCEPTION_ACQUISITION_OUTILS.md` §B.

Rôle : donner au joueur un flux qui POSE le marqueur d'outil (`posseder_secateur`)
que RIEN ne posait — sans quoi toute la chaîne « taille » (`couper`→`tailler`→
`bouturer`, `sim/actions/deblocage.py`) reste morte (D82). L'Atelier est la seule
des 5 fonctions du hub-maison non câblée. Commande Vigueur-SEULE, **jumeau
d'`acheter_au_magazine`** (`sim/magazine.py`) : le magazine gate une offre + débite
la Vigueur + dépose une GRAINE ; ici on gate une offre + débite la Vigueur + pose
un MARQUEUR d'outil (puis on réévalue les déblocages qu'il ouvre).

PORTE — Vigueur SEULE, TÔT, AUCUNE maîtrise (spec §B) : le sécateur est de
l'outillage d'entrée de gamme, et gater sur la maîtrise « taille » créerait un
poule-œuf (on ne peut tailler sans sécateur, on n'aurait pas le sécateur sans
avoir taillé). C'est la différence de fond avec le magazine, dont la maîtrise EST
la condition d'apparition.

GARDE-FOU DE COUCHE (identique à `magazine`/`carnet`/`vigueur`) : `outils` vit au
niveau `sim`, AU-DESSUS du tick. Il importe `sim.vigueur` (fonds) et
`sim.actions.deblocage` (poser le marqueur + rouvrir la chaîne) — **jamais
l'inverse** : `engine`/`fields`/`plants` ne l'importent pas. Aucun RNG (philo #3).
Pas de joueur → pas d'appel ; le golden tourne SANS joueur → ce module n'est
jamais sollicité → no-op strict (golden intact).
"""
from __future__ import annotations

from sim import vigueur
from sim.actions.deblocage import marquer_action, evaluer_deblocages
from sim.actions.paillage import mulch_stock   # canal 3 : l'import matériau crédite le STOCK de mulch
from fields.ecofields import PAILLAGE_DOSE      # unité du stock (une dose = un geste `pailler`)

# --- Registre `OUTILS` data-driven (spec §B) --------------------------------
# Un outil = un MARQUEUR d'action à poser (le même vocabulaire que la chaîne de
# déblocage, `("action", "posseder_secateur")` dans `GESTE_UNLOCK`) + un COÛT
# Vigueur + un drapeau `offre` (l'outil est-il présenté à l'Atelier). Structure
# EXTENSIBLE : greffoir, bêche… s'ajouteront ici sans toucher la logique.
#
# `cout_vigueur` = PLACEHOLDER de calibrage F5 (comme `COUT_MAGAZINE`). Choisi
# MODÉRÉ (bien en-dessous du magazine) : l'outil d'entrée de gamme doit être
# accessible tôt, sur la seule Vigueur de base (MAX_BASE=100), sans progression
# préalable — sinon la chaîne taille resterait inatteignable au débutant (D82).
OUTILS: dict[str, dict] = {
    "secateur": {
        "marqueur": "posseder_secateur",
        "cout_vigueur": 40.0,   # placeholder, calibrage F5
        "offre": True,
    },
}


def _possede(game_state: dict, player: str, marqueur: str) -> bool:
    """Le joueur porte-t-il déjà ce marqueur d'outil ? Lecture PURE de la tranche
    `actions_faites` (là où `marquer_action` consigne les verbes-déclencheurs et
    les marqueurs d'outil, `sim/actions/deblocage.py`). Ne crée AUCUNE clé (no-op
    golden) : un joueur sans couche déblocage n'a rien acquis → False."""
    faites = game_state.get("actions_faites")
    if not faites:
        return False
    porte = faites.get(player)
    return bool(porte) and marqueur in porte


def offre_outils(game_state: dict, player: str) -> list[str]:
    """Outils présentés à l'Atelier pour ce joueur (spec §B) : ceux dont le drapeau
    `offre` est ouvert. Porte Vigueur-SEULE → aucune maîtrise à vérifier ici, la
    liste est STABLE (ici : toujours `["secateur"]`). Tri STABLE = ordre du registre
    (déterminisme, pas de RNG). Lecture PURE. Le `game_state`/`player` sont acceptés
    pour figer la signature (parité `magazine_offres`) et brancher un futur gating
    par état sans casser l'appelant."""
    return [outil for outil, spec in OUTILS.items() if spec.get("offre")]


def acquerir_outil(game_state: dict, player: str, outil: str) -> bool:
    """Acquiert un outil à l'Atelier : gate offre → (idempotence) → dépense Vigueur
    → pose le marqueur → rouvre la chaîne de déblocage (spec §B). Renvoie `True` ssi
    l'acquisition a eu lieu, `False` SANS aucun effet sinon. Jumeau
    d'`acheter_au_magazine` : event-driven HORS TICK (appelé par le pont/UI, jamais
    le tick). Aucune exception (bool franc, kickoff §Le patron).

    Séquence (ordre important pour ne JAMAIS débiter sans livrer) :
      1. GATE STRICT — `outil` doit être dans `offre_outils(...)` au moment de
         l'acquisition (on RE-VÉRIFIE, on ne fait pas confiance à l'appelant). Hors
         offre → `False`, rien débité.
      2. IDEMPOTENCE — si le marqueur est DÉJÀ posé (outil déjà possédé), on refuse
         proprement SANS nouvelle dépense (`False`) : ré-acquérir ne coûte rien et ne
         double rien. Distinct d'un « succès » : l'appelant sait qu'aucun débit n'a
         eu lieu (le `bilan` du pont rafraîchit la Vigueur inchangée).
      3. VIGUEUR — `vigueur.spend(cost)` renvoie le RATIO d'effort : 1.0 ssi payé en
         entier. Fonds insuffisants → ratio < 1.0 ; on ANNULE (on ne livre pas un
         outil à moitié payé). NB : `spend` draine `min(cost, courante)` même en
         échec — coût « tenté » de l'acte (sémantique de `sim/actions.py`).
      4. LIVRAISON — `marquer_action(gs, player, marqueur)` pose l'outil, puis
         `evaluer_deblocages(gs, player)` rouvre tout geste que ce marqueur débloque
         (`couper`, puis `tailler` en cascade). `True`.

    PUR côté écolo : touche UNIQUEMENT l'état JOUEUR (`vigueur`, `actions_faites`/
    `gestes_debloques`), jamais les champs ni le tick. Aucun RNG."""
    if outil not in offre_outils(game_state, player):
        return False                          # gate : hors offre, aucun effet
    marqueur = OUTILS[outil]["marqueur"]
    if _possede(game_state, player, marqueur):
        return False                          # déjà possédé → pas de nouvelle dépense
    cost = OUTILS[outil]["cout_vigueur"]
    if vigueur.spend(game_state, player, cost) < 1.0:
        return False                          # fonds insuffisants → acquisition annulée
    marquer_action(game_state, player, marqueur)
    evaluer_deblocages(game_state, player)
    return True


# --- Registre `MATERIAUX` data-driven (moyens d'agir ③, canal 3) -------------
# L'Atelier fournit aussi de la MATIÈRE contre Vigueur : un import EXTERNE de mulch,
# parallèle au magazine de graines (le magazine importe déjà des espèces « de
# l'extérieur ») → le principe de `paillage.py` (« le mulch VIENT de quelque part »)
# TIENT : ce n'est pas du « mulch abstrait », c'est un achat explicite en Vigueur.
# Un matériau = une NATURE de `NATURES_MULCH` (ici `paille`, déjà couplée) + une
# DOSE créditée au stock (en unités de `PAILLAGE_DOSE` : un geste `pailler` en
# consomme une) + un COÛT Vigueur + un drapeau `offre`. EXTENSIBLE (botte de BRF,
# ballot de foin…) sans toucher la logique. `dose`/`cout_vigueur` = PLACEHOLDERS de
# calibrage F5 : trois doses par botte, coût MODÉRÉ (dépannage bon marché, sans
# remplacer le glanage/la récolte gratuits — l'import RESTE un pis-aller Vigueur).
MATERIAUX: dict[str, dict] = {
    "botte_paille": {
        "nature": "paille",
        "dose": 3.0 * PAILLAGE_DOSE,   # placeholder, calibrage F5
        "cout_vigueur": 20.0,          # placeholder, calibrage F5
        "offre": True,
    },
}


def offre_materiaux(game_state: dict, player: str) -> list[str]:
    """Matériaux présentés à l'Atelier (parité `offre_outils`) : ceux dont le drapeau
    `offre` est ouvert. Vigueur-SEULE, aucune maîtrise → liste STABLE (ordre du
    registre, déterminisme). Lecture PURE ; `game_state`/`player` acceptés pour figer
    la signature et brancher un futur gating sans casser l'appelant."""
    return [mat for mat, spec in MATERIAUX.items() if spec.get("offre")]


def acquerir_materiau(game_state: dict, player: str, materiau: str) -> bool:
    """Acquiert un matériau (mulch) à l'Atelier : gate offre → dépense Vigueur →
    crédite le STOCK de mulch de sa nature (moyens d'agir ③, canal 3). Renvoie `True`
    ssi l'acquisition a eu lieu, `False` SANS aucun effet sinon. Jumeau
    d'`acquerir_outil` (event-driven HORS TICK), à ceci près qu'il n'est PAS
    idempotent (on peut racheter du mulch autant qu'on veut : c'est un consommable,
    pas un outil) et qu'il pose de la MATIÈRE (stock) plutôt qu'un marqueur.

    Séquence (ordre important pour ne JAMAIS débiter sans livrer) :
      1. GATE STRICT — `materiau` doit être dans `offre_materiaux(...)` (on
         RE-VÉRIFIE, on ne fait pas confiance à l'appelant). Hors offre → `False`.
      2. VIGUEUR — `vigueur.spend(cost)` renvoie le RATIO d'effort : 1.0 ssi payé en
         entier. Fonds insuffisants → ratio < 1.0 ; on ANNULE (pas de botte à moitié
         payée). NB : `spend` draine `min(cost, courante)` même en échec.
      3. LIVRAISON — `mulch_stock(gs)[nature] += dose` : la matière atterrit au stock,
         `pailler` la posera au sol (le principe `paillage.py` tient : mulch sourcé).

    PUR côté écolo : touche l'état JOUEUR (`vigueur`) + le STOCK profil (`mulch_stock`,
    patron `player_seed_bank`, PAS un champ du tick) — jamais les champs ni le tick.
    Aucun RNG (philo #3)."""
    if materiau not in offre_materiaux(game_state, player):
        return False                          # gate : hors offre, aucun effet
    spec = MATERIAUX[materiau]
    if vigueur.spend(game_state, player, spec["cout_vigueur"]) < 1.0:
        return False                          # fonds insuffisants → acquisition annulée
    mulch_stock(game_state)[spec["nature"]] += spec["dose"]
    return True
