"""
SYMBIOSE — tests/test_golden.py
Filet de non-régression DÉTERMINISTE — désormais un SMOKE TEST rapide.

Le moteur est déterministe (règle de design #3) : ce test rejoue un scénario fixe
et calcule un hash sha256 de (1) le LOG complet semaine par semaine + (2) un
DIGEST d'état final (chaque plante + champs écologiques de chaque tuile). Si le
hash diffère de la référence (`golden_hash.txt`), le comportement a bougé.

REFONTE smoke test (sprint maison, tronçon 1 — décision Q4,
CONCEPTION_MAISON_OMBRE.md §7). Le golden n'est plus le scénario lourd de
`main.py` (devenu une démo) : il vise « quelques secondes » pour tourner souvent.
Petit monde, court horizon, mais qui exerce toujours le cœur du tick :
succession + reproduction (automne) + transition hivernale + pérenne (pommier)
+ multi-sol (terre/argile).

Ce qui NE rentre plus ici, par construction trop long :
  - sénescence du pommier (~70 ans) → `tests/test_senescence.py` (lancé à la demande).
  - ombre de la maison / phototropisme (tronçons 2-3) → tests ciblés dédiés.

Lancement (depuis data/code/) :
  python3 -m tests.test_golden            # vérifie contre golden_hash.txt
  python3 -m tests.test_golden --capture  # (re)capture le hash de référence
"""

import sys
import os
import hashlib

from world import Tile
from plants import (Tomato, Basil, Sunflower, Bean, Clover, Pepper,
                    Yarrow, Phacelia, AppleTree)
from fields import init_eco
from sim.engine import Engine

# Smoke test : 2 sols contrastés, 4 ans (assez pour succession + automne ×4 +
# hiver ×4 + croissance du pommier ; pas pour sa sénescence, cf. en-tête).
N_YEARS = 4
SOILS = ["terre", "argile"]
HASH_FILE = os.path.join(os.path.dirname(__file__), "golden_hash.txt")

# Attributs d'instance capturés dans le digest (ordre fixe).
_PLANT_ATTRS = ("current_stage", "age_weeks", "age_years", "health",
                "growth_factor", "x_cm", "y_cm",
                "shade_memory", "drought_memory", "stress_memory")
_RONDELLES = ("fertilite", "humidite", "lombric", "maladie",
              "pollinisateur", "paillage", "auxiliaire")


def build_world():
    """Monde déterministe du smoke test : 2 tuiles 6×8 (terre/argile), jardin
    diversifié + attire-auxiliaires sur la tuile paire, un pommier (pérenne)."""
    tiles = []
    ecos = {}
    for i, soil in enumerate(SOILS):
        tid = f"T{i}"
        tile = Tile(tile_id=tid, soil_type=soil)
        if soil == "argile":
            eco = init_eco(tid, 6, 8, humidite=2.0, fertilite=1.2, microbiome=0.3)
        else:
            eco = init_eco(tid, 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
        # Jardin diversifié de base
        tile.add_plant(Tomato,    2, 2)
        tile.add_plant(Basil,     2, 4)
        tile.add_plant(Bean,      4, 2)
        tile.add_plant(Sunflower, 0, 1)
        tile.add_plant(Pepper,    4, 6)
        if i % 2 == 0:  # attire-auxiliaires sur les tuiles paires
            tile.add_plant(Yarrow,   3, 5)
            tile.add_plant(Phacelia, 1, 6)
            tile.add_plant(Clover,   5, 4)
        tiles.append(tile)
        ecos[tid] = eco
    # Pommier sur la tuile 0 (exerce les pérennes : dormance hivernale, age_curve)
    tiles[0].add_plant(AppleTree, 0, 7)
    return tiles, ecos


def final_digest(tiles, ecos) -> str:
    """Empreinte exacte de l'état final (floats via repr → round-trip)."""
    lines = []
    for tile in tiles:
        lines.append(f"TILE {tile.tile_id} {tile.soil_type}")
        for r in _RONDELLES:
            lines.append(f"  ROND {r}={tile.get_rondelle_count(r)}")
        for p in tile.plants:  # ordre naturel = déterministe
            attrs = " ".join(f"{a}={getattr(p, a)!r}" for a in _PLANT_ATTRS)
            genes = " ".join(f"{k}={p.genes[k]!r}" for k in sorted(p.genes))
            lines.append(f"  P {p.name} pos={p.position} alive={p.is_alive} "
                         f"{attrs} GENES[{genes}]")
        s = ecos[tile.tile_id].summary()
        lines.append("  ECO " + " ".join(f"{k}={s[k]!r}" for k in sorted(s)))
    return "\n".join(lines)


def compute_hash() -> str:
    tiles, ecos = build_world()
    game_state = {
        "tiles": tiles, "eco": ecos, "scores": {},
        "current_player": "joueur_1", "week": 1, "log": [],
    }
    engine = Engine(game_state)
    h = hashlib.sha256()
    for _ in range(N_YEARS):
        for _ in range(52):
            log = engine.tick_semaine()
            for line in log:
                h.update(line.encode("utf-8"))
                h.update(b"\n")
            game_state["log"].clear()  # borne la mémoire
    h.update(b"=== FINAL DIGEST ===\n")
    h.update(final_digest(tiles, ecos).encode("utf-8"))
    return h.hexdigest()


def main():
    capture = "--capture" in sys.argv
    digest = compute_hash()
    if capture or not os.path.exists(HASH_FILE):
        with open(HASH_FILE, "w") as f:
            f.write(digest + "\n")
        print(f"[golden] hash de référence capturé : {digest}")
        return 0
    with open(HASH_FILE) as f:
        ref = f.read().strip()
    if digest == ref:
        print(f"[golden] PASS — hash identique : {digest}")
        return 0
    print(f"[golden] FAIL — divergence !\n  attendu : {ref}\n  obtenu  : {digest}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
