"""D100 — tronçon mesure 2 (lecture seule, 0 modif moteur).
(1) DÉTERMINISME par commande : 2 runs identiques → diff de signature.
(2) COURBE densité→part : tick_populations% vs tick_light% à N plantes croissant.
(3) COÛT PEINTRE : temps de sérialisation des sprites (sample_sprites+cap) par snapshot,
    et nb de sprites vs nb de (tuile,type) présents (= cible D2 1/type/tuile).
Usage : PYTHONPATH=data/code python3 mesure_d100b.py  (depuis data/code/)
"""
import cProfile, pstats, time, hashlib
from sim.engine import Engine
from world.building import House
from plants.catalogue import PLANT_CATALOGUE
from world import Tile
from fields import init_eco


def engine_of(tiles, ecos, house=None):
    gs = {"tiles": tiles, "eco": ecos, "scores": {}, "current_player": "joueur_1",
          "week": 1, "log": [], "house": house or House(), "seed": 12345}
    return Engine(gs)


def signature(tiles, ecos):
    h = hashlib.sha256()
    for t in tiles:
        e = ecos[t.tile_id]
        for name in sorted(e.populations):
            f = e.populations[name]
            for row in f.data:
                h.update(",".join(f"{v:.9f}" for v in row).encode())
        for p in t.plants:
            h.update(f"{p.position}:{round(p.vitalite,9)}".encode())
    return h.hexdigest()[:16]


# ---------- (1) DÉTERMINISME ----------
def determinisme():
    from tests.test_golden import build_world
    def run():
        tiles, ecos = build_world()
        eng = engine_of(tiles, ecos)
        for _ in range(40):
            eng.tick_semaine()
        return signature(tiles, ecos)
    s1, s2 = run(), run()
    print("\n===== (1) DÉTERMINISME (golden, 2 runs × 40 ticks) =====")
    print(f"  run1={s1}  run2={s2}  →  {'IDENTIQUE (déterministe)' if s1==s2 else 'DIFFÈRE (non déterministe!)'}")
    return s1 == s2


# ---------- monde dense paramétrique ----------
def build_dense(n_target):
    """Une tuile 12×12, remplie de ~n_target plantes (mix robuste), sol riche."""
    R = C = 12
    tile = Tile(tile_id=f"DENSE{n_target}", soil_type="terre", grid_rows=R, grid_cols=C)
    eco = init_eco(tile.tile_id, R, C, humidite=1.6, fertilite=1.3,
                   microbiome=0.7, soil_type="terre", heterogene=True)
    eco.lumiere.fill(1.0)
    especes = [PLANT_CATALOGUE[k] for k in ("trefle", "courgette", "tournesol",
                                            "haricot", "violette")]
    i = 0
    for r in range(R):
        for c in range(C):
            if i >= n_target:
                break
            tile.add_plant(especes[i % len(especes)], r, c)
            i += 1
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    for stake in tile.stakes:
        while stake.add("paillage"):
            pass
    return [tile], {tile.tile_id: eco}


def part_phases(eng, tiles, ecos, warm, measured):
    for _ in range(warm):
        eng.tick_semaine()
    pr = cProfile.Profile(); pr.enable()
    for _ in range(measured):
        eng.tick_semaine()
    pr.disable()
    st = pstats.Stats(pr); total = st.total_tt
    part = {}
    for (fn, ln, fname), (cc, nc, tt, ct, cs) in st.stats.items():
        if fname == "tick_populations" and "vie_macro" in fn:
            part["pop"] = ct
        if fname == "compute" and "light" in fn:
            part["light"] = ct
    return total, part.get("pop", 0.0), part.get("light", 0.0)


def courbe():
    M = 30
    print("\n===== (2) COURBE densité→COÛT ABSOLU (1 tuile 12×12=144 plots, warm 30, 30 ticks) =====")
    print(f"  {'plantes':>7} {'tick_ms':>8} {'pop_ms':>7} {'light_ms':>8} {'reste_ms':>8}")
    from tests.test_golden import build_world
    gt, ge = build_world()
    tot, pop, li = part_phases(engine_of(gt, ge), gt, ge, 30, M)
    npl = sum(len(t.plants) for t in gt)
    print(f"  {npl:>7} {tot/M*1000:>8.1f} {pop/M*1000:>7.1f} {li/M*1000:>8.1f} "
          f"{(tot-pop-li)/M*1000:>8.1f}  (golden réel, 2 tuiles/96 plots)")
    for n in (10, 30, 60, 100, 144):
        tiles, ecos = build_dense(n)
        tot, pop, li = part_phases(engine_of(tiles, ecos), tiles, ecos, 30, M)
        npl = sum(len(t.plants) for t in tiles)
        print(f"  {npl:>7} {tot/M*1000:>8.1f} {pop/M*1000:>7.1f} {li/M*1000:>8.1f} "
              f"{(tot-pop-li)/M*1000:>8.1f}")


# ---------- (3) COÛT PEINTRE ----------
def cout_peintre():
    from fields.population.perception import (
        sample_sprites, cap_sprites_global, SPRITES_MONDE_MAX)
    print("\n===== (3) COÛT PEINTRE (snapshot sprites), warm 45 (plein été) =====")
    from tests.test_golden import build_world
    scenarios = [("golden", build_world()), ("dense-100", build_dense(100))]
    for label, (tiles, ecos) in scenarios:
        eng = engine_of(tiles, ecos)
        for _ in range(45):
            eng.tick_semaine()
        # temps d'un tick complet (référence)
        t0 = time.perf_counter()
        for _ in range(20):
            eng.tick_semaine()
        ms_tick = (time.perf_counter()-t0)/20*1000
        # temps de la construction sprites d'un snapshot
        def build_sprites():
            cand = []
            present = set()
            for t in tiles:
                e = ecos[t.tile_id]
                for f in e.populations.values():
                    ss = sample_sprites(f, 12345)
                    if ss:
                        present.add((t.tile_id, f.spec.name))
                    for s in ss:
                        cand.append(((t.tile_id, f.spec.name), s))
            kept = cap_sprites_global(cand, SPRITES_MONDE_MAX)
            return len(cand), len(kept), len(present)
        t0 = time.perf_counter()
        reps = 30
        for _ in range(reps):
            ncand, nkept, npresent = build_sprites()
        ms_paint = (time.perf_counter()-t0)/reps*1000
        print(f"  {label:10s} tick={ms_tick:7.2f}ms  peintre={ms_paint:6.2f}ms "
              f"({100*ms_paint/ms_tick:4.1f}% d'un tick)  sprites={ncand}→{nkept}  "
              f"(tuile,type) présents={npresent}  → cible D2 ≈ {npresent} sprites")


if __name__ == "__main__":
    determinisme()
    courbe()
    cout_peintre()
