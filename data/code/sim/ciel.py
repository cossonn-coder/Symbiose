"""
SYMBIOSE — sim/ciel.py
Lecture AGRÉGÉE du ciel : préavis du composé catastrophe + « ciel de la semaine ».

Sprint effondrement météo, tronçon ② (docs/champs/climat/conception_effondrement_meteo.md §3).
`sim/weather.py` annonce chaque événement à venir ISOLÉMENT (`weather_signs`,
`forecast`). Un effondrement est un COMPOSÉ : plusieurs événements haute intensité
rapprochés — « l'hiver de tous les dangers ». Ce module ajoute la lecture du composé
et l'agrégat que le pont/encart Godot (tronçon ④) consommera.

Tout ici est READ-ONLY sur la fonction météo pure : on LIT `forecast`/`weather_signs`/
`weather_state` (le « cadeau de la fonction pure », §3), on ne TIRE rien de neuf et on
ne touche AUCUN champ de simulation. Zéro RNG vivant (philo #3), aucun impact sur le
golden. Couches : ce module vit dans `sim` et n'importe que `sim.weather` (même
couche) — jamais une couche haute (engine).
"""

from __future__ import annotations
from dataclasses import dataclass

from sim.weather import (
    CALME, forecast, weather_signs, weather_state, WeatherSign,
)


# --- Calibrage de la convergence (post-test F5, docs …/conception_effondrement_meteo.md §3) ---
# Fenêtre resserrée dans laquelle on cherche la GRAPPE d'événements. Volontairement
# courte (3 semaines) : un composé, c'est le danger qui se DENSIFIE, pas la simple
# somme de l'année. `forecast` étant O(H), le coût reste négligeable (une fois/semaine).
HORIZON_COMPOSE = 3

# Intensité (en σ, magnitude de `hash_gauss`) qu'un événement doit atteindre pour
# COMPTER dans le composé. En deçà, l'événement est trop faible pour peser sur « l'hiver
# de tous les dangers » — on ne veut pas que des bruines minuscules gonflent le score.
SEUIL_SEVERE = 0.8

# Seuil de GRAVITÉ (scalaire de convergence) au-delà duquel on déclare un composé.
# La convergence est la somme des intensités sévères de la fenêtre → un composé peut
# naître d'UN événement exceptionnel (grêle à ~1.9 σ) OU de PLUSIEURS coups moyens
# rapprochés : dans les deux cas, le danger cumulé justifie « l'hiver de tous les
# dangers ». Calibré ~0.8 composé/an sur seed 12345 (F5 ajustable, non gravé au golden).
COMPOSE_SEUIL = 1.8

# Palier de maîtrise « météo/climat » (0..5, cf. sim/maitrise.py) à partir duquel le
# joueur NOMME le composé. 4 = expertise. Sous ce seuil, le ciel s'assombrit quand même
# (signe perceptif toujours montré, §5) mais rien ne le nomme — le masque §4.3 ne touche
# QUE la lecture, jamais l'événement (déterminisme simulatoire intact).
NOMMAGE_PALIER = 4

# Signe diégétique INTENSIFIÉ du composé (§3.b) — donnée, voix naturaliste, français
# accentué. Aucune logique de rendu, aucun chiffre (philo #5) : la couche d'affichage
# (encart ④) traduira ces libellés en ciel qui vire au plomb.
SIGNE_COMPOSE: tuple[str, ...] = (
    "les oiseaux s'affolent puis désertent d'un coup",
    "le ciel se plombe, un poids sourd s'installe dans l'air",
    "une lumière basse, jaune et sale, écrase le jardin",
)

# Nom du composé — révélé seulement au palier ≥ NOMMAGE_PALIER (voix carnet, §5).
NOM_COMPOSE = "l'hiver de tous les dangers"


def convergence(seed: int, week: int, horizon: int = HORIZON_COMPOSE) -> float:
    """
    Niveau de CONVERGENCE à la semaine `week` : densité de danger météo à venir.

    On évalue `forecast` sur la fenêtre resserrée et on SOMME l'intensité des
    événements assez sévères (≥ `SEUIL_SEVERE`, calme exclu). Le scalaire monte quand
    plusieurs coups durs se rapprochent — ou qu'un seul, exceptionnel, approche. C'est
    une pure LECTURE de la fonction météo (comme le forecast lui-même) : PURE,
    déterministe, sans état, sans RNG (philo #3). Ce n'est PAS un nouvel événement.
    """
    total = 0.0
    for ev in forecast(seed, week, horizon):
        if ev.kind != CALME.kind and ev.intensity >= SEUIL_SEVERE:
            total += ev.intensity
    return round(total, 3)


def est_compose(seed: int, week: int) -> bool:
    """Vrai si un composé catastrophe (« l'hiver de tous les dangers ») approche —
    convergence au-delà du seuil de gravité. Pure et déterministe."""
    return convergence(seed, week) >= COMPOSE_SEUIL


@dataclass(frozen=True)
class CielSemaine:
    """
    Agrégat immuable du ciel de la semaine courante (philo #3 — même patron que
    `WeatherEvent`/`WeatherSign`). Structure PRÊTE À SÉRIALISER par le pont (tronçon ④),
    équivalent Python de l'encart Godot (CLAUDE.md « toute mécanique Godot a son
    équivalent Python »). La couche d'affichage rend, ne calcule rien.
    """
    evenement_courant: str            # kind météo de la semaine ("Beau temps" si calme)
    nebulosite: float                 # couverture nuageuse de fond [0,1] (couleur du ciel)
    convergence: float                # densité de danger à venir (scalaire de gravité)
    signes: tuple[WeatherSign, ...]   # signes lisibles 1-2 sem en avant (par événement)
    signe_compose: tuple[str, ...]    # signe intensifié SI composé, () sinon (perceptif)
    nom_compose: str | None           # nom du composé — seulement si palier ≥ seuil


def ciel_semaine(seed: int, week: int, palier_climat: int = 0,
                 horizon: int = 2) -> CielSemaine:
    """
    « Ciel de la semaine » : agrège, pour la semaine courante, tout ce que le joueur
    peut LIRE du ciel (§3.c). PURE, read-only sur la simulation.

    Contenu :
      - `evenement_courant` + `nebulosite` : l'état atmosphérique de fond (via
        `weather_state`, la couleur/nuages implicites du ciel actuel) ;
      - `signes` : les signes des événements qui tombent dans 1..`horizon` semaines
        (`weather_signs`, chacun avec son masque `signed` §4.3) ;
      - `convergence` + `signe_compose` : le préavis du composé (a/b). Le signe
        intensifié est TOUJOURS présent dès qu'un composé approche (le ciel s'assombrit
        pour tous, §5) — seul le `nom_compose` dépend du palier de maîtrise climat.

    Le filtrage fin des `signes` selon le palier reste à la charge de l'appelant
    (couche UI / D12), comme pour `weather_signs`.
    """
    event, _t_air, nebul = weather_state(seed, week)
    signes = tuple(weather_signs(seed, week, horizon))
    conv = convergence(seed, week)
    compose = conv >= COMPOSE_SEUIL

    signe_compose = SIGNE_COMPOSE if compose else ()
    nom = NOM_COMPOSE if (compose and palier_climat >= NOMMAGE_PALIER) else None

    return CielSemaine(
        evenement_courant=event.kind,
        nebulosite=nebul,
        convergence=conv,
        signes=signes,
        signe_compose=signe_compose,
        nom_compose=nom,
    )
