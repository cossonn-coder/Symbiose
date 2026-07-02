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
from fields.faune_encyclo import FAUNE_ENCYCLO
from sim.champignon_encyclo import CLE_CHAMPIGNON
from sim.actions import observer, OBJETS_TOUCHES
from sim import maitrise as M
from sim import maitrise_detection as MD
from sim import pages
from sim.evenements import evenements

# Reverse mapping classe → clé de catalogue (objet → clé), DÉRIVÉ des catalogues
# moteur (jamais dupliqué) : sert à retrouver la clé d'espèce d'une plante du monde
# (survol, ou balayage debug). Même construction que
# `maitrise_detection._CLE_DE_CLASSE`.
_CLE_DE_CLASSE = {cls: cle
                  for cle, cls in {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}.items()}

# Nom de CLASSE (str) → clé de catalogue. Le snapshot sérialise l'espèce d'une
# plante en `cls.__name__` (serialize.py) ; le C# renvoie donc ce nom au survol.
# La résolution nom → clé vit ICI (Python source de vérité, « Godot bête ») :
# le C# ne connaît jamais les clés catalogue.
_CLE_DE_NOM = {cls.__name__: cle
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

# Poids des preuves de progression geste/outil/technique (D60 ③, §3.4) —
# PLACEHOLDERS NOMMÉS, *calibrage D12.4*. Deux robinets :
#   - USAGE répété : chaque utilisation RÉUSSIE d'un geste crédite une preuve LÉGÈRE
#     (< 1) sur le geste + ses outils + sa technique — le savoir-faire s'affine par
#     la pratique, mais lentement (beaucoup d'usages pour un palier) ;
#   - SUCCÈS écologique imputé (`detecter`) : preuve FORTE (≥ 1) sur le geste — une
#     amélioration écologique attribuée au geste vaut bien plus qu'un simple usage.
PREUVE_USAGE_LEGER = 0.34   # usage réussi (léger, < 1)
PREUVE_SUCCES_FORT = 1.0    # succès écologique imputé (fort, ≥ 1)


def observer_apres_tick(game_state: dict, player: str, log: list[str]) -> None:
    """Chaîne de maîtrise après un `step_week` (hooks A + B + révélation page).
    Appelée par `cmd_step_week` juste après le tick, sur le `log` de la semaine
    écoulée (AVANT `log.clear()`), pour le joueur courant. Lecture seule du monde
    et du log ; les seules écritures touchent l'état JOUEUR (maîtrise, Vigueur de
    découverte, set de pages) — jamais le cœur écolo (golden intact)."""
    semaine = game_state["week"] - 1
    _observer(game_state, player, log)                          # hook A (découverte)
    zones_creditees: list = []                                  # ③ volet succès
    promos = MD.detecter(game_state, player, log, semaine,      # hook B (crédit palier)
                         zones_creditees=zones_creditees)
    for objet, palier in promos:                                # révélation page (§2·B)
        if palier == PALIER_PAGE:
            pages.reveler_page(game_state, player, robinet="récompense",
                               contexte={"concept": objet})
    _crediter_succes_gestes(game_state, player, semaine, zones_creditees)  # ③ volet 2


def _objets_du_geste(verb: str) -> list[str]:
    """Les objets de maîtrise d'un geste (D60 ③) : le VERBE lui-même (le geste) ∪ ses
    TECHNIQUE/OUTILS statiques (`OBJETS_TOUCHES`, classés en onglets par `type_de` au
    ⑥). PAS la cible vivante — elle a sa propre voie via `detecter` (pas de double
    comptage, kickoff §« Ce qu'il NE faut PAS faire »). Lecture pure d'une table."""
    return [verb, *OBJETS_TOUCHES.get(verb, ())]


def decouvrir_a_usage(game_state: dict, player: str, verb: str) -> None:
    """Canal de découverte NEUF (Q3) : à la 1ʳᵉ utilisation RÉUSSIE d'un geste, DÉCOUVRE
    (palier 0→1) le geste + sa technique + ses outils. Un geste ne se survole pas — on
    l'apprend en l'employant. `observer` est idempotent (ré-usage ne re-découvre rien)
    ; il crédite au passage le petit gain de Vigueur de découverte (§4.3), comme le
    survol d'une espèce. Appelé par `cmd_action` quand `result.applied`."""
    for objet in _objets_du_geste(verb):
        observer(game_state, player, objet)


def crediter_usage(game_state: dict, player: str, verb: str) -> None:
    """Volet 1 (§3.4) : chaque utilisation RÉUSSIE crédite une preuve LÉGÈRE sur le
    geste + ses outils + sa technique, MAIS seulement sur les objets DÉJÀ découverts
    (palier ≥ 1). Comme `decouvrir_a_usage` tourne juste avant dans `cmd_action`, ils
    le sont tous dès le 1ᵉ usage — le gate évite néanmoins de créditer un objet qu'on
    n'aurait pas encore observé (cohérence avec le gate d'observation de la détection).
    Ne crédite JAMAIS la cible vivante (double comptage). Poids `PREUVE_USAGE_LEGER`."""
    for objet in _objets_du_geste(verb):
        if M.palier(game_state, player, objet) >= 1:
            M.enregistrer_preuve(game_state, player, objet, poids=PREUVE_USAGE_LEGER)


def _crediter_succes_gestes(game_state: dict, player: str, semaine: int,
                            zones_creditees: list) -> None:
    """Volet 2 (§3.4) : quand `detecter` a imputé une amélioration écologique à un
    geste (levée de stagnation / reproduction provoquée), crédite ce GESTE d'une preuve
    FORTE (`PREUVE_SUCCES_FORT`). `detecter` a signalé les `(zone, depuis)` créditées ;
    on retrouve le(s) verbe(s) posé(s) sur ces zones dans la fenêtre (`verbes_imputables`)
    et on les crédite. Le geste doit être découvert (crédit ⇒ pas d'auto-découverte
    intempestive ; en pratique il l'est via `decouvrir_a_usage`). Idempotence naturelle :
    une zone consommée par `detecter` n'est plus re-signalée."""
    for zone, depuis in zones_creditees:
        for verb in MD.verbes_imputables(game_state, player, zone, semaine, depuis):
            if M.palier(game_state, player, verb) >= 1:
                M.enregistrer_preuve(game_state, player, verb, poids=PREUVE_SUCCES_FORT)


def noter_geste_pont(game_state: dict, player: str, semaine: int, zone,
                     verb: str | None = None) -> None:
    """Hook C (imputation §2) : enregistre un geste joueur sur `zone=(tile_id,r,c)`
    dans la fenêtre d'imputation, pour que `detecter` (au prochain tick) crédite au
    joueur la levée d'une stagnation ou une reproduction provoquée. Délégué tel quel
    à la façade moteur — le pont ne réimplémente aucune règle. `verb` (D60 ③,
    optionnel) est mémorisé pour créditer le GESTE lui-même en poids fort au succès."""
    MD.noter_geste(game_state, player, semaine, zone, verb=verb)


def observer_espece(game_state: dict, player: str, nom: str) -> bool:
    """Hook A par SURVOL (retour F5 Nico), MULTI-RÈGNES (D60 ②). Une entité n'est
    observée que quand le joueur PASSE LA SOURIS dessus (voir son nom) — pas parce
    qu'elle vit dans le jardin. On résout `nom` en clé de maîtrise puis on DÉCOUVRE
    (idempotent : ré-observer ne re-crédite rien). Résolution par règne, dans un
    ordre déterministe :

      1. NOM DE CLASSE de plante (`_CLE_DE_NOM`, `cls.__name__` du snapshot) → clé
         catalogue (inchangé : le survol PLANTE envoie le nom de classe) ;
      2. CLÉ ANIMALE connue (`FAUNE_ENCYCLO`) → cette clé telle quelle. La vie macro
         (`MacroLife`/`ForagerLayer`) connaît déjà les clés d'espèce (`puceron`,
         `abeille`…) et les envoie directement — pas de reverse-map (kickoff ②) ;
      3. CLÉ CHAMPIGNON générique (`CLE_CHAMPIGNON` = `"champignon"`, survol d'un
         carpophore) → cette clé ;
      4. sinon `None` → no-op (nom inconnu : aucune fausse découverte).

    Renvoie True ssi nouvelle découverte."""
    cle = _CLE_DE_NOM.get(nom)
    if cle is None and (nom in FAUNE_ENCYCLO or nom == CLE_CHAMPIGNON):
        cle = nom
    if cle is None:
        return False
    return observer(game_state, player, cle)


def _observer(game_state: dict, player: str, log: list[str]) -> None:
    """Hook A — volet CONCEPTS (les ESPÈCES passent désormais par le SURVOL,
    `observer_espece`, retour F5 : voir une plante ≠ l'observer). Découvre les
    concepts transversaux lus dans le log du tick, à leur 1ʳᵉ occurrence
    (idempotence d'`observer`) : stagnation sec→eau / ombre→lumière / froid→météo
    (mapping canonique) ; reproduction biparentale → pollinisation."""
    for ev in evenements(log):
        if ev.kind == "stagnation":
            concept = MD.CONCEPT_PAR_STAGNATION.get(ev.cause)
            if concept:
                observer(game_state, player, concept)
        elif ev.kind == "reproduction" and ev.cause == "biparental":
            observer(game_state, player, _CONCEPT_REPRO_BIPARENTAL)
