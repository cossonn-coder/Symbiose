"""
SYMBIOSE — plants/species/adventices.py
Adventices : 4 archétypes de succession écologique (pioneer, nitrogen_fixer,
grass, competitor). Données pures (niveau 3), s'appuient sur `plants.base`.
"""

from __future__ import annotations
from plants.base import PlantBase, GrowthStage


class BursaPastoris(PlantBase):
    """
    Capsella bursa-pastoris — Bourse-à-pasteur (Brassicaceae).
    Archétype Pioneer : germe sur sol nu, cycle court, enrichit la MO.
    Stratégie r : pousse vite, meurt vite, laisse des graines et de la nécromasse.
    """
    family = "Brassicaceae"
    genus  = "Capsella"
    name   = "Bourse-à-pasteur"
    resistance_ecrasement  = 0.55  # hampe cassable, rosette survit (volet 2 §4)
    stimulation_ecrasement = 0.2
    rarity = "Pionnière"
    keywords = ["Pionnière", "Couvre-sol", "Compost"]
    space_tolerance_weeks = 5
    life_cycle = "annual"
    winter_strategy = "die"
    archetype = "pioneer"
    reproduction_rate = 0.08   # forte production graines
    foliage_density = 0.35     # feuillage léger
    fungal_susceptibility = 0.6
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=3,
        ),
        GrowthStage(
            name="adulte", duration_weeks=4, strate="basse",
            vigueur_cost=0, canopy_height=25,
            effects=[
                {
                    "type": "permanent", "trigger": "weekly",
                    "action": "inject_field", "variable": "om_fresh",
                    "amount": 0.03, "cible": "local",
                    "description": "Pionnière — enrichit la MO"
                }
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=3, strate="basse",
            vigueur_cost=0, canopy_height=40,
            effects=[
                {
                    "type": "recolte",
                    "action": "score", "axis": "biodiversite", "amount": 1,
                    "description": "Floraison pionnière — biodiversité"
                }
            ],
        ),
    ]


class MedicagoLupulina(PlantBase):
    """
    Medicago lupulina — Minette (Fabaceae).
    Archétype Nitrogen fixer : légumineuse spontanée, recharge microbiome et fertilité.
    Colonise les sols pauvres — la succession la fait apparaître quand fertilite < seuil.
    """
    family = "Fabaceae"
    genus  = "Medicago"
    name   = "Minette"
    resistance_ecrasement  = 0.7   # port bas rampant, encaisse (volet 2 §4)
    stimulation_ecrasement = 0.5
    rarity = "Pionnière"
    keywords = ["Fixatrice N₂", "Couvre-sol", "Mellifère"]
    space_tolerance_weeks = 5
    life_cycle = "perennial"
    winter_strategy = "dormant"
    archetype = "nitrogen_fixer"
    reproduction_rate = 0.05
    foliage_density = 0.40
    longevity_years = 3    # vivace courte
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=3,
        ),
        GrowthStage(
            name="adulte", duration_weeks=0, strate="sol",  # vivace
            vigueur_cost=0, canopy_height=30, root_radius=50,  # pivot légumineuse
            effects=[
                {
                    "type": "permanent", "trigger": "weekly",
                    "action": "inject_field", "variable": "fertilite",
                    "amount": 0.04, "cible": "local",
                    "description": "Fixation N₂ — fertilité"
                },
                {
                    "type": "floraison",
                    "action": "score", "axis": "biodiversite", "amount": 1,
                    "description": "Floraison mellifère"
                }
            ],
        ),
    ]
    # Microbiome non scripté : émerge des exsudats universels (boucle rhizosphère).
    family_effects = [
        {
            "type": "permanent", "trigger": "weekly",
            "action": "inject_field", "variable": "fertilite",
            "amount": 0.03, "cible": "local",
            "description": "Fixation N₂ familiale"
        }
    ]


class PoaAnnua(PlantBase):
    """
    Poa annua — Pâturin annuel (Poaceae).
    Archétype Grass : compétiteur hydrique, stabilise le sol, banque de graines permanente.
    Racines fibreuses horizontales — épuise l'humidité locale mais maintient la structure.
    """
    family = "Poaceae"
    genus  = "Poa"
    name   = "Pâturin annuel"
    resistance_ecrasement  = 0.9   # graminée : talle, PROFITE du piétinement (volet 2 §4)
    stimulation_ecrasement = 0.9
    rarity = "Pionnière"
    keywords = ["Couvre-sol", "Structurante", "Invasive"]
    space_tolerance_weeks = 7
    life_cycle = "perennial"
    winter_strategy = "dormant"
    archetype = "grass"
    reproduction_rate = 0.06
    foliage_density = 0.35     # graminée fine, ombre légère
    longevity_years = 3        # vivace courte
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=3,
        ),
        GrowthStage(
            name="adulte", duration_weeks=0, strate="basse",  # vivace
            vigueur_cost=0, canopy_height=30, root_radius=75,  # racines fibreuses larges
            effects=[
                {
                    "type": "permanent", "trigger": "weekly",
                    "action": "inject_field", "variable": "om_fresh",
                    "amount": 0.02, "cible": "local",
                    "description": "Graminée — accumulation MO racinaire"
                }
            ],
        ),
    ]


class Taraxacum(PlantBase):
    """
    Taraxacum officinale — Pissenlit (Asteraceae).
    Archétype Competitor : pivot profond, monopolise espace racinaire, ferme canopée basse.
    Très résilient — stress_tolerance élevée, résiste aux perturbations.
    """
    family = "Asteraceae"
    genus  = "Taraxacum"
    name   = "Pissenlit"
    resistance_ecrasement  = 0.8   # rosette plaquée, encaisse, repart mou (volet 2 §4)
    stimulation_ecrasement = 0.4
    rarity = "Établie"
    keywords = ["Accumulatrice", "Mellifère", "Bioindicatrice", "Résistant"]
    space_tolerance_weeks = 8   # extrêmement tolérant
    life_cycle = "perennial"
    winter_strategy = "dormant"
    archetype = "competitor"
    reproduction_rate = 0.04
    foliage_density = 0.50
    longevity_years = 8    # vivace longue
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=3,
        ),
        GrowthStage(
            name="rosette", duration_weeks=0, strate="basse",  # vivace
            vigueur_cost=0, canopy_height=30,
            canopy_radius=55, root_radius=60,  # rosette large, basse + pivot
            effects=[
                {
                    "type": "permanent", "trigger": "weekly",
                    "action": "inject_field", "variable": "fertilite",
                    "amount": 0.03, "cible": "local",
                    "description": "Accumulatrice — remonte les nutriments profonds"
                },
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1, "probability": 0.7,
                    "description": "Floraison mellifère précoce"
                }
            ],
        ),
    ]
    family_effects = [
        {
            "type": "floraison",
            "action": "add_rondelle", "variable": "pollinisateur",
            "amount": 1, "max": 3,
            "description": "Floraison mellifère familiale (Asteraceae)"
        }
    ]
