"""D100 — PLAFOND de gain, dérivé du cProfile (addition sur mesures faites, 0 modif moteur).
Pour chaque grille appelée avec des ARGS IDENTIQUES n fois/tuile, le récupérable par
mémoïsation = cum × (n-1)/n. On somme, on exprime en ms/tick et en % de pop et du tick.
Scénarios : golden (2 tuiles/96 plots) + tuile dense 117 plantes/144 plots.
"""
import cProfile, pstats
from sim.engine import Engine
from world.building import House
from plants.catalogue import PLANT_CATALOGUE
from world import Tile
from fields import init_eco

# Grilles appelées avec args IDENTIQUES (dédup nette). Clé = (fichier_suffix, funcname).
# Les closures nectar (registry:326, 5 attractivités DIFFÉRENTES) et espece/paillage
# (args différents) NE sont PAS dans ce set net — traitées à part.
IDENTIQUES = [  # (funcname, filesub)  -- tous appelés avec les mêmes args → dédup (n-1)/n
    ("_litter_grid", "resources"), ("_undisturbed_grid", "resources"),
    ("_pollinisateur_habitat_grid", "resources"), ("_foliage_grid", "resources"),
    ("_humide_litiere_grid", "resources"), ("_soil_food_grid", "resources"),
    ("_mare_habitat_grid", "resources"), ("_monoculture_grid", "resources"),
]


def engine_of(tiles, ecos):
    return Engine({"tiles": tiles, "eco": ecos, "scores": {}, "current_player": "j",
                   "week": 1, "log": [], "house": House(), "seed": 12345})


def build_dense(n):
    R = C = 12
    tile = Tile(tile_id=f"D{n}", soil_type="terre", grid_rows=R, grid_cols=C)
    eco = init_eco(tile.tile_id, R, C, humidite=1.6, fertilite=1.3, microbiome=0.7,
                   soil_type="terre", heterogene=True)
    eco.lumiere.fill(1.0)
    esp = [PLANT_CATALOGUE[k] for k in ("trefle","courgette","tournesol","haricot","violette")]
    i = 0
    for r in range(R):
        for c in range(C):
            if i >= n: break
            tile.add_plant(esp[i % len(esp)], r, c); i += 1
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    for s in tile.stakes:
        while s.add("paillage"): pass
    return [tile], {tile.tile_id: eco}


def analyse(label, tiles, ecos, n_tiles, warm=40, M=52):
    eng = engine_of(tiles, ecos)
    for _ in range(warm): eng.tick_semaine()
    pr = cProfile.Profile(); pr.enable()
    for _ in range(M): eng.tick_semaine()
    pr.disable()
    st = pstats.Stats(pr); total = st.total_tt
    idx = {}
    pop_cum = light_cum = atplot_self = zero_cum = nectar_cum = 0.0
    nectar_nc = 0
    for (fn, ln, fname), (cc, nc, tt, ct, cs) in st.stats.items():
        idx[(fname, fn.split('/')[-1].replace('.py',''))] = (nc, ct, tt)
        if fname == "tick_populations" and "vie_macro" in fn: pop_cum = ct
        if fname == "compute" and "light" in fn: light_cum = ct
        if fname == "at_plot" and "grids" in fn: atplot_self = tt
        if fname == "_zero_grid": zero_cum += tt
        if fname == "_grid" and "registry" in fn:  # closure nectar (5 attractivités)
            nectar_cum = tt; nectar_nc = nc
    print(f"\n===== {label} =====  total {total/M*1000:.1f} ms/tick "
          f"| pop {pop_cum/M*1000:.1f} ms | light {light_cum/M*1000:.1f} ms")
    recup = 0.0
    print(f"  {'grille (args identiques)':30s} {'n/tuile':>7} {'cum ms/tick':>11} {'récup ms/tick':>13}")
    for fname, filesub in IDENTIQUES:
        key = (fname, filesub)
        if key not in idx: continue
        nc, ct, tt = idx[key]
        n_pt = nc / M / n_tiles
        if n_pt <= 1.001: continue
        r = ct * (n_pt - 1) / n_pt
        recup += r
        print(f"  {fname:30s} {n_pt:>7.1f} {ct/M*1000:>11.2f} {r/M*1000:>13.2f}")
    # nectar : scan plantes partagé (CEILING = (n-1)/n de la self, borne haute car grilles diffèrent)
    nectar_recup_ceiling = nectar_cum * (nectar_nc/M/n_tiles - 1) / (nectar_nc/M/n_tiles) if nectar_nc else 0.0
    print(f"  {'[nectar scan, PLAFOND]':30s} {nectar_nc/M/n_tiles:>7.1f} {nectar_cum/M*1000:>11.2f} "
          f"{nectar_recup_ceiling/M*1000:>13.2f}  (borne haute : grilles diffèrent)")
    print(f"  --- récupérable grilles identiques : {recup/M*1000:6.2f} ms/tick "
          f"({100*recup/pop_cum:4.1f}% de pop, {100*recup/total:4.1f}% du tick)")
    print(f"  --- + nectar (plafond)             : {(recup+nectar_recup_ceiling)/M*1000:6.2f} ms/tick "
          f"({100*(recup+nectar_recup_ceiling)/pop_cum:4.1f}% de pop)")
    print(f"  --- at_plot self (accès direct, TOUT le moteur) : {atplot_self/M*1000:.2f} ms/tick "
          f"({100*atplot_self/total:.1f}% du tick) — fraction dans pop non isolée")
    print(f"  --- _zero_grid churn : {zero_cum/M*1000:.2f} ms/tick")


if __name__ == "__main__":
    from tests.test_golden import build_world
    gt, ge = build_world()
    analyse("GOLDEN (2 tuiles/96 plots)", gt, ge, n_tiles=2)
    dt, de = build_dense(117)
    analyse("DENSE 117 plantes/144 plots", dt, de, n_tiles=1)
