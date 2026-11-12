"""
SYMBIOSE — sim/quetes.py
Le SYSTÈME DE QUÊTES côté JOUEUR (D79, tronçon ①).
Spec de référence : `docs/joueur/automate/conception_quetes.md`.

Une quête est un DÉSIR posé par une voix (une lettre), et une LECTURE passive de
l'état du monde pour savoir s'il est comblé — jamais un ordre, jamais un pilote
(conception §1). La quête OBSERVE, elle ne pousse aucune plante (philo #1/#2).

DISTINCT DU HARNAIS AUTOMATE (F1) : `tools/jardinier_auto/objectifs.py` est le
cœur objectif de l'AUTOMATE (branché derrière `automate on`, ignoré par les gestes
du joueur humain). D79 est un module MOTEUR joueur NEUF : il PARTAGE la forme de
données `(geste, quantite, cible)` mais possède son propre état (sauvegardé) et
son propre point de comptage — un HOOK sur le dispatch des gestes joueur, pas la
boucle automate. Le code est indépendant (aucun import croisé).

GARDE-FOU DE COUCHE : `quetes` est au niveau `sim`, jamais importé par `engine` /
`fields` / `plants`. Il n'importe que `plants.catalogue` (résolution des cibles),
comme `objectifs.py`. OPT-IN STRICT : `game_state["quetes"]` n'existe qu'après un
`ajouter_quete()`. Le golden écologique tourne SANS joueur ni quête → aucune clé
→ `notifier_geste()` est un no-op total → **golden intact**.

FAMILLES DE CONDITIONS (conception §4, mini-catalogue déclaratif FERMÉ) :
  - ① `("recolte_cumulee", geste, quantite, cible)` — comptée par HOOK geste.
  - ② `("hauteur_min", cible, metres)` / `("floraison_min", cible, n)` /
    `("nombre_vivant_min", cible, n)` — lues sur le SNAPSHOT hors tick, à la
    demande (passage de saison / ouverture du panneau), JAMAIS dans le tick moteur
    → golden intact. Aucun hook : un balayage borné `tiles → plants`.
L'aiguillage se fait sur le TAG (1er élément de la condition) : le hook geste ne
sert QUE `recolte_cumulee` ; `evaluer_etat()` ne sert QUE les tags d'état (registre
`_EVALUATEURS_ETAT`). Les deux familles cohabitent sans se marcher dessus.

État (miroir du pattern `objectifs.py`, philo #3 — la progression vit HORS du
frozen) :
    game_state["quetes"][id] = {
        "quete": Quete, "progression": int,
        "semaine_debut": int, "semaine_fin": int|None,  # None tant qu'active
    }
Le dict garde l'ordre d'insertion (add piloté par l'appelant) ; toute LISTE
produite est triée par `id` (déterminisme).
"""
from __future__ import annotations
from dataclasses import dataclass

from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from sim import maitrise, pages, vigueur
from sim.seeds import Seed

CLE_QUETES = "quetes"

# Plafond de quêtes ACTIVES simultanées (garde-fou #6, conception §4) : tant que
# le plafond est plein, aucune nouvelle lettre n'arrive — ce qui tue l'effet
# « checklist » et préserve l'apprentissage diffus. Les quêtes ACCOMPLIES
# (`semaine_fin` posé) ne comptent PAS (le plafond borne le présent, pas l'histoire).
PLAFOND_QUETES_ACTIVES = 6


@dataclass(frozen=True)
class Quete:
    """Une quête posée par une lettre (voix épistolaire, conception §7). Frozen :
    une quête est une CONSTANTE de contenu ; sa PROGRESSION vit à part dans
    `game_state` (philo #3). Champs :
      - `id` : identifiant stable et unique (clé d'état + tri déterministe) ;
      - `donneur` : prénom qui signe la lettre (« Marcel »), pas un PNJ (V1) ;
      - `condition` : tuple déclaratif `(tag, ...)` — pour ① le seul tag actif est
        `"recolte_cumulee"` : `("recolte_cumulee", geste, quantite, cible)` ;
      - `recompense` : POSÉ ici, traité aux tronçons ③/④ (opaque pour ①) ;
      - `declencheur` : condition d'OUVERTURE (③) — `None` (d'emblée),
        `("palier", objet, seuil)` ou `("saison", semaine_min)` ;
      - `texte_lettre` : corps épistolaire (③, V1), affiché par le panneau ⑤.
    `recompense`/`declencheur` sont typés `object` (catalogue déclaratif ouvert,
    V3) : ① ne les interprète pas, il les transporte ; ③ les traite."""

    id: str
    donneur: str
    condition: tuple
    recompense: object = None
    declencheur: object = None
    texte_lettre: str = ""      # corps épistolaire (V1) ; vide pour les quêtes de test


def _catalogue() -> dict:
    """Fusion des catalogues d'espèces nommées (cultivées + pérennes). Une cible de
    condition est une CLÉ de ce dict ; la valeur est la `plant_class` à comparer."""
    return {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}


def _classe_cible(cible: str):
    """La `plant_class` correspondant à une clé d'espèce, ou None si la clé est
    inconnue du catalogue (→ cible inatteignable, gérée au tronçon ③)."""
    return _catalogue().get(cible)


def _etat(game_state: dict) -> dict:
    """Le registre de quêtes dans `game_state` (créé à la volée, opt-in strict :
    aucune clé tant qu'aucune quête n'a été ajoutée → golden intact)."""
    return game_state.setdefault(CLE_QUETES, {})


# --- API d'écriture ----------------------------------------------------------
def ajouter_quete(game_state: dict, quete: Quete) -> None:
    """Pose une quête (arrivée d'une lettre). `semaine_debut` = semaine courante lue
    dans `game_state`. Idempotent sur l'`id` : un ré-ajout écrase le record (repart
    de zéro). C'est le SEUL geste d'opt-in : avant lui, `game_state` n'a pas de clé
    `quetes` et `notifier_geste` est un no-op strict."""
    _etat(game_state)[quete.id] = {
        "quete": quete,
        "progression": 0,
        "semaine_debut": game_state.get("week", 0),
        "semaine_fin": None,
    }


# --- API de lecture ----------------------------------------------------------
def quetes_actives(game_state: dict) -> list:
    """Les `Quete` encore actives (non accomplies), triées par `id` (déterminisme)."""
    reg = game_state.get(CLE_QUETES, {})
    return [reg[qid]["quete"] for qid in sorted(reg)
            if reg[qid]["semaine_fin"] is None]


def progression(game_state: dict, quete_id: str) -> int:
    """Compteur courant d'une quête (0 si inconnue)."""
    rec = game_state.get(CLE_QUETES, {}).get(quete_id)
    return rec["progression"] if rec else 0


def est_accomplie(game_state: dict, quete_id: str) -> bool:
    """Vrai si la quête est comblée (fenêtre close). La progression vit hors du
    `Quete` frozen → on prend `game_state`, pas la quête."""
    rec = game_state.get(CLE_QUETES, {}).get(quete_id)
    return bool(rec) and rec["semaine_fin"] is not None


# --- Matching d'une condition cumulée ---------------------------------------
def _sert_recolte_cumulee(condition: tuple, verbe: str, plant) -> bool:
    """Ce geste (`verbe` sur `plant`) fait-il avancer une condition
    `("recolte_cumulee", geste, quantite, cible)` ? Vrai ssi le verbe est le geste
    visé ET l'espèce de `plant` est la cible. Miroir de `objectifs.sert`."""
    _tag, geste, _quantite, cible = condition
    if geste != verbe:
        return False
    cls = _classe_cible(cible)
    return cls is not None and getattr(plant, "plant_class", None) is cls


# --- Le HOOK : comptage sur le geste joueur (F2) -----------------------------
def notifier_geste(game_state: dict, player: str, verbe: str, plant) -> None:
    """HOOK appelé APRÈS un geste JOUEUR RÉUSSI (depuis le dispatch du pont,
    `tools/simserver/plante_route.py`). Pour chaque quête `recolte_cumulee` ACTIVE
    servie par ce geste : +1 sur la progression ; à l'atteinte de la `quantite`, la
    quête se CLÔT (`semaine_fin`) et un événement est ÉMIS au ledger (`_consigner`).

    Comptage par hook, PAS par re-parse du ledger (F2). No-op strict si aucune quête
    (opt-in) → golden intact. `player` est accepté pour la symétrie avec les hooks
    joueur (`detecter`/`tick_player_vigueur`) et l'évolution multi-avatar ; l'état
    des quêtes est mono-joueur pour l'instant (comme `objectifs.py`), non indexé par
    `player`. Itère les `id` TRIÉS (déterminisme, philo #3)."""
    reg = game_state.get(CLE_QUETES)
    if not reg:
        return
    for qid in sorted(reg):
        rec = reg[qid]
        if rec["semaine_fin"] is not None:
            continue
        cond = rec["quete"].condition
        if cond[0] != "recolte_cumulee":
            continue                       # ② branchera ses tags ici
        if not _sert_recolte_cumulee(cond, verbe, plant):
            continue
        rec["progression"] += 1
        if rec["progression"] >= cond[2]:
            rec["semaine_fin"] = game_state.get("week", 0)
            _consigner_accomplissement(game_state, rec["quete"])


def _decrire_condition(condition: tuple) -> str:
    """Description COURTE et factuelle d'une condition (pour le ledger ✉ ; le chiffre
    exact y est admis — le ledger est un canal technique, pas le HUD primaire). Route
    par tag ; couvre les deux familles (① cumulée + ② état). La forme `recolte_cumulee`
    est identique au ① (aucune régression de message)."""
    tag = condition[0]
    if tag == "recolte_cumulee":
        _t, geste, quantite, cible = condition
        return f"{geste} ×{quantite} {cible}"
    if tag == "hauteur_min":
        _t, cible, metres = condition
        return f"{cible} ≥ {metres} m"
    if tag == "floraison_min":
        _t, cible, n = condition
        return f"{cible} en fleur ×{n}"
    if tag == "nombre_vivant_min":
        _t, cible, n = condition
        return f"{cible} vivant ×{n}"
    return tag


def _consigner_accomplissement(game_state: dict, quete: Quete) -> None:
    """Émet une ligne de log PARSABLE à l'accomplissement (conception §6) — le
    canal EXISTANT `game_state["log"]`, consigné au ledger des voix au tick suivant
    (`journal.consigner`, qui vide le log). Une entrée carnet « j'ai porté … au
    voisin » pourra en NAÎTRE (câblage du parseur : tronçon ③, non fait ici — une
    ligne non reconnue est ignorée sans dommage). Marqueur ✉ (lettre), style des
    autres marqueurs du tick. Sans clé `log` (hors serveur) → no-op silencieux."""
    log = game_state.get("log")
    if log is None:
        return
    log.append(f"✉ Quête accomplie ({quete.donneur}) : "
               f"{_decrire_condition(quete.condition)}")


# --- ② Conditions d'ÉTAT : lecture du snapshot vivant, hors tick ------------
# Seuil de « pleine floraison ». CANONIQUE = `sim/engine/floraison.py` /
# `decompo.py::SEUIL_FLEURI` (0.5) ET la vue C# qui dessine une fleur à
# `floraison ≥ 0.5` — une seule vérité. Redéfini LOCALEMENT (valeur, pas import) :
# `quetes` est couche `sim`, sous `engine` (règle de couches `sim ← engine` : on ne
# remonte jamais vers engine), et c'est le patron déjà en place dans les mixins
# d'engine (cf. le commentaire de `engine/carnivore.py`).
SEUIL_FLEURI = 0.5

# Phrases DIÉGÉTIQUES (V2, conception §3) : progression en langage vivant, JAMAIS un
# chiffre (le chiffre exact reste au mode debug, exposé à part au ⑤). Quatre bandes
# par type : <1/3, <2/3, <1, accompli (≥1).
_PHRASE_CIBLE_ABSENTE = "cette plante n'a pas encore trouvé sa place au jardin"
_PHRASE_ACCOMPLIE = "c'est fait, la lettre peut repartir"
_BANDES_HAUTEUR = ("à peine sorti de terre", "il prend de la hauteur",
                   "presque à hauteur voulue", "ça y est, il a la stature demandée")
_BANDES_FLORAISON = ("pas une fleur encore", "la floraison s'éveille",
                     "ça y est presque, ça fleurit de partout", "un vrai tapis de fleurs")
_BANDES_NOMBRE = ("il en manque encore beaucoup", "la petite troupe s'étoffe",
                  "presque le compte", "les voilà en nombre")
_BANDES_RECOLTE = ("le panier est encore vide", "de quoi grappiller",
                   "de quoi remplir un cageot", "la cagette est pleine")


def _phrase(ratio: float, bandes: tuple) -> str:
    """Mappe un ratio d'avancement (≥ 0) sur une des 4 bandes diégétiques. Seuils
    fixes 1/3, 2/3, 1 (déterministe, aucun chiffre restitué à l'appelant)."""
    if ratio >= 1.0:
        return bandes[3]
    if ratio >= 2.0 / 3.0:
        return bandes[2]
    if ratio >= 1.0 / 3.0:
        return bandes[1]
    return bandes[0]


def _plantes_vivantes(game_state: dict, cls):
    """Itère les plantes VIVANTES de l'espèce `cls` sur le snapshot (`tiles → plants`),
    hors tick. Balayage borné (K conditions × N plantes), aucun O(N²). Robuste aux
    faux game_state (pas de clé `tiles`) → itère du vide."""
    for tile in game_state.get("tiles", ()):
        for plant in getattr(tile, "plants", ()):
            if getattr(plant, "is_alive", False) and plant.plant_class is cls:
                yield plant


def _eval_hauteur_min(condition: tuple, game_state: dict):
    """`("hauteur_min", cible, metres)` : accomplie ssi une plante vivante de l'espèce
    atteint la hauteur. Lecture via `PlantInstance.current_height` (cm) — le prédicat
    EXISTANT (ne recalcule rien)."""
    _tag, cible, metres = condition
    cls = _classe_cible(cible)
    if cls is None:
        return False, _PHRASE_CIBLE_ABSENTE
    seuil_cm = metres * 100.0
    plus_haut = max((p.current_height for p in _plantes_vivantes(game_state, cls)),
                    default=0.0)
    ratio = plus_haut / seuil_cm if seuil_cm > 0 else 1.0
    return plus_haut >= seuil_cm, _phrase(ratio, _BANDES_HAUTEUR)


def _eval_floraison_min(condition: tuple, game_state: dict):
    """`("floraison_min", cible, n)` : accomplie ssi ≥ n plantes vivantes de l'espèce
    sont EN FLEUR — état floral `p.floraison ≥ SEUIL_FLEURI`, même prédicat que
    l'engine/la vue (ne recalcule aucune phénologie)."""
    _tag, cible, n = condition
    cls = _classe_cible(cible)
    if cls is None:
        return False, _PHRASE_CIBLE_ABSENTE
    fleuris = sum(1 for p in _plantes_vivantes(game_state, cls)
                  if getattr(p, "floraison", 0.0) >= SEUIL_FLEURI)
    ratio = fleuris / n if n > 0 else 1.0
    return fleuris >= n, _phrase(ratio, _BANDES_FLORAISON)


def _eval_nombre_vivant_min(condition: tuple, game_state: dict):
    """`("nombre_vivant_min", cible, n)` : accomplie ssi ≥ n plants vivants de
    l'espèce coexistent sur le terrain."""
    _tag, cible, n = condition
    cls = _classe_cible(cible)
    if cls is None:
        return False, _PHRASE_CIBLE_ABSENTE
    vivants = sum(1 for _ in _plantes_vivantes(game_state, cls))
    ratio = vivants / n if n > 0 else 1.0
    return vivants >= n, _phrase(ratio, _BANDES_NOMBRE)


_EVALUATEURS_ETAT = {
    "hauteur_min": _eval_hauteur_min,
    "floraison_min": _eval_floraison_min,
    "nombre_vivant_min": _eval_nombre_vivant_min,
}


def evaluer_etat(game_state: dict) -> None:
    """Balaye les quêtes d'ÉTAT actives et CLÔT celles comblées sur le snapshot
    courant. À appeler HORS tick (passage de saison, ouverture du panneau courrier) —
    jamais dans la boucle moteur → golden intact. Chaque clôture : `semaine_fin` +
    événement ✉ au ledger (comme le hook cumulé). Les tags `recolte_cumulee` sont
    IGNORÉS ici (ils vivent sur le hook geste). No-op strict sans quête (opt-in).
    Itère les id TRIÉS (déterminisme, philo #3)."""
    reg = game_state.get(CLE_QUETES)
    if not reg:
        return
    for qid in sorted(reg):
        rec = reg[qid]
        if rec["semaine_fin"] is not None:
            continue
        evalr = _EVALUATEURS_ETAT.get(rec["quete"].condition[0])
        if evalr is None:
            continue                       # recolte_cumulee → hook geste, pas ici
        accomplie, _ = evalr(rec["quete"].condition, game_state)
        if accomplie:
            rec["semaine_fin"] = game_state.get("week", 0)
            _consigner_accomplissement(game_state, rec["quete"])


def avancement(game_state: dict, quete_id: str) -> str:
    """Phrase DIÉGÉTIQUE (V2) de l'avancement d'une quête, pour le panneau courrier
    (⑤). Accomplie → phrase de clôture ; sinon route par tag : condition d'état →
    évaluée sur le snapshot, `recolte_cumulee` → tirée du compteur/hook. Quête inconnue
    → chaîne vide. Read-only (n'écrit rien, ne clôt rien : c'est `evaluer_etat` qui
    clôt)."""
    rec = game_state.get(CLE_QUETES, {}).get(quete_id)
    if rec is None:
        return ""
    if rec["semaine_fin"] is not None:
        return _PHRASE_ACCOMPLIE
    cond = rec["quete"].condition
    evalr = _EVALUATEURS_ETAT.get(cond[0])
    if evalr is not None:
        return evalr(cond, game_state)[1]
    ratio = rec["progression"] / cond[2] if cond[2] > 0 else 1.0   # recolte_cumulee
    return _phrase(ratio, _BANDES_RECOLTE)


# --- ③ Atteignabilité : une lettre peut rêver d'une espèce absente -----------
def _cible_de_condition(condition: tuple) -> str:
    """La CIBLE (clé d'espèce) portée par une condition. Position selon la famille :
    `recolte_cumulee` la porte en index 3, les conditions d'état en index 1."""
    return condition[3] if condition[0] == "recolte_cumulee" else condition[1]


def est_atteignable(condition: tuple) -> bool:
    """Vrai ssi l'espèce visée existe au catalogue. Une lettre qui rêve du « kiwi »
    (grimpante absente, D26/F3) est INATTEIGNABLE : elle reste ouverte sans jamais
    s'accomplir (#4 — pas d'échec), et le panneau ⑤ peut le signaler diégétiquement.
    Read-only, aucun effet."""
    return _classe_cible(_cible_de_condition(condition)) is not None


# --- ③ Déclenchement déterministe (palier maîtrise / jalon saison, zéro RNG) --
def _declencheur_satisfait(game_state: dict, player: str, declencheur) -> bool:
    """La condition d'OUVERTURE d'une lettre est-elle remplie ? DÉTERMINISTE, aucun
    `random` (philo #3) :
      - `None` → toujours (la lettre arrive d'emblée) ;
      - `("palier", objet, seuil)` → `maitrise.palier(...) >= seuil` (D12.2) ;
      - `("saison", semaine_min)` → semaine courante `>= semaine_min`.
    Un déclencheur inconnu reste muet (`False`) — jamais d'ouverture par défaut."""
    if declencheur is None:
        return True
    tag = declencheur[0]
    if tag == "palier":
        _t, objet, seuil = declencheur
        return maitrise.palier(game_state, player, objet) >= seuil
    if tag == "saison":
        _t, semaine_min = declencheur
        return game_state.get("week", 0) >= semaine_min
    return False


def evaluer_declencheurs(game_state: dict, player: str) -> list:
    """Ouvre les lettres du CORPUS dont le déclencheur est satisfait, dans la limite
    du PLAFOND de quêtes actives (#6). À appeler HORS tick (passage de saison) —
    jamais dans la boucle moteur. DÉTERMINISTE : parcours des `id` TRIÉS, arrêt net
    dès le plafond atteint (les lettres restantes attendent leur tour → file stable).
    Une lettre déjà posée (active OU accomplie) n'est JAMAIS reposée. Renvoie les
    ids ouverts (ordre d'ouverture). No-op pour le golden (jamais appelé sans joueur).

    Import LOCAL du corpus (`quetes_corpus` importe `Quete` d'ici → dépendance
    inverse résolue à l'appel, pas au chargement)."""
    from sim.quetes_corpus import QUETES_CORPUS
    reg = game_state.get(CLE_QUETES, {})
    actives = sum(1 for r in reg.values() if r["semaine_fin"] is None)
    ouverts: list = []
    for qid in sorted(QUETES_CORPUS):
        if actives + len(ouverts) >= PLAFOND_QUETES_ACTIVES:
            break                              # plafond plein → plus rien n'arrive
        if qid in reg:
            continue                           # déjà posée (active ou accomplie)
        if _declencheur_satisfait(game_state, player, QUETES_CORPUS[qid].declencheur):
            ajouter_quete(game_state, QUETES_CORPUS[qid])
            ouverts.append(qid)
    return ouverts


# --- ③ Récompenses SIMPLES à l'accomplissement (V3) --------------------------
def _appliquer_recompense(game_state: dict, player: str, recompense) -> None:
    """Verse UNE récompense (V3) — appelée à l'accomplissement, hors tick. Deux classes :
    SIMPLES (état JOUEUR via les API EXISTANTES : banque de graines, pages, Vigueur D11,
    maîtrise D12, technique enseignée) et MATÉRIELLES rares (④ : `vivace`/`structure` → un ACTEUR neuf apparaît
    dans le monde). Aucun buff plante (#2) : on ne dope aucune plante en terre — on crédite
    le joueur OU on fait naître un cadeau. `None` = plaisir pur → no-op. Un contexte minimal
    (banque/monde absents) fait échouer silencieusement le canal concerné (pas de destination)."""
    if recompense is None:
        return
    tag = recompense[0]
    if tag == "graine":
        banque = game_state.get("player_seed_bank")
        if banque is not None:
            banque.add(Seed(species=recompense[1]))
    elif tag == "vigueur":
        vigueur.gain(game_state, player, recompense[1])
    elif tag == "maitrise":
        _t, objet, poids = recompense
        maitrise.enregistrer_preuve(game_state, player, objet, poids)
    elif tag == "page":
        pages.reveler_page(game_state, player, "fouille")
    elif tag == "vivace":                         # ④ récompense MATÉRIELLE rare
        _offrir_vivace(game_state, recompense[1], recompense[2])
    elif tag == "structure":                      # ④ récompense MATÉRIELLE rare
        _offrir_structure(game_state, recompense[1], player)
    elif tag == "technique":                      # le courrier ENSEIGNE (accès aux gestes ②)
        _enseigner(game_state, player, *recompense[1:])


# --- Le courrier ENSEIGNE (sprint ACCÈS AUX GESTES ②, conception
# `docs/joueur/gestes/conception_refonte_palette.md` §3.3) ----------------------
# Une lettre dont le désir est comblé peut transmettre un SAVOIR-FAIRE. C'est l'une
# des quatre portes des techniques (`PORTES_TECHNIQUE`, `sim/actions/deblocage.py`),
# la seule qui passe par un voisin. Toujours de l'état JOUEUR, jamais une plante (#2).
def _reevaluer_gestes(game_state: dict, player: str) -> None:
    """Fait relire les portes et les gestes après une récompense, et range les gestes
    NOUVELLEMENT ouverts là où le pont les ramasse pour sa notification
    (`gestes_debloques_recents`, vidé au snapshot suivant). On FUSIONNE avec ce que
    le hook de maîtrise a pu y poser la même semaine, au lieu de l'écraser.

    Import LOCAL : `sim.actions` est un gros paquet qui n'a pas à être chargé pour
    lire une lettre, et on garde ainsi `quetes` importable sans lui (même précaution
    que les imports locaux d'`_offrir_vivace`)."""
    from sim.actions.deblocage import evaluer_deblocages
    nouveaux = evaluer_deblocages(game_state, player)
    if nouveaux:
        recents = game_state.setdefault("gestes_debloques_recents", {})
        recents[player] = sorted(set(recents.get(player, ())) | set(nouveaux))


def _enseigner(game_state: dict, player: str, technique: str,
               marqueur: str | None = None) -> None:
    """Récompense `("technique", objet)` ou `("technique", objet, marqueur)`.

    Deux formes, une seule logique en aval (la réévaluation des portes) :
      - SANS marqueur : la lettre suffit. La technique est découverte ici (palier 1),
        et ses gestes d'entrée s'ouvrent à la réévaluation.
      - AVEC marqueur : la lettre pose un événement au ledger du joueur
        (`lettre_greffe`, `lettre_essaim`) et c'est la PORTE de la technique qui
        décide. Pour l'essaim la lettre suffit, la technique est découverte aussitôt.
        Pour la greffe la porte exige AUSSI le greffoir : découvrir la technique ici
        ouvrirait `greffer` sans l'outil, ce que la conception refuse (§3.2)."""
    if marqueur is None:
        maitrise.decouvrir(game_state, player, technique)
    else:
        from sim.actions.deblocage import marquer_evenement
        marquer_evenement(game_state, player, marqueur)
    _reevaluer_gestes(game_state, player)


# --- ④ Récompenses MATÉRIELLES rares (V3) : un ACTEUR neuf apparaît, jamais un
# buff. On ne touche AUCUNE plante en terre (#2) — on FAIT NAÎTRE un cadeau (une
# pérenne instanciée à un âge avancé, une structure posée), comme le voisin qui
# offre son vieux pommier. Réservées à quelques belles lettres.
def _tuile_cadeau(game_state: dict):
    """La tuile-destination d'un cadeau matériel : la PREMIÈRE par `tile_id`
    (déterministe, philo #3). Renvoie None hors d'un vrai monde (contexte de test
    minimal sans `tiles`) → le cadeau retombe silencieusement (comme le canal
    `graine` sans banque). Placement au plot (0,0) — règle simple et stable."""
    tiles = game_state.get("tiles")
    if not tiles:
        return None
    return min(tiles, key=lambda t: t.tile_id)


def _offrir_vivace(game_state: dict, espece: str, annees: float) -> None:
    """Offre une pérenne LIGNEUSE déjà enracinée depuis `annees` (cadeau matériel).
    On ne forge PAS un état incohérent (#2, kickoff §Ne PAS faire) : on instancie une
    `PlantInstance` NEUVE puis on la FAIT POUSSER par le vrai chemin de croissance
    (`grow_plant`, growth_factor plein soleil = la sonde de calibration des arbres) sur
    `annees × 52` ticks — le moteur voit une plante VALIDE, avec sa structure de segments
    tabulée à son âge, exactement « comme si elle avait poussé ». DÉTERMINISTE : `form_seed`
    (identité morphologique) est amorcé par `form_seed_at` sur la seed globale, zéro RNG.
    Silencieux si l'espèce n'est pas une pérenne du catalogue ou hors d'un vrai monde."""
    cls = PERENNIAL_CATALOGUE.get(espece)
    tile = _tuile_cadeau(game_state)
    if cls is None or tile is None:
        return
    from plants.base import PlantInstance          # imports LOCAUX (rare, évite tout cycle de chargement)
    from sim.growth.phases import grow_plant
    from fields import form_seed_at
    seed = game_state.get("seed", 0)
    plant = PlantInstance(plant_class=cls, position=(0, 0))
    plant.form_seed = form_seed_at(seed, plant.x_cm, plant.y_cm,
                                   game_state.get("week", 0))
    for w in range(int(round(annees * 52))):       # croissance réelle, tick à tick
        grow_plant(plant, seed, w)                 # light_field=None → apex droit (plein soleil)
    plant.age_years = float(annees)                # âge cohérent avec la structure poussée
    tile.plants.append(plant)


def _offrir_structure(game_state: dict, kind: str, player: str | None = None) -> None:
    """Pose une structure permanente `kind` (un `bac` à compost) en cadeau — un ACTEUR
    posé, pas un buff. On ajoute la `Structure` à `eco.structures` EXACTEMENT comme le
    fait `poser_bac` après paiement, MAIS sans facturer de Vigueur : un cadeau est GRATUIT
    (appeler `poser_bac` prélèverait la Vigueur du joueur — absurde pour un présent). On
    respecte l'unicité par tuile (au plus un bac, comme `poser_bac`) : si la tuile en porte
    déjà un, le cadeau retombe silencieusement. Silencieux hors d'un vrai monde.

    POSSÉDER VAUT AVOIR POSÉ (accès aux gestes ②, conception §3.1) : le bac offert
    consigne pour `player` le même marqueur d'action que le geste de pose
    (`poser_bac`). Sans cela le cadeau restait inutilisable : `composter`, `retourner`
    et `epandre` attendent `("action", "poser_bac")`. Le marqueur n'est posé que si la
    structure l'a réellement été, et seulement pour un verbe que les tables lisent."""
    tile = _tuile_cadeau(game_state)
    ecos = game_state.get("eco")
    if tile is None or not ecos:
        return
    eco = ecos.get(tile.tile_id)
    if eco is None:
        return
    from fields.ecofields import Structure
    from sim.actions.compost import structure_de_tuile
    if structure_de_tuile(eco, kind) is not None:
        return                                     # déjà une structure de ce type (unicité tuile)
    eco.structures.append(Structure(kind=kind, plot=(0, 0)))
    from sim.actions.deblocage import DECLENCHEURS, marquer_action
    verbe_pose = f"poser_{kind}"
    if player is not None and verbe_pose in DECLENCHEURS:
        marquer_action(game_state, player, verbe_pose)
        _reevaluer_gestes(game_state, player)


# --- ⑤ Vue read-only : alimentation du panneau « courrier » ------------------
def etat_courrier(game_state: dict, debug: bool = False) -> list:
    """VUE read-only des lettres pour le panneau courrier Godot (⑤). ÉVALUE d'abord
    les quêtes d'état sur le snapshot courant (`evaluer_etat`, hors tick — l'ouverture
    du panneau est un point d'évaluation légitime, conception §4) puis renvoie TOUTES
    les lettres posées (actives ET accomplies), triées par `id` (déterminisme, philo
    #3), chacune : `id`, `donneur`, `texte_lettre`, `avancement` (phrase DIÉGÉTIQUE
    V2), `accomplie` (→ la vue coche la lettre), `atteignable` (→ la vue signale un
    rêve hors catalogue, F3). Le CHIFFRE exact (`progression` + `condition` brute) n'est
    joint QUE si `debug` (V2/#5 : jamais de chiffre en primaire). No-op → liste vide sans
    quête (opt-in). Ne verse AUCUNE récompense (c'est le driver `remettre_recompenses`
    au passage de semaine qui honore)."""
    evaluer_etat(game_state)
    reg = game_state.get(CLE_QUETES, {})
    lettres = []
    for qid in sorted(reg):
        quete = reg[qid]["quete"]
        item = {
            "id": qid,
            "donneur": quete.donneur,
            "texte_lettre": quete.texte_lettre,
            "avancement": avancement(game_state, qid),
            "accomplie": est_accomplie(game_state, qid),
            "atteignable": est_atteignable(quete.condition),
        }
        if debug:                                  # chiffre exact réservé au debug (#5)
            item["progression"] = progression(game_state, qid)
            item["condition"] = _decrire_condition(quete.condition)
        lettres.append(item)
    return lettres


def remettre_recompenses(game_state: dict, player: str) -> list:
    """Verse les récompenses des quêtes ACCOMPLIES pas encore honorées. À appeler
    HORS tick (passage de saison / ouverture du panneau), APRÈS `notifier_geste` /
    `evaluer_etat` qui clôturent. IDEMPOTENT : un drapeau `recompense_versee` empêche
    tout double versement (appels répétés inoffensifs). DÉTERMINISTE (ids triés).
    Renvoie les ids honorés. No-op strict sans quête (opt-in) → golden intact."""
    reg = game_state.get(CLE_QUETES)
    if not reg:
        return []
    honorees: list = []
    for qid in sorted(reg):
        rec = reg[qid]
        if rec["semaine_fin"] is None or rec.get("recompense_versee"):
            continue
        _appliquer_recompense(game_state, player, rec["quete"].recompense)
        rec["recompense_versee"] = True
        honorees.append(qid)
    return honorees
