"""
SYMBIOSE — tests/test_fecondation.py
Test ciblé du D139 ①b — LA FLEUR VISITÉE FAIT DES GRAINES (conception §6.3).

📖 Ce que le golden re-figé ne prouve pas, ce test le garde :
  1. `feconder` : mode `self` → 1 ; sans pollen → `a` (gène `autofecondation`) ;
     croît avec `pollen_recu` et tend vers 1 ; remet `pollen_recu` à 0 et désarme ;
  2. la fanaison (`_tick_fruits`) fige la fécondation d'une HERBACÉE qui a fleuri ;
  3. une plante qui n'a pas fleuri (`fecondation = 0`) ne dépose rien à la banque ;
  4. sans pollen, toutes les graines sont autofécondées (F de l'enfant > 0).

Lancement (depuis data/code/) : python3 -m tests.test_fecondation
"""

import sys

from plants import PlantInstance, Phacelia, Fig, Borage
from world import Tile
from fields import init_eco
from sim.engine import Engine
from sim.engine.decompo import feconder, SEUIL_FLEURI
from sim.engine.fin_de_cycle import semer_fin_de_cycle
from sim.reproduction import heredite

SEED = 42
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


def _plante(cls, pollen=0.0, pos=(1, 1), **genes):
    p = PlantInstance(plant_class=cls, position=pos)
    p.genes.update(genes)
    p.pollen_recu = pollen
    p.a_fleuri = True
    return p


def test_feconder():
    print("\n[1] feconder : a + (1 − a)·g(pollen)")
    check("mode self → 1 (figuier)", Fig.pollination_mode == "self"
          and feconder(_plante(Fig)) == 1.0)
    p0 = _plante(Phacelia)
    a = p0.gene("autofecondation")
    check("sans pollen → a", abs(feconder(p0) - a) < 1e-12, f"a={a:.3f}")
    vals = [feconder(_plante(Phacelia, x)) for x in (0.5, 2.0, 10.0, 1e6)]
    check("croît avec pollen_recu", all(u < v for u, v in zip(vals, vals[1:])),
          " ".join(f"{v:.3f}" for v in vals))
    check("tend vers 1", 0.999 < vals[-1] <= 1.0)
    p = _plante(Phacelia, 3.0)
    feconder(p)
    check("pollen_recu remis à 0, désarmée", p.pollen_recu == 0.0 and not p.a_fleuri)


def test_fanaison_herbacee():
    print("\n[2] la fanaison d'une herbacée fige sa fécondation")
    tile = Tile(tile_id="T0", soil_type="terre")
    eco = init_eco("T0", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "joueur_1", "week": 1, "log": []}
    eng = Engine(gs)
    p = tile.add_plant(Phacelia, 2, 2)
    p.pollen_recu = 2.0
    p.floraison = SEUIL_FLEURI + 0.1
    eng._tick_fruits(tile, eco, 20)
    check("armée en pleine fleur, pas encore fécondée", p.a_fleuri and p.fecondation == 0.0)
    p.floraison = 0.1
    eng._tick_fruits(tile, eco, 21)
    a = p.gene("autofecondation")
    check("fanée → fecondation figée, pollen à 0",
          p.fecondation > a and p.pollen_recu == 0.0, f"fec={p.fecondation:.3f}")


def test_pas_fleurie_pas_de_graine():
    print("\n[3] une plante non fleurie ne dépose rien")
    tile = Tile(tile_id="T0", soil_type="terre")
    eco = init_eco("T0", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
    p = tile.add_plant(Borage, 2, 2)
    dens = lambda: eco.seed_bank.species_density(2, 2, Borage)
    avant = dens()
    semer_fin_de_cycle(p, tile, eco, SEED, 30)
    check("fecondation 0 → banque-sol inchangée", dens() == avant, f"{dens():.4f}")
    p.fecondation = 1.0
    semer_fin_de_cycle(p, tile, eco, SEED, 30)
    check("fecondation 1 → la banque reçoit des graines", dens() > avant, f"{dens():.4f}")


def test_sans_pollen_autofecondees():
    print("\n[4] sans pollen, toutes les graines sont autofécondées")
    mere = _plante(Phacelia, 0.0, pos=(1, 1))
    pere = _plante(Phacelia, 0.0, pos=(1, 2))
    feconder(mere)
    Fs = [heredite(mere, pere, SEED, w)[1] for w in range(1, 80)]
    check("F > 0 pour chaque graine", all(F > 0.0 for F in Fs), f"n={len(Fs)}")
    mere.fecondation = 1.0             # très visitée : la part croisée revient
    n_croise = sum(heredite(mere, pere, SEED, w)[1] == 0.0 for w in range(1, 80))
    check("fécondation pleine → des graines croisées", n_croise > 0, f"{n_croise}/79")


def main():
    test_feconder()
    test_fanaison_herbacee()
    test_pas_fleurie_pas_de_graine()
    test_sans_pollen_autofecondees()
    ok = sum(r for _, r in _results)
    print(f"\n{ok}/{len(_results)} OK")
    return 0 if ok == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
