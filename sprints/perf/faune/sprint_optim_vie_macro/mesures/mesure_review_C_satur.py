"""Dette C (revue 2026-08-02) — SATURATION sur GRANDE tuile réelle 16×11=176, 3 SEEDS.

Correctifs : (1) la densité de saturation a été mesurée sur 121 plots (petite tuile)
puis appliquée aux 4 tuiles de 176 — or capacite.py annonce une densité qui BAISSE
avec la surface (0,83 petite → 0,68 grande) ; on la mesure donc à 176.
(2) « effondrement an 26 pas du bruit car déterministe » confond déterminisme et
non-stochasticité : un tirage rare seedé est déterministe ET stochastique. Trois
seeds tranchent : si l'effondrement est structurel il tombe partout ; si c'est un
tirage rare, les dates diffèrent (ou aucun). On rend les 3 SÉRIES BRUTES + les dates.

Aucune moyenne présentée comme « la » saturation, aucun N_max recalculé ici.

Usage : PYTHONPATH=data/code python3 -u <ce script>   (depuis data/code/)
"""
from sim.engine import Engine
from world.building import House
from plants.catalogue import PLANT_CATALOGUE
from world import Tile
from fields import init_eco

ROWS, COLS = 16, 11          # 176 plots (grande tuile réelle, SECTORS)
PLOTS = ROWS * COLS
ANS = 30
FONDATRICES = ("trefle", "tournesol", "violette")
SEEDS = (12345, 271828, 987654)


def build(seed):
    tile = Tile(tile_id="SAT", soil_type="terre", grid_rows=ROWS, grid_cols=COLS)
    eco = init_eco("SAT", ROWS, COLS, humidite=1.6, fertilite=1.3, microbiome=0.7,
                   soil_type="terre", heterogene=True)
    eco.lumiere.fill(1.0)
    esp = [PLANT_CATALOGUE[k] for k in FONDATRICES]
    # 5 fondatrices espacées (échelle 16×11) — même densité de départ que la petite tuile
    for i, (r, c) in enumerate([(3, 2), (3, 8), (12, 2), (12, 8), (8, 5)]):
        tile.add_plant(esp[i % len(esp)], r, c)
    return [tile], {"SAT": eco}, Engine(
        {"tiles": [tile], "eco": {"SAT": eco}, "scores": {}, "current_player": "j",
         "week": 1, "log": [], "house": House(), "seed": seed})


def alive(tiles):
    return sum(sum(1 for p in t.plants if p.is_alive) for t in tiles)


if __name__ == "__main__":
    print(f"# SATURATION 3 SEEDS — tuile {ROWS}×{COLS} = {PLOTS} plots, germination ON", flush=True)
    for seed in SEEDS:
        tiles, ecos, eng = build(seed)
        print(f"\n# --- seed {seed} ---", flush=True)
        print(f"# {'annee':>5} {'N':>4} {'pl/plot':>8} {'yoy%':>7}", flush=True)
        hist = []
        chutes = []
        for an in range(1, ANS + 1):
            for _ in range(52):
                eng.tick_semaine()
            n = alive(tiles)
            yoy = 100.0 * (n - hist[-1]) / max(1, hist[-1]) if hist else 0.0
            flag = "  <<< CHUTE" if hist and yoy <= -25.0 else ""
            print(f"  {an:>5} {n:>4} {n/PLOTS:>8.3f} {yoy:>+7.1f}{flag}", flush=True)
            if hist and yoy <= -25.0:
                chutes.append((an, hist[-1], n, yoy))
            hist.append(n)
        mx = max(hist)
        print(f"# seed {seed} : max={mx} ({mx/PLOTS:.3f} pl/plot) ; "
              f"chutes≥25% aux années {[c[0] for c in chutes] or 'AUCUNE'}", flush=True)
    print("\n# FIN — 3 séries brutes ci-dessus. Pas de moyenne, pas de N_max recalculé.", flush=True)
