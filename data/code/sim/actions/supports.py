"""
SYMBIOSE — sim/actions/supports.py
Gestes JOUEUR de la GRIMPE (D49 volet A, CONCEPTION_GRIMPANTES §6, tronçon ④).
Couche joueur du sprint grimpantes : poser des structures-support et PALISSER une
grimpante sarmenteuse. Modelés sur la famille pose (`compost.poser_bac`,
`conteneurs.poser_pot`) — phase PLANIFICATION, coût MODÉRÉ, geste BINAIRE (posé
QUE si la Vigueur est intégralement payée ; un geste à vide draine sans rien poser).

Quatre gestes :
  - `poser_tuteur`  : pieu FIN vertical (une grimpante à vrille l'enroule).
  - `poser_treillis`: grille SURFACE (support fin étendu, mêmes prises).
  - `poser_pergola` : structure SURFACE haute (couvre, prises hautes).
  - `palisser`      : attache À LA MAIN une grimpante `sarmenteux` (jasmin) à un
    support posé voisin. C'est le SEUL canal d'accroche du sarmenteux (il n'a aucun
    organe d'accroche → `support_compatible` le refuse partout, ② `world/support.py`) :
    le joueur noue la canne au support. Aucune autre grimpante n'a besoin de
    palissage (crampon/vrille_volubile s'accrochent seuls au tick, `sim/grimpe.py`).

Les supports vivent dans `tile.supports` (défaut `[]` → aucune accroche possible →
golden NEUTRE). Ces gestes la PEUPLENT, hors tick : le smoke n'en pose aucun et ne
palisse rien → golden INTACT par construction (event-driven).

Concepts de maîtrise associés (déclarés, NON câblés au tick, §6) : technique
`palissage`, outils `tuteur`/`treillis`/`pergola` (nommés dans `couts.OBJETS_TOUCHES`,
classés par `encyclopedie_types`). Sans état moteur aujourd'hui → `M.palier(...) == 0`
→ atténuation neutre 1.0 (dégradation gracieuse §10.5), comme `compostage`.
"""
from __future__ import annotations

import math

from constants import PLOT_CM
from sim.vigueur import spend
from world import Support
from .couts import cout_action, OBJETS_TOUCHES

# Rayon de palissage : le joueur ne peut nouer une canne qu'à un support À PORTÉE
# de la plante — même voisinage borné que l'accroche automatique (`sim/grimpe.py`),
# pour une géométrie cohérente. Placeholder de calibrage (maquette ⑥).
RAYON_PALISSAGE_CM = 1.5 * PLOT_CM

# Gabarits des trois structures (§6, placeholders de calibrage — maquette ⑥).
# `height_cm` = hauteur d'appui offerte ; `finesse` qualifie la prise (pieu fin vs
# grille/paroi, INERTE au moteur, lue plus tard par le rendu ⑥).
_GABARITS: dict[str, tuple[float, str]] = {
    "tuteur":   (180.0, "fin"),      # pieu vertical grêle
    "treillis": (180.0, "surface"),  # grille verticale étendue
    "pergola":  (220.0, "surface"),  # structure haute couvrante
}


def _poser_support(game_state: dict, player: str, tile, kind: str,
                   x_cm: float, y_cm: float) -> Support | None:
    """Cœur commun des trois `poser_*` (§6). Instancie un `Support` de type `kind`
    à la position monde-tuile `(x_cm, y_cm)` et l'ajoute à `tile.supports` — phase
    PLANIFICATION, coût MODÉRÉ. Binaire (modèle `poser_bac`) : posé QUE si le coût
    est intégralement payé. Renvoie le `Support` posé, ou None (Vigueur insuffisante).
    Contrairement au bac/pile (⑤), PAS d'unicité par tuile : on peut aligner
    plusieurs tuteurs (une rangée de haricots)."""
    cost = cout_action(game_state, player, f"poser_{kind}", OBJETS_TOUCHES[f"poser_{kind}"])
    if spend(game_state, player, cost) < 1.0:
        return None
    height_cm, finesse = _GABARITS[kind]
    sup = Support(support_type=kind, x_cm=x_cm, y_cm=y_cm,
                  height_cm=height_cm, finesse=finesse)
    tile.supports.append(sup)
    return sup


def poser_tuteur(game_state: dict, player: str, tile,
                 x_cm: float, y_cm: float) -> Support | None:
    """Poser un TUTEUR (pieu fin) à `(x_cm, y_cm)` (§6). Cf. `_poser_support`."""
    return _poser_support(game_state, player, tile, "tuteur", x_cm, y_cm)


def poser_treillis(game_state: dict, player: str, tile,
                   x_cm: float, y_cm: float) -> Support | None:
    """Poser un TREILLIS (grille) à `(x_cm, y_cm)` (§6). Cf. `_poser_support`."""
    return _poser_support(game_state, player, tile, "treillis", x_cm, y_cm)


def poser_pergola(game_state: dict, player: str, tile,
                  x_cm: float, y_cm: float) -> Support | None:
    """Poser une PERGOLA (structure haute) à `(x_cm, y_cm)` (§6). Cf. `_poser_support`."""
    return _poser_support(game_state, player, tile, "pergola", x_cm, y_cm)


def palisser(game_state: dict, player: str, plant, tile) -> bool:
    """Palisser (§6) — attacher À LA MAIN la grimpante `sarmenteux` `plant` au support
    posé le PLUS PROCHE dans son rayon (structures de `tile.supports`). C'est le seul
    canal d'accroche du sarmenteux : le joueur noue la canne, là où `support_compatible`
    refuse toute saisie automatique (② : `_COMPATIBILITE["sarmenteux"] == ∅`).

    Refus EN AMONT — aucune Vigueur dépensée (modèle `deplacer_pot`/`epandre` jauge
    vide : on ne paie pas un geste impossible) — si :
      • la plante n'est PAS de mode `sarmenteux` (les autres s'accrochent seules,
        palisser n'a aucun sens ; on ne double pas une accroche existante) ;
      • la plante est déjà accrochée (`support is not None`) ;
      • aucun support n'est à portée (rien à quoi nouer).

    Sinon geste BINAIRE (modèle `poser_*`) : l'accroche n'est posée QUE si le coût
    MODÉRÉ est intégralement payé. Pose `plant.support = (support, height_cm)` — le
    plancher d'apex renforcé (`sim/growth/geometrie._apex_z_floor`, ①/②) fera monter
    la plante le long du support. Renvoie True si palissé, False sinon."""
    cls = plant.plant_class
    if getattr(cls, "mode_grimpe", None) != "sarmenteux" or plant.support is not None:
        return False                          # pas un sarmenteux libre → geste impossible
    sup = _support_a_portee(plant, tile)
    if sup is None:
        return False                          # rien à portée → rien dépensé
    cost = cout_action(game_state, player, "palisser", OBJETS_TOUCHES["palisser"])
    if spend(game_state, player, cost) < 1.0:
        return False                          # Vigueur insuffisante → non palissé
    plant.support = (sup, sup.height_cm)
    return True


def _support_a_portee(plant, tile) -> Support | None:
    """Le `Support` posé le plus proche de `plant` dans `RAYON_PALISSAGE_CM`, ou None.
    Départage déterministe (distance PUIS index de pose, zéro RNG, philo #3), comme
    `sim/grimpe.chercher_support`. Le mur maison n'est PAS candidat ici : palisser un
    sarmenteux au mur (espalier) demanderait le repère monde de la tuile → différé (le
    canal principal du palissage reste les structures posées ; l'espalier sarmenteux
    est un raffinement de maquette ⑥). Une canne se noue à un support, jamais à un hôte
    vivant → seuls les `Support` inertes sont candidats."""
    candidats = []
    for i, sup in enumerate(tile.supports):
        d = math.hypot(plant.x_cm - sup.x_cm, plant.y_cm - sup.y_cm)
        if d <= RAYON_PALISSAGE_CM:
            candidats.append((d, i, sup))
    if not candidats:
        return None
    return min(candidats, key=lambda t: (t[0], t[1]))[2]
