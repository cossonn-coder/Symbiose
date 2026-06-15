"""
SYMBIOSE — sim/growth/phases.py
Les phases de la croissance (§D.1-D.6) et le point d'entrée `grow_plant` : une
passe par plante et par tick fait POUSSER sa structure de segments, pilotée par
l'AUXINE (dominance apicale émergente) + un BORNAGE (le vieux bois tombe).
Déterministe (philo #3 : aucun RNG, tout passe par fields._hash_noise).

Inclut aussi l'étiolement (Q7), partagé entre la croissance (élongation accrue) et
l'engine (coût de robustesse côté convalescence).
"""

from __future__ import annotations
import math

from fields import _hash_noise
from .constantes import (AUXIN_PROD_FLOOR, AUXIN_RELEASE_SCALE, AUXIN_DECAY,
                         AUXIN_INHIB_THRESHOLD, THICKEN_RATE, THICKNESS_INIT,
                         JITTER_RAD, ETIOLEMENT_LIGHT_SEUIL, ETIOLEMENT_GAIN)
from .geometrie import (_tip, _horiz, _lateral_dir, _phototropic_bias,
                        _depths, _children, _subtree, _apex_in_subtree, _rebuild)


# ---------------------------------------------------------------------------
# Les 4 phases de la croissance (§D)
# ---------------------------------------------------------------------------

def _update_auxin(segs: list, dominance: float) -> None:
    """§D.1 — production aux apex (relâchée avec l'âge), transport descendant.
    `dominance` (profil espèce apical_dominance_base) = production d'un apex au
    repos : plus elle est haute, plus l'auxine inhibe loin → flèche ; plus elle est
    basse, plus tôt les latéraux débourrent → buisson."""
    plant_age = max((s.age_weeks for s in segs), default=0)
    f_age = max(AUXIN_PROD_FLOOR, 1.0 - plant_age / AUXIN_RELEASE_SCALE)
    for s in segs:
        s.auxin = dominance * f_age if s.is_apex else 0.0
    depth = _depths(segs)
    for i in sorted(range(len(segs)), key=lambda i: -depth[i]):  # extrémités d'abord
        s = segs[i]
        if s.parent is not None:
            par = segs[s.parent]
            par.auxin = max(par.auxin, s.auxin * AUXIN_DECAY)


def _elongate_emit(plant, speed: float, max_height: float, max_extent: float,
                   emit_length: float, light_field=None, strength: float = 0.0) -> None:
    """§D.2 — l'apex allonge, émet un segment axial au seuil, se retire à portée.
    Bornage par le gabarit du profil espèce : l'apex se retire quand son extrémité
    dépasse `max_height` en hauteur OU `max_extent` en extension horizontale — la
    structure reste dans l'enveloppe (hauteur × rayon de couronne) de l'espèce.
    `emit_length` (profil espèce) = longueur d'un segment émis : grand pour un arbre
    (flèche en peu de segments), petit pour une herbacée (granularité fine).
    Phototropisme (§D.4) : le segment émis prend la direction de l'apex BIAISÉE vers
    le gradient de lumière local (`_phototropic_bias`), bornée et déterministe ;
    `light_field=None` ou `strength=0` → direction axiale droite (ancien comportement)."""
    segs = plant.segments
    collet = segs[0].base
    new_segs = []
    for i, s in enumerate(list(segs)):  # snapshot : indices stables (on append)
        if not s.is_apex:
            s.thickness_cm += THICKEN_RATE        # le bois porteur épaissit
            continue
        tip = _tip(s)
        if tip[2] >= max_height or _horiz(tip, collet) >= max_extent:
            s.is_apex = False                     # gabarit atteint → l'apex se retire
            continue
        s.length_cm += speed
        if s.length_cm >= emit_length:
            s.length_cm = emit_length             # cap → le segment devient du bois
            s.is_apex = False
            tip = _tip(s)
            new_dir = _phototropic_bias(s.dir, tip[0], tip[1], light_field, strength)
            new_segs.append(_mk(i, tip, new_dir, s.auxin))  # apex penché vers la lumière
    segs.extend(new_segs)


def _debourrement(plant, seed: int, week: int, branch_angle: float,
                  dominance: float) -> None:
    """§D.3 — un bourgeon sous le seuil d'auxine naît latéral (devient apex).
    `branch_angle` (radians, profil espèce) = angle d'insertion ; `dominance` =
    auxine de production du nouvel apex (= apical_dominance_base)."""
    segs = plant.segments
    new_segs = []
    for i, s in enumerate(list(segs)):
        if s.is_apex or not s.has_bud or s.auxin >= AUXIN_INHIB_THRESHOLD:
            continue
        bx, by = int(s.base[0]), int(s.base[1])
        phi   = _hash_noise(seed, week, bx + i, by) * 2.0 * math.pi
        jit   = (_hash_noise(seed, week, bx, by + i) - 0.5) * JITTER_RAD
        ldir  = _lateral_dir(s.dir, branch_angle + jit, phi)
        s.has_bud = False                         # bourgeon consommé
        new_segs.append(_mk(i, _tip(s), ldir, dominance))
    segs.extend(new_segs)


def _elaguer(plant, wood_persistence: int, max_segments: int) -> None:
    """§D.6 — sénescence du bois sans apex + plafond `max_segments`. Collet protégé.
    `wood_persistence` (profil espèce) = longévité du bois sans apex actif ;
    `max_segments` (profil espèce) = plafond dur de segments (haut pour un arbre)."""
    segs = plant.segments
    if len(segs) <= 1:
        return
    ch       = _children(segs)
    depth    = _depths(segs)
    has_apex = _apex_in_subtree(segs, ch, depth)
    kill = set()
    # Sénescence : vieux bois sans apex dans son sous-arbre → le sous-arbre tombe.
    for i, s in enumerate(segs):
        if s.parent is None:
            continue                              # collet protégé
        if s.age_weeks > wood_persistence and not has_apex[i]:
            kill.update(_subtree(i, ch))
    # Plafond MAX_SEGMENTS : d'abord les plus vieux improductifs (§D.6 « en
    # priorité »), puis — filet DUR — les extrémités les plus profondes (taille
    # de la couronne) jusqu'à repasser sous le plafond. Garantit le bornage.
    alive = len(segs) - len(kill)
    if alive > max_segments:
        improd = sorted(
            (i for i in range(len(segs))
             if i not in kill and segs[i].parent is not None and not has_apex[i]),
            key=lambda i: -segs[i].age_weeks)
        deepest = sorted(
            (i for i in range(len(segs))
             if segs[i].parent is not None),
            key=lambda i: -depth[i])
        for i in improd + deepest:
            if alive <= max_segments:
                break
            if i in kill:
                continue
            kill.update(_subtree(i, ch))
            alive = len(segs) - len(kill)
    if kill:
        _rebuild(plant, kill)


def _mk(parent: int, base: tuple, direction: tuple, auxin: float):
    """Fabrique un segment apex neuf (import paresseux pour éviter un cycle)."""
    from plants.base import Segment
    return Segment(parent=parent, base=base, dir=direction, length_cm=0.0,
                   thickness_cm=THICKNESS_INIT, age_weeks=0, auxin=auxin,
                   is_apex=True, has_bud=True)


# ---------------------------------------------------------------------------
# Facteur saisonnier (placeholder local — pas d'import engine, anti-cycle)
# ---------------------------------------------------------------------------

def _season_factor(week: int) -> float:
    """Croissance ralentie en hiver (semaines 40-52). Levier à calibrer."""
    wiy = ((week - 1) % 52) + 1
    return 0.25 if wiy >= 40 else 1.0


# ---------------------------------------------------------------------------
# Étiolement (Q7) — partagé entre growth (élongation) et engine (robustesse)
# ---------------------------------------------------------------------------

def shade_tolerance_effective(plant) -> float:
    """Tolérance à l'ombre effective = base d'espèce × gène individuel (Q6)."""
    return plant.plant_class.shade_tolerance_base() * plant.gene("tolerance_ombre")


def est_etiole(plant, light_field) -> bool:
    """Vrai si la plante S'ÉTIOLE ce tick : héliophile (tolérance effective < 1)
    sous une lumière effective < ETIOLEMENT_LIGHT_SEUIL. light_field None ⇒ False
    (les outils/tests sans lumière restent inchangés)."""
    if light_field is None:
        return False
    tol = shade_tolerance_effective(plant)
    if tol >= 1.0:
        return False
    light_eff = min(1.0, light_field.light_received(plant) * tol)
    return light_eff < ETIOLEMENT_LIGHT_SEUIL


# ---------------------------------------------------------------------------
# Point d'entrée — une passe de croissance par plante par tick
# ---------------------------------------------------------------------------

def grow_plant(plant, seed: int, week: int, light_field=None) -> None:
    """
    Fait pousser la structure de `plant` d'un tick, selon le PROFIL DE SON ESPÈCE
    (plant.plant_class : vitesse, dominance, gabarit, angle… cf. PlantBase §E). Les
    constantes de module ci-dessus ne sont plus lues ici — elles restent les DÉFAUTS
    mirroir sur PlantBase. `growth_factor` (lumière intégrée) module la vitesse, en
    LECTURE seule.

    `light_field` (LightField du tick, ou None) : source du gradient pour le
    phototropisme (§D.4). None → apex droit, comportement historique inchangé.

    Tronçon 2 : pour une espèce MIGRÉE (`procedural_growth`), l'empreinte est
    recalculée en fin de passe (update_footprint, §G) → height_at/canopy_radius_at…
    la liront. Pour une espèce non migrée, la structure reste INERTE (non lue).
    """
    segs = plant.segments
    if not segs:
        return
    cls = plant.plant_class
    for s in segs:
        s.age_weeks += 1
    speed = cls.growth_speed * plant.growth_factor * _season_factor(week)
    # Étiolement (Q7) : un héliophile ombragé file vers la lumière — élongation
    # axiale accrue. Émergent : combiné au phototropisme (_elongate_emit), l'apex
    # grêle peut atteindre une trouée et être sauvé.
    if est_etiole(plant, light_field):
        speed *= (1.0 + ETIOLEMENT_GAIN)
    _update_auxin(segs, cls.apical_dominance_base)
    _elongate_emit(plant, speed, cls.max_height_cm, cls.max_extent_cm,
                   cls.emit_length_cm, light_field, cls.phototropism_strength)
    _debourrement(plant, seed, week, math.radians(cls.branch_angle),
                  cls.apical_dominance_base)
    _elaguer(plant, cls.wood_persistence, cls.max_segments)
    # Rejet de souche : une plante vivante entièrement dormante (plus aucun apex,
    # ex. après senescence totale du vieux bois) reprend du collet → run éternel.
    if not any(s.is_apex for s in plant.segments):
        plant.segments[0].has_bud = True
    # §G — empreinte dérivée de la structure (seulement pour les espèces migrées :
    # les autres gardent l'ancien chemin par les stades → recalcul inutile).
    if cls.procedural_growth:
        plant.update_footprint()
