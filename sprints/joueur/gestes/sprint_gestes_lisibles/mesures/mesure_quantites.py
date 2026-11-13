"""
Mesure reproductible des QUANTITÉS des gestes (sprint GESTES LISIBLES ①, §5).

Trois chiffres, monde `full`, seed 42, tous gestes passés par les façades moteur :
  1. GLANER   — masse créditée au stock par un glanage d'un plot ORDINAIRE (plot
                médian des plots qui ont de la litière tendre), en doses de paillis ;
  2. COMPOST  — `compost_mur` d'un bac rempli de toute la litière tendre de sa tuile,
                après une saison (13 semaines), et l'effet d'un épandage sur `om_stable` ;
  3. MIEL     — Vigueur rendue par la récolte d'une ruche posée au printemps, après
                une saison (sans équipement, cas du joueur débutant).

Usage (depuis data/code/) :
  python3 ../../sprints/joueur/gestes/sprint_gestes_lisibles/mesures/mesure_quantites.py
"""
import contextlib
import os
import sys

sys.path.insert(0, os.getcwd())

from fields.ecofields import PAILLAGE_DOSE             # noqa: E402
from sim import actions as A                          # noqa: E402
from sim import vigueur as V                          # noqa: E402
from sim.actions.paillage import TISSUS_GLANABLES     # noqa: E402
from tools.simserver.server import SimServer          # noqa: E402

J = "joueur_1"
SAISON = 13


def _monde(semaines: int):
    srv = SimServer()
    srv.cmd_init({"config": "full", "seed": 42})
    eng = srv.engine
    with contextlib.redirect_stdout(sys.stderr):
        for _ in range(semaines):
            eng.tick_semaine()
    gs = eng.game_state
    V.ensure_player(gs, J)["courante"] = 1e6     # on mesure des quantités, pas la bourse
    return eng, gs


def _tendre(eco, r, c) -> float:
    return sum(p.masse for p in eco.litiere[r][c]
               if p.masse > 0.0 and p.tissu in TISSUS_GLANABLES)


def mesure_glaner(gs):
    masses = []
    for t in gs["tiles"]:
        eco = gs["eco"][t.tile_id]
        for r in range(eco.rows):
            for c in range(eco.cols):
                m = _tendre(eco, r, c)
                if m > 0.0:
                    masses.append((m, t.tile_id, r, c))
    masses.sort()
    m, tid, r, c = masses[len(masses) // 2]
    credit = A.glaner(gs, J, gs["eco"][tid], r, c)
    return {"plots_avec_litiere": len(masses), "masse_mediane": m,
            "credit_median": credit, "doses": credit / PAILLAGE_DOSE,
            "masse_max": masses[-1][0]}


def mesure_compost(eng, gs):
    t = gs["tiles"][0]
    eco = gs["eco"][t.tile_id]
    bac = A.poser_bac(gs, J, eco, 0, 0)
    for r in range(eco.rows):
        for c in range(eco.cols):
            A.composter(gs, J, eco, r, c, bac)
    brut = sum(p.masse for p in bac.contenu)
    with contextlib.redirect_stdout(sys.stderr):
        for _ in range(SAISON):
            eng.tick_semaine()
    mur = bac.compost_mur
    r, c = eco.rows // 2, eco.cols // 2
    om0 = eco.om_stable.at_plot(r, c)
    n0 = eco.n.at_plot(r, c)
    epandu = A.epandre(gs, J, eco, r, c, bac)
    return {"contenu_brut": brut, "compost_mur": mur, "epandu": epandu,
            "om_stable": (om0, eco.om_stable.at_plot(r, c)),
            "n": (n0, eco.n.at_plot(r, c))}


def mesure_miel(eng, gs):
    t = gs["tiles"][0]
    eco = gs["eco"][t.tile_id]
    ruche = A.poser_ruche(gs, J, eco, eco.rows // 2, eco.cols // 2)
    with contextlib.redirect_stdout(sys.stderr):
        for _ in range(SAISON):
            eng.tick_semaine()
    miel, essaim = ruche.miel, ruche.essaim
    gain = A.recolter_miel(gs, J, ruche, eco)
    return {"essaim": essaim, "miel": miel, "gain_vigueur_sans_equipement": gain}


def main():
    eng, gs = _monde(8)             # printemps
    print("GLANER printemps", mesure_glaner(gs))
    eng, gs = _monde(26)            # fin d'été (l'année commence à l'équinoxe)
    print("GLANER fin d'été", mesure_glaner(gs))
    print("COMPOST ", mesure_compost(eng, gs))
    eng, gs = _monde(4)             # printemps : la ruche se peuple pendant l'été
    print("MIEL    ", mesure_miel(eng, gs))


if __name__ == "__main__":
    main()
