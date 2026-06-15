"""
SYMBIOSE — plants/base/empreintes.py
Empreinte spatiale au sol : dérivation rayon → plots + défauts métriques par
strate (Sprint éclairement D20-D21). Couche basse de `plants.base`, aucune
dépendance interne au paquet.
"""

from __future__ import annotations

from constants import PLOT_CM


def _plots_in_radius(x_cm: float, y_cm: float, radius_cm: float) -> list[tuple]:
    """
    Plots (row, col) dont le centre cartésien tombe dans un disque de rayon
    `radius_cm` centré sur la position continue (x_cm, y_cm).

    Embedding cartésien orthogonal : centre du plot (r, c) = (c·50+25, r·50+25).
    Le plot-foyer est toujours inclus. Peut renvoyer des plots hors grille — les
    consommateurs (uptake, conflits…) filtrent via is_valid_plot.

    Échelle de référence (plante au centre de son plot) :
        rayon ≤ 35      → 1 plot (foyer)
        rayon 50–70     → 5 plots (croix)
        rayon 71–99     → 9 plots (bloc 3×3)
    """
    fr = int(y_cm // PLOT_CM)
    fc = int(x_cm // PLOT_CM)
    k = int(radius_cm // PLOT_CM) + 1
    r2 = radius_cm * radius_cm
    out = []
    for dr in range(-k, k + 1):
        for dc in range(-k, k + 1):
            r = fr + dr
            c = fc + dc
            cx = c * PLOT_CM + PLOT_CM / 2
            cy = r * PLOT_CM + PLOT_CM / 2
            if (cx - x_cm) ** 2 + (cy - y_cm) ** 2 <= r2:
                out.append((r, c))
    if (fr, fc) not in out:
        out.append((fr, fc))
    return out

# ---------------------------------------------------------------------------
# DÉFAUTS PAR STRATE — extensibilité du catalogue
# ---------------------------------------------------------------------------
#
# Une espèce hérite GRATUITEMENT de ces valeurs via sa strate par stade. Elle
# ne renseigne explicitement (override sur GrowthStage / classe) que ce qui
# dévie (rosette large, racines traçantes, feuillage opaque…). Ajouter une
# espèce « standard » ne demande donc qu'une hauteur par stade et sa strate.
#
#   height   : hauteur potentielle de repli (cm) si canopy_height non précisé
#   canopy_r : rayon de canopée par défaut (cm)
#   root_r   : rayon racinaire par défaut (cm)
#   density  : opacité d'ombre par défaut [0–1]

STRATE_DEFAULTS = {
    "sol":       {"height": 10,  "canopy_r": 25, "root_r": 30, "density": 0.40},
    "basse":     {"height": 30,  "canopy_r": 30, "root_r": 30, "density": 0.50},
    "moyenne":   {"height": 80,  "canopy_r": 50, "root_r": 55, "density": 0.55},
    "haute":     {"height": 180, "canopy_r": 55, "root_r": 60, "density": 0.65},
    "grimpante": {"height": 150, "canopy_r": 25, "root_r": 55, "density": 0.50},
}

# Tolérance à l'ombre de RÉFÉRENCE par strate (compétition intra-plot, Q6).
# >1 = sciaphile (prospère/lève à l'ombre), <1 = héliophile (pénalisé dès
# l'ombrage). Défaut écologique : les strates basses du sous-bois tolèrent
# l'ombre, les hautes la fuient. Valeur de DÉPART (calibrage §4), modulée
# individuellement par le gène `tolerance_ombre`. La base d'espèce est dérivée
# de la strate du stade MATURE (cf. PlantBase.shade_tolerance_base).
STRATE_SHADE_TOLERANCE = {
    "sol":       1.25,
    "basse":     1.25,
    "moyenne":   1.00,
    "haute":     0.90,
    "grimpante": 1.00,
}

# Empreinte procédurale (D29 réorienté, tronçon 2) — rayon racinaire dérivé de la
# couronne (§G, §8 acté : pas de structure souterraine). k calibré : la tomate
# veut root ≈ canopy (drip-line). Module-level (1 espèce migrée) → per-espèce plus tard.
PROC_ROOT_RATIO = 1.0   # root_radius = PROC_ROOT_RATIO · canopy_radius
