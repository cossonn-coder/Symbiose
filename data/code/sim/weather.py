"""
SYMBIOSE — sim/weather.py
Météo déterministe : `weather_at(seed, week)` — fonction PURE du temps, sans état.

Pivot de la conception météo (CONCEPTION_METEO.md §0-1). L'ancien moteur tirait
l'aléa de saison avec `random.choice(ALEAS_METEO)` : un RNG *live* qui consommait
l'état global de `random` et ne restait déterministe que grâce à une béquille
`random.seed(42)` — ce qui violait la philo #3 (déterminisme = seed global + hash
spatial, jamais de RNG vivant). On remplace ce tirage par une fonction pure à
base de `_hash_noise`. Bénéfice clé : une fonction pure du temps est *évaluable
en avance sans faire avancer la simulation* → le forecast (D16, sous-sprint 04)
et les signes (Z2) en découlent gratuitement.

Périmètre de CE sous-sprint (01) : déterminisation SEULE. `weather_at` produit un
`WeatherEvent` riche (catalogue + saisonnalité §1.3) ; l'engine le mappe vers les
effets `Alea` EXISTANTS (humidité/paillage/santé), couplage inchangé. La
température (02), les réponses médiées par gène (03) et le forecast (04)
viendront s'y brancher ensuite.

Couches : ce module vit dans `sim` et n'importe que `fields` (couche basse) —
aucun import de `sim.engine` (sinon cycle, car engine importe weather).
"""

from __future__ import annotations
from dataclasses import dataclass

from fields import _hash_noise, hash_gauss


# --- Canaux-sentinelles ----------------------------------------------------
# `_hash_noise(seed, week, r, c)` mélange seed/semaine/coordonnées. En réservant
# des coordonnées (r, c) TRÈS au-delà de la grille des plots (au plus 6×8), les
# tirages météo deviennent décorrélés des tirages spatiaux du sol (sénescence,
# reproduction, perturbation…). Chaque canal = un flux indépendant.
K_OCC  = (90_001, 0)   # un événement a-t-il lieu, ou temps calme ?
K_PICK = (90_002, 0)   # lequel (parmi les candidats de la saison) ?
K_MAG  = (90_003, 0)   # intensité (loi normale via hash_gauss)
K_PEST = (90_004, 0)   # ravageur (canal séparé, hors météo)

# Probabilité qu'un début de saison porte un VRAI événement (sinon temps calme).
# Calibrage indicatif (post-test, cf. CONCEPTION_METEO.md §5) — l'ancien modèle
# avait presque toujours un aléa actif au passage de saison.
P_EVENT = 0.60


@dataclass(frozen=True)
class WeatherEvent:
    """
    Un événement météo, structure de donnée immuable (philo #3 — pas de table
    mutable). `intensity` et `scope`/`duration_weeks` sont portés dès maintenant
    pour le forecast (04) et les réponses médiées (03), même si l'engine ne les
    exploite pas encore au sous-sprint 01.
    """
    kind: str
    intensity: float = 0.0       # magnitude en σ (hash_gauss), 0 pour le calme
    duration_weeks: int = 1      # ponctuel (1) vs état multi-semaines (>1)
    scope: str = "global"        # "global" (toute la tuile) | "local" (patch)


# Cas par défaut : temps calme, aucun effet.
CALME = WeatherEvent("Beau temps", 0.0, 1, "global")

# Catalogue §1.3 — (kind, scope, durée, fenêtre saisonnière en week_in_year).
# Calendrier du moteur : printemps 1-13, été 14-26, automne 27-39, hiver 40-52.
# Les fenêtres collent à ce calendrier (les semaines « p.ex. » de la spec étaient
# indicatives). Distinction ponctuel (durée 1) vs état climatique (durée > 1).
_CATALOGUE = [
    # kind,              scope,    durée, fenêtre (lo, hi)
    ("Gelée tardive",    "global", 1,     (8, 15)),    # fin de printemps
    ("Canicule",         "global", 2,     (16, 26)),   # été
    ("Sécheresse",       "global", 4,     (18, 32)),   # été → début automne (état)
    ("Tempête",          "global", 1,     (27, 52)),   # automne + hiver
    ("Grêle",            "local",  1,     (10, 26)),   # orages de fin printemps/été
    ("Pluie prolongée",  "global", 3,     (27, 52)),   # automne + hiver (état)
    ("Redoux",           "global", 1,     (40, 52)),   # hiver
]


def weather_at(seed: int, week: int) -> WeatherEvent:
    """
    Tire l'événement météo de la semaine `week`, de façon PURE et déterministe.

    Modèle §1.3 à trois canaux décorrélés :
      - K_OCC  décide événement vs temps calme ;
      - K_PICK choisit parmi les candidats DE LA SAISON (la saisonnalité fait
        office de pondération : seuls les événements en fenêtre sont candidats) ;
      - K_MAG  donne l'intensité (loi normale, magnitude en σ).

    `week` est la semaine ABSOLUE (monotone sur les années) → la météo varie
    d'une année sur l'autre. `week_in_year` ne sert qu'à la saisonnalité.
    """
    wiy = ((week - 1) % 52) + 1

    occ = _hash_noise(seed, week, *K_OCC)
    if occ >= P_EVENT:
        return CALME

    cands = [e for e in _CATALOGUE if e[3][0] <= wiy <= e[3][1]]
    if not cands:
        return CALME

    pick = _hash_noise(seed, week, *K_PICK)
    kind, scope, duration, _ = cands[int(pick * len(cands)) % len(cands)]
    mag = abs(hash_gauss(seed, week, K_MAG[0], K_MAG[1]))
    return WeatherEvent(kind, round(mag, 3), duration, scope)


def forecast(seed: int, week: int, horizon: int = 2) -> list[WeatherEvent]:
    """
    Prévision (D16) — « cadeau de la fonction pure » : prévoir = évaluer
    `weather_at` en avance. La semaine venue, l'engine calcule LA MÊME fonction →
    prévision == réalité, par construction. (Les signes du sous-sprint 04 liront
    ceci ; l'engine ne s'en sert pas encore.)
    """
    return [weather_at(seed, week + k) for k in range(1, horizon + 1)]
