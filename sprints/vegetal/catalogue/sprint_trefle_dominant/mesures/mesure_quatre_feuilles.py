"""
SYMBIOSE — mesure du sprint TRÈFLE DOMINANT ③ : combien de trèfles à quatre feuilles ?
Monde `full`, automate curatif, lecture de l'état chaque semaine, sans sonde moteur.
Relève le hash de chaque pied adulte : les comptes se déduisent pour plusieurs
probabilités d'un même run. L'automate n'écarte que les pieds de la probabilité en
vigueur, donc seule la ligne de `PROBA_QUATRE_FEUILLES` est strictement exacte.

Usage, depuis data/code/ :
  python3 <chemin>/mesure_quatre_feuilles.py --seed 42 --ans 5 --sortie resultat.json
"""
from __future__ import annotations
import argparse
import json
import os
import statistics
import sys

sys.path.insert(0, os.getcwd())

CANDIDATES = (0.002, 0.003, 0.005, 0.008, 0.01)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--ans", type=int, default=5)
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args()

    from fields.noise import _hash_noise
    from plants import Clover
    from sim import quatre_feuilles as Q
    from tools.simserver.server import SimServer
    srv = SimServer()
    srv.cmd_init({"config": "full", "seed": a.seed})
    srv.cmd_automate({"op": "on", "profil": {"desherbage": "curatif"}})
    gs = srv.engine.game_state

    def u_de(p) -> float:
        return _hash_noise(gs["seed"] ^ p.form_seed, Q._SALT_QUATRE_FEUILLES,
                           round(p.x_cm * 100), round(p.y_cm * 100))

    gardes = []          # garde les pieds en vie : un id ne peut pas être recyclé
    annees = []
    for an in range(1, a.ans + 1):
        vus: dict = {}
        par_semaine = []
        adultes = 0
        for _ in range(52):
            rep = srv.cmd_step_week({})
            if not rep.get("ok"):
                raise RuntimeError(rep)
            adultes = 0
            semaine = []
            for t in gs["tiles"]:
                for p in t.plants:
                    if p.plant_class is Clover and p.is_alive and p.current_stage >= 1:
                        adultes += 1
                        u = u_de(p)
                        semaine.append(u)
                        vus[id(p)] = u
                        gardes.append(p)
            par_semaine.append(semaine)
        ligne = {"an": an, "adultes_fin": adultes, "pieds_differents": len(vus), "par_proba": {}}
        for proba in CANDIDATES:
            sim = [sum(1 for u in s if u < proba) for s in par_semaine]
            ligne["par_proba"][str(proba)] = {
                "pieds_vus_an": sum(1 for u in vus.values() if u < proba),
                "a_la_fois_moy": round(statistics.fmean(sim), 2),
                "a_la_fois_min": min(sim), "a_la_fois_max": max(sim),
            }
        annees.append(ligne)
        print(json.dumps(ligne, ensure_ascii=False), flush=True)
    with open(a.sortie, "w") as f:
        json.dump({"seed": a.seed, "proba": Q.PROBA_QUATRE_FEUILLES, "annees": annees}, f,
                  ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
