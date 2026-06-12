"""
SYMBIOSE — sim/growth.py
Croissance procédurale des plantes (D29 réorienté, tronçon 1 : cœur INERTE).

Une passe par plante et par tick fait POUSSER sa structure de segments
(plants.base.Segment), pilotée par l'AUXINE le long de la structure (dominance
apicale émergente) + un BORNAGE (le vieux bois tombe). Source de vérité Python,
déterministe (philo #3 : aucun RNG, tout passe par fields._hash_noise).

CE QUI EST INERTE À CE TRONÇON : la structure grandit À CÔTÉ. Personne ne la
LIT encore (height_at/canopy_radius_at viennent toujours des stades). Donc le
golden écologique NE BOUGE PAS — grow_plant ne touche QUE `plant.segments`,
jamais les champs ni les attributs hashés (current_stage, growth_factor,
mémoires…). Le câblage à l'empreinte = tronçon 2 (re-figeage maîtrisé).

Algorithme (CONCEPTION_CROISSANCE.md §D), dans l'ordre, par plante vivante :
  §D.1 auxine : production aux apex (relâchée avec l'âge → moteur permanent),
        transport descendant décroissant, inhibition latérale (dominance) ;
  §D.2 allongement & émission : l'apex allonge puis émet un segment axial ;
  §D.3 débourrement : un bourgeon dont l'auxine passe sous le seuil naît latéral ;
  §D.6 bornage : le bois trop vieux et sans apex actif meurt et TOMBE ; plafond
        MAX_SEGMENTS ; collet (parent=None) protégé → structure bornée.

Phototropisme (§D.4) : BRANCHÉ (sprint maison, tronçon 3). À l'émission d'un
segment axial, l'apex biaise sa direction horizontale vers le gradient local de
lumière-sol (lu dans le LightField passé à grow_plant), de façon déterministe,
bornée (angle max/émission, jamais à plat) et d'intensité paramétrable par espèce
(PlantBase.phototropism_strength). LightField absent (None) → apex droit = ancien
comportement (les tests/outils qui n'injectent pas de lumière restent inchangés).
Le jitter déterministe d'azimut des LATÉRAUX (§D.3) est conservé tel quel.
"""
from __future__ import annotations
import math

from constants import PLOT_CM
from fields import _hash_noise

# Tronçon 2 : les leviers PAR ESPÈCE (vitesse, dominance, angle, gabarit, longévité
# du bois) ont été promus en attributs de classe sur PlantBase (§E.1). Les constantes
# marquées « ↳ défaut PlantBase » ci-dessous ne sont plus lues par grow_plant : elles
# restent comme valeurs de référence, mirroir des défauts de PlantBase. Les autres
# (EMIT_LENGTH, THICK*, JITTER_RAD, MAX_SEGMENTS, AUXIN_DECAY/THRESHOLD/FLOOR/SCALE)
# demeurent des leviers de module communs à toutes les espèces.

# --- Auxine (dynamique de la dominance apicale, §D.1) ----------------------
AUXIN_SOURCE          = 1.0     # ↳ défaut PlantBase.apical_dominance_base (production d'un apex au repos)
AUXIN_DECAY           = 0.88    # transport descendant : auxin ×= DECAY par segment
AUXIN_INHIB_THRESHOLD = 0.35    # sous ce niveau, un bourgeon peut débourrer
AUXIN_PROD_FLOOR      = 0.15    # plancher de production (vieux sujet s'étale)
AUXIN_RELEASE_SCALE   = 400.0   # semaines : échelle de relâchement avec l'âge

# --- Allongement & émission (§D.2) -----------------------------------------
GROWTH_SPEED   = 2.0     # ↳ défaut PlantBase.growth_speed (cm/tick d'allongement)
EMIT_LENGTH    = 8.0     # cm : au-delà, l'apex émet un segment axial
THICKNESS_INIT = 0.3     # épaisseur d'un segment neuf
THICKEN_RATE   = 0.03    # cm/tick d'épaississement du bois porteur

# --- Débourrement (§D.3) ----------------------------------------------------
BRANCH_ANGLE = math.radians(50.0)  # ↳ défaut PlantBase.branch_angle (50°) — converti à la lecture
JITTER_RAD   = math.radians(20.0)  # amplitude du jitter déterministe d'azimut

# --- Phototropisme (§D.4 — biais directionnel vers la lumière) --------------
PHOTOTROPISM_STRENGTH = 0.30                # ↳ défaut PlantBase.phototropism_strength (MARQUÉ, Q3)
MAX_PHOTOTROPISM_TILT = math.radians(12.0)  # déviation max d'azimut par segment émis (borné)
MIN_APEX_Z            = 0.30                 # composante verticale plancher de l'apex (jamais à plat)

# --- Bornage (§D.6 — run éternel) ------------------------------------------
MAX_REACH_CM     = 200.0  # ↳ défaut PlantBase.max_height_cm/max_extent_cm (gabarit d'arbre)
WOOD_PERSISTENCE = 60     # ↳ défaut PlantBase.wood_persistence (longévité du bois sans apex)
MAX_SEGMENTS     = 40     # plafond dur de segments par plante (filet de sécurité)

# --- Seam de perturbation (§F) ---------------------------------------------
COUPE_NETTE = 0.8   # intensité-seuil : AU-DELÀ, la perturbation ÉCIME (retrait du
                    # segment ciblé + son sous-arbre) ; EN DEÇÀ, elle ne fait que
                    # baisser l'auxine locale (perturbation douce). Levier de calibrage.

# --- Calibrage de l'ÉCRASEMENT (volet 2, CONCEPTION_ECRASEMENT §5) ----------
# Ces leviers sont LUS par sim.actions.ecraser_plante (geste joueur event-driven),
# JAMAIS par grow_plant → le golden ne peut pas bouger. growth.py reste pur
# structurel : la mutation `health` (régime NET) est faite dans actions.py ; ici on
# ne fournit que les CONSTANTES + la fonction d'âge (pures, déterministes).
INTENSITE_PIED     = 1.0    # intensité nominale d'un pied au sol (espèce de résistance
                           # nulle → NET franc) ; modulée par resistance × âge en aval.
SEUIL_DEGAT        = 0.5    # seuil sur (1 − stimulation) : au-delà, un écrasement NET
                           # entame la santé. Sépare les épargnées (stim ≥ 0.5 : basilic,
                           # pâturin, trèfle…) des entamées (stim < 0.5 : tournesol…).
LIGNIFICATION_SCALE = 52.0  # semaines : échelle de lignification. f≈0 pour un semis
                           # (s'écrase), → 1 pour un sujet établi (résistance pleine).


def f_lignification(age_weeks: float) -> float:
    """Fraction de lignification ∈ [0,1] (Q4) — croissante bornée de l'âge. Un semis
    (age_weeks ≈ 0) ⇒ ≈ 0 : sa résistance effective est quasi nulle, il s'écrase. Un
    sujet établi (age_weeks ≥ LIGNIFICATION_SCALE) ⇒ 1 : résistance pleine (un tronc
    ne s'écrase pas). Pure, déterministe (zéro RNG)."""
    return min(1.0, max(0.0, age_weeks) / LIGNIFICATION_SCALE)


# ---------------------------------------------------------------------------
# Géométrie 3D (pure)
# ---------------------------------------------------------------------------

def _tip(s) -> tuple:
    """Extrémité d'un segment = base + dir·length."""
    return (s.base[0] + s.dir[0] * s.length_cm,
            s.base[1] + s.dir[1] * s.length_cm,
            s.base[2] + s.dir[2] * s.length_cm)


def _dist(p: tuple, q: tuple) -> float:
    return math.sqrt((p[0]-q[0])**2 + (p[1]-q[1])**2 + (p[2]-q[2])**2)


def _horiz(p: tuple, q: tuple) -> float:
    """Distance horizontale (plan sol) entre deux points — extension de couronne."""
    return math.hypot(p[0]-q[0], p[1]-q[1])


def _norm(v: tuple) -> tuple:
    m = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
    if m < 1e-9:
        return (0.0, 0.0, 1.0)
    return (v[0]/m, v[1]/m, v[2]/m)


def _cross(a: tuple, b: tuple) -> tuple:
    return (a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0])


def _lateral_dir(d: tuple, theta: float, phi: float) -> tuple:
    """
    Direction d'un latéral : la direction du porteur `d` inclinée de `theta`,
    avec azimut `phi` (jitter déterministe). Base orthonormée construite autour
    de `d` (référence = verticale, ou X si `d` est ~vertical).
    """
    ref = (0.0, 0.0, 1.0) if abs(d[2]) < 0.99 else (1.0, 0.0, 0.0)
    u = _norm(_cross(d, ref))
    v = _cross(d, u)
    ct, st = math.cos(theta), math.sin(theta)
    cp, sp = math.cos(phi), math.sin(phi)
    return _norm((ct*d[0] + st*(cp*u[0] + sp*v[0]),
                  ct*d[1] + st*(cp*u[1] + sp*v[1]),
                  ct*d[2] + st*(cp*u[2] + sp*v[2])))


# ---------------------------------------------------------------------------
# Phototropisme (§D.4) — biais directionnel vers la lumière (pure, déterministe)
# ---------------------------------------------------------------------------

def _light_at(lf, r: int, c: int) -> float:
    """Lumière-sol au plot (r,c), bornes CLAMPÉES sur la grille. Le clamp (≠
    at_plot qui renvoie 0 hors grille) évite une fausse pente au bord de tuile :
    en lisière, la différence finie devient unilatérale au lieu de plonger à 0."""
    rr = 0 if r < 0 else (lf.rows - 1 if r >= lf.rows else r)
    cc = 0 if c < 0 else (lf.cols - 1 if c >= lf.cols else c)
    return lf.data[rr][cc]


def _light_gradient(tx: float, ty: float, lf) -> tuple:
    """Gradient horizontal de la lumière-sol au point (tx,ty) cm (repère tuile-local,
    x=Est, y=Sud). Différences finies entre plots voisins (Est−Ouest, Sud−Nord).
    Pointe vers le plus lumineux ; (0,0) si l'éclairement est uniforme (→ pas de
    biais : le golden ne dérive pas en lumière homogène, piège §7)."""
    fr = int(ty // PLOT_CM)
    fc = int(tx // PLOT_CM)
    gx = _light_at(lf, fr, fc + 1) - _light_at(lf, fr, fc - 1)
    gy = _light_at(lf, fr + 1, fc) - _light_at(lf, fr - 1, fc)
    return (gx, gy)


def _phototropic_bias(d: tuple, tx: float, ty: float, lf, strength: float) -> tuple:
    """Direction de l'apex `d` biaisée vers le gradient de lumière (§D.4). Rotation
    de `d` vers le gradient horizontal, d'un angle BORNÉ (≤ MAX_PHOTOTROPISM_TILT par
    émission, ∝ gradient × strength) et avec un PLANCHER de verticalité (MIN_APEX_Z :
    l'apex ne se couche jamais à plat — la verticalité reste l'attracteur, la lumière
    la dévie). Déterministe, zéro RNG. strength≤0 ou lumière uniforme → `d` inchangé."""
    if strength <= 0.0 or lf is None:
        return d
    gx, gy = _light_gradient(tx, ty, lf)
    gmag = math.hypot(gx, gy)
    if gmag < 1e-9:
        return d                                   # éclairement uniforme : pas de biais
    tilt = min(MAX_PHOTOTROPISM_TILT, strength * gmag)
    gh = (gx / gmag, gy / gmag, 0.0)               # direction unitaire vers le clair (horizontale)
    dot = d[0] * gh[0] + d[1] * gh[1]              # gh[2] = 0
    # composante de gh perpendiculaire à d (axe de rotation dans le plan (d, gh))
    perp = (gh[0] - dot * d[0], gh[1] - dot * d[1], -dot * d[2])
    pm = math.sqrt(perp[0]**2 + perp[1]**2 + perp[2]**2)
    if pm < 1e-9:
        return d                                   # apex déjà aligné sur le gradient
    perp = (perp[0]/pm, perp[1]/pm, perp[2]/pm)
    ct, st = math.cos(tilt), math.sin(tilt)
    nd = _norm((ct*d[0] + st*perp[0], ct*d[1] + st*perp[1], ct*d[2] + st*perp[2]))
    if nd[2] < MIN_APEX_Z:                          # plancher : jamais à plat
        h = math.hypot(nd[0], nd[1])
        if h > 1e-9:
            k = math.sqrt(max(0.0, 1.0 - MIN_APEX_Z * MIN_APEX_Z)) / h
            nd = (nd[0] * k, nd[1] * k, MIN_APEX_Z)
    return nd


# ---------------------------------------------------------------------------
# Topologie de l'arbre de segments (pure)
# ---------------------------------------------------------------------------

def _depths(segs: list) -> list:
    """Profondeur de chaque segment (collet = 0). O(n²) borné par MAX_SEGMENTS."""
    out = [0] * len(segs)
    for i, s in enumerate(segs):
        d, p = 0, s.parent
        while p is not None:
            d += 1
            p = segs[p].parent
        out[i] = d
    return out


def _children(segs: list) -> dict:
    ch = {i: [] for i in range(len(segs))}
    for i, s in enumerate(segs):
        if s.parent is not None:
            ch[s.parent].append(i)
    return ch


def _subtree(root: int, ch: dict) -> list:
    out, stack = [], [root]
    while stack:
        i = stack.pop()
        out.append(i)
        stack.extend(ch[i])
    return out


def _apex_in_subtree(segs: list, ch: dict, depth: list) -> list:
    """True[i] si le sous-arbre enraciné en i contient au moins un apex actif."""
    res = [False] * len(segs)
    for i in sorted(range(len(segs)), key=lambda i: -depth[i]):  # enfants d'abord
        res[i] = segs[i].is_apex or any(res[c] for c in ch[i])
    return res


def _rebuild(plant, kill: set) -> None:
    """Retire les segments de `kill` et réindexe les `parent` survivants."""
    segs = plant.segments
    survivors = [i for i in range(len(segs)) if i not in kill]
    remap = {old: new for new, old in enumerate(survivors)}
    new_segs = []
    for old in survivors:
        s = segs[old]
        s.parent = None if s.parent is None else remap[s.parent]
        new_segs.append(s)
    plant.segments = new_segs


# ---------------------------------------------------------------------------
# Seam de perturbation §F — point d'entrée UNIQUE de l'altération de structure
# ---------------------------------------------------------------------------

def atteindre_segment(plant, segment_id: int, intensite: float) -> None:
    """Seam de perturbation (CONCEPTION_CROISSANCE §F) — l'UNIQUE point d'entrée par
    lequel quoi que ce soit abîme la structure. Le mécanisme ne sait PAS qui :
    `tailler` aujourd'hui ; grêle / ravageur / vent plus tard appelleront le MÊME
    seam. Pur structurel — couche `sim`, déterministe, zéro RNG, zéro Vigueur.

    `intensite` ∈ [0,1] continue :
      - DOUX (< COUPE_NETTE) : baisse SEULEMENT l'auxine locale → lève l'inhibition
        en aval (modélise notching / courbure). La structure reste intacte ; le
        débourrement local peut SUIVRE au prochain `grow_plant` si l'auxine retombe
        sous AUXIN_INHIB_THRESHOLD — émergent, non codé ici.
      - NET (≥ COUPE_NETTE) : écimage = retrait du segment ciblé ET de tout son
        sous-arbre (décision #2 : segment INCLUS). COLLET PROTÉGÉ : si le segment est
        le collet (`parent is None`) on ne retire rien (la baisse d'auxine suffit ;
        `grow_plant` a déjà le rejet de souche s'il ne reste aucun apex).

    Le seam n'écrit QUE l'ÉTAT (auxine / liste de segments). L'architecture de
    réponse (débourrement des bourgeons survivants) ÉMERGE au tick de croissance
    suivant — c'est tout l'intérêt du découplage (philo #2)."""
    segs = plant.segments
    seg = segs[segment_id]
    seg.auxin = max(0.0, seg.auxin - intensite)             # douce : lève l'inhibition
    if intensite >= COUPE_NETTE and seg.parent is not None:  # net, hors collet → écimage
        ch = _children(segs)
        _rebuild(plant, set(_subtree(segment_id, ch)))       # seg INCLUS (décision #2)


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
