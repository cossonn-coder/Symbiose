"""
SYMBIOSE — plants/species/compagnes.py
Plantes compagnes attire-auxiliaires (prédateurs des ravageurs) : Achillée et
Phacélie. Données pures (niveau 3), s'appuient sur `plants.base`.
"""

from __future__ import annotations
from plants.base import PlantBase, GrowthStage, Asteraceae


class Yarrow(Asteraceae):
    """
    Achillea millefolium — Achillée millefeuille (Asteraceae).
    Compagne attire-auxiliaires : ses ombelles nourrissent syrphes, coccinelles
    et guêpes parasitoïdes (prédateurs des pucerons/chenilles). Pose la rondelle
    `auxiliaire` à la floraison → renforce la régulation des ravageurs (M6).
    Vivace rustique, mellifère (pollinisateur via la famille Asteraceae).
    """
    genus = "Achillea"
    name = "Achillée millefeuille"
    resistance_ecrasement  = 0.75  # stolons, repart (volet 2 §4)
    stimulation_ecrasement = 0.6
    rarity = "Établie"
    keywords = ["Auxiliaire", "Mellifère", "Compagne", "Médicinale"]
    space_tolerance_weeks = 5
    life_cycle = "perennial"
    winter_strategy = "dormant"
    foliage_density = 0.40
    longevity_years = 6
    reproduction_rate = 0.30   # ressemis (M7) — vivace sans archétype
    fungal_susceptibility = 0.3
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=3,
        ),
        GrowthStage(
            name="adulte", duration_weeks=0, strate="basse",  # vivace
            vigueur_cost=1, canopy_height=40, canopy_radius=30,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "auxiliaire",
                    "amount": 1, "max": 3,
                    "description": "Ombelles — attire les auxiliaires prédateurs"
                },
            ],
        ),
    ]


class Phacelia(PlantBase):
    """
    Phacelia tanacetifolia — Phacélie (Boraginaceae).
    Engrais vert annuel très mellifère, fleur emblématique pour attirer les
    auxiliaires (syrphes surtout). Pose `pollinisateur` ET `auxiliaire` à la
    floraison. Cycle court — meurt à l'hiver, laisse graines et nécromasse.
    """
    family = "Boraginaceae"
    genus = "Phacelia"
    name = "Phacélie"
    resistance_ecrasement  = 0.45  # tige tendre dressée, déformée (volet 2 §4)
    stimulation_ecrasement = 0.2
    rarity = "Établie"
    keywords = ["Auxiliaire", "Mellifère", "Engrais vert", "Compagne"]
    space_tolerance_weeks = 4
    life_cycle = "annual"
    winter_strategy = "die"
    foliage_density = 0.45
    reproduction_rate = 0.06
    fungal_susceptibility = 0.3
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="sol",
            vigueur_cost=1, effects=[], canopy_height=4,
        ),
        GrowthStage(
            name="adulte", duration_weeks=5, strate="basse",
            vigueur_cost=1, canopy_height=60, canopy_radius=30,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Floraison très mellifère"
                },
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "auxiliaire",
                    "amount": 1, "max": 3,
                    "description": "Attire les auxiliaires prédateurs (syrphes)"
                },
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=3, strate="basse",
            vigueur_cost=0, canopy_height=80,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "auxiliaire",
                    "amount": 1, "max": 3,
                    "description": "Attire les auxiliaires prédateurs"
                },
            ],
        ),
    ]
