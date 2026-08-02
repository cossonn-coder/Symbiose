"""D100/D32 — RE-MESURE du plateau de saturation (#1 Nico, 2026-08-01).

Le chiffre « ~0,83 pl/plot » qui multiplie tout N_max venait d'un COMMENTAIRE de
capacite.py, jamais re-vérifié. Ici on le MESURE par commande : une tuile 11×11
(121 plots, comme le commentaire), germination + succession + reproduction ON, on
laisse le recrutement remplir et on compte les plantes VIVANTES chaque année (52
semaines) jusqu'au plateau (recrutement = mortalité).

Sortie annuelle, une ligne = un point (année, N vivantes, pl/plot). Arrêt anticipé
si plateau stable (±2 % sur 4 années) → économise le temps.

Usage : PYTHONPATH=data/code python3 -u mesure_saturation.py   (depuis data/code/)
"""
from sim.engine import Engine
from world.building import House
from plants.catalogue import PLANT_CATALOGUE
from world import Tile
from fields import init_eco

RC = 11            # tuile 11×11 = 121 plots (aligne le commentaire de capacite.py)
ANS = 30           # borne dure (52 sem/an) ; arrêt anticipé au plateau
FONDATRICES = ("trefle", "tournesol", "violette")


def build():
    tile = Tile(tile_id="SAT", soil_type="terre", grid_rows=RC, grid_cols=RC)
    eco = init_eco("SAT", RC, RC, humidite=1.6, fertilite=1.3, microbiome=0.7,
                   soil_type="terre", heterogene=True)
    eco.lumiere.fill(1.0)
    # quelques fondatrices espacées ; germination/reproduction NON coupées → recrutement libre
    esp = [PLANT_CATALOGUE[k] for k in FONDATRICES]
    for i, (r, c) in enumerate([(2, 2), (2, 8), (8, 2), (8, 8), (5, 5)]):
        tile.add_plant(esp[i % len(esp)], r, c)
    return [tile], {"SAT": eco}


def alive(tiles):
    return sum(sum(1 for p in t.plants if p.is_alive) for t in tiles)


if __name__ == "__main__":
    tiles, ecos = build()
    eng = Engine({"tiles": tiles, "eco": ecos, "scores": {}, "current_player": "j",
                  "week": 1, "log": [], "house": House(), "seed": 12345})
    plots = RC * RC
    print(f"# SATURATION — tuile {RC}x{RC} = {plots} plots, germination ON, seed 12345", flush=True)
    print(f"# {'annee':>5} {'N_vivantes':>11} {'pl/plot':>8}", flush=True)
    hist = []
    for an in range(1, ANS + 1):
        for _ in range(52):
            eng.tick_semaine()
        n = alive(tiles)
        hist.append(n)
        print(f"  {an:>5} {n:>11} {n/plots:>8.3f}", flush=True)
        # arrêt anticipé : plateau stable ±2 % sur 4 dernières années
        if len(hist) >= 4:
            w = hist[-4:]
            if max(w) - min(w) <= 0.02 * max(1, max(w)):
                print(f"# PLATEAU atteint an {an} : N≈{n} ({n/plots:.3f} pl/plot) "
                      f"[stable ±2% sur 4 ans]", flush=True)
                break
    else:
        print(f"# borne {ANS} ans atteinte sans plateau strict ; dernier N={hist[-1]} "
              f"({hist[-1]/plots:.3f} pl/plot)", flush=True)
    print(f"# FIN saturation. max observé = {max(hist)} ({max(hist)/plots:.3f} pl/plot)", flush=True)
