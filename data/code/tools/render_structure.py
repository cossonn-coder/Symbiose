"""
SYMBIOSE — tools/render_structure.py
Aperçu VISUEL de la structure de croissance procédurale (D29 réorienté).

But : « voir où on en est » SANS attendre le rendu Godot (tronçon 4). On rejoue
le VRAI moteur (sim.growth.grow_plant, source de vérité déterministe) sur
quelques plantes représentatives, puis on projette leurs segments en isométrie
et on émet un SVG (pur Python, zéro dépendance — s'ouvre dans un navigateur ou
Nextcloud). C'est une maquette de ce que rastérisera le tronçon 4 (§H.1), pas le
rendu final : ici on dessine des lignes vectorielles, là-bas des pixels au palier
de zoom. Le bois est brun (épaisseur ∝ thickness_cm), les apex actifs verts ; une
ellipse au sol figure l'empreinte de couronne dérivée (§G).

Usage (depuis data/code/) :
  python3 -m tools.render_structure            # → tools/apercu_structure.svg
  python3 -m tools.render_structure mon.svg    # chemin de sortie explicite
"""
from __future__ import annotations
import copy
import math
import os
import sys

from plants import Tomato, AppleTree, PlantInstance
from fields import LightField, solar_slice, SOLAR_DECLINATION, SOLAR_HOUR_ANGLES, _hash_noise
from world.building import House
from constants import PLOT_CM
import sim.growth as G

SEED = 0x5AB1057E

# Projection iso : (dx,dy,dz) cm relatifs au collet → écran. dz (hauteur) tire
# vers le HAUT (y SVG vers le bas → on soustrait). Cohérent avec §H.1 (la sim vit
# en cm 3D sol, l'affichage projette en iso). cos30 ≈ 0.866, sin30 = 0.5.
PX_PER_CM = 0.42
COS30, SIN30 = 0.8660254, 0.5


def _iso(dx: float, dy: float, dz: float, ppc: float = PX_PER_CM) -> tuple[float, float]:
    return ((dx - dy) * COS30 * ppc,
            ((dx + dy) * SIN30 - dz) * ppc)


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


# ===========================================================================
# MAQUETTE SAISONNIÈRE 3 SECTEURS (sprint maison, tronçon 4)
# ===========================================================================
# But : VOIR l'ombre déterministe de la maison + le phototropisme, sur un cycle
# annuel. Contrairement à l'aperçu ci-dessus (qui pousse « dans le vide »,
# growth_factor=1.0, aucune lumière), ici on rejoue le VRAI moteur dans un monde
# AVEC la maison : chaque spécimen reçoit l'ombre (rectangle balayé §3) et se
# penche vers le clair (phototropisme §4). Outil read-only — zéro logique éco
# nouvelle, zéro RNG, golden intact.
#
# Repère monde (cm), x=Est, y=Sud, Nord en haut. Maison 8×8×6 m centrée en
# (1000,1000) → emprise (600,600)-(1400,1400). À 49°N l'ombre de midi pointe au
# Nord. On place 3 spécimens dans l'anneau de jardin :
#   S  plein soleil  — au Sud du mur (jamais ombré à midi ; espalier en bonus) ;
#   NE intermédiaire — au coin NE, juste à l'EST de la bande d'ombre de midi
#                      (x>1400) → seulement ombré le soir (pénombre partielle) ;
#   NO ombre         — au N-NO, x dans la bande [600,1400] → ombré à midi ET le
#                      matin (umbra). NB : le modèle solaire est SYMÉTRIQUE E-O
#                      (angles horaires ±45°) → l'écart NE/NO vient ici de la
#                      POSITION (profondeur dans la bande d'ombre), pas de
#                      l'orientation. Un vrai contraste matin/soir n'est visible
#                      que sur la PHASE de l'ombre (tranches empilées), pas sur
#                      la lumière journalière intégrée.

# Chaque secteur = une TUILE de l'anneau de jardin qui NE chevauche PAS l'emprise
# de la maison (sinon les plots « sous le toit » à LIGHT_FLOOR créent une fausse
# falaise de gradient → faux phototropisme, cf. piège lisière §7). Le bord de la
# tuile coïncide avec le mur → la différence finie se clampe sur le mur (garden,
# lumineux), pas sur l'ombre interne. L'inclinaison pédagogique naît en LISIÈRE
# d'ombre (pénombre, un côté clair / un côté sombre), jamais en umbra uniforme.
#
# (nom, origin_x, origin_y, rows, cols, plant_lx, plant_ly) — tuile en cm monde,
# collet du spécimen en cm tuile-local. Emprise maison = (600,600)-(1400,1400).
# Lumière reçue mesurée à maturité : S≈1.00 > NE≈0.74 > NO≈0.41 (contraste net).
SECTEURS_MAQ = [
    # Au Sud du mur : plein soleil + espalier, jamais ombré → spécimen le + vigoureux.
    ("S — plein soleil",   600.0, 1400.0, 12, 16, 400.0, 300.0),   # collet monde (1000,1700)
    # Coin NE, juste à l'EST de la bande d'ombre de midi (x>1400) : ombré le soir →
    # pénombre, lisière → l'apex se penche vers l'Est ouvert.
    ("NE — pénombre",     1400.0,    0.0, 12, 12, 160.0, 470.0),   # collet monde (1560,470)
    # Bord OUEST de la bande d'ombre de midi (x≈700, dans [600,1400]) : ombré midi
    # + matin → plus sombre que NE, lisière ouest → se penche vers l'Ouest ouvert.
    ("NO — ombre",         200.0,    0.0, 12, 16, 500.0, 470.0),   # collet monde (700,470)
]

# Saison → semaine ABSOLUE de capture (les 4 saisons de l'année 2 : la tomate a
# déjà une tige lisible dans les 4 panneaux). saison_de(week) maps via
# week_in_year = ((week-1) % 52) + 1 (cf. SAISONS engine : 1-13 / 14-26 / 27-39 /
# 40-52). On pousse en CONTINU et on capture aux 4 jalons → on voit l'ombre
# s'allonger l'hiver ET le plant grandir d'une saison à l'autre.
SAISON_WEEK_MAQ = {
    "printemps": 1 * 52 + 7,    # 59
    "ete":       1 * 52 + 20,   # 72
    "automne":   1 * 52 + 33,   # 85
    "hiver":     1 * 52 + 46,   # 98
}
SAISONS_ORDRE = ["printemps", "ete", "automne", "hiver"]
SAISON_LABEL = {"printemps": "printemps", "ete": "été",
                "automne": "automne", "hiver": "hiver"}

# Échelle de la maquette (px/cm) : ~2× l'aperçu pour que le PLANT (et son
# inclinaison) soit lisible. La maison (8 m) dépasse alors le panneau → seule son
# empreinte proche apparaît, le reste est clippé (c'est l'OMBRE, pas le volume,
# qui porte l'info ; sa LONGUEUR encode déjà la hauteur du mur).
MAQ_PX = 0.85

# Sujet = TOMATE : tige unique dominante → l'inclinaison phototropique se LIT
# proprement (≠ pommier qui branche dans toutes les directions et noie le signal).
# NB : grow_plant seul ne tue pas (la mort froid/mildiou vit dans l'engine, non
# appelé ici) → la tomate traverse l'hiver dans cette maquette read-only.
MAQ_SPECIES = Tomato


def _saison_of(week: int) -> str:
    """Saison d'une semaine absolue (miroir local de engine.saison_de, sans import
    de la couche engine depuis un outil)."""
    wiy = ((week - 1) % 52) + 1
    if wiy < 14:  return "printemps"
    if wiy < 27:  return "ete"
    if wiy < 40:  return "automne"
    return "hiver"


def _grow_sector(cls, ox: float, oy: float, rows: int, cols: int,
                 lx: float, ly: float, house: House) -> dict:
    """Pousse UN spécimen dans la tuile (origine monde ox,oy ; rows×cols plots) au
    point tuile-local (lx,ly), dans un vrai LightField + maison, en CONTINU jusqu'à
    la dernière semaine de capture ; renvoie {saison: (plante_copiée, lumière_reçue)}
    aux 4 jalons saisonniers.

    Réplique la boucle de l'engine : compute lumière → growth_factor (EMA vers
    0.6+0.4·lumière reçue) → grow_plant(…, light_field) qui penche l'apex vers le
    gradient de lumière-sol. Déterministe (SEED fixe, zéro RNG)."""
    p = PlantInstance(plant_class=cls,
                      position=(int(ly // PLOT_CM), int(lx // PLOT_CM)),
                      x_cm=lx, y_cm=ly)
    lf = LightField(rows, cols)
    week_to_saison = {w: s for s, w in SAISON_WEEK_MAQ.items()}
    last_week = max(SAISON_WEEK_MAQ.values())
    snaps: dict = {}
    for week in range(1, last_week + 1):
        saison = _saison_of(week)
        lf.compute([p], saison, house=house, tile_origin=(ox, oy))
        light = lf.light_received(p)
        target_g = 0.6 + 0.4 * light               # même loi que engine._tick_*
        p.growth_factor += (target_g - p.growth_factor) * 0.10
        p.growth_factor = max(0.3, min(1.0, p.growth_factor))
        G.grow_plant(p, SEED, week, lf)
        if week in week_to_saison:
            snaps[week_to_saison[week]] = (copy.deepcopy(p), light)
    return snaps


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


def _shadow_polys(house: House, saison: str,
                  cwx: float, cwy: float) -> list:
    """Polygones d'ombre de la maison au sol, UN par tranche solaire diurne de la
    saison (matin/midi/soir). Chacun = enveloppe convexe de l'emprise + l'emprise
    translatée de hauteur·inv_tan dans la direction d'ombre. Coords ÉCRAN (iso),
    relatives au collet monde (cwx,cwy). Empilés translucides : l'umbra (toujours
    ombrée, ex. plein Nord) ressort plus sombre que la pénombre (un seul créneau)."""
    decl = SOLAR_DECLINATION[saison]
    hx0, hy0, hx1, hy1 = house.footprint_bounds
    corners = [(hx0, hy0), (hx1, hy0), (hx1, hy1), (hx0, hy1)]
    polys = []
    for hour in SOLAR_HOUR_ANGLES:
        s = solar_slice(decl, hour, house.latitude_deg)
        if s is None:
            continue
        sdx, sdy, inv_tan, _w = s
        length = house.height_cm * inv_tan
        pts = corners + [(cx + sdx * length, cy + sdy * length) for cx, cy in corners]
        screen = [_iso(wx - cwx, wy - cwy, 0.0, MAQ_PX) for wx, wy in pts]
        hull = _convex_hull(screen)
        if len(hull) >= 3:
            polys.append(hull)
    return polys


def _house_footprint_at(house: House, cwx: float, cwy: float,
                        fx: float, fy: float) -> str:
    """Empreinte PLATE de la maison au sol (parallélogramme iso), translatée au
    pied du panneau (fx,fy). On ne dessine PAS le volume extrudé : à ce zoom le mur
    (6 m) sortirait du cadre et écraserait la scène ; la hauteur est déjà lisible
    via la LONGUEUR de l'ombre. C'est juste le repère « la maison est là »."""
    hx0, hy0, hx1, hy1 = house.footprint_bounds
    corners = [(hx0, hy0), (hx1, hy0), (hx1, hy1), (hx0, hy1)]
    pts = [_iso(wx - cwx, wy - cwy, 0.0, MAQ_PX) for wx, wy in corners]
    d = " ".join(f"{fx+x:.1f},{fy+y:.1f}" for x, y in pts)
    return (f'<polygon points="{d}" fill="#b8a981" fill-opacity="0.85" '
            f'stroke="#7d7050" stroke-width="1.5"/>')


def _top_shift(plant: PlantInstance) -> float:
    """Déport HORIZONTAL (cm) du point le plus haut par rapport au collet — mesure
    LISIBLE de la courbure de la tige vers la lumière (↑ avec phototropism_strength).
    Robuste au branchage : on suit le SOMMET, pas l'angle d'un apex latéral
    quelconque (un rameau penché ferait un faux 117°)."""
    cx, cy = plant.segments[0].base[0], plant.segments[0].base[1]
    top = None
    for s in plant.segments:
        tz = s.base[2] + s.dir[2] * s.length_cm
        if top is None or tz > top[2]:
            tx = s.base[0] + s.dir[0] * s.length_cm
            ty = s.base[1] + s.dir[1] * s.length_cm
            top = (tx, ty, tz)
    return math.hypot(top[0] - cx, top[1] - cy)


# ===========================================================================
# ORGANES PROCÉDURAUX (croissance procédurale, tronçon 5 — §H.2)
# ===========================================================================
# Feuilles / fleurs / fruits DESSINÉS PAR ALGORITHME (pas de sprites), accrochés
# aux segments selon le profil d'espèce (`organ_site`, `deciduous`,
# `foliage_density_at`). Forme/couleur = fonction du STADE d'organe (bouton →
# fleur → fruit vert → fruit mûr) et de la SAISON. Déterministe (zéro RNG : tout
# passe par `_hash_noise`, philo #3). Pur RENDU read-only : ne touche ni le moteur
# ni le golden ; les organes sont reconstructibles à la volée (§J) — pas d'état.
# Structuré « specs 3D → projection iso » pour un futur portage Godot (D24).

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


def _panel_sector(snap, secteur: str, saison: str, house: House,
                  world_x: float, world_y: float,
                  ox: float, oy: float, pw: float, ph: float, clip_id: str) -> str:
    """Un panneau (secteur × saison) : ombre(s) de la maison empilées + volume
    maison + spécimen penché. (ox,oy) = coin haut-gauche du panneau."""
    plant, light = snap
    cx, cy = plant.segments[0].base[0], plant.segments[0].base[1]   # collet tuile-local
    foot_x = ox + pw / 2.0
    # Collet remonté aux 2/3 : laisse de la place SOUS le plant pour que l'empreinte
    # de la maison (au Sud des secteurs N) apparaisse en bas du cadre (sinon elle se
    # projette hors-panneau vers le bas et la maison n'est visible qu'au secteur S).
    foot_y = oy + ph * 0.66
    # Sol ÉCLAIRÉ (teinte terre chaude) : l'ombre sombre empilée doit s'y détacher
    # — sinon, sur un fond sombre, l'info pédagogique centrale (l'ombre) disparaît.
    out = [f'<clipPath id="{clip_id}"><rect x="{ox+1:.0f}" y="{oy+1:.0f}" '
           f'width="{pw-2:.0f}" height="{ph-2:.0f}" rx="5"/></clipPath>',
           f'<rect x="{ox}" y="{oy}" width="{pw}" height="{ph}" '
           f'fill="#4a432f" stroke="#6d6446" rx="6"/>',
           f'<g clip-path="url(#{clip_id})">']

    # Ombre(s) de la maison : tranches diurnes empilées (umbra/pénombre). Collet
    # monde = (world_x, world_y) (le spécimen est au centre de sa tuile).
    for hull in _shadow_polys(house, saison, world_x, world_y):
        d = " ".join(f"{foot_x+sx:.1f},{foot_y+sy:.1f}" for sx, sy in hull)
        out.append(f'<polygon points="{d}" fill="#11140a" fill-opacity="0.34"/>')

    # Empreinte plate de la maison (repère du projeteur d'ombre), au pied du panneau.
    out.append(_house_footprint_at(house, world_x, world_y, foot_x, foot_y))

    # Spécimen : segments projetés relativement au collet (repère tuile-local =
    # repère monde à l'offset près, qui s'annule pour la plante).
    segs = sorted(plant.segments, key=lambda s: -s.thickness_cm)
    for s in segs:
        bx, by, bz = s.base
        tx = bx + s.dir[0] * s.length_cm
        ty = by + s.dir[1] * s.length_cm
        tz = bz + s.dir[2] * s.length_cm
        x1, y1 = _iso(bx - cx, by - cy, bz, MAQ_PX)
        x2, y2 = _iso(tx - cx, ty - cy, tz, MAQ_PX)
        w = max(0.8, s.thickness_cm * MAQ_PX * 2.2)
        color = "#5ec46a" if s.is_apex else "#7a5230"
        out.append(f'<line x1="{foot_x + x1:.1f}" y1="{foot_y + y1:.1f}" '
                   f'x2="{foot_x + x2:.1f}" y2="{foot_y + y2:.1f}" '
                   f'stroke="{color}" stroke-width="{w:.1f}" stroke-linecap="round"/>')
    # Organes procéduraux (feuilles + fleurs/fruits) par-dessus le bois.
    out.extend(_draw_organs(plant, saison, cx, cy, foot_x, foot_y, MAQ_PX))
    out.append('</g>')

    # Légendes (hors clip).
    cls = plant.plant_class
    h = cls.height_at(plant)
    pli = _top_shift(plant)
    out.append(f'<text x="{ox + 8:.0f}" y="{oy + 17:.0f}" fill="#dfeaf3" '
               f'font-family="monospace" font-size="12">{secteur}</text>')
    out.append(f'<text x="{ox + pw - 8:.0f}" y="{oy + 17:.0f}" fill="#9fc0dc" '
               f'font-family="monospace" font-size="12" text-anchor="end">'
               f'{SAISON_LABEL[saison]}</text>')
    # Fond sombre sous la légende du bas (sinon illisible quand l'empreinte claire
    # de la maison passe dessous, secteurs N).
    out.append(f'<rect x="{ox + 4:.0f}" y="{oy + ph - 21:.0f}" width="{pw - 8:.0f}" '
               f'height="16" fill="#06101a" fill-opacity="0.72" rx="3"/>')
    out.append(f'<text x="{ox + 8:.0f}" y="{oy + ph - 9:.0f}" fill="#bfe0c8" '
               f'font-family="monospace" font-size="10">'
               f'lum={light:.2f}  pli={pli:.0f}cm  h={h:.0f}cm</text>')
    return "\n".join(out)


def render_maquette(path: str, strength: float, etiquette: str) -> None:
    """Grille `secteurs (lignes) × 4 saisons (colonnes)` pour une intensité de
    phototropisme donnée (`strength`). Pousse 3 spécimens (S/NE/NO) en CONTINU
    dans un vrai LightField + maison, capture 4 saisons, projette en iso et émet
    le SVG. `strength` est posé sur l'espèce le temps du rendu puis restauré."""
    house = House()
    orig = MAQ_SPECIES.phototropism_strength
    MAQ_SPECIES.phototropism_strength = strength
    try:
        secteurs = []
        for name, ox, oy, rows, cols, lx, ly in SECTEURS_MAQ:
            snaps = _grow_sector(MAQ_SPECIES, ox, oy, rows, cols, lx, ly, house)
            secteurs.append((name, ox + lx, oy + ly, snaps))   # collet monde
    finally:
        MAQ_SPECIES.phototropism_strength = orig

    pw, ph, gap = 280.0, 300.0, 10.0
    ncols = len(SAISONS_ORDRE)
    nrows = len(secteurs)
    top = 56.0
    W = gap + ncols * (pw + gap)
    H = top + nrows * (ph + gap) + gap
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" '
            f'height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}">',
            f'<rect width="{W:.0f}" height="{H:.0f}" fill="#06101a"/>',
            f'<text x="{gap:.0f}" y="22" fill="#eaf4fb" font-family="monospace" '
            f'font-size="15">SYMBIOSE — maquette saisonnière maison/ombre · '
            f'phototropisme {etiquette} (strength={strength:.2f})</text>',
            f'<text x="{gap:.0f}" y="42" fill="#9fc0dc" font-family="monospace" '
            f'font-size="11">tomate · 3 secteurs × 4 saisons · ombre déterministe '
            f'empilée (umbra sombre / pénombre) · apex vert penché vers le clair · '
            f'lum=lumière reçue, pli=déport horizontal du sommet</text>']
    for ri, (name, wx, wy, snaps) in enumerate(secteurs):
        oy = top + ri * (ph + gap)
        for ci, saison in enumerate(SAISONS_ORDRE):
            ox = gap + ci * (pw + gap)
            clip = f"clip_{ri}_{ci}"
            body.append(_panel_sector(snaps[saison], name, saison, house,
                                      wx, wy, ox, oy, pw, ph, clip))
    body.append('</svg>')
    with open(path, "w") as f:
        f.write("\n".join(body))
    print(f"[maquette {etiquette}] écrit : {path}")
    for name, wx, wy, snaps in secteurs:
        cells = "  ".join(
            f"{SAISON_LABEL[s][:4]}:lum{snaps[s][1]:.2f}/pli{_top_shift(snaps[s][0]):.0f}cm"
            for s in SAISONS_ORDRE)
        print(f"  {name:18s} {cells}")


if __name__ == "__main__":
    here = os.path.dirname(__file__)
    if len(sys.argv) > 1 and sys.argv[1] == "apercu":
        # Ancien aperçu structure (préservé) : python3 -m tools.render_structure apercu [out.svg]
        out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "apercu_structure.svg")
        render(out)
    else:
        # Tronçon 4 : maquette saisonnière, subtil ET marqué (Nico tranche à l'œil).
        render_maquette(os.path.join(here, "maquette_saison_subtil.svg"), 0.10, "subtil")
        render_maquette(os.path.join(here, "maquette_saison_marque.svg"), 0.30, "marqué")
