"""
SYMBIOSE — sim/engine/calendrier.py
Calendrier saisonnier du moteur : découpage de l'année en 52 semaines / 4
saisons et les prédicats de phase (début/fin de saison, floraison, récolte).

Helpers PURS (aucune dépendance moteur) : isolés ici pour que la boucle de
tick (`boucle.py`) reste lisible et que les tests puissent importer
`saison_de` / `FRUIT_NOUAISON_WEEK` sans tirer tout l'Engine.
"""

from __future__ import annotations

SAISONS = {
    "printemps": range(1,  14),
    "ete":       range(14, 27),
    "automne":   range(27, 40),
    "hiver":     range(40, 53),
}
PHASES_ACTIVES = {"printemps", "ete", "automne"}

# Nouaison (③) : la mise à fruit a lieu UNE fois par an, au début de l'été.
# Un rendez-vous annuel fixe (≠ tick par tick) évite la sur-création de fruits
# et garantit le déterminisme (pitfall #4 du kickoff).
FRUIT_NOUAISON_WEEK = SAISONS["ete"].start

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
