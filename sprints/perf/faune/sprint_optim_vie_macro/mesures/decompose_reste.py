"""D100 — décomposition de `reste` (= tick − pop − light) sur banc dense(117).

Lecture seule. Ne modifie aucun moteur. Répond à la correction Nico (2026-08-01) :
« reste = 355 ms = 67 % du tick, jamais décomposé ; mon 'uptake/croissance/décompo'
était une supposition, pas une mesure ». Ici on lit le cProfile déjà en main.

Deux vues NON redondantes :
  (A) cumtime des phases NOMMÉES appelées par tick_semaine (avec overlap possible) ;
  (B) top self-time (tottime) — SOMME EXACTE au total, aucun double comptage :
      c'est la vue qui dit vraiment où part le temps.

Usage : PYTHONPATH=data/code python3 <ce script>   (depuis data/code/)
"""
import cProfile, pstats
from sim.engine import Engine
from world.building import House
from plafond_d100 import build_dense  # réutilise le banc dense(n) déjà écrit


def engine_of(tiles, ecos):
    return Engine({"tiles": tiles, "eco": ecos, "scores": {}, "current_player": "j",
                   "week": 1, "log": [], "house": House(), "seed": 12345})


# phases nommées appelées (in)directement par tick_semaine (boucle.py) — vue (A)
PHASES = [
    ("tick_light", "light"), ("tick_populations", "vie_macro"),
    ("grow_plant", "growth"), ("_apply_uptake", None), ("_update_physiology", None),
    ("resolve_plant_turn", "effects"), ("apply_disturbances", "effects"),
    ("succession", "succession"), ("tick_seed_bank", None),
    ("tick_decomposition", None), ("tick_diffusion", None),
    ("tick_lifecycle_bridges", "vie_macro"), ("_reproduction", None),
    ("tick_hydrology", None), ("tick_structure", None), ("tick_ph", None),
    ("tick_mycelium", None), ("tick_allelopathie", None), ("tick_couverture", None),
    ("tick_abri", None), ("tick_thermique", None), ("tick_rosee", None),
    ("_avancer_stades", None), ("_tick_senescence_health", None),
    ("_wind_damage", None), ("_tick_floraison", None), ("_apply_exudates", None),
]


def analyse(label, tiles, ecos, warm=40, M=52):
    eng = engine_of(tiles, ecos)
    for _ in range(warm):
        eng.tick_semaine()
    n_plants = sum(len(t.plants) for t in tiles)
    n_plots = sum(e.rows * e.cols for e in ecos.values())
    pr = cProfile.Profile(); pr.enable()
    for _ in range(M):
        eng.tick_semaine()
    pr.disable()
    st = pstats.Stats(pr); total = st.total_tt

    # index : (fname, file) -> (nc, cum, self)
    pop = light = 0.0
    by_fname = {}
    for (fn, ln, fname), (cc, nc, tt, ct, cs) in st.stats.items():
        by_fname.setdefault(fname, []).append((fn, ln, nc, ct, tt))
        if fname == "tick_populations" and "vie_macro" in fn: pop = ct
        if fname == "compute" and "light" in fn: light = ct
    # tick_light passe par compute() de light.py — on prend compute comme proxy light
    reste = total - pop - light

    print(f"\n===== {label} : {n_plots} plots, {n_plants} plantes, {M} ticks (warm {warm}) =====")
    print(f"  total  {total/M*1000:7.1f} ms/tick")
    print(f"  pop    {pop/M*1000:7.1f} ms/tick  ({100*pop/total:4.1f}%)")
    print(f"  light  {light/M*1000:7.1f} ms/tick  ({100*light/total:4.1f}%)")
    print(f"  RESTE  {reste/M*1000:7.1f} ms/tick  ({100*reste/total:4.1f}%)  <-- à ouvrir")

    print("\n  --- (A) phases NOMMÉES par cumtime (overlap possible, indicatif) ---")
    rows = []
    for name, filesub in PHASES:
        for fn, ln, nc, ct, tt in by_fname.get(name, []):
            if filesub and filesub not in fn:
                continue
            rows.append((ct, name, fn.split('/')[-1], nc, tt))
    for ct, name, fl, nc, tt in sorted(rows, reverse=True):
        tag = "" if name in ("tick_light", "tick_populations") else "  [reste]"
        print(f"    {name:24s} {fl:16s} cum={ct/M*1000:7.2f} ms/tick "
              f"({100*ct/total:4.1f}%) self={tt/M*1000:6.2f}{tag}")

    print("\n  --- (B) top self-time (tottime — somme EXACTE au total) ---")
    flat = []
    for (fn, ln, fname), (cc, nc, tt, ct, cs) in st.stats.items():
        flat.append((tt, fname, fn.split('/')[-1], ln, nc))
    tot_self = sum(x[0] for x in flat)
    for tt, fname, fl, ln, nc in sorted(flat, reverse=True)[:25]:
        print(f"    {tt/M*1000:7.2f} ms/tick ({100*tt/tot_self:4.1f}%)  "
              f"{fname:28s} {fl}:{ln}")


if __name__ == "__main__":
    dt, de = build_dense(117)
    analyse("DENSE(117)", dt, de)
