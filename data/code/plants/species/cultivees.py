"""
SYMBIOSE — plants/species/cultivees.py
Espèces cultivées du potager (niveau 3) : Solanacées, Légumineuses, Astéracées,
Lamiacées. Données pures, s'appuient sur les familles de `plants.base`.
"""

from __future__ import annotations
from plants.base import (GrowthStage,
                         Solanaceae, Fabaceae, Asteraceae, Lamiaceae)


# --- Solanaceae ---

class Tomato(Solanaceae):
    genus = "Solanum"
    name = "Tomate"
    # Sensibilité EMBLÉMATIQUE à la juglone (sprint ALLÉLOPATHIE ⑤) : la tomate est
    # le cas d'école du dépérissement sous noyer. > 1 = plus sensible que le standard
    # (borné [0,1] par la rampe → une forte charge effondre sa niche/croissance).
    allelopathie_sensibilite = 1.5
    t_germ_opt = 22.0              # FRILEUSE : exige un sol bien chaud, lève tard (fenêtre ③)
    t_germ_tol = 7.0               # étroite → ne lève pas sur sol frais de printemps
    bloom_forcing_gdd = 40.0       # ÉTÉ (~S20) : fleurit dès l'installation estivale (①)
    bloom_duration = 6
    resistance_ecrasement  = 0.35  # tige cassante, repart un peu (volet 2 §4)
    stimulation_ecrasement = 0.4
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
    fruitier              = True   # porte des fruits traçables (③ ; maturity_years=0 → dès l'année)
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
    t_germ_opt = 24.0              # la PLUS frileuse : tropicale, lève très tard (fenêtre ③)
    t_germ_tol = 6.0               # la plus étroite des cultivées chaudes
    resistance_ecrasement  = 0.35  # buissonnant cassant, repart un peu (volet 2 §4)
    stimulation_ecrasement = 0.4
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
    resilience_base = 0.8          # R — annuelle tendre à tige volubile fragile
    t_germ_opt = 20.0              # FRILEUSE : sème « quand le sol est chaud au toucher » (③)
    t_germ_tol = 7.0               # étroite → pourrit en terre froide
    resistance_ecrasement  = 0.3   # tige volubile fragile (volet 2 §4)
    stimulation_ecrasement = 0.2
    hauteur_autoportante   = 35.0  # cm tenus debout sans appui (D49 ①) : au-delà,
                                   # libre → l'apex retombe (affalement émergent)
    mode_grimpe            = "vrille_volubile"  # cherche à s'enrouler (support valide en ②)
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
    resilience_base = 1.25         # S — couvre-sol vivace piétinable, repart du stolon
    t_germ_opt = 16.0              # tempérée : couvre-sol qui lève au mitan du printemps (③)
    t_germ_tol = 10.0              # tolérante (germe printemps comme arrière-saison)
    resistance_ecrasement  = 0.85  # couvre-sol piétinable, ramifie (volet 2 §4)
    stimulation_ecrasement = 0.8
    rarity = "Pionnière"
    keywords = ["Fixatrice N₂", "Couvre-sol", "Mellifère"]
    space_tolerance_weeks = 5  # très tolérant, couvre-sol résilient
    life_cycle = "perennial"
    winter_strategy = "dormant"
    foliage_density = 0.40
    reproduction_rate = 0.35   # ressemis (M7) — vivace sans archétype
    # Couvre-sol stolonifère réel (sprint LUXURIANCE ②) : le trèfle tapisse par ramets
    # (stolons rampants) autant que par graine → arbitrage émergent graines ↔ ramets.
    # `stolon` = besoin de lumière au sol pour s'établir (le stolon ne prend pas sous
    # une canopée fermée) → auto-limitation. Cf. `sim/clonal.py`, table D65 §2.2.
    clonal_mode = "stolon"
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
    # --- Allélopathie racinaire (sprint ALLÉLOPATHIE ⑤) ---
    # Émission MODÉRÉE : le tournesol est notoirement allélopathique (composés
    # phénoliques des racines et feuilles) — il « espace » ses voisines sensibles.
    # On surcharge `family_effects` pour AJOUTER l'injection SANS perdre la floraison
    # mellifère familiale (Asteraceae) → on la RE-DÉCLARE ici (l'override remplace la
    # liste héritée, pas de fusion). Le trait `allelopathie_emission` arme aussi
    # l'autotoxicité ④ (la monoculture de tournesol fatigue son sol).
    allelopathie_emission = 0.08   # MODÉRÉ (phénols) — entre l'aromatique et le noyer
    family_effects = [
        {
            "type": "floraison",
            "action": "add_rondelle",
            "variable": "pollinisateur",
            "amount": 1,
            "max": 3,
            "description": "Floraison mellifère familiale"
        },
        {
            "type": "permanent",
            "trigger": "weekly",
            "action": "inject_field",
            "variable": "allelopathie",
            "amount": 0.08,
            "cible": "local",
            "description": "Phénols racinaires — allélopathie modérée"
        },
    ]
    resilience_base = 0.8          # R — flèche unique annuelle, grandes feuilles tendres
    hail_resistance_base = 0.7     # larges limbes exposés — la grêle les déchire
    t_germ_opt = 20.0              # FRILEUSE (origine prairie chaude) : lève au sol réchauffé (③)
    t_germ_tol = 8.0               # étroite-moyenne
    bloom_forcing_gdd = 55.0       # ÉTÉ (~S22) : grande floraison estivale, longue (①)
    bloom_duration = 8             # tournesol : floraison longue
    resistance_ecrasement  = 0.15  # flèche unique : écimé = décapité, ne repart pas (volet 2 §4)
    stimulation_ecrasement = 0.05
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
    resilience_base = 0.8          # R — annuelle tendre frileuse, noircit au moindre stress
    t_germ_opt = 22.0              # FRILEUSE tropicale : exige la chaleur, lève tard (fenêtre ③)
    t_germ_tol = 6.0               # étroite → noircit au moindre coup de froid
    resistance_ecrasement  = 0.4   # écimé facilement MAIS repart buissonnant = le pincement (volet 2 §4)
    stimulation_ecrasement = 0.85
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
