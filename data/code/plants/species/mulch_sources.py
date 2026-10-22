"""
SYMBIOSE — plants/species/mulch_sources.py
Espèces SOURCES DE MULCH annuelles (sprint équilibre invasion ⑤, D10) : Blé
(Poaceae), Chanvre (Cannabaceae NEUVE) et Seigle (Poaceae, sprint ALLÉLOPATHIE ⑤
— engrais vert allélopathique). Toutes produisent de la PAILLE à la récolte
(`mulch_source="paille"`, lu par `sim.actions.paillage.recolter_paille` au geste
joueur — event-driven, golden NEUTRE au repos).

Elles INCARNENT le levier permacole du sprint : « l'espèce sert l'idée » (règle
catalogue). On les cultive pour COUVRIR le sol — la récolte n'alimente pas
seulement le score, elle remplit le stock de paille qui étouffera la levée férale
et retiendra l'humidité (interconnexion récolte → paillage → germination↓/ET↓).

Données PURES (niveau 3), s'appuient sur `plants.base`. Le chanvre déclare sa
famille Cannabaceae au niveau ESPÈCE (patron Phacelia/Carrot : une famille neuve
= un simple attribut `family`, pas une classe de `familles.py`). HORS scénario
golden (jamais semées sur les 2 tuiles du smoke) → dérive NEUTRE.
"""

from __future__ import annotations
from plants.base import GrowthStage, Poaceae, PlantBase


class Wheat(Poaceae):
    """
    Triticum aestivum — Blé (Poaceae).
    Graminée annuelle de strate moyenne : elle lève au frais, monte en chaume puis
    en épi, et sa PAILLE (le chaume sec après moisson) est le mulch de référence du
    maraîcher — léger, aéré, décomposition rapide (nature "paille" : `decay=1.0`,
    `humidite_w=1.2`, pas d'allélopathie ni de décalage pH). Anémophile (Poaceae).
    Hérite de la compétition hydrique fibreuse de sa famille. `mulch_source="paille"`.
    """
    genus = "Triticum"
    name = "Blé"
    feuillage = "fin"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.0  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    rarity = "Établie"
    keywords = ["Céréale", "Paille", "Couvre-sol", "Comestible"]
    t_germ_opt = 12.0              # rustique : lève sur sol seulement frais de printemps (③)
    t_germ_tol = 11.0              # large
    resistance_ecrasement  = 0.6   # chaume souple, plie et repart de la touffe
    stimulation_ecrasement = 0.3
    space_tolerance_weeks = 4
    life_cycle = "annual"
    winter_strategy = "die"
    foliage_density = 0.45
    mulch_source = "paille"        # récolté → stock paille (④/⑤)
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=6,
        ),
        GrowthStage(
            name="tallage", duration_weeks=4, strate="basse",
            vigueur_cost=1, effects=[], canopy_height=35,
        ),
        # Épiaison : chaume dressé. Anémophile → PAS d'effet floraison-pollinisateur.
        GrowthStage(
            name="épiaison", duration_weeks=5, strate="moyenne",
            vigueur_cost=2, canopy_height=90, canopy_radius=15,
            effects=[
                {
                    "type": "floraison",
                    "action": "score",
                    "axis": "biodiversite",
                    "amount": 1,
                    "description": "Épiaison — la céréale monte en grain"
                },
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=3, strate="moyenne",
            vigueur_cost=0, canopy_height=100, canopy_radius=15,
            effects=[
                {
                    "type": "recolte",
                    "action": "score",
                    "axis": "recolte",
                    "amount": 1,
                    "description": "Moisson — grain récolté, la paille reste à couvrir le sol"
                },
            ],
        ),
    ]


class Rye(Poaceae):
    """
    Secale cereale — Seigle (Poaceae). ENGRAIS VERT ALLÉLOPATHIQUE (sprint
    ALLÉLOPATHIE ⑤) : la facette « couvert stratégique permaculture », opposée à la
    vivace toxique (armoise). Semé DENSE à l'automne, il couvre le sol tout l'hiver,
    puis ses racines exsudent des allélochimiques (acides benzoxazinoïdes, DIBOA/BOA)
    qui ÉTOUFFENT chimiquement la levée des adventices dicotylédones — sans se gêner
    lui-même (graminée TOLÉRANTE, cf. `Poaceae.allelopathie_sensibilite=0.4`). On le
    FAUCHE au printemps : sa paille couvre le sol (`mulch_source="paille"`) et l'effet
    résiduel garde la planche nette quelques semaines (le maraîcher plante DANS le
    mulch de seigle). Émission MODÉRÉE. Anémophile (Poaceae). `mulch_source="paille"`.

    On surcharge `family_effects` pour AJOUTER l'injection allélopathique SANS perdre
    la compétition hydrique fibreuse familiale (Poaceae) → on la RE-DÉCLARE ici (un
    override remplace la liste héritée, pas de fusion). HORS golden (jamais semé) →
    dérive NEUTRE.
    """
    genus = "Secale"
    name = "Seigle"
    feuillage = "fin"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.0  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    rarity = "Établie"
    keywords = ["Céréale", "Engrais vert", "Allélopathe", "Couvre-sol"]
    t_germ_opt = 10.0              # TRÈS rustique : lève au froid (semé à l'automne) (③)
    t_germ_tol = 12.0              # très large — la plus rustique des céréales
    resistance_ecrasement  = 0.6   # chaume souple, plie et repart de la touffe
    stimulation_ecrasement = 0.3
    space_tolerance_weeks = 5
    life_cycle = "annual"
    winter_strategy = "die"
    foliage_density = 0.50         # couvert dense — étouffe la lumière au sol
    mulch_source = "paille"        # fauché → stock paille (④/⑤)
    allelopathie_emission = 0.08   # MODÉRÉ (benzoxazinoïdes) — couvert nettoyant ; arme l'autotox ④
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "action": "inject_field",
            "variable": "humidite",
            "amount": -0.06,
            "cible": "local",
            "description": "Racines fibreuses — compétition hydrique intense"
        },
        {
            "type": "permanent",
            "trigger": "weekly",
            "action": "inject_field",
            "variable": "allelopathie",
            "amount": 0.08,
            "cible": "local",
            "description": "Benzoxazinoïdes — allélopathie de couvert nettoyant"
        },
    ]
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=6,
        ),
        GrowthStage(
            name="tallage", duration_weeks=5, strate="basse",
            vigueur_cost=1, effects=[], canopy_height=40,
        ),
        # Épiaison : chaume dressé. Anémophile → PAS d'effet floraison-pollinisateur.
        GrowthStage(
            name="épiaison", duration_weeks=5, strate="moyenne",
            vigueur_cost=2, canopy_height=140, canopy_radius=15,
            effects=[
                {
                    "type": "floraison",
                    "action": "score",
                    "axis": "biodiversite",
                    "amount": 1,
                    "description": "Épiaison — le seigle monte en grain"
                },
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=3, strate="moyenne",
            vigueur_cost=0, canopy_height=160, canopy_radius=15,
            effects=[
                {
                    "type": "recolte",
                    "action": "score",
                    "axis": "recolte",
                    "amount": 1,
                    "description": "Fauche — le couvert se couche, la paille reste à nettoyer le sol"
                },
            ],
        ),
    ]


class Hemp(PlantBase):
    """
    Cannabis sativa — Chanvre (Cannabaceae, famille NEUVE déclarée à l'espèce).
    Annuelle HAUTE à croissance fulgurante et fibre robuste : sa tige donne une
    PAILLE DURABLE (fibres longues, décomposition plus lente qu'une paille de
    céréale — mais on la range sous la même nature "paille" du modèle ④, faute
    d'une 4ᵉ nature dédiée : la nuance de durabilité est diégétique, pas mécanique).
    Plante-service étouffe-adventices : son ombrage dense (`foliage_density=0.70`)
    et sa vitesse la font couvrir le sol nu en une saison — un couvert vivant AVANT
    d'être un couvert mort. Anémophile (dioïque). `mulch_source="paille"`.
    """
    family = "Cannabaceae"
    genus = "Cannabis"
    name = "Chanvre"
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.0  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    resilience_base = 1.0          # intermédiaire — annuelle vigoureuse à tige fibreuse mais tendre jeune
    rarity = "Établie"
    keywords = ["Fibre", "Paille", "Étouffe-adventice", "Structurante"]
    t_germ_opt = 16.0              # tempéré : lève au mitan du printemps (③)
    t_germ_tol = 10.0              # tolérante
    resistance_ecrasement  = 0.25  # tige unique fibreuse : pliée = cassée, ne repart guère
    stimulation_ecrasement = 0.1
    space_tolerance_weeks = 3
    life_cycle = "annual"
    winter_strategy = "die"
    pollination_mode = "wind"      # dioïque anémophile → aucune retombée butineurs
    pollination_radius_cm = 400.0
    foliage_density = 0.70         # canopée dense — étouffe les adventices dessous
    mulch_source = "paille"        # récolté → stock paille (④/⑤)
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="basse",
            vigueur_cost=1, effects=[], canopy_height=8,
        ),
        GrowthStage(
            name="jeune", duration_weeks=3, strate="moyenne",
            vigueur_cost=1, effects=[], canopy_height=80,
        ),
        # Tige haute fibreuse. Anémophile → PAS d'effet floraison-pollinisateur.
        GrowthStage(
            name="adulte", duration_weeks=6, strate="haute",
            vigueur_cost=2, canopy_height=250, canopy_radius=25,
            effects=[
                {
                    "type": "floraison",
                    "action": "score",
                    "axis": "biodiversite",
                    "amount": 1,
                    "description": "Floraison discrète — la fibre monte"
                },
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=3, strate="haute",
            vigueur_cost=0, canopy_height=300, canopy_radius=25,
            effects=[
                {
                    "type": "recolte",
                    "action": "score",
                    "axis": "luxuriance",
                    "amount": 1,
                    "description": "Rouissage — la tige donne une paille de fibre durable"
                },
            ],
        ),
    ]
