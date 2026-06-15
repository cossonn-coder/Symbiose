"""
SYMBIOSE — tools/maquette/iso.py
Primitives de projection isométrique et de géométrie partagées par les rendus
SVG (aperçu structure + maquette saisonnière). Éclaté de l'ex-monolithe
`tools/render_structure.py` (Sprint refactor global, SS⑤) : zéro logique éco,
juste de la projection et de la géométrie pures (déterministes).
"""
from __future__ import annotations

SEED = 0x5AB1057E

# Projection iso : (dx,dy,dz) cm relatifs au collet → écran. dz (hauteur) tire
# vers le HAUT (y SVG vers le bas → on soustrait). Cohérent avec §H.1 (la sim vit
# en cm 3D sol, l'affichage projette en iso). cos30 ≈ 0.866, sin30 = 0.5.
PX_PER_CM = 0.42
COS30, SIN30 = 0.8660254, 0.5


def _iso(dx: float, dy: float, dz: float, ppc: float = PX_PER_CM) -> tuple[float, float]:
    return ((dx - dy) * COS30 * ppc,
            ((dx + dy) * SIN30 - dz) * ppc)


def _convex_hull(points: list) -> list:
    """Enveloppe convexe (Andrew monotone chain) d'un nuage de points écran.
    Sert à dessiner l'ombre d'un pavé balayé = enveloppe des 8 coins (emprise +
    emprise translatée par la direction d'ombre)."""
    pts = sorted(set((round(x, 2), round(y, 2)) for x, y in points))
    if len(pts) <= 2:
        return pts
    def cross(o, a, b):
        return (a[0]-o[0]) * (b[1]-o[1]) - (a[1]-o[1]) * (b[0]-o[0])
    lower: list = []
    for q in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    upper: list = []
    for q in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    return lower[:-1] + upper[:-1]
