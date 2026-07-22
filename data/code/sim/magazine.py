"""
SYMBIOSE — sim/magazine.py
Le MAGAZINE DE BOTANIQUE — quatrième et dernière des voix narratives (sprint
Voix narratives, tronçon ⑥, dette D13) ET 4ᵉ canal d'acquisition d'espèces.
Spec de référence : `docs/narration/voix/conception_voix_narratives.md` §2.4 + §3
(table D12.2, décision C).

Rôle (doc §2.4) : introduire VOLONTAIREMENT une espèce, vs les 3 canaux subis
(succession spontanée, événements rares, friche). Ce N'EST PAS une monnaie : la
MAÎTRISE est la condition d'APPARITION (palier 3 d'un membre de famille → les
sœurs s'offrent), la VIGUEUR est le COÛT d'OBTENTION (un acte rare et décisif).

Deux fonctions, event-driven HORS TICK :
  - `magazine_offres(gs, player, saison)` — LECTURE pure : sœurs offertes.
  - `acheter_au_magazine(gs, player, espece)` — ÉCRITURE bornée à l'état JOUEUR
    (Vigueur + banque de graines), JAMAIS au cœur écolo.

GARDE-FOU DE COUCHE (identique à `carnet`/`encyclopedie`/`vigueur`/`maitrise`) :
`magazine` est au niveau `sim`, AU-DESSUS du tick. **`engine`/`fields`/`plants`
ne l'importent JAMAIS.** Aucun RNG. Pas de joueur / pas de maîtrise palier 3 →
offre `[]` ; achat hors offre ou fonds insuffisants → `False` SANS effet. Le
golden tourne le moteur SANS joueur → aucune offre, aucun achat → no-op strict.

DÉCISION C FIGÉE (doc §3, table D12.2) : les sœurs s'ouvrent dès qu'UN membre de
la famille atteint le **palier 3** (réutilise le spillover famille déjà codé). Le
magazine lit le palier d'UN membre de la famille (pas de l'espèce offerte, qui
est par définition encore inconnue du joueur).
"""
from __future__ import annotations

from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from sim import maitrise, vigueur
from sim.encyclopedie import NIVEAU_MAX
from sim.encyclopedie_corpus import FICHES
from sim.seeds import Seed

# --- Calibrage (placeholder D12.4, knob en tête de module) -------------------
# COUT_MAGAZINE : Vigueur débitée à l'achat. Proposé ÉLEVÉ et PONCTUEL (doc §2.4)
# — introduire une espèce est un acte rare et décisif, pas une dépense courante.
# Valeur à calibrer post-test (D12.4) ; choisie ici au-dessus du MAX_BASE (100)
# pour rappeler qu'un achat suppose un plafond de Vigueur déjà gonflé par la
# maîtrise (palier_bonus) — on n'achète pas au magazine sans avoir progressé.
COUT_MAGAZINE = 120.0

# Seuil d'ouverture des sœurs (décision C, doc §3) : palier 3 = « maîtrise ».
SEUIL_MAGAZINE = 3

# Niveau de la FICHE PRODUIT que le magazine affiche d'une sœur offerte (doc §2.1
# « la fiche de niveau ≥ 2 est ce que le magazine affiche… le joueur lit avant
# d'acheter »). C'est de la donnée éditoriale du PRODUIT (argument de vente), pas
# la fiche du joueur sur l'espèce — la sœur est par définition encore au palier 0,
# `encyclopedie_lire` renverrait `None`. On sert donc le corpus tronqué au niveau 2
# directement (N1 silhouette + N2 biologie), borné à NIVEAU_MAX (réutilise §6).
NIVEAU_FICHE_PRODUIT = min(2, NIVEAU_MAX)

# Catalogue MAÎTRE des espèces (cultivées + adventices nommées + pérennes) — la
# source des « sœurs » candidates. Identique au pool que `maitrise.famille_de`
# sait classer par famille (les deux dérivent des mêmes catalogues moteur).
_CATALOGUE_MAITRE: dict[str, type] = {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}


def _banque(game_state: dict):
    """Banque de graines du joueur (`PlayerSeedBank`), stockée sous la clé
    `player_seed_bank` du `game_state` (cf. `main.py`/`tools/simserver`). Peut être
    absente (golden sans joueur, contexte de test minimal) → `None`. Lecture pure.

    NB : une seule banque par `game_state` (elle SUIT l'avatar, cf. `seeds.py`) —
    le `player` ne sert qu'à la maîtrise/Vigueur ; la banque est l'inventaire du
    joueur courant de ce terrain."""
    return game_state.get("player_seed_bank")


def _familles_maitrisees(game_state: dict, player: str) -> set[str]:
    """Familles botaniques dont AU MOINS UN membre du catalogue maître est au
    palier ≥ SEUIL_MAGAZINE pour ce joueur (décision C). Lecture pure de
    `maitrise.palier` — ne crée AUCUNE clé (no-op golden). Sans couche maîtrise →
    ensemble vide."""
    familles: set[str] = set()
    for espece, cls in _CATALOGUE_MAITRE.items():
        if maitrise.palier(game_state, player, espece) >= SEUIL_MAGAZINE:
            familles.add(cls.family)
    return familles


def magazine_offres(game_state: dict, player: str, saison: str | None = None) -> list[str]:
    """Espèces SŒURS offertes au magazine pour ce joueur (doc §2.4, décision C).

    Une espèce `S` est offerte ssi :
      1. sa FAMILLE compte déjà un membre AU PALIER ≥ 3 (maîtrise → ouverture) ;
      2. `S` n'est PAS encore dans la banque de graines du joueur (sinon ce serait
         déjà acquis — on n'offre que ce qui manque, « catalogue maître moins banque
         joueur ») ;
      3. `S` n'est PAS le membre déjà maîtrisé lui-même au sens où, s'il est déjà en
         banque, le point 2 l'exclut ; un membre maîtrisé mais ABSENT de la banque
         redevient légitimement offrable (cas limite assumé : on a appris l'espèce
         sur le terrain sans jamais en ranger la graine).

    Tri STABLE = ordre du catalogue maître (déterminisme, pas de RNG).

    FILTRE SAISON — TODO(catalogue) : le doc §2.4 prévoit un « numéro saisonnier »
    qui ne propose que les espèces DE SAISON (filtre par fenêtre de semis de
    l'espèce). MAIS le catalogue moteur ne porte AUCUNE fenêtre de semis à ce jour
    (vérifié : pas d'attribut `sow_season`/`sowing_window` sur les classes de
    `plants/`). Conformément au kickoff (« si l'info n'existe pas → TODO nommé, ne
    pas inventer ») et au garde-fou « ne pas fabriquer un calendrier », le paramètre
    `saison` est ACCEPTÉ pour figer la signature du doc mais reste INACTIF tant que
    le catalogue ne porte pas la donnée. À brancher quand une fenêtre de semis
    existera côté `plants/` (filtrer ici les sœurs hors-saison).

    Sans palier 3 sur aucune famille → liste VIDE. PUR (aucune écriture, aucun RNG).
    """
    familles = _familles_maitrisees(game_state, player)
    if not familles:
        return []
    banque = _banque(game_state)
    offres: list[str] = []
    for espece, cls in _CATALOGUE_MAITRE.items():
        if cls.family not in familles:
            continue
        if banque is not None and banque.count(espece) > 0:
            continue                          # déjà en banque → pas une offre
        offres.append(espece)
    return offres


def acheter_au_magazine(game_state: dict, player: str, espece: str,
                        saison: str | None = None) -> bool:
    """Achète une espèce sœur : gate offre → dépense Vigueur → dépose le lot en
    banque (doc §2.4). Renvoie `True` ssi l'achat a eu lieu, `False` SANS aucun
    effet sinon. Event-driven HORS TICK (appelé par le driver/UI, jamais le tick).

    Séquence (ordre important pour ne JAMAIS débiter sans livrer) :
      1. GATE STRICT — `espece` doit être dans `magazine_offres(...)` au moment de
         l'achat (on RE-VÉRIFIE, on ne fait pas confiance à l'appelant, kickoff
         « Pièges »). Hors offre → `False`, rien débité.
      2. BANQUE PRÊTE — il faut une `PlayerSeedBank` pour déposer le lot ; absente
         → `False`, rien débité (on ne brûle pas de Vigueur sans destination).
      3. VIGUEUR — `vigueur.spend(COUT_MAGAZINE)` renvoie le RATIO d'effort : 1.0
         ssi le coût est ENTIÈREMENT payé. Fonds insuffisants → ratio < 1.0 ; on
         ANNULE (on ne livre pas un achat à moitié payé). NB : `spend` draine
         `min(cost, courante)` même en échec — c'est le coût « tenté » de l'acte
         (cohérent avec la sémantique de `sim/actions.py`).
      4. LIVRAISON — `bank.add(Seed(species=espece))` → un lot d'une graine NEUTRE
         de l'espèce (génétique de base : un produit « catalogue », pas un cultivar
         sélectionné). `True`.

    PUR côté écolo : touche UNIQUEMENT l'état JOUEUR (`vigueur`, `player_seed_bank`),
    jamais les champs ni le tick. Aucun RNG."""
    if espece not in magazine_offres(game_state, player, saison):
        return False                          # gate : hors offre, aucun effet
    banque = _banque(game_state)
    if banque is None:
        return False                          # pas de destination → on ne débite pas
    if vigueur.spend(game_state, player, COUT_MAGAZINE) < 1.0:
        return False                          # fonds insuffisants → achat annulé
    banque.add(Seed(species=espece))
    return True


def magazine_fiche(espece: str) -> dict | None:
    """Fiche PRODUIT que le magazine affiche d'une espèce offerte (doc §2.1, couplage
    encyclopédie : « le joueur lit avant d'acheter »). Réutilise le CORPUS de ④
    (`FICHES`, §6) — pas de second corpus — tronqué au niveau de présentation
    NIVEAU_FICHE_PRODUIT (N1 silhouette + N2 biologie). C'est l'argument de vente
    de l'éditeur, INDÉPENDANT du palier du joueur sur cette sœur (encore inconnue,
    donc `encyclopedie_lire` renverrait `None`).

    Même STRUCTURE que `encyclopedie_lire` (réutilisable par l'UI Godot D24).
    Espèce hors corpus → `None` (jamais de KeyError). PUR : lecture de donnée."""
    fiche = FICHES.get(espece)
    if fiche is None:
        return None
    niveaux = {n: fiche[n] for n in range(1, NIVEAU_FICHE_PRODUIT + 1)}
    return {"espece": espece, "niveau_max": NIVEAU_FICHE_PRODUIT, "niveaux": niveaux}
