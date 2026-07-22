"""
SYMBIOSE — tests/test_automate_troncon2.py
Vérifs FONCTIONNELLES du tronçon ② du jardinier automate (table complète,
priorisation, chaînage, désherbage, part_recoltee, détecteur d'impasses).
Spec : docs/joueur/automate/conception_jardinier_automate.md §5/§7 + kickoff
sprints/sprint_jardinier_auto/02_table_budget_impasses.md.

Tests de LOGIQUE PURE (on nourrit `proposer`/`profil` avec des perceptions et des
voisins fabriqués → pas besoin de dérouler un moteur). Le monde `full` n'a PAS de
chaîne de mulch (aucun squelette ligneux, aucune espèce à paille) : le banc y
consigne donc `sol_nu → ravitaillement_manquant`, ce qui est correct. Ici on
CONSTRUIT une source de mulch pour prouver que le chaînage broyer→pailler s'arme.

Usage (depuis data/code/) :
  python3 -m tests.test_automate_troncon2
"""
from __future__ import annotations
from types import SimpleNamespace

from tools.jardinier_auto.profil import LIBRE
from tools.jardinier_auto.proposition import proposer, Plan
from tools.jardinier_auto.impasses import (
    Impasse, GESTE_INEXISTANT, RAVITAILLEMENT_MANQUANT)
from tools.jardinier_auto.regles import regles_pour
from sim.actions.paillage import mulch_stock
from sim.actions.gestes import PAILLAGE_DOSE
from dataclasses import replace

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


def _percept(**over):
    """Une perception neutre (rien à faire) surchargée par `over`."""
    base = dict(position=(3, 4), vitalite=1.0, maturite=0.0, humidite=1.5,
                lumiere=1.0, qi=1.0, paillage=1.0, structure=1.0,
                litiere_tendre=0.0,
                ferale_cible=None, voisin_ombrageant=None)
    base.update(over)
    return SimpleNamespace(**base)


def _plant():
    return SimpleNamespace(name="Tomate", position=(3, 4), y_cm=175.0, x_cm=225.0,
                           is_alive=True, plant_class=SimpleNamespace(mulch_source=None))


def test_chainage_broyer_puis_pailler():
    """sol_nu sans mulch mais AVEC un squelette ligneux à portée → propose BROYER ;
    une fois le stock crédité → propose PAILLER (nature du stock)."""
    gs = {}
    mulch_stock(gs)                                   # crée le stock à 0
    plant = _plant()
    squelette = SimpleNamespace(bois_restant=5.0, is_alive=False,
                                y_cm=180.0, x_cm=230.0, plant_class=None)
    percept = _percept(paillage=0.0)                  # sol nu
    p1 = proposer(gs, plant, [plant, squelette], "T0", "sol_nu", percept)
    ok1 = isinstance(p1, Plan) and p1.verbe == "broyer" and p1.cible_obj is squelette
    check("chaînage — sans stock, propose broyer le squelette", ok1,
          f"plan={getattr(p1, 'verbe', p1)}")
    mulch_stock(gs)["brf"] = PAILLAGE_DOSE            # broyage effectué → stock crédité
    p2 = proposer(gs, plant, [plant, squelette], "T0", "sol_nu", percept)
    ok2 = isinstance(p2, Plan) and p2.verbe == "pailler" and p2.nature == "brf"
    check("chaînage — stock présent, propose pailler(brf)", ok2,
          f"plan={getattr(p2, 'verbe', p2)}/{getattr(p2, 'nature', '')}")


def test_impasse_ravitaillement():
    """sol_nu, aucun mulch, AUCUNE source (ni squelette ni paille) → impasse."""
    gs = {}
    mulch_stock(gs)
    plant = _plant()
    p = proposer(gs, plant, [plant], "T0", "sol_nu", _percept(paillage=0.0))
    ok = isinstance(p, Impasse) and p.cause == RAVITAILLEMENT_MANQUANT
    check("impasse — sol_nu sans source de mulch → ravitaillement_manquant", ok,
          f"{getattr(p, 'cause', p)}")


def test_glaner_leve_impasse():
    """sol_nu, aucun mulch, aucun squelette ni paille — MAIS de la litière tendre au
    plot (moyens d'agir ③, canal 1) → propose GLANER (cible milieu), plus d'impasse."""
    gs = {}
    mulch_stock(gs)
    plant = _plant()
    percept = _percept(paillage=0.0, litiere_tendre=PAILLAGE_DOSE * 2)  # feuilles au sol
    p = proposer(gs, plant, [plant], "T0", "sol_nu", percept)
    ok = (isinstance(p, Plan) and p.verbe == "glaner"
          and p.cible == "milieu" and p.cible_obj is None)
    check("canal 1 — litière tendre au plot → glaner (lève l'impasse)", ok,
          f"plan={getattr(p, 'verbe', p)}")


def test_impasse_geste_inexistant():
    """exces_eau : aucun geste dans la table (drainer/creuser n'existent pas)."""
    gs = {}
    plant = _plant()
    p = proposer(gs, plant, [plant], "T0", "exces_eau", _percept(humidite=2.9))
    ok = isinstance(p, Impasse) and p.cause == GESTE_INEXISTANT
    check("impasse — exces_eau sans geste → geste_inexistant", ok,
          f"{getattr(p, 'cause', p)}")


def test_repli_hydrique_pailler_vers_arroser():
    """hydrique : pailler d'abord (durable), mais sans mulch ni source → repli sur
    arroser (biais permacole ET robustesse)."""
    gs = {}
    mulch_stock(gs)
    plant = _plant()
    p = proposer(gs, plant, [plant], "T0", "hydrique", _percept(humidite=0.5))
    ok = isinstance(p, Plan) and p.verbe == "arroser"
    check("repli — hydrique sans mulch → arroser", ok, f"{getattr(p, 'verbe', p)}")


def test_desherbage_seuils():
    """Les seuils de concurrence dépendent du mode `desherbage` (§4)."""
    aucun = replace(LIBRE, desherbage="aucun").seuil_concurrence()
    curatif = replace(LIBRE, desherbage="curatif").seuil_concurrence()
    systematique = replace(LIBRE, desherbage="systematique").seuil_concurrence()
    check("désherbage — seuils aucun/curatif/systematique = None/2/1",
          aucun is None and curatif == 2 and systematique == 1,
          f"{aucun}/{curatif}/{systematique}")


def test_deraciner_cible():
    """concurrence_ferale avec une cible férale diagnostiquée → propose deraciner."""
    gs = {}
    plant = _plant()
    ferale = SimpleNamespace(name="Pissenlit", position=(3, 4))
    p = proposer(gs, plant, [plant], "T0", "concurrence_ferale",
                 _percept(ferale_cible=ferale))
    ok = isinstance(p, Plan) and p.verbe == "deraciner" and p.cible_obj is ferale
    check("désherbage — concurrence_ferale → deraciner la cible", ok,
          f"{getattr(p, 'verbe', p)}")


def test_part_recoltee():
    """Le slider tronque le nombre de récoltes (round(part×n))."""
    n = 10
    check("part_recoltee — 1.0→10, 0.5→5, 0.0→0",
          replace(LIBRE, part_recoltee=1.0).n_a_recolter(n) == 10
          and replace(LIBRE, part_recoltee=0.5).n_a_recolter(n) == 5
          and replace(LIBRE, part_recoltee=0.0).n_a_recolter(n) == 0)


def test_priorite_hydrique_pailler_avant_arroser():
    """La table ordonne pailler(12) AVANT arroser(10) pour hydrique (biais §5)."""
    verbes = [r.verbe for r in regles_pour("hydrique")]
    check("priorité — hydrique = [pailler, arroser]", verbes == ["pailler", "arroser"],
          f"{verbes}")


def main() -> int:
    print("=== test_automate_troncon2 ===")
    for fn in (test_chainage_broyer_puis_pailler, test_impasse_ravitaillement,
               test_glaner_leve_impasse,
               test_impasse_geste_inexistant, test_repli_hydrique_pailler_vers_arroser,
               test_desherbage_seuils, test_deraciner_cible, test_part_recoltee,
               test_priorite_hydrique_pailler_avant_arroser):
        fn()
    ko = [n for n, ok in _results if not ok]
    if ko:
        print(f"[troncon2] FAIL — {len(ko)} échec(s) : {ko}")
        return 1
    print(f"[troncon2] PASS — {len(_results)} vérifs OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
