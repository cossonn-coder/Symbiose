"""
SYMBIOSE — plants/species/aromatiques.py
Aromatiques persistantes (Lamiaceae) : Thym et Lavande. Données pures (niveau 3),
s'appuient sur `plants.base`.

Concept distinct des `compagnes` (annuelles attire-auxiliaires) : ce sont des
sous-arbrisseaux VIVACES et EVERGREEN (feuillage conservé l'hiver). Elles
exercent pour la première fois le chemin `winter_strategy="evergreen"` du moteur
(sim/engine/mortalite.py) : à l'hiver elles ne meurent NI n'entrent en dormance
profonde — juste une légère réduction métabolique (coussin de thym vert sous le
gel). Famille Lamiaceae ⇒ héritent gratis de la répulsion familiale des nuisibles
au voisinage (family_effects) ET nourrissent fort abeille/papillon via les tables
`_ATTRACT_*` de population.py, dès lors qu'elles posent la rondelle
`pollinisateur` à la floraison.
"""

from __future__ import annotations
from plants.base import GrowthStage, Lamiaceae


class Thyme(Lamiaceae):
    """
    Thymus vulgaris — Thym (Lamiaceae).
    Sous-arbrisseau coussin, persistant (evergreen) et mellifère. Couvre-sol
    ligneux qui encaisse le piétinement (résistance élevée à l'écrasement) et
    nourrit l'abeille à la floraison. Vivace longue, ressemis modéré.
    """
    genus = "Thymus"
    name = "Thym"
    ph_opt = 7.4                   # calciphile : prospère sur sol calcaire (garrigue) — fenêtre ⑤
    ph_tol = 1.1
    resistance_ecrasement  = 0.8   # coussin ligneux : encaisse le piétinement (volet 2 §4)
    stimulation_ecrasement = 0.5
    rarity = "Établie"
    keywords = ["Aromatique", "Mellifère", "Médicinale", "Couvre-sol"]
    space_tolerance_weeks = 4
    life_cycle = "perennial"
    winter_strategy = "evergreen"  # PREMIER porteur de ce chemin — feuillage gardé l'hiver
    deciduous = False              # evergreen ⇒ ombre non nulle même en hiver
    foliage_density = 0.35
    longevity_years = 8
    reproduction_rate = 0.10
    fungal_susceptibility = 0.2    # aromatique — peu sensible
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=3,
        ),
        GrowthStage(
            name="adulte", duration_weeks=0, strate="basse",  # vivace
            vigueur_cost=1, canopy_height=25, canopy_radius=25,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Floraison mellifère — nourrit l'abeille"
                },
            ],
        ),
    ]


class Lavender(Lamiaceae):
    """
    Lavandula angustifolia — Lavande (Lamiaceae).
    Sous-arbrisseau structurant, persistant (evergreen). Plus haute que le thym,
    elle organise l'espace en strate basse-moyenne et nourrit abeille comme
    papillon à la floraison. Vivace très longue, ressemis faible.
    """
    genus = "Lavandula"
    name = "Lavande"
    ph_opt = 7.4                   # calciphile : terrain sec et calcaire — fenêtre ⑤
    ph_tol = 1.1
    resistance_ecrasement  = 0.6   # touffe ligneuse, plie sans casser (volet 2 §4)
    stimulation_ecrasement = 0.4
    rarity = "Établie"
    keywords = ["Aromatique", "Mellifère", "Structurante", "Médicinale"]
    space_tolerance_weeks = 4
    life_cycle = "perennial"
    winter_strategy = "evergreen"
    deciduous = False
    foliage_density = 0.45
    longevity_years = 12
    reproduction_rate = 0.08
    fungal_susceptibility = 0.2
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=4,
        ),
        GrowthStage(
            name="adulte", duration_weeks=0, strate="basse",  # vivace
            vigueur_cost=1, canopy_height=50, canopy_radius=40,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Floraison mellifère — abeille et papillon"
                },
            ],
        ),
    ]
