"""
SYMBIOSE — tools/maquette/secteurs.py
MAQUETTE SAISONNIÈRE 3 SECTEURS (sprint maison, tronçon 4).

But : VOIR l'ombre déterministe de la maison + le phototropisme, sur un cycle
annuel. Contrairement à l'aperçu (qui pousse « dans le vide », growth_factor=1.0,
aucune lumière), ici on rejoue le VRAI moteur dans un monde AVEC la maison :
chaque spécimen reçoit l'ombre (rectangle balayé §3) et se penche vers le clair
(phototropisme §4). Outil read-only — zéro logique éco nouvelle, zéro RNG, golden
intact.

Repère monde (cm), x=Est, y=Sud, Nord en haut. Maison 8×8×6 m centrée en
(1000,1000) → emprise (600,600)-(1400,1400). À 49°N l'ombre de midi pointe au
Nord. On place 3 spécimens dans l'anneau de jardin :
  S  plein soleil  — au Sud du mur (jamais ombré à midi ; espalier en bonus) ;
  NE intermédiaire — au coin NE, juste à l'EST de la bande d'ombre de midi
                     (x>1400) → seulement ombré le soir (pénombre partielle) ;
  NO ombre         — au N-NO, x dans la bande [600,1400] → ombré à midi ET le
                     matin (umbra). NB : le modèle solaire est SYMÉTRIQUE E-O
                     (angles horaires ±45°) → l'écart NE/NO vient ici de la
                     POSITION (profondeur dans la bande d'ombre), pas de
                     l'orientation. Un vrai contraste matin/soir n'est visible
                     que sur la PHASE de l'ombre (tranches empilées), pas sur
                     la lumière journalière intégrée.

Éclaté de l'ex-monolithe `tools/render_structure.py` (Sprint refactor global,
SS⑤). Plusieurs symboles restent ré-exportés par `tools/render_structure.py`
(`SECTEURS_MAQ`, `SAISON_WEEK_MAQ`, `SAISONS_ORDRE`, `MAQ_SPECIES`,
`_grow_sector`) — `tools/export_structure.py` les importe pour la MÊME scène.
"""
from __future__ import annotations
import copy
import math

from plants import Tomato, PlantInstance
from fields import LightField, solar_slice, SOLAR_DECLINATION, SOLAR_HOUR_ANGLES
from world.building import House
from constants import PLOT_CM
import sim.growth as G

from .iso import _iso, _convex_hull, SEED
from .organes import _draw_organs

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
