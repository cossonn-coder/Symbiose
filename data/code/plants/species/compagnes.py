"""
SYMBIOSE — plants/species/compagnes.py
Plantes compagnes (attire-auxiliaires, mellifères, engrais verts) : Achillée,
Phacélie, Bourrache, Consoude, Moutarde. Données pures (niveau 3), s'appuient
sur `plants.base`.

Boraginaceae (Phacélie, Bourrache, Consoude) et Brassicaceae (Moutarde) sont
déjà câblées dans les tables `_ATTRACT_*` de population.py → l'attractivité
florale est héritée GRATIS : il suffit que ces espèces posent la rondelle
`pollinisateur` à la floraison (Boraginaceae nourrit fort l'abeille ;
Brassicaceae nourrit fort le syrphe). Consoude et Moutarde jouent aussi le rôle
d'accumulatrice/engrais vert (injection locale de fertilité / matière organique).
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


class Borage(PlantBase):
    """
    Borago officinalis — Bourrache (Boraginaceae).
    Annuelle mellifère majeure à ressemis spontané : ses fleurs bleues nourrissent
    fort l'abeille (Boraginaceae). Comestible (fleurs/feuilles) et engrais vert
    léger. Cycle court — meurt à l'hiver, laisse graines et nécromasse.
    """
    family = "Boraginaceae"
    genus = "Borago"
    name = "Bourrache"
    resistance_ecrasement  = 0.4   # tige creuse charnue, casse net (volet 2 §4)
    stimulation_ecrasement = 0.2
    rarity = "Établie"
    keywords = ["Mellifère", "Comestible", "Engrais vert"]
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
                    "description": "Floraison très mellifère — abeille"
                },
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=3, strate="basse",
            vigueur_cost=0, canopy_height=70,
            effects=[
                {
                    "type": "recolte",
                    "action": "score", "axis": "biodiversite", "amount": 1,
                    "description": "Monte en graines — biodiversité"
                },
            ],
        ),
    ]


class Comfrey(PlantBase):
    """
    Symphytum officinale — Consoude (Boraginaceae).
    Accumulatrice dynamique vivace : pivot profond (root_radius large, patron
    pissenlit) qui remonte les nutriments du sous-sol → injection locale de
    fertilité. Biomasse abondante pour le paillis/compost, et mellifère à la
    floraison (abeille). Entre en dormance l'hiver.
    """
    family = "Boraginaceae"
    genus = "Symphytum"
    name = "Consoude"
    resistance_ecrasement  = 0.65  # rosette charnue, repart du pivot (volet 2 §4)
    stimulation_ecrasement = 0.4
    rarity = "Établie"
    keywords = ["Accumulatrice", "Mellifère", "Engrais vert", "Biomasse"]
    space_tolerance_weeks = 5
    life_cycle = "perennial"
    winter_strategy = "dormant"
    foliage_density = 0.55
    longevity_years = 10
    reproduction_rate = 0.04
    fungal_susceptibility = 0.3
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=4,
        ),
        GrowthStage(
            name="adulte", duration_weeks=0, strate="basse",  # vivace
            vigueur_cost=1, canopy_height=50, canopy_radius=40,
            root_radius=60,   # pivot profond (patron pissenlit) → remonte les nutriments
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
                    "amount": 1,
                    "description": "Floraison mellifère — abeille"
                },
            ],
        ),
    ]


class Mustard(PlantBase):
    """
    Sinapis alba — Moutarde blanche (Brassicaceae).
    Engrais vert pionnier annuel : pousse vite, produit de la biomasse (injection
    locale de matière organique fraîche, patron bourse-à-pasteur) et nourrit fort
    le syrphe à la floraison (Brassicaceae). `archetype=None` à dessein : c'est une
    CULTIVÉE compagne, pas une adventice de succession — on évite tout télescopage
    avec WEED_CATALOGUE / la germination spontanée.
    """
    family = "Brassicaceae"
    genus = "Sinapis"
    name = "Moutarde"
    resistance_ecrasement  = 0.45  # hampe tendre, casse (volet 2 §4)
    stimulation_ecrasement = 0.2
    rarity = "Établie"
    keywords = ["Engrais vert", "Mellifère", "Pionnière"]
    space_tolerance_weeks = 4
    life_cycle = "annual"
    winter_strategy = "die"
    archetype = None               # cultivée compagne, PAS une adventice de succession
    foliage_density = 0.40
    reproduction_rate = 0.07
    fungal_susceptibility = 0.5
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="sol",
            vigueur_cost=1, effects=[], canopy_height=4,
        ),
        GrowthStage(
            name="adulte", duration_weeks=5, strate="basse",
            vigueur_cost=1, canopy_height=50, canopy_radius=25,
            effects=[
                {
                    "type": "permanent", "trigger": "weekly",
                    "action": "inject_field", "variable": "om_fresh",
                    "amount": 0.02, "cible": "local",
                    "description": "Engrais vert — biomasse, matière organique fraîche"
                },
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Floraison mellifère — nourrit le syrphe"
                },
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=3, strate="basse",
            vigueur_cost=0, canopy_height=60,
            effects=[
                {
                    "type": "recolte",
                    "action": "score", "axis": "biodiversite", "amount": 1,
                    "description": "Monte en graines — biodiversité"
                },
            ],
        ),
    ]
