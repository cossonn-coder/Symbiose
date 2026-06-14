"""
SYMBIOSE — tests/test_fruits.py
Tests ciblés des organes-fruits traçables (décompo·compost ③, absorbe D19).

Un fruit cesse d'être un PROXY DE RENDU saisonnier : il devient un ÉTAT MOTEUR
réel (engine._tick_fruits) — il naît à la nouaison, mûrit, se mange UN par UN
(actions.manger ciblé → déplétion) et tombe en litière `fruit` s'il n'est pas
cueilli (cascade fertilité). Hors golden : on force l'âge et la structure pour
exercer le cycle complet en quelques ticks (le golden, lui, reste NEUTRE car
AppleTree fructifie à maturity_years=5 > sa fenêtre de 2 ans).

Couvre :
  1. Nouaison : à FRUIT_NOUAISON_WEEK, une espèce `fruitier` mûre pose un fruit
     vert (maturité ≈ 0) par site reproducteur (`organ_sites`).
  2. Gate d'âge : sous `maturity_years`, AUCUN fruit (→ neutralité golden).
  3. Annualité : la nouaison ne se déclenche QU'à FRUIT_NOUAISON_WEEK ; une
     nouvelle cohorte fait chuter l'ancienne en litière.
  4. Maturation : `maturite += FRUIT_DMAT` à chaque tick.
  5. Chute : un fruit sur-mûr (> MATURITE_CHUTE) tombe → litière `fruit`.
  6. Déterminisme : deux runs identiques → fruits identiques (zéro RNG).
  7. manger ciblé : gain ∝ maturité du fruit visé, l'organe DISPARAÎT (D19).
  8. manger générique : sans `fruit_index` (ou index hors-borne) → façade
     plante entière (chemin legacy, tests vigueur D1-D4 préservés).

Usage (depuis data/code/) :
  python3 -m tests.test_fruits
"""
import sys

from world import Tile
from plants import AppleTree, Fruit, organ_sites
from plants.base import Segment
from fields import init_eco, FRUIT_MASSE, FRUIT_DMAT, MATURITE_CHUTE
from sim.engine import Engine, FRUIT_NOUAISON_WEEK
from sim import actions as ACT
from sim import vigueur as V
from sim.vigueur_plante import vigueur_plante

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _apex(z, x=0.0):
    """Segment-apex synthétique dressé (dir +z) à la hauteur `z`."""
    return Segment(parent=None, base=(x, 0.0, z), dir=(0.0, 0.0, 1.0),
                   length_cm=50.0, thickness_cm=2.0, age_weeks=10,
                   auxin=0.5, is_apex=True)


def _monde(age_years=6.0, n_apex=3):
    """Pommier `fruitier` à structure CONTRÔLÉE (n_apex apex dressés à des
    hauteurs distinctes → le retrait du meneur `lateral` est déterministe).
    Tuile 6×6 terre, germination spontanée coupée (isole le pommier)."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("T0", 6, 6, humidite=1.5, fertilite=1.2, microbiome=0.3)
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    apple = tile.add_plant(AppleTree, 3, 3)
    apple.age_years = age_years
    apple.segments = [_apex(z=100.0 + 30.0 * i, x=10.0 * i) for i in range(n_apex)]
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "joueur_1", "week": 1, "log": []}
    V.ensure_player(gs, "joueur_1")
    eng = Engine(gs)
    return gs, tile, eco, apple, eng


def _litiere_fruit(eco, r, c):
    return sum(p.masse for p in eco.litiere[r][c] if p.tissu == "fruit")


# ---------------------------------------------------------------------------
# 1. Nouaison
# ---------------------------------------------------------------------------
def test_nouaison():
    print("\n[1] nouaison : un fruit vert par site reproducteur à FRUIT_NOUAISON_WEEK")
    gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=3)
    attendu = len(organ_sites(apple))   # lateral : 3 apex → meneur retiré → 2
    eng._tick_fruits(tile, eco, FRUIT_NOUAISON_WEEK)
    check("nombre de fruits = nombre de sites", len(apple.fruits) == attendu,
          f"{len(apple.fruits)} fruits / {attendu} sites")
    check("fruits verts (mûris d'un seul pas)",
          apple.fruits and all(abs(f.maturite - FRUIT_DMAT) < 1e-9 for f in apple.fruits),
          f"maturité={apple.fruits[0].maturite:.3f}")
    check("masse initiale = FRUIT_MASSE",
          all(abs(f.masse - FRUIT_MASSE) < 1e-9 for f in apple.fruits))


# ---------------------------------------------------------------------------
# 2. Gate d'âge (neutralité golden)
# ---------------------------------------------------------------------------
def test_gate_age():
    print("\n[2] gate d'âge : sous maturity_years, AUCUNE nouaison (→ golden NEUTRE)")
    gs, tile, eco, apple, eng = _monde(age_years=1.0, n_apex=3)  # < maturity_years=5
    eng._tick_fruits(tile, eco, FRUIT_NOUAISON_WEEK)
    check("jeune arbre : zéro fruit", apple.fruits == [],
          f"age={apple.age_years} maturity_years={AppleTree.maturity_years}")
    apple.age_years = 6.0
    eng._tick_fruits(tile, eco, FRUIT_NOUAISON_WEEK)
    check("arbre mûr : fruits posés", len(apple.fruits) > 0)


# ---------------------------------------------------------------------------
# 3. Annualité (rendez-vous fixe + remplacement de cohorte)
# ---------------------------------------------------------------------------
def test_annualite():
    print("\n[3] annualité : nouaison QUE à FRUIT_NOUAISON_WEEK ; nouvelle cohorte → chute de l'ancienne")
    gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=3)
    # Une semaine ordinaire ne noue rien.
    eng._tick_fruits(tile, eco, FRUIT_NOUAISON_WEEK + 1)
    check("hors nouaison : aucun fruit créé", apple.fruits == [])
    # Nouaison année 1.
    eng._tick_fruits(tile, eco, FRUIT_NOUAISON_WEEK)
    n1 = len(apple.fruits)
    check("nouaison année 1", n1 > 0)
    # Nouaison année 2 : l'ancienne cohorte (non récoltée) chute en litière.
    avant = _litiere_fruit(eco, 3, 3)
    eng._tick_fruits(tile, eco, FRUIT_NOUAISON_WEEK)
    apres = _litiere_fruit(eco, 3, 3)
    check("cohorte précédente versée en litière `fruit`", apres > avant,
          f"litière {avant:.3f} → {apres:.3f}")
    check("cohorte renouvelée (verte)",
          len(apple.fruits) == n1 and apple.fruits[0].maturite <= FRUIT_DMAT + 1e-9)


# ---------------------------------------------------------------------------
# 4. Maturation
# ---------------------------------------------------------------------------
def test_maturation():
    print("\n[4] maturation : maturité += FRUIT_DMAT par tick ordinaire")
    gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=1)
    eng._tick_fruits(tile, eco, FRUIT_NOUAISON_WEEK)   # nouaison (1er pas)
    m0 = apple.fruits[0].maturite
    eng._tick_fruits(tile, eco, FRUIT_NOUAISON_WEEK + 1)  # tick ordinaire
    m1 = apple.fruits[0].maturite
    check("la maturité augmente d'un pas", abs((m1 - m0) - FRUIT_DMAT) < 1e-9,
          f"{m0:.3f} → {m1:.3f} (+{FRUIT_DMAT})")


# ---------------------------------------------------------------------------
# 5. Chute des sur-mûrs
# ---------------------------------------------------------------------------
def test_chute():
    print("\n[5] chute : un fruit sur-mûr (> MATURITE_CHUTE) tombe → litière `fruit`")
    gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=1)
    # Fruit posé juste SOUS le seuil ; un pas le pousse au-delà → chute.
    apple.fruits = [Fruit(0, MATURITE_CHUTE - FRUIT_DMAT / 2, FRUIT_MASSE)]
    avant = _litiere_fruit(eco, 3, 3)
    eng._tick_fruits(tile, eco, FRUIT_NOUAISON_WEEK + 1)
    apres = _litiere_fruit(eco, 3, 3)
    check("le fruit a quitté la plante", apple.fruits == [])
    check("masse déposée en litière `fruit`",
          abs((apres - avant) - FRUIT_MASSE) < 1e-9, f"+{apres - avant:.3f}")


# ---------------------------------------------------------------------------
# 6. Déterminisme
# ---------------------------------------------------------------------------
def test_determinisme():
    print("\n[6] déterminisme : deux runs identiques → fruits identiques (zéro RNG)")
    def run():
        gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=4)
        traj = []
        for w in range(FRUIT_NOUAISON_WEEK, FRUIT_NOUAISON_WEEK + 8):
            eng._tick_fruits(tile, eco, w)
            traj.append(tuple(round(f.maturite, 6) for f in apple.fruits))
        return traj
    a, b = run(), run()
    check("trajectoires de maturité identiques", a == b,
          f"{len(a)} pas comparés")


# ---------------------------------------------------------------------------
# 7. manger ciblé (gain ∝ maturité, déplétion réelle D19)
# ---------------------------------------------------------------------------
def test_manger_cible():
    print("\n[7] manger ciblé : gain ∝ maturité du fruit visé, l'organe DISPARAÎT")
    gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=1)
    apple.fruits = [Fruit(0, 0.3, FRUIT_MASSE), Fruit(0, 0.9, FRUIT_MASSE)]
    g_vert = ACT.manger(gs, "joueur_1", apple, eco, fruit_index=0)
    check("fruit vert mangé → retiré", len(apple.fruits) == 1)
    g_mur = ACT.manger(gs, "joueur_1", apple, eco, fruit_index=0)  # le mûr restant
    check("fruit mûr mangé → plus de fruits", apple.fruits == [])
    check("gain croît avec la maturité", g_mur > g_vert > 0.0,
          f"vert={g_vert:.2f} < mûr={g_mur:.2f}")
    # Les autres facteurs (santé, Qi, gène) étant identiques, le ratio des gains
    # = ratio des maturités (0.9 / 0.3 = 3).
    check("gain strictement proportionnel à la maturité",
          abs(g_mur / g_vert - 3.0) < 1e-6, f"ratio={g_mur / g_vert:.4f}")


# ---------------------------------------------------------------------------
# 8. manger générique (fallback legacy — D1-D4 vigueur préservés)
# ---------------------------------------------------------------------------
def test_manger_generique():
    print("\n[8] manger générique : sans index (ou hors-borne) → façade plante entière")
    gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=1)
    apple.fruits = [Fruit(0, 0.5, FRUIT_MASSE)]
    attendu = ACT.HARVEST_GAIN_FULL * vigueur_plante(apple, eco)
    g_none = ACT.manger(gs, "joueur_1", apple, eco)              # pas d'index
    check("sans index : gain = façade plante entière", abs(g_none - attendu) < 1e-9)
    check("sans index : fruits INTACTS", len(apple.fruits) == 1)
    g_oob = ACT.manger(gs, "joueur_1", apple, eco, fruit_index=9)  # hors-borne
    check("index hors-borne : repli générique", abs(g_oob - attendu) < 1e-9)
    check("index hors-borne : fruits INTACTS", len(apple.fruits) == 1)


def main():
    test_nouaison()
    test_gate_age()
    test_annualite()
    test_maturation()
    test_chute()
    test_determinisme()
    test_manger_cible()
    test_manger_generique()

    print("\n" + "=" * 60)
    total = len(_results)
    ok = sum(1 for _, c in _results if c)
    for name, cond in _results:
        if not cond:
            print(f"  ÉCHEC : {name}")
    print(f"RÉSULTAT : {ok}/{total} vérifications passées")
    if ok == total:
        print("[test_fruits] PASS")
        return 0
    print("[test_fruits] FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
