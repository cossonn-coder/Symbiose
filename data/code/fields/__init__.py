"""
SYMBIOSE — paquet fields/
Ré-export de l'API publique des champs écologiques. Conserve exactement la
surface de l'ancien module plat `fields.py` (les sites d'appel font
`from fields import X`).
"""

from constants import PLOT_CM

from fields.noise import (
    _hash_noise, hash_gauss, climate_stress, CLIMATE_AMPLITUDE,
)
from fields.grids import (
    GridField, DisturbanceField,
    MORTALITY_RATE, HERBIVORY_BASE, DISTURBANCE_INERTIA,
)
from fields.light import (
    LightField, solar_slice, _point_in_capsule,
    LATITUDE_DEG, LIGHT_FLOOR, SOLAR_DECLINATION, SOLAR_HOUR_ANGLES,
    CANOPY_SAMPLE_FRAC,
)
from fields.seedbank import (
    SeedBank, GeneStat, GrainEnAttente,
    SEED_ARCHETYPES, SEED_VIABILITY_LOSS, SEED_DISTURBANCE_GAIN,
    SEED_LATE_GAIN, SEED_LATE_MIN_MATURITY, SEED_COMPETITOR_MATURITY,
    SPECIES_SEED_VIABILITY_LOSS, SPECIES_POOL_MIN_DENSITY,
)
from fields.population import (
    PopulationField, TrophicSpec, SpriteSample,
    build_population_specs, sample_sprites,
    POP_MAX, POP_INERTIA, DENSITE_PAR_SPRITE, SPRITES_PAR_PLOT_MAX,
)
from fields.ecofields import (
    EcoFields, init_eco, inject_patch,
    HUMIDITY_INERTIA, FERTILITY_INERTIA, MICROBE_INERTIA,
    BASE_RAIN, EVAPORATION, DRAINAGE, SOIL_RETENTION, DRAINAGE_PAR_SOL,
    HUM_EXCES, HUM_NOYE, ASPHYXIE_UPTAKE_MALUS, ASPHYXIE_UPTAKE_FLOOR,
    ASPHYXIE_MEMORY_LERP, ASPHYXIE_HEALTH_SEUIL, ASPHYXIE_RATE,
    T_AMBIENT_INIT, TEMP_MIN, TEMP_MAX,
    EVAP_TEMP_REF, EVAP_TEMP_COEF, EVAP_MIN,
    OM_FRESH_DECAY, OM_ACTIVE_DECAY, OM_STABLE_DECAY,
    OM_FRESH_HUMIF, OM_FRESH_MINER, OM_ACTIVE_HUMIF, OM_ACTIVE_MINER,
    OM_STABLE_MINER, LEACHING_LOSS, BIOMASS_EXPORT,
    MICROBE_FOOD_REF, MICROBE_DECAY_MAX,
    EXUDATE_BASE, EXUDATE_OM_SHARE, UPTAKE_MICRO_BONUS,
    VIT_W_MICRO, VIT_W_ACTIVE, VIT_W_FERT, VIT_W_STRUCTURE, VIT_W_DISTURB,
    SOIL_FAST_RATE, SOIL_DEEP_RATE,
    SENESCENCE_ONSET, SEN_RATE, HEAL_RATE, HEAL_SEN_CUTOFF,
    DAMPOFF_BASE, DAMPOFF_HUM_SEUIL, FUNGAL_BASE,
    RESEED_RADIUS_CM, NECROMASS_PER_CM,
    UPTAKE, SOIL_SIGNATURE,
)
