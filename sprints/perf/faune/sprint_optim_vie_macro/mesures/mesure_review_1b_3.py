"""Réponses aux dettes 1b et 3 de la revue (2026-08-02).

1b — COURBE light À SURFACE FIXE = taille de tuile RÉELLE du jeu.
   Le monde réel (main.py SECTORS) n'a PAS de tuile 144 : 4 tuiles 11×11=121 et
   4 tuiles 11×16 / 16×11 = 176 (non uniforme). On fixe la surface au PIRE CAS
   réel (176 plots = 16×11) et on fait varier N sur la plage de densité jouable
   (jusqu'à saturation ~0,79 → ~140 plantes). Exposant ajusté = pente log-log.

3  — DETTE 3 : rejouer k=1 et k=9 SEULEMENT, 3× chacun, rendre min/médiane/max
   du tick (et tick/k). Même protocole cProfile que measure_nmax.py (comparable
   aux 501·532·513·501·519 du carnet).

Usage : PYTHONPATH=data/code python3 <ce script>   (depuis data/code/)
"""
import cProfile, pstats, math, statistics
from sim.engine import Engine
from world.building import House
from plants.catalogue import PLANT_CATALOGUE
from world import Tile
from fields import init_eco

ESP = ("trefle", "courgette", "tournesol", "haricot", "violette")


def make_tile(tile_id, rows, cols, n):
    """Tuile rows×cols avec n plantes (1/plot), germination coupée, paillage plein."""
    tile = Tile(tile_id=tile_id, soil_type="terre", grid_rows=rows, grid_cols=cols)
    eco = init_eco(tile_id, rows, cols, humidite=1.6, fertilite=1.3, microbiome=0.7,
                   soil_type="terre", heterogene=True)
    eco.lumiere.fill(1.0)
    esp = [PLANT_CATALOGUE[k] for k in ESP]
    i = 0
    for r in range(rows):
        for c in range(cols):
            if i >= n:
                break
            tile.add_plant(esp[i % len(esp)], r, c); i += 1
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    for s in tile.stakes:
        while s.add("paillage"):
            pass
    return tile, eco


def engine_of(tiles, ecos):
    return Engine({"tiles": tiles, "eco": ecos, "scores": {}, "current_player": "j",
                   "week": 1, "log": [], "house": House(), "seed": 12345})


def measure(tiles, ecos, warm=20, M=20):
    """Retourne (tick_ms, light_ms, pop_ms, n_plants) — cProfile, comme measure_nmax."""
    eng = engine_of(tiles, ecos)
    for _ in range(warm):
        eng.tick_semaine()
    n_plants = sum(sum(1 for p in t.plants if p.is_alive) for t in tiles)
    pr = cProfile.Profile(); pr.enable()
    for _ in range(M):
        eng.tick_semaine()
    pr.disable()
    st = pstats.Stats(pr); total = st.total_tt
    pop = light = 0.0
    for (fn, ln, fname), (cc, nc, tt, ct, cs) in st.stats.items():
        if fname == "tick_populations" and "vie_macro" in fn: pop = ct
        if fname == "compute" and "light" in fn: light = ct
    f = 1000.0 / M
    return total * f, light * f, pop * f, n_plants


if __name__ == "__main__":
    # ================= 1b — surface FIXE = tuile réelle worst case 16×11=176 =====
    ROWS, COLS = 16, 11           # = 176 plots (plus grande tuile réelle, SECTORS)
    print(f"\n===== (1b) SURFACE FIXE = {ROWS}×{COLS} = {ROWS*COLS} plots (pire cas réel) =====")
    print("     N croissant à surface constante = le régime où l'O(N²) mord")
    pts = []
    for n in (20, 50, 80, 110, 140):
        t, e = make_tile("FIX", ROWS, COLS, n)
        tick, light, pop, npl = measure([t], {"FIX": e})
        print(f"  N={n:>3} (vivantes={npl:>3}) | tick={tick:7.1f}  light={light:6.1f}  pop={pop:6.1f} ms")
        pts.append((npl, light))
    # exposant ajusté = pente de la régression log-log light ~ N^alpha
    xs = [math.log(n) for n, _ in pts]
    ys = [math.log(l) for _, l in pts]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    alpha = sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / sum((x-mx)**2 for x in xs)
    print(f"  → EXPOSANT AJUSTÉ (log-log, {len(pts)} points) : light ~ N^{alpha:.2f}")
    print(f"    CAVEAT : surface fixe → light = baseline_∝plots (const) + terme_∝N ;")
    print(f"    la baseline constante TIRE la pente vers le BAS (sous-estime l'exposant du terme variable).")

    # ================= 3 — k=1 et k=9, 3× chacun, min/médiane/max ================
    print("\n===== (3) DETTE 3 — k=1 et k=9, 3 runs chacun (tuile 12×12 comme carnet) =====")
    for k in (1, 9):
        ticks = []
        for rep in range(3):
            tiles, ecos = [], {}
            for ti in range(k):
                tid = f"W{ti}"
                tt, ee = make_tile(tid, 12, 12, 144)
                tiles.append(tt); ecos[tid] = ee
            tick, light, pop, npl = measure(tiles, ecos)
            ticks.append(tick)
            print(f"  k={k} run{rep+1} : tick={tick:7.1f} ms  (tick/k={tick/k:6.1f})  plantes={npl}")
        lo, md, hi = min(ticks), statistics.median(ticks), max(ticks)
        print(f"  k={k} → tick   min={lo:7.1f}  méd={md:7.1f}  max={hi:7.1f}  (étendue {100*(hi-lo)/md:.1f} %)")
        print(f"  k={k} → tick/k min={lo/k:7.1f}  méd={md/k:7.1f}  max={hi/k:7.1f}")
