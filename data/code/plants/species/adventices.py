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
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.2  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    resilience_base = 1.25         # S — pionnière rustique r-stratège, la rosette encaisse tout
    resistance_ecrasement  = 0.55  # hampe cassable, rosette survit (volet 2 §4)
    stimulation_ecrasement = 0.2
    rarity = "Pionnière"
    keywords = ["Pionnière", "Couvre-sol", "Compost"]
    space_tolerance_weeks = 5
    life_cycle = "annual"
    winter_strategy = "die"
    archetype = "pioneer"
    t_germ_opt = 11.0          # pionnière rustique : lève tôt sur sol nu frais (fenêtre ③)
    t_germ_tol = 13.0          # large → colonise dès le réchauffement de sortie d'hiver
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
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.6  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    resilience_base = 1.25         # S — légumineuse pionnière rampante des sols pauvres, rustique
    resistance_ecrasement  = 0.7   # port bas rampant, encaisse (volet 2 §4)
    stimulation_ecrasement = 0.5
    rarity = "Pionnière"
    keywords = ["Fixatrice N₂", "Couvre-sol", "Mellifère"]
    space_tolerance_weeks = 5
    life_cycle = "perennial"
    winter_strategy = "dormant"
    archetype = "nitrogen_fixer"
    t_germ_opt = 13.0          # légumineuse spontanée des sols pauvres : lève au frais (fenêtre ③)
    t_germ_tol = 12.0          # large
    decompactante = True   # racine pivot de légumineuse : décompacte/aère le sol (⑧, RACINE_PIVOT)
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
                    "action": "inject_field", "variable": "n",
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
            "action": "inject_field", "variable": "n",
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
    feuillage = "fin"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.0  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    resilience_base = 1.25         # S — graminée fibreuse pionnière, coriace (elle hérite de
                                   # PlantBase et non de la classe Poaceae : valeur posée en
                                   # explicite pour éviter le défaut silencieux 1.0)
    hail_resistance_base = 1.4     # feuilles étroites de graminée — la grêle glisse (≡ Poaceae)
    resistance_ecrasement  = 0.9   # graminée : talle, PROFITE du piétinement (volet 2 §4)
    stimulation_ecrasement = 0.9
    rarity = "Pionnière"
    keywords = ["Couvre-sol", "Structurante", "Invasive"]
    space_tolerance_weeks = 7
    life_cycle = "perennial"
    winter_strategy = "dormant"
    archetype = "grass"
    t_germ_opt = 12.0          # graminée pionnière : lève tôt et tard, fenêtre permissive (③)
    t_germ_tol = 13.0          # large → banque permanente, germe sur une longue saison
    reproduction_rate = 0.06
    seed_dispersal = "anemochore"   # caryopse léger de graminée — graines au vent (⑤, §5.3)
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
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.7  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    resilience_base = 1.25         # S — pivot profond, rosette plaquée : repart de la racine
    resistance_ecrasement  = 0.8   # rosette plaquée, encaisse, repart mou (volet 2 §4)
    stimulation_ecrasement = 0.4
    rarity = "Établie"
    keywords = ["Accumulatrice", "Mellifère", "Bioindicatrice", "Résistant"]
    space_tolerance_weeks = 8   # extrêmement tolérant
    life_cycle = "perennial"
    winter_strategy = "dormant"
    archetype = "competitor"
    t_germ_opt = 12.0          # pissenlit ultra-rustique : germe sur une très large plage (③)
    t_germ_tol = 14.0          # la plus large du catalogue — opportuniste tous azimuts
    reproduction_rate = 0.04
    seed_dispersal = "anemochore"   # aigrette plumée (pappus) — graines au vent (⑤, §5.3)
    silhouette = "rosette"          # rosette plaquée large (luxuriance ③) — dévie du défaut `touffe` de la strate basse ; HORS golden → neutre
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
                    "action": "inject_field", "variable": "n",
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


class Molene(PlantBase):
    """
    Verbascum thapsus — Bouillon-blanc / Molène (Scrophulariaceae).
    Archétype `disease_indicator` (sprint MÉMOIRE D'INOCULUM ③) : bisannuelle
    pionnière INDICATRICE de terre malade persistante. Elle ne lève PAS par le
    gradient de maturité du sol mais par la porte de RELÂCHE `arch_inoculum` —
    elle colonise les plots durablement chargés en inoculum (là où les cultures
    tombent, elle prospère). Rosette laineuse l'an 1, haute hampe florale jaune
    l'an 2 (montaison monocarpique), puis mort. Médicinale (feuilles pectorales).

    Peu sensible aux pathogènes du sol (`fungal_susceptibility` basse) : c'est
    justement ce qui lui permet de tenir là où l'inoculum accable les autres.
    """
    family = "Scrophulariaceae"
    genus  = "Verbascum"
    name   = "Molène"
    feuillage = "cireux"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.05  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    resilience_base = 1.2          # S — pionnière rustique des sols pauvres/remués, rosette coriace
    resistance_ecrasement  = 0.5   # hampe cassable, rosette laineuse survit (volet 2 §4)
    stimulation_ecrasement = 0.2
    rarity = "Indicatrice"
    keywords = ["Indicatrice", "Médicinale", "Bisannuelle"]
    silhouette = "rosette"         # rosette laineuse plaquée l'an 1 ; HORS golden → neutre
    space_tolerance_weeks = 6
    life_cycle = "biennial"        # rosette l'an 1, hampe l'an 2, mort monocarpique (gate ③)
    winter_strategy = "dormant"    # passe l'hiver de l'an 1 en rosette
    archetype = "disease_indicator"
    t_germ_opt = 15.0              # pionnière de sol nu remué : lève au réchauffement (fenêtre ③)
    t_germ_tol = 12.0              # large → opportuniste sur terrain perturbé/vicié
    fungal_susceptibility = 0.2    # BASSE — prospère là où l'inoculum abat les autres (rôle indicateur)
    reproduction_rate = 0.07       # forte production de graines minuscules, banque durable
    foliage_density = 0.40
    longevity_years = 2
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=3,
        ),
        # An 1 : rosette laineuse plaquée — PLAFOND tant que age_years < 1.0 (gate
        # annuel des bisannuelles). Aucun effet `floraison` → PAS le stade de montaison.
        GrowthStage(
            name="rosette", duration_weeks=6, strate="basse",
            vigueur_cost=0, effects=[], canopy_height=20, canopy_radius=22,
            root_radius=25,   # pivot qui décompacte le sol vicié
        ),
        # An 2 : montaison. 1er stade fleuri → stade de MONTAISON repéré par le gate.
        GrowthStage(
            name="hampe", duration_weeks=6, strate="haute",
            vigueur_cost=1, canopy_height=150, canopy_radius=20,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Haute hampe jaune — mellifère, nourrit l'abeille"
                },
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=4, strate="haute",
            vigueur_cost=0, canopy_height=160,
            effects=[
                {
                    "type": "recolte",
                    "action": "score", "axis": "biodiversite", "amount": 1,
                    "description": "Montée en graines — banque durable, biodiversité"
                },
            ],
        ),
    ]
