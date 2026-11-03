"""
SYMBIOSE — plants/species/prairie.py
Flore de prairie spontanée (sprint TRÈFLE DOMINANT ②, D126) : Dactyle, Fétuque rouge,
Plantain lancéolé. Elles portent l'archétype `grass` ou `competitor` mais n'en sont
PAS la tête : la banque de graines reste par archétype, et `sim/succession.py` choisit
ensuite l'espèce selon l'azote du plot (table `FLORE_SPONTANEE`, plants/catalogue.py).

Le dactyle est la pièce qui ferme le cycle du trèfle : l'azote fixé le fait lever, sa
touffe haute et dense ombre le sol, et les stolons ne prennent plus sous cette ombre
(porte de lumière de `sim/clonal.py`). Rien n'agit directement sur le trèfle (philo #2).
Données pures (niveau 3), s'appuient sur `plants.base`.
"""

from __future__ import annotations
from plants.base import PlantBase, Poaceae, GrowthStage


class Dactyle(Poaceae):
    """
    Dactylis glomerata — Dactyle aggloméré (Poaceae).
    Grande graminée en touffes denses des sols riches : lève sur l'azote laissé par les
    légumineuses, puis ombre le sol à son pied. Racines fibreuses gourmandes en eau
    (`family_effects` de Poaceae).
    """
    genus = "Dactylis"
    name = "Dactyle"
    feuillage = "moyen"  # transpiration (D111 ①) : limbe large pour une graminée
    nectar = 0.0  # anémophile
    resistance_ecrasement = 0.6    # touffe dressée, repart de la souche
    stimulation_ecrasement = 0.3
    rarity = "Établie"
    keywords = ["Nitrophile", "Touffe", "Fourragère", "Ombrage"]
    life_cycle = "perennial"
    winter_strategy = "dormant"
    archetype = "grass"
    t_germ_opt = 14.0              # graminée tempérée : lève au frais, printemps et automne
    t_germ_tol = 11.0
    reproduction_rate = 0.05
    seed_dispersal = "anemochore"  # caryopse léger, comme le pâturin
    foliage_density = 0.75         # touffe serrée : c'est elle qui arrête la lumière
    longevity_years = 6
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=4, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=5,
        ),
        GrowthStage(
            name="touffe", duration_weeks=0, strate="moyenne",  # vivace
            # Rayon 50 : défaut de la strate moyenne. À 35, l'ombre ne passe sous la porte
            # des stolons que sur le plot du pied (mesures/apres_flore.md).
            vigueur_cost=0, canopy_height=90, canopy_radius=50, root_radius=50,
            effects=[
                {
                    "type": "permanent", "trigger": "weekly",
                    "action": "inject_field", "variable": "om_fresh",
                    "amount": 0.03, "cible": "local",
                    "description": "Touffe — accumulation MO racinaire"
                }
            ],
        ),
    ]


class FetuqueRouge(Poaceae):
    """
    Festuca rubra — Fétuque rouge (Poaceae).
    Graminée fine et sobre des sols moyens et pauvres : gazon bas, ombre légère. À la
    différence du dactyle, elle ne pompe pas l'eau du plot (pas d'effet de famille) et
    laisse le trèfle cohabiter.
    """
    genus = "Festuca"
    name = "Fétuque rouge"
    feuillage = "fin"  # feuilles filiformes
    nectar = 0.0  # anémophile
    resistance_ecrasement = 0.9    # gazon : talle sous le pied, comme le pâturin
    stimulation_ecrasement = 0.8
    rarity = "Établie"
    keywords = ["Sobre", "Gazon", "Couvre-sol"]
    life_cycle = "perennial"
    winter_strategy = "dormant"
    archetype = "grass"
    t_germ_opt = 13.0
    t_germ_tol = 12.0
    reproduction_rate = 0.05
    seed_dispersal = "anemochore"
    foliage_density = 0.35         # gazon fin, ombre légère
    longevity_years = 5
    family_effects = []            # sobre : pas de compétition hydrique de famille
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=3,
        ),
        GrowthStage(
            name="gazon", duration_weeks=0, strate="basse",  # vivace
            vigueur_cost=0, canopy_height=25, canopy_radius=20, root_radius=40,
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


class PlantainLanceole(PlantBase):
    """
    Plantago lanceolata — Plantain lancéolé (Plantaginaceae, famille neuve).
    Rosette plaquée de feuilles étroites à nervures saillantes, épi brun au bout d'une
    hampe nue. Indifférent à l'azote, il encaisse le piétinement et tient les prairies
    fauchées. Anémophile : son épi donne du pollen au vent, pas de nectar.
    """
    family = "Plantaginaceae"
    genus = "Plantago"
    name = "Plantain lancéolé"
    feuillage = "moyen"
    nectar = 0.0
    resilience_base = 1.25         # S — rosette plaquée à souche courte, comme le pissenlit
    resistance_ecrasement = 0.85   # la plante des chemins : le pied ne la tue pas
    stimulation_ecrasement = 0.5
    rarity = "Établie"
    keywords = ["Rosette", "Médicinale", "Bioindicatrice"]
    space_tolerance_weeks = 7
    life_cycle = "perennial"
    winter_strategy = "dormant"
    archetype = "competitor"
    t_germ_opt = 14.0
    t_germ_tol = 13.0
    reproduction_rate = 0.04
    pollination_mode = "wind"
    pollination_radius_cm = 300.0
    silhouette = "rosette"
    foliage_density = 0.45
    longevity_years = 6
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=3,
        ),
        GrowthStage(
            name="rosette", duration_weeks=0, strate="basse",  # vivace
            vigueur_cost=0, canopy_height=25, canopy_radius=22, root_radius=40,
            effects=[],
        ),
    ]
