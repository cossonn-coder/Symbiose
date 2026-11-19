"""Contrôle ② plante vivante : monde `full` (seed 42), 52 semaines depuis l'ouverture
(s10) — plantes vivantes par semaine et causes de mort (lues au log par
`sim.evenements`, comme la chronique). Lancer depuis data/code :
    python3 ../../sprints/vegetal/sante/sprint_plante_vivante/mesures/controle_vie.py
Herbivorie TELLE QUELLE (la règle ③ n'est pas encore là) : on regarde le modèle de
vie, pas encore le critère d'ouverture (⑤)."""
import sys
from collections import Counter
sys.path.insert(0, ".")
from tools.sim_server import SimServer
from sim.evenements import evenements

srv = SimServer()
srv.cmd_init({"config": "full", "seed": 42})
eng = srv.engine
debut = eng.week
causes_tot = Counter()
par_espece = Counter()
print("sem  vivantes  morts(cause:n)")
while eng.week < debut + 52:
    log = eng.tick_semaine()
    w = eng.week - 1
    vivantes = sum(p.is_alive for t in eng.tiles for p in t.plants)
    morts = Counter(e.cause or "?" for e in evenements(log) if e.kind == "mort")
    causes_tot += morts
    par_espece += Counter((e.cause or "?", e.espece) for e in evenements(log)
                          if e.kind == "mort")
    print(f"{w:3d}  {vivantes:7d}  " + " ".join(f"{c}:{n}" for c, n in morts.most_common()))
print("TOTAL", " ".join(f"{c}:{n}" for c, n in causes_tot.most_common()))
print("PAR ESPÈCE", " ".join(f"{c}/{e}:{n}" for (c, e), n in par_espece.most_common(30)))
