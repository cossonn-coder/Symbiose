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
SÉPARÉE `t_min_nuit_type_at` (helper pur ci-dessous) : la nuit le soleil ne joue plus,
seuls couvert (litière) et nébulosité protègent du rayonnement vers le ciel clair.
Les EXTRÊMES de la semaine (D139 niche thermique ①) : `t_min_nuit_at` (nuit la plus
froide, lue par le gel) et `t_max_jour` (jour le plus chaud, lu par `t_feuille`).
"""

from __future__ import annotations

import math

from .constants import (GAIN_SOLAIRE, THERMAL_INERTIA, INTENSITE_SAISON,
                        REFROID_EVAP, ISOLATION_COUVERT, LITIERE_REF,
                        K_NEBUL_DIURNE, RAYONNEMENT_NOCTURNE, WINDCHILL_COEF,
                        ECART_NUIT_FROIDE, AMPLITUDE_DIURNE, ECART_JOUR_CHAUD,
                        SNOW_ACCUM, SNOW_MELT_BASE, SNOW_MELT_WARM,
                        MICROBE_T_OPT, MICROBE_T_TOL, MICROBE_HUM_OPT,
                        MICROBE_HUM_SAT_FLOOR, MICROBE_CLIM_FLOOR)


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


def _couvert_nuit(eco, r: int, c: int) -> float:
    """Couvert nocturne du plot ∈ [0,1] : litière + neige + écran posé (cf. ci-dessous)."""
    return min(1.0, eco.om_fresh_at(r, c) / LITIERE_REF + eco.snow
               + eco.couvert_at(r, c))


def t_min_nuit_at(eco, r: int, c: int, t_air: float, nebulosite: float) -> float:
    """Nuit la PLUS FROIDE de la semaine au plot (r,c) (D139, niche thermique ①) —
    lue par le GEL des plantes (boucle.py) et la GLACE des mares (glace.py).

        T_nuit_froide = T_nuit_type − ECART_NUIT_FROIDE · (1 − couvert) · (1 − nébulosité)

    📖 Le tick est hebdomadaire : la nuit TYPE (ci-dessous) est une nuit moyenne. Une
    plante, elle, gèle la PIRE nuit de la semaine. L'écart a la même forme que le
    rayonnement : la nuit la plus froide est une nuit claire et calme sur sol nu ; le
    paillage, la neige et le voile en protègent autant que de la nuit type (sous un
    couvert plein, les deux rejoignent T_air). Toujours ≤ la nuit type. Pure, zéro RNG.

    La ROSÉE et le GIVRE restent sur la nuit type (`t_min_nuit_type_at`) : ils font le
    BILAN de condensation de toutes les nuits de la semaine, pas de la pire."""
    ecart = ECART_NUIT_FROIDE * (1.0 - _couvert_nuit(eco, r, c)) * (1.0 - nebulosite)
    return t_min_nuit_type_at(eco, r, c, t_air, nebulosite) - ecart


def t_max_jour(t_air: float, nebulosite: float) -> float:
    """Jour le PLUS CHAUD de la semaine (°C d'air, D139 niche thermique ①) — miroir de
    la nuit la plus froide :

        T_max_jour = T_air + (AMPLITUDE_DIURNE + ECART_JOUR_CHAUD) · (1 − nébulosité)

    T_air est la moyenne de la semaine ; l'après-midi type la dépasse de la demi-
    amplitude diurne, le plus chaud de la semaine d'un écart de plus. Un ciel couvert
    écrase les deux. Uniforme par tuile (c'est de l'AIR) : ce qui chauffe une feuille
    plus qu'une autre — soleil et soif — est dans `t_feuille` (sim/engine/feuille.py).
    Toujours ≥ T_air. Pure, zéro RNG."""
    return t_air + (AMPLITUDE_DIURNE + ECART_JOUR_CHAUD) * (1.0 - nebulosite)


def t_min_nuit_type_at(eco, r: int, c: int, t_air: float, nebulosite: float) -> float:
    """Température minimale de la nuit TYPE (moyenne) de la semaine au plot (r,c) —
    lue par la rosée/le givre (bilan de toutes les nuits) et base de la nuit la plus
    froide (`t_min_nuit_at`). PAS lue par la croissance (T ressentie diurne ⑤).

    ⚠️ La logique s'INVERSE par rapport au diurne. La nuit, le soleil ne chauffe
    plus : ce ne sont PAS les plots ensoleillés qui gèlent, mais les plots
    DÉCOUVERTS qui rayonnent leur chaleur vers le ciel CLAIR. On NE relit donc
    PAS `temperature_sol` (carte diurne) — on calcule une carte séparée à partir
    de T_air :

        T_min_nuit = T_air − RAYONNEMENT_NOCTURNE · (1 − couvert) · (1 − nébulosité)

    - `couvert` = litière locale normalisée `min(1, om_fresh_at/LITIERE_REF)` PLUS
      le manteau neigeux `eco.snow` (⑦) PLUS l'écran POSÉ `eco.couvert_at` (voile/
      cloche, effondrement météo ③) : un sol nu rayonne à plein, un sol paillé,
      enneigé OU voilé garde sa chaleur. Sous un bon manteau/voile (couvert→1) il
      sature à 1 → `T_min_nuit → T_air` : neige et voile PROTÈGENT du gel (effet
      igloo). `couvert_at` = 0.0 tant qu'aucune couverture n'est posée → terme neutre,
      golden NEUTRE.
    - `(1 − nébulosité)` : un ciel couvert renvoie l'IR → peu de gel. Les gelées
      arrivent par nuit CLAIRE et calme.

    WIND CHILL (sprint VENT & ÉVAPOTRANSPIRATION ③, §5.5) : le vent LOCAL abaisse
    encore la T_min ressentie (`−WINDCHILL_COEF·eco.vent[r,c]`) — un coin ABRITÉ
    (vent local faible) garde sa chaleur, cohérent avec le brise-vent §4. Lit le
    champ d'abri SPATIALISÉ (③) ; à `eco.vent` nul (calme / pas de tick d'abri) le
    terme est NUL → comportement ②/historique inchangé.

    Pure, zéro RNG, zéro effet de bord (philo #3 — lit `eco.snow`/`eco.vent`/
    `couvert_at`, ne les écrit pas)."""
    couvert = _couvert_nuit(eco, r, c)
    t_min = t_air - RAYONNEMENT_NOCTURNE * (1.0 - couvert) * (1.0 - nebulosite)
    return t_min - WINDCHILL_COEF * eco.vent.at_plot(r, c)


def microbe_clim_factor(t_sol: float, hum_norm: float) -> float:
    """Facteur CLIMATIQUE de l'activité microbienne ∈ [MICROBE_CLIM_FLOOR, 1]
    (sprint météo→champs ④, CONCEPTION_METEO_CHAMPS §5). Terme MULTIPLICATIF, PAS
    un champ neuf : `tick_decomposition` le pose sur la vitesse de décompo, donc sur
    le recyclage ET (indirectement) sur le microbiome. Pur, zéro RNG, zéro effet de
    bord — calcul isolé ici comme `t_min_nuit_at` (couche `fields`).

        f_clim = max(FLOOR, f_temp · f_hum)

    - `f_temp` : CLOCHE gaussienne centrée sur `MICROBE_T_OPT` (~20 °C), de demi-
      largeur `MICROBE_T_TOL`. = 1 à l'optimum, → 0 au gel (dormance) ET à la
      canicule (stress thermique). `exp(−((T_sol − OPT)/TOL)²)`.
    - `f_hum` : nul au sol SEC (microbes dormants), monte LINÉAIREMENT jusqu'à 1 au
      sol FRAIS (`hum_norm = MICROBE_HUM_OPT`), puis REDESCEND vers
      `MICROBE_HUM_SAT_FLOOR` à saturation (`hum_norm = 1`) — l'anoxie freine un peu
      l'aérobie (le « léger ↓ » de la Pluie prolongée, §5).

    `hum_norm` = `min(1, humidite/3)` (MÊME échelle que `tick_thermique`). Le plancher
    `MICROBE_CLIM_FLOOR` évite un f_clim nul DUR (la décompo abiotique/fongique ne
    s'arrête jamais tout à fait). À f_clim ≈ 1 (sol doux et frais), décompo INCHANGÉE."""
    f_temp = math.exp(-(((t_sol - MICROBE_T_OPT) / MICROBE_T_TOL) ** 2))
    if hum_norm <= MICROBE_HUM_OPT:
        # Branche SÈCHE → OPTIMUM : 0 au sec, 1 au sol frais (montée linéaire).
        f_hum = hum_norm / MICROBE_HUM_OPT if MICROBE_HUM_OPT > 0.0 else 1.0
    else:
        # Branche OPTIMUM → SATURATION : redescend de 1 vers le plancher d'anoxie.
        t = (hum_norm - MICROBE_HUM_OPT) / (1.0 - MICROBE_HUM_OPT)
        f_hum = 1.0 - t * (1.0 - MICROBE_HUM_SAT_FLOOR)
    return max(MICROBE_CLIM_FLOOR, f_temp * f_hum)


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
