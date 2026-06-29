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
import math
from dataclasses import dataclass

from fields import _hash_noise, hash_gauss, climate_stress
from fields.ecofields.constants import NEBULOSITE   # table météo→nébulosité (④, donnée PURE côté fields)


# --- Canaux-sentinelles ----------------------------------------------------
# `_hash_noise(seed, week, r, c)` mélange seed/semaine/coordonnées. En réservant
# des coordonnées (r, c) TRÈS au-delà de la grille des plots (au plus 6×8), les
# tirages météo deviennent décorrélés des tirages spatiaux du sol (sénescence,
# reproduction, perturbation…). Chaque canal = un flux indépendant.
K_OCC  = (90_001, 0)   # un événement a-t-il lieu, ou temps calme ?
K_PICK = (90_002, 0)   # lequel (parmi les candidats de la saison) ?
K_MAG  = (90_003, 0)   # intensité (loi normale via hash_gauss)
K_PEST = (90_004, 0)   # ravageur (canal séparé, hors météo)
K_SIGN = (90_005, 0)   # un événement émet-il un signe diégétique ? (§4.3)

# Probabilité qu'une SEMAINE porte un VRAI événement (sinon temps calme).
# Sous-sprint 02 : la météo passe en cadence HEBDOMADAIRE (consultée chaque
# semaine, plus seulement au passage de saison) → P_EVENT abaissé de 0.60 (01,
# 4×/an) à 0.15 pour viser ~8 événements notables/an et laisser le jardin
# survivre 30 ans. Calibrage post-test (CONCEPTION_METEO.md §5).
P_EVENT = 0.15

# --- Climat normal saisonnier (CONCEPTION_METEO.md §1.1) -------------------
# Normale de température : sinusoïde Normandie océanique. Minimum ~semaine 4
# (fin janvier), maximum ~semaine 30 (fin juillet). Faible amplitude (hivers
# doux, étés frais). T_MOY/T_AMP = calibrage post-test.
T_MOY = 11.0   # °C — moyenne annuelle
T_AMP = 7.0    # °C — demi-amplitude saisonnière
# Dérive interannuelle (§1.2) : on réutilise climate_stress (±CLIMATE_AMPLITUDE
# ≈ ±0.08) ; ce facteur la convertit en ±~1 °C de « caractère » d'année.
DRIFT_TEMP = 12.0

# --- Deltas de température par événement (CONCEPTION_METEO.md §2.1/2.2) -----
# Gel/canicule/redoux migrent de leur mapping provisoire WEATHER_ALEA (humidité/
# santé, 01) vers de VRAIS deltas de température transitoires. Les autres
# événements (Sécheresse, Tempête, Grêle, Pluie prolongée) gardent leur effet
# milieu existant via WEATHER_ALEA (engine) — remplacement progressif (03).
TEMP_DELTA_BASE = {
    "Gelée tardive": -9.0,   # plonge sous 0 au printemps → gate de croissance + (gel tissulaire = 03)
    "Canicule":      +7.0,   # été brûlant → évaporation accrue (couplage hydrologie)
    "Redoux":        +5.0,   # hiver doux → réveil prématuré (vulnérabilité émergente)
    "Neige":         -6.0,   # ⑦ : tombe sous 0 → entre dans TEMP_DRIVEN, déclenche le gel ET dépose le manteau neigeux (effet igloo, cf. thermique.t_min_nuit_at)
}
# Événements pilotés par la température (pas d'effet WEATHER_ALEA en plus).
TEMP_DRIVEN = frozenset(TEMP_DELTA_BASE)


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
    ("Neige",            "global", 2,     (44, 52)),   # ⑦ cœur de l'hiver (état multi-semaines, dépose le manteau)
    ("Orage",            "local",  1,     (16, 30)),   # ⑦ été (orages convectifs : pluie battante + vent)
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


def temp_norm(week_in_year: int, year_fraction: float | None = None,
              phase: float = 0.0) -> float:
    """
    Température NORMALE de la semaine (°C) — toile de fond lisse, 100 % prévisible
    (CONCEPTION_METEO.md §1.1) : `T_MOY − T_AMP·cos(2π·(w − 4)/52)`.

    `week_in_year` ∈ [1, 52]. Si `year_fraction` est fourni, on superpose la dérive
    interannuelle `climate_stress` (§1.2, `phase` dérivée du seed) → certaines
    années plus fraîches/douces, sur plusieurs ans. Fonction PURE (pas de RNG).
    """
    base = T_MOY - T_AMP * math.cos(2.0 * math.pi * (week_in_year - 4) / 52.0)
    if year_fraction is not None:
        base += climate_stress(year_fraction, phase) * DRIFT_TEMP
    return base


def temperature_delta(event: WeatherEvent) -> float:
    """
    Delta de température transitoire (°C) porté par un `WeatherEvent`, modulé par
    son intensité (magnitude en σ). 0 pour les événements non thermiques (le
    milieu réagit alors via WEATHER_ALEA côté engine). Pure et déterministe.
    """
    base = TEMP_DELTA_BASE.get(event.kind, 0.0)
    if base == 0.0:
        return 0.0
    # intensity ∈ [~0, ~3] (abs d'une normale) ; on garantit un effet plancher
    # quand l'événement tombe et on borne pour éviter les extrêmes absurdes.
    scale = max(0.5, min(2.0, event.intensity))
    return base * scale


def weather_state(seed: int, week: int) -> tuple[WeatherEvent, float, float]:
    """
    État météo COMPLET de la semaine `week` : `(événement, T_air °C, nébulosité)`.
    Point de vérité UNIQUE du calcul que l'engine (boucle.py étape 1) et le
    snapshot (serialize.py §A) faisaient à l'identique — un seul endroit pour
    qu'ils ne divergent jamais. PURE et déterministe (aucun état moteur lu).

    `T_air` = normale saisonnière (avec dérive interannuelle, `phase` dérivée du
    seed = « caractère d'année ») + delta transitoire de l'événement.

    `nébulosité` — sprint VENT & ÉVAPOTRANSPIRATION ② (§2.3) : la couverture nuageuse
    n'est plus la table figée `NEBULOSITE[kind]`, elle est DYNAMIQUE sous le vent. La
    table donne le POINT DE DÉPART (couverture de référence de l'événement), le vent
    la CHASSE : un vent fort disperse la couche (`nebulosite_dynamique` ①). C'est le
    couplage le plus structurant du sprint — la nébulosité gouverne ensuite la lumière,
    la rosée et la thermique. Vent nul → couverture figée inchangée (golden re-figé
    LARGE annoncé : tout le bloc lumière/rosée/thermique bouge ensemble).

    Import LOCAL de `wind` : `wind.py` importe déjà `weather_at`/`CALME` de ce module
    → un import au niveau module créerait un cycle. L'import différé (au 1er appel)
    le résout sans dupliquer le catalogue de nébulosité.
    """
    from sim.wind import nebulosite_dynamique   # local : évite le cycle weather↔wind
    week_in_year  = ((week - 1) % 52) + 1
    event         = weather_at(seed, week)
    year_fraction = (week - 1) / 52.0
    phase         = (seed & 0xFFFF) / 0xFFFF * 2.0 * math.pi
    t_air         = temp_norm(week_in_year, year_fraction, phase) + temperature_delta(event)
    nebul         = nebulosite_dynamique(seed, week)
    return event, t_air, nebul


def forecast(seed: int, week: int, horizon: int = 2) -> list[WeatherEvent]:
    """
    Prévision (D16) — « cadeau de la fonction pure » : prévoir = évaluer
    `weather_at` en avance. La semaine venue, l'engine calcule LA MÊME fonction →
    prévision == réalité, par construction. (Les signes du sous-sprint 04 liront
    ceci ; l'engine ne s'en sert pas encore.)
    """
    return [weather_at(seed, week + k) for k in range(1, horizon + 1)]


# --- Signes diégétiques (Z2, CONCEPTION_METEO.md §4) ------------------------
# Un signe = un indice perceptif rendu dans le monde 1-2 semaines AVANT
# l'événement (jamais d'icône calendrier, philo #5). Ces libellés sont des
# DONNÉES (français, voix naturaliste) que la couche d'affichage (Godot, plus
# tard) traduira en sprites/sons. AUCUNE logique de rendu ici.
#
# Table recopiée fidèlement de §4.1. Note : la spec groupe « Canicule /
# sécheresse » sur une même ligne → Canicule et Sécheresse partagent leurs
# signes. C'est l'ambiguïté VOULUE (§4.1 « certains signes sont ambigus entre
# deux événements proches ») : un même signe pointe vers plusieurs événements,
# ce qui crée l'incertitude d'interprétation des débuts.
_SIGNES_CHALEUR_SEC = (
    "ciel blanc laiteux",
    "insectes au ras du sol",
    "sol qui craquelle",
    "feuilles qui se recroquevillent",
)
SIGN_TABLE: dict[str, tuple[str, ...]] = {
    "Gelée tardive": (
        "ciel clair et étoilé au crépuscule",
        "brume rasante au petit matin",
        "anneau (halo) autour de la lune",
    ),
    "Canicule": _SIGNES_CHALEUR_SEC,
    "Sécheresse": _SIGNES_CHALEUR_SEC,
    "Tempête": (
        "oiseaux qui se taisent puis s'agitent et volent bas",
        "le vent tourne",
        "ciel qui vire au plomb",
    ),
    "Grêle": (
        "nuages d'enclume sombres",
        "chute brutale de la lumière",
        "calme lourd « avant l'orage »",
    ),
    "Pluie prolongée": (
        "ciel bas et gris constant",
        "escargots et limaces qui sortent",
        "hirondelles qui rasent le sol",
    ),
    "Redoux": (
        "fonte, gouttes",
        "oiseaux qui se remettent à chanter",
    ),
    "Neige": (
        "ciel bas et ouaté",
        "silence feutré, sons étouffés",
        "air qui pique et sèche",
    ),
    "Orage": (
        "chaleur lourde et moite",
        "cumulus qui bourgeonnent en tours",
        "premiers grondements lointains",
    ),
}


def is_signed(seed: int, week: int) -> bool:
    """
    Masque de signe (§4.3) : l'événement de la semaine `week` émet-il un signe
    diégétique ? ~80 % oui. PURE et déterministe.

    `week` = la semaine ABSOLUE de l'ÉVÉNEMENT (pas la semaine d'observation) →
    un événement donné est signé (ou non) de façon STABLE, qu'on l'observe à
    j-1 ou j-2. Les ~20 % non signés arrivent sans préavis tant qu'on n'est pas
    transcendant ; au transcendant, le palier lève le masque CÔTÉ UI (l'événement
    lui-même ne change pas — seule la visibilité de son signe dépend de la
    maîtrise, déterminisme simulatoire intact).
    """
    return _hash_noise(seed, week, *K_SIGN) > 0.20


@dataclass(frozen=True)
class WeatherSign:
    """
    Lecture perceptive d'un événement météo à venir, structure immuable (philo
    #3). `signed` porte le masque §4.3 : l'appelant (couche palier/UI, D12)
    décide d'afficher les `signed=True` seulement (sous transcendant), ou de
    tout révéler au transcendant — sans re-toucher ce module.
    """
    kind: str                  # type de l'événement annoncé
    in_weeks: int              # dans combien de semaines il tombe (1..horizon)
    signs: tuple[str, ...]     # signes perceptifs (données, voix naturaliste)
    signed: bool               # émet-il un signe ? (~80 %, §4.3)


def weather_signs(seed: int, week: int, horizon: int = 2) -> list[WeatherSign]:
    """
    Signes diégétiques visibles à la semaine `week` parce qu'un événement météo
    arrive dans 1..`horizon` semaines (§4). PURE, sans état, sans RNG live : on
    lit `weather_at` en avance (le « cadeau de la fonction pure », §3) et on
    classe. Read-only sur la simulation — n'écrit dans aucun champ.

    Renvoie la structure COMPLÈTE (tous les événements à venir, calme exclu),
    chacun avec son flag `signed` (décision actée 04). Le filtrage selon le
    palier de maîtrise (D12) est à la charge de l'appelant.
    """
    out: list[WeatherSign] = []
    for k in range(1, horizon + 1):
        ev = weather_at(seed, week + k)
        if ev.kind == CALME.kind:        # temps calme : aucun signe
            continue
        out.append(WeatherSign(
            kind=ev.kind,
            in_weeks=k,
            signs=SIGN_TABLE[ev.kind],
            signed=is_signed(seed, week + k),
        ))
    return out
