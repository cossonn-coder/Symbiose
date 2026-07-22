"""
SYMBIOSE — sim/actions/deblocage.py
DÉBLOCAGE des gestes (sprint PALETTE DE GESTES, tronçon ①).
Spec : `docs/joueur/gestes/conception_palette_gestes.md` §3.2/§3.3/§3.4 + kickoff
`sprints/joueur/gestes/sprint_palette_gestes/01_deblocage_python.md`.

L'ÉTAT et les DONNÉES du déblocage, PAR AVATAR, persistés dans la save JSON
(comme maîtrise/encyclopédie) — jamais de logique de simulation. Le joueur ouvre
sa palette de gestes en apprenant (maîtrise), en agissant (poser un bac ouvre
composter) ou en reproduisant un phénomène (voie expérimentale émergente). La
palette Godot LIT l'ensemble ouvert dans le snapshot ; elle ne propose que
l'ouvert (pas de gating DUR — un geste verrouillé n'existe simplement pas encore
dans la palette, philo #6 : jamais de punition d'une tentative).

GARDE-FOU DE COUCHE (miroir de `sim/maitrise.py`, §6) : ce module vit AU-DESSUS
du tick écologique. Le golden (`tests/test_golden.py`) est une succession
spontanée SANS joueur → aucune clé `gestes_debloques` n'est jamais créée → no-op
strict. Si le golden bouge, c'est un BUG (fuite dans le tick), pas un re-figeage.
Aucun RNG (philo #3) : l'évaluation des conditions est déterministe.

Import LÉGER de `sim.maitrise` (lecture de palier) uniquement — on n'importe
JAMAIS les gestes eux-mêmes (respect des couches : ce module est data/état).
"""
from __future__ import annotations

from sim import maitrise as M


# --- Set de BASE (D9) : gestes toujours disponibles, dès le 1ᵉ avatar ---------
# Gestes rustiques du jardinier débutant (calibrage F5, ajustable). `tailler` a
# QUITTÉ la BASE (D12) : il devient GATED derrière la chaîne sécateur→couper→
# tailler ci-dessous. `deraciner`/`grelinette` = BASE (gestes rustiques, kickoff).
# `pincer`/`arracher`/`glaner` = BASE (acquisition des moyens d'agir ①/③, spec
# §A/§C) : gestes à mains nues du gradient structurel (`pincer < arracher <
# couper/tailler`) et glanage de litière — amorçables SANS outil ni maîtrise, dès
# le 1ᵉ avatar (c'est ce qui répond au F5 « pas d'option couper » : un geste
# structurel d'emblée). Leur absence ici les grisait à jamais dans la palette Godot
# (④). No-op golden : le smoke tourne sans joueur → clé `gestes_debloques` jamais
# créée → ce set n'est jamais matérialisé.
GESTES_BASE: frozenset[str] = frozenset({
    "planter", "arroser", "recolter", "manger",
    "ecraser", "becher", "favoriser_auxiliaire",
    "deraciner", "grelinette",
    "pincer", "arracher", "glaner",
    # Terrassement (hydrologie ⑦) : gestes rustiques à la bêche, du même registre que
    # `becher`/`deraciner` — amorçables dès le 1ᵉ avatar (creuser une cuvette, ouvrir
    # un fossé de drainage n'exige aucune maîtrise). No-op golden (set jamais matérialisé
    # hors joueur). Découverte à l'usage (D60) via le pont, comme les autres.
    "creuser", "drainer",
})


# --- Table data-driven `GESTE_UNLOCK` (§3.3) ---------------------------------
# Pour chaque geste GATED : une LISTE de conditions ALTERNATIVES (OU implicite —
# ouvert si l'UNE passe). Formes atomiques d'une condition (grammaire §3.2, D12) :
#   ("maitrise", objet, palier) — vrai si M.palier(gs, player, objet) >= palier ;
#   ("action", verbe)           — vrai si le joueur a RÉALISÉ ce verbe-déclencheur ;
#   ("et", [cond, cond, …])     — composée, vraie si TOUTES les sous-conditions ;
#   ("evenement", marqueur)     — voie expérimentale émergente, vraie si le marqueur
#                                 écologique a été consigné au ledger du joueur (le
#                                 MOTEUR le pose quand le phénomène se produit ; ici
#                                 on ne fait que le LIRE).
# Conditions PROPOSÉES (calibrage F5, ajustable). Les clés `bouturer`/`greffer`
# sont posées ICI ; le geste lui-même arrive en ②/③ (dispatch tolérant tant que
# le verbe n'existe pas).
GESTE_UNLOCK: dict[str, list] = {
    # taille — chaîne D12 : sécateur → couper → tailler → bouturer.
    "couper":   [("action", "posseder_secateur")],
    "tailler":  [("action", "couper")],
    "bouturer": [("et", [("maitrise", "taille", 2), ("maitrise", "semis", 2)]),
                 ("evenement", "bouture_spontanee")],
    "greffer":  [("maitrise", "greffe", 1)],   # câblé en ③, clé posée ici

    # compost
    "poser_bac":    [("maitrise", "compostage", 1)],
    "poser_pile":   [("maitrise", "compostage", 1)],
    "composter":    [("action", "poser_bac")],
    "retourner":    [("action", "poser_bac")],
    "epandre":      [("action", "poser_bac")],
    "empiler_bois": [("action", "poser_pile")],

    # conteneurs
    "poser_pot":         [("maitrise", "jardinage_hors_sol", 1)],
    "poser_bac_culture": [("maitrise", "jardinage_hors_sol", 1)],
    "deplacer_pot":      [("action", "poser_pot")],
    "planter_conteneur": [("action", "poser_pot")],

    # supports
    "poser_tuteur":   [("maitrise", "palissage", 1)],
    "poser_treillis": [("maitrise", "palissage", 1)],
    "poser_pergola":  [("maitrise", "palissage", 1)],
    "palisser":       [("action", "poser_tuteur")],

    # paillage
    "pailler": [("maitrise", "paillage", 1)],
    "broyer":  [("maitrise", "paillage", 1)],

    # ruche
    "poser_ruche":   [("maitrise", "apiculture", 1)],
    "recolter_miel": [("action", "poser_ruche")],
}


# Verbes-DÉCLENCHEURS (voie action §3.2·b) : seuls ces gestes, une fois RÉUSSIS,
# ouvrent un autre geste → seuls eux méritent un `marquer_action` (couplage
# minimal, kickoff). Dérivé de `GESTE_UNLOCK` : tout verbe cité dans une condition
# `("action", …)`. `posseder_secateur` n'est pas un geste (marqueur d'outil posé
# par le futur flux d'acquisition d'outils, calibrage F5) → mais on le laisse dans
# l'ensemble pour que `marquer_action("posseder_secateur")` reste reconnu.
DECLENCHEURS: frozenset[str] = frozenset(
    cond[1]
    for conditions in GESTE_UNLOCK.values()
    for cond in conditions
    if cond[0] == "action"
)


# --- État joueur (miroir de M.ensure_player_maitrise) ------------------------
def init_gestes_debloques(game_state: dict, player: str) -> set[str]:
    """Crée (si besoin) et renvoie l'ensemble des gestes ouverts d'un avatar.
    C'est le geste d'OPT-IN : tant qu'aucun joueur n'est initialisé, `game_state`
    n'a pas de clé `gestes_debloques` → le tick reste un no-op strict (golden
    intact). Tout nouvel avatar démarre au set de BASE (D9)."""
    debl = game_state.setdefault("gestes_debloques", {})
    return debl.setdefault(player, set(GESTES_BASE))


def _actions_faites(game_state: dict, player: str) -> set[str]:
    """Ensemble des VERBES-déclencheurs déjà réalisés par l'avatar (voie action,
    §3.2·b). Crée la tranche à la volée (opt-in, comme les gestes ouverts)."""
    faites = game_state.setdefault("actions_faites", {})
    return faites.setdefault(player, set())


def est_debloque(game_state: dict, player: str, verbe: str) -> bool:
    """Lecture pure : le geste est-il ouvert pour cet avatar ? Un geste de BASE
    l'est toujours ; un geste GATED l'est une fois `evaluer_deblocages` l'a
    ouvert. Ne crée RIEN (un joueur sans couche déblocage → BASE par défaut)."""
    if verbe in GESTES_BASE:
        return True
    debl = game_state.get("gestes_debloques")
    if not debl:
        return False
    ouverts = debl.get(player)
    return bool(ouverts) and verbe in ouverts


def marquer_action(game_state: dict, player: str, verbe: str) -> None:
    """Consigne qu'un VERBE-déclencheur a été réalisé (voie action §3.2·b). Idempotent
    (un set). À appeler UNIQUEMENT sur les déclencheurs de la chaîne (`poser_bac`,
    `poser_pile`, `poser_pot`, `poser_tuteur`, `poser_ruche`, `couper`,
    `posseder_secateur`) — couplage MINIMAL : n'importe quel autre geste n'a pas
    besoin d'être marqué (il ne déclenche aucun déblocage)."""
    _actions_faites(game_state, player).add(verbe)


# --- Événements écologiques émergents (voie c, §3.2·c) -----------------------
def marquer_evenement(game_state: dict, player: str, marqueur: str) -> None:
    """Consigne un MARQUEUR écologique émergent au ledger du joueur (voie
    expérimentale §3.2·c) : ex. `bouture_spontanee` (une branche taillée plantée
    et maintenue humide qui s'enracine seule). Posé par le MOTEUR quand le
    phénomène se produit — le câblage du phénomène lui-même arrive en ② (bouture).
    Ici on n'expose que le RÉCEPTACLE (lecture par `_cond_remplie`). Idempotent."""
    marqueurs = game_state.setdefault("marqueurs_ecolo", {})
    marqueurs.setdefault(player, set()).add(marqueur)


def _a_evenement(game_state: dict, player: str, marqueur: str) -> bool:
    """Lecture pure : le marqueur écologique a-t-il été consigné pour l'avatar ?"""
    marqueurs = game_state.get("marqueurs_ecolo")
    if not marqueurs:
        return False
    m = marqueurs.get(player)
    return bool(m) and marqueur in m


# --- Évaluateur de condition (récursif, 4 formes) ----------------------------
def _cond_remplie(game_state: dict, player: str, cond: tuple) -> bool:
    """Vrai ssi la condition `cond` est satisfaite pour l'avatar. Couvre les 4
    formes de la grammaire (§3.2). Récursif pour la forme composée `et`.
    Déterministe (aucun RNG). Une forme inconnue est traitée comme NON remplie
    (dégradation gracieuse : on n'ouvre jamais un geste par erreur de table)."""
    forme = cond[0]
    if forme == "maitrise":
        _, objet, palier = cond
        return M.palier(game_state, player, objet) >= palier
    if forme == "action":
        return cond[1] in _actions_faites(game_state, player)
    if forme == "evenement":
        return _a_evenement(game_state, player, cond[1])
    if forme == "et":
        return all(_cond_remplie(game_state, player, sous) for sous in cond[1])
    return False


def _verbe_ouvrable(game_state: dict, player: str, verbe: str,
                    conditions: list) -> bool:
    """Vrai ssi l'UNE des conditions ALTERNATIVES (OU) du geste est remplie."""
    return any(_cond_remplie(game_state, player, cond) for cond in conditions)


# --- Hook d'évaluation (event-driven, hors tick) -----------------------------
def evaluer_deblocages(game_state: dict, player: str) -> list[str]:
    """Ouvre tout geste GATED dont une condition est désormais remplie et qui
    n'était pas déjà ouvert ; renvoie la liste (triée, déterministe) des verbes
    NOUVELLEMENT ouverts — pour la NOTIFICATION diégétique côté pont/vue.

    Event-driven (§3.3) : à appeler APRÈS un franchissement de palier
    (`crediter_succes`/`detecter`) ou APRÈS une action déclenchante. Idempotent :
    un geste déjà ouvert n'est jamais re-signalé. Ne touche que l'état JOUEUR
    (opt-in) → golden intact."""
    ouverts = init_gestes_debloques(game_state, player)
    nouveaux: list[str] = []
    for verbe, conditions in GESTE_UNLOCK.items():
        if verbe not in ouverts and _verbe_ouvrable(game_state, player,
                                                     verbe, conditions):
            ouverts.add(verbe)
            nouveaux.append(verbe)
    nouveaux.sort()   # ordre déterministe (le dict est ordonné, mais on borne)
    return nouveaux


def gestes_debloques(game_state: dict, player: str) -> list[str]:
    """Liste TRIÉE des gestes ouverts d'un avatar (BASE ∪ ce qui a été débloqué) —
    forme d'EXPO au snapshot du pont (la palette Godot la lit). Lecture pure : un
    joueur sans couche déblocage retombe sur la BASE (aucune écriture)."""
    debl = game_state.get("gestes_debloques")
    ouverts = (debl or {}).get(player)
    if not ouverts:
        return sorted(GESTES_BASE)
    return sorted(ouverts)
