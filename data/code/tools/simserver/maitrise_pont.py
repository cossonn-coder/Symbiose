"""
SYMBIOSE — tools/simserver/maitrise_pont.py
La CHAÎNE DE MAÎTRISE du pont (sprint UI voix narratives, tronçon ①).
Spec de référence : `docs/conception/CONCEPTION_VOIX_NARRATIVES_UI.md` §2.

Sans maîtrise, les quatre voix restent MUETTES (encyclopédie/magazine/carnet
interprétatif sont gatés par un palier ≥ 1 ou ≥ 3). Ce module BRANCHE la chaîne
qui les alimente, DEUX hooks appelés par le serveur APRÈS le tick :

  - `observer_apres_tick(gs, player, log)` — hook A (découverte) + hook B
    (`detecter`, crédit de palier) + la RÉVÉLATION d'une page au palier 3.
  - `noter_geste_pont(...)` — hook C (imputation), délégué tel quel à
    `maitrise_detection.noter_geste`, appelé depuis `cmd_action`.

GARDE-FOU DE COUCHE (identique aux autres modules `sim` de voix) : tout vit
AU-DESSUS du tick, dans le pont opt-in joueur. `engine`/`fields`/`plants` ne
l'importent JAMAIS ; le golden tourne le moteur SANS serveur → ces hooks ne sont
jamais appelés → golden intact. Aucun RNG : `observer`/`detecter`/`reveler_page`
sont déterministes (le robinet « récompense » ne tire aucun aléa).

Convention `semaine` (identique à `consigner`) : `gs["week"] - 1` (le tick a déjà
incrémenté la semaine ; le log qu'on lit appartient à la semaine écoulée).
"""
from __future__ import annotations

from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from sim.actions import observer
from sim import maitrise_detection as MD
from sim import pages
from sim.evenements import evenements

# Reverse mapping classe → clé de catalogue (objet → clé), DÉRIVÉ des catalogues
# moteur (jamais dupliqué) : sert à retrouver la clé d'espèce d'une plante vivante
# du monde post-tick pour la DÉCOUVRIR (hook A). Même construction que
# `maitrise_detection._CLE_DE_CLASSE`.
_CLE_DE_CLASSE = {cls: cle
                  for cle, cls in {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}.items()}

# Concept transversal DÉCOUVERT à la 1ʳᵉ observation d'une reproduction biparentale
# (§2, hook A) : voir un croisement à deux parents fait naître l'idée de
# pollinisation. Les stagnations sec/ombre/froid réutilisent le mapping canonique
# de `maitrise_detection` (source unique).
_CONCEPT_REPRO_BIPARENTAL = "pollinisation"

# Palier qui déclenche la révélation d'une page « récompense » (micro-décision B,
# §2) : atteindre la MAÎTRISE d'un objet (palier 3) libère une belle page de son
# concept. Seul robinet de ce sprint (hasard/fouille → D54).
PALIER_PAGE = 3


def observer_apres_tick(game_state: dict, player: str, log: list[str]) -> None:
    """Chaîne de maîtrise après un `step_week` (hooks A + B + révélation page).
    Appelée par `cmd_step_week` juste après le tick, sur le `log` de la semaine
    écoulée (AVANT `log.clear()`), pour le joueur courant. Lecture seule du monde
    et du log ; les seules écritures touchent l'état JOUEUR (maîtrise, Vigueur de
    découverte, set de pages) — jamais le cœur écolo (golden intact)."""
    semaine = game_state["week"] - 1
    _observer(game_state, player, log)                          # hook A (découverte)
    promos = MD.detecter(game_state, player, log, semaine)      # hook B (crédit palier)
    for objet, palier in promos:                                # révélation page (§2·B)
        if palier == PALIER_PAGE:
            pages.reveler_page(game_state, player, robinet="récompense",
                               contexte={"concept": objet})


def noter_geste_pont(game_state: dict, player: str, semaine: int, zone) -> None:
    """Hook C (imputation §2) : enregistre un geste joueur sur `zone=(tile_id,r,c)`
    dans la fenêtre d'imputation, pour que `detecter` (au prochain tick) crédite au
    joueur la levée d'une stagnation ou une reproduction provoquée. Délégué tel quel
    à la façade moteur — le pont ne réimplémente aucune règle."""
    MD.noter_geste(game_state, player, semaine, zone)


def _observer(game_state: dict, player: str, log: list[str]) -> None:
    """Hook A (découverte, §2). DEUX sources, chacune dédupliquée par
    l'idempotence d'`observer` (ré-observer un objet connu ne re-crédite rien) :

      - ESPÈCES : chaque espèce d'une plante VIVANTE du monde post-tick → débloque
        la fiche encyclopédie niveau 1.
      - CONCEPTS : à la 1ʳᵉ occurrence dans le log du tick — stagnation
        sec→eau / ombre→lumière / froid→météo (mapping canonique) ;
        reproduction biparentale → pollinisation."""
    # Espèces vivantes du monde post-tick.
    for tile in game_state.get("tiles", []):
        for p in tile.plants:
            if not p.is_alive:
                continue
            cle = _CLE_DE_CLASSE.get(p.plant_class)
            if cle:
                observer(game_state, player, cle)
    # Concepts lus dans le log de la semaine écoulée.
    for ev in evenements(log):
        if ev.kind == "stagnation":
            concept = MD.CONCEPT_PAR_STAGNATION.get(ev.cause)
            if concept:
                observer(game_state, player, concept)
        elif ev.kind == "reproduction" and ev.cause == "biparental":
            observer(game_state, player, _CONCEPT_REPRO_BIPARENTAL)
