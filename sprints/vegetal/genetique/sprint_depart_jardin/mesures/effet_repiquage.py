"""Départ du jardin ④ — effet EN JEU du choc de repiquage. Lancer depuis data/code :
    python3 ../../sprints/vegetal/genetique/sprint_depart_jardin/mesures/effet_repiquage.py
Monde full seed 42 : les 3 godets de la maison repiqués en s10 dans S (7,13-15), avec
choc vs témoin (racines_coupees remis à 0). Colonnes : (hauteur, bilan_net, coupées,
stade, vivante)."""
import sys, contextlib; sys.path.insert(0, ".")
from tools.sim_server import SimServer
from sim import actions as A, vigueur as V
def run(choc):
    srv = SimServer()
    with contextlib.redirect_stdout(sys.stderr):
        srv.cmd_init({"config": "full", "seed": 42})
    gs = srv.engine.game_state
    V.ensure_player(gs, "joueur_1")["courante"] = 1e6
    S = [t for t in gs["tiles"] if t.tile_id == "S"][0]
    plants = []
    for ctn, c in zip(gs["containers"], (13, 14, 15)):
        p = ctn.plants[0]
        A.repiquer(gs, "joueur_1", ctn, S, 7, c)
        if not choc: p.racines_coupees = 0.0
        plants.append(p)
    rows = []
    for _ in range(10):
        with contextlib.redirect_stdout(sys.stderr):
            srv.engine.tick_semaine()
        rows.append([(round(p.current_height,1), round(p.bilan_net,2), round(p.racines_coupees,2), p.current_stage, p.is_alive) for p in plants])
    return rows
a, b = run(True), run(False)
for w, (ra, rb) in enumerate(zip(a, b), start=10):
    print(w, "CHOC", ra, "\n   TEMOIN", rb)
