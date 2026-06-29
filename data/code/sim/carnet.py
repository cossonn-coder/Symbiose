"""
SYMBIOSE — sim/carnet.py
Le CARNET AUTO — première des quatre voix narratives (sprint Voix narratives,
tronçon ③, dettes D14 + D43).
Spec de référence : `docs/conception/CONCEPTION_VOIX_NARRATIVES.md` §2.1 + §5.

Voix « je », à la première personne. Le carnet est un LECTEUR read-only du ledger
②  (`sim/journal.py`) : il ne consigne RIEN, n'avance aucun tick, n'utilise aucun
RNG. Pour chaque entrée du ledger il choisit un CONCEPT (table `CONCEPT_DE`, §5.0)
puis un REGISTRE :

  - DESCRIPTIF tant que le concept n'est pas maîtrisé (palier < SEUIL_CARNET) —
    « Le plant de tomate fait grise mine. »
  - INTERPRÉTATIF dès que le palier du CONCEPT atteint le seuil — « Encore la
    soif : ce sol draine trop vite, je le sais maintenant. »

Le registre se recalcule À LA CONSULTATION (révélation rétroactive, décision B du
doc §0) : une vieille note « se comprend » quand on finit par maîtriser sa cause.
Le palier lu est celui du CONCEPT de l'entrée (pas de l'espèce) — maîtriser
*l'eau* éclaire toutes les notes de soif, pas seulement celles d'une espèce.

GARDE-FOU DE COUCHE (identique à `journal.py` / `maitrise.py`) : `carnet` est au
niveau `sim`, AU-DESSUS du tick. **`engine`/`fields`/`plants` ne l'importent
JAMAIS.** Il lit `game_state["journal"]` (②) et `maitrise.palier` (D12). Pas de
joueur consigné → `carnet_lire` renvoie `[]` (no-op golden, jamais de crash).

CORPUS = LIVRABLE ÉDITORIAL (doc §5) : les tables ci-dessous sont de la DONNÉE
recopiée fidèlement du doc, pas de la logique. Ne pas réécrire les gabarits.
"""
from __future__ import annotations

from sim import maitrise

# --- Calibrage (PLACEHOLDER NOMMÉ, à régler post-test D12.4) ------------------
# Palier du CONCEPT à partir duquel la note bascule en interprétatif (décision B
# du doc §0). Le réglage d'aide « interprétatif anticipé » (Options, défaut NON,
# cf. CLAUDE.md) ramène ce seuil à 1 pour le joueur concerné — voir `_seuil`.
SEUIL_CARNET = 3
SEUIL_ANTICIPE = 1

# Concept de repli quand une paire (kind, cause) n'est pas tabulée (§5.0) : on ne
# crashe JAMAIS sur un événement inattendu (kickoff « Pièges »), on le range sous
# un concept neutre et on garde un gabarit générique (cf. _GABARIT_FALLBACK).
CONCEPT_FALLBACK = "observation"


# --- Table CONCEPT_DE[(kind, cause)] → concept (doc §5.0, VERBATIM) -----------
# Quel concept de maîtrise « gate » le registre de chaque entrée. Les causes de
# reproduction (auto/biparental/introgr.) mappent toutes vers `reproduction`,
# comme le doc l'écrit en une seule ligne ; la « levée (reprise) » est un cas
# spécial dont le concept EST sa cause (eau/lumière/météo) → traité par code dans
# `_concept_de` plutôt que par une entrée figée.
CONCEPT_DE: dict[tuple[str, str | None], str] = {
    ("germination", None):        "succession",
    ("stagnation", "sec"):        "eau",
    ("stagnation", "noyé"):       "eau",
    ("stagnation", "ombre"):      "lumière",
    ("stagnation", "froid"):      "météo",
    ("floraison", None):          "pollinisation",
    ("nouaison", None):           "pollinisation",
    ("reproduction", "auto"):        "reproduction",
    ("reproduction", "biparental"):  "reproduction",
    ("reproduction", "introgr."):    "reproduction",
    ("reproduction", None):          "reproduction",
    ("mort", "sénescence"):       "sénescence",
    ("mort", "asphyxie"):         "eau",
    ("mort", "gel"):              "météo",
    ("mort", "conflit"):          "compétition",
    ("ravageur", None):           "ravageurs",
    ("abscission", None):         "décomposition",
    ("acclimatation", None):      "adaptation",          # D43 (doc §5.1 dernière ligne)
}

# Concept de la « levée (reprise) » : doc §5.0 dit « = la cause (eau / lumière /
# météo) ». La reprise hérite donc du concept de ce qui la bloquait. On mappe la
# cause de reprise (sec/noyé → eau, ombre → lumière, froid → météo) ; cause None
# → succession (reprise spontanée).
_CONCEPT_LEVEE: dict[str | None, str] = {
    "sec": "eau", "noyé": "eau", "ombre": "lumière", "froid": "météo",
    None: "succession",
}


def _concept_de(kind: str, cause: str | None) -> str:
    """Concept qui gate le registre d'une entrée (§5.0). Cas spécial « levée » :
    son concept EST sa cause (la reprise se comprend quand on maîtrise ce qui
    bloquait). Toute paire inconnue → CONCEPT_FALLBACK (jamais de crash, kickoff
    « Pièges »)."""
    if kind == "levée":
        return _CONCEPT_LEVEE.get(cause, "succession")
    return CONCEPT_DE.get((kind, cause), CONCEPT_FALLBACK)


# --- Table GABARIT[(kind, cause, registre)] → texte (doc §5.1, VERBATIM) ------
# Voix interne 1ʳᵉ personne. Slots : {e} = espèce, {l} = lieu (dérivé de la zone),
# {s} = saison/semaine. Recopié des 2 colonnes du doc §5.1 (descriptif | interpré-
# tatif). La « levée (reprise) » porte la cause `=cause levée` dans le doc → on la
# tabule sous cause None (le gabarit ne dépend pas finement de la cause de reprise).
_D = "descriptif"
_I = "interprétatif"
GABARIT: dict[tuple[str, str | None, str], str] = {
    ("germination", None, _D): "Une pousse de {e} a levé {l}.",
    ("germination", None, _I): "{e} a germé {l} : chaleur et humidité réunies, le sol y était prêt.",

    ("stagnation", "sec", _D): "Le plant de {e} {l} fait grise mine, feuilles molles.",
    ("stagnation", "sec", _I): "Encore la soif {l} — ce sol draine trop vite pour {e}, je le sais maintenant.",
    ("stagnation", "noyé", _D): "{e} {l} a le pied dans l'eau, plus rien ne bouge.",
    ("stagnation", "noyé", _I): "Trop d'eau {l} : les racines de {e} étouffent, le sol ne ressuie pas.",
    ("stagnation", "ombre", _D): "{e} {l} s'étire, pâle, tiges filantes.",
    ("stagnation", "ombre", _I): "L'ombre {l} bride {e} — elle file chercher la lumière qu'on lui vole.",
    ("stagnation", "froid", _D): "{e} {l} est figée depuis le coup de froid.",
    ("stagnation", "froid", _I): "Le froid {l} a mis {e} en pause : sous son seuil, rien ne pousse.",

    ("levée", None, _D): "{e} {l}, longtemps à l'arrêt, est repartie.",
    ("levée", None, _I): "{e} {l} repart — j'ai levé ce qui la bloquait, et ça a payé.",

    ("floraison", None, _D): "{e} {l} s'est couverte de fleurs.",
    ("floraison", None, _I): "{e} fleurit {l} : la table est mise pour les butineurs, la nouaison se joue là.",
    ("nouaison", None, _D): "Des fruits se forment sur {e} {l}.",
    ("nouaison", None, _I): "Nouaison {l} — le pollen reçu a porté, le fruit grossira.",

    ("reproduction", None, _D): "{e} a essaimé alentour {l}.",
    ("reproduction", None, _I): "{e} se ressème {l} : la lignée se perpétue, le brassage a eu lieu.",

    ("mort", "sénescence", _D): "Le vieux pied de {e} {l} s'est éteint.",
    ("mort", "sénescence", _I): "{e} {l} a bouclé son cycle — la sénescence, pas un accident ; sa nécromasse nourrit déjà le sol.",
    ("mort", "asphyxie", _D): "{e} {l} a dépéri puis succombé.",
    ("mort", "asphyxie", _I): "Noyée {l} : l'excès d'eau prolongé a fini par tuer {e}.",
    ("mort", "gel", _D): "{e} {l} a été emportée par le gel.",
    ("mort", "gel", _I): "Le gel {l} a eu {e} — au-delà de sa rusticité, rien à faire.",
    ("mort", "conflit", _D): "{e} {l} a cédé la place à plus vigoureux.",
    ("mort", "conflit", _I): "Éclaircissage naturel {l} : {e} a perdu la course à la lumière et aux ressources.",

    ("ravageur", None, _D): "Des bestioles s'affairent sur {e} {l}.",
    ("ravageur", None, _I): "Pression de ravageurs {l} — si les auxiliaires sont là, l'équilibre se rétablit seul.",
    ("abscission", None, _D): "{e} {l} laisse tomber ses feuilles.",
    ("abscission", None, _I): "Abscission {l} : {e} se déleste avant l'hiver, sa litière amorce l'humus de l'an prochain.",

    ("acclimatation", None, _D): "Le feuillage de {e} {l} a pris un éclat cireux, glauque.",
    ("acclimatation", None, _I): "{e} {l} s'est acclimatée — et ses descendants naîtront pré-armés contre ce stress.",
}

# Gabarit générique quand la paire (kind, cause) n'a pas de texte dédié (§5.0 ne
# tabule pas tous les croisements possibles). Jamais un crash, jamais une chaîne
# vide — une note neutre mais lisible.
_GABARIT_FALLBACK = {
    _D: "Quelque chose s'est passé du côté de {e} {l}.",
    _I: "{e} {l} — un événement que je commence à comprendre.",
}

# Reproduction : les 3 causes (auto/biparental/introgr.) partagent le gabarit
# `reproduction None` ci-dessus → on neutralise la cause pour la clé de gabarit.
_KIND_CAUSE_NEUTRE = {"reproduction"}


# --- Lieu lisible dérivé de la zone (slot {l}) -------------------------------
def _lieu(zone: tuple) -> str:
    """Libellé de lieu (slot `{l}`) dérivé de la `zone` du ledger : `(tile_id, r,
    c)` ou `(tile_id,)`. On reste FACTUEL et stable (« sur T0 en (2,3) ») plutôt
    que de prétendre un « coin nord-est » qui supposerait de connaître la
    géométrie réelle de la tuile (hors périmètre ③). L'UI Godot (D24) pourra
    enjoliver ce libellé ; le carnet Python garde une zone non ambiguë."""
    if not zone:
        return "au jardin"
    tid = zone[0]
    if len(zone) >= 3:
        return f"sur {tid} en ({zone[1]},{zone[2]})"
    return f"sur {tid}"


# --- Sélection du registre ---------------------------------------------------
def _reglage_anticipe(game_state: dict, player: str) -> bool:
    """Flag du réglage d'aide « interprétatif anticipé » (Options, défaut NON, cf.
    CLAUDE.md). Quand il est ON, le carnet bascule en interprétatif dès le palier
    1 (`SEUIL_ANTICIPE`) — pour qui veut révéler les causes tôt, au prix de la
    méthode scientifique. Le menu Options n'est pas encore exposé en Python : on
    lit un flag OPTIONNEL `game_state["options"][player]["carnet_anticipe"]` posé
    par le driver, défaut False.
    # TODO(options): brancher le flag réel quand le menu Options sera implémenté."""
    opts = game_state.get("options", {})
    return bool(opts.get(player, {}).get("carnet_anticipe", False))


def _seuil(game_state: dict, player: str) -> int:
    """Seuil de bascule effectif pour ce joueur : SEUIL_CARNET, ou SEUIL_ANTICIPE
    si le réglage d'aide est actif."""
    return SEUIL_ANTICIPE if _reglage_anticipe(game_state, player) else SEUIL_CARNET


def _registre(game_state: dict, player: str, concept: str) -> str:
    """Registre d'une entrée selon le palier du CONCEPT (révélation rétroactive,
    décision B) : interprétatif dès que `palier(concept) ≥ seuil`, descriptif
    sinon. Lecture pure de `maitrise.palier` (ne crée aucune clé)."""
    if maitrise.palier(game_state, player, concept) >= _seuil(game_state, player):
        return _I
    return _D


def _texte(kind: str, cause: str | None, registre: str, espece: str | None,
           zone: tuple, semaine: int) -> str:
    """Texte final d'une entrée : gabarit `(kind, cause, registre)` avec ses slots
    remplis (`{e}`/`{l}`/`{s}`). La reproduction neutralise sa cause pour la clé.
    Paire absente du corpus → gabarit générique (jamais de crash, kickoff)."""
    cle_cause = None if kind in _KIND_CAUSE_NEUTRE else cause
    gabarit = GABARIT.get((kind, cle_cause, registre)) or _GABARIT_FALLBACK[registre]
    # Espèce absente (aléa sans plante : ravageur de saison) → libellé neutre.
    nom = espece if espece else "le couvert"
    return gabarit.format(e=nom, l=_lieu(zone), s=semaine)


# --- API publique ------------------------------------------------------------
def carnet_lire(game_state: dict, player: str, filtre: dict | None = None) -> list[dict]:
    """Renvoie le carnet FORMATÉ d'un joueur (doc §2.1) : une liste d'entrées
    `{semaine, zone, concept, registre, texte}`, dans l'ordre chronologique du
    ledger. PUR (lecture seule). Sans tranche `journal` pour ce joueur → `[]`
    (golden-safe). Le registre est recalculé MAINTENANT (révélation rétroactive).

    `filtre` optionnel (indexation §2.1), tout champ est ET-combiné :
      - `{"concept": "eau"}`     → seulement les notes du concept donné ;
      - `{"zone": (tid, r, c)}`  → seulement une zone ;
      - `{"saison": s}`          → seulement une semaine (slot {s})."""
    journal = game_state.get("journal")
    if not journal:
        return []
    st = journal.get(player)
    if not st:
        return []

    out: list[dict] = []
    for e in st["entries"]:
        concept = _concept_de(e["kind"], e["cause"])
        if not _passe_filtre(e, concept, filtre):
            continue
        registre = _registre(game_state, player, concept)
        out.append({
            "semaine": e["semaine"],
            "zone": e["zone"],
            "concept": concept,
            "registre": registre,
            "texte": _texte(e["kind"], e["cause"], registre,
                            e["espece"], e["zone"], e["semaine"]),
        })
    return out


def _passe_filtre(entree: dict, concept: str, filtre: dict | None) -> bool:
    """Indexation §2.1 : une entrée passe si elle satisfait TOUS les critères du
    `filtre` (concept / zone / saison). `filtre` None ou vide → tout passe."""
    if not filtre:
        return True
    if "concept" in filtre and concept != filtre["concept"]:
        return False
    if "zone" in filtre and entree["zone"] != filtre["zone"]:
        return False
    if "saison" in filtre and entree["semaine"] != filtre["saison"]:
        return False
    return True
