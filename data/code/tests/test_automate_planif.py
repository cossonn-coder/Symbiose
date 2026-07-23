"""
SYMBIOSE — tests/test_automate_planif.py
Vérifs du PLANIFICATEUR moyens-fins de l'automate (D87 tronçon ②) : catalogue
d'opérateurs créatifs (operateurs.py) + chaînage arrière borné (planification.py).
Spec : docs/joueur/automate/conception_automate_but.md §2/§4 + kickoff
sprints/joueur/automate/sprint_automate_but/02_operateurs_regression.md.

LOGIQUE PURE, opt-in : on monte un `engine` JOUET (SimpleNamespace tiles/game_state/
week) avec de vraies `Tile`/`PlantInstance` — pas besoin de dérouler un moteur. Le
tronçon n'est PAS branché dans la boucle → aucune conséquence sur le golden (vérifié
à part par test_golden). On prouve :
  A. objectif recolter + graine en banque + plot libre → Plan(planter) au bon plot,
     DÉTERMINISTE (2 runs → plans + journaux identiques) ;
  B. banque vide + offre magazine (palier 3 famille) → Plan(acheter_magazine) ;
  C. banque vide + pas d'offre → VEILLE `chainon_manquant`, aucun geste ;
  D. cultivée `fruitier` sans habitat → sous-chaîne `favoriser_auxiliaire` ;
     cultivée `fruitier=False` → PAS de sous-chaîne pollinisation ;
  E. `but_satisfait` distingue fruit mûr (fruitier) vs maturité végétative.

Usage (depuis data/code/) :
  python3 -m tests.test_automate_planif
"""
from __future__ import annotations
import json
from types import SimpleNamespace

from world.tile import Tile
from plants.base import PlantInstance
from plants.base.stades import Fruit
from plants.catalogue import PLANT_CATALOGUE
from sim.seeds import PlayerSeedBank, Seed
from sim import maitrise, vigueur, maitrise_detection as MD
from tools.jardinier_auto import LIBRE, Objectif, ajouter_objectif, objectifs_actifs
from tools.jardinier_auto.planification import avancer_plans, CLE_PLANS
from tools.jardinier_auto.operateurs import but_satisfait
from tools.jardinier_auto.trace import journal

P = "joueur_1"
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# Fabrique de monde jouet
# ---------------------------------------------------------------------------

def _monde(objectif, *, graines=(), plantes=(), palier3=None, vigueur_haute=False):
    """Monte un engine jouet déterministe. `graines` = espèces déposées en banque ;
    `plantes` = (espece, r, c) posées VIVANTES et déclarées cultivées ; `palier3` =
    espèce dont on force le palier 3 (ouvre les sœurs au magazine)."""
    tile = Tile(tile_id="t0", soil_type="terre")
    gs = {"current_player": P, "week": 5, "player_seed_bank": PlayerSeedBank()}
    for sp in graines:
        gs["player_seed_bank"].add(Seed(species=sp))
    for sp, r, c in plantes:
        p = PlantInstance(plant_class=PLANT_CATALOGUE[sp], position=(r, c))
        tile.plants.append(p)
        MD.marquer_replante(gs, P, "t0", r, c)      # sous tutelle (cultivée)
    if palier3 is not None:
        maitrise.decouvrir(gs, P, palier3)
        gs["maitrise"][P]["objets"][palier3]["palier"] = 3
    if vigueur_haute:
        vigueur.ensure_player(gs, P)
        gs["vigueur"][P]["max_base"] = 500.0
        gs["vigueur"][P]["courante"] = 500.0
    ajouter_objectif(gs, objectif)
    engine = SimpleNamespace(tiles=[tile], game_state=gs, week=gs["week"])
    return engine


# ---------------------------------------------------------------------------
# A. Semis : graine en banque + plot libre → Plan(planter) au bon plot
# ---------------------------------------------------------------------------

def test_planter():
    obj = Objectif("recolter", 3, "tomate", "obj_tom")
    engine = _monde(obj, graines=["tomate"])
    plans, veilles = avancer_plans(engine, objectifs_actifs(engine.game_state), LIBRE)
    check("un seul plan émis", len(plans) == 1, f"{len(plans)} plan(s)")
    p = plans[0]
    check("plan = planter", p.verbe == "planter" and p.facteur == "advenir")
    check("placement = premier plot libre (0,0)",
          p.cible_obj.tile.tile_id == "t0" and (p.cible_obj.r, p.cible_obj.c) == (0, 0),
          f"({p.cible_obj.r},{p.cible_obj.c})")
    check("priorité créative basse (5)", p.priorite == 5)
    check("aucune veille", veilles == [])


def test_planter_determinisme():
    def run():
        obj = Objectif("recolter", 3, "tomate", "obj_tom")
        engine = _monde(obj, graines=["tomate"])
        plans, _ = avancer_plans(engine, objectifs_actifs(engine.game_state), LIBRE)
        rendu = [(p.verbe, p.cible_obj.espece, p.cible_obj.r, p.cible_obj.c) for p in plans]
        return rendu, json.dumps(journal(engine.game_state), sort_keys=True)
    r1, j1 = run()
    r2, j2 = run()
    check("A. rejeu identique (plans + journal)", r1 == r2 and j1 == j2,
          "plans/journaux égaux" if j1 == j2 else "DIVERGENTS")


# ---------------------------------------------------------------------------
# B. Achat : banque vide + offre magazine (palier 3 famille) → Plan(acheter)
# ---------------------------------------------------------------------------

def test_acheter_magazine():
    obj = Objectif("recolter", 3, "poivron", "obj_poi")
    # palier 3 tomate → poivron (sœur Solanaceae) offert ; banque vide ; Vigueur haute.
    engine = _monde(obj, palier3="tomate", vigueur_haute=True)
    plans, veilles = avancer_plans(engine, objectifs_actifs(engine.game_state), LIBRE)
    check("un seul plan émis", len(plans) == 1, f"{len(plans)} plan(s)")
    check("plan = acheter_magazine",
          plans and plans[0].verbe == "acheter_magazine"
          and plans[0].cible_obj.espece == "poivron")
    check("achat sans lieu (tile/plot None)",
          plans and plans[0].cible_obj.tile is None and plans[0].cible_obj.r is None)
    check("aucune veille", veilles == [])


def test_acheter_bloque_sans_vigueur():
    # même offre, mais Vigueur au défaut (100) < COUT_MAGAZINE (120) → pré fausse.
    obj = Objectif("recolter", 3, "poivron", "obj_poi")
    engine = _monde(obj, palier3="tomate", vigueur_haute=False)
    plans, veilles = avancer_plans(engine, objectifs_actifs(engine.game_state), LIBRE)
    check("B'. Vigueur insuffisante → pas d'achat", plans == [])
    check("B'. → veille chainon graine", veilles == [("obj_poi", "graine", "aucune")])


# ---------------------------------------------------------------------------
# C. Impasse douce : banque vide + pas d'offre → VEILLE, aucun geste
# ---------------------------------------------------------------------------

def test_veille_chainon_manquant():
    obj = Objectif("recolter", 3, "haricot", "obj_har")
    engine = _monde(obj)                      # ni graine, ni maîtrise → aucune voie
    plans, veilles = avancer_plans(engine, objectifs_actifs(engine.game_state), LIBRE)
    check("C. aucun geste créatif", plans == [])
    check("C. veille chainon_manquant (graine)",
          veilles == [("obj_har", "graine", "aucune")])
    etat = engine.game_state[CLE_PLANS]["obj_har"]
    check("C. état automate_plans persiste le chaînon", etat["chainon"] == "graine")
    diags = [l for l in journal(engine.game_state) if l["categorie"] == "diagnostic"]
    check("C. un diagnostic de chaînon manquant tracé",
          len(diags) == 1 and diags[0]["detail"]["manque"] == "graine")


# ---------------------------------------------------------------------------
# D. Sous-chaîne pollinisation TYPÉE fruitier (C2/C4)
# ---------------------------------------------------------------------------

def test_favoriser_si_fruitier():
    # tomate (fruitier) déjà cultivée, quantité 1 → n_vivantes(1) == nb_cible(1) :
    # PAS de semis ; mais fruitière sans habitat → favoriser_auxiliaire proposé.
    obj = Objectif("recolter", 1, "tomate", "obj_tom")
    engine = _monde(obj, plantes=[("tomate", 1, 2)])
    plans, _ = avancer_plans(engine, objectifs_actifs(engine.game_state), LIBRE)
    verbes = [p.verbe for p in plans]
    check("D. favoriser_auxiliaire proposé pour une fruitière",
          verbes == ["favoriser_auxiliaire"], f"verbes={verbes}")
    check("D. cible = la tuile de la cultivée",
          plans and plans[0].cible_obj.tile.tile_id == "t0")


def test_pas_de_favoriser_si_non_fruitier():
    # poivron (fruitier=False) cultivé, quantité 1 → ni semis ni pollinisation.
    obj = Objectif("recolter", 1, "poivron", "obj_poi")
    engine = _monde(obj, plantes=[("poivron", 1, 2)])
    plans, veilles = avancer_plans(engine, objectifs_actifs(engine.game_state), LIBRE)
    check("D. non-fruitier → aucune sous-chaîne pollinisation", plans == [])
    check("D. non-fruitier → aucune veille (compte atteint)", veilles == [])


# ---------------------------------------------------------------------------
# E. but_satisfait : fruit mûr vs maturité végétative
# ---------------------------------------------------------------------------

def test_but_satisfait():
    tom_mur = PlantInstance(plant_class=PLANT_CATALOGUE["tomate"], position=(0, 0))
    tom_mur.fruits = [Fruit(0, 1.0, 0.1)]
    check("E. fruitier + fruit mûr → satisfait", but_satisfait(tom_mur, "tomate"))
    tom_vert = PlantInstance(plant_class=PLANT_CATALOGUE["tomate"], position=(0, 0))
    tom_vert.fruits = [Fruit(0, 0.5, 0.1)]
    check("E. fruitier + fruit vert → NON satisfait", not but_satisfait(tom_vert, "tomate"))

    n = len(PLANT_CATALOGUE["poivron"].growth_stages)
    poi_mur = PlantInstance(plant_class=PLANT_CATALOGUE["poivron"], position=(0, 0),
                            current_stage=n - 1)
    check("E. non-fruitier + maturité végétative → satisfait",
          but_satisfait(poi_mur, "poivron"))
    poi_semis = PlantInstance(plant_class=PLANT_CATALOGUE["poivron"], position=(0, 0),
                              current_stage=0)
    check("E. non-fruitier + semis → NON satisfait", not but_satisfait(poi_semis, "poivron"))


def main():
    test_planter()
    test_planter_determinisme()
    test_acheter_magazine()
    test_acheter_bloque_sans_vigueur()
    test_veille_chainon_manquant()
    test_favoriser_si_fruitier()
    test_pas_de_favoriser_si_non_fruitier()
    test_but_satisfait()
    n_ok = sum(1 for _, ok in _results if ok)
    n = len(_results)
    print(f"\n[test_automate_planif] {n_ok}/{n} OK")
    if n_ok != n:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
