"""
SYMBIOSE — sim/actions/ruche.py
Gestes apicoles du joueur (arc pollinisation ⑥, CONCEPTION §H/§I — couche joueur).

Deux gestes, modelés sur la famille décompo ⑤ et sur la récolte :
  - `poser_ruche` : pose une structure `ruche` VIDE (planification, coût MODÉRÉ,
    binaire comme `poser_bac`). Une ruche vide CAPTURE un essaim sauvage au tick
    (`fields/apiculture.tick_ruches`) seulement si le champ `abeille` local est
    suffisant — il faut d'abord soigner le milieu (philo #1 : pas d'abeilles dans la
    nature → ruche vide).
  - `recolter_miel` : transfère la réserve `miel` → **Vigueur joueur** (canal récolte,
    comme cueillir un fruit, §I.2). GATÉ par un ÉQUIPEMENT apicole qui n'est pas
    fabriqué mais DÉBLOQUÉ PAR MAÎTRISE (§I.3, relie l'arc à D12) : sans le palier de
    maîtrise requis, la récolte est partielle (et déclenchera l'alarme/la piqûre §J au
    tronçon ⑦ — hook posé ici, pénalité émergente, pas de malus forfaitaire).

Le miel récolté → Vigueur, jamais bonus direct sur une plante (philo #2). La
production de miel et la capture d'essaim sont du MOTEUR (`tick_ruches`) ; ce module
ne fait qu'orchestrer la pose et la récolte côté joueur.
"""
from __future__ import annotations

from sim.vigueur import spend, gain
from sim import maitrise as M               # gate équipement = palier de maîtrise (D12)
from fields.ecofields import Structure       # structure posable (⑤) — kind="ruche" (⑥)
from fields.alarme import declencher_alarme, ALARME_DEPOT   # phéromone d'alarme apienne (⑦ §J)
from .couts import cout_action, OBJETS_TOUCHES

# Gate de l'équipement apicole (§I.3) : il APPARAÎT comme capacité au palier de
# maîtrise du concept pollinisation (réutilise le concept transversal existant, crédité
# par le croisement bipartental §9.3 → récolter le miel sans se faire piquer est une
# RÉCOMPENSE de compréhension, pas un achat). Palier 3 = « maîtrise » (échelle 1→5).
CONCEPT_ABEILLES  = "pollinisation"
SEUIL_EQUIPEMENT  = 3

# Conversion miel → Vigueur + pénalité sans équipement (placeholders, calibrage
# post-test). Sans équipement la récolte est PARTIELLE (on n'ose pas tout prendre,
# les abeilles défendent — l'alarme/piqûre §J viendra au ⑦).
MIEL_VIGUEUR_RATIO = 3.0    # Vigueur rendue par unité de miel récoltée
RECOLTE_SANS_EQUIP = 0.30   # fraction récoltable sans équipement apicole


def poser_ruche(game_state: dict, player: str, eco, r: int, c: int) -> Structure | None:
    """Poser une ruche (§H.1) au plot (r,c) — phase PLANIFICATION, coût MODÉRÉ.
    Crée une structure `ruche` VIDE (essaim=0, miel=0) et l'ajoute à `eco.structures`.
    Binaire (modèle `poser_bac`) : posée QUE si le coût est intégralement payé — un
    geste à vide draine la Vigueur sans rien poser. La capture de l'essaim se fait
    ENSUITE au tick (`tick_ruches`), conditionnée au champ abeille local (philo #1).
    Renvoie la `Structure` posée, ou None si la Vigueur est insuffisante."""
    cost = cout_action(game_state, player, "poser_ruche", OBJETS_TOUCHES["poser_ruche"])
    if spend(game_state, player, cost) < 1.0:
        return None
    struct = Structure(kind="ruche", plot=(r, c))
    eco.structures.append(struct)
    return struct


def equipe(game_state: dict, player: str) -> bool:
    """Le joueur dispose-t-il de l'équipement apicole (§I.3) ? Vrai ssi son palier de
    maîtrise du concept pollinisation atteint `SEUIL_EQUIPEMENT`. Lecture PURE (palier
    d'un concept inconnu = 0 → False, dégradation gracieuse)."""
    return M.palier(game_state, player, CONCEPT_ABEILLES) >= SEUIL_EQUIPEMENT


def recolter_miel(game_state: dict, player: str, struct: Structure, eco=None) -> float:
    """Récolter le miel d'une ruche (§I.2) — canal récolte, coût FAIBLE, gain ∝ miel
    transféré × `MIEL_VIGUEUR_RATIO`. **Refus EN AMONT si rien à récolter** (réserve
    vide → aucune Vigueur dépensée, modèle `epandre`). Avec l'équipement (§I.3) : vide
    la réserve. Sans équipement : récolte PARTIELLE (`RECOLTE_SANS_EQUIP`) ET pose une
    phéromone d'alarme au plot de la ruche (§J.1, ⑦) → les abeilles piquent au curseur
    (réaction temps réel, côté Godot ; le moteur ne fait que poser le signal). L'effort
    est tronqué si la Vigueur ne couvre pas le coût (ratio de `spend`, comme `recolter`).

    `eco` (optionnel) ne sert qu'au dépôt d'alarme : absent (appels de test sans monde)
    → la récolte fonctionne, sans signal posé (dégradation gracieuse, cf `declencher_alarme`).
    Renvoie la Vigueur effectivement gagnée (0.0 = rien récolté / non payé)."""
    if struct.miel <= 0.0:
        return 0.0                              # réserve vide → aucune Vigueur dépensée
    cost = cout_action(game_state, player, "recolter_miel", OBJETS_TOUCHES["recolter_miel"])
    ratio = spend(game_state, player, cost)
    equipped = equipe(game_state, player)
    frac = 1.0 if equipped else RECOLTE_SANS_EQUIP
    recolte = struct.miel * frac * ratio
    struct.miel -= recolte
    gain_v = recolte * MIEL_VIGUEUR_RATIO
    gain(game_state, player, gain_v)
    if not equipped and eco is not None:
        declencher_alarme(eco, struct.plot[0], struct.plot[1], ALARME_DEPOT)
    return gain_v
