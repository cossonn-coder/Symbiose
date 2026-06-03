"""
SYMBIOSE — paquet sim/
Orchestration de la simulation : effets, reproduction, banque-joueur,
succession et moteur de tick. Ré-export de l'API publique.
"""

from sim.effects import (
    resolve, resolve_plant_turn, apply_mutations,
    AddRondelle, RemoveRondelle, ReduceHealth, AddScore,
    InjectField, PropagateDisease, Notification,
    necromass_biomass, apply_disturbances,
    herbivory_pressure, damping_off, fungal_disease, background_mortality,
)
from sim.seeds import Seed, PlayerSeedBank
from sim.reproduction import (
    find_father, child_genes, is_seed_bearing, pollinator_reach,
)
from sim.succession import choisir_archetype, succession, spring_flush
from sim.engine import Engine, saison_de
