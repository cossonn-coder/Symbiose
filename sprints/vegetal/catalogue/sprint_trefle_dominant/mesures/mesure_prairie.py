"""
SYMBIOSE — mesure du sprint TRÈFLE DOMINANT (D126) : le tapis bouge-t-il ?
Lance le monde `full` (même fabrique que le F5, via SimServer) avec l'automate
curatif, et relève à chaque fin d'année : trèfle en plantes et en plots, part,
espèces, azote moyen par tuile, plantes par plot, morts de trèfle de l'année,
âges des pieds, et la liste des plots à trèfle (pour comparer an 3 et an 5).

Aucune sonde dans le moteur : on lit l'état après chaque `cmd_step_week`.

Usage (depuis data/code/, ou d'une copie d'un autre commit pour la référence) :
  python3 <chemin>/mesure_prairie.py --seed 42 --ans 5 --sortie resultat.json

`--moteur-seul` appelle `tick_semaine()` sans passer par `cmd_step_week` : l'automate
est monté mais ne joue JAMAIS (il joue dans `cmd_step_week`). C'est ainsi qu'a été
mesurée la référence du kickoff (729 plantes, trèfle 434) ; l'option sert à la rejouer.
"""
from __future__ import annotations
import argparse
import json
import os
import statistics
import sys
import time

sys.path.insert(0, os.getcwd())

NOM_TREFLE = "Trèfle"


def _vivants(engine):
    for t in engine.game_state["tiles"]:
        for p in t.plants:
            if p.is_alive:
                yield t, p


def _bilan_annuel(engine, morts: int) -> dict:
    plantes = list(_vivants(engine))
    trefles = [(t, p) for t, p in plantes if p.name == NOM_TREFLE]
    plots_trefle = sorted({(t.tile_id, *p.position) for t, p in trefles})
    plots_tous = {(t.tile_id, *p.position) for t, p in plantes}
    par_espece: dict[str, int] = {}
    for _, p in plantes:
        par_espece[p.name] = par_espece.get(p.name, 0) + 1
    azote_tuile, part_tuile = {}, {}
    for t in engine.game_state["tiles"]:
        azote_tuile[t.tile_id] = round(engine.game_state["eco"][t.tile_id].n.average(), 3)
        vivants = [p for p in t.plants if p.is_alive]
        n_t = sum(1 for p in vivants if p.name == NOM_TREFLE)
        part_tuile[t.tile_id] = round(n_t / len(vivants), 3) if vivants else 0.0
    azote_sous = [engine.game_state["eco"][tid].n.at_plot(r, c)
                  for tid, r, c in plots_trefle]
    ages = [p.age_years for _, p in trefles]
    # L'ombre du dactyle ferme-t-elle la porte des stolons (CLONAL_LIGHT_SEUIL) sur son plot ?
    plots_dactyle = {(t.tile_id, *p.position) for t, p in plantes
                     if p.name == "Dactyle" and p.current_stage > 0}
    sous_seuil = [pl for pl in plots_dactyle
                  if engine.game_state["eco"][pl[0]].lumiere.at_plot(pl[1], pl[2]) < 0.30]
    return {
        "semaine": engine.week - 1,
        "plantes": len(plantes),
        "trefle": len(trefles),
        "plots_trefle": len(plots_trefle),
        "part_trefle": round(len(trefles) / len(plantes), 3) if plantes else 0.0,
        "especes": len(par_espece),
        "par_espece": dict(sorted(par_espece.items(), key=lambda kv: -kv[1])),
        "plantes_par_plot": round(len(plantes) / len(plots_tous), 2) if plots_tous else 0.0,
        "azote_par_tuile": azote_tuile,
        "part_trefle_par_tuile": part_tuile,
        "azote_sous_trefle": {
            "moy": round(statistics.fmean(azote_sous), 3),
            "min": round(min(azote_sous), 3),
            "max": round(max(azote_sous), 3),
        } if azote_sous else None,
        "morts_trefle_annee": morts,
        "age_trefle": {"moy": round(statistics.fmean(ages), 2),
                       "max": round(max(ages), 2)} if ages else None,
        "liste_plots_trefle": plots_trefle,
        "plots_dactyle_adulte": len(plots_dactyle),
        "plots_dactyle_sous_seuil": len(sous_seuil),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--ans", type=int, default=5)
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--moteur-seul", action="store_true")
    a = ap.parse_args()

    from tools.simserver.server import SimServer
    srv = SimServer()
    rep = srv.cmd_init({"config": "full", "seed": a.seed})
    if not rep.get("ok"):
        raise RuntimeError(rep)
    rep = srv.cmd_automate({"op": "on", "profil": {"desherbage": "curatif"}})
    if not rep.get("ok"):
        raise RuntimeError(rep)

    annees = []
    morts = 0
    t_annee = time.perf_counter()
    avant = {id(p): p for _, p in _vivants(srv.engine) if p.name == NOM_TREFLE}
    for sem in range(1, a.ans * 52 + 1):
        if a.moteur_seul:
            srv.engine.tick_semaine()
        else:
            rep = srv.cmd_step_week({})
            if not rep.get("ok"):
                raise RuntimeError(rep)
        apres = {id(p): p for _, p in _vivants(srv.engine) if p.name == NOM_TREFLE}
        # `avant` garde les objets en vie : un id ne peut pas être recyclé entre deux semaines.
        morts += sum(1 for i in avant if i not in apres)
        avant = apres
        if sem % 52 == 0:
            secondes = time.perf_counter() - t_annee   # temps du tick seul, bilan exclu
            annees.append(_bilan_annuel(srv.engine, morts))
            annees[-1]["secondes_annee"] = round(secondes, 2)
            t_annee = time.perf_counter()
            morts = 0
            print(f"an {sem // 52} : {annees[-1]['plantes']} plantes, "
                  f"trèfle {annees[-1]['trefle']} sur {annees[-1]['plots_trefle']} plots",
                  flush=True)
    with open(a.sortie, "w") as f:
        json.dump({"seed": a.seed, "annees": annees}, f, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
