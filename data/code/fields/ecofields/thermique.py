"""
SYMBIOSE — fields/ecofields/thermique.py
Microclimat de surface : calcul PUR de la carte `temperature_sol` (par plot).

Isolé de `container.py` (déjà dense) pour le garder sous le seuil de taille : le
conteneur n'expose qu'une fine méthode `tick_thermique` qui délègue ici. Fonction
pure, zéro RNG, zéro log — déterminisme philo #3.

Modèle DIURNE COMPLET (tronçon ④) — solaire·nébulosité − latente − isolation :

    facteur_nebul        = 1 − K_NEBUL_DIURNE · nébulosité
    cible[r,c]            = T_air + GAIN_SOLAIRE · lumière_sol[r,c] · intensité_saison · facteur_nebul
                                  − REFROID_EVAP · humidité_norm[r,c]
                                  − ISOLATION_COUVERT · litière_norm[r,c]
    temperature_sol[r,c] += (cible − temperature_sol[r,c]) · THERMAL_INERTIA

T_air (champ `temperature`, rempli uniforme par l'engine) sert de base ; la
lumière-sol (intégrale diurne du LightField, où l'ombre maison/canopée est déjà
encodée) module la surchauffe ; `intensité_saison` l'atténue en saison froide ;
la nébulosité (④) bride le gain solaire un ciel couvert (la météo, scalaire par
tick, entre ENFIN dans la thermique) ; le terme latent (②) refroidit les plots
humides (l'eau qui s'évapore prend de l'énergie au sol → cercle vicieux de la
sécheresse) ; le terme isolation (③) tamponne les plots couverts d'une litière
dense (paillis naturel issu de la décompo → interconnexion des acteurs) ;
l'inertie tamponne les sauts d'une semaine sur l'autre (le sol garde sa chaleur).

L'humidité ET la litière lues ici sont celles de FIN du tick précédent :
`tick_thermique` tourne en 2b, AVANT `tick_hydrology` (3) et AVANT la décompo.
Cohérent (la T_sol du matin dépend de l'humidité/du couvert accumulés) et
déterministe — ne pas réordonner. La nébulosité, elle, est celle de l'événement
météo DU tick (déjà tiré en 1, déterministe).

Modèle diurne COMPLET (4 termes). Le gel NOCTURNE (tronçon ⑥) ajoute une carte
SÉPARÉE `t_min_nuit_at` (helper pur ci-dessous) : la nuit le soleil ne joue plus,
seuls couvert (litière) et nébulosité protègent du rayonnement vers le ciel clair.
"""

from __future__ import annotations

from .constants import (GAIN_SOLAIRE, THERMAL_INERTIA, INTENSITE_SAISON,
                        REFROID_EVAP, ISOLATION_COUVERT, LITIERE_REF,
                        K_NEBUL_DIURNE, RAYONNEMENT_NOCTURNE,
                        SNOW_ACCUM, SNOW_MELT_BASE, SNOW_MELT_WARM)


def tick_thermique(eco, saison: str, nebulosite: float = 0.0) -> None:
    """Met à jour `eco.temperature_sol` depuis `eco.temperature` (T_air),
    `eco.lumiere` (lumière-sol diurne), `eco.humidite` (refroidissement
    évaporatif), la litière (`om_fresh_at`, isolation par le couvert) et la
    `nebulosite` (scalaire météo du tick : 0 = ciel clair, atténue le gain
    solaire). Le défaut `0.0` garde l'helper testable sans météo. Pure : n'écrit
    QUE `temperature_sol`."""
    intensite     = INTENSITE_SAISON.get(saison, 1.0)
    facteur_nebul = 1.0 - K_NEBUL_DIURNE * nebulosite
    t_sol = eco.temperature_sol
    for r in range(eco.rows):
        for c in range(eco.cols):
            t_air    = eco.temperature.data[r][c]
            lum      = eco.lumiere.at_plot(r, c)
            hum_norm = min(1.0, eco.humidite.at_plot(r, c) / 3.0)
            lit_norm = min(1.0, eco.om_fresh_at(r, c) / LITIERE_REF)
            cible = (t_air + GAIN_SOLAIRE * lum * intensite * facteur_nebul
                     - REFROID_EVAP * hum_norm
                     - ISOLATION_COUVERT * lit_norm)
            cur   = t_sol.data[r][c]
            t_sol.set(r, c, cur + (cible - cur) * THERMAL_INERTIA)


def t_min_nuit_at(eco, r: int, c: int, t_air: float, nebulosite: float) -> float:
    """Température minimale NOCTURNE estimée au plot (r,c) — borne basse de la
    semaine, lue par le GEL (boucle.py), PAS par la croissance (qui reste sur la
    T ressentie diurne ⑤).

    ⚠️ La logique s'INVERSE par rapport au diurne. La nuit, le soleil ne chauffe
    plus : ce ne sont PAS les plots ensoleillés qui gèlent, mais les plots
    DÉCOUVERTS qui rayonnent leur chaleur vers le ciel CLAIR. On NE relit donc
    PAS `temperature_sol` (carte diurne) — on calcule une carte séparée à partir
    de T_air :

        T_min_nuit = T_air − RAYONNEMENT_NOCTURNE · (1 − couvert) · (1 − nébulosité)

    - `couvert` = litière locale normalisée `min(1, om_fresh_at/LITIERE_REF)` PLUS
      le manteau neigeux `eco.snow` (⑦) : un sol nu rayonne à plein, un sol paillé
      OU enneigé garde sa chaleur. Sous un bon manteau (`snow→1`) le couvert sature
      à 1 → `T_min_nuit → T_air` : la neige PROTÈGE du gel (effet igloo).
    - `(1 − nébulosité)` : un ciel couvert renvoie l'IR → peu de gel. Les gelées
      arrivent par nuit CLAIRE et calme.

    Pure, zéro RNG, zéro effet de bord (philo #3 — lit `eco.snow`, ne l'écrit pas)."""
    couvert = min(1.0, eco.om_fresh_at(r, c) / LITIERE_REF + eco.snow)
    return t_air - RAYONNEMENT_NOCTURNE * (1.0 - couvert) * (1.0 - nebulosite)


def snow_next(snow: float, temp_now: float, is_neige: bool) -> float:
    """Manteau neigeux du prochain tick (⑦) — fonction PURE de l'état précédent.

    Isolé ici (comme `t_min_nuit_at`) pour garder `container.py` sous le seuil de
    taille : le conteneur n'expose qu'une fine `tick_snow` qui délègue.

    - Semaine de Neige → accumulation bornée : `min(1, snow + SNOW_ACCUM)`.
    - Sinon → fonte : `snow − SNOW_MELT_BASE − SNOW_MELT_WARM·max(0, temp_now)`,
      bornée à 0. Fond lentement au froid (fond constant), vite au dégel (couplage
      température). Déterministe, zéro RNG."""
    if is_neige:
        return min(1.0, snow + SNOW_ACCUM)
    melt = SNOW_MELT_BASE + SNOW_MELT_WARM * max(0.0, temp_now)
    return max(0.0, snow - melt)
