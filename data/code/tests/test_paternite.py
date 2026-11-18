"""
SYMBIOSE — tests/test_paternite.py
Test ciblé du D139 ①c — LE PÈRE EST CELUI DONT LE POLLEN ARRIVE (conception §6.3).

📖 Principe de Bateman : une fleur attirante, plus visitée, exporte plus de pollen et
engendre plus de graines chez ses voisines. Ce test garde :
  1. butineurs : `sample_foragers` rend une recharge par visite ; le crédit
     `pollen_donne` croît avec les visites et se partage ∝ poids floral ;
  2. vent : une source anémophile au vent d'une cible est créditée de ce qu'elle
     envoie, la cible de sa part auto-anémophile ;
  3. `find_father` : tiré ∝ `pollen_donne` (le plus gros donneur gagne le plus
     souvent), poids nuls → le plus proche, hors portée → jamais tiré ;
  4. remise à 0 de `pollen_donne` en semaine 1 (`_tick_floraison`).

Lancement (depuis data/code/) : python3 -m tests.test_paternite
"""

import sys
from types import SimpleNamespace

from plants import PlantInstance, Phacelia
from plants.species.prairie import Dactyle
from fields import sample_foragers, ForagerParams
from sim.engine.butineurs import _apply_deposits
from sim.engine.anemophilie import AnemophilieMixin
from sim.engine.floraison import FloraisonMixin
from sim.reproduction import find_father

SEED = 42
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


def _mure(cls, pos=(2, 2), dx=0.0, donne=0.0):
    """Plante en âge de fleurir, décalée de `dx` cm, crédit mâle `donne`."""
    p = PlantInstance(plant_class=cls, position=pos)
    p.current_stage = len(cls.growth_stages) - 1
    p.x_cm += dx
    p.pollen_donne = donne
    return p


class _Plat:
    """Champ uniforme (vent ou température) minimal."""
    def __init__(self, v):
        self.v = v

    def at_plot(self, r, c):
        return self.v


class _Eco:
    def __init__(self, dens=1.0, vent=0.0, temp=10.0):
        self._dens = dens
        self.vent = _Plat(vent)
        self.temperature = _Plat(temp)

    def pollinator_density(self, r, c):
        return self._dens


def test_butineurs():
    print("\n[1] butineurs : recharge → pollen_donne ∝ visites et poids floral")
    field = SimpleNamespace(spec=SimpleNamespace(salt=500, name="abeille"),
                            rows=3, cols=3, data=[[1.0] * 3 for _ in range(3)])
    grids = {"Phacélie": [[1.0] * 3 for _ in range(3)]}
    params = ForagerParams(n_max=4, substeps=5, perception=1, deposit=0.5, recharge=0.5)
    _, deposits, recharges = sample_foragers(field, grids, params, SEED, 20)
    check("une recharge par visite (plus que de dépôts)",
          len(recharges) > len(deposits) > 0, f"{len(recharges)} vs {len(deposits)}")
    check("recharge = params.recharge", all(q == 0.5 for *_, q in recharges))
    a, b = _mure(Phacelia), _mure(Phacelia)
    plants_at = {"Phacélie": {(2, 2): [(a, 3.0), (b, 1.0)]}}
    _apply_deposits([("Phacélie", 2, 2, 0.5)], plants_at, None, "pollen_donne")
    check("partage ∝ poids floral (3:1)", abs(a.pollen_donne - 3 * b.pollen_donne) < 1e-12
          and abs(a.pollen_donne + b.pollen_donne - 0.5) < 1e-12)
    avant = a.pollen_donne
    _apply_deposits([("Phacélie", 2, 2, 0.5)] * 3, plants_at, None, "pollen_donne")
    check("croît avec les visites", a.pollen_donne > avant)
    check("pollen_recu intact", a.pollen_recu == 0.0 and b.pollen_recu == 0.0)


def test_vent():
    print("\n[2] vent : la source au vent est créditée de ce qu'elle envoie")
    cible = _mure(Dactyle)
    src = _mure(Dactyle, dx=100.0)          # à l'est de la cible
    loin = _mure(Dactyle, dx=-100.0)        # sous le vent : n'envoie rien à la cible
    for p in (cible, src, loin):
        p.floraison = 1.0
    tile = SimpleNamespace(plants=[cible, src, loin])
    AnemophilieMixin()._tick_anemophilie(tile, _Eco(vent=0.5), 0.0, 1.0)  # vent d'est
    check("source au vent créditée", src.pollen_donne > 0.0, f"{src.pollen_donne:.3f}")
    check("le plus en amont donne le plus", src.pollen_donne > loin.pollen_donne,
          f"amont={src.pollen_donne:.3f} aval={loin.pollen_donne:.3f}")
    check("Σ donné = Σ reçu (rien ne se perd au crédit)",
          abs(sum(p.pollen_donne for p in tile.plants)
              - sum(p.pollen_recu for p in tile.plants)) < 1e-9)


def test_find_father():
    print("\n[3] find_father : loterie ∝ pollen_donne × (1 − d²/R²)")
    eco, tile = _Eco(dens=1.0), SimpleNamespace()
    gagne = {"fort": 0, "faible": 0}
    for i in range(200):
        mere = _mure(Phacelia, pos=(i % 10, i // 10))
        fort = _mure(Phacelia, pos=mere.position, dx=40.0, donne=3.0)
        faible = _mure(Phacelia, pos=mere.position, dx=-40.0, donne=1.0)
        pere = find_father(mere, [mere, fort, faible], tile, eco, SEED, 30 + i % 7)
        gagne["fort" if pere is fort else "faible"] += 1
    part = gagne["fort"] / 200
    check("le gros donneur gagne ~3/4", 0.65 < part < 0.85, f"part={part:.2f} [n=200]")
    mere = _mure(Phacelia)
    pres = _mure(Phacelia, dx=30.0)
    loin = _mure(Phacelia, dx=80.0)
    check("poids nuls → le plus proche",
          find_father(mere, [mere, loin, pres], tile, eco, SEED, 30) is pres)
    hors = _mure(Phacelia, dx=10_000.0, donne=1e6)
    tires = {id(find_father(mere, [mere, pres, hors], tile, eco, SEED, w))
             for w in range(52)}
    check("hors portée jamais tiré", id(hors) not in tires)


def test_remise_a_zero():
    print("\n[4] pollen_donne remis à 0 en semaine 1")
    p = _mure(Phacelia, donne=5.0)
    tile = SimpleNamespace(plants=[p])
    FloraisonMixin()._tick_floraison(tile, _Eco(), 20)
    check("gardé en cours d'année", p.pollen_donne == 5.0)
    FloraisonMixin()._tick_floraison(tile, _Eco(), 1)
    check("remis à 0 en semaine 1", p.pollen_donne == 0.0)


def main():
    test_butineurs()
    test_vent()
    test_find_father()
    test_remise_a_zero()
    ok = sum(1 for _, c in _results if c)
    print(f"\n{ok}/{len(_results)} OK")
    return 0 if ok == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
