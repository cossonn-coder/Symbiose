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

from plants import Tomato, Basil, PlantInstance
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


# --- 6. Allure d'empreinte (tronçon 2) : la TOMATE migrée lit la structure -----
#
# La tomate est la 1re espèce `procedural_growth` : son empreinte
# (height_at/canopy_radius_at/root_radius_at) est DÉRIVÉE de la structure (§G), plus
# des stades. On valide l'ALLURE en croissance libre (semaine d'été fixe pour
# écarter le ralenti hivernal) : la flèche monte MONOTONIQUEMENT de ~3 cm vers son
# gabarit (~150 cm), la couronne s'élargit dans l'enveloppe, le tout déterministe.
# Au-delà du pic, la plante S'ÉTALE (auxine relâchée avec l'âge, §D.1) — on ne teste
# donc la monotonie QUE sur la phase de montée (jusqu'au pic).

H_GABARIT = 150.0   # Tomato.max_height_cm
FHW       = 18.0    # Tomato.foliage_halfwidth (couronne minimale, flèche droite)
CR_ENV    = FHW + 32.0   # enveloppe de couronne = foliage_halfwidth + max_extent_cm


def _free_growth(plant, n, week=20):
    """Croissance libre déterministe (été fixe, pleine vigueur) ; renvoie les
    trajectoires d'empreinte (hauteur, rayon de couronne)."""
    plant.growth_factor = 1.0
    hs, crs = [], []
    for _ in range(n):
        G.grow_plant(plant, SEED, week)
        hs.append(Tomato.height_at(plant))
        crs.append(Tomato.canopy_radius_at(plant))
    return hs, crs


def test_allure_tomate():
    p = _fresh()
    hs, crs = _free_growth(p, 80)
    peak = max(range(len(hs)), key=lambda i: hs[i])
    # Départ bas (jeune flèche) puis montée jusqu'au gabarit.
    check("allure: départ bas (~3 cm)", hs[0] < 10, f"h0={hs[0]:.1f}")
    check("allure: hauteur monte vers le gabarit (~150 cm)",
          140 <= hs[peak] <= H_GABARIT + 6, f"pic={hs[peak]:.1f}@t{peak+1}")
    check("allure: jamais au-dessus du gabarit", max(hs) <= H_GABARIT + 6,
          f"max={max(hs):.1f}")
    check("allure: montée monotone (jusqu'au pic)",
          all(hs[i] >= hs[i-1] - 1e-9 for i in range(1, peak + 1)))
    # Couronne : non nulle dès le départ (foliage_halfwidth), s'élargit dans l'enveloppe.
    check("allure: couronne non nulle au départ", abs(crs[0] - FHW) < 1e-6,
          f"cr0={crs[0]:.1f}")
    # +overshoot : l'apex latéral se retire APRÈS avoir dépassé max_extent d'un pas
    # d'élongation (la couronne peut donc excéder l'enveloppe nominale de ~1 tick).
    check("allure: couronne dans l'enveloppe", FHW - 1e-6 <= max(crs) <= CR_ENV + G.GROWTH_SPEED,
          f"crmax={max(crs):.1f} (env={CR_ENV:.0f}+{G.GROWTH_SPEED:.0f})")
    check("allure: couronne monotone (jusqu'au pic)",
          all(crs[i] >= crs[i-1] - 1e-9 for i in range(1, peak + 1)))
    # root_radius dérivé (= PROC_ROOT_RATIO · couronne).
    check("allure: rayon racinaire dérivé de la couronne",
          abs(Tomato.root_radius_at(p) - Tomato.canopy_radius_at(p)) < 1e-6)


def test_allure_determinisme():
    p1, p2 = _fresh(), _fresh()
    h1, c1 = _free_growth(p1, 60)
    h2, c2 = _free_growth(p2, 60)
    check("allure: empreinte déterministe (60 ticks)", h1 == h2 and c1 == c2,
          f"hfin {h1[-1]:.1f} vs {h2[-1]:.1f}")


def test_temoin_non_migre():
    """Une espèce NON migrée (Basil) garde l'ancien chemin (empreinte = stades) :
    sa structure pousse mais n'est jamais lue (footprint reste None)."""
    check("témoin: Tomato migrée (procedural_growth)", Tomato.procedural_growth)
    check("témoin: Basil non migrée", not Basil.procedural_growth)
    b = PlantInstance(plant_class=Basil, position=POS)
    cr_avant = Basil.canopy_radius_at(b)
    b.growth_factor = 1.0
    for k in range(20):
        G.grow_plant(b, SEED, 1 + k)
    check("témoin: structure pousse quand même", len(b.segments) > 1,
          f"len={len(b.segments)}")
    check("témoin: empreinte = stades (inchangée par la structure)",
          Basil.canopy_radius_at(b) == cr_avant, f"cr={Basil.canopy_radius_at(b)}")
    check("témoin: cache d'empreinte jamais peuplé", b.footprint is None)


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Croissance procédurale (D29 réorienté, tronçons 1-2)")
    print("=" * 60)
    test_naissance()
    test_croissance_dominance()
    test_debourrement()
    test_bornage()
    test_determinisme()
    test_allure_tomate()
    test_allure_determinisme()
    test_temoin_non_migre()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
