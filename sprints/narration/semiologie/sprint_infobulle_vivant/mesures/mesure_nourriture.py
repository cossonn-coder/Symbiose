"""INFO-BULLE DU VIVANT ① — MESURE des bandes de nourriture (lecture seule).
Run témoin : monde de démo `full` (seed serveur par défaut 0x5AB1057E), N semaines.
Chaque semaine, relève l'`activite` de chaque sprite PEINT (`peindre_presence`, le
même peintre que le snapshot) et de chaque butineur (activite de son champ au plot).
Sort les tertiles (bornes rare/suffisante/abondante) sur les sprites, et à titre de
contrôle sur les butineurs. Aucune écriture moteur (lecture du monde entre 2 ticks).
Usage (depuis data/code/) :
  python3 ../../sprints/narration/semiologie/sprint_infobulle_vivant/mesures/mesure_nourriture.py [semaines]
"""
import sys
from fields.population import peindre_presence
from tools.simserver.server import SimServer


def quantile(xs, q):
    xs = sorted(xs)
    i = q * (len(xs) - 1)
    lo = int(i)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def main(semaines: int) -> None:
    srv = SimServer()
    srv.cmd_init({"config": "full"})
    gs = srv.engine.game_state
    sprites, butineurs = [], []
    par_espece: dict = {}
    for _ in range(semaines):
        srv.cmd_step_week({})
        for tile in gs["tiles"]:
            eco = gs["eco"][tile.tile_id]
            for f in eco.populations.values():
                for s in peindre_presence(f, gs["seed"]):
                    a = round(s.activite, 2)
                    sprites.append(a)
                    par_espece.setdefault(f.spec.name, []).append(a)
            for ag in (eco.foragers or []):
                fld = eco.populations.get(ag.guild)
                if fld:
                    butineurs.append(round(fld.activite(ag.row, ag.col), 2))
    for nom, xs in (("sprites", sprites), ("butineurs", butineurs)):
        if not xs:
            print(f"{nom}: n=0")
            continue
        t1, t2 = quantile(xs, 1 / 3), quantile(xs, 2 / 3)
        print(f"{nom}: n={len(xs)} min={min(xs):.2f} max={max(xs):.2f} "
              f"médiane={quantile(xs, .5):.2f} tertiles={t1:.2f} / {t2:.2f}")
    print("par espèce (n, médiane) :")
    for nom in sorted(par_espece):
        xs = par_espece[nom]
        print(f"  {nom:11s} n={len(xs):6d} méd={quantile(xs, .5):.2f}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 104)
