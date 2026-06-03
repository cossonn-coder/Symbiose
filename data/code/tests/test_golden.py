"""
SYMBIOSE — tests/test_golden.py
Filet de non-régression DÉTERMINISTE pour le sprint refactor structurel.

Le refactor ne doit RIEN changer au comportement (règle de design #3 :
simulation déterministe). Ce test rejoue un scénario fixe et calcule un hash
sha256 de :
  1. le LOG complet, semaine par semaine (concaténé incrémentalement) ;
  2. un DIGEST d'état final (chaque plante + champs écologiques de chaque tuile).

Si le hash après refactor diffère du hash de référence (`golden_hash.txt`),
le comportement a bougé → on s'arrête.

Scénario (choisi 2026-06-03) : monde 3 tuiles (terre/argile/sable), jardin
diversifié + attire-auxiliaires sur les tuiles d'index pair, un pommier sur la
tuile 0 pour exercer pérennes + sénescence (~70 ans), sur 100 ans. Couvre
succession + reproduction + sénescence + hiver + multi-sol.

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

N_YEARS = 100
SOILS = ["terre", "argile", "sable"]
HASH_FILE = os.path.join(os.path.dirname(__file__), "golden_hash.txt")

# Attributs d'instance capturés dans le digest (ordre fixe).
_PLANT_ATTRS = ("current_stage", "age_weeks", "age_years", "health",
                "growth_factor", "x_cm", "y_cm",
                "shade_memory", "drought_memory", "stress_memory")
_RONDELLES = ("fertilite", "humidite", "lombric", "maladie",
              "pollinisateur", "paillage", "auxiliaire")


def build_world():
    """Construit le monde déterministe du golden (météo désormais pure : plus de
    random.seed — cf. sous-sprint 01 déterminisation, CONCEPTION_METEO.md §0)."""
    tiles = []
    ecos = {}
    for i, soil in enumerate(SOILS):
        tid = f"T{i}"
        tile = Tile(tile_id=tid, soil_type=soil)
        if soil == "sable":
            eco = init_eco(tid, 6, 8, humidite=1.0, fertilite=0.6, microbiome=0.2)
        elif soil == "argile":
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
    # Pommier sur la tuile 0 (exerce pérennes + sénescence sur 100 ans)
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
