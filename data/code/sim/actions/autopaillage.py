"""
SYMBIOSE — sim/actions/autopaillage.py
Couplage PLANTER + PAILLER par MAÎTRISE (sprint équilibre invasion ⑦, D12).

« On paille systématiquement quand on plante, une fois qu'on maîtrise. » Au-dessus
d'un palier de maîtrise de l'ESPÈCE plantée, le geste `planter` (`gestes.py`)
auto-paille le plot ; la NATURE du mulch dépend de la plante (arbre ligneux → BRF,
plante à paille → sa nature propre, potagère → paille). Ce module isole la SEULE
responsabilité « décider si/quoi auto-pailler » — `planter` l'appelle, il n'écrit
lui-même AUCUN champ.

GARDE-FOU golden (philo #3/#4) : la maîtrise vit AU-DESSUS du tick déterministe
(`sim/maitrise.py` §6). Le golden écologique est une succession spontanée SANS
joueur → aucune clé `maitrise` → `M.palier(...) == 0 < SEUIL_AUTOPAILLAGE` → jamais
d'auto-paillage → `planter` inchangé. Zéro RNG (décision pure de l'état maîtrise).

Décision de tarif (kickoff ⑦, tranchée ici) : l'auto-paillage CONSOMME le stock de
mulch comme un `pailler` normal (pas de mulch magique — respect de ④) mais NE
facture AUCUNE Vigueur supplémentaire : chez le jardinier qui maîtrise, le paillage
est un RÉFLEXE fondu dans le geste de plantation (pas un second geste à payer). Sans
stock de la bonne nature, on plante SANS mulch (aucune friction) — la maîtrise ne
crée pas de matière ex nihilo.
"""
from __future__ import annotations

from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from sim import maitrise as M
from fields.ecofields import PAILLAGE_DOSE
from .paillage import stock_disponible, prelever_stock

# Palier de maîtrise de l'espèce À PARTIR duquel `planter` auto-paille (§6). Choisi à
# 3 = « maîtrise » (découverte 1 → investissement 2 → MAÎTRISE 3 → expertise 4 →
# transcendant 5, cf. CLAUDE.md) : le réflexe de paillage naît quand on MAÎTRISE la
# plante, pas dès qu'on l'a juste découverte. PLACEHOLDER NOMMÉ — calibrage D12.4.
SEUIL_AUTOPAILLAGE = 3

# Nature de mulch par défaut d'une potagère/annuelle (la plus commune au potager).
_NATURE_POTAGERE = "paille"


def nature_autopaillage(species: str) -> str:
    """Nature du mulch qu'un jardinier posera d'instinct en plantant `species`
    (§6, « la nature dépend de la plante »), DÉRIVÉE du catalogue (jamais une liste
    figée) :
      • l'espèce déclare une `mulch_source` (blé/chanvre → "paille", sapin →
        "aiguilles", ⑤) → on l'honore (c'est SA matière) ;
      • sinon un arbre LIGNEUX (présent dans `PERENNIAL_CATALOGUE`) → "brf" (on
        paille un arbre au bois raméal fragmenté) ;
      • sinon une potagère/annuelle → "paille".
    Point d'accès unique du mapping — `planter` s'en sert pour choisir le stock à
    prélever et la nature inscrite au plot."""
    cls = {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}.get(species)
    source = getattr(cls, "mulch_source", None)
    if source is not None:
        return source
    if species in PERENNIAL_CATALOGUE:
        return "brf"
    return _NATURE_POTAGERE


def auto_pailler(game_state: dict, player: str, eco, species: str,
                 r: int, c: int) -> str | None:
    """Auto-paille le plot `(r, c)` à la plantation SI (et seulement si) le palier de
    maîtrise de `species` ≥ `SEUIL_AUTOPAILLAGE` ET le stock de la nature idoine
    couvre `PAILLAGE_DOSE`. Appelé par `planter` APRÈS le dépôt réussi de la graine.

    Consomme le stock (patron `pailler`) et pose le mulch (`eco.poser_mulch`) — mais
    NE facture PAS de Vigueur (réflexe combiné, cf. en-tête). Aucun effet direct sur
    le vivant : le mulch amende le CHAMP `paillage`, ses effets émergent au tick
    (philo #2). Zéro RNG.

    Renvoie la nature posée (str) si auto-paillage effectué, sinon `None` (palier
    insuffisant OU stock vide → on a planté sans mulch, aucune friction)."""
    if M.palier(game_state, player, species) < SEUIL_AUTOPAILLAGE:
        return None                              # pas encore maîtrisé → plantation nue
    nature = nature_autopaillage(species)
    if not stock_disponible(game_state, nature, PAILLAGE_DOSE):
        return None                              # pas de matière → pas de mulch magique (④)
    prelever_stock(game_state, nature, PAILLAGE_DOSE)
    eco.poser_mulch(r, c, nature, PAILLAGE_DOSE)
    return nature
