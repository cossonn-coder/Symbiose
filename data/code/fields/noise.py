"""
SYMBIOSE — fields/noise.py
Bruit spatial déterministe + oscillation climatique (fondation pure).

Aucun import interne au projet, aucun RNG live (règle de design #3) → tout le
moteur peut s'appuyer dessus sans cycle.
"""

from __future__ import annotations
import math

# Amplitude de l'oscillation climatique de fond (utilisée par climate_stress).
CLIMATE_AMPLITUDE = 0.080


def _hash_noise(seed: int, week: int, r: int, c: int) -> float:
    """
    Bruit spatial déterministe — aucun RNG pendant le tick.
    Combine seed global, semaine et coordonnées → float [0, 1].
    Utilise un hash entier rapide (PCG-inspired).
    """
    h = seed ^ (week * 0x9e3779b9) ^ (r * 0x6c62272e) ^ (c * 0x517cc1b7)
    h = ((h >> 16) ^ h) * 0x45d9f3b
    h = ((h >> 16) ^ h) * 0x45d9f3b
    h = (h >> 16) ^ h
    return (h & 0x7FFFFFFF) / 0x7FFFFFFF


def hash_gauss(seed: int, week: int, r: int, c: int, k: int = 0) -> float:
    """
    Échantillon N(0,1) déterministe — Box-Muller sur deux tirages _hash_noise
    décorrélés. Aucun RNG live (règle de design #3). `k` décale le flux pour
    obtenir plusieurs tirages indépendants au même (semaine, position).
    """
    u1 = max(1e-9, _hash_noise(seed, week * 2 + k,     r, c))
    u2 =            _hash_noise(seed, week * 2 + k + 1, r, c)
    return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)


def climate_stress(year_fraction: float, phase: float = 0.0) -> float:
    """
    Oscillation climatique lente — sin(2π * fraction_annuelle + phase).
    Retourne une valeur dans [-CLIMATE_AMPLITUDE, +CLIMATE_AMPLITUDE].
    Le joueur ne voit rien explicitement, mais le jardin change d'humeur.
    """
    return math.sin(year_fraction * 2 * math.pi + phase) * CLIMATE_AMPLITUDE
