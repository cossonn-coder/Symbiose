"""
SYMBIOSE — sim/weather.py
Météo déterministe : `weather_at(seed, week)` — fonction PURE du temps, sans état.

Pivot de la conception météo (docs/champs/climat/conception_meteo.md §0-1). L'ancien moteur tirait
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
from calendrier import W_T_MIN, saison_de, wiy_de   # calendrier UNIQUE (D122, couche basse)


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
K_PATCH_R = (90_006, 0)  # centre du patch d'un événement local — ligne (grêle/orage)
K_PATCH_C = (90_007, 0)  # centre du patch d'un événement local — colonne
K_PLUIE   = (90_008, 0)  # épisode de pluie ORDINAIRE (sprint sol qui respire ①, D111)
K_HR      = (90_009, 0)  # bruit hebdo de l'humidité de l'air (rosée, ①)

# Rayon du patch d'un événement `scope="local"`, en fraction de la plus grande
# dimension de la tuile (sprint effondrement météo ①, §2). ~0.42 → le patch couvre
# un COIN, jamais toute la tuile ni rien : la grêle frappe une sous-zone, plus les
# 8 secteurs d'un bloc (honore `scope="local"`, longtemps déclaré mais jamais lu).
PATCH_FRAC = 0.42

# Probabilité qu'une SEMAINE porte un VRAI événement (sinon temps calme).
# Sous-sprint 02 : la météo passe en cadence HEBDOMADAIRE (consultée chaque
# semaine, plus seulement au passage de saison) → P_EVENT abaissé de 0.60 (01,
# 4×/an) à 0.15 pour viser ~8 événements notables/an et laisser le jardin
# survivre 30 ans. Calibrage post-test (docs/champs/climat/conception_meteo.md §5).
P_EVENT = 0.15

# --- Climat normal saisonnier (docs/champs/climat/conception_meteo.md §1.1) -------------------
# Normale de température : sinusoïde Normandie océanique. Minimum en wiy
# `W_T_MIN` = 45 (≈ fin janvier, convention équinoxe D122 — `calendrier.py`),
# maximum 26 semaines plus tard, wiy ≈ 19 (≈ fin juillet). Faible amplitude (hivers
# doux, étés frais). T_MOY/T_AMP = calibrage post-test.
T_MOY = 11.0   # °C — moyenne annuelle
T_AMP = 7.0    # °C — demi-amplitude saisonnière
# Dérive interannuelle (§1.2) : on réutilise climate_stress (±CLIMATE_AMPLITUDE
# ≈ ±0.08) ; ce facteur la convertit en ±~1 °C de « caractère » d'année.
DRIFT_TEMP = 12.0

# --- Deltas de température par événement (docs/champs/climat/conception_meteo.md §2.1/2.2) -----
# Gel/canicule/redoux migrent de leur mapping provisoire WEATHER_ALEA (humidité/
# santé, 01) vers de VRAIS deltas de température transitoires. Les autres
# événements (Sécheresse, Tempête, Grêle, Pluie prolongée) gardent leur effet
# milieu existant via WEATHER_ALEA (engine) — remplacement progressif (03).
TEMP_DELTA_BASE = {
    "Gelée tardive": -9.0,   # plonge sous 0 au printemps → gate de croissance + (gel tissulaire = 03)
    "Canicule":      +7.0,   # été brûlant → évaporation accrue (couplage hydrologie)
    "Redoux":        +5.0,   # hiver doux → réveil prématuré (vulnérabilité émergente)
    "Neige":         -6.0,   # ⑦ : tombe sous 0 → entre dans TEMP_DRIVEN, déclenche le gel ET dépose le manteau neigeux (effet igloo, cf. thermique.t_min_nuit_at)
    # Sprint germination thermique ① — correctif amont : une averse REFROIDIT l'air
    # (couche nuageuse + évaporation des gouttes), trou vérifié (le delta était 0.0 →
    # l'air restait aussi chaud sous la pluie). Delta froid MODÉRÉ : la pluie n'est PAS
    # un événement piloté par la température (elle garde son effet milieu humidité via
    # WEATHER_ALEA), donc elle reste HORS de TEMP_DRIVEN — `temperature_delta` se contente
    # d'AJOUTER ce froid à t_air, sans débrancher WEATHER_ALEA. Placeholder, calibrage ⑥.
    "Pluie prolongée": -3.0,
    "Orage":           -2.0,
}
# Événements pilotés par la température (pas d'effet WEATHER_ALEA en plus).
# La pluie (Pluie prolongée / Orage) porte un delta froid MAIS reste pilotée par le
# milieu : son effet humidité passe par WEATHER_ALEA (engine, branche `not in
# TEMP_DRIVEN`). On l'EXCLUT donc explicitement de cet ensemble — le froid s'ajoute à
# t_air SANS court-circuiter l'apport d'eau. Sinon `frozenset(TEMP_DELTA_BASE)` les
# happerait et débrancherait leur humidité (régression silencieuse).
_TEMP_PLUIE = frozenset({"Pluie prolongée", "Orage"})
TEMP_DRIVEN = frozenset(TEMP_DELTA_BASE) - _TEMP_PLUIE


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
# Calendrier UNIQUE (D122, `calendrier.py`) : wiy 1 ≈ 20 mars ; printemps 1-13,
# été 14-26, automne 27-39, hiver 40-52. Fenêtres recalées au MOIS RÉEL (D122 ③,
# conception_calendrier_unique §4-§5, Normandie océanique) : 1ᵉʳ avr 3 · 1ᵉʳ mai 7 ·
# 1ᵉʳ juin 11 · 1ᵉʳ juil 16 · 1ᵉʳ août 20 · 1ᵉʳ sept 24 · 1ᵉʳ oct 29 · 1ᵉʳ déc 37 ·
# 1ᵉʳ janv 42 · 1ᵉʳ mars 50. Distinction ponctuel (durée 1) vs état (durée > 1).
_CATALOGUE = [
    # kind,              scope,    durée, fenêtre (lo, hi)
    ("Gelée tardive",    "global", 1,     (2, 9)),     # avril → saints de glace (mi-mai)
    ("Canicule",         "global", 2,     (12, 24)),   # juin → août
    ("Sécheresse",       "global", 4,     (12, 28)),   # juin → sept. (état)
    ("Tempête",          "global", 1,     (27, 52)),   # automne + hiver
    ("Grêle",            "local",  1,     (7, 22)),    # mai → août (orages)
    ("Pluie prolongée",  "global", 3,     (27, 52)),   # automne + hiver (état)
    ("Redoux",           "global", 1,     (40, 52)),   # hiver
    ("Neige",            "global", 2,     (38, 49)),   # ⑦ déc. → fév. (état multi-semaines, dépose le manteau)
    ("Orage",            "local",  1,     (8, 24)),    # ⑦ mai → août (orages convectifs : pluie battante + vent)
]


# --- Épisodes de pluie ORDINAIRE (sprint « le sol qui respire » ①, D111 §1b) ---
# Diagnostic mesuré : la pluie n'existait QUE comme aléa (« Pluie prolongée »
# automne-hiver, « Orage » d'été, chacun en concurrence dans le catalogue sous
# P_EVENT=0.15) → ~1-6 semaines de pluie/an, climat méditerranéen, sol désertifié
# dès l'an 2. Un climat OCÉANIQUE pleut en toute saison : on ajoute un canal dédié
# (K_PLUIE, décorrélé des aléas) consulté SEULEMENT les semaines restées calmes →
# un aléa (Sécheresse, Canicule, Gelée…) EXCLUT donc la pluie par construction (un
# seul événement par semaine). Fréquences TOTALES visées (Nico, D-eau c) : hiver
# ~1 sem./3, printemps & automne ~1/4, été ~1/6 (orages). Les probabilités
# ci-dessous sont conditionnelles à « semaine calme » (×0.85) et tiennent compte
# des pluies-aléas du catalogue (mesuré sur 200 graines, cf. 00_etat.md). JAMAIS
# de pluie chaque semaine en jeu (D-pluie) : seul un banc de test la force.
# La pluie reste un `WeatherEvent` réutilisant les kinds EXISTANTS (« Pluie
# prolongée », « Orage » l'été) → nébulosité, préavis `sim/ciel.py`, signes, apport
# `PLUIE_APPORT`, delta froid et vue Godot les lisent sans une ligne de plus.
P_PLUIE_SAISON = {"printemps": 0.27, "ete": 0.16, "automne": 0.22, "hiver": 0.35}
# Intensité d'un épisode ORDINAIRE : tirée sous le seuil de sévérité du composé
# (`sim/ciel.py` SEUIL_SEVERE = 0.8) → une averse ordinaire n'alimente jamais
# « l'hiver de tous les dangers » ; seule la « Pluie prolongée »-ALÉA peut le faire.
PLUIE_INTENSITE_MAX = 0.75


def _saison_meteo(wiy: int) -> str:
    """Saison du calendrier moteur (printemps 1-13, été 14-26, automne 27-39, hiver
    40-52). Lit le calendrier UNIQUE racine (D122) — plus de copie locale."""
    return saison_de(wiy)


def _pluie_ordinaire(seed: int, week: int, wiy: int) -> WeatherEvent:
    """Épisode de pluie ordinaire d'une semaine CALME, ou `CALME`. Pur (hash)."""
    saison = _saison_meteo(wiy)
    if _hash_noise(seed, week, *K_PLUIE) >= P_PLUIE_SAISON[saison]:
        return CALME
    kind = "Orage" if saison == "ete" else "Pluie prolongée"
    scope = "local" if kind == "Orage" else "global"
    inten = PLUIE_INTENSITE_MAX * _hash_noise(seed, week, *K_MAG)
    return WeatherEvent(kind, round(inten, 3), 1, scope)


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
        return _pluie_ordinaire(seed, week, wiy)   # semaine calme : pleut-il ? (①)

    cands = [e for e in _CATALOGUE if e[3][0] <= wiy <= e[3][1]]
    if not cands:
        return _pluie_ordinaire(seed, week, wiy)

    pick = _hash_noise(seed, week, *K_PICK)
    kind, scope, duration, _ = cands[int(pick * len(cands)) % len(cands)]
    mag = abs(hash_gauss(seed, week, K_MAG[0], K_MAG[1]))
    return WeatherEvent(kind, round(mag, 3), duration, scope)


def patch_local(seed: int, week: int, rows: int, cols: int):
    """
    Masque spatial déterministe d'un événement `scope="local"` (grêle / orage, §2).

    Renvoie un prédicat `est_dans_patch(r, c) -> bool` : un DISQUE de plots, centré
    sur un plot tiré par hash (canaux sentinelles décorrélés de la grille du sol),
    rayon ∝ `PATCH_FRAC`. Un événement local ne frappe donc qu'un COIN de la tuile —
    un plot hors patch est épargné → variance spatiale de survie sous un même hiver
    (philo #7). PURE et déterministe (zéro RNG, philo #3) : deux runs identiques
    frappent exactement le même coin. Un événement `scope="global"` n'appelle jamais
    ceci (l'engine frappe alors toute la tuile).
    """
    cr = _hash_noise(seed, week, *K_PATCH_R) * rows
    cc = _hash_noise(seed, week, *K_PATCH_C) * cols
    rayon2 = (PATCH_FRAC * max(rows, cols)) ** 2

    def est_dans_patch(r: int, c: int) -> bool:
        return (r - cr) ** 2 + (c - cc) ** 2 <= rayon2

    return est_dans_patch


def temp_norm(week_in_year: int, year_fraction: float | None = None,
              phase: float = 0.0) -> float:
    """
    Température NORMALE de la semaine (°C) — toile de fond lisse, 100 % prévisible
    (docs/champs/climat/conception_meteo.md §1.1) : `T_MOY − T_AMP·cos(2π·(w − W_T_MIN)/52)`.

    `week_in_year` ∈ [1, 52]. Si `year_fraction` est fourni, on superpose la dérive
    interannuelle `climate_stress` (§1.2, `phase` dérivée du seed) → certaines
    années plus fraîches/douces, sur plusieurs ans. Fonction PURE (pas de RNG).
    """
    base = T_MOY - T_AMP * math.cos(2.0 * math.pi * (week_in_year - W_T_MIN) / 52.0)
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


# Banc de TEST « pluie chaque semaine » (D111 ①e, D-pluie : JAMAIS en jeu). Le flag
# `game_state["pluie_forcee"]` n'est posé QUE par le hook du banc `pluie_continue` ;
# il remplace l'événement de chaque semaine par cette pluie (aléas compris).
PLUIE_FORCEE = WeatherEvent("Pluie prolongée", 0.5, 1, "global")


def weather_state(seed: int, week: int,
                  pluie_forcee: bool = False) -> tuple[WeatherEvent, float, float]:
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

    `pluie_forcee` (banc de TEST `pluie_continue`, D111 ①e) : l'événement de la
    semaine devient `PLUIE_FORCEE` ; T_air et nébulosité en découlent. Défaut False
    → comportement de jeu inchangé.
    """
    from sim.wind import nebulosite_dynamique   # local : évite le cycle weather↔wind
    week_in_year  = ((week - 1) % 52) + 1
    event         = PLUIE_FORCEE if pluie_forcee else weather_at(seed, week)
    year_fraction = (week - 1) / 52.0
    phase         = (seed & 0xFFFF) / 0xFFFF * 2.0 * math.pi
    t_air         = temp_norm(week_in_year, year_fraction, phase) + temperature_delta(event)
    nebul         = nebulosite_dynamique(seed, week, event if pluie_forcee else None)
    return event, t_air, nebul


# --- Humidité de l'air (sprint « le sol qui respire » ①, D111 §1a) ----------
# La rosée dérivait son point de rosée de l'humidité du SOL → sol sec ⇒ pas de
# rosée ⇒ sol plus sec (boucle sèche mesurée). En climat océanique, c'est l'AIR
# marin qui porte la vapeur : humidité relative haute, plus haute l'hiver que
# l'été, saturée sous la pluie, effondrée sous un épisode sec. Grandeur PURE
# `f(seed, semaine)` — scalaire uniforme comme T_air — passée en ARGUMENT à la
# rosée (les `fields` n'importent jamais `sim`).
HR_MOY   = 0.80    # humidité relative moyenne annuelle (Normandie ≈ 80 %)
HR_AMP   = 0.07    # demi-amplitude saisonnière (max fin janvier, min fin juillet)
HR_BRUIT = 0.05    # bruit hebdomadaire ± (canal K_HR)
HR_EVENT = {       # humidité imposée par l'événement (None = régime normal)
    "Pluie prolongée": 0.97, "Orage": 0.92, "Neige": 0.92, "Tempête": 0.85,
    "Sécheresse": 0.50, "Canicule": 0.50,
}


def humidite_air(seed: int, week: int, event: WeatherEvent | None = None) -> float:
    """Humidité relative de l'air ∈ [0,1] de la semaine `week` — PURE, déterministe
    (zéro RNG). Normale saisonnière océanique + bruit hebdo, ou la valeur imposée
    par l'événement de la semaine (pluie saturante, sécheresse sèche). `event`
    fourni (événement déjà résolu par l'appelant, ex. banc de pluie forcée) → il
    remplace `weather_at`."""
    ev = event if event is not None else weather_at(seed, week)
    imposee = HR_EVENT.get(ev.kind)
    if imposee is not None:
        return imposee
    wiy = wiy_de(week)
    base = HR_MOY + HR_AMP * math.cos(2.0 * math.pi * (wiy - W_T_MIN) / 52.0)
    base += HR_BRUIT * (2.0 * _hash_noise(seed, week, *K_HR) - 1.0)
    return round(max(0.0, min(1.0, base)), 4)


def forecast(seed: int, week: int, horizon: int = 2) -> list[WeatherEvent]:
    """
    Prévision (D16) — « cadeau de la fonction pure » : prévoir = évaluer
    `weather_at` en avance. La semaine venue, l'engine calcule LA MÊME fonction →
    prévision == réalité, par construction. (Les signes du sous-sprint 04 liront
    ceci ; l'engine ne s'en sert pas encore.)
    """
    return [weather_at(seed, week + k) for k in range(1, horizon + 1)]


# --- Signes diégétiques (Z2, docs/champs/climat/conception_meteo.md §4) ------------------------
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
