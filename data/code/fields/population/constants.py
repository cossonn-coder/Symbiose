"""
SYMBIOSE — fields/population/constants.py
Primitives numériques pures + constantes de calibrage TRANSVERSES de la vie
macroscopique. Extrait de l'ancien module monolithique `population.py` (scission
/refactor 2026-06-30 — comportement strictement inchangé). Les constantes
spécifiques à un seul sous-module vivent avec lui (resources / perception /
registry) ; ICI uniquement ce qui est partagé par plusieurs.
"""
import math


POP_MAX = 1.0          # densité normalisée par plot ∈ [0, POP_MAX]
POP_INERTIA = 0.85     # inertie de MONTÉE (la pop croît vers sa cible à ce rythme)
# Inertie de DÉCRUE (docs/faune/vie_macro/conception_saisonnalite_vie_macro.md §4) : quand la cible
# tombe sous la pop courante, la relaxation est PLUS RAPIDE → la dormance
# automnale ne traîne plus 13 semaines (0.55⁴ ≈ 0.09, extinction en ~4 sem).
# Asymétrie écologique : « meurt vite quand le milieu se dégrade, recolonise
# lentement quand il s'améliore ». Knob de recours → remonter vers 0.70 si les
# bust estivaux deviennent trop pointus (sprites qui clignotent).
POP_INERTIA_DECAY = 0.55

# Couplage température → vitalité de la guilde (chaud = naissances, froid = mort).
# C'est le signal d'INTENSITÉ (« combien » la guilde prospère quand elle est
# active), distinct de la porte saisonnière `phenology` (« quand », ci-dessous).
# Recalibré 2026-07-18 (D86 suite, choix Nico) : les pollinisateurs précoces
# (osmie « abeille des vergers », reines de bourdon) butinent les vergers dès la
# sortie de l'hiver, à 8-12 °C — l'ancienne rampe 6→24 °C (warmth≈0.08 au
# printemps frais) les rendait quasi absents quand pommier/cerisier fleurissent.
# Rampe abaissée à 3→15 °C : la faune est pleinement active dès la belle saison
# fraîche (warmth sature à 15 °C). Global à TOUTES les guildes (décision tranchée
# — cf. journal) : élargit la saison active de toute la vie macro.
T_COLD_ZERO = 3.0      # °C : en dessous, plus aucune chaleur utile (warmth = 0)
T_WARM_FULL = 15.0     # °C : au-dessus, chaleur maximale (warmth = 1)

# --- Saisonnalité photopériodique (docs/faune/vie_macro/conception_saisonnalite_vie_macro.md §2-3) ---
# La DORMANCE/le RÉVEIL des guildes se pilotent par la LONGUEUR DU JOUR, pas par
# la température seule : un signal anticipateur fiable et déterministe (le jour
# court ne ment pas, un redoux si). `daylength(wiy)` est une sinusoïde 8 h↔16 h
# à ~49°N, pic au solstice d'été (wiy≈25, qui PRÉCÈDE le pic thermique wiy≈30 —
# le déphasage saisonnier réel). Chaque guilde a ensuite sa propre FENÊTRE
# d'activité (seuils en heures de jour) — voir TrophicSpec.daylen_min/full.
W_SOLSTICE_ETE = 25    # semaine du jour le plus long
DAYLEN_MOY_H   = 12.0  # longueur de jour moyenne (équinoxes), heures
DAYLEN_AMP_H   = 4.0   # demi-amplitude → 8 h (solstice hiver) ↔ 16 h (solstice été)
# Fenêtre phénologique PAR DÉFAUT (heures de jour) — surchargée par guilde.
DEF_DAYLEN_MIN  = 10.0  # en dessous → dormance (phenology = 0)
DEF_DAYLEN_FULL = 13.0  # au-dessus → pleine activité (phenology = 1)

# Références de normalisation des ressources trophiques → [0, 1].
FOLIAGE_REF = 2.0      # somme de feuillage (santé/3 × densité) saturant la ressource
FLOWER_REF  = 1.5      # somme de "fleurs" (plantes matures) saturant le nectar
OM_REF      = 4.0      # om_fresh + om_active saturant la ressource des vers
MONO_REF    = 3.0      # nb de familles voisines au-delà duquel la monoculture cesse

# Pondérations par défaut (surchargées par TrophicSpec).
#
# Forme MULTIPLICATIVE (capacité de charge × survie) — choisie pour que la
# population puisse COLONISER depuis zéro (la cible ne dépend pas de la pop
# courante) et OSCILLER (la prédation/perturbation rabotent la survie). Une
# forme additive « naissance − mort » plafonnerait tout à zéro dès que la
# population est basse (les morts absolues l'emportent), d'où densités nulles.
#
#   capacité = clamp(resource_w·ressource + habitat_w·habitat, 0, 1)
#   survie   = chaleur · (1 − min(1, pred_w·prédation)) · (1 − min(1, disturb_w·perturbation))
#   cible    = capacité · survie
#
# Le froid (hiver) et la famine sont IMPLICITES : chaleur=0 en hiver annule la
# cible (déclin saisonnier visible) ; si pop > capacité, la cible < pop → déclin.
DEF_RESOURCE_W = 0.80  # poids de la ressource trophique dans la capacité de charge
DEF_HABITAT_W  = 0.45  # poids du plancher d'habitat/nectar dans la capacité
DEF_PRED_W     = 1.20  # sensibilité de la survie à la prédation locale
DEF_DISTURB_W  = 0.60  # sensibilité de la survie à la perturbation locale


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def _smoothstep(x: float, a: float, b: float) -> float:
    """Rampe LISSE [0,1] entre les seuils a (→0) et b (→1) — Hermite 3t²−2t³.
    Plus douce qu'une rampe linéaire (dérivée nulle aux bornes) → pas de
    cassure d'activité quand le jour franchit un seuil."""
    if a == b:
        return 0.0 if x < a else 1.0
    t = _clamp01((x - a) / (b - a))
    return t * t * (3.0 - 2.0 * t)


def daylength(week_in_year: int) -> float:
    """
    Longueur du jour (heures) à ~49°N — sinusoïde 8 h↔16 h, pic au solstice d'été
    (docs/faune/vie_macro/conception_saisonnalite_vie_macro.md §2). Fonction PURE de la semaine (philo
    #3) : le forecast et la phénologie florale (arc pollinisation) pourront s'y
    appuyer. NON-monotone → une simple rampe sur cette grandeur donne du même
    coup le réveil printanier ET la dormance automnale, des deux côtés du solstice.
    """
    return DAYLEN_MOY_H + DAYLEN_AMP_H * math.cos(
        2.0 * math.pi * (week_in_year - W_SOLSTICE_ETE) / 52.0)


def _zero_grid(rows: int, cols: int) -> list[list[float]]:
    return [[0.0] * cols for _ in range(rows)]
