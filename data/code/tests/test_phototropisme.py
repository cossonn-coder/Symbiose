"""
SYMBIOSE — tests/test_phototropisme.py
Test CIBLÉ du phototropisme directionnel (sprint maison, tronçon 3,
CONCEPTION_MAISON_OMBRE.md §4 + §7). Hors du golden smoke test (décision Q4) :
on vérifie ici le COMPORTEMENT (l'apex se penche vers le clair), pas un hash.

Contrats couverts (kickoff 03_phototropisme.md §critères) :
  1. gradient        — sous un gradient de lumière, l'apex se penche vers le clair ;
  2. suit le gradient — sens Est ↔ Ouest selon où est le clair (pas un biais fixe) ;
  3. uniforme        — en lumière homogène, l'apex reste droit (biais ≈ 0, piège §7) :
                       structure BIT-IDENTIQUE au cas sans LightField ;
  4. borné           — déviation ≤ MAX_PHOTOTROPISM_TILT/émission, jamais à plat
                       (z ≥ MIN_APEX_Z), direction unitaire ;
  5. paramétrable    — `phototropism_strength` MARQUÉ penche plus que SUBTIL (> uniforme) ;
  6. déterminisme    — même seed + même gradient → structures identiques.

Usage (depuis data/code/) :
  python3 -m tests.test_phototropisme
"""
import math

from plants import Basil, PlantInstance
from fields.light import LightField
import sim.growth as G

SEED = 0x5AB1057E
ROWS, COLS = 9, 9
POS = (4, 4)               # centre de la grille → marge pour pencher dans tous les sens
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


# --- profils d'intensité (sous-classes : n'override QUE la sensibilité) ------

class _Marked(Basil):
    phototropism_strength = 0.30   # défaut MARQUÉ


class _Subtle(Basil):
    phototropism_strength = 0.10   # comparaison maquette (tronçon 4)


# --- helpers ---------------------------------------------------------------

def _light(fn) -> LightField:
    """LightField dont la lumière-sol vaut fn(r,c) (gradient arbitraire de test)."""
    lf = LightField(ROWS, COLS)
    for r in range(ROWS):
        for c in range(COLS):
            lf.data[r][c] = fn(r, c)
    return lf


def _grow(cls, lf, n=30, week0=1):
    """Croissance isolée de n ticks (semaines en pleine saison → facteur 1.0)."""
    p = PlantInstance(plant_class=cls, position=POS)
    for k in range(n):
        G.grow_plant(p, SEED, week0 + k, lf)
    return p


def _mean_lean(plant) -> tuple:
    """Déplacement horizontal MOYEN des extrémités de segments vs collet (x=Est, y=Sud).
    Le jitter des latéraux s'annule en moyenne ; reste le penchant de l'axe."""
    cx, cy = plant.segments[0].base[0], plant.segments[0].base[1]
    xs = [s.base[0] + s.dir[0] * s.length_cm - cx for s in plant.segments]
    ys = [s.base[1] + s.dir[1] * s.length_cm - cy for s in plant.segments]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def _signature(plant):
    return [(s.parent, round(s.length_cm, 5),
             round(s.dir[0], 5), round(s.dir[1], 5), round(s.dir[2], 5),
             s.is_apex, s.has_bud) for s in plant.segments]


# --- gradients de test ------------------------------------------------------
# x = Est (col croissante), y = Sud (ligne croissante). Lumière bornée [0.15, 1].
_EAST    = lambda r, c: 0.15 + 0.10 * c           # clair à l'Est
_WEST    = lambda r, c: 0.15 + 0.10 * (COLS - 1 - c)
_UNIFORM = lambda r, c: 0.7


def test_uniform_reste_droit():
    """Lumière uniforme → biais nul → structure IDENTIQUE au cas sans LightField."""
    p_unif = _grow(_Marked, _light(_UNIFORM))
    p_none = _grow(_Marked, None)
    lean_x, lean_y = _mean_lean(p_unif)
    check("uniforme : apex reste droit (lean ≈ 0)",
          abs(lean_x) < 1e-9 and abs(lean_y) < 1e-9,
          f"lean=({lean_x:.2e},{lean_y:.2e})")
    check("uniforme : structure bit-identique au cas sans lumière (piège §7)",
          _signature(p_unif) == _signature(p_none))


def test_gradient_penche_vers_le_clair():
    """Gradient Est → l'apex se penche vers l'Est ; Ouest → vers l'Ouest (suit le clair)."""
    east = _grow(_Marked, _light(_EAST))
    west = _grow(_Marked, _light(_WEST))
    ex, ey = _mean_lean(east)
    wx, wy = _mean_lean(west)
    check("gradient Est : se penche vers l'Est (lean_x > 0)", ex > 2.0, f"lean_x={ex:.2f} cm")
    check("gradient Ouest : se penche vers l'Ouest (lean_x < 0)", wx < -2.0, f"lean_x={wx:.2f} cm")
    check("le biais SUIT le gradient (Est et Ouest opposés)", ex > 0 > wx,
          f"Est={ex:.2f} Ouest={wx:.2f}")


def test_intensite_parametrable():
    """MARQUÉ penche nettement plus que SUBTIL, qui penche plus que l'uniforme (≈0)."""
    marked = _mean_lean(_grow(_Marked, _light(_EAST)))[0]
    subtle = _mean_lean(_grow(_Subtle, _light(_EAST)))[0]
    check("marqué > subtil > 0 (paramètre produit 2 allures distinctes)",
          marked > subtle > 0.0, f"marqué={marked:.2f} subtil={subtle:.2f} cm")


def test_borne_jamais_a_plat():
    """_phototropic_bias : sortie unitaire, jamais à plat (z ≥ MIN_APEX_Z), bornée."""
    vert = (0.0, 0.0, 1.0)
    lf = _light(lambda r, c: 0.15 + 0.5 * c)      # gradient TRÈS fort vers l'Est
    out = G._phototropic_bias(vert, 225.0, 225.0, lf, strength=10.0)  # strength extrême
    norm = math.sqrt(out[0]**2 + out[1]**2 + out[2]**2)
    check("sortie unitaire", abs(norm - 1.0) < 1e-9, f"|out|={norm:.6f}")
    check("jamais à plat (z ≥ MIN_APEX_Z)", out[2] >= G.MIN_APEX_Z - 1e-9,
          f"z={out[2]:.3f} (plancher {G.MIN_APEX_Z})")
    check("penche bien vers le clair (Est, x > 0)", out[0] > 0.0, f"x={out[0]:.3f}")
    # déviation depuis la verticale bornée par le plancher de verticalité
    lean_angle = math.acos(max(-1.0, min(1.0, out[2])))
    max_lean = math.acos(G.MIN_APEX_Z)
    check("inclinaison bornée (≤ acos(MIN_APEX_Z))", lean_angle <= max_lean + 1e-9,
          f"lean={math.degrees(lean_angle):.1f}° ≤ {math.degrees(max_lean):.1f}°")


def test_deterministe():
    """Même seed + même gradient → structures rigoureusement identiques (philo #3)."""
    a = _grow(_Marked, _light(_EAST))
    b = _grow(_Marked, _light(_EAST))
    check("déterminisme (2× identiques)", _signature(a) == _signature(b))


def main():
    print("=== test_phototropisme — apex se penche vers la lumière ===")
    test_uniform_reste_droit()
    test_gradient_penche_vers_le_clair()
    test_intensite_parametrable()
    test_borne_jamais_a_plat()
    test_deterministe()
    n_ok = sum(1 for _, ok in _results if ok)
    n = len(_results)
    print(f"\n{n_ok}/{n} tests OK")
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
