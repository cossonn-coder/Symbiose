"""
SYMBIOSE — world/building.py
Config de terrain : la MAISON centrale, décrite comme une donnée paramétrable
(décision Q5, docs/champs/lumiere/conception_maison_ombre.md §3). Pavé opaque en espace continu (cm),
posé dans le repère monde.

⚠️ DONNÉE SEULE (sprint maison, tronçon 1). Cet objet ne projette AUCUNE ombre
ici : il stocke la géométrie + le matériau. L'injection de son ombre dans le
`LightField` est le tronçon 2 (re-figeage localisé). Aucun import lourd : la
maison ne dépend de rien (pure config, comme `constants.PLOT_CM`).
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class House:
    """
    Bâtiment-obstacle paramétrable. Défauts = maison normande centrée du monde
    20×20 m : 8×8 m d'empreinte, 6 m de haut, mur en calcaire de Montmartin.

    Repère : `center_*_cm` est le CENTRE de l'empreinte dans le repère monde
    (mêmes cm que les `origin_*_cm` des tuiles). `width_cm` = extension est-ouest
    (axe x), `depth_cm` = extension nord-sud (axe y).
    """
    center_x_cm:  float = 1000.0   # centre du monde 20×20 m (= 2000 cm)
    center_y_cm:  float = 1000.0
    width_cm:     float = 800.0    # empreinte est-ouest (x)
    depth_cm:     float = 800.0    # empreinte nord-sud (y)
    height_cm:    float = 600.0    # hauteur du mur (longueur d'ombre au tronçon 2)
    wall_albedo:  float = 0.35     # calcaire de Montmartin (effet espalier, tronçon 2)
    latitude_deg: float = 49.0     # Normandie (azimut/élévation solaires, tronçon 2)

    @property
    def footprint_bounds(self) -> tuple[float, float, float, float]:
        """Emprise au sol (x0, y0, x1, y1) en cm dans le repère monde."""
        hw, hd = self.width_cm / 2.0, self.depth_cm / 2.0
        return (self.center_x_cm - hw, self.center_y_cm - hd,
                self.center_x_cm + hw, self.center_y_cm + hd)
