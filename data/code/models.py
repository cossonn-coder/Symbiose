"""
SYMBIOSE — models.py
Dataclasses et hiérarchie de plantes (3 niveaux : Famille → Genre → Espèce).
Système de rondelles, instances de plantes, gestion des conflits spatiaux.
"""

from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, field
from typing import Callable

# ---------------------------------------------------------------------------
# REGISTRE D'EFFETS (callbacks complexes)
# ---------------------------------------------------------------------------

EFFECT_REGISTRY: dict[str, Callable] = {}

def register_effect(name: str):
    """Décorateur pour enregistrer un callback d'effet complexe."""
    def decorator(fn: Callable) -> Callable:
        EFFECT_REGISTRY[name] = fn
        return fn
    return decorator

# ---------------------------------------------------------------------------
# STADE DE CROISSANCE
# ---------------------------------------------------------------------------

@dataclass
class GrowthStage:
    name: str                        # "semis", "jeune", "adulte", "mature"
    duration_weeks: int              # durée minimale avant passage au stade suivant (0 = vivace)
    strate: str                      # "haute","moyenne","basse","sol","grimpante"
    foliar_offsets: list[tuple]      # (Δrow, Δcol) depuis plot central — empreinte aérienne
    root_offsets: list[tuple]        # (Δrow, Δcol) depuis plot central — empreinte souterraine
    vigueur_cost: int                # coût Vigueur pour atteindre ce stade
    effects: list[dict]              # effets data-driven actifs à ce stade
    callback: str | None = None      # clé dans EFFECT_REGISTRY si effet complexe

# ---------------------------------------------------------------------------
# INSTANCE DE PLANTE (avant PlantBase pour la forward ref)
# ---------------------------------------------------------------------------

@dataclass
class PlantInstance:
    plant_class: type                # ex: Tomato
    position: tuple                  # (row, col) du plot central sur la tuile
    current_stage: int = 0          # index dans plant_class.growth_stages
    age_weeks: int = 0              # âge dans le stade courant
    health: int = 3                 # 3=sain, 2=affaibli, 1=malade, 0=mort
    # Mémoire physiologique
    shade_memory: float = 0.0       # intégration lente de l'ombre vécue [0-1]
    drought_memory: float = 0.0     # intégration lente du stress hydrique [0-1]
    stress_memory: float = 0.0      # intégration des perturbations subies [0-1]
                                    # stress↑ → croissance↓ mais résistance↑

    @property
    def stage(self) -> GrowthStage:
        return self.plant_class.growth_stages[self.current_stage]

    @property
    def name(self) -> str:
        return self.plant_class.name

    @property
    def foliar_plots(self) -> list[tuple]:
        """Plots occupés en aérien à ce stade."""
        r, c = self.position
        return [(r + dr, c + dc) for dr, dc in self.stage.foliar_offsets]

    @property
    def root_plots(self) -> list[tuple]:
        """Plots occupés en souterrain à ce stade."""
        r, c = self.position
        return [(r + dr, c + dc) for dr, dc in self.stage.root_offsets]

    @property
    def is_alive(self) -> bool:
        return self.health > 0

    def regress(self) -> bool:
        """
        Régresse d'un stade suite à un conflit spatial non résolu.
        Retourne True si la plante meurt (déjà au stade 0).
        """
        if self.current_stage > 0:
            self.current_stage -= 1
            self.age_weeks = 0
            return False
        else:
            self.health = 0
            return True  # mort

    def advance_stage(self) -> bool:
        """
        Tente de passer au stade suivant.
        Retourne True si un nouveau stade est atteint.
        """
        stages = self.plant_class.growth_stages
        if self.current_stage < len(stages) - 1:
            self.current_stage += 1
            self.age_weeks = 0
            return True
        return False

    def __repr__(self) -> str:
        return (
            f"{self.name}@{self.position} "
            f"[{self.stage.name}] age={self.age_weeks}w santé={self.health}/3"
        )

# ---------------------------------------------------------------------------
# NOTIFICATION DE CONFLIT SPATIAL
# ---------------------------------------------------------------------------

@dataclass
class ConflictNotification:
    plants: list[PlantInstance]      # plantes en conflit (2 ou plus)
    plots: list[tuple]               # plots (row, col) litigieux
    conflict_type: str               # "foliar" ou "root"
    weeks_active: int = 0           # auto-incrémenté chaque semaine
    resolved: bool = False

    def tick(self) -> None:
        """Incrémente le compteur hebdomadaire."""
        if not self.resolved:
            self.weeks_active += 1

    def loser(self) -> PlantInstance:
        """
        La plante la plus jeune (âge_weeks le plus bas) perd.
        En cas d'égalité, la dernière dans la liste.
        """
        return min(self.plants, key=lambda p: p.age_weeks)

    def __repr__(self) -> str:
        noms = " vs ".join(p.name for p in self.plants)
        return (
            f"CONFLIT [{self.conflict_type}] {noms} "
            f"plots={self.plots} semaines={self.weeks_active}"
        )

# ---------------------------------------------------------------------------
# HIÉRARCHIE DES PLANTES — Niveau 1 : PlantBase (abstrait)
# ---------------------------------------------------------------------------

class PlantBase(ABC):
    """
    Classe abstraite racine.
    Les sous-classes définissent family, genus, name, growth_stages, etc.
    """
    family: str = ""
    genus: str = ""
    name: str = ""
    rarity: str = "Établie"              # Pionnière · Établie · Climacique · Ancienne · Sentinelle
    keywords: list[str] = []
    space_tolerance_weeks: int = 3       # délai avant régression en cas de conflit non résolu
    growth_stages: list[GrowthStage] = []
    family_effects: list[dict] = []      # effets partagés au niveau famille
    # Cycle de vie saisonnier
    life_cycle: str = "perennial"        # "annual" | "biennial" | "perennial"
    winter_strategy: str = "dormant"     # "die" | "dormant" | "evergreen"
    archetype: str | None = None         # archétype succession écologique
    reproduction_rate: float = 0.02      # production graines par semaine

    def get_all_effects(self, stage_index: int) -> list[dict]:
        """Fusionne les effets famille + les effets du stade courant."""
        if stage_index >= len(self.growth_stages):
            return self.family_effects[:]
        return self.family_effects + self.growth_stages[stage_index].effects

    @classmethod
    def describe(cls) -> str:
        return f"{cls.name} ({cls.family} › {cls.genus}) — {cls.rarity}"

# ---------------------------------------------------------------------------
# NIVEAU 2 : FAMILLES BOTANIQUES
# ---------------------------------------------------------------------------

class Solanaceae(PlantBase):
    """
    Famille : Solanacées.
    Sensibilité familiale au mildiou : chaque rondelle Maladie active
    dégrade la santé une fois par semaine.
    """
    family = "Solanaceae"
    space_tolerance_weeks = 2  # réagissent vite à la compétition
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "condition": {"rondelle": "maladie", "min": 1},
            "action": "reduce_health",
            "amount": 1,
            "description": "Sensibilité familiale au mildiou"
        }
    ]


class Fabaceae(PlantBase):
    """
    Famille : Légumineuses.
    Fixation N₂ active en permanence — enrichit la rondelle Lombric du sol.
    """
    family = "Fabaceae"
    space_tolerance_weeks = 4  # très tolérantes à la compétition
    # Bonus spécifique légumineuses : fixation N₂ → fertilité. L'enrichissement
    # du microbiome n'est plus scripté ici — il émerge des exsudats universels
    # (boucle rhizosphère, _apply_exudates).
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "action": "inject_field",
            "variable": "fertilite",
            "amount": 0.03,
            "cible": "local",
            "description": "Fixation N₂ — enrichit la fertilité du sol"
        }
    ]


class Asteraceae(PlantBase):
    """
    Famille : Astéracées.
    Floraison mellifère familiale — ajoute un pollinisateur à chaque floraison.
    """
    family = "Asteraceae"
    space_tolerance_weeks = 3
    family_effects = [
        {
            "type": "floraison",
            "action": "add_rondelle",
            "variable": "pollinisateur",
            "amount": 1,
            "max": 3,
            "description": "Floraison mellifère familiale"
        }
    ]


class Lamiaceae(PlantBase):
    """
    Famille : Lamiacées (aromatiques).
    Répulsion naturelle des nuisibles pour les plantes adjacentes.
    """
    family = "Lamiaceae"
    space_tolerance_weeks = 4  # très tolérantes
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "action": "adjacency_bonus",
            "bonus": "reduce_maladie_rondelle",
            "amount": 1,
            "description": "Aromatiques — répulsion naturelle des nuisibles au voisinage"
        }
    ]

class Poaceae(PlantBase):
    """
    Famille : Graminées.
    Compétition hydrique intense — racines fibreuses épuisent l'humidité locale.
    """
    family = "Poaceae"
    space_tolerance_weeks = 6   # très tolérantes à la compétition
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "action": "inject_field",
            "variable": "humidite",
            "amount": -0.06,
            "cible": "local",
            "description": "Racines fibreuses — compétition hydrique intense"
        }
    ]


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
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="sol",
            foliar_offsets=[(0,0)], root_offsets=[(0,0)],
            vigueur_cost=0,
            effects=[],
        ),
        GrowthStage(
            name="adulte", duration_weeks=4, strate="basse",
            foliar_offsets=[(0,0),(0,1)], root_offsets=[(0,0)],
            vigueur_cost=0,
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
            foliar_offsets=[(0,0),(0,1)], root_offsets=[(0,0)],
            vigueur_cost=0,
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
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="sol",
            foliar_offsets=[(0,0)], root_offsets=[(0,0)],
            vigueur_cost=0, effects=[],
        ),
        GrowthStage(
            name="adulte", duration_weeks=0, strate="sol",  # vivace
            foliar_offsets=[(0,0),(0,1),(1,0)], root_offsets=[(0,0),(1,0)],
            vigueur_cost=0,
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
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="sol",
            foliar_offsets=[(0,0)], root_offsets=[(0,0)],
            vigueur_cost=0, effects=[],
        ),
        GrowthStage(
            name="adulte", duration_weeks=0, strate="basse",  # vivace
            foliar_offsets=[(0,0),(0,1),(-1,0)],
            root_offsets=[(0,0),(0,1),(1,0),(0,-1)],  # footprint racinaire large
            vigueur_cost=0,
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
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            foliar_offsets=[(0,0)], root_offsets=[(0,0)],
            vigueur_cost=0, effects=[],
        ),
        GrowthStage(
            name="rosette", duration_weeks=0, strate="basse",  # vivace
            foliar_offsets=[(0,0),(-1,0),(0,-1),(0,1),(1,0)],
            root_offsets=[(0,0),(-1,0),(1,0),(0,1),(0,-1)],  # pivot large
            vigueur_cost=0,
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
# NIVEAU 3 : ESPÈCES
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
    growth_stages = [
        GrowthStage(
            name="semis",
            duration_weeks=3,
            strate="basse",
            foliar_offsets=[(0, 0)],
            root_offsets=[(0, 0)],
            vigueur_cost=1,
            effects=[],
        ),
        GrowthStage(
            name="jeune",
            duration_weeks=4,
            strate="moyenne",
            foliar_offsets=[(0, 0), (-1, 0), (1, 0)],
            root_offsets=[(0, 0), (0, 1)],
            vigueur_cost=2,
            effects=[],
        ),
        GrowthStage(
            name="adulte",
            duration_weeks=6,
            strate="moyenne",
            foliar_offsets=[(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)],
            root_offsets=[(0, 0), (0, 1), (1, 0), (-1, 0)],
            vigueur_cost=2,
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
            name="mature",
            duration_weeks=4,
            strate="moyenne",
            foliar_offsets=[(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)],
            root_offsets=[(0, 0), (0, 1), (1, 0), (-1, 0)],
            vigueur_cost=0,
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
    growth_stages = [
        GrowthStage(
            name="semis",
            duration_weeks=3,
            strate="basse",
            foliar_offsets=[(0, 0)],
            root_offsets=[(0, 0)],
            vigueur_cost=1,
            effects=[],
        ),
        GrowthStage(
            name="adulte",
            duration_weeks=8,
            strate="moyenne",
            foliar_offsets=[(0, 0), (-1, 0), (1, 0)],
            root_offsets=[(0, 0), (0, 1)],
            vigueur_cost=2,
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
            name="mature",
            duration_weeks=4,
            strate="moyenne",
            foliar_offsets=[(0, 0), (-1, 0), (1, 0)],
            root_offsets=[(0, 0), (0, 1)],
            vigueur_cost=0,
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
    growth_stages = [
        GrowthStage(
            name="semis",
            duration_weeks=2,
            strate="sol",
            foliar_offsets=[(0, 0)],
            root_offsets=[(0, 0)],
            vigueur_cost=1,
            effects=[],
        ),
        GrowthStage(
            name="jeune",
            duration_weeks=3,
            strate="grimpante",
            foliar_offsets=[(0, 0), (-1, 0)],
            root_offsets=[(0, 0)],
            vigueur_cost=1,
            effects=[],
        ),
        GrowthStage(
            name="adulte",
            duration_weeks=6,
            strate="grimpante",
            foliar_offsets=[(0, 0), (-1, 0), (-2, 0), (0, -1)],
            root_offsets=[(0, 0), (1, 0)],
            vigueur_cost=2,
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
            name="mature",
            duration_weeks=3,
            strate="grimpante",
            foliar_offsets=[(0, 0), (-1, 0), (-2, 0), (0, -1)],
            root_offsets=[(0, 0), (1, 0)],
            vigueur_cost=0,
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
    growth_stages = [
        GrowthStage(
            name="semis",
            duration_weeks=2,
            strate="sol",
            foliar_offsets=[(0, 0)],
            root_offsets=[(0, 0)],
            vigueur_cost=0,
            effects=[],
        ),
        GrowthStage(
            name="adulte",
            duration_weeks=0,  # vivace — reste adulte indéfiniment
            strate="sol",
            foliar_offsets=[(0, 0), (0, 1), (1, 0)],
            root_offsets=[(0, 0), (0, 1)],
            vigueur_cost=1,
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
    growth_stages = [
        GrowthStage(
            name="semis",
            duration_weeks=2,
            strate="basse",
            foliar_offsets=[(0, 0)],
            root_offsets=[(0, 0)],
            vigueur_cost=1,
            effects=[],
        ),
        GrowthStage(
            name="jeune",
            duration_weeks=3,
            strate="moyenne",
            foliar_offsets=[(0, 0), (-1, 0)],
            root_offsets=[(0, 0), (1, 0)],
            vigueur_cost=1,
            effects=[],
        ),
        GrowthStage(
            name="adulte",
            duration_weeks=6,
            strate="haute",
            foliar_offsets=[(0, 0), (-1, 0), (0, -1), (0, 1)],
            root_offsets=[(0, 0), (1, 0), (-1, 0), (0, 1)],
            vigueur_cost=2,
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
            name="mature",
            duration_weeks=3,
            strate="haute",
            foliar_offsets=[(0, 0), (-1, 0), (0, -1), (0, 1)],
            root_offsets=[(0, 0), (1, 0), (-1, 0), (0, 1)],
            vigueur_cost=0,
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
    growth_stages = [
        GrowthStage(
            name="semis",
            duration_weeks=2,
            strate="basse",
            foliar_offsets=[(0, 0)],
            root_offsets=[(0, 0)],
            vigueur_cost=1,
            effects=[],
        ),
        GrowthStage(
            name="adulte",
            duration_weeks=8,
            strate="basse",
            foliar_offsets=[(0, 0), (0, 1)],
            root_offsets=[(0, 0)],
            vigueur_cost=1,
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
            name="mature",  # monte en graines
            duration_weeks=3,
            strate="basse",
            foliar_offsets=[(0, 0), (0, 1)],
            root_offsets=[(0, 0)],
            vigueur_cost=0,
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

# ---------------------------------------------------------------------------
# TIGES ET RONDELLES
# ---------------------------------------------------------------------------

RONDELLE_TYPES = frozenset(["fertilite", "humidite", "lombric", "maladie", "pollinisateur", "paillage"])

@dataclass
class StakeSlot:
    slot_id: int                                              # 0–9
    rondelles: list[str] = field(default_factory=list)       # max 3 rondelles du même type

    @property
    def variable(self) -> str | None:
        """Type de rondelle sur cette tige (toutes identiques)."""
        return self.rondelles[0] if self.rondelles else None

    @property
    def count(self) -> int:
        return len(self.rondelles)

    @property
    def is_bonus(self) -> bool:
        """Bonus homogène : 3 rondelles identiques."""
        return self.count == 3

    def add(self, rondelle_type: str) -> bool:
        """
        Ajoute une rondelle. Refuse si plein ou si type différent.
        Retourne True si réussi.
        """
        if rondelle_type not in RONDELLE_TYPES:
            raise ValueError(f"Type inconnu : {rondelle_type}")
        if self.count >= 3:
            return False
        if self.rondelles and self.rondelles[0] != rondelle_type:
            return False  # types mixtes interdits
        self.rondelles.append(rondelle_type)
        return True

    def remove_top(self) -> str | None:
        """Retire la rondelle du dessus. Retourne son type ou None."""
        return self.rondelles.pop() if self.rondelles else None

    def __repr__(self) -> str:
        return f"Tige#{self.slot_id} [{self.variable or '—'} ×{self.count}]"

# ---------------------------------------------------------------------------
# TUILE
# ---------------------------------------------------------------------------

@dataclass
class Tile:
    tile_id: str
    soil_type: str                                             # "terre","argile","sable","roche"
    grid_rows: int = 6
    grid_cols: int = 8                                         # 48 plots en quinconce
    plants: list[PlantInstance] = field(default_factory=list)
    stakes: list[StakeSlot] = field(
        default_factory=lambda: [StakeSlot(i) for i in range(10)]
    )
    conflicts: list[ConflictNotification] = field(default_factory=list)

    # --- Accès aux rondelles ---

    def get_rondelle_count(self, variable: str) -> int:
        """Total de rondelles d'un type sur toutes les tiges."""
        return sum(s.count for s in self.stakes if s.variable == variable)

    def get_bonus_variables(self) -> list[str]:
        """Variables avec 3 rondelles identiques (bonus homogène actif)."""
        return [s.variable for s in self.stakes if s.is_bonus and s.variable]

    # --- Géométrie de la grille ---

    def is_valid_plot(self, row: int, col: int) -> bool:
        return 0 <= row < self.grid_rows and 0 <= col < self.grid_cols

    def neighbors(self, row: int, col: int) -> list[tuple]:
        """
        6 voisins hexagonaux (grille quinconce).
        La parité de la ligne détermine le décalage horizontal.
        """
        if row % 2 == 0:
            deltas = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
        else:
            deltas = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
        return [
            (row + dr, col + dc)
            for dr, dc in deltas
            if self.is_valid_plot(row + dr, col + dc)
        ]

    def plots_within_radius(self, row: int, col: int, radius: int) -> list[tuple]:
        """
        Retourne tous les plots dans un rayon donné (BFS sur les voisins).
        """
        visited = set()
        frontier = {(row, col)}
        for _ in range(radius):
            next_frontier = set()
            for r, c in frontier:
                for nb in self.neighbors(r, c):
                    if nb not in visited:
                        next_frontier.add(nb)
            visited |= frontier
            frontier = next_frontier
        visited |= frontier
        visited.discard((row, col))  # exclut le plot central
        return list(visited)

    # --- Plantes ---

    def plants_at(self, row: int, col: int, layer: str = "both") -> list[PlantInstance]:
        """
        Plantes dont le footprint inclut le plot (row, col).
        layer : "foliar", "root" ou "both"
        """
        result = []
        for p in self.plants:
            if not p.is_alive:
                continue
            if layer in ("foliar", "both") and (row, col) in p.foliar_plots:
                result.append(p)
            elif layer == "root" and (row, col) in p.root_plots:
                result.append(p)
        return result

    def add_plant(self, plant_class: type, row: int, col: int) -> PlantInstance | None:
        """
        Plante une espèce sur ce plot.
        Retourne l'instance créée, ou None si le plot est invalide.
        """
        if not self.is_valid_plot(row, col):
            return None
        instance = PlantInstance(plant_class=plant_class, position=(row, col))
        self.plants.append(instance)
        return instance

    def remove_plant(self, instance: PlantInstance) -> None:
        """Retire une plante de la tuile (ex: mort, compost)."""
        if instance in self.plants:
            self.plants.remove(instance)

    # --- Conflits ---

    def detect_conflicts(self) -> list[ConflictNotification]:
        """
        Détecte les nouveaux conflits spatiaux sur la tuile.
        Un conflit = plusieurs plantes vivantes qui partagent un plot
        dans la même couche (foliar ou root), et pas encore signalé.
        """
        new_conflicts = []
        alive = [p for p in self.plants if p.is_alive]

        for layer, get_plots in [("foliar", lambda p: p.foliar_plots),
                                   ("root", lambda p: p.root_plots)]:
            # Index : plot → liste de plantes qui l'occupent
            plot_map: dict[tuple, list[PlantInstance]] = {}
            for p in alive:
                for plot in get_plots(p):
                    if self.is_valid_plot(*plot):
                        plot_map.setdefault(plot, []).append(p)

            # Plots occupés par 2+ plantes
            for plot, occupants in plot_map.items():
                if len(occupants) < 2:
                    continue
                # Vérifier si ce conflit est déjà signalé
                already = any(
                    c.conflict_type == layer
                    and len(c.plants) == len(occupants)
                    and all(p in occupants for p in c.plants)
                    for c in self.conflicts
                    if not c.resolved
                )
                if not already:
                    nc = ConflictNotification(
                        plants=occupants,
                        plots=[plot],
                        conflict_type=layer
                    )
                    new_conflicts.append(nc)
                    self.conflicts.append(nc)

        return new_conflicts

    def __repr__(self) -> str:
        alive = [p for p in self.plants if p.is_alive]
        return (
            f"Tuile[{self.tile_id}] sol={self.soil_type} "
            f"plantes={len(alive)} conflits={len([c for c in self.conflicts if not c.resolved])}"
        )

# ---------------------------------------------------------------------------
# CATALOGUE DES ESPÈCES DISPONIBLES
# ---------------------------------------------------------------------------

PLANT_CATALOGUE: dict[str, type] = {
    # Plantes cultivées
    "tomate":    Tomato,
    "poivron":   Pepper,
    "haricot":   Bean,
    "trefle":    Clover,
    "tournesol": Sunflower,
    "basilic":   Basil,
    # Adventices / succession écologique
    "bourse_pasteur": BursaPastoris,
    "minette":        MedicagoLupulina,
    "paturin":        PoaAnnua,
    "pissenlit":      Taraxacum,
}

# Catalogue des adventices uniquement (pour la succession)
WEED_CATALOGUE: dict[str, type] = {
    "pioneer":        BursaPastoris,
    "nitrogen_fixer": MedicagoLupulina,
    "grass":          PoaAnnua,
    "competitor":     Taraxacum,
}
