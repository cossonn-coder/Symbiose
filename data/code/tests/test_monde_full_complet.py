"""
SYMBIOSE — tests/test_monde_full_complet.py
GARDE-FOU PERMANENT du monde de jeu (D140 C, départ du jardin ③) : catalogue ⊂ monde
`full`. Toute espèce ajoutée au catalogue doit entrer dans `sim/monde_complet.PLACEMENTS`
(règle « monde full = tout le catalogue », Nico 2026-11-18).

  A. Chaque espèce de PLANT_CATALOGUE ∪ PERENNIAL_CATALOGUE a au moins un pied VIVANT
     et MATURE (`is_seed_bearing`) à l'init du monde `full` — et de `propre` (même monde).
  B. Ouverture en semaine 10 (après les saints de glace) ; arbres à l'âge de leur
     première fructification (au moins 11 ans) ; graines déjà semées, dont une tendre.
  C. La table de placement ne pose rien sur un plot déjà occupé ni hors tuile.

Golden non concerné (le smoke ne passe jamais par ce monde).
Usage (depuis data/code/) : python3 -m tests.test_monde_full_complet
"""
import contextlib
import io
from collections import Counter

from plants import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from plants.perennials import PerennialWoody
from sim.monde_complet import (especes_matures, SEMAINE_OUVERTURE, AGE_ARBRES_DEMO,
                               PLACEMENTS)
from tools.simserver.server import SimServer

_results = []
TENDRES = {"tomate", "poivron", "basilic", "haricot", "courgette"}


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


def _monde(config):
    srv = SimServer()
    with contextlib.redirect_stdout(io.StringIO()):
        rep = srv.cmd_init({"config": config, "seed": 42})
    assert rep["ok"], rep
    return srv.engine.game_state


def test_catalogue_complet():
    for config in ("full", "propre"):
        print(f"\n[A] catalogue ⊂ monde {config}")
        matures = especes_matures(_monde(config)["tiles"])
        for cle in sorted(set(PLANT_CATALOGUE) | set(PERENNIAL_CATALOGUE)):
            if cle not in matures:
                check(f"{config} : {cle}", False,
                      f"ajouter {cle} au monde full (sim/monde_complet.PLACEMENTS)")
        check(f"{config} : les {len(PLANT_CATALOGUE) + len(PERENNIAL_CATALOGUE)} "
              "espèces sont présentes et mûres",
              set(PLANT_CATALOGUE) | set(PERENNIAL_CATALOGUE) <= matures)


def test_ouverture():
    print("\n[B] ouverture")
    gs = _monde("full")
    check("départ en semaine 10", gs["week"] == SEMAINE_OUVERTURE == 10, gs["week"])
    arbres = [p for t in gs["tiles"] for p in t.plants
              if issubclass(p.plant_class, PerennialWoody)]
    jeunes = [(p.name, p.age_years) for p in arbres
              if p.age_years < max(AGE_ARBRES_DEMO, p.plant_class.maturity_years)]
    check("arbres à l'âge de leur 1ʳᵉ fructification", not jeunes, jeunes)
    grains = [g.species for t in gs["tiles"] for lot in t.grains_en_attente.values()
              for g in lot]
    check("graines déjà semées, dont une tendre",
          len(grains) >= 3 and bool(TENDRES & set(grains)), grains)


def test_plots_libres():
    print("\n[C] placements sur plots libres")
    gs = _monde("full")
    par_id = {t.tile_id: t for t in gs["tiles"]}
    hors = [(cle, tu, r, c) for cle, tu, r, c in PLACEMENTS
            if not par_id[tu].is_valid_plot(r, c)]
    check("aucun placement hors tuile", not hors, hors)
    doubles = [(t.tile_id, pos) for t in gs["tiles"]
               for pos, n in Counter(p.position for p in t.plants).items() if n > 1]
    check("aucun plot doublement planté à l'init", not doubles, doubles)


if __name__ == "__main__":
    test_catalogue_complet()
    test_ouverture()
    test_plots_libres()
    ok = sum(1 for _, r in _results if r)
    print(f"\n{ok}/{len(_results)} OK")
    raise SystemExit(0 if ok == len(_results) else 1)
