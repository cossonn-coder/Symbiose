"""
SYMBIOSE — tests/test_hauteur_acquise.py
Hauteur ACQUISE (sprint lisibilité du bilan ①, `docs/vegetal/sante/conception_lisibilite_bilan.md`
§2.1) : une plante ne rapetisse pas. Le `growth_factor` règle la vitesse de pousse ; un
déficit du bilan le fait baisser, mais la tige bâtie reste debout. Seule une destruction
des parties aériennes retire de la hauteur.

  [ombre]    banc `plante_vivante` : les poivrons au pied du mur nord meurent de faim
             SANS perdre un centimètre (avant : 60 → 47 cm [seed 42, n=1]) ;
  [dormance] même banc, consoudes : la vivace herbacée redescend à l'entrée de l'hiver
             (repli aérien), puis ne rapetisse plus au printemps ;
  [taille]   une tomate (procédurale : hauteur = sa structure) taillée perd de la hauteur ;
  [régression] une espèce sans structure qui régresse d'un stade perd sa hauteur acquise.

Lancement (depuis data/code/) :
  python3 -m tests.test_hauteur_acquise
"""

import sys

from tools.sim_server import SimServer
from sim.engine import Engine
from sim import vigueur as V
import sim.actions as ACT
from tests.vigueur.harness import _minimal_state

SEMAINES_BANC = 34          # s12 → s46 : l'été des poivrons, l'entrée en hiver des consoudes


def _tuile(gs, nom):
    return next(t for t in gs["tiles"] if t.tile_id == nom)


def test_banc_ombre_et_dormance():
    srv = SimServer()
    srv.cmd_init({"config": "plante_vivante", "seed": 42})
    gs = srv.engine.game_state
    poivrons = list(_tuile(gs, "OMBRE").plants)
    consoudes = sorted(_tuile(gs, "REFEUILLE").plants, key=lambda p: p.position)[1:]
    vu_p = {id(p): [p.current_height] for p in poivrons}
    vu_c = {id(p): [] for p in consoudes}
    for _ in range(SEMAINES_BANC):
        srv.engine.tick_semaine()
        gs["log"].clear()
        for p in poivrons:
            if p.is_alive:
                vu_p[id(p)].append(p.current_height)
        for p in consoudes:
            vu_c[id(p)].append(p.current_height)
    assert not any(p.is_alive for p in poivrons), "les poivrons à l'ombre doivent mourir"
    for h in vu_p.values():
        assert all(b >= a - 1e-9 for a, b in zip(h, h[1:])), h
    print(f"[ombre] PASS — poivrons morts de faim sans rapetisser "
          f"({[round(h[-1], 1) for h in vu_p.values()]} cm à la mort)")
    for p in consoudes:
        h = vu_c[id(p)]
        assert p.is_alive, "les consoudes passent l'hiver"
        assert h[-1] < max(h) - 1.0, h            # repli aérien : la hauteur retombe l'hiver
    print(f"[dormance] PASS — consoudes : été {[round(max(vu_c[id(p)]), 1) for p in consoudes]}"
          f" → hiver {[round(vu_c[id(p)][-1], 1) for p in consoudes]} cm")


def test_taille_tomate():
    gs = _minimal_state(week=20)
    tile, eco = gs["tiles"][0], gs["eco"]["T0"]
    tomate = tile.plants[0]
    eng = Engine(gs)
    for _ in range(8):
        eng.tick_semaine()
        gs["log"].clear()
    avant = tomate.current_height
    V.ensure_player(gs, "joueur_1")["courante"] = 100.0
    assert ACT.tailler(gs, "joueur_1", tomate, eco)
    tomate.update_footprint()                  # le cache d'empreinte suit au grow suivant
    apres = tomate.current_height
    assert apres < avant - 1e-6, (avant, apres)
    print(f"[taille] PASS — tomate taillée {avant:.1f} → {apres:.1f} cm")


def test_regression_non_procedurale():
    gs = _minimal_state(week=20)
    basilic = gs["tiles"][0].plants[1]
    basilic.advance_stage()
    basilic.retenir_hauteur()
    haut = basilic.current_height
    basilic.growth_factor = 0.5               # déficit : la vitesse tombe, pas la taille
    assert abs(basilic.current_height - haut) < 1e-9
    basilic.regress()                          # parties aériennes perdues
    assert basilic.current_height < haut - 1e-6, (haut, basilic.current_height)
    print(f"[régression] PASS — basilic {haut:.1f} → {basilic.current_height:.1f} cm")


def main():
    test_banc_ombre_et_dormance()
    test_taille_tomate()
    test_regression_non_procedurale()
    return 0


if __name__ == "__main__":
    sys.exit(main())
