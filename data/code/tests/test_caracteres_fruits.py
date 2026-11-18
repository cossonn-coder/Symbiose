"""
SYMBIOSE — tests/test_caracteres_fruits.py
Test ciblé du D139 caractères vivants ② — FRUITS ET COMESTIBILITÉ.

Ce que le golden re-figé ne prouve pas (il constate seulement une dérive), ce test
le garde :
  1. `taille_fruit` : gros fruits → moins de fruits, masse totale ≈ conservée ;
  2. manger une feuille de tomate COÛTE de la Vigueur, une feuille de basilic en rend
     (plus qu'une feuille neutre) ; un fruit de lierre coûte ; le geste reste gratuit ;
  3. la bouchée toxique laisse une ligne de log que le carnet relit ;
  4. la pression des ravageurs croît avec `appetence_feuille` (plancher 0,2) ;
  5. les neutres d'espèce de la conception §2.2 sont posés.

Lancement (depuis data/code/) : python3 -m tests.test_caracteres_fruits
"""

import sys

from world import Tile
from plants import (PlantInstance, AppleTree, Tomato, Basil, Clover, Fruit, Ivy,
                    Pepper)
from plants.base import Segment
from fields import init_eco
from sim import actions as ACT
from sim import vigueur as V
from sim import gout
from sim.engine.decompo import nouer
from sim.evenements import evenements
from sim.carnet import carnet_lire
from sim.journal import consigner
from sim.effects.perturbations import herbivory_pressure

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


def _pommier(taille):
    """Pommier mûr à 6 apex (sites de fruits), gène `taille_fruit` imposé."""
    tile = Tile(tile_id="TF", soil_type="terre", grid_rows=6, grid_cols=6)
    p = tile.add_plant(AppleTree, 3, 3)
    p.age_years = 6.0
    p.segments = [Segment(parent=None, base=(10.0 * i, 0.0, 100.0 + 30.0 * i),
                          dir=(0.0, 0.0, 1.0), length_cm=10.0, thickness_cm=0.5,
                          age_weeks=10, auxin=1.0, is_apex=True) for i in range(6)]
    p.genes = {"taille_fruit": taille}
    return p


def test_taille_nombre():
    print("\n[1] taille_fruit : gros fruits ou nombreux petits")
    n, m = {}, {}
    for g in (0.6, 1.0, 1.5):
        cohortes = nouer(_pommier(g), 1.0)
        n[g] = sum(f.nombre for f in cohortes)
        m[g] = sum(f.nombre * f.masse for f in cohortes)
    check("gros fruits → moins de fruits", n[1.5] < n[1.0] < n[0.6], str(n))
    check("masse totale ≈ conservée (±5 %)",
          all(abs(m[g] / m[1.0] - 1.0) < 0.05 for g in m),
          " ".join(f"{g}:{m[g]:.3f}" for g in m))


def _gs():
    gs = {"tiles": [], "eco": {}, "log": []}
    st = V.ensure_player(gs, "j")
    st["max_base"] = 1000.0
    st["courante"] = 100.0
    return gs, st


def _mure(cls, **genes):
    tile = Tile(tile_id="TG", soil_type="terre", grid_rows=6, grid_cols=6)
    p = tile.add_plant(cls, 2, 2)
    p.current_stage = len(cls.growth_stages) - 1
    p.vitalite = 1.0
    p.genes = dict(genes)
    return tile, p


def test_manger():
    print("\n[2] manger : le goût de l'organe fait la valeur, le geste reste gratuit")
    eco = init_eco("TG", 6, 6, fertilite=1.5, microbiome=1.0)
    gs, st = _gs()
    _, tomate = _mure(Tomato)
    v = ACT.manger(gs, "j", tomate, eco)
    check("feuille de tomate : perte de Vigueur", v < 0.0 and st["courante"] < 100.0,
          f"valeur={v:.2f} courante={st['courante']:.2f}")
    check("perte ∝ |appétence| (−0,6)",
          abs(v + gout.PERTE_TOXIQUE * ACT.HARVEST_GAIN_FULL * 0.6) < 1e-9)
    _, basilic = _mure(Basil)
    _, neutre = _mure(Basil, appetence_feuille=0.0)
    gs, st = _gs()
    vb, vn = ACT.manger(gs, "j", basilic, eco), ACT.manger(gs, "j", neutre, eco)
    check("feuille de basilic : gain, plus qu'une feuille neutre", vb > vn > 0.0,
          f"{vb:.2f} > {vn:.2f}")
    _, amer = _mure(Basil, appetence_feuille=-0.2)
    check("feuille amère (−0,2) : nourrit moins, sans perte",
          0.0 < ACT.manger(gs, "j", amer, eco) < vn)
    _, lierre = _mure(Ivy)
    lierre.fruits = [Fruit(0, 1.0, 0.05)]
    gs, st = _gs()
    vl = ACT.manger(gs, "j", lierre, eco, fruit_index=0)
    check("fruit de lierre : perte de Vigueur", vl < 0.0 and st["courante"] < 100.0,
          f"{vl:.2f}")
    _, poivron = _mure(Pepper)
    poivron.fruits = [Fruit(0, 1.0, 0.05)]
    check("fruit de poivron (feuille toxique) : gain",
          ACT.manger(gs, "j", poivron, eco, fruit_index=0) > 0.0)
    gs, st = _gs()
    gs["options"] = {"j": {"vigueur_infinie": True}}
    ACT.manger(gs, "j", tomate, eco)
    check("Vigueur infinie : la perte est masquée (seul point de débit)",
          st["courante"] == 100.0)


def test_carnet():
    print("\n[3] la bouchée toxique laisse une note au carnet")
    eco = init_eco("TG", 6, 6)
    tile, tomate = _mure(Tomato)
    gs, _ = _gs()
    gs["tiles"] = [tile]
    ACT.manger(gs, "j", tomate, eco)
    check("une ligne de goût écrite", len(gs["log"]) == 1 and gout.MARQUEUR in gs["log"][0],
          repr(gs["log"]))
    evs = evenements(gs["log"])
    check("événement relu : gout / toxique_feuille / tomate / TG",
          len(evs) == 1 and (evs[0].kind, evs[0].cause, evs[0].espece, evs[0].tile_id)
          == ("gout", "toxique_feuille", "tomate", "TG"), repr(evs))
    consigner(gs, "j", gs["log"], 3)
    notes = carnet_lire(gs, "j")
    check("note du carnet : mal au ventre",
          notes and "mal au ventre" in notes[-1]["texte"]
          and notes[-1]["concept"] == gout.CONCEPT, repr(notes[-1:]))
    _, basilic = _mure(Basil)
    gs["log"].clear()
    ACT.manger(gs, "j", basilic, eco)
    check("bouchée savoureuse : aucune note", gs["log"] == [])


def test_ravageurs():
    print("\n[4] la pression des ravageurs croît avec appetence_feuille")
    tile = Tile(tile_id="PF", soil_type="terre", grid_rows=4, grid_cols=4)
    eco = init_eco("PF", 4, 4, humidite=1.5, fertilite=1.0, microbiome=0.3,
                   soil_type="terre")
    eco.category_density = lambda cat, r, c: 0.5 if cat == "ravageur" else 0.0

    def pression(a):
        p = tile.add_plant(Clover, 1, 1)
        p.genes = {"appetence_feuille": a}
        muts = herbivory_pressure(p, tile, {}, eco)
        return float(muts[0].reason.split("p=")[1]) if muts else 0.0
    vals = {a: pression(a) for a in (-1.0, -0.6, 0.0, 0.6)}
    check("croît avec l'appétence", vals[-0.6] < vals[0.0] < vals[0.6], str(vals))
    check("plancher : un feuillage très toxique reste un peu brouté", vals[-1.0] > 0.0,
          f"{vals[-1.0]:.3f}")


def test_neutres():
    print("\n[5] neutres d'espèce (conception §2.2)")
    attendu = {(Tomato, "appetence_feuille"): -0.6, (Tomato, "appetence_fruit"): 0.7,
               (Ivy, "appetence_fruit"): -0.8, (Basil, "appetence_feuille"): 0.6,
               (Clover, "appetence_feuille"): 0.0, (Clover, "appetence_fruit"): 0.3}
    for (cls, g), v in attendu.items():
        p = PlantInstance(plant_class=cls, position=(0, 0))
        p.genes = {}
        check(f"{cls.__name__}.{g} = {v}", p.gene(g) == v, repr(p.gene(g)))


def main():
    test_taille_nombre()
    test_manger()
    test_carnet()
    test_ravageurs()
    test_neutres()
    print("\n" + "=" * 60)
    ok = sum(1 for _, c in _results if c)
    print(f"caractères vivants ② — fruits : {ok}/{len(_results)} OK")
    return 0 if ok == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
