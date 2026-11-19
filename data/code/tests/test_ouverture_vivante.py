"""
SYMBIOSE — tests/test_ouverture_vivante.py
Banc d'ACCEPTATION de l'ouverture du monde `full` (D140 G, sprint plante vivante ⑤,
docs/vegetal/sante/conception_plante_vivante.md §7). Monde `full`, seed 42, de
l'ouverture (semaine 10) à la semaine 30 incluse — critères de Nico (2026-11-18) :
  1. AUCUN arbre posé mort ;
  2. ≤ 25 % des herbacées posées mortes, hors fin de cycle (annuelle/bisannuelle
     qui a fini sa vie : c'est la vie normale, pas une mortalité d'ouverture) ;
  3. ≤ 4 rejets de souche par arbre mort, au total (fin de la cascade, ④).

📖 Pédagogie (Nico) : « posée » = toute plante VIVANTE à l'ouverture (jardin de
`build_world_full` + espèces posées adultes par `sim/monde_complet`). Une mort est
appariée à sa cause en lisant le log du tick par `sim.evenements` (même lecture que
la chronique) : (tuile, plot, espèce) ; repli sur la tuile inconnue pour les dégâts
écrits avant les en-têtes `[T0]` (nuit froide). Lent (~20 ticks du monde full,
≈ 15 s sur la VM) : banc de sprint.
Lancer depuis data/code : `python3 -m tests.test_ouverture_vivante`.
"""

import re
import sys
from collections import Counter

from plants import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from plants.perennials import PerennialWoody
from sim.evenements import evenements
from tools.sim_server import SimServer

SEMAINE_FIN = 30
PART_HERBACEES_MAX = 0.25
REJETS_PAR_ARBRE_MORT_MAX = 4
_RE_REJET_SOUCHE = re.compile(r"Rejet de souche.*×(\d+) \[souche de")

ECHECS = []


def check(nom, ok, detail=""):
    print(("  ok   " if ok else "  ÉCHEC ") + nom + (f" — {detail}" if detail else ""))
    if not ok:
        ECHECS.append(nom)


_CLE_DE = {v: k for k, v in {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}.items()}


def mesurer(seed: int = 42, fin: int = SEMAINE_FIN) -> dict:
    """Déroule le monde `full` de l'ouverture à `fin` ; renvoie les morts des
    plantes posées (avec cause et facteur limitant au dernier tick), les arbres
    morts (tous, posés ou non) et les rejets de souche."""
    srv = SimServer()
    srv.cmd_init({"config": "full", "seed": seed})
    eng = srv.engine
    vivantes = {id(p): (p, t.tile_id) for t in eng.tiles for p in t.plants if p.is_alive}
    posees = dict(vivantes)
    morts_posees, arbres_morts, rejets = [], 0, 0
    while eng.week <= fin:
        log = eng.tick_semaine()
        semaine = eng.week - 1
        causes = {}
        for ev in evenements(log):
            if ev.kind == "mort":
                causes.setdefault((ev.tile_id, ev.pos, ev.espece), ev.cause)
                causes.setdefault((None, ev.pos, ev.espece), ev.cause)
        rejets += sum(int(m.group(1)) for l in log
                      for m in [_RE_REJET_SOUCHE.search(l)] if m)
        presentes = {id(p) for t in eng.tiles for p in t.plants if p.is_alive}
        for i, (p, tuile) in list(vivantes.items()):
            if i in presentes:
                continue
            del vivantes[i]
            if issubclass(p.plant_class, PerennialWoody):
                arbres_morts += 1
            if i in posees:
                esp = _CLE_DE.get(p.plant_class)
                cause = (causes.get((tuile, p.position, esp))
                         or causes.get((None, p.position, esp)) or "non_consignee")
                morts_posees.append({"semaine": semaine, "espece": esp, "cause": cause,
                                     "arbre": issubclass(p.plant_class, PerennialWoody),
                                     "limitant": getattr(p, "limitant", None)})
        for t in eng.tiles:
            for p in t.plants:
                if p.is_alive and id(p) not in vivantes:
                    vivantes[id(p)] = (p, t.tile_id)
    n_arbres = sum(issubclass(p.plant_class, PerennialWoody) for p, _ in posees.values())
    return {"n_posees": len(posees), "n_arbres": n_arbres,
            "n_herbacees": len(posees) - n_arbres, "morts": morts_posees,
            "arbres_morts": arbres_morts, "rejets": rejets}


def test_ouverture(m: dict) -> None:
    arbres = [x for x in m["morts"] if x["arbre"]]
    herb = [x for x in m["morts"] if not x["arbre"] and x["cause"] != "fin_de_cycle"]
    part = len(herb) / max(1, m["n_herbacees"])
    print(f"[ouverture full s10→s{SEMAINE_FIN}] posées {m['n_posees']} "
          f"(arbres {m['n_arbres']}, herbacées {m['n_herbacees']})")
    print("  morts posées par cause :",
          dict(Counter(x["cause"] for x in m["morts"]).most_common()))
    print("  morts posées par (cause, espèce, limitant) :",
          dict(Counter((x["cause"], x["espece"], x["limitant"])
                       for x in m["morts"]).most_common()))
    check("aucun arbre posé mort", not arbres, str(arbres))
    check(f"herbacées posées mortes hors fin de cycle ≤ {PART_HERBACEES_MAX:.0%}",
          part <= PART_HERBACEES_MAX, f"{len(herb)}/{m['n_herbacees']} = {part:.1%}")
    check(f"rejets ≤ {REJETS_PAR_ARBRE_MORT_MAX} par arbre mort",
          m["rejets"] <= REJETS_PAR_ARBRE_MORT_MAX * m["arbres_morts"],
          f"{m['rejets']} rejets, {m['arbres_morts']} arbres morts")


if __name__ == "__main__":
    test_ouverture(mesurer())
    print("ÉCHECS : " + (", ".join(ECHECS) if ECHECS else "aucun"))
    sys.exit(1 if ECHECS else 0)
