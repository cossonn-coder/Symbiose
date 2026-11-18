"""
SYMBIOSE — tests/test_caracteres_sol.py
Test ciblé du D139 caractères vivants ④ — SOL ET EXPANSION.

Ce que le golden re-figé ne prouve pas (il constate seulement une dérive), ce test
le garde, un caractère après l'autre :
  1. `vigueur_clonale` : plus de ramets, plus loin ; moins de graines (clonales
     seulement) ; le ramet hérite des gènes et du F de sa mère ;
  2. `portee_graine` : la graine anémochore se pose plus loin sous le vent ; son
     pool lève moins (graine légère) ; barochore : gène non lu ;
  3. `fixation_azote` : l'azote injecté suit le gène, et reste freiné en sol riche ;
  4. `allelopathie` : la quantité émise suit le gène ;
  5. `mycorhization` : plus de P prélevé sous un même réseau ; le gain de nutrition
     n'existe qu'en sol pauvre ; le prix (`cout_genetique`) est payé partout.

Lancement (depuis data/code/) : python3 -m tests.test_caracteres_sol
"""

import math
import sys

from world import Tile
from plants import PlantInstance, Bean, Sunflower, Tomato, Clover
from plants.species.sauvages import Raspberry
from plants.species.adventices import Taraxacum
from plants.caracteres import CARACTERES
from fields import init_eco
from fields.seedbank import SeedBank
from sim.clonal import emettre_ramets
from sim.effects.resolution import resolve
from sim.engine.mortalite import MortaliteMixin
from sim.nutrition_plante import facteur_nutrition

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


NOMS = ["vigueur_clonale", "portee_graine", "fixation_azote", "allelopathie",
        "mycorhization"]


def test_registre():
    print("\n[0] cinq caractères en queue du registre")
    noms = list(CARACTERES)[-5:]
    check("ordre en queue", noms == NOMS, str(noms))
    p = PlantInstance(plant_class=Clover, position=(0, 0))
    p.genes = {}
    check("neutres 1,0", all(p.gene(g) == 1.0 for g in noms))


# --- 1. vigueur_clonale --------------------------------------------------------

def _ramets(g):
    """Ramets d'un framboisier mûr sur deux étés, gène `vigueur_clonale` = g :
    (nombre, distance moyenne en cm, dernier ramet)."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=20, grid_cols=20)
    eco = init_eco("T0", 20, 20, humidite=1.0, fertilite=1.0, microbiome=0.3)
    mere = tile.add_plant(Raspberry, 10, 10)
    mere.current_stage = len(Raspberry.growth_stages) - 1
    mere.genes = {"vigueur_clonale": g, "hauteur": 1.1}
    mere.F = 0.25
    eco.lumiere.at_plot = lambda r, c: 0.9
    eco.couverture_sol.at_plot = lambda r, c: 0.0
    x0, y0 = mere.x_cm, mere.y_cm
    dist, dernier = [], None
    for wk in list(range(14, 39)) + list(range(66, 91)):
        avant = set(map(id, tile.plants))
        emettre_ramets(tile, eco, 42, wk)
        for p in tile.plants:
            if id(p) not in avant:
                dist.append(math.hypot(p.x_cm - x0, p.y_cm - y0))
                dernier = p
        mere.stress_memory = 0.0
    return len(dist), (sum(dist) / len(dist) if dist else 0.0), dernier, mere


def test_clonal():
    print("\n[1] vigueur_clonale : cadence, portée, prix en graines")
    n_f, d_f, _, _ = _ramets(0.6)
    n_v, d_v, ramet, mere = _ramets(1.5)
    check("plus de ramets", n_v > n_f, f"{n_v} > {n_f}")
    check("ramets plus loin", d_v > d_f, f"{d_v:.0f} > {d_f:.0f} cm")
    check("le ramet hérite gènes et F", ramet is not None
          and ramet.genes == mere.genes and ramet.F == mere.F)
    p = PlantInstance(plant_class=Raspberry, position=(0, 0))
    p.genes = {"vigueur_clonale": 1.5}
    check("clonale : graines ÷ gène",
          abs(p.taux_graines() - Raspberry.reproduction_rate / 1.5) < 1e-12)
    t = PlantInstance(plant_class=Tomato, position=(0, 0))
    t.genes = {"vigueur_clonale": 1.5}
    check("non clonale : gène non lu", t.taux_graines() == Tomato.reproduction_rate)


# --- 2. portee_graine ----------------------------------------------------------

class _Moteur(MortaliteMixin):
    def __init__(self, gs):
        self.game_state = gs


class _PissenlitFecond(Taraxacum):
    reproduction_rate = 1.0          # porte de hash toujours ouverte (test)


def _plot_depose(g):
    tile = Tile(tile_id="TP", soil_type="terre", grid_rows=20, grid_cols=20)
    eco = init_eco("TP", 20, 20, humidite=1.0, fertilite=1.0, microbiome=0.3)
    mere = tile.add_plant(_PissenlitFecond, 10, 2)
    mere.current_stage = len(Taraxacum.growth_stages) - 1
    mere.genes = {"portee_graine": g}
    mere.fecondation = 1.0
    gs = {"tiles": [tile], "eco": {"TP": eco}, "log": [], "seed": 42, "week": 39}
    # Vent venu de l'ouest (wind_dir = π) → graines vers l'est (colonnes croissantes).
    _Moteur(gs)._reproduction(tile, eco, 39, wind_dir=math.pi, wind_force=1.0)
    for r in range(20):
        for c in range(20):
            if eco.seed_bank.species[r][c].get(_PissenlitFecond):
                return r, c
    return None


def test_portee():
    print("\n[2] portee_graine : vol plus long, levée plus rare")
    court, loin = _plot_depose(0.6), _plot_depose(1.5)
    check("la graine légère se pose plus loin sous le vent",
          court is not None and loin is not None and loin[1] > court[1],
          f"{loin} vs {court}")
    sb = SeedBank(1, 2)
    sb.add_species(0, 0, Taraxacum, 0.5, {"portee_graine": 1.0})
    sb.add_species(0, 1, Taraxacum, 0.5, {"portee_graine": 1.5})
    check("anémochore : pool léger lève moins",
          sb.densite_levable(0, 1, Taraxacum) < sb.densite_levable(0, 0, Taraxacum))
    sb2 = SeedBank(1, 1)
    sb2.add_species(0, 0, Clover, 0.5, {"portee_graine": 1.5})
    check("barochore : gène non lu",
          sb2.densite_levable(0, 0, Clover) == sb2.species_density(0, 0, Clover))


# --- 3/4. fixation_azote, allelopathie (effets inject_field) -------------------

def _injecte(cls, variable, gene, g, n_sol=0.0):
    tile = Tile(tile_id="TA", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("TA", 6, 6, humidite=1.0, fertilite=1.0, microbiome=0.3)
    for r in range(6):
        for c in range(6):
            eco.n.set(r, c, n_sol)
    p = tile.add_plant(cls, 3, 3)
    p.genes = {gene: g}
    gs = {"tiles": [tile], "eco": {"TA": eco}, "log": [], "seed": 42, "week": 10}
    total = 0.0
    for eff in cls.family_effects:
        if eff.get("variable") == variable:
            for m in resolve(eff, p, tile, gs, "weekly"):
                total += m.amount
    return total


def test_fixation():
    print("\n[3] fixation_azote : × gène, freinée en sol riche")
    bas, haut = (_injecte(Bean, "n", "fixation_azote", g) for g in (0.7, 1.4))
    check("azote injecté ∝ gène", haut > bas > 0.0 and abs(haut / bas - 2.0) < 1e-9,
          f"{haut:.4f} / {bas:.4f}")
    riche = _injecte(Bean, "n", "fixation_azote", 1.4, n_sol=1.2)
    check("freinée en sol riche", riche < 0.3 * haut, f"{riche:.4f} < {haut:.4f}")


def test_allelopathie():
    print("\n[4] allelopathie : × gène")
    bas, haut = (_injecte(Sunflower, "allelopathie", "allelopathie", g)
                 for g in (0.7, 1.4))
    check("émission ∝ gène", haut > bas > 0.0 and abs(haut / bas - 2.0) < 1e-9,
          f"{haut:.4f} / {bas:.4f}")


# --- 5. mycorhization ----------------------------------------------------------

def _p_preleve(g):
    e = init_eco("myco", 1, 1, humidite=2.0, microbiome=0.0, fertilite=3.0)
    e.ph.set(0, 0, 6.5)
    e.mycelium.set(0, 0, 0.5)
    return e.plant_uptake(0, 0, 2, mycorhization=g).get("p", 0.0)


def _nutrition(g, p_sol):
    tile = Tile(tile_id="TM", soil_type="terre", grid_rows=3, grid_cols=3)
    eco = init_eco("TM", 3, 3, humidite=1.0, fertilite=1.0, microbiome=0.3,
                   soil_type="terre")
    for r in range(3):
        for c in range(3):
            eco.p.set(r, c, p_sol)
            eco.mycelium.set(r, c, 0.6)
    p = tile.add_plant(Tomato, 1, 1)
    p.current_stage = 1                       # semis-jeune : le P pèse
    p.genes = {"mycorhization": g}
    return facteur_nutrition(p, eco)


def test_mycorhization():
    print("\n[5] mycorhization : P relayé, utile en sol pauvre seulement, payé")
    check("plus de P sous le même réseau", _p_preleve(1.4) > _p_preleve(0.7),
          f"{_p_preleve(1.4):.4f} > {_p_preleve(0.7):.4f}")
    pauvre = (_nutrition(0.7, 0.05), _nutrition(1.4, 0.05))
    riche = (_nutrition(0.7, 3.0), _nutrition(1.4, 3.0))
    check("sol pauvre : nutrition meilleure", pauvre[1] > pauvre[0],
          f"{pauvre[1]:.3f} > {pauvre[0]:.3f}")
    check("sol riche : aucun gain", riche[0] == riche[1] == 1.0, str(riche))
    p = PlantInstance(plant_class=Tomato, position=(0, 0))
    p.genes = {"mycorhization": 1.3}
    check("prix en sucre (cout_genetique < 1)", p.cout_genetique() < 1.0,
          f"{p.cout_genetique():.3f}")


def main():
    test_registre()
    test_clonal()
    test_portee()
    test_fixation()
    test_allelopathie()
    test_mycorhization()
    print("\n" + "=" * 60)
    ok = sum(1 for _, c in _results if c)
    print(f"caractères vivants ④ — sol et expansion : {ok}/{len(_results)} OK")
    return 0 if ok == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
