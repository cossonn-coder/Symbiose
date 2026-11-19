"""Mesure ① plante vivante : bilan_net par espèce du monde `full` (seed 42, ouverture
s10), herbivorie NEUTRALISÉE en mémoire (la règle actuelle tue 121/136 posées avant
s21 : on mesure la niche, pas l'hécatombe que ③ corrige). Lancer depuis data/code :
    python3 ../../sprints/vegetal/sante/sprint_plante_vivante/mesures/bilan_par_espece.py [semaines...]
Par espèce posée (pied vivant au plot de PLACEMENTS) : bilan_net de la semaine écoulée,
réserves, et les facteurs (lumière, eau, T, nutrition, allélopathie, présence)."""
import sys
sys.path.insert(0, ".")
import sim.effects.perturbations as pert
import sim.engine.croissance as cr
import sim.bilan as bl
from tools.sim_server import SimServer
from sim.monde_complet import PLACEMENTS, _classe

pert.herbivory_pressure = lambda *a, **k: []      # neutralisation EN MÉMOIRE (golden intact)
facteurs = {}
_orig = cr.semaine_bilan


def _espion(plant, **kw):
    facteurs[id(plant)] = (bl.f_lum(kw["light_eff"]), bl.f_eau(plant, kw["hum_percue"]),
                           bl.f_temp(plant, kw["temp"], kw["t_feuille"]), kw["f_nut"],
                           kw["f_allelo"], kw["presence"], kw["t_air"])
    return _orig(plant, **kw)


cr.semaine_bilan = _espion


def releve(eng):
    pos = {(t, r, c): cle for cle, t, r, c in PLACEMENTS}
    out = {}
    for t in eng.tiles:
        for p in t.plants:
            cle = pos.get((t.tile_id, *p.position))
            if cle and p.is_alive and p.plant_class is _classe(cle) and cle not in out:
                out[cle] = p
    return out


if __name__ == "__main__":
    semaines = [int(a) for a in sys.argv[1:]] or [16, 20, 26]
    srv = SimServer()
    srv.cmd_init({"config": "full", "seed": 42})
    eng = srv.engine
    while eng.week <= max(semaines):
        eng.tick_semaine()
        w = eng.week - 1
        if w in semaines:
            print(f"--- semaine {w}  (lum eau T nut allelo presence | T_air)")
            for cle, p in sorted(releve(eng).items(), key=lambda kv: kv[1].bilan_net):
                f = facteurs.get(id(p), ())
                print(f"{cle:15s} net={p.bilan_net:+.2f} res={p.reserves:.2f} "
                      + " ".join(f"{x:.2f}" for x in f))
