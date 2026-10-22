"""
SYMBIOSE — tests/test_bois_mort.py
Tests ciblés du tronçon ② du sprint « le sol qui respire » (D111) : une branche qui
meurt (élaguée par `_elaguer`) TOMBE en litière `bois` sous elle au lieu de disparaître.

  A. `grow_plant` renvoie les segments élagués (liste vide sinon).
  B. `deposer_bois_tombe` : ligneux → litière `bois` ∝ longueur × épaisseur², au plot
     de la verticale du milieu du segment, borné à la tuile.
  C. herbacée (non ligneuse) → rien.
  D. un pommier dont on force le plafond de segments dépose bien du bois (bout en bout).
②bis (mort des branches) :
  E. ombre : une couronne sombre perd des branches, une éclairée non ; tronc protégé.
  F. tempête : l'arbre exposé casse, l'abrité non ; choix déterministe.
  G. arbuste non procédural (framboisier) : bois sec largué à sa semaine.
  H. donnée `ligneux` : thym → squelette de bois, tomate → rien.
  I. init `full` : du bois au sol dès la semaine 0, âges variés, déterministe.
②ter (arbres adultes) :
  J. pré-croissance : déterministe, ≫ 1 segment à 10 ans ; pommier de `full` crû.
  K. tolérance à l'ombre par espèce : bouleau < pommier < chêne < charme < hêtre.
  L. rythme borné : fenêtre 1 sem./CLADO_FENETRE, au plus n_max branche (la plus sombre).
⑦bis (bois continu) :
  M. grosseur : gros bois plus lent que brindille ; défaut = taux historique exact ;
     fusion pondérée par la masse ; segments tombés et squelette portent leur diamètre.
  N. tiges de l'année (tomate, courgette) → `herbace`, jamais `bois`.
  O. ceinture : dépôt en bord seulement, secteur coupé → moins, sans ceinture → rien,
     déterministe.

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

# --- ②bis ---------------------------------------------------------------------
import copy
from fields.grids import GridField
from plants.species.sauvages import Raspberry
from plants.species.aromatiques import Thyme
from sim.effects.perturbations import frac_bois_mort
from sim.growth import (branches_ombragees, couper_branches, seuil_et_age,
                        branches_a_casser)
from sim.growth.cladoptose import axe_porteur
from sim.growth.geometrie import _children
import sim.engine.branches as BR

adulte = PlantInstance(plant_class=AppleTree, position=(2, 4))
for w in range(1, 521):
    grow_plant(adulte, 42, w, None)
n0 = len(adulte.segments)
seuil, age = seuil_et_age(1.0)

# E. ombre
sombre = copy.deepcopy(adulte)
r_sombre = branches_ombragees(sombre, 0.05, 0.6, seuil, age)
check("ombre : couronne sombre → des branches condamnées", len(r_sombre) > 0, len(r_sombre))
axe = axe_porteur(sombre.segments, _children(sombre.segments))
check("ombre : jamais le tronc ni la flèche", not (set(r_sombre) & axe))
tb = couper_branches(sombre, r_sombre)
check("ombre : segments renvoyés pour la litière", len(tb) > 0 and len(sombre.segments) == n0 - len(tb),
      f"{len(tb)} tombés, {len(sombre.segments)}/{n0} restent")
check("ombre : couronne éclairée sans feuillage opaque → rien",
      branches_ombragees(copy.deepcopy(adulte), 1.0, 0.0, seuil, age) == [])

# F. tempête : exposé vs abrité
def _eco_vent(v):
    g = GridField(6, 8, initial=v, max_val=10.0)
    return SimpleNamespace(vent=g, turbulence=None, rows=6, cols=8,
                           deposer_litiere=lambda *a: None)
expo = abri = 0
for w in range(1, 41):
    expo += len(BR._casse_vent(copy.deepcopy(adulte), _eco_vent(0.40), 1.8, 42, w))
    abri += len(BR._casse_vent(copy.deepcopy(adulte), _eco_vent(0.15), 1.8, 42, w))
check("tempête : l'exposé casse, l'abrité non", expo > 0 and abri == 0, f"{expo} vs {abri}")
k1 = branches_a_casser(copy.deepcopy(adulte), 2, 42, 7, 0.25)
k2 = branches_a_casser(copy.deepcopy(adulte), 2, 42, 7, 0.25)
check("tempête : choix des branches déterministe", k1 == k2 and len(k1) == 2, k1)

# G. arbuste non procédural
eco4 = init_eco("nul", 4, 4)
fr = PlantInstance(plant_class=Raspberry, position=(1, 1))
fr.age_weeks = 80
fr.current_stage = len(Raspberry.growth_stages) - 1
m_hors = BR._chute_arbuste(fr, eco4, Raspberry.bois_chute_semaine + 1)
m_fr = BR._chute_arbuste(fr, eco4, Raspberry.bois_chute_semaine)
check("arbuste : bois largué à SA semaine seulement", m_hors == 0.0 and m_fr > 0.0
      and abs(_bois(eco4, 1, 1) - m_fr) < 1e-12, f"{m_fr:.4f}")

# H. donnée ligneux
check("ligneux : thym → part de bois au squelette",
      frac_bois_mort(PlantInstance(plant_class=Thyme, position=(0, 0))) > 0.0)
check("ligneux : tomate → aucune", frac_bois_mort(tom) == 0.0)

# I. init full
from tools.simserver.server import SimServer
def _init_bois():
    srv = SimServer(); srv.cmd_init({"config": "full", "seed": 1521550718})
    return [(e.tile_id if hasattr(e, "tile_id") else i, r, c, round(p.masse, 9), round(p.age_sem, 6))
            for i, e in enumerate(srv.engine.game_state["eco"].values())
            for r in range(e.rows) for c in range(e.cols)
            for p in e.litiere[r][c] if p.tissu == "bois"]
b1, b2 = _init_bois(), _init_bois()
ages = {round(a) for *_, a in b1}
check("init full : du bois au sol dès la semaine 0", len(b1) >= 8, f"{len(b1)} plots")
check("init full : âges variés", len(ages) >= 5, sorted(ages)[:8])
check("init full : déterministe (2 inits identiques)", b1 == b2)

# J. pré-croissance (hors tick)
from sim.precroissance import pre_croitre
from sim.growth import fenetre_ouverte
from sim.growth.constantes import CLADO_FENETRE
def _pre(ans):
    a = PlantInstance(plant_class=AppleTree, position=(3, 3))
    pre_croitre(a, 1521550718, ans)
    return a
a1, a2 = _pre(10), _pre(10)
forme = lambda a: [(s.base, s.dir, s.length_cm, s.thickness_cm) for s in a.segments]
check("pré-croissance : déterministe", forme(a1) == forme(a2))
check("pré-croissance : arbre de 10 ans ≫ 1 segment", len(a1.segments) >= 30, len(a1.segments))
check("pré-croissance : empreinte à jour (couronne > 1 m)",
      AppleTree.canopy_radius_at(a1) > 100.0, round(AppleTree.canopy_radius_at(a1)))
srv_f = SimServer(); srv_f.cmd_init({"config": "full", "seed": 1521550718})
pom = [p for t in srv_f.engine.game_state["tiles"] for p in t.plants if p.name == "Pommier"][0]
check("init full : pommier pré-vieilli a une structure (D105)",
      len(pom.segments) > 1 and AppleTree.height_at(pom) > 150.0,
      f"{len(pom.segments)} seg., {AppleTree.height_at(pom):.0f} cm")

# K. tolérance à l'ombre par espèce
from plants.perennials import BirchTree, OakTree, HornbeamTree, BeechTree
tols = [c.shade_tolerance_base() for c in (BirchTree, AppleTree, OakTree, HornbeamTree, BeechTree)]
check("tolérance ombre : héliophile → sciaphile croissante", tols == sorted(tols)
      and len(set(tols)) == len(tols), tols)

# L. rythme borné
ouvertes = sum(fenetre_ouverte(adulte, 7, w) for w in range(1, 1 + 10 * CLADO_FENETRE))
check("fenêtre : 1 semaine sur CLADO_FENETRE", ouvertes == 10, ouvertes)
tous = branches_ombragees(copy.deepcopy(adulte), 0.05, 0.6, seuil, age)
un = branches_ombragees(copy.deepcopy(adulte), 0.05, 0.6, seuil, age, n_max=1)
check("rythme : n_max=1 → une seule branche parmi les condamnées",
      len(tous) > 1 and len(un) == 1 and un[0] in tous, f"{len(tous)} → {un}")

# M. grosseur du bois (⑦bis)
from fields.ecofields.litiere import facteur_grosseur, BOIS_DIAM_DEFAUT, diam_pondere
def _fond(diam, n=52):
    e = init_eco("m", 3, 3, humidite=1.5, fertilite=1.0, microbiome=0.3)
    e.deposer_litiere(1, 1, "bois", 1.0, diam)
    for _ in range(n):
        e.tick_decomposition()
    return _bois(e, 1, 1)
b_brin, b_def, b_bra, b_tronc = _fond(0.3), _fond(BOIS_DIAM_DEFAUT), _fond(5.0), _fond(30.0)
check("grosseur : brindille < défaut < branche < tronc (masse restante après 1 an)",
      b_brin < b_def < b_bra < b_tronc, f"{b_brin:.3f} < {b_def:.3f} < {b_bra:.3f} < {b_tronc:.3f}")
check("grosseur : facteur 1 exact au diamètre par défaut", facteur_grosseur(BOIS_DIAM_DEFAUT) == 1.0)
e_m = init_eco("m", 3, 3, humidite=1.0, fertilite=1.0, microbiome=0.3)
e_m.deposer_litiere(0, 0, "bois", 3.0, 20.0)
e_m.deposer_litiere(0, 0, "bois", 1.0, 0.4)
pb = next(q for q in e_m.litiere[0][0] if q.tissu == "bois")
check("grosseur : fusion pondérée par la masse", abs(pb.diam_cm - (3 * 20 + 0.4) / 4) < 1e-9,
      round(pb.diam_cm, 3))
e_m.deposer_litiere(1, 1, "bois", 1.0)
e_m.deposer_litiere(1, 1, "bois", 0.7)
check("grosseur : défaut + défaut reste EXACTEMENT le défaut",
      next(q for q in e_m.litiere[1][1] if q.tissu == "bois").diam_cm == BOIS_DIAM_DEFAUT)
e_s = init_eco("s", 6, 6, humidite=1.0, fertilite=1.0, microbiome=0.3)
pom_s = PlantInstance(plant_class=AppleTree, position=(2, 2))
deposer_bois_tombe(pom_s, [_seg(125, 125, 1, 0, 50, 4.0)], e_s)
check("grosseur : segment tombé = son épaisseur",
      abs(next(q for q in e_s.litiere[2][3] if q.tissu == "bois").diam_cm - 4.0) < 1e-9)
from sim.effects import deposer_mort
mort = _pre(10)
deposer_mort(mort, e_s)
check("grosseur : squelette = diamètre pondéré de sa structure, figé à la mort",
      mort.bois_diam_cm > 1.0 and abs(mort.bois_diam_cm - diam_pondere(mort.segments)) < 1e-12,
      round(mort.bois_diam_cm, 2))

# N. tiges de l'année → herbacé, jamais bois
from plants.species.potageres import Zucchini
for cls_t in (Tomato, Zucchini):
    e_t = init_eco("t", 3, 3, humidite=1.0, fertilite=1.0, microbiome=0.3)
    pt = PlantInstance(plant_class=cls_t, position=(1, 1))
    pt.current_stage = len(cls_t.growth_stages) - 1
    deposer_mort(pt, e_t)
    tissus = {q.tissu for q in e_t.litiere[1][1] if q.masse > 0}
    check(f"tige de l'année : {cls_t.__name__} → herbacé, pas de bois",
          "herbace" in tissus and "bois" not in tissus and pt.bois_restant == 0.0, tissus)

# O. la ceinture boisée lâche du bois en lisière
from sim.engine.ceinture_bois import bois_de_lisiere
from world import Tile
from fields.peripherie import secteur_neutre, OUEST
def _lisiere(densite, hauteur, n=104, ceint=True):
    tl = Tile(tile_id="L", soil_type="terre", origin_x_cm=0, origin_y_cm=0)
    e = init_eco("L", 10, 10, humidite=1.0, fertilite=1.0, microbiome=0.3)
    s = secteur_neutre(OUEST); s.update(type="foret", densite_ligneuse=densite,
                                        hauteur_canopee=hauteur)
    for w in range(1, n + 1):
        bois_de_lisiere(tl, e, [s] if ceint else None, "hiver", 7, w, 0.3, 1.25)
    return e
e_l = _lisiere(0.8, 1500.0)
cols = [sum(_bois(e_l, r, c) for r in range(10)) for c in range(10)]
check("ceinture : du bois au bord ouest, rien au-delà de la portée",
      cols[0] > 0 and all(v == 0 for v in cols[8:]), [round(v, 2) for v in cols])
check("ceinture : plus au contact qu'au loin", cols[0] > cols[5], f"{cols[0]:.2f} > {cols[5]:.2f}")
tot = lambda e: sum(_bois(e, r, c) for r in range(10) for c in range(10))
check("ceinture : secteur coupé (densité, hauteur ↓) → moins de bois",
      tot(_lisiere(0.1, 300.0)) < tot(e_l) * 0.3,
      f"{tot(_lisiere(0.1, 300.0)):.2f} < {tot(e_l):.2f}")
check("ceinture : sans ceinture → rien", tot(_lisiere(0.8, 1500.0, ceint=False)) == 0.0)
check("ceinture : déterministe", [_bois(_lisiere(0.8, 1500.0), r, 0) for r in range(10)]
      == [_bois(e_l, r, 0) for r in range(10)])
diams = {round(q.diam_cm, 1) for r in range(10) for c in range(10)
         for q in e_l.litiere[r][c] if q.tissu == "bois"}
check("ceinture : grosseurs variées (brindilles et branches)",
      min(diams) < 1.0 and max(diams) > 2.0, f"{min(diams)}–{max(diams)}")

n_ok = sum(ok for _, ok in _results)
print(f"\n{n_ok}/{len(_results)} OK")
sys.exit(0 if n_ok == len(_results) else 1)
