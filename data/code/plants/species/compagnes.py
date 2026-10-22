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
from plants.base import PlantBase, GrowthStage, Asteraceae, Amaryllidaceae


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
    feuillage = "fin"  # transpiration (D111 ①) : type de feuillage d'espèce
    resilience_base = 1.25         # S — vivace rustique stolonifère, très encaissante
    resistance_ecrasement  = 0.75  # stolons, repart (volet 2 §4)
    stimulation_ecrasement = 0.6
    rarity = "Établie"
    keywords = ["Auxiliaire", "Mellifère", "Compagne", "Médicinale"]
    space_tolerance_weeks = 5
    life_cycle = "perennial"
    winter_strategy = "dormant"
    t_germ_opt = 14.0              # vivace rustique des prés : lève au frais (fenêtre ③)
    t_germ_tol = 12.0              # large
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
    feuillage = "fin"  # transpiration (D111 ①) : type de feuillage d'espèce
    resilience_base = 0.8          # R — engrais vert annuel à tige tendre, cycle court
    resistance_ecrasement  = 0.45  # tige tendre dressée, déformée (volet 2 §4)
    stimulation_ecrasement = 0.2
    rarity = "Établie"
    keywords = ["Auxiliaire", "Mellifère", "Engrais vert", "Compagne"]
    space_tolerance_weeks = 4
    life_cycle = "annual"
    winter_strategy = "die"
    t_germ_opt = 13.0              # engrais vert rustique : lève vite au frais (fenêtre ③)
    t_germ_tol = 11.0              # large
    bloom_forcing_gdd = 38.0       # ÉTÉ précoce (~S20) : engrais vert à cycle éclair, fleurit vite (①)
    bloom_duration = 6
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
    feuillage = "large"  # transpiration (D111 ①) : type de feuillage d'espèce
    resilience_base = 1.0          # intermédiaire — annuelle vigoureuse mais charnue/cassante
    resistance_ecrasement  = 0.4   # tige creuse charnue, casse net (volet 2 §4)
    stimulation_ecrasement = 0.2
    rarity = "Établie"
    keywords = ["Mellifère", "Comestible", "Engrais vert"]
    space_tolerance_weeks = 4
    life_cycle = "annual"
    winter_strategy = "die"
    t_germ_opt = 16.0              # tempérée : lève au mitan du printemps (fenêtre ③)
    t_germ_tol = 10.0              # tolérante (ressemis spontané sur une large saison)
    bloom_forcing_gdd = 45.0       # ÉTÉ (~S21) : mellifère majeure de plein été (①)
    bloom_duration = 7
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
    feuillage = "large"  # transpiration (D111 ①) : type de feuillage d'espèce
    resilience_base = 1.25         # S — vivace pionnière à pivot profond, quasi indestructible
    root_loss_tolerance_base = 1.4 # niche campagnol (③) : pivot charnu profond → le chevelu rongé se refait, l'uptake tient
    resistance_ecrasement  = 0.65  # rosette charnue, repart du pivot (volet 2 §4)
    stimulation_ecrasement = 0.4
    rarity = "Établie"
    keywords = ["Accumulatrice", "Mellifère", "Engrais vert", "Biomasse"]
    space_tolerance_weeks = 5
    life_cycle = "perennial"
    winter_strategy = "dormant"
    t_germ_opt = 15.0              # vivace tempérée : lève au printemps établi (fenêtre ③)
    t_germ_tol = 11.0              # large
    bloom_forcing_gdd = 50.0       # ÉTÉ (~S21) : mellifère de plein été, longue (①)
    bloom_duration = 8
    foliage_density = 0.55
    longevity_years = 10
    reproduction_rate = 0.04
    fungal_susceptibility = 0.3
    bouturable = True              # bouture de tronçon de racine charnue (palette ②)
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
                    "action": "inject_field", "variable": "n",
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
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    resilience_base = 0.8          # R — engrais vert annuel à croissance éclair, tendre
    resistance_ecrasement  = 0.45  # hampe tendre, casse (volet 2 §4)
    stimulation_ecrasement = 0.2
    rarity = "Établie"
    keywords = ["Engrais vert", "Mellifère", "Pionnière"]
    space_tolerance_weeks = 4
    life_cycle = "annual"
    winter_strategy = "die"
    archetype = None               # cultivée compagne, PAS une adventice de succession
    t_germ_opt = 12.0              # engrais vert rustique : lève vite au frais, même tardif (③)
    t_germ_tol = 12.0              # large
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


class Garlic(Amaryllidaceae):
    """
    Allium sativum — Ail (Amaryllidaceae).
    Bisannuelle compagne répulsive : ses composés soufrés éloignent les nuisibles
    du voisinage (family_effects Amaryllidaceae → protège la santé des voisines,
    bonne compagne des Solanacées/Rosacées). Feuilles dressées étroites l'an 1,
    hampe florale (« fleur d'ail ») l'an 2, puis bulbe comestible. Cycle bisannuel
    → exerce le gate annuel de montaison (rosette an 1, hampe an 2).
    """
    genus = "Allium"
    name = "Ail"
    feuillage = "cireux"  # transpiration (D111 ①) : type de feuillage d'espèce
    resilience_base = 1.0          # intermédiaire — bisannuelle bulbeuse, tenue moyenne
    root_loss_tolerance_base = 0.7 # niche campagnol (③) : bulbe & racines superficielles concentrés → le rongeur emporte l'organe de réserve d'un coup
    resistance_ecrasement  = 0.4   # hampe tendre, casse ; le bulbe survit sous terre
    stimulation_ecrasement = 0.2
    rarity = "Établie"
    keywords = ["Répulsif", "Comestible", "Compagne", "Bisannuelle"]
    space_tolerance_weeks = 4
    life_cycle = "biennial"
    winter_strategy = "dormant"
    t_germ_opt = 12.0              # rustique : démarre au frais (planté en sol refroidi) (③)
    t_germ_tol = 10.0              # tolérante
    foliage_density = 0.20         # feuilles étroites, ombre faible
    longevity_years = 2
    reproduction_rate = 0.03
    growth_stages = [
        GrowthStage(
            name="plantation", duration_weeks=3, strate="sol",
            vigueur_cost=1, effects=[], canopy_height=4,
        ),
        # An 1 : feuilles dressées (PAS d'effet floraison → pas le stade de montaison).
        GrowthStage(
            name="feuilles", duration_weeks=6, strate="basse",
            vigueur_cost=1, effects=[], canopy_height=25, canopy_radius=12,
        ),
        # An 2 : hampe florale (1er stade fleuri → stade de montaison du gate).
        GrowthStage(
            name="hampe", duration_weeks=4, strate="basse",
            vigueur_cost=2, canopy_height=50, canopy_radius=12,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1, "probability": 0.5,
                    "description": "Fleur d'ail — visitée modérément"
                },
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=3, strate="basse",
            vigueur_cost=0, canopy_height=50,
            effects=[
                {
                    "type": "recolte",
                    "action": "score", "axis": "recolte", "amount": 2,
                    "description": "Récolte du bulbe"
                },
            ],
        ),
    ]
