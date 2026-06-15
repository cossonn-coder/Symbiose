"""
SYMBIOSE — sim/effects (paquet)
Système hybride probabiliste.

Effets discrets (maladie, pollinisateur) : probabilité modulée par les champs.
Effets flux (microbiome, fertilité) : injection directe dans les champs continus.
Philosophie : jamais bonus/malus directs sur les plantes — flux → contrainte
écologique → réponse biologique émergente.

Éclaté en paquet au Sprint refactor global (SS③, 2026-06-15) ; l'ancien
`sim/effects.py` (703 l) devient ce paquet. L'API publique est ré-exportée ici →
tous les imports existants (`from sim.effects import apply_mutations,
deposer_mort, AddRondelle…`) et le ré-export en bloc de `sim/__init__.py`
marchent sans changement.

Orientation :
  - `mutations.py`     — vocabulaire des mutations (dataclasses)
  - `resolution.py`    — resolve / callbacks / apply_mutations / resolve_plant_turn
  - `perturbations.py` — mortalités de fond, herbivorie, deposer_mort, apply_disturbances
"""

from .mutations import (AddRondelle, RemoveRondelle, ReduceHealth, AddScore,
                        InjectField, PropagateDisease, Notification, Mutation)
from .resolution import (resolve, basil_companion_check, apply_mutations,
                         resolve_plant_turn)
from .perturbations import (
    necromass_biomass, tissu_mort, frac_bois_mort, deposer_mort,
    damping_off, fungal_disease, drought_stress_damage,
    herbivory_pressure, background_mortality, apply_disturbances,
    DROUGHT_DAMAGE_THRESHOLD, DROUGHT_DAMAGE_RATE,
    HERBIVORY_GAIN, HERBIVORY_LETHAL_AUX, HERBIVORY_LETHAL_MICRO,
)

__all__ = [
    "AddRondelle", "RemoveRondelle", "ReduceHealth", "AddScore",
    "InjectField", "PropagateDisease", "Notification", "Mutation",
    "resolve", "basil_companion_check", "apply_mutations", "resolve_plant_turn",
    "necromass_biomass", "tissu_mort", "frac_bois_mort", "deposer_mort",
    "damping_off", "fungal_disease", "drought_stress_damage",
    "herbivory_pressure", "background_mortality", "apply_disturbances",
    "DROUGHT_DAMAGE_THRESHOLD", "DROUGHT_DAMAGE_RATE",
    "HERBIVORY_GAIN", "HERBIVORY_LETHAL_AUX", "HERBIVORY_LETHAL_MICRO",
]
