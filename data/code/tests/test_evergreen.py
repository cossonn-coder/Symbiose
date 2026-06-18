"""
SYMBIOSE — tests/test_evergreen.py
Catalogue enrichi, tronçon ② — verrou du chemin `winter_strategy="evergreen"`.

Le chemin evergreen (sim/engine/mortalite.py:_winter_transition) existait dans le
moteur mais n'était exercé par AUCUNE espèce avant l'ajout du thym et de la
lavande. Une vivace evergreen NE meurt PAS l'hiver et n'entre PAS en dormance
profonde — juste une légère réduction métabolique (stress_memory +0.05). Ce test
plante un thym, le fait traverser ≥1 hiver complet (la transition hivernale est
déclenchée semaines 49-52, cf. boucle.py) et vérifie qu'il est ENCORE VIVANT et
ENCORE FEUILLÉ en hiver (evergreen ⇒ non caduc ⇒ ombre non nulle même au gel).

Sanity catalogue : les 5 nouvelles espèces (thym, lavande, bourrache, consoude,
moutarde) s'instancient, germent et dépassent le stade semis.

Lancement (depuis data/code/) :
  python3 -m tests.test_evergreen
"""

import sys

from world import Tile
from plants import Thyme, Lavender, Borage, Comfrey, Mustard
from plants.catalogue import PLANT_CATALOGUE
from fields import init_eco
from sim.engine import Engine

WEEKS_PAST_WINTER = 60   # > 52 → traverse la transition hivernale (semaines 49-52)


def _engine_with(tile, eco):
    """Engine sur une tuile + eco, germination spontanée NEUTRALISÉE (on isole le
    comportement des plantes posées, pas la succession)."""
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    game_state = {
        "tiles": [tile], "eco": {tile.tile_id: eco}, "scores": {},
        "current_player": "joueur_1", "week": 1, "log": [],
    }
    return Engine(game_state)


def test_thym_survit_hiver():
    """Un thym (evergreen) traverse un hiver SANS mourir et garde son feuillage."""
    tile = Tile(tile_id="EV", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("EV", 6, 6, humidite=1.5, fertilite=1.2, microbiome=0.3)
    engine = _engine_with(tile, eco)
    thym = tile.add_plant(Thyme, 3, 3)

    for _ in range(WEEKS_PAST_WINTER):
        engine.tick_semaine()

    assert thym.is_alive, "le thym evergreen est mort en traversant l'hiver"
    foliage_hiver = thym.plant_class.foliage_density_at(thym, saison="hiver")
    assert foliage_hiver > 0.0, (
        f"thym evergreen sans feuillage en hiver (densité {foliage_hiver}) — "
        "un evergreen n'est pas caduc")
    print(f"[evergreen] PASS — thym vivant après hiver, feuillage hiver "
          f"{foliage_hiver:.2f} (âge {thym.age_years:.1f} ans)")


def test_catalogue_germination():
    """Les 5 nouvelles espèces germent et dépassent le stade semis."""
    especes = {"thym": Thyme, "lavande": Lavender, "bourrache": Borage,
               "consoude": Comfrey, "moutarde": Mustard}
    # Présence + identité dans le catalogue
    for cle, klass in especes.items():
        assert PLANT_CATALOGUE.get(cle) is klass, f"{cle} absent/incorrect du catalogue"

    tile = Tile(tile_id="GE", soil_type="terre", grid_rows=6, grid_cols=8)
    eco = init_eco("GE", 6, 8, humidite=1.5, fertilite=1.2, microbiome=0.3)
    engine = _engine_with(tile, eco)
    posees = {cle: tile.add_plant(klass, 1 + i, 1 + i)
              for i, (cle, klass) in enumerate(especes.items())}

    for _ in range(12):   # > durée des stades semis (2-3 sem) avec marge
        engine.tick_semaine()

    for cle, inst in posees.items():
        assert inst.is_alive, f"{cle} est morte avant d'atteindre l'âge adulte"
        assert inst.current_stage >= 1, (
            f"{cle} n'a pas dépassé le stade semis (stade {inst.stage.name})")
    print(f"[evergreen] PASS — 5 espèces germent et atteignent un stade adulte : "
          f"{', '.join(especes)}")


def main():
    test_thym_survit_hiver()
    test_catalogue_germination()
    print("[evergreen] TOUS LES TESTS PASSENT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
