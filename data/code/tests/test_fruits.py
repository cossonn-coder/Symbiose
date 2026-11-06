"""
SYMBIOSE — tests/test_fruits.py
Tests ciblés des organes-fruits traçables (décompo·compost ③, absorbe D19).

Un fruit cesse d'être un PROXY DE RENDU saisonnier : il devient un ÉTAT MOTEUR
réel (engine._tick_fruits) — il naît à la nouaison, mûrit, se mange UN par UN
(actions.manger ciblé → déplétion) et tombe en litière `fruit` s'il n'est pas
cueilli (cascade fertilité). Hors golden : on force l'âge, la structure et la
`floraison` pour exercer le cycle complet en quelques ticks (le golden, lui,
reste NEUTRE car AppleTree fructifie à maturity_years=5 > sa fenêtre de 2 ans,
donc ne fleurit jamais dans le golden).

Nouaison POLLINISÉE (tronçon ④, §B) : la nouaison ne se déclenche plus à une
semaine fixe (FRUIT_NOUAISON_WEEK), mais EN FIN DE FLORAISON, par plante — quand
sa `floraison` retombe après avoir culminé. La fraction de sites qui nouent
dépend du MODE : `insect` lit la dose `pollen_recu` (g(), sans plancher),
`self`/`wind` nouent pleinement.

Couvre :
  1. Nouaison : en fin de floraison, une fruitière mûre pose des fruits verts
     (maturité ≈ 0) sur ses sites reproducteurs (`organ_sites`).
  2. Gate d'âge : sous `maturity_years`, AUCUN fruit (→ neutralité golden).
  3. Cohorte annuelle : une nouvelle nouaison fait chuter l'ancienne en litière.
  4. Maturation : `maturite += 1 / fruit_semaines_maturation` à chaque tick (pommier).
  5. Chute : un fruit sur-mûr (> MATURITE_CHUTE) tombe → litière `fruit`.
  6. Déterminisme : deux runs identiques → fruits identiques (zéro RNG).
  7. Modes de pollinisation : `insect` sans pollen → 0 fruit (sans plancher) ;
     dose forte → nouaison ≈ pleine ; `self` → pleine sans pollen.
  8. manger ciblé : gain ∝ maturité du fruit visé, l'organe DISPARAÎT (D19).
  9. manger générique : sans `fruit_index` (ou index hors-borne) → façade
     plante entière (chemin legacy, tests vigueur D1-D4 préservés).
 10. Cohortes (VERGER VIVANT ③) : `nombre` fruits par site, manger en retire un,
     sans levier d'espèce 1 fruit par site sous MAX_ORGANS.

Usage (depuis data/code/) :
  python3 -m tests.test_fruits
"""
import sys

from world import Tile
from plants import AppleTree, Fruit, organ_sites
from plants.base import Segment
from fields import init_eco, FRUIT_MASSE, MATURITE_CHUTE
from sim.engine import Engine
from sim.engine.decompo import frac_nouaison
from sim import actions as ACT
from sim import vigueur as V
from sim.vigueur_plante import vigueur_plante

# Le pommier a sa propre durée de maturation (sprint HOUPPIER ③) ; `FRUIT_DMAT` reste le
# défaut des autres fruitières, vérifié par `tests/bancs/test_verger_mur.py`.
DMAT_POMMIER = 1.0 / AppleTree.fruit_semaines_maturation

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


def _litiere_fruit_tuile(eco):
    """Litière `fruit` de toute la tuile : un arbre la répand sous sa couronne (③)."""
    return sum(_litiere_fruit(eco, r, c) for r in range(eco.rows) for c in range(eco.cols))


def _nouer(eng, tile, eco, plant, pollen=100.0, w=1):
    """Force une nouaison « en fin de floraison » : pleine floraison (arme
    `a_fleuri`) puis fanaison (déclenche la nouaison). `pollen` alimente la dose
    entomophile (insect → frac=g(pollen)). Le 2e pas mûrit la cohorte d'un cran
    (maturité ≈ un pas), comme l'ancienne nouaison à pas unique."""
    plant.floraison = 1.0
    eng._tick_fruits(tile, eco, w)         # arme a_fleuri (pleine floraison)
    plant.floraison = 0.0
    plant.pollen_recu = pollen
    eng._tick_fruits(tile, eco, w)         # floraison fanée → nouaison


# ---------------------------------------------------------------------------
# 1. Nouaison
# ---------------------------------------------------------------------------
def test_nouaison():
    print("\n[1] nouaison : fruits verts par site reproducteur en fin de floraison")
    gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=3)
    attendu = len(organ_sites(apple))   # lateral : 3 apex → meneur retiré → 2
    _nouer(eng, tile, eco, apple)       # dose forte → frac≈1 → tous les sites
    check("nombre de fruits = nombre de sites", len(apple.fruits) == attendu,
          f"{len(apple.fruits)} fruits / {attendu} sites")
    check("fruits verts (mûris d'un seul pas)",
          apple.fruits and all(abs(f.maturite - DMAT_POMMIER) < 1e-9 for f in apple.fruits),
          f"maturité={apple.fruits[0].maturite:.3f}")
    check("masse initiale = masse d'un fruit de l'espèce (VERGER VIVANT ③)",
          all(abs(f.masse - AppleTree.fruit_masse) < 1e-9 for f in apple.fruits))
    check("cohortes : fruits_par_site × frac par site",
          sum(f.nombre for f in apple.fruits)
          == round(frac_nouaison(100.0) * AppleTree.fruits_par_site * attendu),
          f"{[f.nombre for f in apple.fruits]}")


# ---------------------------------------------------------------------------
# 2. Gate d'âge (neutralité golden)
# ---------------------------------------------------------------------------
def test_gate_age():
    print("\n[2] gate d'âge : sous maturity_years, AUCUNE nouaison (→ golden NEUTRE)")
    gs, tile, eco, apple, eng = _monde(age_years=1.0, n_apex=3)  # < maturity_years=5
    _nouer(eng, tile, eco, apple)
    check("jeune arbre : zéro fruit", apple.fruits == [],
          f"age={apple.age_years} maturity_years={AppleTree.maturity_years}")
    apple.age_years = 6.0
    _nouer(eng, tile, eco, apple)
    check("arbre mûr : fruits posés", len(apple.fruits) > 0)


# ---------------------------------------------------------------------------
# 3. Cohorte annuelle (remplacement de cohorte)
# ---------------------------------------------------------------------------
def test_cohorte():
    print("\n[3] cohorte : floraison sans fanaison ne noue pas ; nouvelle cohorte → chute de l'ancienne")
    gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=3)
    # Pleine floraison SANS fanaison ne noue rien (front descendant requis).
    apple.floraison = 1.0
    eng._tick_fruits(tile, eco, 1)
    check("floraison sans fanaison : aucun fruit créé", apple.fruits == [])
    # Nouaison année 1 (fin de floraison).
    _nouer(eng, tile, eco, apple)
    n1 = len(apple.fruits)
    check("nouaison année 1", n1 > 0)
    # Nouaison année 2 : l'ancienne cohorte (non récoltée) chute en litière.
    avant = _litiere_fruit(eco, 3, 3)
    _nouer(eng, tile, eco, apple)
    apres = _litiere_fruit(eco, 3, 3)
    check("cohorte précédente versée en litière `fruit`", apres > avant,
          f"litière {avant:.3f} → {apres:.3f}")
    check("cohorte renouvelée (verte)",
          len(apple.fruits) == n1 and apple.fruits[0].maturite <= DMAT_POMMIER + 1e-9)


# ---------------------------------------------------------------------------
# 4. Maturation
# ---------------------------------------------------------------------------
def test_maturation():
    print("\n[4] maturation : maturité += 1 / durée de l'espèce par tick ordinaire")
    gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=1)
    _nouer(eng, tile, eco, apple)        # nouaison (cohorte verte, +1 pas)
    m0 = apple.fruits[0].maturite
    eng._tick_fruits(tile, eco, 2)       # tick ordinaire (floraison=0, a_fleuri faux)
    m1 = apple.fruits[0].maturite
    check("la maturité augmente d'un pas", abs((m1 - m0) - DMAT_POMMIER) < 1e-9,
          f"{m0:.3f} → {m1:.3f} (+{DMAT_POMMIER:.3f})")


# ---------------------------------------------------------------------------
# 5. Chute des sur-mûrs
# ---------------------------------------------------------------------------
def test_chute():
    print("\n[5] chute : un fruit sur-mûr (> MATURITE_CHUTE) tombe → litière `fruit`")
    gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=1)
    # Fruit posé juste SOUS le seuil ; un pas le pousse au-delà → chute.
    apple.fruits = [Fruit(0, MATURITE_CHUTE - DMAT_POMMIER / 2, FRUIT_MASSE, 5)]
    avant = _litiere_fruit_tuile(eco)
    eng._tick_fruits(tile, eco, 1)
    apres = _litiere_fruit_tuile(eco)
    check("le fruit a quitté la plante", apple.fruits == [])
    check("masse déposée en litière `fruit` = nombre × masse (cohorte ③)",
          abs((apres - avant) - 5 * FRUIT_MASSE) < 1e-9, f"+{apres - avant:.3f}")


# ---------------------------------------------------------------------------
# 6. Déterminisme
# ---------------------------------------------------------------------------
def test_determinisme():
    print("\n[6] déterminisme : deux runs identiques → fruits identiques (zéro RNG)")
    def run():
        gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=4)
        _nouer(eng, tile, eco, apple)        # nouaison déterministe
        traj = []
        for w in range(8):
            eng._tick_fruits(tile, eco, w)   # maturation ordinaire
            traj.append(tuple(round(f.maturite, 6) for f in apple.fruits))
        return traj
    a, b = run(), run()
    check("trajectoires de maturité identiques", a == b,
          f"{len(a)} pas comparés")


# ---------------------------------------------------------------------------
# 7. Modes de pollinisation (§B.2 : insect lit la dose SANS plancher ; self plein)
# ---------------------------------------------------------------------------
def test_modes():
    print("\n[7] modes : insect sans pollen → 0 fruit ; dose forte → plein ; self → plein sans pollen")
    # insect, dose nulle → aucun fruit (sans plancher = pression écologique).
    gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=3)
    _nouer(eng, tile, eco, apple, pollen=0.0)
    check("insect sans pollen : 0 fruit (sans plancher)", apple.fruits == [],
          f"frac(0)={frac_nouaison(0.0):.3f}")
    # insect, dose forte → nouaison ≈ pleine.
    gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=3)
    plein = len(organ_sites(apple))
    _nouer(eng, tile, eco, apple, pollen=100.0)
    check("insect dose forte : nouaison ≈ pleine", len(apple.fruits) == plein,
          f"{len(apple.fruits)}/{plein} (frac(100)={frac_nouaison(100.0):.3f})")
    # self : nouaison pleine MÊME sans pollen (court-circuite la dose).
    gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=3)
    mode_orig = AppleTree.pollination_mode
    try:
        AppleTree.pollination_mode = "self"
        _nouer(eng, tile, eco, apple, pollen=0.0)
        check("self sans pollen : nouaison pleine", len(apple.fruits) == plein,
              f"{len(apple.fruits)}/{plein}")
    finally:
        AppleTree.pollination_mode = mode_orig


# ---------------------------------------------------------------------------
# 7. manger ciblé (gain ∝ maturité, déplétion réelle D19)
# ---------------------------------------------------------------------------
def test_manger_cible():
    print("\n[8] manger ciblé : gain ∝ maturité du fruit visé, l'organe DISPARAÎT")
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
    print("\n[9] manger générique : sans index (ou hors-borne) → façade plante entière")
    gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=1)
    apple.fruits = [Fruit(0, 0.5, FRUIT_MASSE)]
    attendu = ACT.HARVEST_GAIN_FULL * vigueur_plante(apple, eco)
    g_none = ACT.manger(gs, "joueur_1", apple, eco)              # pas d'index
    check("sans index : gain = façade plante entière", abs(g_none - attendu) < 1e-9)
    check("sans index : fruits INTACTS", len(apple.fruits) == 1)
    g_oob = ACT.manger(gs, "joueur_1", apple, eco, fruit_index=9)  # hors-borne
    check("index hors-borne : repli générique", abs(g_oob - attendu) < 1e-9)
    check("index hors-borne : fruits INTACTS", len(apple.fruits) == 1)


# ---------------------------------------------------------------------------
# 10. Cohortes (VERGER VIVANT ③)
# ---------------------------------------------------------------------------
def test_cohortes():
    print("\n[10] cohortes : manger retire UN fruit ; sans levier, 1 fruit par site")
    gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=1)
    apple.fruits = [Fruit(0, 0.9, FRUIT_MASSE, 3)]
    ACT.manger(gs, "joueur_1", apple, eco, fruit_index=0)
    check("cohorte de 3 mangée une fois → 2", apple.fruits and apple.fruits[0].nombre == 2)
    ACT.manger(gs, "joueur_1", apple, eco, fruit_index=0)
    ACT.manger(gs, "joueur_1", apple, eco, fruit_index=0)
    check("dernier fruit mangé → cohorte retirée", apple.fruits == [])
    # Sans levier (chemin des herbacées) : comportement d'avant, plafond MAX_ORGANS.
    gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=14)
    par_site, masse = AppleTree.fruits_par_site, AppleTree.fruit_masse
    try:
        AppleTree.fruits_par_site, AppleTree.fruit_masse = None, None
        _nouer(eng, tile, eco, apple)
        check("sans levier : ≤ MAX_ORGANS cohortes d'un fruit à FRUIT_MASSE",
              len(apple.fruits) == len(organ_sites(apple)) == 10
              and all(f.nombre == 1 and f.masse == FRUIT_MASSE for f in apple.fruits),
              f"{len(apple.fruits)} cohortes")
    finally:
        AppleTree.fruits_par_site, AppleTree.fruit_masse = par_site, masse
    gs, tile, eco, apple, eng = _monde(age_years=6.0, n_apex=14)
    _nouer(eng, tile, eco, apple)
    check("avec levier : tous les apex latéraux sont des sites (sans plafond)",
          len(apple.fruits) == len(organ_sites(apple, plafond=None)) == 13,
          f"{len(apple.fruits)} cohortes")
    _nouer(eng, tile, eco, apple, pollen=0.05)
    n = sum(f.nombre for f in apple.fruits)
    check("peu de pollen : peu de fruits, sur moins de sites",
          0 < n == round(frac_nouaison(0.05) * AppleTree.fruits_par_site * 13)
          and len(apple.fruits) <= 13, f"{n} fruits, {len(apple.fruits)} cohortes")


def main():
    test_nouaison()
    test_gate_age()
    test_cohorte()
    test_maturation()
    test_chute()
    test_determinisme()
    test_modes()
    test_manger_cible()
    test_manger_generique()
    test_cohortes()

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
