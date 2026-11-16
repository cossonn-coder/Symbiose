"""
SYMBIOSE — sim/tempo.py
Le TEMPO DE VIE d'une plante en vraies unités (D139 ③) : une seule conversion,
partagée par les trois horloges que pilote le gène `phenologie_florale`.

POURQUOI UN MODULE À PART ?
Le gène `phenologie_florale` vaut désormais une AVANCE EN SEMAINES (+1 = la
plante fleurit une semaine plus tôt que son espèce). Trois horloges la lisent :
  1. la FLORAISON (`sim/engine/floraison.py`) — seuil de forçage thermique ;
  2. l'ABSCISSION des caducs (`sim/engine/decompo.py`, et le pont qui en dérive
     la rampe d'automne) — semaine de largage ;
  3. la SÉNESCENCE (`sim/engine/mortalite.py`) — début du déclin de fin de vie,
     avec son MIROIR EXACT dans `sim/semiologie.py` (le signe visible).
Si chacun refaisait sa conversion, ils divergeraient au premier recalibrage (et
le signe de sénescence mentirait sur la mort). D'où UNE fonction par horloge,
ICI, que tous appellent. Couche `sim` (lit `fields` et la météo pure) : aucun
import de `sim.engine` → `semiologie` peut s'en servir sans remonter de couche.

LA CONVERSION, HORLOGE PAR HORLOGE
  - Floraison : une semaine d'avance = abaisser le seuil de forçage des
    degrés-jours qu'une semaine apporte À L'ÉPOQUE où l'espèce fleurit
    (`gdd_par_semaine`). Un pommier fleurit au début du printemps (~3 °C·j par
    semaine), un tournesol en plein été (~9) : la même « semaine » ne vaut pas le
    même nombre de degrés-jours. C'est ce qui fait de la semaine une VRAIE unité.
  - Abscission et sénescence : elles gardent le calibrage du sprint DÉSYNC
    PHÉNOLOGIE, exprimé par rapport à l'ancien gène-facteur (g − 1). Une semaine
    d'avance vaut `1 / SEMAINES_PAR_TEMPO` de ce g − 1 : avec 10, l'écart-type
    neuf (σ_A = 1 semaine) retrouve exactement l'ancien σ (0,10) → ±1,5 semaine
    de largage, ±0,05 de longévité au début du déclin. Le couplage entre horloges
    (« une plante précoce l'est en tout ») est donc conservé tel quel.

Déterministe et pur : `gdd_par_semaine` lit la température NORMALE (`temp_norm`,
sans aléa) et se mémoïse par espèce — jamais recalculée dans un tick.
"""

from __future__ import annotations
from fields import (SENESCENCE_ONSET, SEN_ONSET_JITTER, ABSCISSION_BASE,
                    ABSCISSION_JITTER, ABSCISSION_MIN, ABSCISSION_MAX)
from sim.weather import temp_norm

# Base thermique du forçage floral (°C) — en deçà, aucun degré-jour utile. Déplacée
# ici depuis `sim/engine/floraison.py` (qui la ré-exporte) : la conversion des
# semaines en degrés-jours en a besoin, et `sim` ne lit pas `sim.engine`.
T_BASE_FLORAISON = 6.0

# Semaines d'avance par unité de l'ancien gène-facteur (g − 1). Cf. en-tête.
SEMAINES_PAR_TEMPO = 10.0
# Plancher du taux de forçage (°C·j / semaine) : une espèce dont le seuil tombe dans
# une semaine quasi froide garderait sinon un décalage nul (gène muet).
GDD_SEMAINE_MIN = 1.0

_cache_gdd: dict = {}


def avance(plant) -> float:
    """Avance du tempo de vie de la plante, en semaines (> 0 = précoce)."""
    return plant.gene("phenologie_florale")


def gdd_par_semaine(plant_class) -> float:
    """Degrés-jours de forçage qu'apporte UNE semaine à l'époque où l'espèce
    fleurit, en climat normal : on cumule `max(0, T_norm − T_BASE)` depuis la
    semaine 1 jusqu'au franchissement de `bloom_forcing_gdd`, et on rend l'apport
    de cette semaine-là (plancher GDD_SEMAINE_MIN). Mémoïsé par espèce."""
    v = _cache_gdd.get(plant_class)
    if v is None:
        seuil = plant_class.bloom_forcing_gdd
        cumul, v = 0.0, GDD_SEMAINE_MIN
        for w in range(1, 53):
            apport = max(0.0, temp_norm(w) - T_BASE_FLORAISON)
            cumul += apport
            if cumul >= seuil:
                v = max(GDD_SEMAINE_MIN, apport)
                break
        _cache_gdd[plant_class] = v
    return v


def seuil_floraison(plant) -> float:
    """Seuil de forçage floral INDIVIDUEL (°C·j) : celui de l'espèce, abaissé de
    `avance` semaines de forçage (relevé si l'avance est négative)."""
    cls = plant.plant_class
    return cls.bloom_forcing_gdd - avance(plant) * gdd_par_semaine(cls)


def _ecart_ancien(plant) -> float:
    """Avance exprimée dans l'ancienne échelle du gène-facteur (g − 1)."""
    return avance(plant) / SEMAINES_PAR_TEMPO


def semaine_abscission(plant) -> int:
    """Semaine de largage PROPRE à un caduc, bornée à la fenêtre d'automne
    [ABSCISSION_MIN, ABSCISSION_MAX] (précoce → largue plus tôt)."""
    w = round(ABSCISSION_BASE - ABSCISSION_JITTER * _ecart_ancien(plant))
    return max(ABSCISSION_MIN, min(ABSCISSION_MAX, w))


def onset_senescence(plant) -> float:
    """Début PROPRE du déclin de fin de vie, en fraction de longévité, borné à
    [0,05 ; 0,95] (précoce → sénesce plus tôt)."""
    return max(0.05, min(0.95,
                         SENESCENCE_ONSET - SEN_ONSET_JITTER * _ecart_ancien(plant)))
