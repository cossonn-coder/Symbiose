"""
SYMBIOSE — tests/test_niche_thermique.py
Niche thermique d'espèce + caractères en °C + plasticité (D139, sprint niche
thermique ②). Hors golden : plantes et EcoFields à conditions forcées.

Vérifie :
  - les limites effectives (`lim_gel`, `lim_froid`, `lim_chaud`, `lim_brul`) lues sur
    l'espèce, décalées par les gènes et par l'endurcissement / l'acclimatation ;
  - `heat_memory` monte sous une feuille chaude (soleil × soif) et pilote
    l'expression de `limite_chaud` ;
  - l'hérédité et le priming des trois caractères thermiques ;
  - le coût de la tolérance génétique (`cout_thermique`) ;
  - les 52 espèces du catalogue portent une niche explicite.

Usage (depuis data/code/) :
  python3 -m tests.test_niche_thermique
"""
import math
import sys

from world import Tile
from plants import Basil, Rye, CornSalad, Zucchini, Clover
from plants.genetics import EXPR_MAX, K_THERMO, ACCLIM_CHAUD_MAX
from plants.base.instance import PlantInstance
from fields import init_eco
from sim.engine import Engine
from sim.reproduction import heredite, child_expression

_results = []
SEED = 42


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'OK ' if cond else 'XX '} {name}" + (f" — {detail}" if detail else ""))


def _p(cls, genes=None):
    p = PlantInstance(plant_class=cls, position=(0, 0))
    p.genes = dict(genes or {})
    return p


def test_limites():
    print("\n[1] limites effectives : espèce + gènes + plasticité")
    b = _p(Basil)
    check("basilic neutre : lim_gel = −1 °C", b.lim_gel() == -1.0, f"{b.lim_gel()}")
    b.expression["rusticite_froid"] = EXPR_MAX
    check("basilic endurci : ne gagne rien (endurcissement_max 0)", b.lim_gel() == -1.0)
    check("basilic : lésion par le froid à 10 °C", b.lim_froid() == 10.0)
    s = _p(Rye)
    check("seigle tendre : −8 °C", s.lim_gel() == -8.0)
    s.expression["rusticite_froid"] = EXPR_MAX
    check("seigle endurci : −25 °C", abs(s.lim_gel() + 25.0) < 1e-9, f"{s.lim_gel()}")
    s.genes["rusticite_froid"] = 1.5
    check("rusticité +1,5 °C : −26,5 °C", abs(s.lim_gel() + 26.5) < 1e-9)
    check("seigle : pas de lésion sans gel (−∞)", s.lim_froid() == -math.inf)
    b2 = _p(Basil, {"limite_froid": 2.0})
    check("limite_froid +2 : lésion à 8 °C", b2.lim_froid() == 8.0)
    z = _p(Zucchini)
    base_c, base_b = z.lim_chaud(), z.lim_brul()
    z.genes["limite_chaud"] = 2.0
    check("limite_chaud relève lim_chaud et lim_brul",
          z.lim_chaud() == base_c + 2.0 and z.lim_brul() == base_b + 2.0)
    z.expression["limite_chaud"] = EXPR_MAX
    check(f"acclimatation chaude complète : +{ACCLIM_CHAUD_MAX} °C",
          abs(z.lim_brul() - (base_b + 2.0 + ACCLIM_CHAUD_MAX)) < 1e-9)
    check("expressed_gene d'un caractère en °C = génotype",
          z.expressed_gene("limite_chaud") == 2.0)


def test_heat_memory():
    print("\n[2] heat_memory monte sous une feuille chaude, pas à l'ombre fraîche")
    def lab(hum):
        tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
        eco = init_eco("T0", 6, 6, humidite=1.2, fertilite=1.2, microbiome=0.3)
        plant = tile.add_plant(CornSalad, 3, 3)
        gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
              "current_player": "j1", "week": 1, "log": []}
        eco.humidite.at_plot = lambda r, c, _h=hum: _h
        eco.lumiere.light_received = lambda p: 1.0
        return Engine(gs), tile, eco, plant
    eng, tile, eco, chaude = lab(0.0)          # sol sec, plein soleil
    eco.temperature.fill(25.0)
    for _ in range(20):
        eng._update_physiology(tile, eco, nebulosite=0.0)
    eng2, tile2, eco2, fraiche = lab(2.5)      # sol frais
    eco2.temperature.fill(10.0)
    for _ in range(20):
        eng2._update_physiology(tile2, eco2, nebulosite=1.0)
    check("mâche assoiffée au soleil : heat_memory > 0,3", chaude.heat_memory > 0.3,
          f"{chaude.heat_memory:.3f}")
    check("et limite_chaud s'exprime", chaude.expression["limite_chaud"] > 1.0)
    check("mâche au frais : heat_memory = 0", fraiche.heat_memory == 0.0)


def test_heredite():
    print("\n[3] hérédité et priming des caractères thermiques")
    mere = _p(Clover, {"rusticite_froid": 3.0, "limite_froid": 1.0, "limite_chaud": -2.0})
    pere = _p(Clover, {"rusticite_froid": 3.0, "limite_froid": 1.0, "limite_chaud": -2.0})
    enfants = [heredite(mere, pere, SEED, w)[0] for w in range(1, 120)]
    for g, v in (("rusticite_froid", 3.0), ("limite_froid", 1.0), ("limite_chaud", -2.0)):
        moy = sum(e[g] for e in enfants) / len(enfants)
        check(f"{g} hérité (moyenne ≈ {v})", abs(moy - v) < 0.4, f"{moy:.2f}")
    mere.expression["limite_chaud"] = EXPR_MAX
    check("priming de limite_chaud transmis",
          child_expression(mere)["limite_chaud"] > 1.0)


def test_cout():
    print("\n[4] coût de la tolérance génétique")
    p = _p(Clover)
    check("neutre : cout_thermique = 1", p.cout_thermique() == 1.0)
    p.genes = {"rusticite_froid": 2.0, "limite_froid": 1.0, "limite_chaud": 1.0}
    check("4 °C de tolérance : 1 − 4·K_THERMO",
          abs(p.cout_thermique() - (1.0 - 4 * K_THERMO)) < 1e-9)
    p.genes = {"rusticite_froid": -3.0}
    check("frileux : aucun gain ni coût", p.cout_thermique() == 1.0)
    p.genes = {"limite_chaud": 1.0}
    # D139 caractères vivants ① : rapatrié dans `cout_genetique` (même site moteur).
    check("cout_genetique intègre le coût thermique",
          abs(p.cout_genetique() - (1.0 - K_THERMO)) < 1e-12)


def test_catalogue():
    print("\n[5] chaque espèce du catalogue déclare sa niche")
    from plants.base.familles import PlantBase
    import plants.catalogue  # noqa: F401  (charge toutes les espèces)

    def sous(c):
        for s in c.__subclasses__():
            yield s
            yield from sous(s)
    especes = {s for s in sous(PlantBase) if "name" in s.__dict__}
    manquent = [s.__name__ for s in especes if "t_gel_tendre" not in s.__dict__]
    check(f"{len(especes)} espèces, toutes avec leur niche", not manquent, str(manquent))
    incoh = [s.__name__ for s in especes
             if not (s.t_gel_tendre < s.t_chaud_stress < s.t_brulure)]
    check("gel < stress chaud < brûlure", not incoh, str(incoh))


if __name__ == "__main__":
    test_limites()
    test_heat_memory()
    test_heredite()
    test_cout()
    test_catalogue()
    ok = sum(r for _, r in _results)
    print(f"\n{ok}/{len(_results)} OK")
    sys.exit(0 if ok == len(_results) else 1)
