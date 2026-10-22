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
  3. `crediter_saison` (INFO-BULLE DU VIVANT ①, D110 a·b) — le NOM d'une bête ou d'un
     champignon (par espèce depuis le sol qui respire ⑤) se mérite en la regardant au fil des saisons : chaque survol dans une
     saison NEUVE crédite +1 palier, jusqu'à `SEUIL_CARNET` (3 saisons distinctes →
     nommée). Jamais les plantes (leur maîtrise passe par la détection D12).
"""
from __future__ import annotations

from sim import maitrise
from sim import journal
from sim.vision import palier_lu   # vision (⑥) : info-bulle complète le temps de l'effet
from sim.carnet import _seuil, SEUIL_CARNET
from sim.signes_corpus import SIGNES
from fields.faune_encyclo import FAUNE_ENCYCLO
from fields.fongique import REGISTRE_FONGIQUE
from sim.champignon_voix import champignons_nommes

# `kind` des notes de signe au ledger (clé du carnet `CONCEPT_DE[("signe", cause)]`).
KIND_SIGNE = "signe"

# Durée d'une saison en semaines : l'année de 52 semaines se découpe en 4 saisons
# de 13 (`sim/engine/calendrier.SAISONS` : 1-13, 14-26, 27-39, 40-52). Calcul local
# pour ne pas tirer le paquet `engine` depuis une voix narrative.
_SEMAINES_PAR_SAISON = 13

# Clé privée de la tranche joueur de maîtrise (même convention que `_detection` de
# `maitrise_detection`) : `{clé: dernière saison absolue créditée}`. Dict str → int
# → JSON-sérialisable tel quel. `maitrise.py` l'ignore (il ne lit que `objets`).
_CLE_SAISONS = "_saisons_vues"


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
    return palier_lu(game_state, player, concept) >= _seuil(game_state, player)


def faune_apprise(game_state: dict, player: str, espece: str) -> bool:
    """Une bête est apprise (nom révélé) quand le palier de sa clé de maîtrise
    atteint le seuil du carnet interprétatif. Lecture pure."""
    return palier_lu(game_state, player, espece) >= _seuil(game_state, player)


def appris(game_state: dict, player: str) -> dict:
    """Ce que le joueur a appris, pour la vue : `{"signes": [...], "faune": [...],
    "champignons": {...}}` dans l'ordre stable des corpus. La liste `faune` porte
    aussi les espèces de champignons nommées (en dernier, ordre du registre) : même
    règle de nom que les bêtes, une seule liste à tester côté vue. `champignons`
    (sol qui respire ⑤) = `{clé: {nom, comestibilite}}` des seules espèces nommées —
    la comestibilité n'existe pour la vue qu'une fois le nom mérité. LECTURE PURE
    (aucune clé créée) : sans couche maîtrise, listes et dict vides."""
    vivants = [*FAUNE_ENCYCLO, *REGISTRE_FONGIQUE]
    return {
        "signes": [s for s in SIGNES if signe_appris(game_state, player, s)],
        "faune": [f for f in vivants if faune_apprise(game_state, player, f)],
        "champignons": champignons_nommes(game_state, player),
    }


def crediter_saison(game_state: dict, player: str, cle: str, semaine: int,
                    decouverte: bool) -> bool:
    """Crédit par OBSERVATION SAISONNIÈRE d'une bête ou du champignon (`cle` déjà
    résolue par le pont ; l'appelant garantit que ce n'est pas une plante). À
    appeler APRÈS la découverte du survol (`decouverte` = ce survol vient de la
    faire) :
      - découverte → la saison courante est mémorisée (le 1er survol EST la 1ʳᵉ
        saison, palier 1) ; clé déjà connue sans mémoire (état antérieur au sprint)
        → idem, sans crédit (prudence : on ignore quand elle a été vue) ;
      - saison STRICTEMENT postérieure à la dernière créditée ET palier <
        `SEUIL_CARNET` → exactement +1 palier (preuve = ce qui manque au palier
        courant), puis la saison est mémorisée. Sinon rien.
    Déterministe, hors tick (geste joueur). Renvoie True ssi un palier a été gagné.
    Effet de bord assumé : Σ paliers ↑ → `palier_bonus` (Vigueur max) ↑ un peu."""
    st = maitrise.ensure_player_maitrise(game_state, player)
    vues = st.setdefault(_CLE_SAISONS, {})
    # Semaine 0 (survol avant le 1er tick) = même saison que la semaine 1 : pas de
    # palier « gratuit » entre l'init et le premier pas.
    saison = _saison_absolue(max(1, semaine))
    derniere = vues.get(cle)
    if decouverte or derniere is None:
        vues[cle] = saison
        return False
    p = maitrise.palier(game_state, player, cle)
    if saison <= derniere or p >= SEUIL_CARNET:
        return False
    manque = maitrise.preuves_requises(p) - st["objets"][cle]["preuves"]
    maitrise.enregistrer_preuve(game_state, player, cle, poids=manque)
    vues[cle] = saison
    return True
