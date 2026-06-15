"""
SYMBIOSE — sim/growth/geometrie.py
Briques PURES et déterministes (zéro RNG) de la croissance : géométrie 3D des
segments, topologie de l'arbre, et biais phototropique vers la lumière. Aucune
mutation d'état métier ici sauf `_rebuild` (réindexation après élagage/coupe).
"""

from __future__ import annotations
import math

from constants import PLOT_CM
from .constantes import MAX_PHOTOTROPISM_TILT, MIN_APEX_Z

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
