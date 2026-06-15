"""
SYMBIOSE — tools/maquette/apercu.py
Aperçu VISUEL de la structure de croissance procédurale (D29 réorienté).

But : « voir où on en est » SANS attendre le rendu Godot (tronçon 4). On rejoue
le VRAI moteur (sim.growth.grow_plant, source de vérité déterministe) sur
quelques plantes représentatives, puis on projette leurs segments en isométrie
et on émet un SVG (pur Python, zéro dépendance — s'ouvre dans un navigateur ou
Nextcloud). C'est une maquette de ce que rastérisera le tronçon 4 (§H.1), pas le
rendu final : ici on dessine des lignes vectorielles, là-bas des pixels au palier
de zoom. Le bois est brun (épaisseur ∝ thickness_cm), les apex actifs verts ; une
ellipse au sol figure l'empreinte de couronne dérivée (§G).

Éclaté de l'ex-monolithe `tools/render_structure.py` (Sprint refactor global,
SS⑤). `render` reste ré-exporté par `tools/render_structure.py` (CLI `apercu`).
"""
from __future__ import annotations

from plants import Tomato, AppleTree, PlantInstance
import sim.growth as G

from .iso import _iso, SEED, PX_PER_CM, COS30, SIN30
from .organes import _draw_organs


def _grow(cls, n: int, week_mode: str = "real") -> PlantInstance:
    """Rejoue grow_plant n ticks (déterministe). week_mode 'real' = cycle
    saisonnier (1+k) ; 'summer' = été fixe (croissance non ralentie)."""
    p = PlantInstance(plant_class=cls, position=(2, 2))
    p.growth_factor = 1.0
    for k in range(n):
        week = (1 + k) if week_mode == "real" else 20
        G.grow_plant(p, SEED, week)
    return p


def _panel(plant: PlantInstance, title: str, ox: float, oy: float,
           pw: float, ph: float) -> str:
    """Un panneau SVG pour une plante : segments projetés + ombre de couronne +
    légende. (ox,oy) = coin haut-gauche ; le collet est placé en bas-centre."""
    cls = plant.plant_class
    cx, cy = plant.segments[0].base[0], plant.segments[0].base[1]
    foot_x = ox + pw / 2.0           # collet au centre horizontal
    foot_y = oy + ph - 26.0          # collet près du bas (place pour la légende)
    out = [f'<rect x="{ox}" y="{oy}" width="{pw}" height="{ph}" '
           f'fill="#0d1b12" stroke="#1f3b2a" rx="6"/>']

    # Ombre au sol = empreinte de couronne dérivée (§G), ellipse iso d'un disque.
    cr = cls.canopy_radius_at(plant)
    ex, ey = cr * COS30 * PX_PER_CM * 2.0, cr * SIN30 * PX_PER_CM * 2.0
    out.append(f'<ellipse cx="{foot_x:.1f}" cy="{foot_y:.1f}" '
               f'rx="{ex:.1f}" ry="{ey:.1f}" fill="#14331f" opacity="0.6"/>')

    # Segments : du plus profond (bois épais) au plus fin. Tri par épaisseur pour
    # que les fines brindilles passent au-dessus du tronc.
    segs = sorted(plant.segments, key=lambda s: -s.thickness_cm)
    for s in segs:
        bx, by, bz = s.base
        tx = bx + s.dir[0] * s.length_cm
        ty = by + s.dir[1] * s.length_cm
        tz = bz + s.dir[2] * s.length_cm
        x1, y1 = _iso(bx - cx, by - cy, bz)
        x2, y2 = _iso(tx - cx, ty - cy, tz)
        w = max(0.8, s.thickness_cm * PX_PER_CM * 2.2)
        color = "#5ec46a" if s.is_apex else "#7a5230"   # apex vert vif / bois brun
        out.append(f'<line x1="{foot_x + x1:.1f}" y1="{foot_y + y1:.1f}" '
                   f'x2="{foot_x + x2:.1f}" y2="{foot_y + y2:.1f}" '
                   f'stroke="{color}" stroke-width="{w:.1f}" stroke-linecap="round"/>')
    # Organes procéduraux (tronçon 5), saison « été » par défaut pour l'aperçu.
    out.extend(_draw_organs(plant, "ete", cx, cy, foot_x, foot_y, PX_PER_CM))

    h = cls.height_at(plant)
    nseg = len(plant.segments)
    out.append(f'<text x="{ox + 8:.0f}" y="{oy + 18:.0f}" fill="#cfe8d4" '
               f'font-family="monospace" font-size="13">{title}</text>')
    out.append(f'<text x="{ox + 8:.0f}" y="{oy + ph - 8:.0f}" fill="#8fb89a" '
               f'font-family="monospace" font-size="11">'
               f'h={h:.0f}cm couronne={cr:.0f}cm seg={nseg}</text>')
    return "\n".join(out)


def render(path: str) -> None:
    # Plantes représentatives (toutes déterministes via grow_plant).
    specimens = [
        (_grow(Tomato, 80, "summer"),   "Tomate · flèche mûre"),
        (_grow(AppleTree, 3 * 52),      "Pommier · an 3 (jeune)"),
        (_grow(AppleTree, 7 * 52),      "Pommier · an 7 (étalement)"),
        (_grow(AppleTree, 10 * 52),     "Pommier · an 10 (etale)"),
    ]
    pw, ph, gap = 300.0, 340.0, 12.0
    cols = len(specimens)
    W = gap + cols * (pw + gap)
    H = gap + ph + gap + 30
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" '
            f'height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}">',
            f'<rect width="{W:.0f}" height="{H:.0f}" fill="#081109"/>',
            f'<text x="{gap:.0f}" y="20" fill="#e6f3ea" font-family="monospace" '
            f'font-size="15">SYMBIOSE — structure procédurale (source Python, '
            f'déterministe) · bois brun, apex vert, ombre = couronne dérivée</text>']
    for i, (plant, title) in enumerate(specimens):
        ox = gap + i * (pw + gap)
        body.append(_panel(plant, title, ox, 30 + gap, pw, ph))
    body.append('</svg>')
    with open(path, "w") as f:
        f.write("\n".join(body))
    print(f"[render] aperçu écrit : {path}")
    for plant, title in specimens:
        cls = plant.plant_class
        print(f"  {title:32s} h={cls.height_at(plant):6.0f}cm "
              f"couronne={cls.canopy_radius_at(plant):5.0f}cm "
              f"seg={len(plant.segments):3d}")
