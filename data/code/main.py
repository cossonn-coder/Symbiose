"""
SYMBIOSE — main.py
Scénario de test MULTI-TUILES : monde 3×3 (9 tuiles × 6×8 plots = 432 plots),
sols contrastés. La moitié des tuiles (index pair) reçoit des plantes compagnes
ATTIRE-AUXILIAIRES (achillée, phacélie) qui posent la rondelle `auxiliaire` →
renforcent la régulation des ravageurs (M6). Les tuiles témoins (index impair)
n'en ont pas. On observe ainsi le contraste de régulation, la succession et la
sénescence (un pommier sur la tuile centrale) sur la durée.
"""

import sys
from collections import Counter
from world import Tile
from plants import (Tomato, Basil, Sunflower, Bean, Clover, Pepper,
                    Yarrow, Phacelia, AppleTree)
from fields import init_eco, inject_patch
from sim.engine import Engine

# 9 tuiles, sols contrastés (sable = pauvre/sec, argile = humide, terre = standard)
SOILS = ["terre", "argile", "sable",
         "terre", "terre",  "sable",
         "argile", "terre", "sable"]


def build_tile(idx: int, soil: str):
    tid = f"T{idx}"
    tile = Tile(tile_id=tid, soil_type=soil)
    if soil == "sable":
        eco = init_eco(tid, 6, 8, humidite=1.0, fertilite=0.6, microbiome=0.2)
    elif soil == "argile":
        eco = init_eco(tid, 6, 8, humidite=2.0, fertilite=1.2, microbiome=0.3)
    else:
        eco = init_eco(tid, 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
    return tile, eco


def plant_garden(tile, with_auxiliaries: bool):
    """Jardin diversifié de base ; +attire-auxiliaires si demandé."""
    tile.add_plant(Tomato,    2, 2)
    tile.add_plant(Basil,     2, 4)
    tile.add_plant(Bean,      4, 2)
    tile.add_plant(Sunflower, 0, 1)
    tile.add_plant(Pepper,    4, 6)
    if with_auxiliaries:
        tile.add_plant(Yarrow,   3, 5)   # achillée (vivace attire-auxiliaires)
        tile.add_plant(Phacelia, 1, 6)   # phacélie (annuelle attire-auxiliaires)
        tile.add_plant(Clover,   5, 4)


tiles = []
ecos = {}
aux_tiles = set()
for i, soil in enumerate(SOILS):
    tile, eco = build_tile(i, soil)
    with_aux = (i % 2 == 0)
    plant_garden(tile, with_aux)
    if with_aux:
        aux_tiles.add(tile.tile_id)
    tiles.append(tile)
    ecos[tile.tile_id] = eco

# Pommier sur la tuile centrale (T4), en coin — observer la sénescence (~70 ans).
tiles[4].add_plant(AppleTree, 0, 7)

game_state = {
    "tiles": tiles,
    "eco":   ecos,
    "scores": {},
    "current_player": "joueur_1",
    "week": 1,
    "log":  [],
}

print("╔══════════════════════════════════════════════════════╗")
print("║   SYMBIOSE — Simulation monde 3×3 (9 tuiles)         ║")
print("║   Attire-auxiliaires (achillée/phacélie) vs témoins  ║")
print("╚══════════════════════════════════════════════════════╝")
print(f"Tuiles attire-auxiliaires : {sorted(aux_tiles)}")
print(f"Tuiles témoins            : {sorted(t.tile_id for t in tiles if t.tile_id not in aux_tiles)}")

engine = Engine(game_state)


def composition(tiles) -> Counter:
    """Couvert vivant agrégé sur toutes les tuiles, par archétype."""
    c = Counter()
    for tile in tiles:
        for p in tile.plants:
            if p.is_alive:
                c[getattr(p.plant_class, "archetype", None) or "cultivée"] += 1
    return c


def aux_rondelles(tiles, group) -> float:
    """Moyenne de rondelles `auxiliaire` sur un groupe de tuiles."""
    sel = [t for t in tiles if t.tile_id in group]
    if not sel:
        return 0.0
    return sum(t.get_rondelle_count("auxiliaire") for t in sel) / len(sel)


# Nombre d'années : 1er argument CLI, sinon 30 (9 tuiles = lourd ; le coût/an
# grimpe avec le nombre de plantes). Pour la maturité de succession ou la
# sénescence du pommier (~70 ans), lancer « python3 main.py 200 ».
N_YEARS    = int(sys.argv[1]) if len(sys.argv) > 1 else 30
SNAP_EVERY = 10
SNAP_WEEK  = 26    # plein été — couvert maximal

control_tiles = {t.tile_id for t in tiles} - aux_tiles

print("\nTRAJECTOIRE — couvert vivant agrégé (S26) + rondelles auxiliaire moyennes")
print(f"{'année':>6} {'pion':>5} {'fixe':>5} {'gram':>5} {'comp':>5} {'cult':>5} "
      f"{'%viv':>5} {'aux+':>5} {'aux0':>5}")
for y in range(1, N_YEARS + 1):
    for _ in range(52):
        wiy = ((engine.week - 1) % 52) + 1
        engine.tick_semaine()
        if wiy == SNAP_WEEK and (y == 1 or y == N_YEARS or y % SNAP_EVERY == 0):
            c = composition(tiles)
            pion = c["pioneer"]; fix = c["nitrogen_fixer"]
            gra  = c["grass"];   comp = c["competitor"]; cult = c["cultivée"]
            viv  = fix + gra + comp
            spont = pion + viv
            pct  = 100.0 * viv / spont if spont else 0.0
            a_plus = aux_rondelles(tiles, aux_tiles)
            a_zero = aux_rondelles(tiles, control_tiles)
            print(f"{y:>6} {pion:>5} {fix:>5} {gra:>5} {comp:>5} {cult:>5} "
                  f"{pct:>4.0f}% {a_plus:>5.1f} {a_zero:>5.1f}")
    engine.game_state["log"].clear()

# --- Résumé final ---
print("\n" + "═"*60)
print("RÉSUMÉ FINAL — par tuile")
print("═"*60)
print(f"{'tuile':>6} {'sol':>7} {'aux?':>5} {'vivantes':>9} "
      f"{'aux●':>5} {'pollin●':>8} {'vitalité':>9}")
for tile in tiles:
    eco = ecos[tile.tile_id]
    alive = sum(1 for p in tile.plants if p.is_alive)
    is_aux = "oui" if tile.tile_id in aux_tiles else "—"
    auxr = tile.get_rondelle_count("auxiliaire")
    polr = tile.get_rondelle_count("pollinisateur")
    print(f"{tile.tile_id:>6} {tile.soil_type:>7} {is_aux:>5} {alive:>9} "
          f"{auxr:>5} {polr:>8} {eco.vitalite_average():>9.3f}")

# Moyennes par groupe (montre l'effet attire-auxiliaires)
def group_avg(group, fn):
    sel = [t for t in tiles if t.tile_id in group]
    return sum(fn(t) for t in sel) / len(sel) if sel else 0.0

print("\nContraste attire-auxiliaires vs témoins (moyennes par tuile) :")
for label, group in [("attire-aux", aux_tiles), ("témoins   ", control_tiles)]:
    auxr = group_avg(group, lambda t: t.get_rondelle_count("auxiliaire"))
    vit  = group_avg(group, lambda t: ecos[t.tile_id].vitalite_average())
    alive = group_avg(group, lambda t: sum(1 for p in t.plants if p.is_alive))
    print(f"  {label} : auxiliaire●={auxr:.1f}  vitalité={vit:.3f}  vivantes={alive:.1f}")

scores = game_state.get("scores", {})
if scores:
    print("\nScores finaux :")
    for pid, sc in scores.items():
        total = sum(sc.values())
        print(f"  {pid} — récolte:{sc.get('recolte',0)} "
              f"luxuriance:{sc.get('luxuriance',0)} "
              f"biodiversité:{sc.get('biodiversite',0)} TOTAL:{total}")
