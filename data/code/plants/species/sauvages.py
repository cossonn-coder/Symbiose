"""
SYMBIOSE — plants/species/sauvages.py
Plantes spontanées « sauvages » du catalogue enrichi ③ — actuellement l'Ortie
(Urticaceae). Données pures (niveau 3), s'appuient sur `plants.base`.

DISTINCT d'`adventices.py` : ces espèces ne sont PAS des archétypes de succession
(`archetype=None`) → elles n'entrent PAS dans WEED_CATALOGUE ni dans la
germination spontanée. Elles existent au catalogue (PLANT_CATALOGUE) pour être
posées par le joueur ou acquises (magazine), pas tirées par la SeedBank. Leur
intérêt est écologique (hôte de chenilles, biomasse azotée, bioindication).
"""

from __future__ import annotations
from plants.base import GrowthStage, Urticaceae, Ericaceae


class Nettle(Urticaceae):
    """
    Urtica dioica — Ortie (Urticaceae).
    Vivace robuste, bioindicatrice de sols riches en azote : sa famille injecte
    localement de la fertilité (biomasse azotée minéralisée). Anémophile (fleurs
    discrètes au vent → aucune retombée butineurs). Hôte majeur de chenilles de
    papillons (paon-du-jour, vulcain) — via le pont chenille générique. Biomasse
    abondante pour le paillis/compost. Comestible (jeunes pousses).
    """
    genus = "Urtica"
    name = "Ortie"
    resistance_ecrasement  = 0.6   # touffe dressée, repart de la souche
    stimulation_ecrasement = 0.4
    rarity = "Établie"
    keywords = ["Bioindicatrice", "Comestible", "Biomasse", "Hôte"]
    space_tolerance_weeks = 5
    life_cycle = "perennial"
    winter_strategy = "dormant"
    archetype = None               # PAS une adventice de succession (hors WEED_CATALOGUE)
    seed_dispersal = "anemochore"  # akène léger d'ortie — graines au vent (⑤, §5.3)
    foliage_density = 0.50
    longevity_years = 8
    reproduction_rate = 0.10
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=4,
        ),
        # Vivace : touffe adulte (duration 0). PAS d'effet floraison-pollinisateur
        # (anémophile) — l'injection d'azote vient du family_effects d'Urticaceae.
        GrowthStage(
            name="adulte", duration_weeks=0, strate="basse",
            vigueur_cost=1, canopy_height=90, canopy_radius=30,
            root_radius=40,
            effects=[],
        ),
    ]


class Vaccinium(Ericaceae):
    """
    Vaccinium myrtillus — Myrtille (Ericaceae).
    Sous-arbrisseau ACIDOPHILE/calcifuge des landes et sous-bois acides : le
    DÉMONSTRATEUR ROI de la fenêtre pH (tronçon ⑤). Sa fenêtre basse (`ph_opt=4.8`,
    `ph_tol=0.8`) fait qu'elle ne lève ni ne prospère sur calcaire ; sous SEUIL_
    ACIDOPHILE, posée sur sol alcalin (`ph > CHLOROSE_PH`) elle subit la CHLOROSE
    ferrique (jaunissement, malus de vigueur). archetype=None ⇒ hors WEED_CATALOGUE
    (jamais tirée par la succession) : posée par le joueur / acquise (magazine).
    Mellifère (cloches discrètes), baies comestibles.
    """
    genus = "Vaccinium"
    name = "Myrtille"
    ph_opt = 4.8                   # acidophile strict — fenêtre étroite (calcifuge)
    ph_tol = 0.8
    resistance_ecrasement  = 0.5
    stimulation_ecrasement = 0.3
    rarity = "Établie"
    keywords = ["Acidophile", "Comestible", "Mellifère", "Indicatrice"]
    space_tolerance_weeks = 4
    life_cycle = "perennial"
    winter_strategy = "dormant"
    deciduous = True               # caduc : feuillage rougi puis largué l'automne
    archetype = None               # PAS une adventice de succession (hors WEED_CATALOGUE)
    foliage_density = 0.40
    longevity_years = 15
    reproduction_rate = 0.06
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=4,
        ),
        GrowthStage(
            name="adulte", duration_weeks=0, strate="basse",
            vigueur_cost=1, canopy_height=40, canopy_radius=30,
            root_radius=35,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Floraison mellifère — clochettes nourrissant l'abeille"
                },
            ],
        ),
    ]
