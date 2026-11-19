"""Mesure ③ lisibilité du bilan : feuillage/réserves des 3 consoudes du banc
`plante_vivante` (seed 42 comme la vue, n=1), semaine par semaine. Lancer depuis data/code :
    python3 ../../sprints/vegetal/sante/sprint_lisibilite_bilan/mesures/consoudes.py [semaines]
Imprime aussi les poivrons de l'ombre (feuillage, réserves, vitalité, vivants) et la
litière par tissu sur leurs plots (pour la vue ③ A)."""
import sys
sys.path.insert(0, ".")
from tools.sim_server import SimServer

n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
srv = SimServer()
srv.cmd_init({"config": "plante_vivante", "seed": 42})
eng = srv.engine
tiles = {t.tile_id: t for t in eng.tiles}


def ligne():
    ref = tiles["REFEUILLE"]
    cons = sorted((p for p in ref.plants if p.plant_class.__name__ == "Comfrey"
                   and p.position[0] == 4 and p.position[1] in (2, 4, 6)),
                  key=lambda p: p.position[1])
    c = " ".join(f"{p.feuillage:.2f}/{p.reserves:.2f}" for p in cons)
    omb = tiles["OMBRE"]
    po = [p for p in omb.plants if p.plant_class.__name__ == "Pepper"]
    pv = " ".join(f"{p.feuillage:.2f}/{p.reserves:.2f}/{p.vitalite:.2f}" for p in po)
    return f"s{eng.week:3d} consoudes(f/r) {c} | poivrons(f/r/v) {pv}"


print("init", ligne())
for _ in range(n):
    eng.tick_semaine()
    print(ligne())


def litiere_poivrons():
    omb = tiles["OMBRE"]
    eco = eng.game_state["eco"]["OMBRE"]
    out = []
    for c in (2, 4, 6):
        parts = {p.tissu: (round(p.masse, 2), round(p.age_sem, 1))
                 for p in eco.litiere[7][c] if p.masse > 0}
        out.append(f"c{c}:{parts}")
    return " ".join(out)


if len(sys.argv) > 2:
    for _ in range(int(sys.argv[2])):
        eng.tick_semaine()
        vivants = sum(1 for p in tiles["OMBRE"].plants if p.plant_class.__name__ == "Pepper")
        print(f"s{eng.week} poivrons={vivants} {litiere_poivrons()}")
