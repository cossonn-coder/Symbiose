"""
SYMBIOSE — sim/engine/transpiration.py
Transpiration FOLIAIRE saisonnière (sprint « le sol qui respire » ①, D111 §1c).

Pédagogie : l'eau qu'une plante prélève dans le sol n'est pas « bue » par la
racine, elle est TIRÉE par les feuilles — les stomates s'ouvrent, l'eau s'évapore
de la feuille et la colonne d'eau remonte depuis le sol. Pas de feuilles (arbre
défeuillé, vivace rentrée sous terre) ⇒ presque pas de prélèvement ; air froid et
ciel couvert ⇒ faible demande ; plein soleil chaud et venteux ⇒ forte demande.
C'est ce qui permet la RECHARGE D'HIVER du sol en climat océanique : le jardin
dort, la pluie remplit le réservoir, puis l'été le vide doucement.

Facteur = demande climatique × feuillage présent × coefficient de feuillage.
Il ne module QUE le prélèvement d'eau (`plant_uptake(transpiration=…)`), jamais
la plante elle-même (philo #2 : on agit sur un flux). Pur, zéro RNG.

Couches : vit dans `sim.engine` (lit `semaine_abscission` du frère `decompo`) ;
la saison et la météo du tick lui sont passées par la boucle.
"""

from __future__ import annotations

from fields import CHUTE_SEMAINES
from .decompo import semaine_abscission

# --- Coefficient de transpiration par TYPE DE FEUILLAGE (constante d'espèce) ---
# Nico (D-feuillage) : « les feuilles grandes et ouvertes transpirent plus que les
# épines ». Surface foliaire et épaisseur de cuticule : une grande feuille molle
# (courge, tournesol) perd beaucoup ; une feuille cireuse/duveteuse (thym, lavande)
# ou une aiguille (sapin) protège son eau. `moyen` = 1.0 = calibrage historique.
COEF_FEUILLAGE = {
    "large":    1.30,
    "moyen":    1.00,
    "fin":      0.80,
    "cireux":   0.55,
    "aiguilles": 0.40,
}

# --- Demande climatique (mêmes pilotes que l'évaporation : chaleur, ciel, vent) ---
# Normalisée à ~1.0 par une journée d'été ordinaire (T_air ≈ 18 °C, ciel clair,
# brise) → l'uptake historique (calibré sans saison) reste l'ordre de grandeur de
# la pleine saison ; l'hiver froid et couvert tombe vers 0.
T_DEMANDE_MIN = 3.0    # °C — en dessous, les stomates restent quasi fermés
T_DEMANDE_REF = 16.0   # °C — demande thermique « pleine » (facteur 1)
T_DEMANDE_MAX = 1.5    # plafond du facteur thermique (canicule)
CIEL_COUVERT  = 0.45   # part de la demande restante sous ciel totalement couvert
VENT_DEMANDE  = 0.25   # surcroît de demande à vent de masse d'air force 1

# --- Feuillage présent (phénologie foliaire grossière, calendrier moteur) ---
# Débourrement : rampe linéaire du début du printemps (sem. 1) à DEBOURREMENT_FIN.
DEBOURREMENT_FIN = 8
# Vivace « dormant » non caduque (rosette, souche) : ce qui reste l'hiver.
FEUILLAGE_DORMANT = 0.15


def demande_climatique(t_air: float, nebulosite: float, vent: float) -> float:
    """Demande évaporatoire de l'air ∈ [0, ~2] : chaleur × ciel × vent. PURE."""
    f_t = (t_air - T_DEMANDE_MIN) / (T_DEMANDE_REF - T_DEMANDE_MIN)
    f_t = max(0.0, min(T_DEMANDE_MAX, f_t))
    f_ciel = CIEL_COUVERT + (1.0 - CIEL_COUVERT) * (1.0 - nebulosite)
    return f_t * f_ciel * (1.0 + VENT_DEMANDE * vent)


def feuillage_present(plant, saison: str, week_in_year: int) -> float:
    """Fraction du feuillage en place ∈ [0,1] selon la stratégie d'hiver :
    persistant → 1 toute l'année (sa transpiration d'hiver est bridée par la
    seule demande) ; caduc → 0 de son abscission au printemps, puis débourrement ;
    vivace dormante → rosette résiduelle l'hiver ; annuelle → 1 tant qu'elle vit."""
    cls = plant.plant_class
    if cls.winter_strategy == "evergreen" or cls.winter_strategy == "die":
        return 1.0
    if saison == "printemps":
        return min(1.0, week_in_year / DEBOURREMENT_FIN)
    if saison == "hiver":
        return 0.0 if cls.deciduous else FEUILLAGE_DORMANT
    if saison == "automne" and cls.deciduous \
            and week_in_year >= semaine_abscission(plant):
        return 0.0
    return 1.0


def feuillage_visible(plant, saison: str, week_in_year: int) -> float:
    """Part de la couronne encore en place à montrer ∈ [0,1], hint de pont PUR (AUTOMNE
    VISIBLE ③). Persistant ou non caduc : 1. Caduc : 1 avant sa semaine d'abscission, baisse
    linéaire au rythme du largage, 0 jusqu'au débourrement (rampe de `feuillage_present`).
    `week_in_year` = la semaine que le snapshot s'apprête à simuler : à `semaine_abscission`
    rien n'est encore tombé (1), une semaine plus tard le premier quart est au sol.

    Distinct de `feuillage_present`, qui tombe à 0 d'un coup pour l'eau, et de
    `foliage_density_at` (lumière), réglée sur l'entrée en hiver : la couronne peut donc
    paraître dégarnie alors que son ombre moteur reste pleine (limite assumée, conception
    §3.3)."""
    if not plant.plant_class.deciduous:
        return 1.0
    if saison == "automne":
        reste = 1.0 - (week_in_year - semaine_abscission(plant)) / CHUTE_SEMAINES
        return max(0.0, min(1.0, reste))
    return feuillage_present(plant, saison, week_in_year)


def facteur_transpiration(plant, saison: str, week_in_year: int,
                          demande: float) -> float:
    """Facteur multiplicatif du prélèvement d'EAU de `plant` ce tick."""
    coef = COEF_FEUILLAGE.get(getattr(plant.plant_class, "feuillage", "moyen"), 1.0)
    return demande * feuillage_present(plant, saison, week_in_year) * coef
