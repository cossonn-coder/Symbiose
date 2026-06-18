"""
SYMBIOSE — fields/ecofields/thermique.py
Microclimat de surface : calcul PUR de la carte `temperature_sol` (par plot).

Isolé de `container.py` (déjà dense) pour le garder sous le seuil de taille : le
conteneur n'expose qu'une fine méthode `tick_thermique` qui délègue ici. Fonction
pure, zéro RNG, zéro log — déterminisme philo #3.

Modèle (tronçon ②, sprint thermique-microclimat) — surchauffe solaire − latente :

    cible[r,c]            = T_air + GAIN_SOLAIRE · lumière_sol[r,c] · intensité_saison
                                  − REFROID_EVAP · humidité_norm[r,c]
    temperature_sol[r,c] += (cible − temperature_sol[r,c]) · THERMAL_INERTIA

T_air (champ `temperature`, rempli uniforme par l'engine) sert de base ; la
lumière-sol (intégrale diurne du LightField, où l'ombre maison/canopée est déjà
encodée) module la surchauffe ; `intensité_saison` l'atténue en saison froide ;
le terme latent (②) refroidit les plots humides (l'eau qui s'évapore prend de
l'énergie au sol → cercle vicieux de la sécheresse) ; l'inertie tamponne les
sauts d'une semaine sur l'autre (le sol garde sa chaleur).

L'humidité lue ici est celle de FIN du tick précédent : `tick_thermique` tourne
en 2b, AVANT `tick_hydrology` (3). Cohérent (la T_sol du matin dépend de
l'humidité accumulée) et déterministe — ne pas réordonner.

Les termes isolation par le couvert (③) et nébulosité (④) s'ajouteront à `cible`
aux tronçons suivants.
"""

from __future__ import annotations

from .constants import GAIN_SOLAIRE, THERMAL_INERTIA, INTENSITE_SAISON, REFROID_EVAP


def tick_thermique(eco, saison: str) -> None:
    """Met à jour `eco.temperature_sol` depuis `eco.temperature` (T_air),
    `eco.lumiere` (lumière-sol diurne) et `eco.humidite` (refroidissement
    évaporatif). Pure : n'écrit QUE `temperature_sol`."""
    intensite = INTENSITE_SAISON.get(saison, 1.0)
    t_sol = eco.temperature_sol
    for r in range(eco.rows):
        for c in range(eco.cols):
            t_air    = eco.temperature.data[r][c]
            lum      = eco.lumiere.at_plot(r, c)
            hum_norm = min(1.0, eco.humidite.at_plot(r, c) / 3.0)
            cible = (t_air + GAIN_SOLAIRE * lum * intensite
                     - REFROID_EVAP * hum_norm)
            cur   = t_sol.data[r][c]
            t_sol.set(r, c, cur + (cible - cur) * THERMAL_INERTIA)
