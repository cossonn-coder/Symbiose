"""Banc « pluie chaque semaine » (D111 ①e) — vérifie que la pluie forcée a VRAIMENT agi
sur toute la chaîne aval, SANS réglage ad hoc, contre le monde `full` témoin (même
graine, même monde, météo normale). Lecture seule. Lancer depuis `data/code/` :
    PYTHONPATH=. python3 ../../sprints/champs/sol/sprint_sol_qui_respire/mesures/banc_pluie.py [semaines]
Maillons vérifiés : sol au plafond 3,0 → flaques `eau_surface` → marécage `marais_memory`
(creux) → asphyxie sur argile → recul de l'acclimatation. (Carpophores : tronçon ③.)"""
import sys, statistics as st
from tools.simserver.server import SimServer
from fields.ecofields.constants import HUM_CAP, MARAIS_ON
from sim.semiologie import asphyxie, acclimatation
from sim.engine.calendrier import saison_de

N = int(sys.argv[1]) if len(sys.argv) > 1 else 30
SEED = 0x5AB1057E


def etat(srv):
    gs = srv.engine.game_state
    saison = saison_de(((gs["week"] - 2) % 52) + 1)
    ecos = gs["eco"]
    hs = [v for e in ecos.values() for row in e.humidite.data for v in row]
    eau = sum(v for e in ecos.values() for row in e.eau_surface.data for v in row)
    mar = [v for e in ecos.values() for row in e.marais_memory.data for v in row]
    asph_arg, acc, vivantes = [], [], 0
    for t in gs["tiles"]:
        e = ecos[t.tile_id]
        for p in t.plants:
            if not p.is_alive:
                continue
            vivantes += 1
            acc.append(acclimatation(p, e, saison))
            if t.soil_type == "argile":
                asph_arg.append(asphyxie(p, e, saison))
    return {"hmed": st.median(hs), "plafond": sum(h >= HUM_CAP - 0.05 for h in hs) / len(hs),
            "eau": eau, "marais_max": max(mar), "marais_on": sum(m >= MARAIS_ON for m in mar),
            "asph_arg": sum(a > 0 for a in asph_arg) / max(1, len(asph_arg)),
            "acc": sum(a > 0.1 for a in acc) / max(1, len(acc)), "n": vivantes}


def run(config):
    srv = SimServer(); srv.cmd_init({"config": config, "seed": SEED})
    traj = []
    for w in range(N):
        srv.cmd_step_week({})
        traj.append(etat(srv))
    return traj


pluie, temoin = run("pluie_continue"), run("full")
print("sem | PLUIE hmed plafond eau marais_max/on asph_arg acc n || TÉMOIN hmed eau marais_max asph_arg acc n")
for w in range(3, N, 4):
    a, b = pluie[w], temoin[w]
    print(f"{w+1:3d} | {a['hmed']:.2f} {a['plafond']:.2f} {a['eau']:.2f} {a['marais_max']:.2f}/{a['marais_on']}"
          f" {a['asph_arg']:.2f} {a['acc']:.2f} {a['n']} || {b['hmed']:.2f} {b['eau']:.2f} {b['marais_max']:.2f}"
          f" {b['asph_arg']:.2f} {b['acc']:.2f} {b['n']}")
fin_p, fin_t = pluie[-1], temoin[-1]
verdicts = {
    "sol au plafond (part de plots ≥ HUM_CAP−0,05 > 50 %)": fin_p["plafond"] > 0.5,
    "flaques eau_surface > 0": max(x["eau"] for x in pluie) > 0.0,
    "marécage marais_memory ≥ MARAIS_ON quelque part": max(x["marais_on"] for x in pluie) > 0,
    "asphyxie sur argile > témoin": max(x["asph_arg"] for x in pluie) > max(x["asph_arg"] for x in temoin),
    "acclimatation en recul vs témoin": fin_p["acc"] < fin_t["acc"],
}
for k, ok in verdicts.items():
    print(("OK   " if ok else "MUET ") + k)
