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

PORTES DES TECHNIQUES (sprint ACCÈS AUX GESTES ①, 2026-11-12 —
`docs/joueur/gestes/conception_refonte_palette.md` §3). `GESTE_UNLOCK` seul tournait
en rond : une technique n'était découverte qu'en réussissant un geste… qu'elle
verrouillait (20 gestes sur 32 jamais ouverts). La table `PORTES_TECHNIQUE` ajoute
l'étage manquant : franchir une porte DÉCOUVRE la technique (palier 1), et les
conditions `("maitrise", <technique>, 1)` deviennent vraies d'elles-mêmes. Le test
`tests/test_atteignabilite.py` refait le point fixe et interdit le retour de l'impasse.
Seul import ajouté : la constante `PAILLAGE_DOSE` de `fields` (couche plus basse).
"""
from __future__ import annotations

from fields.ecofields import PAILLAGE_DOSE   # unité du stock de mulch (une dose = un `pailler`)
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
#   ("stock", nature, seuil)    — vrai si le stock de mulch de cette nature atteint
#                                 `seuil` (on a de quoi faire) ;
#   ("compte", verbe, n)        — vrai si le joueur a RÉUSSI `n` fois ce geste.
# Ces deux dernières formes (accès aux gestes ①) servent surtout aux PORTES plus bas.
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
    # perchoir (zoochorie ④) : on le comprend en ayant planté un tuteur (les oiseaux
    # s'y posent), ou par la maîtrise de la technique elle-même.
    "poser_perchoir": [("action", "poser_tuteur"), ("maitrise", "perchoir", 1)],

    # paillage. `broyer` suit la règle « l'OUTIL fait le geste » (accès aux gestes ①) :
    # il s'ouvrait sur la maîtrise du paillage, il s'ouvre sur le broyeur de l'Atelier
    # (marqueur posé au tronçon ② — sa technique est `broyage`, pas `paillage`).
    "pailler": [("maitrise", "paillage", 1)],
    "broyer":  [("action", "posseder_broyeur")],

    # couvertures climatiques (effondrement météo ③) — la maîtrise du concept `météo`
    # (levée en lisant les signes de gel/froid, cf. CONCEPT_PAR_STAGNATION) ouvre les
    # trois gestes de préparation. Seconde voie (accès aux gestes ①) : la technique
    # `protection-climatique` elle-même, que la porte « voile de l'Atelier » découvre.
    "poser_voile":    [("maitrise", "météo", 1), ("maitrise", "protection-climatique", 1)],
    "poser_cloche":   [("maitrise", "météo", 1), ("maitrise", "protection-climatique", 1)],
    "poser_ombriere": [("maitrise", "météo", 1), ("maitrise", "protection-climatique", 1)],

    # ruche
    "poser_ruche":   [("maitrise", "apiculture", 1)],
    "recolter_miel": [("action", "poser_ruche")],

    # sylviculture périphérique (PÉRIPHÉRIE ④, conception §4.3) — l'OUTIL fait le
    # geste : sans hache on n'abat pas, sans serpe on ne recèpe pas (marqueurs posés
    # par l'Atelier, `sim/outils.py`). L'étêtage, lui, s'apprend APRÈS le taillis :
    # on découvre la trogne en ayant recépé, pas en achetant un outil de plus.
    "abattre": [("action", "posseder_hache")],
    "receper": [("action", "posseder_serpe")],
    "eteter":  [("action", "receper")],

    # eau & roche périphériques (PÉRIPHÉRIE ⑤, conception §4.3). Deux logiques :
    #   • `entailler` suit la règle « l'OUTIL fait le geste » : sans pioche, pas
    #     d'entaille (marqueur posé par l'Atelier, `sim/outils.py`) ;
    #   • `endiguer`/`deriver` sont à la BÊCHE, qui n'a pas de marqueur d'outil (les
    #     gestes de bêche sont de BASE, cf. `creuser`/`drainer`). On les ouvre donc sur
    #     l'EXPÉRIENCE : avoir creusé une fois. C'est l'idiome d'`eteter` ← `receper`
    #     (on apprend à déplacer l'eau en ayant remué la terre), et ça met `creuser`
    #     dans `DECLENCHEURS` par simple dérivation — rien à câbler côté pont.
    "endiguer":  [("action", "creuser")],
    "deriver":   [("action", "creuser")],
    "entailler": [("action", "posseder_pioche")],
}


# --- Table data-driven `PORTES_TECHNIQUE` (accès aux gestes ①, conception §3.2) ---
# Pour chaque TECHNIQUE qui verrouille des gestes : une LISTE de conditions
# ALTERNATIVES (même grammaire que `GESTE_UNLOCK`, OU implicite). Une porte franchie
# DÉCOUVRE la technique (palier 0 → 1, `M.decouvrir`) ; elle n'ouvre aucun geste
# directement — c'est `GESTE_UNLOCK` qui le fait, à la passe suivante de
# `evaluer_deblocages`. RÈGLE (R2) : aucune porte ne passe par un geste de sa propre
# technique, sinon on retombe dans la poule et l'œuf.
# Quatre familles de portes : l'ATELIER (`posseder_*`), un GESTE DE BASE voisin
# (`compte`, `stock`), l'OBSERVATION (`evenement` posé par le pont après le tick) et
# le COURRIER (`lettre_*`). Les marqueurs `posseder_*`, `lettre_*` et d'observation
# sont POSÉS au tronçon ② ; ici on ne fait que les LIRE (comme `bouture_spontanee`).
# Seuils = point de départ, calibrage F5 (R7). Les noms de technique sont ceux
# d'`OBJETS_TOUCHES` (`sim/actions/couts.py`), vérifiés par le test d'atteignabilité.
# `broyage` n'a pas de porte : son seul geste, `broyer`, s'ouvre par l'outil.
PORTES_TECHNIQUE: dict[str, list] = {
    # Trois glanages : on a un tas de feuilles, l'idée du compost vient seule. Ou bien
    # on POSSÈDE un bac (celui qu'offre Odette pose le marqueur `poser_bac` au ② :
    # « posséder vaut avoir posé »).
    "compostage": [("compte", "glaner", 3), ("action", "poser_bac")],
    # On a de quoi pailler (feuilles glanées, ou botte de paille de l'Atelier).
    "paillage": [("stock", "feuilles", PAILLAGE_DOSE),
                 ("stock", "paille", PAILLAGE_DOSE)],
    "jardinage_hors_sol": [("action", "posseder_pots")],
    "palissage": [("action", "posseder_tuteurs"),
                  ("evenement", "grimpante_sans_appui")],
    "perchoir": [("evenement", "merle_seme")],
    # La greffe demande le savoir (la lettre) ET l'outil (le greffoir).
    "greffe": [("et", [("evenement", "lettre_greffe"),
                       ("action", "posseder_greffoir")])],
    "apiculture": [("maitrise", "pollinisation", 2),
                   ("evenement", "lettre_essaim")],
    "protection-climatique": [("action", "posseder_voile")],
}


def _atomes(cond: tuple):
    """Déplie une condition en ses formes ATOMIQUES (descend dans les `et`). Sert à
    dériver des tables les ensembles que le pont doit surveiller."""
    if cond[0] == "et":
        for sous in cond[1]:
            yield from _atomes(sous)
    else:
        yield cond


def _cites(forme: str) -> frozenset[str]:
    """Tous les noms cités par une condition de forme `forme` dans les DEUX tables."""
    return frozenset(
        atome[1]
        for table in (GESTE_UNLOCK, PORTES_TECHNIQUE)
        for conditions in table.values()
        for cond in conditions
        for atome in _atomes(cond)
        if atome[0] == forme
    )


# Verbes-DÉCLENCHEURS (voie action §3.2·b) : seuls ces gestes, une fois RÉUSSIS,
# ouvrent un autre geste → seuls eux méritent un `marquer_action` (couplage
# minimal, kickoff). Dérivé des tables : tout nom cité dans une condition
# `("action", …)`, y compris sous un `et` et dans les portes. Les `posseder_*` ne
# sont pas des gestes (marqueurs d'outil posés par l'Atelier, `sim/outils.py`) → on
# les laisse dans l'ensemble pour que `marquer_action("posseder_secateur")` reste
# reconnu.
DECLENCHEURS: frozenset[str] = _cites("action")

# Verbes COMPTÉS : seuls les gestes cités par une condition `("compte", …)` méritent
# un `compter_geste` au pont (même dérivation, même couplage minimal).
VERBES_COMPTES: frozenset[str] = _cites("compte")


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


def compter_geste(game_state: dict, player: str, verbe: str) -> int:
    """Incrémente le compteur de RÉUSSITES d'un geste (forme `compte`) et renvoie le
    nouveau total. À appeler par le pont, au même endroit que `marquer_action`, pour
    les seuls verbes de `VERBES_COMPTES`. État opt-in créé à la volée
    (`game_state["gestes_comptes"][player][verbe]`) → jamais matérialisé sans joueur."""
    comptes = game_state.setdefault("gestes_comptes", {}).setdefault(player, {})
    comptes[verbe] = comptes.get(verbe, 0) + 1
    return comptes[verbe]


def _compte(game_state: dict, player: str, verbe: str) -> int:
    """Lecture pure du compteur (0 si rien n'a été compté). Ne crée aucune clé."""
    return ((game_state.get("gestes_comptes") or {}).get(player) or {}).get(verbe, 0)


def _stock(game_state: dict, nature: str) -> float:
    """Lecture pure du stock de mulch d'une nature (0 sans stock). On lit le dict
    DIRECTEMENT : `paillage.mulch_stock()` créerait la clé à la lecture, et importer
    `sim.actions.paillage` d'ici brouillerait les couches (ce module est data/état)."""
    return (game_state.get("mulch_stock") or {}).get(nature, 0.0)


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


# --- Évaluateur de condition (récursif, 6 formes) ----------------------------
def _cond_remplie(game_state: dict, player: str, cond: tuple) -> bool:
    """Vrai ssi la condition `cond` est satisfaite pour l'avatar. Couvre les 6
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
    if forme == "stock":
        _, nature, seuil = cond
        return _stock(game_state, nature) >= seuil
    if forme == "compte":
        _, verbe, n = cond
        return _compte(game_state, player, verbe) >= n
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
    # 1) Les PORTES d'abord (accès aux gestes ①) : toute technique encore inconnue
    #    dont une porte est franchie est DÉCOUVERTE (palier 1). L'ordre compte : la
    #    passe `GESTE_UNLOCK` qui suit lit ces paliers et ouvre les gestes d'entrée
    #    dans le MÊME appel. Idempotent (`M.decouvrir` ne refait rien au palier ≥ 1).
    for technique, portes in PORTES_TECHNIQUE.items():
        if M.palier(game_state, player, technique) == 0 and _verbe_ouvrable(
                game_state, player, technique, portes):
            M.decouvrir(game_state, player, technique)
    # 2) Puis les gestes.
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
