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
import json

from plants import Tomato, Basil, AppleTree, Fig, PlantInstance, Segment
from plants.perennials import (CherryTree, HornbeamTree, BeechTree,
                               WalnutTree, OakTree)
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


def _apex_meneur(plant):
    """Index de l'apex à la cime la plus haute (= ce que `_segment_cible('apex')` vise)."""
    segs = plant.segments
    apex = [i for i, s in enumerate(segs) if s.is_apex]
    return max(apex, key=lambda i: segs[i].base[2] + segs[i].dir[2] * segs[i].length_cm)


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


# --- 7. Seam de perturbation §F : atteindre_segment (écimage / doux / collet) ----
#
# Le seam est l'UNIQUE point d'entrée d'altération de structure (tronçon 3). On le
# teste DIRECTEMENT (sans Vigueur ni `tailler` — contrat ACTION testé dans
# test_vigueur). Il n'écrit que l'ÉTAT (auxine / segments) ; l'architecture de
# réponse (débourrement) ÉMERGE au tick `grow_plant` suivant (philo #2).

def test_seam_ecimage():
    p = _fresh()
    _grow(p, 20)
    # Amener l'apex meneur à PORTER de la longueur avant d'écimer : couper un tip
    # fraîchement émis (longueur 0) ne rabaisserait PAS la cime (le bois parent la
    # tient déjà à la même hauteur). On vise un apex bien engagé → la coupe RABAT
    # réellement (décision #2), robuste à la parité du calibrage.
    week = 21
    while p.segments[_apex_meneur(p)].length_cm < G.EMIT_LENGTH * 0.5:
        G.grow_plant(p, SEED, week); week += 1
    n_before, h_before = len(p.segments), _height(p)
    G.atteindre_segment(p, _apex_meneur(p), intensite=1.0)   # ≥ COUPE_NETTE → écimage
    check("écimage: sous-arbre retiré (len ↓)", len(p.segments) < n_before,
          f"{n_before}→{len(p.segments)}")
    check("écimage: hauteur de cime baisse (rabat)", _height(p) < h_before,
          f"{h_before:.1f}→{_height(p):.1f}")
    n_cut = len(p.segments)
    _grow(p, 6, week0=week)
    # Débourrement ÉMERGENT : moins d'apex → l'auxine retombe → les bourgeons
    # survivants naissent latéraux au(x) tick(s) suivant(s). Rien n'est codé ici.
    check("écimage: débourrement émergent (latéraux nés au tick suivant)",
          len(p.segments) > n_cut, f"{n_cut}→{len(p.segments)}")
    check("écimage: ramification présente après débourrement",
          _branch_points(p) >= 1, f"branch={_branch_points(p)}")


def test_seam_doux():
    p = _fresh()
    _grow(p, 24)
    n_before = len(p.segments)
    seg = _apex_meneur(p)
    a_before = p.segments[seg].auxin
    G.atteindre_segment(p, seg, intensite=0.3)   # < COUPE_NETTE → perturbation douce
    check("doux: intensité sous le seuil d'écimage", 0.3 < G.COUPE_NETTE)
    check("doux: aucun segment retiré", len(p.segments) == n_before,
          f"len={len(p.segments)}")
    check("doux: auxine locale baissée de l'intensité",
          abs(p.segments[seg].auxin - max(0.0, a_before - 0.3)) < 1e-9,
          f"{a_before:.3f}→{p.segments[seg].auxin:.3f}")


def test_seam_collet_protege():
    p = _fresh()   # 1 segment = collet apex (parent None)
    G.atteindre_segment(p, 0, intensite=1.0)   # ≥ COUPE_NETTE MAIS collet → rien retiré
    check("collet protégé: rien retiré (collet jamais coupé)",
          len(p.segments) == 1, f"len={len(p.segments)}")
    _grow(p, 10)
    check("collet protégé: la plante repart (rejet de souche)",
          _height(p) > 0.0, f"h={_height(p):.1f}")


def test_seam_determinisme():
    def run():
        p = _fresh()
        _grow(p, 20)
        G.atteindre_segment(p, _apex_meneur(p), intensite=1.0)
        _grow(p, 10, week0=21)
        return _signature(p)
    check("seam: déterministe (même séquence d'appels → structures identiques)",
          run() == run())


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


# --- 8. Allure pommier (tronçon 3bis) : 1re LIGNEUSE migrée ----------------
#
# Le pommier (AppleTree) est la 1re pérenne ligneuse `procedural_growth` : son
# empreinte (height/canopy/root) est DÉRIVÉE de la structure (§G), plus de
# l'age_curve interpolée. Cible d'allure = la fenêtre du golden (10 ans →
# ~350 cm de haut, ~200 cm de couronne ; §E.3 « reproduire l'allure d'abord »).
# On valide en croissance libre sur 520 ticks (cycle saisonnier RÉEL via 1+k,
# growth_factor=1.0) : montée monotone de la flèche vers ~350, couronne qui
# s'élargit (l'étalement `etale` émerge du relâchement d'auxine), bornage.


def _grow_apple(n=520):
    p = PlantInstance(plant_class=AppleTree, position=POS)
    p.growth_factor = 1.0
    hs, crs, lens = [], [], []
    for k in range(n):
        G.grow_plant(p, SEED, 1 + k)            # cycle saisonnier réel (1+k)
        hs.append(AppleTree.height_at(p))
        crs.append(AppleTree.canopy_radius_at(p))
        lens.append(len(p.segments))
    return p, hs, crs, lens


def test_allure_pommier():
    p, hs, crs, lens = _grow_apple()
    h10, cr10 = hs[-1], crs[-1]
    # Montée : départ bas (jeune flèche), an 10 dans ±20 % du gabarit (350 cm).
    check("pommier: départ bas (~30 cm)", hs[0] < 40, f"h0={hs[0]:.1f}")
    check("pommier: hauteur an 10 ≈ 350 (±20 %)", 300 <= h10 <= 420, f"h10={h10:.1f}")
    check("pommier: montée monotone (la flèche ne redescend jamais)",
          all(hs[i] >= hs[i-1] - 1e-9 for i in range(1, len(hs))), f"h10={h10:.1f}")
    # Couronne : non nulle au départ (foliage_halfwidth), s'élargit vers ~200 (±20 %).
    check("pommier: couronne non nulle au départ",
          crs[0] >= AppleTree.foliage_halfwidth - 1e-9, f"cr0={crs[0]:.1f}")
    check("pommier: couronne an 10 ≈ 200 (±20 %)", 160 <= cr10 <= 240, f"cr10={cr10:.1f}")
    check("pommier: couronne s'élargit (cr10 > cr0)", cr10 > crs[0],
          f"{crs[0]:.1f}→{cr10:.1f}")
    # Bornage (run éternel) : len plafonné par max_segments, jamais éteint.
    check("pommier: structure bornée (≤ max_segments)",
          max(lens) <= AppleTree.max_segments, f"max={max(lens)} (cap={AppleTree.max_segments})")
    check("pommier: jamais éteint (≥1, run éternel)", min(lens) >= 1, f"min={min(lens)}")


def test_allure_pommier_determinisme():
    _, h1, c1, _ = _grow_apple(260)
    _, h2, c2, _ = _grow_apple(260)
    check("pommier: empreinte déterministe (260 ticks)", h1 == h2 and c1 == c2,
          f"hfin {h1[-1]:.1f} vs {h2[-1]:.1f}")


# --- 8bis. Épaisseur du bois (sprint lisibilité ligneuse) : pipe model + borne --
#
# Remplace l'accumulation uniforme non bornée (baobab + ronces d'égal diamètre) par
# une épaisseur DÉRIVÉE de la topologie (pipe model : section ∝ n_terminaux portés
# en aval) et d'une croissance secondaire SATURANTE avec l'âge. Contrats :
#   (a) amincissement monotone — parent ≥ enfant, collet le plus épais ;
#   (b) tronc BORNÉ — collet ≤ THICKNESS_INIT + girth_max à tout âge (5 ans ET 50) ;
#   (c) déterminisme — mêmes ticks → mêmes épaisseurs (zéro RNG, philo #3).


def _apple_at(n):
    """Pommier grandi n ticks (cycle saisonnier réel), pleine vigueur."""
    p = PlantInstance(plant_class=AppleTree, position=POS)
    p.growth_factor = 1.0
    for k in range(n):
        G.grow_plant(p, SEED, 1 + k)
    return p


def test_taper_amincissement_monotone():
    p = _apple_at(520)                          # ~10 ans → structure ramifiée
    segs = p.segments
    check("taper: plus d'un segment (arbre ramifié)", len(segs) > 5,
          f"len={len(segs)}")
    mono = all(segs[s.parent].thickness_cm >= s.thickness_cm - 1e-9
               for s in segs if s.parent is not None)
    check("taper: amincissement monotone (parent ≥ enfant)", mono)
    collet = segs[0].thickness_cm
    check("taper: collet le plus épais",
          collet >= max(s.thickness_cm for s in segs) - 1e-9,
          f"collet={collet:.2f}")
    # Brindilles fines : au moins une extrémité proche de THICKNESS_INIT (≠ baobab
    # uniforme). Le contraste collet/brindille tue les « ronces diamètre baobab ».
    fin = min(s.thickness_cm for s in segs)
    check("taper: brindilles fines (contraste avec le collet)",
          fin < collet * 0.5, f"fin={fin:.2f} vs collet={collet:.2f}")


def test_taper_tronc_borne():
    from sim.growth.constantes import THICKNESS_INIT
    bound = THICKNESS_INIT + AppleTree.girth_max_cm + 1e-6
    c5  = _apple_at(260).segments[0].thickness_cm    # ~5 ans
    c50 = _apple_at(2600).segments[0].thickness_cm   # ~50 ans (borne tient dans la durée)
    check("taper: tronc borné à ~5 ans", c5 <= bound, f"{c5:.2f} ≤ {bound:.2f}")
    check("taper: tronc borné à ~50 ans (pas de baobab)", c50 <= bound,
          f"{c50:.2f} ≤ {bound:.2f}")
    check("taper: le tronc grossit AVEC l'âge (saturant)", c50 > c5,
          f"{c5:.2f} → {c50:.2f}")


def test_taper_determinisme():
    def run():
        return [round(s.thickness_cm, 6) for s in _apple_at(260).segments]
    check("taper: épaisseurs déterministes (260 ticks, zéro RNG)", run() == run())


def test_pommier_temoin_non_migre():
    """Une LIGNEUSE NON migrée (Figuier) garde l'age_curve : l'override résolu ne
    fuit pas. Sa hauteur suit age_years ; sa structure pousse mais reste non lue."""
    check("témoin ligneux: AppleTree migré", AppleTree.procedural_growth)
    check("témoin ligneux: Fig non migré", not Fig.procedural_growth)
    f = PlantInstance(plant_class=Fig, position=POS)
    f.age_years = 10.0                          # age_curve Fig : (10, 400, 250)
    h_age = Fig.height_at(f)                     # = 400 × growth_factor × gène
    for k in range(40):
        G.grow_plant(f, SEED, 1 + k)
    check("témoin ligneux: hauteur = age_curve (inchangée par la structure)",
          abs(Fig.height_at(f) - h_age) < 1e-9, f"h={Fig.height_at(f):.1f}")
    check("témoin ligneux: structure poussée mais jamais lue", len(f.segments) > 1,
          f"len={len(f.segments)}")
    check("témoin ligneux: cache d'empreinte jamais peuplé", f.footprint is None)


# --- 8ter. Feuillus étalés migrés (D91 ①) : 5 nouvelles ligneuses procédurales --
#
# Cerisier, charme, hêtre, noyer, chêne passent de l'age_curve tabulée à la
# croissance procédurale en segments (comme le pommier). On valide, en croissance
# libre sur ~520 ticks (an 10, cycle saisonnier réel) : (a) chaque espèce est bien
# migrée ; (b) elle POUSSE (hauteur an 10 >> semis) et reste MONOTONE (la couronne
# ne s'effondre pas, le cap segments ne rabote pas la flèche) ; (c) structure bornée
# (≤ max_segments, jamais éteinte) ; (d) déterminisme (zéro RNG, philo #3). Les
# valeurs de calibrage précises sont des placeholders → F5 (T4) : on teste l'ALLURE
# (ordre de grandeur, montée saine), pas des seuils fins. HORS golden (aucune de ces
# espèces n'est dans le smoke).

_FEUILLUS_D91 = [CherryTree, HornbeamTree, BeechTree, WalnutTree, OakTree]


def _grow_tree(cls, n=520):
    p = PlantInstance(plant_class=cls, position=POS)
    p.growth_factor = 1.0
    hs, lens = [], []
    for k in range(n):
        G.grow_plant(p, SEED, 1 + k)            # cycle saisonnier réel
        hs.append(cls.height_at(p))
        lens.append(len(p.segments))
    return p, hs, lens


def test_feuillus_d91_migres():
    for cls in _FEUILLUS_D91:
        check(f"{cls.name}: migré (procedural_growth)", cls.procedural_growth)
        p, hs, lens = _grow_tree(cls)
        check(f"{cls.name}: a poussé (an 10 >> semis)", hs[-1] > 200.0,
              f"h10={hs[-1]:.1f}")
        check(f"{cls.name}: montée monotone (flèche ne redescend jamais)",
              all(hs[i] >= hs[i-1] - 1e-9 for i in range(1, len(hs))),
              f"h10={hs[-1]:.1f}")
        check(f"{cls.name}: structure bornée (≤ max_segments)",
              max(lens) <= cls.max_segments, f"max={max(lens)} (cap={cls.max_segments})")
        check(f"{cls.name}: jamais éteinte (≥1, run éternel)", min(lens) >= 1,
              f"min={min(lens)}")


def test_feuillus_d91_determinisme():
    for cls in (CherryTree, OakTree):          # échantillon (kickoff : au moins ces 2)
        p1, h1, _ = _grow_tree(cls, 260)
        p2, h2, _ = _grow_tree(cls, 260)
        check(f"{cls.name}: empreinte déterministe (260 ticks)",
              h1 == h2 and p1.segments == p2.segments,
              f"hfin {h1[-1]:.1f} vs {h2[-1]:.1f}")


def test_serialisation_structure():
    """Tronçon 6 (§J) : la structure de segments est sérialisable en JSON et
    round-trip FIDÈLE (sérialise → JSON → désérialise = structure identique), et
    une structure restaurée **continue de pousser à l'identique** (l'état complet
    du bois est restitué). Les organes (régénérés) ne sont PAS stockés."""
    p = PlantInstance(plant_class=Tomato, position=POS)
    p.growth_factor = 1.0
    for k in range(60):
        G.grow_plant(p, SEED, 1 + k)
    check("sérial: structure non triviale", len(p.segments) > 5, f"len={len(p.segments)}")

    # Round-trip JSON : sérialise → texte → recharge dans une instance NEUVE.
    blob = json.dumps(p.structure_to_dict())            # doit être JSON-sérialisable
    data = json.loads(blob)
    q = PlantInstance(plant_class=Tomato, position=POS)
    q.restore_structure(data)
    check("sérial: même nombre de segments", len(q.segments) == len(p.segments))
    check("sérial: round-trip FIDÈLE (segments identiques)", q.segments == p.segments)
    check("sérial: base/dir restitués en tuples",
          all(isinstance(s.base, tuple) and isinstance(s.dir, tuple) for s in q.segments))
    check("sérial: cache d'empreinte invalidé au chargement", q.footprint is None)

    # Allègement §J : les organes (régénérés par le rendu) ne sont PAS sérialisés.
    check("sérial: organes exclus du dict (allègement §J)",
          all("organs" not in d for d in data))
    check("sérial: organes restaurés vides", all(s.organs == [] for s in q.segments))

    # Continuation déterministe : la structure restaurée pousse comme l'originale.
    q.growth_factor = 1.0
    for k in range(40):
        G.grow_plant(p, SEED, 61 + k)
        G.grow_plant(q, SEED, 61 + k)
    check("sérial: restaurée pousse à l'identique (len)", len(q.segments) == len(p.segments),
          f"p={len(p.segments)} q={len(q.segments)}")
    check("sérial: restaurée pousse à l'identique (structure)", q.segments == p.segments)
    check("sérial: empreinte dérivée identique après reprise",
          abs(Tomato.height_at(q) - Tomato.height_at(p)) < 1e-9)


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Croissance procédurale (D29 réorienté, tronçons 1-6)")
    print("=" * 60)
    test_naissance()
    test_croissance_dominance()
    test_debourrement()
    test_bornage()
    test_determinisme()
    test_allure_tomate()
    test_allure_determinisme()
    test_seam_ecimage()
    test_seam_doux()
    test_seam_collet_protege()
    test_seam_determinisme()
    test_temoin_non_migre()
    test_allure_pommier()
    test_allure_pommier_determinisme()
    test_taper_amincissement_monotone()
    test_taper_tronc_borne()
    test_taper_determinisme()
    test_pommier_temoin_non_migre()
    test_feuillus_d91_migres()
    test_feuillus_d91_determinisme()
    test_serialisation_structure()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
