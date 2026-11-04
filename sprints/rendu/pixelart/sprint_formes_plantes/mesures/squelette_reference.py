# SYMBIOSE — mesure du tronçon ⑤ (FORMES DES PLANTES) : référence par semaine du monde
# `full`, pour prouver que retirer le squelette des herbacées ne bouge pas l'écologie.
#
# Par semaine : digest de `tests.test_golden.final_digest`, hash du log, plantes, espèces,
# segments, fruits, CPU du tick (`process_time`, moins sensible à la charge que l'horloge).
# Sonde posée AUTOUR du moteur, sur l'instance : `tick_semaine` et `organ_sites` enveloppés.
#
# Usage, depuis le `data/code/` à mesurer :
#   python3 <ce fichier> --sortie ref.json [--automate] [--semaines 156] [--seed 42]
#                        [--sans-depot-taille]
# `--sans-depot-taille` : la coupe de l'automate sur une espèce concernée ne dépose rien, et
# la masse qu'elle aurait déposée est relevée. Sert à prouver que cette masse est le SEUL
# écart de digest avec automate (formes ⑤, même option des deux côtés).
import argparse
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.getcwd())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--automate", action="store_true")
    ap.add_argument("--semaines", type=int, default=156)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--sans-depot-taille", action="store_true")
    a = ap.parse_args()

    from tests.test_golden import final_digest
    from tools.simserver.server import SimServer
    import sim.engine.decompo as decompo

    sites_semaine = []
    vrai_sites = decompo.organ_sites

    def sites_sondes(plant):
        sites = vrai_sites(plant)
        sites_semaine.append((plant.name, len(sites)))
        return sites

    decompo.organ_sites = sites_sondes

    masse_taille = [0.0]
    if a.sans_depot_taille:
        import sim.actions as ACT
        vrai_tailler = ACT.tailler

        def concernee(c):       # écrit à la main : le code d'avant n'a pas le prédicat
            return not (c.procedural_growth or c.ligneux or c.mode_grimpe is not None
                        or c.fruitier)

        def tailler_sonde(gs, joueur, plant, eco, **k):
            if not concernee(plant.plant_class):
                return vrai_tailler(gs, joueur, plant, eco, **k)
            vrai_depot = eco.deposer_litiere

            def depot(r, c, tissu, masse, *x, **y):
                masse_taille[0] += max(0.0, masse)

            eco.deposer_litiere = depot
            try:
                return vrai_tailler(gs, joueur, plant, eco, **k)
            finally:
                del eco.deposer_litiere   # retire la sonde d'instance
                assert eco.deposer_litiere == vrai_depot

        ACT.tailler = tailler_sonde

    srv = SimServer()
    rep = srv.cmd_init({"config": "full", "seed": a.seed})
    if not rep.get("ok"):
        raise RuntimeError(rep)
    if a.automate:
        rep = srv.cmd_automate({"op": "on", "profil": {"desherbage": "curatif"}})
        if not rep.get("ok"):
            raise RuntimeError(rep)

    eng = srv.engine
    cpu = [0.0]
    vrai_tick = eng.tick_semaine

    def tick_sonde():
        t0 = time.process_time()
        try:
            return vrai_tick()
        finally:
            cpu[0] = time.process_time() - t0

    eng.tick_semaine = tick_sonde

    lignes = []
    for _ in range(a.semaines):
        sites_semaine.clear()
        t_sem = time.process_time()
        rep = srv.cmd_step_week({})
        cpu_semaine = time.process_time() - t_sem
        if not rep.get("ok"):
            raise RuntimeError(rep)
        gs = eng.game_state
        tiles, ecos = gs["tiles"], gs["eco"]
        vivantes = [p for t in tiles for p in t.plants if p.is_alive]
        digest = hashlib.sha256(final_digest(tiles, ecos).encode()).hexdigest()
        lignes.append({
            "semaine": eng.week - 1, "digest": digest, "plantes": len(vivantes),
            "especes": len({p.name for p in vivantes}),
            "segments": sum(len(p.segments) for t in tiles for p in t.plants),
            "fruits": sum(len(p.fruits) for p in vivantes),
            "sites": list(sites_semaine),
            "cpu_tick_s": cpu[0], "ms_tick": srv._last_ms_tick,
            "cpu_semaine_s": cpu_semaine, "masse_taille": masse_taille[0],
        })
        with open(a.sortie, "w") as f:
            json.dump({"seed": a.seed, "automate": a.automate, "lignes": lignes}, f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
