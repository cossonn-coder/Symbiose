"""
SYMBIOSE — tests/test_population.py
Filet de non-régression pour la vie macroscopique (D31.1).

Deux garanties :
  1. GOLDEN DE CHAMP — les densités des 4 champs de population
     (ravageur/auxiliaire/pollinisateur/vers_de_terre) sont DÉTERMINISTES et
     reproductibles sur N semaines (hash sha256 contre `population_hash.txt`).
  2. BORNES & PERCEPTION — densité ∈ [0, POP_MAX] partout ; `sample_sprites`
     respecte le cap par plot ; les positions de sprites sont INDÉPENDANTES de
     la semaine (pure fonction de seed/position/slot).

Lancement (depuis data/code/) :
  python3 -m tests.test_population            # vérifie contre population_hash.txt
  python3 -m tests.test_population --capture  # (re)capture le hash de référence
"""

import sys
import os
import hashlib

from world import Tile
from plants import Tomato, Basil, Sunflower, Bean, Yarrow, Phacelia
from fields import (init_eco, POP_MAX, SPRITES_PAR_PLOT_MAX,
                    sample_sprites, PopulationField, build_population_specs)
from sim.engine import Engine

N_WEEKS = 60
SEED = 0x5AB1057E
HASH_FILE = os.path.join(os.path.dirname(__file__), "population_hash.txt")
GUILDS = ("ravageur", "auxiliaire", "pollinisateur", "vers_de_terre")


def build_world():
    """Petit monde déterministe : 2 tuiles, jardin diversifié + attire-auxiliaires."""
    tiles, ecos = [], {}
    for i, soil in enumerate(["terre", "argile"]):
        tid = f"T{i}"
        tile = Tile(tile_id=tid, soil_type=soil)
        eco = init_eco(tid, 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
        tile.add_plant(Tomato,    2, 2)
        tile.add_plant(Basil,     2, 4)
        tile.add_plant(Bean,      4, 2)
        tile.add_plant(Sunflower, 0, 1)
        if i % 2 == 0:
            tile.add_plant(Yarrow,   3, 5)
            tile.add_plant(Phacelia, 1, 6)
        tiles.append(tile)
        ecos[tid] = eco
    return tiles, ecos


def _run(tiles, ecos):
    gs = {"tiles": tiles, "eco": ecos, "scores": {},
          "current_player": "joueur_1", "week": 1, "log": [], "seed": SEED}
    engine = Engine(gs)
    for _ in range(N_WEEKS):
        engine.tick_semaine()
        gs["log"].clear()
    return tiles, ecos


def population_digest(tiles, ecos) -> str:
    """Empreinte exacte des densités des 4 champs (round 6 → round-trip)."""
    lines = []
    for tile in tiles:
        eco = ecos[tile.tile_id]
        for g in GUILDS:
            f = eco.populations[g]
            lines.append(f"{tile.tile_id}/{g}")
            for r in range(f.rows):
                lines.append(" ".join(f"{f.at_plot(r, c):.6f}"
                                      for c in range(f.cols)))
    return "\n".join(lines)


def compute_hash() -> str:
    tiles, ecos = _run(*build_world())
    h = hashlib.sha256()
    h.update(population_digest(tiles, ecos).encode("utf-8"))
    return h.hexdigest()


# ---------------------------------------------------------------------------
# 2. BORNES & PERCEPTION
# ---------------------------------------------------------------------------

def test_bornes_densite():
    """Toute densité reste dans [0, POP_MAX] après une simulation."""
    tiles, ecos = _run(*build_world())
    for tile in tiles:
        for g in GUILDS:
            f = ecos[tile.tile_id].populations[g]
            for r in range(f.rows):
                for c in range(f.cols):
                    d = f.at_plot(r, c)
                    assert 0.0 <= d <= POP_MAX, f"{g}@{r},{c} densité {d} hors bornes"
    print("[pop] bornes densité ∈ [0, POP_MAX] : OK")


def test_cap_sprites():
    """sample_sprites ne dépasse jamais le cap par plot, même à densité saturée."""
    spec = build_population_specs()[0]
    f = PopulationField(spec, 6, 8)
    f.fill(POP_MAX)   # densité maximale partout → cap doit s'appliquer
    sprites = sample_sprites(f, SEED)
    per_plot = {}
    for s in sprites:
        per_plot[(s.row, s.col)] = per_plot.get((s.row, s.col), 0) + 1
    assert per_plot, "aucun sprite à densité max"
    assert max(per_plot.values()) <= SPRITES_PAR_PLOT_MAX, "cap par plot dépassé"
    # densité nulle → aucun sprite
    f.fill(0.0)
    assert sample_sprites(f, SEED) == [], "densité nulle devrait donner 0 sprite"
    print(f"[pop] cap sprites ≤ {SPRITES_PAR_PLOT_MAX}/plot : OK")


def test_positions_independantes_semaine():
    """
    Les positions de sprites ne dépendent QUE de seed/position/slot — donc deux
    échantillonnages du MÊME état de champ sont identiques, et un slot occupe
    toujours le même point quelle que soit la densité (tant qu'il reste visible).
    """
    spec = build_population_specs()[0]
    f = PopulationField(spec, 6, 8)
    f.fill(POP_MAX)
    a = sample_sprites(f, SEED)
    b = sample_sprites(f, SEED)
    assert [(s.row, s.col, s.slot, s.x_frac, s.y_frac) for s in a] == \
           [(s.row, s.col, s.slot, s.x_frac, s.y_frac) for s in b], \
           "échantillonnage non reproductible"
    # Le slot 0 d'un plot donné occupe le même point à densité faible ou forte.
    pos_haute = {(s.row, s.col, s.slot): (s.x_frac, s.y_frac) for s in a}
    f.fill(0.30)   # densité plus faible → moins de slots, mais positions stables
    for s in sample_sprites(f, SEED):
        assert pos_haute[(s.row, s.col, s.slot)] == (s.x_frac, s.y_frac), \
            "un slot a bougé quand la densité a changé (téléportation interdite)"
    print("[pop] positions indépendantes de la semaine : OK")


def test_determinisme_golden():
    """Le hash des densités doit être stable (deux runs identiques)."""
    h1 = compute_hash()
    h2 = compute_hash()
    assert h1 == h2, "densités non déterministes entre deux runs !"
    capture = "--capture" in sys.argv
    if capture or not os.path.exists(HASH_FILE):
        with open(HASH_FILE, "w") as f:
            f.write(h1 + "\n")
        print(f"[pop] hash de référence capturé : {h1}")
        return
    with open(HASH_FILE) as f:
        ref = f.read().strip()
    assert h1 == ref, f"divergence !\n  attendu : {ref}\n  obtenu  : {h1}"
    print(f"[pop] golden de champ — hash identique : {h1}")


def main():
    test_bornes_densite()
    test_cap_sprites()
    test_positions_independantes_semaine()
    test_determinisme_golden()
    print("[pop] TOUS LES TESTS PASSENT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
