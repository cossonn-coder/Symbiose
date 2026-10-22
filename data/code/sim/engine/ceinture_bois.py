"""
SYMBIOSE — sim/engine/ceinture_bois.py
La LISIÈRE BOISÉE lâche du bois mort dans le jardin (D111 ⑦bis, décision Nico :
« oui la ceinture forestière fournit du bois »).

Pourquoi : un jardin qui jouxte un bois reçoit en continu brindilles et branches
des couronnes qui débordent et de celles que le vent arrache. UN arbre du jardin
lâche ~0,03 de bois par an (mesuré au ②ter) quand le stock au sol fond de moitié
par an : seule une source à l'échelle d'un BOISEMENT entretient un bois mort
permanent, là où les champignons du bois (pleurote, hypholome, collybie)
fructifient — la lisière.

Modèle (agrégat, on ne simule pas les arbres de la ceinture — D32) :
  • source = un secteur ligneux (`densite_ligneuse` > 0 : forêt, friche) ;
  • portée = ordre de grandeur d'une couronne qui déborde, ∝ hauteur de canopée ;
  • chaque semaine, chaque plot de la bande tire (hachage, zéro RNG) une CHUTE avec
    une probabilité ∝ densité × hauteur × poids de distance au bord × saison
    (automne-hiver plus) × tempête (masse d'air × rafale, l'arbre de lisière est
    exposé) ;
  • une chute = brindilles (souvent), branche, ou grosse branche (rare), chacune
    avec sa GROSSEUR → la décompo dépend du diamètre (litière, ⑦bis).
Un secteur coupé (`couper_secteur` baisse densité et hauteur) en lâche moins : la
cause reste au milieu (philo #1). Sans ceinture → no-op strict (golden/smoke).
"""
from __future__ import annotations

from constants import PLOT_CM
from fields import _hash_noise
from fields.peripherie import plots_de_bord

# Canaux-sentinelles de hachage (tranche 91_1xx, décorrélée de la ceinture 91_00x).
K_CHUTE, K_PIECE, K_MASSE, K_DIAM = 91_101, 91_102, 91_103, 91_104

HAUTEUR_REF_CM   = 1500.0   # lisière de référence (15 m)
HAUTEUR_MIN_CM   = 200.0    # une friche (ronces, jeunes ligneux) sans canopée mesurée
PORTEE_PAR_CM    = 0.25     # portée = 1/4 de la hauteur (couronne qui déborde)
PORTEE_MAX_CM    = 400.0
# Probabilité hebdomadaire d'une chute sur un plot AU CONTACT d'une lisière de
# référence pleine (densité 1, 15 m). ~1,5 chute/an au contact × ~0,17 de masse
# moyenne ≈ 0,25 de bois par plot de contact et par an. Knob de calibrage.
P_CHUTE          = 0.03
SAISON           = {"printemps": 0.6, "ete": 0.5, "automne": 1.4, "hiver": 1.5}
TEMPETE_SEUIL    = 1.0      # force × rafale au-delà duquel les branches cassent (~10 % des sem.)
TEMPETE_K        = 3.0      # surcroît de chutes par unité de sévérité
# Pièces : (part cumulée, masse min-max, diamètre cm min-max).
PIECES = ((0.70, (0.03, 0.08), (0.3, 1.0)),    # brindilles
          (0.95, (0.15, 0.50), (2.0, 6.0)),    # branche
          (1.00, (0.60, 1.50), (8.0, 15.0)))   # grosse branche


def _entre(b: tuple, u: float) -> float:
    return b[0] + (b[1] - b[0]) * u


def _intensite(secteur: dict) -> tuple[float, float]:
    """(intensité relative, portée cm) d'un secteur ; (0, 0) s'il n'est pas ligneux."""
    d = secteur.get("densite_ligneuse", 0.0)
    if d <= 0.0 or secteur.get("type") == "falaise":
        return 0.0, 0.0
    h = max(HAUTEUR_MIN_CM, secteur.get("hauteur_canopee", 0.0))
    return d * h / HAUTEUR_REF_CM, min(PORTEE_MAX_CM, h * PORTEE_PAR_CM)


def bois_de_lisiere(tile, eco, ceinture, saison: str, seed: int, week: int,
                    vent_force: float, gust_peak: float) -> list:
    """Dépose le bois tombé de la ceinture sur les plots de bord de `tile`.
    Renvoie les lignes de log (une par tuile, seulement en tempête)."""
    if not ceinture:
        return []
    sev = max(0.0, vent_force * gust_peak - TEMPETE_SEUIL)
    facteur = SAISON.get(saison, 1.0) * (1.0 + TEMPETE_K * sev)
    origine = (tile.origin_x_cm, tile.origin_y_cm)
    r0, c0 = int(origine[1] // PLOT_CM), int(origine[0] // PLOT_CM)   # repère MONDE
    total = 0.0
    for s in ceinture:
        intens, portee = _intensite(s)
        if intens <= 0.0:
            continue
        for r, c, poids in plots_de_bord(s["cote"], eco.rows, eco.cols, origine, portee):
            rm, cm = r0 + r, c0 + c
            if _hash_noise(seed + K_CHUTE, week, rm, cm) >= P_CHUTE * intens * poids * facteur:
                continue
            u = _hash_noise(seed + K_PIECE, week, rm, cm)
            _, masses, diams = next((p for p in PIECES if u < p[0]), PIECES[-1])
            masse = _entre(masses, _hash_noise(seed + K_MASSE, week, rm, cm))
            eco.deposer_litiere(r, c, "bois", masse,
                                _entre(diams, _hash_noise(seed + K_DIAM, week, rm, cm)))
            total += masse
    if sev > 0.0 and total > 0.0:
        return [f"    🪵 La tempête arrache du bois à la lisière (+{total:.2f})"]
    return []
