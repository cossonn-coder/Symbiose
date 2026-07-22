"""
SYMBIOSE — tests/test_golden.py
Filet de non-régression DÉTERMINISTE — désormais un SMOKE TEST rapide.

Le moteur est déterministe (règle de design #3) : ce test rejoue un scénario fixe
et calcule un hash sha256 de (1) le LOG complet semaine par semaine + (2) un
DIGEST d'état final (chaque plante + champs écologiques de chaque tuile). Si le
hash diffère de la référence (`golden_hash.txt`), le comportement a bougé.

REFONTE smoke test (sprint maison, tronçon 1 — décision Q4,
docs/champs/lumiere/conception_maison_ombre.md §7). Le golden n'est plus le scénario lourd de
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

from world import Tile, House
from plants import (Tomato, Basil, Sunflower, Bean, Clover, Pepper,
                    Yarrow, Phacelia, AppleTree)
from fields import init_eco
from sim.engine import Engine
from sim.seeds import semer_fondateur

# Seed global du terrain (déterminisme, philo #3) — celui que l'Engine prend par
# défaut (`game_state.get("seed", 42)`). Partagé par les semis directs FONDATEURS
# (`semer_fondateur`, sprint DIVERSITÉ FONDATRICE ①) pour que leur variance
# génétique dérive du MÊME canal que le reste de la simulation.
SEED = 42

# Smoke test : 2 sols contrastés, 2 ans (raccourci au sous-sprint ① décompo —
# assez pour succession + automne ×2 + hiver ×2 + croissance du pommier ; pas
# pour sa sénescence, cf. en-tête). Étendu à 4 ans = trop long pour un smoke.
N_YEARS = 2
SOILS = ["terre", "argile"]
HASH_FILE = os.path.join(os.path.dirname(__file__), "golden_hash.txt")

# Attributs d'instance capturés dans le digest (ordre fixe).
_PLANT_ATTRS = ("current_stage", "age_weeks", "age_years", "vitalite",
                "growth_factor", "x_cm", "y_cm",
                "shade_memory", "drought_memory", "stress_memory")
_RONDELLES = ("fertilite", "humidite", "lombric", "maladie",
              "pollinisateur", "paillage", "auxiliaire")


# Offsets monde des 2 tuiles vs la maison centrée (1000,1000 ; empreinte
# [600,600]→[1400,1400]) : T0 au NORD (subit l'ombre), T1 au SUD (zone albédo).
# Le smoke test exerce ainsi l'ombre + l'albédo de la maison (tronçon 2).
TILE_ORIGINS = {0: (700.0, 0.0), 1: (700.0, 1500.0)}


def build_world():
    """Monde déterministe du smoke test : 2 tuiles 6×8 (terre/argile), jardin
    diversifié + attire-auxiliaires sur la tuile paire, un pommier (pérenne).
    Maison centrée → ombre/albédo injectés (T0 ombragée au nord, T1 au sud)."""
    tiles = []
    ecos = {}
    for i, soil in enumerate(SOILS):
        tid = f"T{i}"
        ox, oy = TILE_ORIGINS[i]
        tile = Tile(tile_id=tid, soil_type=soil, origin_x_cm=ox, origin_y_cm=oy)
        if soil == "argile":
            eco = init_eco(tid, 6, 8, humidite=2.0, fertilite=1.2, microbiome=0.3,
                           soil_type=soil, heterogene=True)
        else:
            eco = init_eco(tid, 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3,
                           soil_type=soil, heterogene=True)
        # Jardin diversifié de base — semis FONDATEURS (variance génétique propre,
        # sprint DIVERSITÉ FONDATRICE ① : plus de clones neutres au démarrage).
        semer_fondateur(tile, Tomato,    2, 2, SEED)
        semer_fondateur(tile, Basil,     2, 4, SEED)
        semer_fondateur(tile, Bean,      4, 2, SEED)
        semer_fondateur(tile, Sunflower, 0, 1, SEED)
        semer_fondateur(tile, Pepper,    4, 6, SEED)
        if i % 2 == 0:  # attire-auxiliaires sur les tuiles paires
            semer_fondateur(tile, Yarrow,   3, 5, SEED)
            semer_fondateur(tile, Phacelia, 1, 6, SEED)
            semer_fondateur(tile, Clover,   5, 4, SEED)
        tiles.append(tile)
        ecos[tid] = eco
    # Pommier sur la tuile 0 (exerce les pérennes : dormance hivernale, age_curve)
    semer_fondateur(tiles[0], AppleTree, 0, 7, SEED)
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
        "house": House(),   # maison centrée par défaut → ombre/albédo (tronçon 2)
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
