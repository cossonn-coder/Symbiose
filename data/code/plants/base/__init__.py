"""
SYMBIOSE — plants/base (paquet)
Hiérarchie de plantes : empreintes métriques, registre d'effets, stade de
croissance, instance de plante, notification de conflit, PlantBase abstrait +
5 familles botaniques.

Éclaté en paquet au Sprint refactor global (SS④, 2026-06-15) ; l'ancien
`plants/base.py` (738 l) devient ce paquet. L'API publique est ré-exportée ici →
tous les imports existants (`from plants.base import PlantInstance, GrowthStage,
Segment, PlantBase…`) et le ré-export en bloc de `plants/__init__.py` marchent
sans changement.

Orientation :
  - `empreintes.py` — _plots_in_radius + défauts métriques par strate
  - `effets.py`     — registre d'effets (callbacks complexes)
  - `stades.py`     — GrowthStage, Segment, Fruit, organ_sites
  - `instance.py`   — PlantInstance, ConflictNotification
  - `familles.py`   — PlantBase abstrait + 5 familles botaniques
"""

from .empreintes import (_plots_in_radius, STRATE_DEFAULTS,
                         STRATE_SHADE_TOLERANCE, PROC_ROOT_RATIO)
from .effets import EFFECT_REGISTRY, register_effect
from .stades import GrowthStage, Segment, Fruit, MAX_ORGANS, organ_sites
from .instance import PlantInstance, ConflictNotification
from .familles import (PlantBase,
                       Solanaceae, Fabaceae, Asteraceae, Lamiaceae, Poaceae,
                       Urticaceae, Amaryllidaceae, Ericaceae, Violaceae,
                       Sphagnaceae, Droseraceae)

__all__ = [
    "_plots_in_radius", "STRATE_DEFAULTS", "STRATE_SHADE_TOLERANCE", "PROC_ROOT_RATIO",
    "EFFECT_REGISTRY", "register_effect",
    "GrowthStage", "Segment", "Fruit", "MAX_ORGANS", "organ_sites",
    "PlantInstance", "ConflictNotification", "PlantBase",
    "Solanaceae", "Fabaceae", "Asteraceae", "Lamiaceae", "Poaceae",
    "Urticaceae", "Amaryllidaceae", "Ericaceae", "Violaceae", "Sphagnaceae",
    "Droseraceae",
]
