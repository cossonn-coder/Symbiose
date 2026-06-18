"""
SYMBIOSE — paquet plants/
Ré-export de l'API publique (les sites d'appel font `from plants import X`).
"""

from plants.genetics import (
    GENE_NAMES, GENE_INIT_SIGMA, MUTATION_SIGMA,
    GENE_MIN, GENE_MAX, GENE_HARD_MIN, GENE_HARD_MAX,
    clamp_gene, neutral_genes, species_compatible,
)
from plants.base import (
    _plots_in_radius, STRATE_DEFAULTS, EFFECT_REGISTRY, register_effect,
    GrowthStage, Segment, Fruit, MAX_ORGANS, organ_sites,
    PlantInstance, ConflictNotification, PlantBase,
    Solanaceae, Fabaceae, Asteraceae, Lamiaceae, Poaceae,
)
from plants.species import (
    BursaPastoris, MedicagoLupulina, PoaAnnua, Taraxacum,
    Tomato, Pepper, Bean, Clover, Sunflower, Basil, Yarrow, Phacelia,
    Borage, Comfrey, Mustard, Thyme, Lavender,
)
from plants.perennials import (
    PerennialWoody, Fig, AppleTree, CherryTree, WalnutTree, OakTree,
)
from plants.catalogue import (
    PLANT_CATALOGUE, WEED_CATALOGUE, PERENNIAL_CATALOGUE,
)
