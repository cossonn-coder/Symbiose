"""Mesure du banc `stress_au_bilan` (⑤) : chaque pied, semaine par semaine, par le
serveur (chemin du F5, seed 42) — vivant ?, réserves, feuillage, embolie, racines,
voix de la cause ; puis les morts lues au carnet (journal) et à la chronique.
Lancement (depuis data/code/) :
  python3 ../../sprints/vegetal/sante/sprint_stress_au_bilan/mesures/banc_causes.py [semaines]
"""
import sys
sys.path.insert(0, ".")
from tools.sim_server import SimServer
from sim.causes_bilan import voix_cause

N = int(sys.argv[1]) if len(sys.argv) > 1 else 16
srv = SimServer()
rep = srv.cmd_init({"config": "stress_au_bilan", "seed": 42})
assert rep["ok"], rep
gs = srv.engine.game_state
print("départ s", gs["week"], "warmup", rep.get("warmup"))
for i in range(N):
    assert srv.cmd_step_week({}).get("ok", True)
    ligne = [f"s{gs['week']-1:>3}"]
    for t in gs["tiles"]:
        for p in t.plants:
            if p.age_years < 0.2 and t.tile_id != "FIN_DE_CYCLE":
                continue
            etat = "†" if not p.is_alive else ""
            ligne.append(f"{t.tile_id[:5]}{p.position[1]}{etat} r{p.reserves:.2f} f{p.feuillage:.2f}"
                         f" e{p.embolie:.2f} pm{p.pourriture_memory:.2f} {voix_cause(p) or '-'}")
    print(" | ".join(ligne))
j = gs.get("journal", {}).get(gs["current_player"], {})
print("\ncarnet (morts) :")
for e in j.get("entries", []):
    if e["kind"] == "mort":
        print("  ", e)
print("\nchronique :")
print(srv._chronique.texte()[-1500:])
