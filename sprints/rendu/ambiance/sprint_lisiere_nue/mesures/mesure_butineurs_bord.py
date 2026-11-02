"""
Mesure du tronçon ① de LISIÈRE NUE (hors golden, lecture seule) : le pommier
croise-t-il des butineurs en an 1 ?

Deux mondes, parce que `bancs/mesure_calendrier.py` lit `floraison_saisons`, un banc
SANS ceinture (donc sans colonie, par construction) :
  - full   : le monde de jeu, avec sa ceinture ;
  - banc   : `floraison_saisons` + `generer_ceinture(seed)` posée à la main.
Pour chaque semaine où un pommier a floraison ≥ 0,5 : densité de butineurs sur ses
plots foliaires, moyenne de tuile (seuil 0,05 de `mesure_calendrier`), pollen reçu.

Usage, depuis data/code/ : python3 <ce fichier> [--seed 42] [--ans 1]
"""
import argparse
import os
import sys

sys.path.insert(0, os.getcwd())

from bancs.mesure_floraison import _monde
from fields import POLLINATOR_NAMES
from fields.peripherie import generer_ceinture
from tools.simserver.server import SimServer

SEUIL = 0.05


def _dens_plots(eco, plots):
    plots = [p for p in plots if 0 <= p[0] < eco.rows and 0 <= p[1] < eco.cols]
    if not plots:
        return 0.0
    return sum(eco.pollinator_density(r, c) for r, c in plots) / len(plots)


def _moy_tuile(eco):
    return sum(eco.pollinator_density(r, c) for r in range(eco.rows)
               for c in range(eco.cols)) / (eco.rows * eco.cols)


def releve(gs, step, nom, ans):
    print(f"\n== {nom} : ceinture {[s['type'] for s in gs.get('ceinture') or []]}")
    pics, somme, fruits = {}, {}, {}
    for _ in range(ans * 52):
        w = gs["week"]
        log = step()
        an, wiy = (w - 1) // 52 + 1, (w - 1) % 52 + 1
        for t in gs["tiles"]:
            eco = gs["eco"][t.tile_id]
            m = _moy_tuile(eco)
            pics[(an, t.tile_id)] = max(pics.get((an, t.tile_id), 0.0), m)
            somme[an] = somme.get(an, 0.0) + m / (52 * len(gs["tiles"]))
            for p in t.plants:
                if p.is_alive and p.plant_class.__name__ == "AppleTree" and p.floraison >= 0.5:
                    d = _dens_plots(eco, p.foliar_plots)
                    print(f"an {an} s{wiy:02d} {t.tile_id} pommier@({p.x_cm:.0f},{p.y_cm:.0f})"
                          f" floraison {p.floraison:.2f} butineurs plots {d:.3f}"
                          f" tuile {m:.3f} croise {'oui' if m >= SEUIL else 'non'}"
                          f" pollen {p.pollen_recu:.3f}")
        fruits[an] = fruits.get(an, 0) + sum("Nouaison Pommier" in l for l in log or ())
        gs["log"].clear()
    for (an, tid), v in sorted(pics.items()):
        print(f"pic densité moyenne an {an} {tid} : {v:.3f}")
    for an in sorted(somme):
        print(f"an {an} : densité moyenne monde {somme[an]:.3f}, nouaisons pommier {fruits[an]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--ans", type=int, default=1)
    a = ap.parse_args()
    assert a.ans <= 3, "mesures ≤ 3 ans"
    srv = SimServer()
    assert srv.cmd_init({"config": "full", "seed": a.seed}).get("ok")
    releve(srv.engine.game_state, srv.engine.tick_semaine, "full", a.ans)
    gs, engine, _plants, _eco = _monde()
    gs["seed"] = a.seed
    gs["ceinture"] = generer_ceinture(a.seed)
    releve(gs, engine.tick_semaine, "floraison_saisons + ceinture", a.ans)


if __name__ == "__main__":
    main()
