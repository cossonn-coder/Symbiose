"""
SYMBIOSE — tests/test_bois_mort.py
Tests ciblés du tronçon ② du sprint « le sol qui respire » (D111) : une branche qui
meurt (élaguée par `_elaguer`) TOMBE en litière `bois` sous elle au lieu de disparaître.

  A. `grow_plant` renvoie les segments élagués (liste vide sinon).
  B. `deposer_bois_tombe` : ligneux → litière `bois` ∝ longueur × épaisseur², au plot
     de la verticale du milieu du segment, borné à la tuile.
  C. herbacée (non ligneuse) → rien.
  D. un pommier dont on force le plafond de segments dépose bien du bois (bout en bout).

Usage (depuis data/code/) :
  python3 -m tests.test_bois_mort
"""
import sys
from types import SimpleNamespace

from constants import PLOT_CM
from fields import init_eco
from fields.ecofields.constants import BOIS_MORT_PAR_CM3
from plants import PlantInstance
from plants.perennials import AppleTree
from plants.species.cultivees import Tomato
from sim.growth import grow_plant
from sim.engine.decompo import deposer_bois_tombe

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _bois(eco, r, c):
    return sum(p.masse for p in eco.litiere[r][c] if p.tissu == "bois")


def _seg(x, y, dx, dy, length, thick):
    return SimpleNamespace(base=(x, y, 100.0), dir=(dx, dy, 0.0),
                           length_cm=length, thickness_cm=thick)


# --- A. grow_plant renvoie une liste (vide sans élagage) ---
p = PlantInstance(plant_class=AppleTree, position=(2, 2))
t = grow_plant(p, 1, 1)
check("grow_plant renvoie une liste", isinstance(t, list), type(t))
check("rien d'élagué au 1er tick", t == [], len(t))

# --- B. dépôt ligneux, au plot du milieu, ∝ volume ---
eco = init_eco("nul", 4, 4)
seg = _seg(1.5 * PLOT_CM, 1.5 * PLOT_CM, 1.0, 0.0, 60.0, 2.0)   # milieu x=105 → c=2
m = deposer_bois_tombe(p, [seg], eco)
attendu = 60.0 * 2.0 ** 2 * BOIS_MORT_PAR_CM3
check("masse ∝ longueur × épaisseur²", abs(m - attendu) < 1e-12, f"{m} vs {attendu}")
check("dépôt au plot de la verticale du milieu (r=1, c=2)",
      abs(_bois(eco, 1, 2) - attendu) < 1e-12 and _bois(eco, 1, 1) == 0.0,
      f"(1,2)={_bois(eco, 1, 2)} (1,1)={_bois(eco, 1, 1)}")
hors = _seg(3.9 * PLOT_CM, -40.0, 1.0, 0.0, 200.0, 1.0)          # déborde → borné
deposer_bois_tombe(p, [hors], eco)
check("branche hors tuile → plot de bordure (0, 3)", _bois(eco, 0, 3) > 0.0,
      _bois(eco, 0, 3))

# --- C. herbacée → rien ---
eco2 = init_eco("nul", 4, 4)
tom = PlantInstance(plant_class=Tomato, position=(1, 1))
check("herbacée (tomate) : aucun dépôt",
      deposer_bois_tombe(tom, [seg], eco2) == 0.0 and _bois(eco2, 1, 2) == 0.0)
check("liste vide : aucun dépôt", deposer_bois_tombe(p, [], eco2) == 0.0)

# --- D. bout en bout : plafond de segments forcé sur un pommier ---
class PommierBride(AppleTree):
    max_segments = 2

arbre = PlantInstance(plant_class=PommierBride, position=(2, 2))
eco3 = init_eco("nul", 4, 4)
total = 0.0
for w in range(1, 157):
    total += deposer_bois_tombe(arbre, grow_plant(arbre, 1, w), eco3)
somme = sum(_bois(eco3, r, c) for r in range(4) for c in range(4))
check("pommier bridé : du bois tombe au sol", total > 0.0, f"{total:.4f}")
check("conservation : litière bois = masse déposée", abs(somme - total) < 1e-9,
      f"{somme:.6f} vs {total:.6f}")

n_ok = sum(ok for _, ok in _results)
print(f"\n{n_ok}/{len(_results)} OK")
sys.exit(0 if n_ok == len(_results) else 1)
