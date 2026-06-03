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

    def compute(self, plants: list, saison: str) -> list[str]:
        """Recalcule lumière-sol (grille) + lumière reçue par plante pour ce tick."""
        slices = self._sun_slices(saison)
        alive = [p for p in plants if p.is_alive]

        # Snapshot géométrique de chaque plante : (plante, x, y, hauteur, rayon, densité)
        infos = []
        for p in alive:
            cls = p.plant_class
            infos.append((p, p.x_cm, p.y_cm, p.current_height,
                          cls.canopy_radius_at(p), cls.foliage_density_at(p, saison)))

        self.received = {}
        if not slices:                       # nuit polaire théorique : plancher partout
            for r in range(self.rows):
                for c in range(self.cols):
                    self.data[r][c] = LIGHT_FLOOR
            for p, *_ in infos:
                self.received[id(p)] = LIGHT_FLOOR
            return []

        total_w = sum(w for _, _, _, w in slices)

        # --- Lumière reçue par plante (ombres des seuls voisins plus hauts) ---
        order = sorted(infos, key=lambda t: t[3], reverse=True)  # plus haut → plus bas
        for p, px, py, ph, pr, pd in infos:
            d = pr * CANOPY_SAMPLE_FRAC
            samples = ((px, py), (px + d, py), (px - d, py), (px, py + d), (px, py - d))
            acc = 0.0
            for sdx, sdy, inv_tan, w in slices:
                att_sum = 0.0
                for sx, sy in samples:
                    att = 1.0
                    for q, qx, qy, qh, qr, qd in order:
                        if qh <= ph:
                            break            # le reste est plus court ou égal → pas d'ombre
                        if qd <= 0.0:
                            continue
                        if _point_in_capsule(sx, sy, qx, qy, sdx, sdy, qh * inv_tan, qr):
                            att *= (1.0 - qd)
                    att_sum += att
                light_slice = max(LIGHT_FLOOR, att_sum / len(samples))
                acc += light_slice * w
            self.received[id(p)] = acc / total_w

        # --- Lumière-sol par plot (toutes les ombres + plancher) ---
        for r in range(self.rows):
            cy = r * PLOT_CM + PLOT_CM / 2
            for c in range(self.cols):
                cx = c * PLOT_CM + PLOT_CM / 2
                acc = 0.0
                for sdx, sdy, inv_tan, w in slices:
                    att = 1.0
                    for q, qx, qy, qh, qr, qd in infos:
                        if qd <= 0.0:
                            continue
                        if _point_in_capsule(cx, cy, qx, qy, sdx, sdy, qh * inv_tan, qr):
                            att *= (1.0 - qd)
                    acc += att * w
                self.data[r][c] = max(LIGHT_FLOOR, acc / total_w)
        return []
