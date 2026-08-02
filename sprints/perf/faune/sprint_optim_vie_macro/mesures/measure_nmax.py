"""D100/D32 — MESURE à l'échelle N_max (jardin de fin de partie), pas d'extrapolation.

Recadrage Nico (2026-08-01) : le but du jeu = luxuriance maximale = toutes les
tuiles pleines. N_max = plots plantables × densité de saturation. Dérivé du moteur :
  - monde plantable [0, MONDE_CM=2000]² = 40×40 = 1600 plots (peripherie.py) ;
  - maison 800×800 cm = 16×16 = 256 plots non plantables (building.py) ;
  - périphérie (bande 900 cm) = DEHORS le jardin → ne retire rien ;
  - plots plantables ≈ 1600 − 256 = 1344 (hors chemins 50 cm, non chiffrés) ;
  - saturation [LU dans capacite.py, NON RE-VÉRIFIÉ] ≈ 0,83 pl/plot (petite tuile 11×11,
    plateau ~100-105/121 annoncé dans un COMMENTAIRE) à 0,68 (grande) — chiffre à re-mesurer
    (laisser une tuile se remplir germination ON, compter le plateau) avant de le graver ;
  - ⇒ N_max ≈ 900–1115 plantes, ordre de grandeur ~1000 (conditionné au chiffre ci-dessus).

FAIT ARCHITECTURAL à trancher par la mesure : `eco.tick_light(tile.plants, …)` est
appelé PAR TUILE (boucle.py:205), chaque tuile a son propre LightField → le terme
O(N²) porte sur les plantes d'UNE tuile (bornée ~200 plateau / 800 disjoncteur),
PAS du monde entier. Si vrai, le tick du monde est ~LINÉAIRE en nombre de tuiles.

Deux mesures :
  (A) MONDE multi-tuiles : k tuiles 12×12 pleines (144 pl/tuile) → total jusqu'à ~N_max.
      Si le tick croît linéairement en k, l'O(N²) est bien borné par tuile.
  (B) TUILE-UNIQUE géante : une seule tuile jusqu'à ~800 plantes (pire cas per-tile O(N²)),
      pour voir la vraie courbe O(N²) intra-tuile là où elle mord.

Usage : PYTHONPATH=data/code python3 <ce script>   (depuis data/code/)
"""
import cProfile, pstats, math
from sim.engine import Engine
from world.building import House
from plants.catalogue import PLANT_CATALOGUE
from world import Tile
from fields import init_eco

ESP = ("trefle", "courgette", "tournesol", "haricot", "violette")


def make_tile(tile_id, rc, n, ox=0.0, oy=0.0):
    """Une tuile rc×rc avec n plantes (1/plot), germination coupée, paillage plein."""
    tile = Tile(tile_id=tile_id, soil_type="terre", grid_rows=rc, grid_cols=rc)
    eco = init_eco(tile_id, rc, rc, humidite=1.6, fertilite=1.3, microbiome=0.7,
                   soil_type="terre", heterogene=True)
    eco.lumiere.fill(1.0)
    esp = [PLANT_CATALOGUE[k] for k in ESP]
    i = 0
    for r in range(rc):
        for c in range(rc):
            if i >= n:
                break
            tile.add_plant(esp[i % len(esp)], r, c); i += 1
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    for s in tile.stakes:
        while s.add("paillage"):
            pass
    return tile, eco


def build_world(k_tiles, per_tile, rc=12):
    tiles, ecos = [], {}
    for t in range(k_tiles):
        tid = f"W{t}"
        # offsets monde distincts (léger, sans importance pour un light per-tuile)
        tile, eco = make_tile(tid, rc, per_tile, ox=t * rc * 50.0, oy=0.0)
        tiles.append(tile); ecos[tid] = eco
    return tiles, ecos


def build_big_tile(n):
    rc = math.ceil(math.sqrt(n))
    return build_world_from([make_tile("BIG", rc, n)])


def build_world_from(tile_eco_pairs):
    tiles = [t for t, _ in tile_eco_pairs]
    ecos = {t.tile_id: e for t, e in tile_eco_pairs}
    return tiles, ecos


def engine_of(tiles, ecos):
    return Engine({"tiles": tiles, "eco": ecos, "scores": {}, "current_player": "j",
                   "week": 1, "log": [], "house": House(), "seed": 12345})


def measure(label, tiles, ecos, warm=20, M=30):
    eng = engine_of(tiles, ecos)
    for _ in range(warm):
        eng.tick_semaine()
    n_plants = sum(sum(1 for p in t.plants if p.is_alive) for t in tiles)
    n_plots = sum(e.rows * e.cols for e in ecos.values())
    pr = cProfile.Profile(); pr.enable()
    for _ in range(M):
        eng.tick_semaine()
    pr.disable()
    st = pstats.Stats(pr); total = st.total_tt
    pop = light = 0.0
    for (fn, ln, fname), (cc, nc, tt, ct, cs) in st.stats.items():
        if fname == "tick_populations" and "vie_macro" in fn: pop = ct
        if fname == "compute" and "light" in fn: light = ct
    reste = total - pop - light
    f = 1000.0 / M
    print(f"  {label:22s} tuiles={len(tiles):>2} plots={n_plots:>5} plantes={n_plants:>5} | "
          f"tick={total*f:7.1f}  light={light*f:7.1f}  pop={pop*f:6.1f}  reste={reste*f:7.1f} ms/tick")
    return total * f


if __name__ == "__main__":
    print("\n===== (A) MONDE multi-tuiles (12×12 pleines, 144 pl/tuile) =====")
    print("     si tick ∝ k (linéaire), l'O(N²) light est borné PAR TUILE, pas par le monde")
    for k in (1, 2, 4, 8, 9):
        t, e = build_world(k, 144, rc=12)
        measure(f"monde k={k}", t, e)

    print("\n===== (B) TUILE-UNIQUE géante (pire cas O(N²) intra-tuile) =====")
    print("     jusqu'où build_dense monte : une seule tuile, n plantes, rc=ceil(√n)")
    for n in (144, 256, 400, 600, 800):
        t, e = build_big_tile(n)
        measure(f"1 tuile n={n}", t, e)
