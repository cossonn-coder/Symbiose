"""
SYMBIOSE — tools/maquette/organes.py
Organes procéduraux (croissance procédurale, tronçon 5 — §H.2). Feuilles /
fleurs / fruits DESSINÉS PAR ALGORITHME (pas de sprites), accrochés aux segments
selon le profil d'espèce (`organ_site`, `deciduous`, `foliage_density_at`).
Forme/couleur = fonction du STADE d'organe (bouton → fleur → fruit vert → fruit
mûr) et de la SAISON. Déterministe (zéro RNG : tout passe par `_hash_noise`,
philo #3). Pur RENDU read-only : ne touche ni le moteur ni le golden ; les
organes sont reconstructibles à la volée (§J) — pas d'état. Structuré « specs 3D
→ projection iso » pour un futur portage Godot (D24).

Éclaté de l'ex-monolithe `tools/render_structure.py` (Sprint refactor global,
SS⑤). `REPRO_BY_SEASON` reste ré-exporté par `tools/render_structure.py` (le pont
`tools/simserver` l'importe — proxy saisonnier d'organe pour le snapshot).
"""
from __future__ import annotations
import math

from plants import PlantInstance
from fields import _hash_noise

from .iso import _iso, SEED

# Palette par espèce (couleurs SVG). Le décalage saisonnier est appliqué ensuite.
ORGAN_PALETTE = {
    "Tomato":    {"leaf": "#3f9e3a", "flower": "#e8d24a",
                  "fruit_unripe": "#5fae3f", "fruit_ripe": "#d8392a"},
    "AppleTree": {"leaf": "#3f8e3a", "flower": "#f3e0e8",
                  "fruit_unripe": "#82ae4f", "fruit_ripe": "#cc382e"},
}
DEFAULT_PALETTE = {"leaf": "#469a3f", "flower": "#ead85a",
                   "fruit_unripe": "#6fae45", "fruit_ripe": "#cf3a2e"}
AUTUMN_LEAVES = ["#c9a23a", "#c4762a", "#a8392a", "#b8902f", "#9c5a22"]

LEAF_MAX_THICK_CM = 1.6      # au-delà = bois structurel (tronc) → nu, pas de feuilles
LEAF_SPACING_CM   = 11.0     # une feuille tous les ~11 cm de rameau feuillé
LEAF_OFFSET_CM    = 7.0      # déport latéral de la feuille p/r à l'axe du rameau
LEAF_SIZE_CM      = 7.0      # demi-grandeur d'une feuille
MAX_FRUITS        = 10       # plafond d'organes reproducteurs (anti-fouillis)

# Stade d'organe reproducteur visible par saison & espèce (None = aucun).
REPRO_BY_SEASON = {
    "Tomato":    {"printemps": "flower", "ete": "fruit_ripe",
                  "automne": "fruit_ripe", "hiver": None},
    "AppleTree": {"printemps": "flower", "ete": "fruit_unripe",
                  "automne": "fruit_ripe", "hiver": None},
}


def _hex_scale(hexc: str, factor: float) -> str:
    """Éclaircit (factor>1) ou assombrit (factor<1) une couleur #rrggbb, clampé."""
    r = int(hexc[1:3], 16); g = int(hexc[3:5], 16); b = int(hexc[5:7], 16)
    f = lambda v: max(0, min(255, int(v * factor)))
    return f"#{f(r):02x}{f(g):02x}{f(b):02x}"


def _leaf_color(species: str, saison: str, h: float) -> str:
    """Couleur d'une feuille : palette espèce + décalage saisonnier (printemps
    clair, été plein, automne jaune/rouge tiré au hash, hiver = persistant foncé)."""
    base = ORGAN_PALETTE.get(species, DEFAULT_PALETTE)["leaf"]
    if saison == "printemps":
        return _hex_scale(base, 1.25)
    if saison == "automne":
        return AUTUMN_LEAVES[int(h * len(AUTUMN_LEAVES)) % len(AUTUMN_LEAVES)]
    if saison == "hiver":
        return _hex_scale(base, 0.7)          # atteint seulement si persistant (dens>0)
    return base                               # été


def _is_leafy(seg) -> bool:
    """Un segment porte des feuilles s'il est jeune/fin (rameau) ou un apex — le
    bois épais (tronc/charpente) reste nu."""
    return seg.is_apex or seg.thickness_cm <= LEAF_MAX_THICK_CM


def _organ_sites(plant: PlantInstance, organ_site: str) -> list:
    """Points 3D (cm, repère tuile-local) où naissent fleurs/fruits, selon le
    profil (`terminal` = bouts d'apex ; `lateral` = bouts de rameaux latéraux, pas
    le meneur). Plafonné, échantillonné déterministe (anti-fouillis)."""
    apex = [s for s in plant.segments if s.is_apex]
    if not apex:
        return []
    if organ_site == "lateral" and len(apex) > 1:
        # meneur = apex le plus haut (cime) ; on l'exclut → fructification latérale.
        leader = max(apex, key=lambda s: s.base[2] + s.dir[2] * s.length_cm)
        apex = [s for s in apex if s is not leader] or apex
    tips = [(s.base[0] + s.dir[0] * s.length_cm,
             s.base[1] + s.dir[1] * s.length_cm,
             s.base[2] + s.dir[2] * s.length_cm) for s in apex]
    if len(tips) > MAX_FRUITS:                 # sous-échantillonnage régulier
        step = len(tips) / MAX_FRUITS
        tips = [tips[int(i * step)] for i in range(MAX_FRUITS)]
    return tips


def _draw_organs(plant: PlantInstance, saison: str, cx: float, cy: float,
                 foot_x: float, foot_y: float, ppc: float) -> list:
    """SVG des organes (feuilles + fleurs/fruits) projetés en iso, au pied du
    panneau. Déterministe. Dessiné APRÈS le bois (organes par-dessus)."""
    cls = plant.plant_class
    species = cls.__name__
    pal = ORGAN_PALETTE.get(species, DEFAULT_PALETTE)
    out: list = []

    # --- FEUILLES (si feuillage présent cette saison : deciduous+hiver → 0) ---
    if cls.foliage_density_at(plant, saison) > 0.0:
        for i, s in enumerate(plant.segments):
            if not _is_leafy(s):
                continue
            n = max(1, int(s.length_cm / LEAF_SPACING_CM))
            hmag = math.hypot(s.dir[0], s.dir[1])
            perpx, perpy = (-s.dir[1] / hmag, s.dir[0] / hmag) if hmag > 1e-6 else (1.0, 0.0)
            for j in range(n):
                t = (j + 0.5) / n
                px = s.base[0] + s.dir[0] * s.length_cm * t
                py = s.base[1] + s.dir[1] * s.length_cm * t
                pz = s.base[2] + s.dir[2] * s.length_cm * t
                h1 = _hash_noise(SEED, 7, i, j)
                h2 = _hash_noise(SEED, 11, i, j)
                side = 1.0 if h1 < 0.5 else -1.0
                off = LEAF_OFFSET_CM * (0.5 + h2)
                lx = px + perpx * off * side
                ly = py + perpy * off * side
                lz = pz + (h2 - 0.5) * LEAF_OFFSET_CM
                sx, sy = _iso(lx - cx, ly - cy, lz, ppc)
                col = _leaf_color(species, saison, _hash_noise(SEED, 13, i, j))
                r = LEAF_SIZE_CM * ppc
                out.append(f'<ellipse cx="{foot_x+sx:.1f}" cy="{foot_y+sy:.1f}" '
                           f'rx="{r*1.15:.1f}" ry="{r*0.65:.1f}" fill="{col}" '
                           f'fill-opacity="0.92"/>')

    # --- FLEURS / FRUITS (selon organ_site + saison) ---
    organ = REPRO_BY_SEASON.get(species, {}).get(saison)
    if organ:
        for k, (ox3, oy3, oz3) in enumerate(_organ_sites(plant, cls.organ_site)):
            sx, sy = _iso(ox3 - cx, oy3 - cy, oz3, ppc)
            X, Y = foot_x + sx, foot_y + sy
            if organ == "flower":
                # corolle = 5 pétales clairs + cœur
                for p in range(5):
                    a = 2.0 * math.pi * p / 5.0
                    px = X + math.cos(a) * 3.6
                    py = Y + math.sin(a) * 3.6
                    out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.6" '
                               f'fill="{pal["flower"]}"/>')
                out.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="2.0" fill="#e8c63a"/>')
            else:
                col = pal["fruit_ripe"] if organ == "fruit_ripe" else pal["fruit_unripe"]
                rad = 4.6 if organ == "fruit_ripe" else 3.6
                out.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="{rad:.1f}" '
                           f'fill="{col}"/>')
                out.append(f'<circle cx="{X-rad*0.3:.1f}" cy="{Y-rad*0.3:.1f}" '
                           f'r="{rad*0.3:.1f}" fill="#ffffff" fill-opacity="0.45"/>')
    return out
