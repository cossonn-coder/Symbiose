"""
SYMBIOSE — tests/test_croissance.py
Golden de la DYNAMIQUE INERTE de croissance procédurale (D29 réorienté,
tronçon 1). Distinct du golden ÉCOLOGIQUE (`tests/test_golden.py`) : ici on
vérifie le COMPORTEMENT de la structure de segments (sim/growth.py), pas un
hash de trajectoire.

À ce tronçon la structure est INERTE : elle pousse à côté, personne ne la lit
(height_at vient des stades) → le golden écologique doit rester INTACT. Ce test
exerce directement `grow_plant` sur des plantes isolées (pas besoin de l'engine)
et couvre les 5 contrats du kickoff §C :

  1. naissance     — 1 segment apex au collet ;
  2. croissance    — la structure grandit, l'apex DOMINE (peu de latéraux) ;
  3. débourrement  — décapité, des latéraux naissent puis la dominance tient ;
  4. bornage       — sur un long horizon, len sature ≤ MAX_SEGMENTS, du bois
                     tombe, jamais 0 (run éternel) ;
  5. déterminisme  — même seed + même position → structures identiques.

Usage (depuis data/code/) :
  python3 -m tests.test_croissance
"""
from collections import Counter

from plants import Tomato, PlantInstance
import sim.growth as G

SEED = 0x5AB1057E
POS = (2, 2)
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


# --- helpers ---------------------------------------------------------------

def _fresh():
    return PlantInstance(plant_class=Tomato, position=POS)


def _grow(plant, n, week0=1):
    for k in range(n):
        G.grow_plant(plant, SEED, week0 + k)


def _n_apex(plant):
    return sum(1 for s in plant.segments if s.is_apex)


def _branch_points(plant):
    c = Counter(s.parent for s in plant.segments if s.parent is not None)
    return sum(1 for v in c.values() if v >= 2)


def _height(plant):
    return max(s.base[2] + s.dir[2] * s.length_cm for s in plant.segments)


def _signature(plant):
    """Empreinte exacte de la structure (pour le déterminisme)."""
    return [(s.parent, round(s.length_cm, 5),
             round(s.dir[0], 5), round(s.dir[1], 5), round(s.dir[2], 5),
             s.is_apex, s.has_bud) for s in plant.segments]


# --- 1. Naissance : 1 segment apex au collet -------------------------------

def test_naissance():
    p = _fresh()
    segs = p.segments
    check("naissance: 1 seul segment", len(segs) == 1, f"len={len(segs)}")
    s = segs[0]
    check("naissance: apex actif", s.is_apex)
    check("naissance: collet (parent None)", s.parent is None)
    check("naissance: ancré au sol (z=0)", s.base[2] == 0.0,
          f"base={s.base}")
    check("naissance: vertical", s.dir == (0.0, 0.0, 1.0))


# --- 2. Croissance libre : grandit + dominance apicale ---------------------

def test_croissance_dominance():
    p = _fresh()
    h0 = _height(p)
    _grow(p, 20)
    check("croissance: nb segments ↑", len(p.segments) > 1,
          f"len={len(p.segments)}")
    check("croissance: hauteur ↑", _height(p) > h0,
          f"h={_height(p):.1f} (h0={h0:.1f})")
    # Dominance apicale : tant que l'auxine est haute, un seul apex et aucune
    # ramification (la flèche file droit).
    check("dominance: un seul apex", _n_apex(p) == 1, f"n_apex={_n_apex(p)}")
    check("dominance: aucune ramification précoce", _branch_points(p) == 0,
          f"branch={_branch_points(p)}")


# --- 3. Débourrement : décapitation → latéraux → dominance rétablie ---------

def test_debourrement():
    p = _fresh()
    _grow(p, 24)
    n_before = len(p.segments)
    check("débourrement: dominance avant décap", _n_apex(p) == 1)
    # Décapitation directe (l'apex perd son statut → chute d'auxine en aval).
    # (Pas encore `tailler`/le seam — tronçon 3.)
    for s in p.segments:
        if s.is_apex:
            s.is_apex = False
    G.grow_plant(p, SEED, 25)
    check("débourrement: des latéraux naissent", len(p.segments) > n_before,
          f"{n_before}→{len(p.segments)}")
    check("débourrement: apex relancés", _n_apex(p) >= 1,
          f"n_apex={_n_apex(p)}")
    n1 = _n_apex(p)
    _grow(p, 6, week0=26)
    # Dominance rétablie : chaque latéral redevient une flèche dominante dans son
    # sous-arbre → le nombre d'apex n'explose pas tick après tick.
    check("débourrement: dominance se rétablit (apex non croissants)",
          _n_apex(p) <= n1, f"{n1}→{_n_apex(p)}")
    check("débourrement: ramification présente", _branch_points(p) >= 1,
          f"branch={_branch_points(p)}")


# --- 4. Bornage : saturation + chute du vieux bois, jamais 0 ---------------

def test_bornage():
    p = _fresh()
    lens = []
    for k in range(500):
        G.grow_plant(p, SEED, 1 + k)
        lens.append(len(p.segments))
    check("bornage: plafonné ≤ MAX_SEGMENTS", max(lens) <= G.MAX_SEGMENTS,
          f"max={max(lens)} (MAX={G.MAX_SEGMENTS})")
    check("bornage: du vieux bois tombe (len décroît)",
          any(lens[i] < lens[i-1] for i in range(1, len(lens))))
    check("bornage: jamais éteint (run éternel, ≥1)", min(lens) >= 1,
          f"min={min(lens)}")
    check("bornage: a réellement poussé (pic > naissance)", max(lens) > 5,
          f"max={max(lens)}")


# --- 5. Déterminisme : même seed + position → mêmes structures -------------

def test_determinisme():
    p1, p2 = _fresh(), _fresh()
    for k in range(80):
        G.grow_plant(p1, SEED, 1 + k)
        G.grow_plant(p2, SEED, 1 + k)
    check("déterminisme: structures identiques (80 ticks)",
          _signature(p1) == _signature(p2),
          f"len {len(p1.segments)} vs {len(p2.segments)}")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Croissance procédurale (D29 réorienté, tronçon 1)")
    print("=" * 60)
    test_naissance()
    test_croissance_dominance()
    test_debourrement()
    test_bornage()
    test_determinisme()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
