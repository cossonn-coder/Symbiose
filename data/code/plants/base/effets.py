"""
SYMBIOSE — plants/base/effets.py
Registre d'effets (callbacks complexes) : un décorateur enregistre des fonctions
d'effet sous une clé, lues par GrowthStage.callback (sim/effects). Couche basse
de `plants.base`, sans dépendance interne au paquet.
"""

from __future__ import annotations
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
