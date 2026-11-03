"""
SYMBIOSE — tests/test_trefle_cycle.py
Cycle de l'azote du trèfle (sprint TRÈFLE DOMINANT ①, D126) :
  - la fixation d'une Fabaceae décroît avec l'azote du plot, nulle à saturation ;
  - un effet sans la clé `sature_a` garde son flux constant ;
  - le pied de trèfle finit par mourir de vieillesse, et la colonie lui survit ;
  - le tout est déterministe (philo #3).

Lancement (depuis data/code/) : python3 -m tests.test_trefle_cycle
"""

import sys

import sim.champignon_role as _champ_role
import sim.engine.boucle as _boucle
import sim.wind as _wind
from fields import init_eco
from plants import Bean, Clover, MedicagoLupulina, Taraxacum
from sim.effects.mutations import InjectField
from sim.effects.resolution import resolve
from sim.engine import Engine
from sim.weather import CALME
from world import Tile


def _monde(espece, n_plot: float):
    """Tuile 6×6 dont l'azote est uniforme, une plante au centre, au stade adulte."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("T0", 6, 6, humidite=1.5, fertilite=1.2, microbiome=0.3)
    for r in range(6):
        for c in range(6):
            eco.n.data[r][c] = n_plot
    plant = tile.add_plant(espece, 3, 3)
    plant.current_stage = len(espece.growth_stages) - 1
    return tile, eco, plant, {"tiles": [tile], "eco": {"T0": eco}, "seed": 42, "week": 1}


def _azote_injecte(espece, n_plot: float) -> float:
    """Azote total qu'une plante injecte en une semaine, tous effets confondus."""
    tile, _, plant, gs = _monde(espece, n_plot)
    effets = plant.plant_class().get_all_effects(plant.current_stage)
    mutations = [m for e in effets for m in resolve(e, plant, tile, gs, "weekly")]
    return sum(m.amount for m in mutations
               if isinstance(m, InjectField) and m.variable == "n")


def test_fixation_decroit_avec_azote():
    for espece in (Clover, Bean, MedicagoLupulina):
        flux = [_azote_injecte(espece, n) for n in (0.0, 0.4, 0.8, 1.2)]
        assert flux[0] > flux[1] > flux[2] > flux[3] >= 0.0, f"{espece.name} : {flux}"
        assert _azote_injecte(espece, 3.0) == 0.0, f"{espece.name} fixe à saturation"
    assert abs(_azote_injecte(Clover, 0.0) - 0.03) < 1e-9, "fixation pleine sur sol nu"


def test_espece_sans_cle_inchangee():
    pauvre, riche = _azote_injecte(Taraxacum, 0.0), _azote_injecte(Taraxacum, 3.0)
    assert pauvre == riche and abs(pauvre - 0.03) < 1e-9, f"pissenlit : {pauvre} / {riche}"


def _meteo_labo(seed, week, pluie_forcee=False):
    return CALME, 15.0, 0.1


def _colonie(annees: int):
    """Un trèfle fondateur en climat de laboratoire, sans germination spontanée.
    Renvoie (âge du fondateur à sa mort ou None, photo de la tuile à chaque fin d'année)."""
    _boucle.weather_state = _meteo_labo
    _wind.weather_at = lambda seed, week: CALME
    _champ_role.weather_state = _meteo_labo
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("T0", 6, 6, humidite=1.5, fertilite=1.2, microbiome=0.3)
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    fondateur = tile.add_plant(Clover, 3, 3)
    engine = Engine({"tiles": [tile], "eco": {"T0": eco}, "scores": {},
                     "current_player": "joueur_1", "week": 1, "log": []})
    age_mort, photos = None, []
    for sem in range(1, annees * 52 + 1):
        engine.tick_semaine()
        engine.game_state["log"].clear()
        if age_mort is None and not fondateur.is_alive:
            age_mort = fondateur.age_years
        if sem % 52 == 0:
            photos.append(sorted((p.name, p.position, round(p.vitalite, 6))
                                 for p in tile.plants if p.is_alive))
    return age_mort, photos


def test_pied_meurt_colonie_survit_deterministe():
    annees = 6
    age_mort, photos = _colonie(annees)
    assert age_mort is not None, f"fondateur encore vivant après {annees} ans"
    assert age_mort > Clover.longevity() * 0.7, f"mort trop tôt pour la vieillesse : {age_mort:.2f} ans"
    trefles = [x for x in photos[-1] if x[0] == Clover.name]
    assert trefles, "la colonie n'a pas survécu au fondateur"
    assert _colonie(annees) == (age_mort, photos), "deux runs identiques divergent"
    print(f"[trefle_cycle] fondateur mort à {age_mort:.2f} ans, "
          f"{len(trefles)} pieds après {annees} ans")


if __name__ == "__main__":
    for test in (test_fixation_decroit_avec_azote, test_espece_sans_cle_inchangee,
                 test_pied_meurt_colonie_survit_deterministe):
        try:
            test()
            print(f"[trefle_cycle] PASS — {test.__name__}")
        except AssertionError as e:
            print(f"[trefle_cycle] FAIL — {test.__name__} : {e}")
            sys.exit(1)
    sys.exit(0)
