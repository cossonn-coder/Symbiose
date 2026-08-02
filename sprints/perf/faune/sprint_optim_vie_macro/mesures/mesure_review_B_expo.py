"""Dette B (revue 2026-08-02) — EXPOSANT de light à surface FIXE = tuile réelle 176,
avec BRAS DE LEVIER étendu au-delà de la saturation + intervalle sur alpha.

Correctif de 1b : borner l'ajustement à la plage jouable (~7× en N) rend alpha mal
déterminé. Ici on ÉTEND N franchement au-delà de la saturation (N>176 = plusieurs
plantes/plot, surpeuplement réel géré par detect_conflicts) pour donner du levier,
on ajuste la loi de puissance sur TOUTE la plage, on rapporte alpha AVEC son IC 95%,
puis on rend SÉPARÉMENT les ms sur la seule plage jouable (N ≤ ~140, ≤ 0,79 pl/plot).

Usage : PYTHONPATH=data/code python3 -u <ce script>   (depuis data/code/)
"""
import cProfile, pstats, math, statistics
from sim.engine import Engine
from world.building import House
from plants.catalogue import PLANT_CATALOGUE
from world import Tile
from fields import init_eco

ESP = ("trefle", "courgette", "tournesol", "haricot", "violette")
ROWS, COLS = 16, 11                      # = 176 plots (plus grande tuile réelle)
PLOTS = ROWS * COLS


def make_tile(tile_id, n):
    """Tuile 16×11 avec n plantes ROUND-ROBIN (n>176 → empile, surpeuplement réel)."""
    tile = Tile(tile_id=tile_id, soil_type="terre", grid_rows=ROWS, grid_cols=COLS)
    eco = init_eco(tile_id, ROWS, COLS, humidite=1.6, fertilite=1.3, microbiome=0.7,
                   soil_type="terre", heterogene=True)
    eco.lumiere.fill(1.0)
    esp = [PLANT_CATALOGUE[k] for k in ESP]
    for i in range(n):
        r = (i // COLS) % ROWS
        c = i % COLS
        tile.add_plant(esp[i % len(esp)], r, c)
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    for s in tile.stakes:
        while s.add("paillage"):
            pass
    return tile, eco


def measure(n, warm=20, M=20):
    tile, eco = make_tile("FIX", n)
    eng = Engine({"tiles": [tile], "eco": {"FIX": eco}, "scores": {}, "current_player": "j",
                  "week": 1, "log": [], "house": House(), "seed": 12345})
    for _ in range(warm):
        eng.tick_semaine()
    npl = sum(1 for p in tile.plants if p.is_alive)
    pr = cProfile.Profile(); pr.enable()
    for _ in range(M):
        eng.tick_semaine()
    pr.disable()
    st = pstats.Stats(pr); total = st.total_tt
    light = 0.0
    for (fn, ln, fname), (cc, nc, tt, ct, cs) in st.stats.items():
        if fname == "compute" and "light" in fn: light = ct
    f = 1000.0 / M
    return total * f, light * f, npl


if __name__ == "__main__":
    print(f"\n===== Dette B — surface FIXE {ROWS}×{COLS}={PLOTS} plots, N étendu au-delà saturation =====")
    print(f"     saturation ~0,79 → ~{int(0.79*PLOTS)} plantes ; on pousse jusqu'à {280} (>1,5 pl/plot)")
    pts = []          # (N_vivantes, light_ms, N_demande, pl/plot, tick_ms)
    for n in (20, 45, 90, 140, 200, 280):
        tick, light, npl = measure(n)
        dens = npl / PLOTS
        print(f"  N_dem={n:>3}  vivantes={npl:>3}  ({dens:.2f} pl/plot) | tick={tick:7.1f}  light={light:6.1f} ms")
        pts.append((npl, light, n, dens, tick))

    # --- ajustement log-log light ~ N^alpha sur TOUTE la plage + IC 95% ---
    xs = [math.log(p[0]) for p in pts]
    ys = [math.log(p[1]) for p in pts]
    nP = len(pts)
    mx, my = statistics.mean(xs), statistics.mean(ys)
    Sxx = sum((x-mx)**2 for x in xs)
    alpha = sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / Sxx
    b = my - alpha*mx
    resid = [y - (alpha*x + b) for x, y in zip(xs, ys)]
    s2 = sum(r*r for r in resid) / (nP - 2)          # variance résiduelle
    se = math.sqrt(s2 / Sxx)                          # erreur-type de la pente
    t = 2.776                                         # t(0.975, ddl=4) pour 6 points
    print(f"\n  → EXPOSANT (log-log, {nP} points, levier N {math.exp(min(xs)):.0f}→{math.exp(max(xs)):.0f}) :")
    print(f"    alpha = {alpha:.2f}  IC95% [{alpha-t*se:.2f} , {alpha+t*se:.2f}]  (SE={se:.3f})")

    # --- ms SÉPARÉES sur la seule plage JOUABLE (≤ ~0,79 pl/plot) ---
    print(f"\n  → ms sur la PLAGE JOUABLE seule (≤ 0,79 pl/plot) :")
    for npl, light, ndem, dens, tick in pts:
        if dens <= 0.80:
            print(f"    vivantes={npl:>3} ({dens:.2f} pl/plot) | tick={tick:7.1f}  light={light:6.1f} ms")
