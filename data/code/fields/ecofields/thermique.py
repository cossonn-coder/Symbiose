"""
SYMBIOSE — fields/ecofields/thermique.py
Microclimat de surface : calcul PUR de la carte `temperature_sol` (par plot).

Isolé de `container.py` (déjà dense) pour le garder sous le seuil de taille : le
conteneur n'expose qu'une fine méthode `tick_thermique` qui délègue ici. Fonction
pure, zéro RNG, zéro log — déterminisme philo #3.

Modèle (tronçon ①, sprint thermique-microclimat) — surchauffe solaire seule :

    cible[r,c]            = T_air + GAIN_SOLAIRE · lumière_sol[r,c] · intensité_saison
    temperature_sol[r,c] += (cible − temperature_sol[r,c]) · THERMAL_INERTIA

T_air (champ `temperature`, rempli uniforme par l'engine) sert de base ; la
lumière-sol (intégrale diurne du LightField, où l'ombre maison/canopée est déjà
encodée) module la surchauffe ; `intensité_saison` l'atténue en saison froide ;
l'inertie tamponne les sauts d'une semaine sur l'autre (le sol garde sa chaleur).

Les termes refroidissement évaporatif (②), isolation par le couvert (③) et
nébulosité (④) s'ajouteront à `cible` aux tronçons suivants.
"""

from __future__ import annotations

from .constants import GAIN_SOLAIRE, THERMAL_INERTIA, INTENSITE_SAISON


def tick_thermique(eco, saison: str) -> None:
    """Met à jour `eco.temperature_sol` depuis `eco.temperature` (T_air) et
    `eco.lumiere` (lumière-sol diurne). Pure : n'écrit QUE `temperature_sol`."""
    intensite = INTENSITE_SAISON.get(saison, 1.0)
    t_sol = eco.temperature_sol
    for r in range(eco.rows):
        for c in range(eco.cols):
            t_air = eco.temperature.data[r][c]
            lum   = eco.lumiere.at_plot(r, c)
            cible = t_air + GAIN_SOLAIRE * lum * intensite
            cur   = t_sol.data[r][c]
            t_sol.set(r, c, cur + (cible - cur) * THERMAL_INERTIA)
