"""
SYMBIOSE — sim/maitrise_detection.py
Couche DÉTECTION DE SUCCÈS (D12, tronçon i4) — le dernier et le plus délicat.
Spec de référence : `docs/joueur/maitrise/conception_maitrise.md` §9 (le succès par axe).

Jusqu'ici (i1–i3) les preuves de maîtrise arrivaient PAR INJECTION (`crediter_succes`/
`enregistrer_preuve` appelés à la main). Ce module BRANCHE la détection
automatique : il LIT les signaux que le tick émet déjà (§9.1 — le `log` d'un
`tick_semaine` + l'état post-tick des plantes) et en déduit, tout seul, quand un
SUCCÈS a eu lieu — *une action joueur dont l'effet émergent améliore le résultat
au-delà du cours spontané, et qui est observée* (§9.0). Il appelle alors
`maitrise.enregistrer_preuve` sur le bon objet, avec la bonne NATURE (§9.2/§9.3).

GARDE-FOU ABSOLU (§6/§9.6) : la détection vit AU-DESSUS du tick. Elle *lit* le
résultat d'un tick (jamais ne le fait avancer), n'ajoute AUCUN état au tick
déterministe et n'écrit RIEN dans `engine`. Le golden écologique reste INTACT.
Sens de couche : ce module importe `maitrise` + `plants` ; `engine` ne l'importe
JAMAIS (pas d'inversion). Déterminisme total (aucun RNG : fonction pure de l'état
post-tick).

Architecture (décisions i4, documentées dans `00_etat.md`) :
  - LOGEMENT (a) : module dédié appelé par le driver APRÈS chaque `eng.tick_semaine()`
    (symétrique de `tick_player_vigueur`). `actions.py` reste inchangé.
  - IDENTITÉ : `zone = (tile_id, r, c)` (la position-foyer du plot — stable,
    déterministe). L'imputation geste→amélioration se fait sur la ZONE ;
    l'espèce (pour le crédit) se lit dans le nom de la ligne de log.
  - GATE D'OBSERVATION (§9.6, minimal) : on ne crédite qu'un objet DÉJÀ découvert
    (`palier ≥ 1`). L'observation fine (carnet/notif) se branchera dessus → D14.
  - NATURE CROISSANTE (§9.2) : un succès ne crédite l'espèce que si sa nature
    correspond au palier courant (`NATURE_REQUISE`) — impossible de sauter une
    marche. Les concepts (§9.3) ont une nature uniforme (« grâce à ton
    intervention ») → pas de gate par palier.
  - PURETÉ : la détection crédite des PREUVES (maîtrise) ; elle ne touche PAS la
    Vigueur (sens Vigueur→Maîtrise). Le pont Vigueur §4.3 d'un succès AUTO reste
    au driver (il voit les deux couches) — non câblé ici (sobre, calibrage D14).
"""
from __future__ import annotations

from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from sim import maitrise as M
# Le parsing du log a été EXTRAIT dans `sim/evenements.py` (sprint Voix
# narratives, tronçon ① — refactor pur). `_evenements` y est déplacé TEL QUEL et
# ré-importé ici : la détection le consomme à l'identique (golden joueur
# inchangé). Le module commun expose AUSSI `evenements()` (élargi) pour le carnet.
from sim.evenements import _evenements

# --- Placeholders nommés — *calibrage D12.4 post-test* ----------------------
# Largeur de la fenêtre d'imputation (§9.6) : un geste joueur en semaine t peut
# être crédité de l'amélioration qu'il produit dans [t, t+N]. Trop court → on rate
# l'effet différé ; trop long → on impute du hasard. Placeholder visible.
FENETRE_IMPUTATION = 4        # semaines
# Stade minimal d'une recrue FÉRALE pour compter comme « naturalisée » (§9.4(b),
# « atteint jeune/adulte en pleine santé »). 0=semis, 1=jeune pousse, ≥2=établie.
STAGE_NATURALISATION = 2

# Concept transversal lié à chaque cause de stagnation (§9.2/§9.3 ; clés §10.2).
# Lever un `⏸ sec` prouve l'eau, un `🌑 ombre` la lumière, un `❄ froid` la météo.
CONCEPT_PAR_STAGNATION = {"sec": "eau", "ombre": "lumière", "froid": "météo"}

# Nature de preuve REQUISE pour franchir chaque palier d'une ESPÈCE (§9.2). Un
# succès détecté ne crédite l'espèce que si sa nature figure parmi celles que
# l'événement satisfait ET qu'elle correspond au palier courant.
#   1→2 lever une stagnation · 2→3 amener à reproduction ·
#   3→4 optimiser en pleine santé · 4→5 conjonction (§9.4).
NATURE_REQUISE = {1: "stagnation", 2: "reproduction", 3: "optimisation", 4: "conjonction"}

# --- Reverse mapping objet → clé, DÉRIVÉ des catalogues (jamais dupliqué) -----
# (`_CLE_DE_NOM` log → clé vit désormais dans `sim/evenements.py` avec le parsing ;
# ici on n'a plus besoin que du sens objet → clé, pour la naturalisation férale.)
_CATALOGUE = {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}
_CLE_DE_CLASSE = {cls: cle for cle, cls in _CATALOGUE.items()}       # objet → clé


# --- État gameplay de la détection (§9.6) — par avatar, au-dessus du tick -----
def _detection(game_state: dict, player: str) -> dict:
    """Tranche de détection du joueur, logée DANS `game_state["maitrise"][player]`
    sous la clé `_detection` (maîtrise possède `objets`, la détection possède
    `_detection` — `maitrise.py` reste pur, il ignore cette clé). Crée la tranche
    maîtrise si besoin : l'opt-in vaut pour le driver, jamais pour le golden écolo
    (qui n'appelle JAMAIS ce module).

    - `gestes`     : journal des gestes récents `[(semaine, zone, verb)]` (fenêtre
                     §9.6). `verb` (str|None) est le VERBE du geste (D60 ③) : il
                     permet au pont de créditer le geste lui-même en poids fort
                     quand son imputation produit une amélioration. Additif :
                     rétro-compatible (verb=None pour les appels sans verbe).
    - `stagnations`: zone → `(semaine, raison)` — la dernière stagnation vue, en
                     attente d'être levée dans la fenêtre.
    - `replante`   : ensemble des zones plantées PAR LE JOUEUR (§9.6(i)). Tout ce
                     qui n'y est pas est FÉRAL (défaut). Pas encore de geste
                     `planter` → l'ensemble reste vide, tout est féral (correct).
    - `naturalise`/`experte` : flags par espèce pour la conjonction palier 5 (§9.4).
    """
    slice_j = M.ensure_player_maitrise(game_state, player)
    return slice_j.setdefault("_detection", {
        "gestes": [], "stagnations": {},
        "replante": set(), "naturalise": set(), "experte": set(),
    })


# --- API d'enregistrement des gestes joueur (appelée par le driver/UI) -------
def noter_geste(game_state: dict, player: str, semaine: int, zone,
                verb: str | None = None) -> None:
    """Enregistre un geste joueur dans la fenêtre d'imputation (§9.6(ii)). `zone`
    = `(tile_id, r, c)` du plot agi (la détection impute l'amélioration de ce plot
    au geste). Le DRIVER appelle ceci quand le joueur agit (symétrique : il appelle
    `detecter` après chaque tick). On NE câble PAS `actions.py` ici — la détection
    est event-driven *par tick*, les gestes *par clic* : le driver relie les deux
    (découplage acté). Élague la fenêtre au passage.

    `verb` (optionnel, D60 ③) : le verbe du geste, mémorisé pour que la progression
    geste/outil/technique retrouve QUEL geste a produit une amélioration (poids fort).
    Défaut None = rétro-compatible (les appels historiques sans verbe restent valides)."""
    det = _detection(game_state, player)
    det["gestes"].append((semaine, tuple(zone), verb))
    _elaguer(det, semaine)


def marquer_replante(game_state: dict, player: str, tile_id: str, r: int, c: int) -> None:
    """Marque une zone comme PLANTÉE PAR LE JOUEUR (§9.6(i)) — l'inverse de féral.
    Hook pour le futur geste `planter` (pas encore codé) : d'ici là toute plante
    établie par le tick reste férale (correct pour §9.4(b)). Additif, jamais
    appelé par le golden."""
    _detection(game_state, player)["replante"].add((tile_id, r, c))


def _elaguer(det: dict, semaine: int) -> None:
    """Oublie gestes et stagnations sortis de la fenêtre `[semaine-N, semaine]` —
    borne la mémoire et empêche d'imputer du hasard trop ancien (§9.6)."""
    limite = semaine - FENETRE_IMPUTATION
    det["gestes"] = [(s, z, v) for (s, z, v) in det["gestes"] if s >= limite]
    det["stagnations"] = {z: (s, r) for z, (s, r) in det["stagnations"].items()
                          if s >= limite}


def _geste_impute(det: dict, zone, semaine: int, depuis: int) -> bool:
    """Y a-t-il un geste joueur imputable à `zone`, posé entre `depuis` (semaine de
    la stagnation) et `semaine` (de l'amélioration), dans la fenêtre ? C'est le
    cœur de §9.0 : sans geste, l'amélioration est ÉMERGENTE (« ça pousse tout
    seul ») et ne crédite RIEN."""
    return any(z == zone and depuis <= s <= semaine for (s, z, _v) in det["gestes"])


def verbes_imputables(game_state: dict, player: str, zone, semaine: int,
                      depuis: int) -> list[str]:
    """Les VERBES des gestes imputables à `zone` dans la fenêtre `[depuis, semaine]`
    (D60 ③, volet succès). Sert au pont : quand `detecter` a crédité une amélioration
    sur une zone où un geste était imputé, le pont crédite ces verbes en poids fort.
    Ignore les gestes sans verbe (appels historiques). Ordre du journal (déterministe),
    dédupliqué. Lecture pure."""
    det = _detection(game_state, player)
    vus: list[str] = []
    for (s, z, v) in det["gestes"]:
        if v is not None and z == tuple(zone) and depuis <= s <= semaine and v not in vus:
            vus.append(v)
    return vus


def _crediter(game_state: dict, player: str, objet: str, natures: set[str]) -> int | None:
    """Crédite UNE preuve sur `objet` SI (gate §9.6) il est découvert (palier ≥ 1)
    ET (§9.2, espèces) la nature requise à son palier courant figure dans
    `natures`. Les concepts (sans famille → hors `NATURE_REQUISE` par palier) sont
    crédités dès qu'ils sont découverts. Renvoie le palier après crédit, ou None si
    rien n'a été crédité. JAMAIS d'auto-découverte (le gate l'interdit)."""
    pal = M.palier(game_state, player, objet)
    if pal < 1:
        return None                              # gate d'observation : non découvert
    est_espece = M.famille_de(objet) is not None
    if est_espece:
        requise = NATURE_REQUISE.get(pal)
        if requise is None or requise not in natures:
            return None                          # mauvaise marche (§9.2)
    return M.enregistrer_preuve(game_state, player, objet)


# --- Le détecteur principal -------------------------------------------------
def detecter(game_state: dict, player: str, log: list[str], semaine: int,
             zones_creditees: list | None = None) -> list[tuple]:
    """Lit les signaux d'UN tick (`log` retourné par `tick_semaine` + état post-tick
    `game_state["tiles"]`) et crédite les preuves correspondantes. Appelé par le
    driver APRÈS chaque tick. Renvoie la liste des `(objet, palier_après)` crédités
    (matière du pont Vigueur §4.3 et des notifications, branchés au driver/D14).

    `zones_creditees` (optionnel, D60 ③) : si une liste est passée, `detecter` y
    APPEND chaque `(zone, depuis)` où un GESTE imputable a produit un crédit — la
    matière pour que le pont retrouve le(s) verbe(s) (`verbes_imputables`) et les
    crédite en poids fort. Sortie SÉPARÉE de la valeur de retour (rétro-compatible :
    l'appelant qui l'ignore garde le comportement historique). `depuis` = semaine de
    départ de la fenêtre effective, pour retrouver les mêmes gestes.

    Pur au sens golden : observe, ne fait jamais avancer la simulation."""
    det = _detection(game_state, player)
    credits: list[tuple] = []

    def crediter(objet, natures):
        pal = _crediter(game_state, player, objet, natures)
        if pal is not None:
            credits.append((objet, pal))

    def signaler_zone(zone, depuis):
        if zones_creditees is not None:
            zones_creditees.append((tuple(zone), depuis))

    for kind, tile_id, pos, payload in _evenements(log):
        zone = (tile_id, *pos)
        if kind == "stagne":
            det["stagnations"][zone] = (semaine, payload)   # en attente de levée

        elif kind == "avance":
            espece = payload
            stag = det["stagnations"].get(zone)
            if stag and _geste_impute(det, zone, semaine, stag[0]):
                # §9.2 (1→2) : une intervention qui LÈVE une stagnation. Crédite
                # l'espèce (nature « stagnation ») + le concept lié à la cause.
                if espece:
                    crediter(espece, {"stagnation"})
                crediter(CONCEPT_PAR_STAGNATION[stag[1]], {"stagnation"})
                signaler_zone(zone, stag[0])                # geste imputé → poids fort (③)
                del det["stagnations"][zone]                # consommée (pas de re-crédit)

        elif kind == "repro":
            espece, tag = payload
            # §9.2 (2→3) / (3→4) : amener à reproduction grâce à une intervention
            # (geste imputable dans la fenêtre — typ. `favoriser_auxiliaire`). Le
            # croisement BIPARENTAL prouve la pollinisation (§9.3). Une repro AUTO
            # (autofécondation) sans geste reste émergente → rien.
            if espece and _geste_impute(det, zone, semaine, semaine - FENETRE_IMPUTATION):
                crediter(espece, {"reproduction", "optimisation"})
                if M.palier(game_state, player, espece) >= 3:
                    det["experte"].add(espece)              # composante (a) du §9.4
                if tag == "biparental":
                    crediter("pollinisation", {"reproduction"})
                signaler_zone(zone, semaine - FENETRE_IMPUTATION)   # geste imputé (③)

    # Naturalisation férale (§9.4(b)) + conjonction palier 5 : balayage de l'état
    # post-tick. Une recrue FÉRALE (zone non `replante`) qui s'établit (stade ≥
    # seuil) en PLEINE SANTÉ dans le sol façonné « est accueillie comme native ».
    for tile in game_state.get("tiles", []):
        for p in tile.plants:
            if not p.is_alive:
                continue
            zone = (tile.tile_id, *p.position)
            if zone in det["replante"]:
                continue                                     # planté → pas féral
            if p.current_stage >= STAGE_NATURALISATION and p.etat == "sain":
                cle = _CLE_DE_CLASSE.get(p.plant_class)
                if cle:
                    det["naturalise"].add(cle)
    # §9.4 : palier 4→5 = CONJONCTION action experte (a) ET naturalisation (b).
    for espece in det["experte"] & det["naturalise"]:
        crediter(espece, {"conjonction"})

    _elaguer(det, semaine)
    return credits
