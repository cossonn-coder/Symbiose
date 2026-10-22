"""
SYMBIOSE — sim/champignon_voix.py
Ce que le SURVOL d'un carpophore écrit dans les voix (sprint « le sol qui respire »
⑤, D111 §3.4). Corpus : `sim/champignon_encyclo.py` ; registre : `fields/fongique.py`.

Trois services, tous HORS TICK (niveau `sim`, appelés par le pont au survol ;
`engine`/`fields`/`plants` ne l'importent JAMAIS) :

  1. `noter_fructification` — la voix ÉVÉNEMENTS : le carpophore observé est consigné
     au ledger (`kind="fructification"`, `cause` = clé d'espèce), une fois par
     (espèce, saison). 📖 Pourquoi au SURVOL et pas au tick : les carpophores sont de
     la PERCEPTION échantillonnée au snapshot ; les consigner au snapshot ferait
     dépendre le journal de la fréquence d'appel (non-déterminisme) — même leçon que
     les signes (`sim/signes.observer_signe`).
  2. `crediter_concept` — le CARNET bascule en interprétatif au palier du concept de
     l'espèce (saprophytie, mycorhize, parasitisme, sosies). Ce concept se gagne en
     NOMMANT les champignons qui l'illustrent : découverte d'une espèce → concept
     découvert (palier 1) ; chaque espèce nommée → +1 palier (plafond `SEUIL_CARNET`).
     Au palier 3 la page secrète du concept se révèle (robinet « récompense »).
  3. `champignons_nommes` — pour l'info-bulle : nom ET comestibilité, SEULEMENT pour
     les espèces nommées (philo #6 : tant qu'on ne sait pas, manger est un pari).
"""
from __future__ import annotations

from fields.fongique import REGISTRE_FONGIQUE
from sim import journal, maitrise, pages
from sim.carnet import SEUIL_CARNET, _seuil
from sim.champignon_encyclo import FICHES_CHAMPIGNON

KIND_FRUCTIFICATION = "fructification"

# Même découpage que `sim/signes._saison_absolue` (saisons de 13 semaines).
_SEMAINES_PAR_SAISON = 13


def est_champignon(cle: str) -> bool:
    """Vrai si `cle` est une espèce du règne fongique (registre ③)."""
    return cle in REGISTRE_FONGIQUE


def noter_fructification(game_state: dict, player: str, cle: str, zone: tuple,
                         semaine: int) -> bool:
    """Consigne au ledger la fructification observée de `cle` en `zone`. Dédup : une
    note par (espèce, saison) et par joueur, relue dans le ledger (aucun état neuf).
    Renvoie True ssi une note a été écrite."""
    if not est_champignon(cle):
        return False
    st = journal.ensure_player(game_state, player)
    saison = (max(1, semaine) - 1) // _SEMAINES_PAR_SAISON
    for e in reversed(st["entries"]):       # ledger chronologique : lecture bornée
        if (max(1, e["semaine"]) - 1) // _SEMAINES_PAR_SAISON != saison:
            break
        if e["kind"] == KIND_FRUCTIFICATION and e["cause"] == cle:
            return False
    journal._appender(st, {"semaine": semaine, "zone": tuple(zone),
                           "kind": KIND_FRUCTIFICATION, "cause": cle, "espece": cle})
    return True


def crediter_concept(game_state: dict, player: str, cle: str, decouverte: bool,
                     palier_gagne: bool) -> int:
    """Crédit du CONCEPT de l'espèce `cle` après un survol (cf. docstring module).
    `decouverte` = ce survol a découvert l'espèce ; `palier_gagne` = il lui a fait
    gagner un palier (crédit saisonnier). Renvoie le palier du concept."""
    concept = FICHES_CHAMPIGNON[cle]["concept"]
    if decouverte:
        maitrise.decouvrir(game_state, player, concept)
    p = maitrise.palier(game_state, player, concept)
    nommee = maitrise.palier(game_state, player, cle) >= SEUIL_CARNET
    if palier_gagne and nommee and p < SEUIL_CARNET:
        st = maitrise.ensure_player_maitrise(game_state, player)
        manque = maitrise.preuves_requises(p) - st["objets"][concept]["preuves"]
        p = maitrise.enregistrer_preuve(game_state, player, concept, poids=manque)
        if p == SEUIL_CARNET:
            pages.reveler_page(game_state, player, robinet="récompense",
                               contexte={"concept": concept})
    return p


def champignons_nommes(game_state: dict, player: str) -> dict:
    """`{clé: {nom, comestibilite}}` des espèces NOMMÉES (palier ≥ seuil du carnet,
    option « anticipé » comprise — même règle que les bêtes), ordre du registre.
    LECTURE PURE ; sans couche maîtrise → `{}`."""
    seuil = _seuil(game_state, player)
    return {cle: {"nom": esp.nom,
                  "comestibilite": FICHES_CHAMPIGNON[cle]["comestibilite"]}
            for cle, esp in REGISTRE_FONGIQUE.items()
            if maitrise.palier(game_state, player, cle) >= seuil}
