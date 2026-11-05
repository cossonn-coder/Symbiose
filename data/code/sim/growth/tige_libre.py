"""
SYMBIOSE — sim/growth/tige_libre.py
Tige LIBRE d'une liane (sprint HOUPPIER ②) : au-dessus de son appui, une tige ne tient
que sur une certaine longueur. Au-delà elle plie, puis sa partie pliée meurt. PUR
structurel (aucun `eco`) : le dépôt en litière reste à `sim/engine/branches.py`.

📖 Pédagogie (Nico) — pourquoi cette formule ? Une tige dressée flambe sous son propre
poids (Greenhill, 1881) : L ∝ (E/ρ)^⅓ · d^⅔, où E/ρ dit la raideur du matériau pour son
poids et d l'épaisseur. On garde exactement cette forme :

    L_crit = rigidite_tige × f(lignification) × d^⅔      (d : `epaisseur_tige`)

La tige fine et jeune plie vite, la tige épaisse et lignifiée tient plus loin : aucune
règle « hauteur max par espèce », c'est une contrainte physique qui donne le port en
cascade (philo #2). `rigidite_tige` est `None` par défaut : tout ce fichier est inerte
pour toute espèce qui ne le règle pas, haricot compris, donc golden intact.

Trois états d'une pointe, le long de sa branche au-dessus de l'appui :
  libre ≤ L_crit                 elle tient et continue ;
  L_crit < libre                 elle plie : ses nouveaux segments visent le bas ;
  libre > L_crit × MARGE         tout ce qui dépasse L_crit tombe, un bourgeon repart.

Parents avant enfants dans `segs` (invariant de l'append, conservé par `_rebuild`) : une
passe avant suffit, O(n). Zéro RNG (philo #3).
"""

from __future__ import annotations
import math

from .cladoptose import couper_branches
from .constantes import (PLIAGE_GAIN, PLIAGE_Z, MARGE_EFFONDREMENT, LIGNIF_TIGE_MIN,
                         RELAIS_BIAIS, RELAIS_CONTACT_CM, GIRTH_TAU, TAPER_EXP,
                         THICKNESS_INIT)
from .geometrie import _norm, _gravitropic_droop
from .seam import f_lignification

_AUCUN: frozenset = frozenset()


def epaisseur_tige(seg, cls, n_pointes: int) -> float:
    """Épaisseur d'UNE tige de l'âge de `seg`. `thickness_cm` ne convient pas au départ de
    la partie libre : le pipe model y additionne toutes les tiges portées. Au collet d'un
    lierre sans appui il donne 4,18 cm, soit 3 m de tenue [`liane_relais`, s156, seed 42,
    n=1 run], alors qu'une liane est un faisceau de tiges fines, pas un tronc soudé.
    On retire donc la part du faisceau : (1/n_pointes)^exp au lieu de (n_i/n_pointes)^exp."""
    sat = 1.0 - math.exp(-seg.age_weeks / GIRTH_TAU)
    return THICKNESS_INIT + cls.girth_max_cm * sat * (1.0 / n_pointes) ** TAPER_EXP


def longueur_critique(cls, seg, n_pointes: int) -> float:
    """`L_crit` d'une tige partant de `seg`. La jeune tige n'est pas sans tenue : le
    plancher LIGNIF_TIGE_MIN lui laisse une raideur d'herbacée [choix]."""
    lignif = LIGNIF_TIGE_MIN + (1.0 - LIGNIF_TIGE_MIN) * f_lignification(seg.age_weeks)
    return cls.rigidite_tige * lignif * epaisseur_tige(seg, cls, n_pointes) ** (2.0 / 3.0)


def longueurs_libres(plant) -> tuple[list, list]:
    """Pour chaque segment : longueur libre cumulée depuis le passage de l'appui, et
    `L_crit` de sa tige, fixée au segment qui franchit l'appui (`inf` s'il reste dessous).
    Une tige sortie de l'appui reste libre, même si elle redescend : elle pend, elle
    ne s'y rattache pas. Sans appui, c'est la hauteur autoportante qui en tient lieu."""
    cls = plant.plant_class
    h = plant.support[1] if plant.support is not None else cls.hauteur_autoportante
    segs = plant.segments
    a_enfant = {s.parent for s in segs}
    n_pointes = sum(1 for i in range(len(segs)) if i not in a_enfant)
    libre = [0.0] * len(segs)
    crit = [math.inf] * len(segs)
    for i, s in enumerate(segs):
        p = s.parent
        if p is not None and libre[p] > 0.0:
            libre[i] = libre[p] + s.length_cm
            crit[i] = crit[p]
            continue
        z0 = s.base[2]
        z1 = z0 + s.dir[2] * s.length_cm
        if z1 > h:
            libre[i] = s.length_cm * (1.0 if z0 >= h else (z1 - h) / (z1 - z0))
            crit[i] = longueur_critique(cls, s, n_pointes)
    return libre, crit


def apex_plies(plant):
    """Indices des apex au-delà de `L_crit`. Vide sans `rigidite_tige` : inerte."""
    if plant.plant_class.rigidite_tige is None:
        return _AUCUN
    libre, crit = longueurs_libres(plant)
    return {i for i, s in enumerate(plant.segments) if s.is_apex and libre[i] > crit[i]}


def plier(d: tuple) -> tuple:
    """Courbe la direction d'un segment émis vers le bas, jusqu'à PLIAGE_Z. Un plancher
    ne suffit pas : `_clamp_apex_z` laisse telle quelle une pointe qui monte, et le port
    affalé de `DROOP_Z` ne descend que si la lumière l'incline."""
    return d if d[2] <= PLIAGE_Z else _gravitropic_droop(d, 1.0, PLIAGE_GAIN)


def vers_relais(d: tuple, tip: tuple, plant) -> tuple:
    """Une tige relayée peut être à 75 cm de son nouvel appui : elle s'en rapproche en
    montant, sinon elle grimperait dans le vide. `plant.relais` n'est lu que s'il décrit
    encore l'appui courant : une accroche posée par un autre chemin l'invalide d'elle-même."""
    ref, x, y = plant.relais
    if plant.support is None or plant.support[0] is not ref or tip[2] >= plant.support[1]:
        return d
    dx, dy = x - tip[0], y - tip[1]
    m = math.hypot(dx, dy)
    if m < RELAIS_CONTACT_CM:
        return d
    return _norm((d[0] + RELAIS_BIAIS * dx / m, d[1] + RELAIS_BIAIS * dy / m, d[2]))


def effondrer(plant) -> list:
    """Coupe ce qui dépasse `L_crit` sur les tiges passées au-delà de la marge, réveille
    un bourgeon sur le porteur, et RENVOIE les segments tombés (contrat de `couper_branches`).

    📖 On coupe au point de pliage et non à l'appui : la partie dressée tient, seule la
    partie pendante meurt. Le repère est `L_crit` et pas `axe_porteur`, qui protège le
    chemin vers le point le plus haut, celui-là même qui doit tomber ici. Le collet et
    tout ce qui reste sous l'appui ne sont jamais coupés, par construction.
    Repousse en cascade lente : (MARGE − 1) × L_crit à 2 cm/semaine avant la coupe
    suivante sur la même tige, pas d'oscillation d'une semaine à l'autre."""
    if plant.plant_class.rigidite_tige is None:
        return []
    segs = plant.segments
    libre, crit = longueurs_libres(plant)
    pire = list(libre)                                # le plus loin atteint dans le sous-arbre
    for i in range(len(segs) - 1, 0, -1):
        p = segs[i].parent
        if pire[i] > pire[p]:
            pire[p] = pire[i]
    roots = []
    for i in range(1, len(segs)):
        p = segs[i].parent
        if (libre[i] > crit[i] and (p == 0 or libre[p] <= crit[p])
                and pire[i] > crit[i] * MARGE_EFFONDREMENT):
            roots.append(i)
            segs[p].has_bud = True                    # avant la coupe : les indices vont bouger
    return couper_branches(plant, roots)
