"""
SYMBIOSE — fields/light.py
LightField v2 — ombres-capsules astronomiques calculées analytiquement
(pixel-libre). Position solaire ~49°N, 4 saisons × 3 tranches diurnes +
intégrale journalière, cumul multiplicatif des opacités, auto-ombrage exclu.
"""

from __future__ import annotations
import math

from constants import PLOT_CM
from fields.grids import GridField
from fields.light_index import ReceiverIndex

# --- Éclairement astronomique (LightField v2 — ombres-capsules analytiques) ---
LATITUDE_DEG = 49.0          # ~Normandie / 49°N
LIGHT_FLOOR  = 0.15          # plancher de lumière diffuse (rien ne descend à 0)

# Déclinaison solaire par saison (équinoxes ≈ 0°, solstices ≈ ±23.4°)
SOLAR_DECLINATION = {"printemps": 0.0, "ete": 23.4, "automne": 0.0, "hiver": -23.4}

# Trois tranches diurnes éclairées (la nuit n'apporte que le plancher diffus).
# Angle horaire H : 0 = midi solaire, négatif le matin, positif le soir.
SOLAR_HOUR_ANGLES = (-45.0, 0.0, 45.0)   # matin · midi · soir

# Échantillons sous la canopée d'une plante pour moyenner sa lumière reçue
# (centre + 4 points à 0.6·rayon) — capte l'ombrage partiel d'un voisin plus haut.
CANOPY_SAMPLE_FRAC = 0.6

# Portée de l'effet espalier : le sol DEVANT un mur ensoleillé reçoit la lumière
# réfléchie (albédo) sur ≈ 2,5 m, falloff linéaire avec la distance au mur (§3).
WALL_ALBEDO_RADIUS_CM = 250.0

# Densité d'ombre d'un squelette post-mortem DEBOUT (décompo·compost ②, phase B.3) :
# un tronc nu + brindilles projette une ombre DÉGRESSIVE, pas la canopée pleine. Le
# squelette `couchee` (au sol) n'ombre plus (exclu des obstacles). Défini ici (et non
# dans ecofields) pour respecter les couches : ecofields importe light, pas l'inverse.
SILHOUETTE_SECHE = 0.30

# --- LOD des émetteurs d'ombre (D67) ---
# Seuil de POUVOIR OMBRAGEANT sous lequel une plante REÇOIT toujours la lumière mais
# n'ÉMET plus d'ombre (retirée des deux boucles géométriques de `compute`). Pouvoir =
# hauteur × rayon canopée × densité foliaire (les 3 déjà dans `infos`, zéro état neuf,
# déterministe). À 0.0 le LOD est DORMANT (`emitters == infos` ordre exact → bit-identique,
# invariant D3 verrouillé par `tests/test_lod_ombre`). Global de module : le banc
# `tools/diag_lod_ombre.py` le monkeypatche (relu à CHAQUE `compute`).
#
# VALEUR ACTIVE = 37.5 (calibrée au tronçon ②, 2026-07-08, `diag_lod_ombre`). La
# distribution du pouvoir à l'an 6 (config=full) montre une falaise nette : ~80 % des
# plantes sont des semis (pouvoir ~26-37, p80=37.4), les structurantes sont ≥ 262 (p90).
# 37.5 coupe TOUT le cluster de semis sans mordre sur les plantes structurantes → gain
# ~+18 % ms/tick, dérive `light_received` moyenne 0.68 % (négligeable), vis B préservée
# (self-thinning intact), N plateau 689 dans la bande D5 [521, 704]. Un seuil plus haut
# (ex. 299) gagne peu de plus mais triple la dérive et divise la vis B par 2 (coupe des
# structurantes) → écarté. Golden RE-FIGÉ ici (dérive localisée, cf. tronçon ②).
SHADING_POWER_MIN = 37.5


def solar_slice(decl_deg: float, hour_angle_deg: float,
                lat_deg: float = LATITUDE_DEG):
    """
    Position solaire pour une (déclinaison, angle horaire) → caractéristiques de
    l'ombre projetée, dans le repère sol top-down (x = Est, y = Sud, Nord en haut).

    Retourne (shadow_dx, shadow_dy, inv_tan, weight) où (shadow_dx, shadow_dy)
    est la direction unitaire de l'ombre, inv_tan = 1/tan(élévation) (longueur
    d'ombre = hauteur × inv_tan), weight = sin(élévation) (intensité solaire).
    Retourne None si le soleil est sous l'horizon (tranche non éclairée).
    """
    phi = math.radians(lat_deg)
    dec = math.radians(decl_deg)
    H   = math.radians(hour_angle_deg)

    sin_elev = math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(H)
    if sin_elev <= 1e-3:
        return None                      # soleil sous l'horizon
    elev = math.asin(max(-1.0, min(1.0, sin_elev)))
    cos_elev = math.cos(elev)

    # Azimut depuis le Nord, sens horaire (90°=Est, 180°=Sud, 270°=Ouest).
    cos_az = (math.sin(dec) - sin_elev * math.sin(phi)) / (cos_elev * math.cos(phi))
    az = math.acos(max(-1.0, min(1.0, cos_az)))
    if hour_angle_deg > 0.0:             # après-midi → soleil à l'Ouest
        az = 2.0 * math.pi - az

    # L'ombre pointe à l'opposé du soleil. Sol : x=Est, y=Sud (donc Nord = -y).
    shadow_dx = -math.sin(az)
    shadow_dy =  math.cos(az)            # midi (az=π) → (0,-1) = vers le Nord (haut)
    inv_tan = cos_elev / sin_elev
    return (shadow_dx, shadow_dy, inv_tan, sin_elev)


def _point_in_capsule(px: float, py: float,
                      cx: float, cy: float,
                      dx: float, dy: float, length: float, radius: float) -> bool:
    """Le point (px,py) est-il dans la capsule = disque de rayon `radius` glissé
    du centre C=(cx,cy) le long de (dx,dy)·length ? (distance au segment ≤ rayon)"""
    bx = cx + dx * length
    by = cy + dy * length
    abx = bx - cx
    aby = by - cy
    ab2 = abx * abx + aby * aby
    if ab2 <= 1e-9:
        t = 0.0
    else:
        t = (px - cx) * abx + (py - cy) * aby
        t = 0.0 if t < 0.0 else (ab2 if t > ab2 else t) / ab2
    qx = cx + abx * t
    qy = cy + aby * t
    return (px - qx) ** 2 + (py - qy) ** 2 <= radius * radius


def _point_in_swept_rect(px: float, py: float,
                         x0: float, y0: float, x1: float, y1: float,
                         dx: float, dy: float, length: float) -> bool:
    """Le point (px,py) est-il dans le rectangle [x0,x1]×[y0,y1] BALAYÉ le long de
    (dx,dy) sur `length` ? (ombre d'un pavé opaque = la maison, §3).

    Analytique, sans raster : le point est dans le balayage ssi il existe
    s∈[0,length] tel que (px−s·dx, py−s·dy) retombe dans le rectangle. Sur chaque
    axe la contrainte donne un intervalle de s ; on intersecte avec [0,length]."""
    s_lo, s_hi = 0.0, length
    if abs(dx) < 1e-12:
        if not (x0 <= px <= x1):
            return False
    else:
        a, b = (px - x1) / dx, (px - x0) / dx
        lo, hi = (a, b) if a <= b else (b, a)
        if lo > s_lo: s_lo = lo
        if hi < s_hi: s_hi = hi
        if s_lo > s_hi:
            return False
    if abs(dy) < 1e-12:
        if not (y0 <= py <= y1):
            return False
    else:
        a, b = (py - y1) / dy, (py - y0) / dy
        lo, hi = (a, b) if a <= b else (b, a)
        if lo > s_lo: s_lo = lo
        if hi < s_hi: s_hi = hi
        if s_lo > s_hi:
            return False
    return s_lo <= s_hi


def _wall_albedo_bonus(wx: float, wy: float,
                       x0: float, y0: float, x1: float, y1: float,
                       albedo: float, radius: float,
                       sun_dx: float, sun_dy: float) -> float:
    """Surplus de lumière réfléchie sur le sol DEVANT une face de mur ENSOLEILLÉE
    (effet espalier, §3). Repère : x=Est, y=Sud. (sun_dx,sun_dy) = direction du
    soleil (= −direction d'ombre). Une face n'est éclairée que si le soleil la
    frappe (normale·soleil > 0). Contribution bornée, falloff linéaire avec la
    distance perpendiculaire au mur, nulle au-delà de `radius`."""
    bonus = 0.0
    # face : (normale_x, normale_y, distance_devant_le_mur, dans_l'extension_latérale)
    faces = (
        ( 0.0,  1.0, wy - y1, x0 <= wx <= x1),   # Sud   (mur y=y1)
        ( 0.0, -1.0, y0 - wy, x0 <= wx <= x1),   # Nord  (mur y=y0)
        ( 1.0,  0.0, wx - x1, y0 <= wy <= y1),   # Est   (mur x=x1)
        (-1.0,  0.0, x0 - wx, y0 <= wy <= y1),   # Ouest (mur x=x0)
    )
    for nx, ny, perp, in_strip in faces:
        if not in_strip or perp <= 0.0 or perp > radius:
            continue
        lit = nx * sun_dx + ny * sun_dy          # face éclairée si le soleil la frappe
        if lit <= 0.0:
            continue
        bonus += albedo * lit * (1.0 - perp / radius)
    return bonus


class LightField(GridField):
    """
    Champ de lumière v2 — ombres-capsules astronomiques calculées analytiquement
    (pas de raster pixel : on évalue la lumière aux seuls points utiles).

    Deux produits par tick :
      • lumière-sol par plot (grille héritée, lue via at_plot) → germination, niche,
        banque de graines ; subit TOUTES les ombres + plancher diffus.
      • lumière reçue par plante (self.received, via light_received) → photosynthèse
        et avancement de stade ; filtrée par les seuls voisins PLUS HAUTS (l'algo
        tri-hauteur-décroissante exclut l'auto-ombrage).

    Cumul multiplicatif des opacités (foliage_density), intégrale journalière =
    moyenne des tranches éclairées pondérée par l'intensité solaire (sin élévation).
    """

    def __init__(self, rows: int, cols: int):
        super().__init__(rows, cols, initial=1.0, max_val=1.0)
        self.received: dict[int, float] = {}
        self._sun_cache: dict[str, list] = {}
        self._geom_key = None            # empreinte géométrique du dernier compute

    def _sun_slices(self, saison: str) -> list:
        """Tranches éclairées (cachées) pour la saison : liste de
        (shadow_dx, shadow_dy, inv_tan, weight)."""
        slices = self._sun_cache.get(saison)
        if slices is None:
            decl = SOLAR_DECLINATION.get(saison, 0.0)
            slices = [s for H in SOLAR_HOUR_ANGLES
                      if (s := solar_slice(decl, H)) is not None]
            self._sun_cache[saison] = slices
        return slices

    def light_received(self, plant) -> float:
        """Intégrale journalière de lumière reçue par la plante (défaut plein soleil)."""
        return self.received.get(id(plant), 1.0)

    def compute(self, plants: list, saison: str,
                house=None, tile_origin: tuple = (0.0, 0.0)) -> list[str]:
        """Recalcule lumière-sol (grille) + lumière reçue par plante pour ce tick.

        `house` : config `House` (pavé opaque, seul obstacle GLOBAL, option B §1)
        ou None. Si fournie, son **ombre** (rectangle balayé §3) et l'**albédo** de
        ses murs ensoleillés (espalier §3) sont injectés, en convertissant chaque
        plot/échantillon en coordonnées MONDE via `tile_origin` (offset cm de la
        tuile). **None → comportement historique strictement inchangé** (le golden
        smoke test des autres scénarios reste bit-identique)."""
        slices = self._sun_slices(saison)
        alive = [p for p in plants if p.is_alive]

        # Snapshot géométrique de chaque plante : (plante, x, y, hauteur, rayon, densité)
        infos = []
        for p in alive:
            cls = p.plant_class
            infos.append((p, p.x_cm, p.y_cm, p.current_height,
                          cls.canopy_radius_at(p), cls.foliage_density_at(p, saison)))
        # Squelettes post-mortem DEBOUT (②B.3) : ombre dégressive d'un tronc nu
        # (densité SILHOUETTE_SECHE), pas la canopée pleine. Les couchés (au sol) et
        # les morts non marqués sont exclus → ombre nulle. Sans squelette ligneux
        # debout (cas du golden 2 ans), `infos` est strictement inchangé.
        for p in plants:
            if getattr(p, "morte", False) and p.stade_mort == "seche":
                cls = p.plant_class
                infos.append((p, p.x_cm, p.y_cm, p.current_height,
                              cls.canopy_radius_at(p), SILHOUETTE_SECHE))

        # --- LOD émetteur/récepteur (D67) ---
        # `receivers` = TOUTES les plantes (la réception ne change jamais) ;
        # `emitters` = celles dont le pouvoir ombrageant (h × rayon × densité) atteint
        # le seuil (préserve l'ORDRE de `infos`). Seuls les émetteurs projettent une
        # ombre : les scatters (boucle reçue et lumière-sol) itèrent `emitters`,
        # la boucle reçue applique à `receivers`. À SHADING_POWER_MIN = 0.0,
        # `emitters == infos` dans l'ordre exact → bit-identique (invariant D3).
        receivers = infos
        emitters = [t for t in infos if t[3] * t[4] * t[5] >= SHADING_POWER_MIN]

        # --- Géométrie maison (espace MONDE), si présente ---
        ox, oy = tile_origin
        hx0 = hy0 = hx1 = hy1 = h_height = wall_albedo = 0.0
        if house is not None:
            hx0, hy0, hx1, hy1 = house.footprint_bounds
            h_height    = house.height_cm
            wall_albedo = house.wall_albedo

        # --- Cache géométrique (temps figé) ---
        # Empreinte PURE de l'état géométrique : saison, maison, offset de tuile,
        # et pour chaque obstacle (x, y, hauteur, rayon, densité — flottants bruts
        # reproductibles, ORDRE de `infos` déterministe). Pas de `id()`. En temps
        # figé (planification) rien ne bouge → HIT → on réutilise self.data /
        # self.received tels quels. En saison la croissance change la géométrie
        # chaque semaine → MISS → recompute → golden neutre par construction.
        geom_key = (saison, ox, oy, hx0, hy0, hx1, hy1, h_height, wall_albedo,
                    tuple((x, y, h, r, d) for _, x, y, h, r, d in infos))
        if geom_key == self._geom_key:
            return []                        # géométrie inchangée : champ réutilisé
        self._geom_key = geom_key

        self.received = {}
        if not slices:                       # nuit polaire théorique : plancher partout
            for r in range(self.rows):
                for c in range(self.cols):
                    self.data[r][c] = LIGHT_FLOOR
            for p, *_ in receivers:
                self.received[id(p)] = LIGHT_FLOOR
            return []

        total_w = sum(w for _, _, _, w in slices)

        # --- Lumière reçue par plante (ombres des voisins plus hauts + maison) ---
        # SCATTER (tronçon ②, miroir de la lumière-sol D32) — au lieu de faire
        # parcourir à CHAQUE échantillon TOUS les émetteurs plus hauts (gather,
        # O(N²)), chaque émetteur ne VISITE que les échantillons de la bbox de sa
        # capsule, via un `ReceiverIndex` construit sur les échantillons ACTIFS de
        # la tranche. Un échantillon hors bbox renvoyait de toute façon
        # `_point_in_capsule == False` → l'élaguer est BIT-IDENTIQUE (golden intact).
        #
        # Ordre des facteurs : on itère `order` (hauteur décroissante) tel quel,
        # donc chaque échantillon accumule ses (1-qd) dans l'ORDRE EXACT du gather
        # (qui re-triait les candidats par rang de `order`) → produit `att` inchangé.
        order = sorted(emitters, key=lambda t: t[3], reverse=True)  # plus haut → plus bas

        # Pré-calcul des 5 échantillons de chaque récepteur (une seule fois).
        # `rec_samples[ref] = (ph, [(sx0,sy0), … 5 points])`.
        rec_samples = {}
        for p, px, py, ph, pr, pd in receivers:
            d = pr * CANOPY_SAMPLE_FRAC
            rec_samples[id(p)] = (ph, (
                (px, py), (px + d, py), (px - d, py), (px, py + d), (px, py - d)))

        acc = {ref: 0.0 for ref in rec_samples}
        for sdx, sdy, inv_tan, w in slices:
            h_len = h_height * inv_tan
            # 1+2. Échantillons ACTIFS = non masqués par la maison. `att[(ref,k)]`
            # init 1.0 uniquement pour les actifs (les masqués comptent comme 0,
            # exclus de la somme → répliquent le `continue` du gather).
            att = {}
            index_samples = []
            for ref, (ph, samples) in rec_samples.items():
                for k in range(5):
                    sx, sy = samples[k]
                    if house is not None and _point_in_swept_rect(
                            sx + ox, sy + oy, hx0, hy0, hx1, hy1, sdx, sdy, h_len):
                        continue             # masqué → att=0 (hors somme)
                    att[(ref, k)] = 1.0
                    index_samples.append((ph, (ref, k), sx, sy))
            rindex = ReceiverIndex(index_samples)
            # 3. Chaque émetteur (déjà hauteur décroissante) atténue les
            # échantillons couverts par sa capsule.
            for q, qx, qy, qh, qr, qd in order:
                if qd <= 0.0:
                    continue
                length = qh * inv_tan
                bx = qx + sdx * length
                by = qy + sdy * length
                xmin = (qx if qx < bx else bx) - qr
                xmax = (qx if qx > bx else bx) + qr
                ymin = (qy if qy < by else by) - qr
                ymax = (qy if qy > by else by) + qr
                factor = 1.0 - qd
                for ph, key, sx, sy in rindex.in_bbox(xmin, xmax, ymin, ymax):
                    if qh <= ph:
                        continue             # auto-ombrage exclu (même test que gather)
                    if _point_in_capsule(sx, sy, qx, qy, sdx, sdy, length, qr):
                        att[key] *= factor
            # 4. Moyenne par récepteur : somme des att actifs / 5 (les masqués
            # comptent 0 → division par 5, PAS par le nombre d'actifs).
            for ref in rec_samples:
                att_sum = 0.0
                for k in range(5):
                    v = att.get((ref, k))
                    if v is not None:
                        att_sum += v
                acc[ref] += max(LIGHT_FLOOR, att_sum / 5) * w
        for ref in rec_samples:
            self.received[ref] = acc[ref] / total_w

        # --- Lumière-sol par plot (ombres plantes + maison + albédo + plancher) ---
        # SCATTER (D32) — au lieu de tester chaque plot contre chaque plante
        # (gather, aucun élagage), chaque ombre ne VISITE que les plots de sa
        # bounding-box de capsule. Un plot hors bbox renvoie de toute façon False
        # dans `_point_in_capsule` → l'élaguer est BIT-IDENTIQUE (golden intact).
        #
        # Pour chaque tranche, on accumule par plot l'atténuation MULTIPLICATIVE
        # des plantes (init 1.0), en parcourant `infos` dans l'ordre EXACT de la
        # version gather (produit de facteurs (1-qd) dans le même ordre par plot →
        # mêmes flottants bit à bit). Maison (ombre pleine), albédo et plancher
        # restent des termes PAR-PLOT indépendants des plantes → passe finale.
        rows, cols = self.rows, self.cols
        acc_grid = [[0.0] * cols for _ in range(rows)]
        for sdx, sdy, inv_tan, w in slices:
            # Produit des ombres-plantes par plot (1.0 = plein soleil).
            att_grid = [[1.0] * cols for _ in range(rows)]
            for q, qx, qy, qh, qr, qd in emitters:
                if qd <= 0.0:
                    continue
                length = qh * inv_tan
                factor = 1.0 - qd
                bx = qx + sdx * length            # extrémité de la capsule
                by = qy + sdy * length
                xmin = (qx if qx < bx else bx) - qr   # bbox = sur-ensemble strict
                xmax = (qx if qx > bx else bx) + qr   # (marge ±qr sur x ET y)
                ymin = (qy if qy < by else by) - qr
                ymax = (qy if qy > by else by) + qr
                c0 = int(xmin // PLOT_CM); c1 = int(xmax // PLOT_CM)
                r0 = int(ymin // PLOT_CM); r1 = int(ymax // PLOT_CM)
                if c0 < 0: c0 = 0
                if r0 < 0: r0 = 0
                if c1 > cols - 1: c1 = cols - 1
                if r1 > rows - 1: r1 = rows - 1
                for r in range(r0, r1 + 1):
                    cy = r * PLOT_CM + PLOT_CM / 2
                    row_att = att_grid[r]
                    for c in range(c0, c1 + 1):
                        cx = c * PLOT_CM + PLOT_CM / 2
                        if _point_in_capsule(cx, cy, qx, qy, sdx, sdy, length, qr):
                            row_att[c] *= factor
            # Passe par-plot : maison (ombre pleine AVANT le produit plantes →
            # un plot sous la maison ignore les capsules), albédo, pondération.
            h_len = h_height * inv_tan
            for r in range(rows):
                cy = r * PLOT_CM + PLOT_CM / 2
                wy = cy + oy
                row_att = att_grid[r]
                row_acc = acc_grid[r]
                for c in range(cols):
                    if house is not None and _point_in_swept_rect(
                            c * PLOT_CM + PLOT_CM / 2 + ox, wy,
                            hx0, hy0, hx1, hy1, sdx, sdy, h_len):
                        att = 0.0            # sous la maison : ombre pleine
                    else:
                        att = row_att[c]
                    if house is not None and wall_albedo > 0.0:
                        att += _wall_albedo_bonus(
                            c * PLOT_CM + PLOT_CM / 2 + ox, wy,
                            hx0, hy0, hx1, hy1,
                            wall_albedo, WALL_ALBEDO_RADIUS_CM, -sdx, -sdy)
                    row_acc[c] += att * w
        # Plafond [LIGHT_FLOOR, 1.0] : préserve le contrat [0,1] de la lumière-sol
        # (no-op sans maison, acc/total_w ≤ 1).
        for r in range(rows):
            row_acc = acc_grid[r]
            dst = self.data[r]
            for c in range(cols):
                v = row_acc[c] / total_w
                dst[c] = 1.0 if v > 1.0 else (LIGHT_FLOOR if v < LIGHT_FLOOR else v)
        return []
