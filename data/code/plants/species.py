"""
SYMBIOSE — plants/species.py
Espèces concrètes (niveau 3) : 4 adventices archétypes de succession + plantes
cultivées + compagnes attire-auxiliaires.
"""

from __future__ import annotations
from plants.base import (PlantBase, GrowthStage,
                         Solanaceae, Fabaceae, Asteraceae, Lamiaceae, Poaceae)


# ---------------------------------------------------------------------------
# ADVENTICES — 4 archétypes de succession écologique
# ---------------------------------------------------------------------------

class BursaPastoris(PlantBase):
    """
    Capsella bursa-pastoris — Bourse-à-pasteur (Brassicaceae).
    Archétype Pioneer : germe sur sol nu, cycle court, enrichit la MO.
    Stratégie r : pousse vite, meurt vite, laisse des graines et de la nécromasse.
    """
    family = "Brassicaceae"
    genus  = "Capsella"
    name   = "Bourse-à-pasteur"
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


# ---------------------------------------------------------------------------
# NIVEAU 3 : ESPÈCES CULTIVÉES
# ---------------------------------------------------------------------------

# --- Solanaceae ---

class Tomato(Solanaceae):
    genus = "Solanum"
    name = "Tomate"
    rarity = "Établie"
    keywords = ["Mellifère", "Compagne", "Tuteur"]
    space_tolerance_weeks = 2
    life_cycle = "annual"
    winter_strategy = "die"
    foliage_density = 0.55
    # --- Profil de croissance procédurale (D29 réorienté, tronçon 2) ---
    # DÉMONSTRATRICE : 1re espèce migrée sur la voie procédurale (§G). L'empreinte
    # (height_at/canopy_radius_at/root_radius_at) est dérivée de la STRUCTURE, plus
    # des stades. Calibration sur les growth_stages réels (5→30→100→150 cm) — §E.3
    # « reproduire l'allure d'abord ». En croissance libre la flèche monte
    # MONOTONIQUEMENT de ~3 cm vers le gabarit ~150 cm (pic ~tick 75), couronne de
    # ~18 cm (jeune flèche) vers ~49 cm (≈ strate « moyenne » 50) ; PUIS, avec l'âge,
    # l'auxine se relâche et la plante S'ÉTALE (§D.1 « vieux sujet s'étale ») — la
    # hauteur n'est donc pas un plateau éternel, c'est voulu (moteur permanent).
    #   • vitesse / angle laissés aux DÉFAUTS → dynamique de croissance identique au
    #     tronçon 1 sur la fenêtre courte/décapitée que testent les tests structurels ;
    #   • apical_dominance_base=2.2 (> nominal) : la flèche reste tenue jusqu'à ~150 cm
    #     SANS saturer MAX_SEGMENTS (sinon l'élagage amputerait la flèche). Nécessaire
    #     car AUXIN_DECAY/seuil (modules) sont fixes : une flèche de ~19 segments exige
    #     une production d'apex > 1 pour inhiber ses bourgeons profonds.
    procedural_growth     = True
    port_archetype        = "buissonnant"
    apical_dominance_base = 2.2   # flèche tenue jusqu'au gabarit (cf. ci-dessus)
    max_height_cm         = 150.0 # gabarit mature (growth_stages : 150 cm)
    max_extent_cm         = 32.0  # extension horizontale de la couronne
    foliage_halfwidth     = 18.0  # canopée non nulle même en flèche (feuilles : tronçon 5)
    organ_site            = "terminal"
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="basse",
            vigueur_cost=1, effects=[], canopy_height=5,
        ),
        GrowthStage(
            name="jeune", duration_weeks=4, strate="moyenne",
            vigueur_cost=2, effects=[], canopy_height=30,
        ),
        GrowthStage(
            name="adulte", duration_weeks=6, strate="moyenne",
            vigueur_cost=2, canopy_height=100,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle",
                    "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Floraison — attire les pollinisateurs"
                },
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=4, strate="moyenne",
            vigueur_cost=0, canopy_height=150,
            effects=[
                {
                    "type": "recolte",
                    "action": "score",
                    "axis": "recolte",
                    "amount": 3,
                    "description": "Récolte abondante"
                },
            ],
        ),
    ]


class Pepper(Solanaceae):
    genus = "Capsicum"
    name = "Poivron"
    rarity = "Établie"
    keywords = ["Mellifère", "Compagne"]
    space_tolerance_weeks = 2
    life_cycle = "annual"
    winter_strategy = "die"
    foliage_density = 0.50
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="basse",
            vigueur_cost=1, effects=[], canopy_height=5,
        ),
        GrowthStage(
            name="adulte", duration_weeks=8, strate="moyenne",
            vigueur_cost=2, canopy_height=60,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle",
                    "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Floraison mellifère"
                },
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=4, strate="moyenne",
            vigueur_cost=0, canopy_height=80,
            effects=[
                {
                    "type": "recolte",
                    "action": "score",
                    "axis": "recolte",
                    "amount": 2,
                    "description": "Récolte de poivrons"
                },
            ],
        ),
    ]

# --- Fabaceae ---

class Bean(Fabaceae):
    genus = "Phaseolus"
    name = "Haricot"
    rarity = "Pionnière"
    keywords = ["Fixatrice N₂", "Grimpante", "Compagne"]
    space_tolerance_weeks = 3
    life_cycle = "annual"
    winter_strategy = "die"
    foliage_density = 0.50
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="sol",
            vigueur_cost=1, effects=[], canopy_height=5,
        ),
        GrowthStage(
            name="jeune", duration_weeks=3, strate="grimpante",
            vigueur_cost=1, effects=[], canopy_height=30,
        ),
        GrowthStage(
            name="adulte", duration_weeks=6, strate="grimpante",
            vigueur_cost=2, canopy_height=150,
            effects=[
                {
                    "type": "floraison",
                    "action": "score",
                    "axis": "biodiversite",
                    "amount": 1,
                    "description": "Floraison — contribue à la biodiversité"
                },
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=3, strate="grimpante",
            vigueur_cost=0, canopy_height=200,
            effects=[
                {
                    "type": "recolte",
                    "action": "score",
                    "axis": "recolte",
                    "amount": 2,
                    "description": "Récolte de haricots"
                },
            ],
        ),
    ]


class Clover(Fabaceae):
    genus = "Trifolium"
    name = "Trèfle"
    rarity = "Pionnière"
    keywords = ["Fixatrice N₂", "Couvre-sol", "Mellifère"]
    space_tolerance_weeks = 5  # très tolérant, couvre-sol résilient
    life_cycle = "perennial"
    winter_strategy = "dormant"
    foliage_density = 0.40
    reproduction_rate = 0.35   # ressemis (M7) — vivace sans archétype
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=2,
        ),
        GrowthStage(
            name="adulte", duration_weeks=0, strate="sol",  # vivace
            vigueur_cost=1, canopy_height=15,
            effects=[
                {
                    "type": "permanent",
                    "action": "add_rondelle",
                    "variable": "fertilite",
                    "amount": 1,
                    "max": 3,
                    "description": "Couvre-sol vivace — enrichit la fertilité"
                },
                {
                    "type": "floraison",
                    "action": "score",
                    "axis": "biodiversite",
                    "amount": 1,
                    "description": "Floraison mellifère continue"
                },
            ],
        ),
    ]

# --- Asteraceae ---

class Sunflower(Asteraceae):
    genus = "Helianthus"
    name = "Tournesol"
    rarity = "Établie"
    keywords = ["Mellifère", "Structurante", "Accumulatrice"]
    space_tolerance_weeks = 2  # compétitif, surtout en strate haute
    life_cycle = "annual"
    winter_strategy = "die"
    foliage_density = 0.70     # grandes feuilles, ombre dense
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="basse",
            vigueur_cost=1, effects=[], canopy_height=5,
        ),
        GrowthStage(
            name="jeune", duration_weeks=3, strate="moyenne",
            vigueur_cost=1, effects=[], canopy_height=50,
        ),
        GrowthStage(
            name="adulte", duration_weeks=6, strate="haute",
            vigueur_cost=2, canopy_height=180,
            effects=[
                {
                    "type": "floraison",
                    "action": "score",
                    "axis": "biodiversite",
                    "amount": 2,
                    "description": "Grande floraison mellifère"
                },
                {
                    "type": "permanent",
                    "action": "reduce_rondelle",
                    "variable": "humidite",
                    "amount": 1,
                    "description": "Consommation hydrique élevée"
                },
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=3, strate="haute",
            vigueur_cost=0, canopy_height=250,
            effects=[
                {
                    "type": "recolte",
                    "action": "score",
                    "axis": "recolte",
                    "amount": 2,
                    "description": "Récolte de graines"
                },
                {
                    "type": "recolte",
                    "action": "score",
                    "axis": "luxuriance",
                    "amount": 1,
                    "description": "Biomasse structurante"
                },
            ],
        ),
    ]

# --- Lamiaceae ---

class Basil(Lamiaceae):
    genus = "Ocimum"
    name = "Basilic"
    rarity = "Pionnière"
    keywords = ["Compagne", "Mellifère", "Dynamisante"]
    space_tolerance_weeks = 4
    life_cycle = "annual"
    winter_strategy = "die"
    foliage_density = 0.60     # compact dense
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="basse",
            vigueur_cost=1, effects=[], canopy_height=3,
        ),
        GrowthStage(
            name="adulte", duration_weeks=8, strate="basse",
            vigueur_cost=1, canopy_height=25, canopy_radius=30,  # buisson compact
            effects=[
                {
                    "type": "permanent",
                    "action": "companion_bonus",
                    "target_family": "Solanaceae",
                    "bonus": "reduce_maladie_rondelle",
                    "amount": 1,
                    "radius": 2,
                    "description": "Compagnonnage — protège les Solanacées dans un rayon de 2 plots"
                },
                {
                    "type": "floraison",
                    "action": "add_rondelle",
                    "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Floraison mellifère"
                },
            ],
            callback="basil_companion_check",
        ),
        GrowthStage(
            name="mature", duration_weeks=3, strate="basse",
            vigueur_cost=0, canopy_height=40, canopy_radius=30,
            effects=[
                {
                    "type": "recolte",
                    "action": "score",
                    "axis": "recolte",
                    "amount": 1,
                    "description": "Récolte de feuilles"
                },
                {
                    "type": "recolte",
                    "action": "score",
                    "axis": "biodiversite",
                    "amount": 1,
                    "description": "Monte en graines — biodiversité"
                },
            ],
        ),
    ]

# --- Plantes compagnes attire-auxiliaires (prédateurs des ravageurs) ---

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
