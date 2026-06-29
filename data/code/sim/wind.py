"""
SYMBIOSE — sim/wind.py
Vent déterministe : `wind_at(seed, week)` — la MASSE D'AIR, fonction PURE du temps.

Pivot du sprint VENT & ÉVAPOTRANSPIRATION (CONCEPTION_VENT_EVAPOTRANSPIRATION.md
§2). Calqué EXACTEMENT sur `weather.py` : canaux-sentinelles décorrélés, zéro RNG
vivant (philo #3 — déterminisme = seed global + hash de bruit spatial). Deux runs
identiques → vent identique, et le vent est *évaluable en avance* (forecast,
signes) comme la météo.

Périmètre de CE tronçon (①) : on CALCULE la masse d'air (force/direction), ses
régimes intra-journaliers (§2.2) et une nébulosité DYNAMIQUE pilotée par le vent
(§2.3) — mais on ne BRANCHE rien en aval. Personne ne lit ce module dans la boucle
→ golden NEUTRE (bit-identique). Le câblage réel (évapotranspiration, lumière,
rosée, thermique) = tronçon ②.

Couches : ce module vit dans `sim` et n'importe que `fields` (couche basse, le
hash) + `sim.weather` (même couche, pour réutiliser `weather_at`/`NEBULOSITE` sans
dupliquer le catalogue). Aucun import de `sim.engine` (sinon cycle).
"""

from __future__ import annotations
import math
from dataclasses import dataclass

from fields import _hash_noise
from fields.ecofields.constants import NEBULOSITE   # table figée météo→nébulosité (§2.3)
from sim.weather import weather_at, CALME


# --- Canaux-sentinelles vent ----------------------------------------------
# Mêmes principes que `weather.py` : des coordonnées (r, c) réservées TRÈS au-delà
# de la grille des plots décorrèlent ces tirages de tout flux spatial du sol ET des
# tirages météo (qui vivent en 90_00x). Le vent occupe la tranche 90_01x.
K_WIND = (90_010, 0)   # force de fond hebdo (canal principal de la masse d'air)
K_DIR  = (90_011, 0)   # graine de la marche de direction (le vent « tourne »)
K_GUST = (90_012, 0)   # phase des risées intra-journalières (§2.2)

# --- Calibrage force de fond (CONCEPTION §2.1) ----------------------------
# La force de FOND d'une semaine calme est tirée du canal K_WIND ∈ [0,1[, puis
# étalée vers une brise typique. WIND_BASE_SCALE comprime ce tirage : l'essentiel
# du temps on veut une brise faible (~0.2–0.4), pas un coup de vent.
WIND_BASE_SCALE = 0.55
# Saisonnalité : automne/hiver plus venteux (cf. fenêtres Tempête/Pluie prolongée
# du catalogue météo). Sinusoïde minimale en été (~sem 26), maximale au cœur de
# l'hiver (~sem 52/0). WIND_SEASON_AMP = demi-amplitude ajoutée à la force.
WIND_SEASON_AMP = 0.20
# Forces imposées par les événements météo venteux (on CONTINUISE le vent que la
# Tempête/l'Orage portaient déjà comme dégât ponctuel ; Beau temps ≈ brise faible).
WIND_EVENT_FORCE = {
    "Tempête": 1.20,   # coup de vent soutenu (>1)
    "Orage":   0.95,   # rafales convectives
    "Beau temps": None,   # None = pas d'imposition, on garde la force de fond
}

# --- Régimes intra-journaliers (CONCEPTION §2.2) --------------------------
# Enveloppe TEMPORELLE pure appliquée à la force hebdo — PAS de simulation fluide,
# juste un scalaire par sous-tick. SUBTICKS découpe la « journée » simulée ; chaque
# sous-tick a un facteur de modulation (nul / risées / brise de fin de journée).
SUBTICKS = 4
# Seuil de probabilité d'un régime de RISÉES sur la semaine (tiré de K_GUST) :
# en dessous, semaine « lisse » (modulation douce) ; au-dessus, semaine à rafales.
GUST_THRESHOLD = 0.65
# Amplitude du pic de risée (multiplie la force de fond sur le sous-tick de pointe).
GUST_PEAK = 1.8
# Brise de fin de journée (effet venturi thermique §2.2) : léger surcroît de force
# sur le DERNIER sous-tick (l'après-midi se lève une brise). Facteur multiplicatif.
BREEZE_EVENING = 1.25

# --- Couplage vent ↔ nébulosité (CONCEPTION §2.3) -------------------------
# La nébulosité figée NEBULOSITE[kind] devient le POINT DE DÉPART ; le vent la
# pousse : un vent fort CHASSE/DISPERSE la couverture (nébulosité ↓), un vent nul
# la laisse STAGNER (valeur figée inchangée). NEBUL_WIND_CLEAR = part max chassée
# par un vent à force 1. (Le volet « amène les nuages d'un secteur humide » est
# laissé au câblage directionnel du tronçon ② — ici on garde le pilote sobre.)
NEBUL_WIND_CLEAR = 0.45


@dataclass(frozen=True)
class WindState:
    """
    État de vent de la MASSE D'AIR pour une semaine, structure immuable (philo #3).
    `force` ∈ [0, 1+] (0 nul · ~0.3 brise · ~0.7 soutenu · >1 coup de vent) ;
    `direction` ∈ [0, 2π) = d'où vient le vent (varie lentement). La force LOCALE
    par plot (abri/venturi) viendra par-dessus au tronçon ③ — ici c'est uniforme.
    """
    force: float
    direction: float


# Direction : période de la dérive lente (en semaines) et nombre d'harmoniques.
# Une somme de quelques sinusoïdes de basse fréquence donne une rotation « qui
# tourne » sans répétition évidente, en O(1) (≠ marche cumulée O(week)).
DIR_PERIOD = 73.0     # ~1.4 an : le secteur dominant dérive sur plus d'une saison
DIR_HARMONICS = 3


def _direction_at(seed: int, week: int) -> float:
    """
    Direction de la masse d'air ∈ [0, 2π) — dérive LENTE déterministe (le vent
    « tourne » d'une semaine à l'autre, pas de saut brutal). PURE et **O(1)** :
    somme fermée de quelques sinusoïdes basse fréquence (phases/amplitudes tirées
    du hash), au lieu d'une marche cumulée depuis la semaine 1 (qui serait O(week)
    et coûterait des ms en fin de partie — `wind_at` est appelé chaque tick au ②).

    Le seed fixe le secteur dominant du terrain (vents dominants uniques par
    jardin) ; les harmoniques font lentement tourner ce secteur.
    """
    # Phase de base dérivée du seed (chaque terrain a son régime de vents dominants).
    angle = (seed & 0xFFFF) / 0xFFFF * 2.0 * math.pi
    for k in range(1, DIR_HARMONICS + 1):
        phase = _hash_noise(seed, k, *K_DIR) * 2.0 * math.pi
        amp = 0.6 / k   # harmoniques hautes plus discrètes → dérive douce
        angle += amp * math.sin(2.0 * math.pi * week / (DIR_PERIOD / k) + phase)
    return angle % (2.0 * math.pi)


def wind_at(seed: int, week: int) -> WindState:
    """
    Vent de la MASSE D'AIR pour la semaine `week`, PUR et déterministe (§2.1).

    Force = force de FOND (canal K_WIND + saisonnalité automne/hiver), SAUF si
    l'événement météo de la semaine impose une force (Tempête/Orage la forcent
    haute, Beau temps laisse la brise de fond). `week` est ABSOLUE (le vent varie
    d'une année sur l'autre) ; `week_in_year` ne sert qu'à la saisonnalité.
    """
    wiy = ((week - 1) % 52) + 1

    # Force de fond : tirage comprimé + saisonnalité (max au cœur de l'hiver).
    base = _hash_noise(seed, week, *K_WIND) * WIND_BASE_SCALE
    saison = WIND_SEASON_AMP * math.cos(2.0 * math.pi * (wiy - 4) / 52.0)
    # NB : +cos(... (wiy-4) ...) est l'OPPOSÉ de la normale de température
    # (`temp_norm = T_MOY − T_AMP·cos(...)`) → venteux quand il fait froid (hiver,
    # wiy≈4/52), calme l'été (wiy≈30). Cohérent §2.1 (automne/hiver plus venteux).
    force = max(0.0, base + saison)

    # Un événement venteux écrase la force de fond (on continuise le dégât ponctuel).
    event = weather_at(seed, week)
    imposed = WIND_EVENT_FORCE.get(event.kind, 0.0)
    if imposed is not None and imposed > force:
        # intensity (en σ) module l'événement, comme temperature_delta côté météo.
        force = imposed * max(0.6, min(1.6, 0.6 + event.intensity * 0.4))

    return WindState(force=round(force, 4), direction=round(_direction_at(seed, week), 4))


def gust_profile(seed: int, week: int) -> tuple[float, ...]:
    """
    Régimes intra-journaliers (§2.2) : enveloppe TEMPORELLE pure de `SUBTICKS`
    facteurs multiplicatifs appliqués à la force hebdo au fil de la « journée ».
    PURE, O(SUBTICKS) = O(1). Trois figures possibles selon le tirage K_GUST :

      - **lisse** (semaine calme) : modulation douce, légère brise de fin de jour ;
      - **risées** : un sous-tick de pointe (`GUST_PEAK`) → pic d'assèchement et de
        sollicitation mécanique ponctuel (lu plus tard par évapo/thigmo) ;
      - **brise de fin de journée** : le DERNIER sous-tick relevé (`BREEZE_EVENING`,
        venturi thermique) dans tous les cas.

    Renvoyer un PROFIL (pas un scalaire) laisse l'appelant choisir d'intégrer (perte
    hydrique moyenne) ou de lire le pic (dégât mécanique) — sans recalcul.
    """
    g = _hash_noise(seed, week, *K_GUST)
    profile = []
    for s in range(SUBTICKS):
        f = 1.0
        if g >= GUST_THRESHOLD:
            # Risées : pic sur le sous-tick désigné par la phase, creux ailleurs.
            peak_tick = int(g * SUBTICKS) % SUBTICKS
            f = GUST_PEAK if s == peak_tick else 0.6
        if s == SUBTICKS - 1:
            f *= BREEZE_EVENING   # brise de fin de journée, toujours présente
        profile.append(round(f, 3))
    return tuple(profile)


def nebulosite_dynamique(seed: int, week: int) -> float:
    """
    Nébulosité DYNAMIQUE pilotée par le vent (§2.3) — remplace, à terme, la lecture
    figée `NEBULOSITE[kind]` de `weather_state`. ICI elle est seulement CALCULÉE,
    pas branchée (golden neutre) ; le tronçon ② la substituera dans `weather_state`.

    Modèle sobre : on part de la valeur figée (couverture « de référence » de
    l'événement) et le vent la CHASSE — un vent fort disperse la couche nuageuse.
    Vent nul → couverture figée inchangée (stagnation). PURE et déterministe.
    """
    event = weather_at(seed, week)
    base = NEBULOSITE.get(event.kind, 0.10 if event.kind == CALME.kind else 0.10)
    force = wind_at(seed, week).force
    # Un vent à force 1 chasse jusqu'à NEBUL_WIND_CLEAR de la couverture ; borné.
    cleared = base * (1.0 - NEBUL_WIND_CLEAR * min(1.0, force))
    return round(max(0.0, min(1.0, cleared)), 4)
