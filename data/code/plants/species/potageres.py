"""
SYMBIOSE — plants/species/potageres.py
Potagères du lot 2 (catalogue enrichi ③) introduisant TROIS familles botaniques
NEUVES : Carotte (Apiaceae), Courgette (Cucurbitaceae), Mâche (Caprifoliaceae).
Données pures (niveau 3), s'appuient sur `plants.base`.

Fichier DISTINCT de `cultivees.py` (garde-fou taille : cultivees.py est déjà à
~308 LDC pur, l'ajout des trois espèces le ferait franchir le seuil ~350). Aucune
de ces trois familles ne porte d'effet familial → elles posent simplement
`family="…"` au niveau espèce (patron Phacelia/Borage), leur rôle écologique étant
porté par les effets de stade (floraison, fructification). Leur attractivité
florale est câblée dans les tables `_ATTRACT_*` de population.py (sinon repli sur
le défaut 0.30, et l'ombellifère-syrphe de la carotte serait raté).

Deux temps « moteur » de ce lot :
  - la carotte exerce pour la 1re fois le cycle `life_cycle="biennial"` avec le
    GATE ANNUEL de montaison (sim/engine/croissance.py) : rosette l'an 1, ombelle
    l'an 2, puis mort monocarpique (mortalite.py). Son stade de montaison est le
    1er stade portant un effet `floraison` (convention du gate).
  - la courgette exerce le profil `fruitier=True` sur une entomophile : elle ne
    NOUE des fruits que pollinisée (frac_nouaison ∝ pollen reçu, philo #2 :
    flux de pollinisation → contrainte → fruits). Sans butineur, pas de courgette.
"""

from __future__ import annotations
from plants.base import PlantBase, GrowthStage


class Carrot(PlantBase):
    """
    Daucus carota — Carotte (Apiaceae).
    Bisannuelle : rosette de feuilles découpées l'an 1 (racine de réserve qui
    grossit), montée en ombelle blanche mellifère l'an 2 (ressource syrphe n°1),
    puis montaison en graines et mort. Racine comestible. Hôte de chenilles
    d'ombellifères (machaon) — rattachement à une famille-hôte nommée différé
    (pont générique pour l'instant).
    """
    family = "Apiaceae"
    genus = "Daucus"
    name = "Carotte"
    resistance_ecrasement  = 0.6   # rosette plaquée, encaisse mais la racine compte
    stimulation_ecrasement = 0.3
    rarity = "Établie"
    keywords = ["Comestible", "Mellifère", "Bisannuelle", "Hôte"]
    silhouette = "rosette"         # rosette de feuilles découpées l'an 1 (luxuriance ③) ; HORS golden → neutre
    space_tolerance_weeks = 3
    life_cycle = "biennial"        # PREMIER porteur du cycle bisannuel exercé (gate ③)
    winter_strategy = "dormant"    # survit à l'hiver de l'an 1 en rosette
    t_germ_opt = 13.0              # rustique : lève au frais du printemps précoce (fenêtre ③)
    t_germ_tol = 10.0              # tolérante
    foliage_density = 0.40
    longevity_years = 2
    reproduction_rate = 0.06
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=1, effects=[], canopy_height=4,
        ),
        # An 1 : la rosette est le PLAFOND tant que age_years < 1.0 (gate annuel).
        # Aucun effet `floraison` ici → ce n'est PAS le stade de montaison.
        GrowthStage(
            name="rosette", duration_weeks=6, strate="basse",
            vigueur_cost=1, effects=[], canopy_height=18, canopy_radius=20,
            root_radius=25,   # racine pivot de réserve
        ),
        # An 2 : montaison. 1er stade fleuri → stade de MONTAISON repéré par le gate.
        GrowthStage(
            name="ombelle", duration_weeks=5, strate="basse",
            vigueur_cost=2, canopy_height=60, canopy_radius=25,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Ombelle mellifère — nourrit fort le syrphe"
                },
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=3, strate="basse",
            vigueur_cost=0, canopy_height=60,
            effects=[
                {
                    "type": "recolte",
                    "action": "score", "axis": "recolte", "amount": 2,
                    "description": "Récolte de la racine / montée en graines"
                },
            ],
        ),
    ]


class Zucchini(PlantBase):
    """
    Cucurbita pepo — Courgette (Cucurbitaceae).
    Annuelle étalée à port couvre-sol : grandes feuilles, large empreinte au sol
    (exerce la compétition souterraine), grosses fleurs jaunes entomophiles. Porte
    des FRUITS traçables (`fruitier=True`) — mais entomophile : la nouaison dépend
    du pollen reçu (sans butineur, pas de fruit, philo #2). Gros fruits → forte
    attraction animale à la chute.
    """
    family = "Cucurbitaceae"
    genus = "Cucurbita"
    name = "Courgette"
    resistance_ecrasement  = 0.35  # tige creuse charnue, casse net
    stimulation_ecrasement = 0.2
    rarity = "Établie"
    keywords = ["Comestible", "Fruitier", "Couvre-sol", "Mellifère"]
    space_tolerance_weeks = 3
    life_cycle = "annual"
    winter_strategy = "die"
    # Silhouette ÉTALÉE (luxuriance ③, D65 §2.4) : la courge est strate `basse` mais
    # RAMPE au sol → override du défaut de strate (`touffe`) vers `étalée`. L'empreinte
    # au sol élargie est DÉJÀ portée par ses stades (canopy_radius=60 ≫ défaut basse=30) :
    # c'est l'override d'empreinte CIBLÉ (b) là où le défaut de strate ment. Espèce HORS
    # golden → dérive NEUTRE. Pur descripteur pour le rendu ⑥, aucun effet moteur.
    silhouette = "étalée"
    t_germ_opt = 22.0              # FRILEUSE (Cucurbitaceae) : exige un sol chaud, lève tard (③)
    t_germ_tol = 7.0               # étroite → pourrit en terre froide
    foliage_density = 0.60
    reproduction_rate = 0.05
    fruitier = True                # porte des fruits traçables (maturity_years=0 → dès l'année)
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="sol",
            vigueur_cost=1, effects=[], canopy_height=5,
        ),
        # Port étalé : large canopée → occupe le sol, exerce la compétition.
        GrowthStage(
            name="adulte", duration_weeks=6, strate="basse",
            vigueur_cost=2, canopy_height=40, canopy_radius=60,
            root_radius=55,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Grandes fleurs jaunes — abeille / bourdon"
                },
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=4, strate="basse",
            vigueur_cost=0, canopy_height=45, canopy_radius=60,
            effects=[
                {
                    "type": "recolte",
                    "action": "score", "axis": "recolte", "amount": 3,
                    "description": "Récolte de courgettes"
                },
            ],
        ),
    ]


class Strawberry(PlantBase):
    """
    Fragaria vesca — Fraisier des bois (Rosaceae).
    Couvre-sol vivace STOLONIFÈRE : au lieu de rester en touffe, il lance des
    stolons rampants au bout desquels s'enracine une plante-fille — le tapissage
    du couvre-sol du sprint LUXURIANCE ④ (absorbe D62). `clonal_mode="stolon"` :
    le stolon exige de la LUMIÈRE AU SOL pour prendre (gate sim/clonal.py) → il ne
    tapisse PAS sous une canopée fermée, d'où une auto-limitation émergente (≠ la
    menthe au rhizome qui ignore l'ombre). Rosette basse plaquée (`silhouette=
    "rosette"`), fleurs blanches mellifères, puis FRUITS traçables (`fruitier`) très
    attractifs pour la faune à maturité. Famille Rosaceae (comme le pommier).
    HORS scénario golden (jamais semé) → dérive NEUTRE.
    """
    family = "Rosaceae"
    genus = "Fragaria"
    name = "Fraisier"
    resistance_ecrasement  = 0.7   # rosette basse plaquée, encaisse le piétinement
    stimulation_ecrasement = 0.4
    rarity = "Établie"
    keywords = ["Comestible", "Fruitier", "Couvre-sol", "Mellifère"]
    silhouette = "rosette"         # rosette basse plaquée de folioles ; HORS golden → neutre
    space_tolerance_weeks = 4
    life_cycle = "perennial"
    winter_strategy = "dormant"    # persiste en rosette, repart au printemps
    t_germ_opt = 16.0              # tempéré : lève au mitan du printemps (fenêtre ③)
    t_germ_tol = 9.0               # moyenne
    foliage_density = 0.35
    longevity_years = 4
    reproduction_rate = 0.10       # se ressème peu — il mise sur les stolons
    fruitier = True                # fraises traçables (maturity_years=0 → dès l'année)
    # Couvre-sol STOLONIFÈRE (sprint LUXURIANCE ④) : portée COURTE (la plante-fille
    # s'enracine près de la mère, au bout du stolon), gate LUMIÈRE au sol (ne prend
    # pas à l'ombre fermée → auto-limitation, cf. sim/clonal.py). Cadence par défaut.
    # Cf. table D65 §2.2 — même mode que le trèfle, portée plus courte.
    clonal_mode = "stolon"
    clonal_radius_cm = 45.0        # stolon court (défaut 60) — la fille s'enracine près
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=3,
        ),
        # Rosette basse fleurie : 1er stade fleuri → table pour les butineurs.
        GrowthStage(
            name="adulte", duration_weeks=5, strate="basse",
            vigueur_cost=1, canopy_height=15, canopy_radius=18,
            root_radius=20,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Fleurs blanches — nourrit l'abeille"
                },
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=4, strate="basse",
            vigueur_cost=0, canopy_height=15, canopy_radius=18,
            effects=[
                {
                    "type": "recolte",
                    "action": "score", "axis": "recolte", "amount": 2,
                    "description": "Récolte de fraises"
                },
            ],
        ),
    ]


class CornSalad(PlantBase):
    """
    Valerianella locusta — Mâche (Caprifoliaceae).
    Petite annuelle couvre-sol rustique d'hiver : germe en jours courts et pousse
    quand tout stagne (seuil de température bas), résiste au gel. Comestible en
    rosette. Petites fleurs visitées sans plus.
    """
    family = "Caprifoliaceae"
    genus = "Valerianella"
    name = "Mâche"
    resistance_ecrasement  = 0.7   # rosette basse plaquée, encaisse le piétinement
    stimulation_ecrasement = 0.3
    rarity = "Établie"
    keywords = ["Comestible", "Couvre-sol", "Rustique"]
    silhouette = "rosette"         # petite rosette plaquée comestible (luxuriance ③) ; HORS golden → neutre
    space_tolerance_weeks = 4
    life_cycle = "annual"
    winter_strategy = "die"
    foliage_density = 0.30
    reproduction_rate = 0.05
    temp_min_growth = 2.0          # pousse au froid — couvre-sol d'hiver
    t_germ_opt = 10.0              # RUSTIQUE FROIDE : lève en sol frais (germination d'arrière-saison) (③)
    t_germ_tol = 12.0              # large vers le bas — germe quand tout stagne
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=2,
        ),
        GrowthStage(
            name="adulte", duration_weeks=5, strate="sol",
            vigueur_cost=1, canopy_height=12, canopy_radius=12,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1, "probability": 0.5,
                    "description": "Petites fleurs — visitée sans plus"
                },
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=3, strate="basse",
            vigueur_cost=0, canopy_height=18,
            effects=[
                {
                    "type": "recolte",
                    "action": "score", "axis": "biodiversite", "amount": 1,
                    "description": "Monte en graines — biodiversité"
                },
            ],
        ),
    ]
