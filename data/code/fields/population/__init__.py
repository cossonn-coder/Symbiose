"""
SYMBIOSE — fields/population.py
Vie macroscopique observable (D31.1) — champs de population déterministes +
règle d'échantillonnage des sprites.

Modèle TRANCHÉ (docs/faune/vie_macro/conception_vie_macro.md §2, hybride) :
  - DYNAMIQUE = un `PopulationField` générique (sous-classe `GridField`),
    instancié une fois par ESPÈCE nommée (scission ④b/c/d), regroupée en catégorie
    (ravageur / auxiliaire / detritivore) + pollinisateurs par type, borné aux
    432 plots → ~gratuit (D32).
  - PERCEPTION = sprites ÉCHANTILLONNÉS depuis le champ (`sample_sprites`),
    fonction PURE déterministe densité → entités.

Périmètre D31.1 : les champs sont CALCULÉS mais RIEN dans la santé / la
croissance / la reproduction ne les LIT encore (le câblage écologique est
D31.2). → le golden reste INTACT. Aucune écriture sur les champs existants,
aucun log : pur effet de bord sur les champs de population.

Couche `fields` (patron `DisturbanceField` de grids.py). N'importe que
`fields.grids` et `fields.noise` — aucun cycle avec `ecofields` (qui détient les
champs et les ticke).
"""

# Paquet issu de la scission /refactor (2026-06-30) de l'ancien module
# monolithique `population.py` (632 LDC > 400). API publique INCHANGÉE : tout ce
# que les appelants importaient de `fields.population` reste ré-exporté ici (y
# compris les helpers `_`-préfixés utilisés par les tests).
from fields.population.constants import (
    POP_MAX, POP_INERTIA, daylength, _smoothstep,
)
from fields.population.spec import TrophicSpec, PollinatorSpec
from fields.population.field import PopulationField
from fields.population.resources import (
    _foliage_grid, _foliage_solanaceae_grid, _solanaceae_grid, _limace_food_grid,
    _litter_grid, _espece_grid, _undisturbed_grid, _undisturbed_structure_grid,
    _proies_grid, _rapace_habitat_grid, _habitat_nul_grid,
    _pile_grid, _base_habitat_grid, _merle_food_grid, _osmie_habitat_grid,
    _pollinisateur_habitat_grid, _abeille_habitat_grid,
    _aux_fruit_signal, _rav_fruit_signal,
    LIMACE_LITTER_W, LIMACE_FOLIAGE_W, DORY_AIL_REPULSE,
    PILE_HABITAT_W, MERLE_BASE_HABITAT, FRUIT_SIGNAL_REF, FRAC_AUX_POURRI,
)
from fields.population.registry import (
    build_population_specs, build_pollinator_registry, build_pollinator_specs,
    build_lifecycle_bridges, POLLINATOR_NAMES, _make_nectar_grid,
    _ATTRACT_ABEILLE, _ATTRACT_SYRPHE, _ATTRACT_PAPILLON, _ATTRACT_DEFAUT,
)
from fields.population.perception import (
    SpriteSample, sample_sprites, cap_sprites_global, peindre_presence,
    Carpophore, sample_carpophores,
    DENSITE_PAR_SPRITE, SPRITES_PAR_PLOT_MAX, SPRITES_MONDE_MAX,
    CARPO_MYCEL_MIN, CARPO_HUMIDE_MIN, _CARPO_AUTOMNE,
)
