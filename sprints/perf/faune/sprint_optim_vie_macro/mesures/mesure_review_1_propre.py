"""Dette 1 (revue 2026-08-02, 2e passe) — α propre, contamination de charge écartée.

Faute corrigée : B et C ont tourné en tâche de fond SIMULTANÉMENT → les ms de B ont été
prises pendant que C montait en charge, dans l'ordre CROISSANT de N → dérive monotone
confondue avec la pente. Ici : machine AU REPOS, RIEN d'autre en vol, et ORDRE ALTERNÉ
(35, 284, 35, 284…) pour décorréler toute dérive résiduelle de l'ordre de N.

(a) N=35 et N=284 (vivantes) uniquement, 3× chacun, alterné → dispersion inter-run vs
    écart de pente. (b) α sur points ≤176 (régime réel, empilement exclu) vs α global
    (inclut les points empilés 1,1-1,6 pl/plot que le jeu ne produit jamais).

Usage : PYTHONPATH=data/code python3 -u <ce script>   (depuis data/code/, SEUL)
"""
import cProfile, pstats, math, statistics
from sim.engine import Engine
from world.building import House
from plants.catalogue import PLANT_CATALOGUE
from world import Tile
from fields import init_eco

ESP = ("trefle", "courgette", "tournesol", "haricot", "violette")
ROWS, COLS = 16, 11
PLOTS = ROWS * COLS


def make_tile(n):
    tile = Tile(tile_id="FIX", soil_type="terre", grid_rows=ROWS, grid_cols=COLS)
    eco = init_eco("FIX", ROWS, COLS, humidite=1.6, fertilite=1.3, microbiome=0.7,
                   soil_type="terre", heterogene=True)
    eco.lumiere.fill(1.0)
    esp = [PLANT_CATALOGUE[k] for k in ESP]
    for i in range(n):
        tile.add_plant(esp[i % len(esp)], (i // COLS) % ROWS, i % COLS)
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    for s in tile.stakes:
        while s.add("paillage"):
            pass
    return tile, eco


def light_ms(n, warm=20, M=20):
    tile, eco = make_tile(n)
    eng = Engine({"tiles": [tile], "eco": {"FIX": eco}, "scores": {}, "current_player": "j",
                  "week": 1, "log": [], "house": House(), "seed": 12345})
    for _ in range(warm):
        eng.tick_semaine()
    npl = sum(1 for p in tile.plants if p.is_alive)
    pr = cProfile.Profile(); pr.enable()
    for _ in range(M):
        eng.tick_semaine()
    pr.disable()
    st = pstats.Stats(pr)
    light = 0.0
    for (fn, ln, fname), (cc, nc, tt, ct, cs) in st.stats.items():
        if fname == "compute" and "light" in fn: light = ct
    return light * 1000.0 / M, npl


if __name__ == "__main__":
    # (a) ORDRE ALTERNÉ, n_dem 20 → ~35 vivantes, 280 → ~284
    print("# (a) N=35 / N=284, 3× alterné, machine au repos")
    order = [20, 280, 20, 280, 20, 280]
    res = {20: [], 280: []}
    npl_of = {}
    for n in order:
        L, npl = light_ms(n)
        res[n].append(L); npl_of[n] = npl
        print(f"  n_dem={n:>3} (vivantes={npl:>3}) : light={L:6.1f} ms")
    for n in (20, 280):
        v = res[n]
        print(f"  → N={npl_of[n]:>3} : light min={min(v):.1f} méd={statistics.median(v):.1f} "
              f"max={max(v):.1f}  (étendue {100*(max(v)-min(v))/statistics.median(v):.1f} %)")

    # pente entre médianes + bornes par dispersion inter-run
    x1, x2 = math.log(npl_of[20]), math.log(npl_of[280])
    m1, m2 = statistics.median(res[20]), statistics.median(res[280])
    a_med = (math.log(m2) - math.log(m1)) / (x2 - x1)
    # pente la plus PLATE (max bas / min haut) et la plus RAIDE (min bas / max haut)
    a_flat = (math.log(min(res[280])) - math.log(max(res[20]))) / (x2 - x1)
    a_steep = (math.log(max(res[280])) - math.log(min(res[20]))) / (x2 - x1)
    print(f"  → α (2 points, médianes) = {a_med:.2f} ; enveloppe dispersion [{a_flat:.2f} , {a_steep:.2f}]")

    # (b) α ≤176 (régime réel) vs α global — sur les données B existantes
    print("\n# (b) α régime réel (≤176 = ≤1 pl/plot) vs α global (inclut empilé 1,1-1,6)")
    B = [(35, 15.5), (58, 28.2), (102, 49.6), (151, 71.1), (211, 103.7), (284, 157.9)]
    def fit(pts):
        xs = [math.log(n) for n, _ in pts]; ys = [math.log(l) for _, l in pts]
        mx, my = statistics.mean(xs), statistics.mean(ys)
        return sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / sum((x-mx)**2 for x in xs)
    a_sub = fit([p for p in B if p[0] <= 176])
    a_all = fit(B)
    print(f"  α (≤176, {sum(1 for p in B if p[0]<=176)} pts, régime réel) = {a_sub:.2f}")
    print(f"  α (global, 6 pts, avec empilé)             = {a_all:.2f}")
    print(f"  écart = {abs(a_sub-a_all):.2f}")
