"""
SYMBIOSE — sim/signes.py
La LÉGENDE DES SIGNES côté moteur narratif (sprint PLANTE ASSEMBLÉE ⑥).
Spec : `docs/rendu/pixelart/conception_plante_assemblee.md` §4.4.

Deux services, tous deux HORS TICK (niveau `sim`, au-dessus du moteur ;
`engine`/`fields`/`plants` ne l'importent JAMAIS) :

  1. `observer_signe` — le joueur SURVOLE une plante qui porte un signe visible :
     le pont écrit une note au ledger (`sim/journal.py`), comme un geste. JAMAIS le
     tick : si le moteur consignait les symptômes au snapshot, le journal dépendrait
     de la fréquence d'appel du snapshot → non-déterminisme (conception §4.4).
     Le carnet la lit ensuite sans autre changement (`CONCEPT_DE[("signe", cause)]`).
     N'accorde AUCUNE maîtrise : la note est un fait observé, pas une preuve.
  2. `appris` — ce que le joueur a APPRIS (signes, bêtes), en lecture pure, pour
     l'info-bulle à deux niveaux de la vue (⑦) et la fiche « signe » de
     l'encyclopédie. Même bascule que le carnet : `palier(concept) ≥ carnet._seuil`
     — la note se comprend, la fiche s'ouvre et l'info-bulle nomme la cause AU MÊME
     MOMENT. Une bête : palier de SA clé de maîtrise ≥ ce même seuil.
"""
from __future__ import annotations

from sim import maitrise
from sim import journal
from sim.carnet import _seuil
from sim.signes_corpus import SIGNES
from fields.faune_encyclo import FAUNE_ENCYCLO

# `kind` des notes de signe au ledger (clé du carnet `CONCEPT_DE[("signe", cause)]`).
KIND_SIGNE = "signe"

# Durée d'une saison en semaines : l'année de 52 semaines se découpe en 4 saisons
# de 13 (`sim/engine/calendrier.SAISONS` : 1-13, 14-26, 27-39, 40-52). Calcul local
# pour ne pas tirer le paquet `engine` depuis une voix narrative.
_SEMAINES_PAR_SAISON = 13


def _saison_absolue(semaine: int) -> int:
    """Indice de saison depuis le début du jardin (année × 4 + saison) : la clé de
    dédup « une note par (espèce, signe, saison) »."""
    return (semaine - 1) // _SEMAINES_PAR_SAISON


def observer_signe(game_state: dict, player: str, espece: str, signe: str,
                   zone: tuple, semaine: int) -> bool:
    """Consigne au ledger l'observation de `signe` sur `espece` (clé catalogue), en
    `zone=(tile_id, r, c)` (ou plus court). Dédup : une seule note par (espèce,
    signe, saison) et par joueur — relue dans le ledger lui-même (aucun état neuf).
    Signe hors corpus → refusé (aucune fausse note). Renvoie True ssi une note a
    été écrite. Écrit SEULEMENT la tranche journal du joueur."""
    if signe not in SIGNES:
        return False
    st = journal.ensure_player(game_state, player)
    saison = _saison_absolue(semaine)
    # Le ledger est chronologique : on remonte depuis la fin et on s'arrête dès
    # qu'on sort de la saison (lecture bornée, pas de balayage complet).
    for e in reversed(st["entries"]):
        if _saison_absolue(e["semaine"]) != saison:
            break
        if (e["kind"] == KIND_SIGNE and e["cause"] == signe
                and e["espece"] == espece):
            return False
    journal._appender(st, {"semaine": semaine, "zone": tuple(zone),
                           "kind": KIND_SIGNE, "cause": signe, "espece": espece})
    return True


def signe_appris(game_state: dict, player: str, signe: str) -> bool:
    """Un signe est appris quand le palier de SON concept atteint le seuil du carnet
    interprétatif (option « anticipé » comprise). Lecture pure."""
    concept = SIGNES[signe]["concept"]
    return maitrise.palier(game_state, player, concept) >= _seuil(game_state, player)


def faune_apprise(game_state: dict, player: str, espece: str) -> bool:
    """Une bête est apprise (nom révélé) quand le palier de sa clé de maîtrise
    atteint le seuil du carnet interprétatif. Lecture pure."""
    return maitrise.palier(game_state, player, espece) >= _seuil(game_state, player)


def appris(game_state: dict, player: str) -> dict:
    """Ce que le joueur a appris, pour la vue : `{"signes": [...], "faune": [...]}`
    dans l'ordre stable des corpus. LECTURE PURE (aucune clé créée) : sans couche
    maîtrise, deux listes vides."""
    return {
        "signes": [s for s in SIGNES if signe_appris(game_state, player, s)],
        "faune": [f for f in FAUNE_ENCYCLO if faune_apprise(game_state, player, f)],
    }
