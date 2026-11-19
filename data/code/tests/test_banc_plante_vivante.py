"""
SYMBIOSE — tests/test_banc_plante_vivante.py
Oracle du banc `plante_vivante` (D140 G, sprint plante vivante ⑥), lancé À LA DEMANDE.

Monte le banc par le SERVEUR (même chemin que la vue au F5 : seed 42, semaine de
départ du banc), simule 8 semaines (s12 → s20) et vérifie que chaque scène montre ce
qu'elle promet :
  (a) limaces : le semis de chêne meurt, le chêne de 25 ans garde ses feuilles ;
  (b) ombre : les trois poivrons au pied du mur nord meurent de faim ;
  (c) refeuillaison : les consoudes broutées (0,2) ont refait leurs feuilles ;
  (d) souche : le chêne coupé a rejeté, un nombre FINI de rejets (≤ N_REJETS_MAX) ;
et que le snapshot porte `feuillage_bilan` / `reserves` (pont 0.6.21).

Lancement (depuis data/code/) :
  python3 -m tests.test_banc_plante_vivante
"""

import sys

from tools.sim_server import SimServer
from sim.souche import N_REJETS_MAX
from bancs.plante_vivante import AGE_CHENE_COUPE

SEMAINES = 8


def _tuile(gs, nom):
    return next(t for t in gs["tiles"] if t.tile_id == nom)


def main():
    srv = SimServer()
    rep = srv.cmd_init({"config": "plante_vivante", "seed": 42})
    assert rep["ok"] and rep.get("warmup") == 1, rep.get("warmup")
    gs = srv.engine.game_state
    assert gs["week"] == 12, gs["week"]
    morts_faim = set()
    for _ in range(SEMAINES):
        srv.engine.tick_semaine()
        for ligne in gs["log"]:
            if "meurt de faim" in ligne and "Poivron" in ligne:
                morts_faim.add(ligne)
        gs["log"].clear()

    lim = _tuile(gs, "LIMACES")
    chene, semis = (next(p for p in lim.plants if p.position == pos)
                    for pos in ((5, 3), (5, 13)))
    assert chene.is_alive and chene.feuillage > 0.95, chene.feuillage
    assert semis.morte, "le semis de chêne aurait dû succomber aux limaces"
    print(f"[a] PASS — chêne feuillage {chene.feuillage:.2f}, semis mort")

    ombre = _tuile(gs, "OMBRE").plants
    assert not any(p.is_alive for p in ombre), [p.reserves for p in ombre]
    assert morts_faim, "les poivrons à l'ombre doivent mourir de FAIM"
    print(f"[b] PASS — 3 poivrons morts à l'ombre ({len(morts_faim)} ligne(s) de famine)")

    ref = sorted(_tuile(gs, "REFEUILLE").plants, key=lambda p: p.position)
    assert all(p.is_alive for p in ref) and all(p.feuillage > 0.9 for p in ref[1:]), \
        [(p.position, round(p.feuillage, 2)) for p in ref]
    print(f"[c] PASS — consoudes broutées refaites : "
          f"{[round(p.feuillage, 2) for p in ref[1:]]}")

    sou = _tuile(gs, "SOUCHE").plants
    rejets = [p for p in sou if p.age_years < AGE_CHENE_COUPE]   # tout sauf l'arbre coupé
    assert 1 <= len(rejets) <= N_REJETS_MAX, len(rejets)
    print(f"[d] PASS — {len(rejets)} rejet(s) de souche (≤ {N_REJETS_MAX})")

    snap = srv._snapshot()
    vivantes = [p for p in snap["plants"] if not p.get("dead")]
    assert vivantes and all("feuillage_bilan" in p and "reserves" in p for p in vivantes)
    print("[pont] PASS — feuillage_bilan / reserves sur chaque plante vivante")
    return 0


if __name__ == "__main__":
    sys.exit(main())
