"""Re-mesure finale D110 (g)(h)(i) — sol qui respire ⑧ (lecture seule, golden intact).
Usage (depuis data/code/) :
  PYTHONPATH=. python3 ../../sprints/champs/sol/sprint_sol_qui_respire/mesures/remesure_finale.py seed [semaines]
Monde `full`, une semaine sur 4 (comme `mesure_sante.py` de l'info-bulle) on relève au
VRAI snapshot du pont, par an :
  (g) vitalité médiane des plantes vivantes + part portant `acclimatation` (> 0 et
      > 0,05, seuil cité par D110) ;
  (h) carpophores : plot-semaines fructifiants (toutes les semaines) + espèces vues ;
  (i) nourriture sous les butineurs (8ᵉ champ des foragers) : médiane, part < 0,1.
"""
import sys
import collections
from tools.simserver.server import SimServer


def med(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else float("nan")


def main(seed: int, semaines: int) -> None:
    srv = SimServer()
    srv.cmd_init({"config": "full", "seed": seed})
    vit, accl, accl5, nplantes = (collections.defaultdict(list) for _ in range(4))
    carpo = collections.Counter()
    esp = collections.defaultdict(collections.Counter)
    nour = collections.defaultdict(list)
    for w in range(semaines):
        snap = srv.cmd_step_week({})["snapshot"]
        an = w // 52
        for ks in snap["carpophores"].values():
            plots = {(k[0], k[1]): k[6] for k in ks}
            carpo[an] += len(plots)
            for e in plots.values():
                esp[an][e] += 1
        for fs in snap["foragers"].values():
            for f in fs:
                if len(f) > 7:
                    nour[an].append(f[7])
        if w % 4:
            continue
        for p in snap["plants"]:
            if p.get("dead") or "vitalite" not in p:
                continue
            vit[an].append(p["vitalite"])
            a = max((s["intensity"] for s in p.get("leaf_symptoms") or []
                     if s["cause"] == "acclimatation"), default=0.0)
            accl[an].append(a > 0.0)
            accl5[an].append(a > 0.05)
    for an in sorted(vit):
        n = len(vit[an])
        f = nour[an]
        print(f"seed {seed} an {an} : (g) vitalité méd {med(vit[an]):.2f} [n={n}] · "
              f"acclimatation >0 {sum(accl[an]) / n:.0%} / >0,05 {sum(accl5[an]) / n:.0%} · "
              f"(h) carpophores {carpo[an]} plot-sem., espèces {dict(esp[an])} · "
              f"(i) nourriture méd {med(f):.2f}, <0,1 {sum(x < 0.1 for x in f) / max(1, len(f)):.0%} [n={len(f)}]")


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 156)
