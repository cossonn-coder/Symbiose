"""Règne fongique (D111 ③) — lecture seule. Usage (depuis data/code/) :
  PYTHONPATH=. python3 ../../sprints/champs/sol/sprint_sol_qui_respire/mesures/fongique.py \
      seed semaines [config]          (config : full par défaut, ou pluie_continue)
Lit le bloc `carpophores` du VRAI snapshot du pont chaque semaine et rapporte :
plots fructifiants (slot 0) par an, par espèce, par saison, semaines avec carpophores,
plots distincts par espèce ; + coût de la perception carpophore (sample + racines)
rapporté au tick et au snapshot."""
import sys, time, collections
import tools.simserver.serialize as SER
from tools.simserver.server import SimServer

seed, N = int(sys.argv[1]), int(sys.argv[2])
config = sys.argv[3] if len(sys.argv) > 3 else "full"
t_carpo = [0.0]
for nom in ("sample_carpophores", "racines_par_plot"):
    f = getattr(SER, nom)
    def chrono(*a, _f=f, **k):
        t0 = time.perf_counter(); r = _f(*a, **k); t_carpo[0] += time.perf_counter() - t0
        return r
    setattr(SER, nom, chrono)

srv = SimServer(); srv.cmd_init({"config": config, "seed": seed})
gs = srv.engine.game_state
SAISON = ("printemps", "ete", "automne", "hiver")
par_an, par_esp, par_sais, sem_fruit = (collections.Counter() for _ in range(4))
plots_esp = collections.defaultdict(set)
t_tick = t_snap = 0.0
semaines_fruits = []
for w in range(N):
    t0 = time.perf_counter(); srv.cmd_step_week({}); t_tick += time.perf_counter() - t0
    t0 = time.perf_counter(); snap = srv._snapshot(); t_snap += time.perf_counter() - t0
    wiy = ((gs["week"] - 1) % 52) + 1
    an, sais = w // 52, SAISON[min(3, (wiy - 1) // 13)]
    n = 0
    for tid, ks in snap["carpophores"].items():
        for k in ks:
            r, c, *_x, esp = k
            plots_esp[esp].add((tid, r, c))
            if (r, c) not in {(q[0], q[1]) for q in ks[:ks.index(k)]}:
                par_an[an] += 1; par_esp[esp] += 1; par_sais[(an, sais)] += 1; n += 1
    if n:
        sem_fruit[an] += 1; semaines_fruits.append(gs["week"])
print(f"seed {seed} {config} {N} sem. : plots fructifiants/an {dict(par_an)} | "
      f"semaines avec carpophores/an {dict(sem_fruit)}")
print("  par espèce (plots×sem.) :", dict(par_esp.most_common()))
print("  plots distincts :", {k: len(v) for k, v in sorted(plots_esp.items())})
print("  par saison :", dict(sorted(par_sais.items())))
print("  semaines (snapshot) avec carpophores :", semaines_fruits)
print(f"  coût : tick moy {1000 * t_tick / N:.0f} ms, snapshot moy {1000 * t_snap / N:.1f} ms, "
      f"perception carpophores moy {1000 * t_carpo[0] / N:.2f} ms "
      f"({100 * t_carpo[0] / t_tick:.2f} % du tick)")
