"""Contrôle ④ plante vivante (souches à réserve) : monde `full` (seed 42), 52 semaines
depuis l'ouverture (s10) — naissances d'OakTree par semaine (nouvelles instances) et
vagues de rejets de souche (lignes 🌳 du log), par espèce. Lancer depuis data/code :
    python3 ../../sprints/vegetal/sante/sprint_plante_vivante/mesures/diag_chene.py
Avant ④ (2026-11-18) : vagues de chênes ×3 (9 → 27 → 75 → 153, s20-s32)."""
import sys
from collections import Counter
sys.path.insert(0, ".")
from tools.sim_server import SimServer

srv = SimServer()
srv.cmd_init({"config": "full", "seed": 42})
eng = srv.engine
debut = eng.week
vus = {id(p) for t in eng.tiles for p in t.plants}
rejets_tot = Counter()
naiss_chene = 0
print("sem  chênes_nés  chênes_vivants  rejets(espèce×n)")
while eng.week < debut + 52:
    log = eng.tick_semaine()
    w = eng.week - 1
    neufs = [p for t in eng.tiles for p in t.plants if id(p) not in vus]
    vus |= {id(p) for p in neufs}
    nc = sum(p.plant_class.__name__ == "OakTree" for p in neufs)
    naiss_chene += nc
    vivants = sum(p.is_alive and p.plant_class.__name__ == "OakTree"
                  for t in eng.tiles for p in t.plants)
    rej = Counter()
    for l in log:
        if "Rejet de souche" in l:
            esp = l.split("Rejet de souche : ")[1].split(" @")[0]
            rej[esp] += int(l.split(" ×")[1].split()[0])
    rejets_tot += rej
    print(f"{w:3d}  {nc:9d}  {vivants:14d}  " + " ".join(f"{e}×{n}" for e, n in rej.items()))
print("TOTAL chênes nés", naiss_chene, "| rejets", dict(rejets_tot))
