"""INFO-BULLE DU VIVANT ② — distribution de santé des plantes au SNAPSHOT (lecture seule).
Run témoin : monde `full` (seed serveur par défaut), N semaines. Chaque semaine (sur
4), relève pour chaque plante vivante du snapshot : `vitalite`, `automne` et
l'intensité de son 1er symptôme par cause. Sert à situer les SEUILS DE VISIBILITÉ
mesurés au rendu (mesure_seuil.sh) : quelle part des signes et des vitalités tombe
sous le seuil (= le texte se tait / la voix saine parle).
Usage (depuis data/code/) :
  PYTHONPATH=. python3 ../../sprints/narration/semiologie/sprint_infobulle_vivant/mesures/mesure_sante.py [semaines]
"""
import sys
from tools.simserver.server import SimServer


def quantiles(xs, qs):
    xs = sorted(xs)
    return [xs[min(len(xs) - 1, int(q * (len(xs) - 1)))] for q in qs]


def main(semaines: int) -> None:
    srv = SimServer()
    srv.cmd_init({"config": "full"})
    vit, aut, sym = [], [], {}
    for w in range(semaines):
        srv.cmd_step_week({})
        if w % 4:
            continue
        for p in srv._snapshot()["plants"]:
            if p.get("dead") or "vitalite" not in p:
                continue
            vit.append(p["vitalite"])
            aut.append(p.get("automne", 0.0))
            for s in p.get("leaf_symptoms", []) or []:
                sym.setdefault(s["cause"], []).append(s["intensity"])
    qs = (0.05, 0.25, 0.5, 0.75, 0.95)
    print(f"vitalite n={len(vit)} q05/25/50/75/95={quantiles(vit, qs)} "
          f"part<0.999={sum(v < 0.999 for v in vit) / len(vit):.2f}")
    print(f"automne  n={len(aut)} part>0={sum(a > 0 for a in aut) / len(aut):.2f}")
    for c in sorted(sym):
        xs = sym[c]
        print(f"  {c:18s} n={len(xs):6d} q05/25/50/75/95={quantiles(xs, qs)}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 104)
