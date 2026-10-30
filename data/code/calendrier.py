"""
SYMBIOSE — calendrier.py
Calendrier UNIQUE du moteur (D122, docs/champs/climat/conception_calendrier_unique.md).
Fondation pure, ZÉRO import du projet → importable depuis `plants`, `fields`,
`sim` sans cycle (comme `constants.py`). `sim/engine/calendrier.py` le ré-exporte.

Convention (décision C1) : l'année compte 52 semaines `wiy` ∈ [1, 52] et
**commence à l'équinoxe de printemps** — wiy 1 ≈ 20 mars. Une semaine absolue
`week` (monotone sur les années) se ramène à son rang dans l'année par `wiy_de`.

Table de référence mois → semaine (wiy ≈ 1 + jours depuis le 20 mars / 7) :

    1ᵉʳ avr  3 | 1ᵉʳ mai  7 | 1ᵉʳ juin 11 | 1ᵉʳ juil 16 | 1ᵉʳ août 20 | 1ᵉʳ sept 24
    1ᵉʳ oct 29 | 1ᵉʳ nov 33 | 1ᵉʳ déc  37 | 1ᵉʳ janv 42 | 1ᵉʳ févr 46 | 1ᵉʳ mars 50

Pourquoi un seul fichier : avant D122, le climat comptait depuis le 1ᵉʳ janvier
et les étiquettes de saison depuis l'équinoxe (11 semaines d'écart → glace de la
mare « au printemps »). Des copies locales existaient pour éviter un cycle
d'import ; deux copies peuvent diverger, une seule non.
"""

from __future__ import annotations

SAISONS = {
    "printemps": range(1,  14),   # ≈ 20 mars – 19 juin
    "ete":       range(14, 27),   # ≈ 20 juin – 18 sept
    "automne":   range(27, 40),   # ≈ 19 sept – 18 déc
    "hiver":     range(40, 53),   # ≈ 19 déc – 19 mars
}
PHASES_ACTIVES = {"printemps", "ete", "automne"}
SEMAINE_HIVER = SAISONS["hiver"].start   # 40 : première semaine d'hiver

# Phases climatiques nommées (plus de « 4 » ni de « 25 » magiques dans les
# formules). Toutes les sinusoïdes annuelles s'ancrent sur ces deux semaines.
W_T_MIN = 45           # froid le plus vif ≈ fin janvier (aussi : HR max, vent max)
W_SOLSTICE_ETE = 14    # jour le plus long ≈ 21 juin (le pic thermique suit, ≈ wiy 19)

# Nouaison (③) : la mise à fruit a lieu UNE fois par an, au début de l'été.
# Un rendez-vous annuel fixe (≠ tick par tick) évite la sur-création de fruits
# et garantit le déterminisme (pitfall #4 du kickoff).
FRUIT_NOUAISON_WEEK = SAISONS["ete"].start


def wiy_de(week: int) -> int:
    """Rang dans l'année ∈ [1, 52] de la semaine ABSOLUE `week` (≥ 1)."""
    return ((week - 1) % 52) + 1


def saison_de(week):
    for nom, r in SAISONS.items():
        if week in r: return nom
    return "hiver"

def est_debut_saison(week):
    return any(week == r.start for r in SAISONS.values())

def est_fin_saison(week):
    return any(week == r.stop - 1 for r in SAISONS.values())

def est_phase_floraison(week, saison):
    if saison not in PHASES_ACTIVES: return False
    r = SAISONS[saison]
    return week == r.start + len(r) // 2

def est_phase_recolte(week, saison):
    if saison not in PHASES_ACTIVES: return False
    return week == SAISONS[saison].stop - 1
