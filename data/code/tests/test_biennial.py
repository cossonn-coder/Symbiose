"""
SYMBIOSE — tests/test_biennial.py
Catalogue enrichi, tronçon ③ — verrou du GATE ANNUEL des bisannuelles.

Le cycle `life_cycle="biennial"` existait dans le moteur (longévité 2 ans +
mort monocarpique à age>=2, mortalite.py) mais n'était exercé par AUCUNE espèce,
et la progression de stade n'avait AUCUN gate annuel : une bisannuelle aux stades
courts montait à fleur dès l'an 1 (trou confirmé au kickoff). Le tronçon ③ ajoute
un gate dans sim/engine/croissance.py (`_bolt_bloque`) : une bisannuelle ne
franchit pas son stade de MONTAISON (1er stade portant un effet `floraison`) tant
que `age_years < 1.0` → rosette l'an 1, montaison/floraison l'an 2.

Ce test plante une carotte (Apiaceae) et un ail (Amaryllidaceae), simule 2+ ans
et vérifie :
  (a) AN 1 : la plante reste sous le stade de montaison (rosette/feuilles) ;
  (b) AN 2 : elle atteint le stade de montaison (ombelle/hampe), qui porte bien
      l'effet floraison→pollinisateur (preuve que le gate s'ouvre AU bon stade) ;
  (c) elle meurt en fin de 2ᵉ année (âge ~2 ans) — fin de vie de la bisannuelle.

Note sur (c) : pour une bisannuelle de longévité 2, la rampe de sénescence de
fin de vie (mortalite._tick_senescence_health) atteint la plante autour de
l'âge ~1.9, juste avant le déclencheur monocarpique à age>=2.0. Les deux
expriment le même fait — « meurt en fin d'an 2 après avoir fleuri ». Le test ne
couple donc pas la mort à UN chemin précis, seulement à « morte, en an 2 ».

Lancement (depuis data/code/) :
  python3 -m tests.test_biennial
"""

import sys

from world import Tile
from plants import Carrot, Garlic
from fields import init_eco
from sim.engine import Engine
from sim.engine.croissance import _bolt_stage_index


def _engine_with(tile, eco):
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    game_state = {
        "tiles": [tile], "eco": {tile.tile_id: eco}, "scores": {},
        "current_player": "joueur_1", "week": 1, "log": [],
    }
    return Engine(game_state)


def _bolt_has_pollinisateur(plant_class) -> bool:
    """Le stade de montaison porte-t-il un effet floraison→pollinisateur ?"""
    bolt = _bolt_stage_index(plant_class)
    if bolt is None:
        return False
    return any(e.get("type") == "floraison" and e.get("variable") == "pollinisateur"
               for e in plant_class.growth_stages[bolt].effects)


def _run_biennial(klass, nom):
    tile = Tile(tile_id="BI", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("BI", 6, 6, humidite=0.9, fertilite=1.2, microbiome=0.3)
    engine = _engine_with(tile, eco)
    plant = tile.add_plant(klass, 3, 3)

    bolt = _bolt_stage_index(klass)
    assert bolt is not None, f"{nom} : aucun stade de montaison (effet floraison) détecté"

    y1_max_stage = 0
    reached_bolt = False
    death_age = None
    for w in range(1, 130):
        engine.tick_semaine()
        alive = plant in tile.plants and plant.is_alive
        if w <= 52 and alive:
            y1_max_stage = max(y1_max_stage, plant.current_stage)
        if alive and plant.current_stage >= bolt:
            reached_bolt = True
        if death_age is None and not alive:
            death_age = plant.age_years

    # (a) An 1 : jamais atteint la montaison.
    assert y1_max_stage < bolt, (
        f"{nom} : a franchi la montaison dès l'an 1 (stade max {y1_max_stage} "
        f"≥ montaison {bolt}) — le gate annuel a fui")
    # (b) An 2 : atteint la montaison, qui porte l'effet floraison→pollinisateur.
    assert reached_bolt, f"{nom} : n'a jamais atteint la montaison en an 2"
    assert _bolt_has_pollinisateur(klass), (
        f"{nom} : le stade de montaison ne pose pas de rondelle pollinisateur")
    # (c) Morte en fin d'an 2 (âge ~2 ans).
    assert death_age is not None, f"{nom} : toujours vivante après 2+ ans (pas de mort)"
    assert 1.4 <= death_age <= 2.3, (
        f"{nom} : mort à âge {death_age:.2f} hors de la fenêtre de fin d'an 2")
    print(f"[biennial] PASS — {nom} : rosette an 1 (stade max {y1_max_stage}), "
          f"montaison an 2 (stade {bolt}), morte à {death_age:.2f} ans")


def test_carotte_gate():
    _run_biennial(Carrot, "carotte")


def test_ail_gate():
    _run_biennial(Garlic, "ail")


def main():
    test_carotte_gate()
    test_ail_gate()
    print("[biennial] TOUS LES TESTS PASSENT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
