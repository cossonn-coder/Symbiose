"""D100 — tronçon ① MESURE PURE. Lecture seule, ne modifie aucun moteur.
Compare golden (clairsemé) vs luxuriance (dense) :
  (a) part %tick de tick_populations et tick_light
  (c) compte d'appels réel des grilles suspectes (cProfile ncalls)
Usage : python3 mesure_d100.py  (depuis data/code/, PYTHONPATH=data/code)
"""
import cProfile, pstats, io, sys
from sim.engine import Engine
from world.building import House


def build_golden():
    from tests.test_golden import build_world
    tiles, ecos = build_world()
    return tiles, ecos, House()


def build_lux():
    from bancs.luxuriance import luxuriance
    tiles, ecos, house, banque = luxuriance()
    return tiles, ecos, house


def make_engine(tiles, ecos, house):
    gs = {"tiles": tiles, "eco": ecos, "scores": {}, "current_player": "joueur_1",
          "week": 1, "log": [], "house": house}
    return Engine(gs)


def run(label, builder, warm, measured):
    tiles, ecos, house = builder()
    eng = make_engine(tiles, ecos, house)
    for _ in range(warm):
        eng.tick_semaine()
    n_plants = sum(len(t.plants) for t in tiles)
    n_plots = sum(e.rows * e.cols for e in ecos.values())
    pr = cProfile.Profile()
    pr.enable()
    for _ in range(measured):
        eng.tick_semaine()
    pr.disable()
    st = pstats.Stats(pr)
    total = st.total_tt
    # cumtime par fonction cible
    def find(name_substrs, filesub=None):
        hits = []
        for (fn, ln, fname), (cc, nc, tt, ct, cs) in st.stats.items():
            if any(s in fname for s in name_substrs) and (filesub is None or filesub in fn):
                hits.append((fname, fn.split('/')[-1], ln, nc, ct, tt))
        return hits
    print(f"\n===== {label} : {len(tiles)} tuile(s), {n_plots} plots, {n_plants} plantes, "
          f"{measured} ticks (warm {warm}) =====")
    print(f"  total mesuré : {total*1000:.1f} ms  ({total/measured*1000:.2f} ms/tick)")
    for fname, base in [("tick_populations", None), ("tick_light", None),
                        ("compute", "light"), ("tick_lifecycle_bridges", None)]:
        for f, fl, ln, nc, ct, tt in find([fname], base):
            if fl in ("field.py",):  # éviter les collisions PopulationField.tick
                continue
            print(f"  {fname:24s} {fl}:{ln:<4} ncalls={nc:<7} cum={ct*1000:8.1f}ms "
                  f"({100*ct/total:4.1f}%)  self={tt*1000:7.1f}ms")
    print("  --- ncalls des grilles suspectes (compte RÉEL sur ce run) ---")
    suspects = ["_litter_grid", "_undisturbed_grid", "_foliage_grid",
                "_pollinisateur_habitat_grid", "_make_nectar_grid",
                "_soil_food_grid", "_mare_habitat_grid", "_humide_litiere_grid",
                "_rosee_humide_litiere_grid", "_undisturbed_structure_grid",
                "_zero_grid", "at_plot"]
    for s in suspects:
        rows = find([s], "population") + (find([s], "grids") if s in ("_zero_grid", "at_plot") else [])
        for f, fl, ln, nc, ct, tt in sorted(rows, key=lambda x: -x[3]):
            per_tick = nc / measured
            print(f"    {s:28s} {fl}:{ln:<4} ncalls={nc:<8} (~{per_tick:6.1f}/tick) "
                  f"cum={ct*1000:7.1f}ms self={tt*1000:7.1f}ms")
    # closures _grid (espece/proies/nectar/paillage) par ligne
    print("  --- closures _grid (espece/proies/nectar/paillage/mycelium) ---")
    for f, fl, ln, nc, ct, tt in sorted(find(["_grid", "_signal"], "population"), key=lambda x: -x[3]):
        print(f"    {fl}:{ln:<4} {'_grid/_signal':16s} ncalls={nc:<8} (~{nc/measured:6.1f}/tick) "
              f"self={tt*1000:7.1f}ms")


if __name__ == "__main__":
    run("GOLDEN (clairsemé)", build_golden, warm=40, measured=52)
    run("LUXURIANCE (dense)", build_lux, warm=40, measured=52)
