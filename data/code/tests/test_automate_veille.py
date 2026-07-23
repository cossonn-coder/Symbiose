"""
SYMBIOSE — tests/test_automate_veille.py
Vérifs du tronçon ④ (D87) : VEILLE + RE-SONDE + IMPASSES honnêtes du planificateur
de l'automate. Spec : docs/joueur/automate/conception_automate_but.md §4/§5 +
kickoff sprints/joueur/automate/sprint_automate_but/04_veille_impasses.md.

LOGIQUE PURE, opt-in : engine JOUET (SimpleNamespace) + vraies `Tile`/`PlantInstance`.
`avancer_plans` ne fait qu'ANALYSER (aucune exécution moteur) → on pilote le monde à
la main entre deux « ticks » (poser un grain, faire apparaître/mourir une cultivée,
avancer la semaine). On prouve :
  A. suivi de germination (T1) : un semis en attente, la levée (une cultivée apparaît)
     clôt le sous-but (`resultat` leve) ; dans la fenêtre, on n'émet PAS un 2e semis ;
  B. re-semis armé (C3) : fenêtre écoulée SANS levée + signature `(saison, plot)`
     inchangée → `niche_defavorable` directe (0 re-semis) ; condition changée → re-semis ;
     `tentatives > 2` → `niche_defavorable` quoi qu'il arrive ;
  C. réveil chaînon : objectif en veille `chainon_manquant`, l'offre magazine s'ouvre →
     l'objectif SORT de veille et propose `acheter_magazine` (plan `reveil:`) ;
  D. objectif en veille RESTE actif ; impasse tracée UNE fois ;
  E. suffisance N (C1) : la mort d'une cultivée réveille un objectif non-accompli ;
  F. déterminisme : rejeu du scénario niche → journaux identiques.

Usage (depuis data/code/) :
  python3 -m tests.test_automate_veille
"""
from __future__ import annotations
import json
from types import SimpleNamespace

from world.tile import Tile
from plants.base import PlantInstance
from plants.catalogue import PLANT_CATALOGUE
from sim.seeds import PlayerSeedBank, Seed
from sim import maitrise, vigueur, maitrise_detection as MD
from tools.jardinier_auto import LIBRE, Objectif, ajouter_objectif, objectifs_actifs
from tools.jardinier_auto.planification import avancer_plans, CLE_PLANS
from tools.jardinier_auto.trace import journal

P = "joueur_1"
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _monde(objectif, *, graines=(), plantes=(), semaine=5):
    """Engine jouet déterministe. `graines` = espèces en banque ; `plantes` =
    (espece, r, c) posées VIVANTES et cultivées."""
    tile = Tile(tile_id="t0", soil_type="terre")
    gs = {"current_player": P, "week": semaine, "player_seed_bank": PlayerSeedBank()}
    for sp in graines:
        gs["player_seed_bank"].add(Seed(species=sp))
    for sp, r, c in plantes:
        tile.plants.append(PlantInstance(plant_class=PLANT_CATALOGUE[sp], position=(r, c)))
        MD.marquer_replante(gs, P, "t0", r, c)
    ajouter_objectif(gs, objectif)
    engine = SimpleNamespace(tiles=[tile], game_state=gs, week=semaine)
    return engine, tile


def _cultiver(engine, tile, sp, r, c):
    """Fait « apparaître » une cultivée vivante (simule une levée)."""
    tile.plants.append(PlantInstance(plant_class=PLANT_CATALOGUE[sp], position=(r, c)))
    MD.marquer_replante(engine.game_state, P, "t0", r, c)


def _avancer(engine, semaine):
    engine.week = semaine
    engine.game_state["week"] = semaine


def _tick(engine):
    return avancer_plans(engine, objectifs_actifs(engine.game_state), LIBRE)


def _impasses(engine):
    return [l for l in journal(engine.game_state) if l["categorie"] == "impasse"]


# ---------------------------------------------------------------------------
# A. Suivi de germination (T1)
# ---------------------------------------------------------------------------

def test_levee_clot_le_sous_but():
    obj = Objectif("recolter", 3, "poivron", "obj_poi")
    engine, tile = _monde(obj, graines=["poivron"])
    plans, _ = _tick(engine)                     # semaine 5 : semis
    check("A. 1er tick → un semis", [p.verbe for p in plans] == ["planter"])
    etat = engine.game_state[CLE_PLANS]["obj_poi"]
    check("A. semaille mémorisée", etat["semaine_semaille"] == 5 and etat["tentatives_semaille"] == 1)

    _cultiver(engine, tile, "poivron", 3, 3)     # la levée a eu lieu
    _avancer(engine, 6)
    plans, _ = _tick(engine)
    res = [l for l in journal(engine.game_state)
           if l["categorie"] == "resultat" and l["detail"].get("issue") == "leve"]
    check("A. levée détectée → resultat leve tracé", len(res) == 1)
    check("A. suivi réinitialisé", etat["semaine_semaille"] is None and etat["tentatives_semaille"] == 0)
    check("A. pas de re-semis (relais Liebig)", plans == [])


def test_attente_dans_la_fenetre():
    obj = Objectif("recolter", 3, "poivron", "obj_poi")
    engine, _ = _monde(obj, graines=["poivron"])
    _tick(engine)                                # semaine 5 : semis
    _avancer(engine, 7)                          # 7-5 = 2 < FENETRE_LEVEE (4)
    plans, veilles = _tick(engine)
    check("A. dans la fenêtre → aucun 2e semis", plans == [] and veilles == [])


# ---------------------------------------------------------------------------
# B. Re-semis armé sur changement de condition (C3)
# ---------------------------------------------------------------------------

def test_niche_defavorable_signature_inchangee():
    obj = Objectif("recolter", 3, "poivron", "obj_poi")
    engine, _ = _monde(obj, graines=["poivron"])
    _tick(engine)                                # semaine 5 : semis en (0,0), printemps
    _avancer(engine, 9)                          # 9-5 = 4 ≥ fenêtre, MÊME saison, MÊME plot libre
    plans, veilles = _tick(engine)
    check("B. signature inchangée → PAS de re-semis", plans == [])
    check("B. impasse niche_defavorable", veilles == [("obj_poi", "niche_defavorable", "niche")])
    imps = _impasses(engine)
    check("B. impasse tracée (cause niche_defavorable)",
          len(imps) == 1 and imps[0]["cause"] == "niche_defavorable")


def test_re_semis_arme_saison_avancee():
    obj = Objectif("recolter", 3, "poivron", "obj_poi")
    engine, _ = _monde(obj, graines=["poivron"])
    _tick(engine)                                # semaine 5 : semis, printemps
    _avancer(engine, 14)                         # saison → été (condition changée)
    plans, _ = _tick(engine)
    check("B. saison avancée → re-semis armé", [p.verbe for p in plans] == ["planter"])
    etat = engine.game_state[CLE_PLANS]["obj_poi"]
    check("B. 2e tentative comptée", etat["tentatives_semaille"] == 2)


def test_re_semis_arme_autre_plot():
    obj = Objectif("recolter", 3, "poivron", "obj_poi")
    engine, tile = _monde(obj, graines=["poivron"])
    _tick(engine)                                # semis en (0,0)
    tile.grains_en_attente[(0, 0)] = ["grain"]   # (0,0) occupé → 1er plot libre = (0,1)
    _avancer(engine, 9)                          # même saison mais AUTRE plot libre
    plans, _ = _tick(engine)
    check("B. autre plot libre → re-semis armé",
          plans and plans[0].verbe == "planter" and (plans[0].cible_obj.r, plans[0].cible_obj.c) == (0, 1))


def test_garde_fou_tentatives():
    obj = Objectif("recolter", 3, "poivron", "obj_poi")
    engine, tile = _monde(obj, graines=["poivron"])
    _tick(engine)
    etat = engine.game_state[CLE_PLANS]["obj_poi"]
    etat["tentatives_semaille"] = 3              # au-delà du garde-fou dur (≤ 2)
    tile.grains_en_attente[(0, 0)] = ["grain"]   # condition CHANGÉE (autre plot libre)
    _avancer(engine, 9)
    plans, veilles = _tick(engine)
    check("B. tentatives > 2 → niche_defavorable malgré condition changée",
          plans == [] and veilles == [("obj_poi", "niche_defavorable", "niche")])


# ---------------------------------------------------------------------------
# C. Réveil chaînon (re-sonde sur déclencheur)
# ---------------------------------------------------------------------------

def _ouvrir_magazine(gs, espece_soeur):
    maitrise.decouvrir(gs, P, espece_soeur)
    gs["maitrise"][P]["objets"][espece_soeur]["palier"] = 3
    vigueur.ensure_player(gs, P)
    gs["vigueur"][P]["max_base"] = 500.0
    gs["vigueur"][P]["courante"] = 500.0


def test_reveil_chainon_manquant():
    obj = Objectif("recolter", 3, "poivron", "obj_poi")
    engine, _ = _monde(obj)                      # ni graine ni offre → chaînon manquant
    plans, veilles = _tick(engine)
    check("C. départ en veille chainon_manquant",
          plans == [] and veilles == [("obj_poi", "graine", "aucune")])
    etat = engine.game_state[CLE_PLANS]["obj_poi"]
    etat["en_veille"] = True                      # état posé par la boucle (dédup veille)

    _ouvrir_magazine(engine.game_state, "tomate")  # DÉCLENCHEUR : l'offre s'ouvre (sœur Solanaceae)
    _avancer(engine, 6)
    plans, _ = _tick(engine)
    check("C. réveil → propose acheter_magazine",
          plans and plans[0].verbe == "acheter_magazine")
    plan_lignes = [l for l in journal(engine.game_state)
                   if l["categorie"] == "plan" and l["semaine"] == 6]
    check("C. plan de réveil tracé (raison reveil:)",
          plan_lignes and plan_lignes[-1]["detail"]["raison"] == "reveil:magazine_ouvert")
    check("C. objectif sorti de veille", etat["en_veille"] is False)


# ---------------------------------------------------------------------------
# D. Objectif reste actif + impasse une fois
# ---------------------------------------------------------------------------

def test_veille_reste_active_et_impasse_unique():
    obj = Objectif("recolter", 3, "poivron", "obj_poi")
    engine, _ = _monde(obj)                      # chaînon manquant permanent
    _tick(engine)
    _avancer(engine, 6)
    _tick(engine)                                # 2e tick sur le même chaînon
    check("D. objectif TOUJOURS actif (pas retiré)",
          "obj_poi" in [o.id for o in objectifs_actifs(engine.game_state)])
    imps = _impasses(engine)
    check("D. impasse chainon_manquant tracée UNE fois",
          len(imps) == 1 and imps[0]["cause"] == "chainon_manquant")


# ---------------------------------------------------------------------------
# E. Suffisance N (C1) — la mort d'une cultivée réveille l'objectif
# ---------------------------------------------------------------------------

def test_mort_reveille_objectif():
    obj = Objectif("recolter", 1, "poivron", "obj_poi")   # nb_cible = min(1,3) = 1
    engine, tile = _monde(obj, graines=["poivron"], plantes=[("poivron", 2, 2)])
    plans, _ = _tick(engine)                     # compte suffisant (1 vivante) → rien
    check("E. compte suffisant → aucun geste créatif", plans == [])
    tile.plants.clear()                          # la cultivée meurt
    _avancer(engine, 6)
    plans, _ = _tick(engine)
    check("E. mort d'une cultivée → objectif non-accompli re-sème",
          [p.verbe for p in plans] == ["planter"])


# ---------------------------------------------------------------------------
# F. Déterminisme (oracle ①) sur le scénario niche
# ---------------------------------------------------------------------------

def test_determinisme_niche():
    def run():
        obj = Objectif("recolter", 3, "poivron", "obj_poi")
        engine, _ = _monde(obj, graines=["poivron"])
        _tick(engine)
        _avancer(engine, 9)
        _tick(engine)
        return json.dumps(journal(engine.game_state), sort_keys=True, default=str)
    check("F. rejeu identique (journal)", run() == run())


def main():
    test_levee_clot_le_sous_but()
    test_attente_dans_la_fenetre()
    test_niche_defavorable_signature_inchangee()
    test_re_semis_arme_saison_avancee()
    test_re_semis_arme_autre_plot()
    test_garde_fou_tentatives()
    test_reveil_chainon_manquant()
    test_veille_reste_active_et_impasse_unique()
    test_mort_reveille_objectif()
    test_determinisme_niche()
    n_ok = sum(1 for _, ok in _results if ok)
    n = len(_results)
    print(f"\n[test_automate_veille] {n_ok}/{n} OK")
    if n_ok != n:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
