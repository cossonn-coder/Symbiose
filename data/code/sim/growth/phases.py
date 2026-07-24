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

from fields import _hash_noise, form_seed_at
from .constantes import (AUXIN_PROD_FLOOR, AUXIN_RELEASE_SCALE, AUXIN_DECAY,
                         AUXIN_INHIB_THRESHOLD, THICKNESS_INIT,
                         JITTER_RAD, ETIOLEMENT_LIGHT_SEUIL, ETIOLEMENT_GAIN,
                         GIRTH_TAU, TAPER_EXP)
from .geometrie import (_tip, _horiz, _lateral_dir, _phototropic_bias,
                        _gravitropic_droop, _apex_z_floor, _depths, _children,
                        _subtree, _apex_in_subtree, _rebuild, taper_thickness)


# ---------------------------------------------------------------------------
# Les 4 phases de la croissance (§D)
# ---------------------------------------------------------------------------

def _update_auxin(segs: list, dominance: float, release_scale: float) -> None:
    """§D.1 — production aux apex (relâchée avec l'âge), transport descendant.
    `dominance` (profil espèce apical_dominance_base) = production d'un apex au
    repos : plus elle est haute, plus l'auxine inhibe loin → flèche ; plus elle est
    basse, plus tôt les latéraux débourrent → buisson.
    `release_scale` (profil espèce auxin_release_scale) = échelle d'âge du relâchement
    d'auxine : GRAND → l'arbre reste dressé longtemps (chêne, hêtre) ; petit → il
    s'étale tôt (pionnier). Défaut 400 = ancienne constante AUXIN_RELEASE_SCALE."""
    plant_age = max((s.age_weeks for s in segs), default=0)
    f_age = max(AUXIN_PROD_FLOOR, 1.0 - plant_age / release_scale)
    for s in segs:
        s.auxin = dominance * f_age if s.is_apex else 0.0
    depth = _depths(segs)
    for i in sorted(range(len(segs)), key=lambda i: -depth[i]):  # extrémités d'abord
        s = segs[i]
        if s.parent is not None:
            par = segs[s.parent]
            par.auxin = max(par.auxin, s.auxin * AUXIN_DECAY)


def _elongate_emit(plant, speed: float, max_height: float, max_extent: float,
                   emit_length: float, light_field=None, strength: float = 0.0,
                   gain: float = 0.0) -> None:
    """§D.2 — l'apex allonge, émet un segment axial au seuil, se retire à portée.
    Bornage par le gabarit du profil espèce : l'apex se retire quand son extrémité
    dépasse `max_height` en hauteur OU `max_extent` en extension horizontale — la
    structure reste dans l'enveloppe (hauteur × rayon de couronne) de l'espèce.
    `emit_length` (profil espèce) = longueur d'un segment émis : grand pour un arbre
    (flèche en peu de segments), petit pour une herbacée (granularité fine).
    Phototropisme (§D.4) : le segment émis prend la direction de l'apex BIAISÉE vers
    le gradient de lumière local (`_phototropic_bias`), bornée et déterministe ;
    `light_field=None` ou `strength=0` → direction axiale droite (ancien comportement).
    Gravitropisme (D91 ③) : APRÈS le phototropisme, `gain` (profil espèce) fait ployer
    le segment émis vers le bas, échelonné par la profondeur du porteur (tronc dressé,
    rameaux distaux pendants = port pleureur). `gain=0` → direction inchangée (défaut :
    seul le bouleau règle gain>0 → golden bit-identique). ORDRE impératif axial →
    phototropisme → gravitropisme : la retombée n'écrase pas la recherche de lumière."""
    segs = plant.segments
    collet = segs[0].base
    # Plancher de verticalité de l'apex, CONTEXTUEL (grimpe, D49 ①). Dépend de la
    # hauteur courante max(z) de la structure : au-delà de la hauteur autoportante,
    # une grimpante libre voit son plancher s'effondrer → elle s'affale (§3). Pour
    # une non-grimpante → MIN_APEX_Z (comportement historique inchangé).
    max_z = max((_tip(s)[2] for s in segs), default=0.0)
    z_floor = _apex_z_floor(plant, max_z)
    new_segs = []
    for i, s in enumerate(list(segs)):  # snapshot : indices stables (on append)
        if not s.is_apex:
            continue                              # épaisseur = pipe model (taper_thickness), en fin de passe
        tip = _tip(s)
        if tip[2] >= max_height or _horiz(tip, collet) >= max_extent:
            s.is_apex = False                     # gabarit atteint → l'apex se retire
            continue
        s.length_cm += speed
        if s.length_cm >= emit_length:
            s.length_cm = emit_length             # cap → le segment devient du bois
            s.is_apex = False
            tip = _tip(s)
            new_dir = _phototropic_bias(s.dir, tip[0], tip[1], light_field,
                                        strength, z_floor)
            if gain > 0.0:
                # Éloignement horizontal du porteur à l'axe du tronc, normalisé par le
                # gabarit de couronne : 0 sur l'axe (flèche dressée), →1 au bord (rameau
                # distal pendant). Discriminant géométrique leader/rameau (cf. helper).
                off_axis = min(1.0, _horiz(tip, collet) / max_extent) if max_extent > 0 else 0.0
                new_dir = _gravitropic_droop(new_dir, off_axis, gain)  # retombée APRÈS phototropisme
            new_segs.append(_mk(i, tip, new_dir, s.auxin))  # apex penché / affalé selon le plancher
    segs.extend(new_segs)


def _debourrement(plant, seed: int, week: int, branch_angle: float,
                  dominance: float) -> None:
    """§D.3 — un bourgeon sous le seuil d'auxine naît latéral (devient apex).
    `branch_angle` (radians, profil espèce) = angle d'insertion ; `dominance` =
    auxine de production du nouvel apex (= apical_dominance_base).
    ② MODÈLE SPATIAL — l'aléa de branche est amorcé par l'IDENTITÉ morphologique
    (`plant.form_seed`) + un ORDINAL stable (`plant.branch_count`), plus par la
    position+semaine. C'est ce qui donne l'air de famille clonal : le ramet copie
    `form_seed` et rejoue la séquence, sa k-ième branche tire le même angle que la
    k-ième de la mère. Divergence fine ensuite via la lumière/phototropisme
    (§D.2/D.4, hors de cette fonction — NE PAS y toucher).
    `seed`/`week` deviennent inutilisés ici : conservés pour ne pas changer la
    signature attendue par le caller `grow_plant`."""
    segs = plant.segments
    fs = plant.form_seed or form_seed_at(0, plant.x_cm, plant.y_cm, 0)   # repli robuste
    new_segs = []
    for i, s in enumerate(list(segs)):
        if s.is_apex or not s.has_bud or s.auxin >= AUXIN_INHIB_THRESHOLD:
            continue
        k = plant.branch_count            # ordinal STABLE, pas la semaine
        plant.branch_count += 1
        phi   = _hash_noise(fs, 0, k, 0) * 2.0 * math.pi
        jit   = (_hash_noise(fs, 0, k, 1) - 0.5) * JITTER_RAD
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
    """Tolérance à l'ombre effective = base d'espèce × gène EXPRIMÉ (Q6 + plasticité ②
    : une plante acclimatée à l'ombre relève sa tolérance effective de son vivant)."""
    return plant.plant_class.shade_tolerance_base() * plant.expressed_gene("tolerance_ombre")


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

def grow_plant(plant, seed: int, week: int, light_field=None,
               confinement: float = 1.0) -> None:
    """
    Fait pousser la structure de `plant` d'un tick, selon le PROFIL DE SON ESPÈCE
    (plant.plant_class : vitesse, dominance, gabarit, angle… cf. PlantBase §E). Les
    constantes de module ci-dessus ne sont plus lues ici — elles restent les DÉFAUTS
    mirroir sur PlantBase. `growth_factor` (lumière intégrée) module la vitesse, en
    LECTURE seule.

    `light_field` (LightField du tick, ou None) : source du gradient pour le
    phototropisme (§D.4). None → apex droit, comportement historique inchangé.

    `confinement` (sprint pots/bacs ③, CONCEPTION §3 levier 3) : facteur ∈ ]0,1]
    qui bride la VITESSE d'élongation quand le mini-sol d'un conteneur sature de
    racines (signal root-bound). DÉFAUT 1.0 → croissance HISTORIQUE inchangée (la
    boucle tuile passe toujours 1.0 → golden NEUTRE). Le calcul de ce facteur (proxy
    de saturation racinaire rapporté au volume du pot) vit dans `world.container` :
    ici on ne fait que LIRE un scalaire déjà décidé par la contrainte de volume. Ce
    n'est pas un malus « parce que c'est un pot » mais une réponse à la saturation
    physique du réservoir racinaire — l'effet nain ÉMERGE de la contrainte (philo #2).

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
    speed = cls.growth_speed * plant.growth_factor * _season_factor(week) * confinement
    # Étiolement (Q7) : un héliophile ombragé file vers la lumière — élongation
    # axiale accrue. Émergent : combiné au phototropisme (_elongate_emit), l'apex
    # grêle peut atteindre une trouée et être sauvé.
    # Thigmomorphogénèse (vent ④, §5.1) : un port TRAPU (expressed_gene("port_trapu")
    # >1, induit par l'exposition au vent) RÉDUIT cet emballement axial — entre-nœuds
    # courts, tige trapue qui s'étiole moins. On divise le gain par le phénotype trapu
    # (neutre 1.0 ⇒ gain inchangé, golden NEUTRE tant que le vent n'a rien exprimé).
    if est_etiole(plant, light_field):
        gain = ETIOLEMENT_GAIN / plant.expressed_gene("port_trapu")
        speed *= (1.0 + gain)
    _update_auxin(segs, cls.apical_dominance_base, cls.auxin_release_scale)
    _elongate_emit(plant, speed, cls.max_height_cm, cls.max_extent_cm,
                   cls.emit_length_cm, light_field, cls.phototropism_strength,
                   cls.gravitropism_gain)
    _debourrement(plant, seed, week, math.radians(cls.branch_angle),
                  cls.apical_dominance_base)
    _elaguer(plant, cls.wood_persistence, cls.max_segments)
    # Rejet de souche : une plante vivante entièrement dormante (plus aucun apex,
    # ex. après senescence totale du vieux bois) reprend du collet → run éternel.
    if not any(s.is_apex for s in plant.segments):
        plant.segments[0].has_bud = True
    # Épaisseur du bois = pipe model + croissance secondaire saturante (sprint
    # lisibilité ligneuse). UNE seule passe par tick (topologie stable ici), après
    # élagage/rejet, avant l'empreinte. Pure structurelle, sans couplage écologique.
    # Réservée aux espèces migrées : les autres n'exposent pas leur structure.
    if cls.procedural_growth:
        taper_thickness(plant.segments, cls.girth_max_cm, GIRTH_TAU,
                        TAPER_EXP, THICKNESS_INIT)
    # §G — empreinte dérivée de la structure (seulement pour les espèces migrées :
    # les autres gardent l'ancien chemin par les stades → recalcul inutile).
    if cls.procedural_growth:
        plant.update_footprint()
