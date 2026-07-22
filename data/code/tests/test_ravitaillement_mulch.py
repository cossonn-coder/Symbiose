"""
SYMBIOSE — tests/test_ravitaillement_mulch.py
Suite ciblée du tronçon ③ « acquisition des moyens d'agir » : le RAVITAILLEMENT en
mulch par ses 3 canaux (`docs/joueur/outils/conception_acquisition_outils.md` §C +
kickoff `sprints/joueur/outils/sprint_acquisition_outils/03_ravitaillement_mulch.md`). Lève
l'impasse `RAVITAILLEMENT_MANQUANT` : `pailler` refusait faute d'une source de mulch
amorçable tôt.

Propriétés exigées (« Tests ciblés » du kickoff) :
  A. GLANER (canal 1) — un plot avec litière tendre : `mulch_stock["feuilles"]`
     crédité de la masse tendre, litière de surface RÉDUITE (feuilles retirées, bois
     RESTE), Vigueur débitée. Plot sans litière tendre → refus SANS dépense.
  B. NATURE `feuilles` — présente dans `NATURES_MULCH` (profil tendre distinct).
  C. PAILLER APRÈS GLANER — le stock `feuilles` glané couvre `PAILLAGE_DOSE`
     (`stock_disponible` vrai) : la chaîne glaner→pailler est complète.
  D. ACHETER_MATERIAU (canal 3) — `botte_paille` : `mulch_stock["paille"] += dose`,
     Vigueur débitée ; refus si fonds insuffisants (rien crédité) ; refus hors offre.

Event-driven HORS TICK → déterminisme total, aucun RNG. La Vigueur est posée
directement (raccourci de test, comme test_acquisition_outils).

Usage (depuis data/code/) :
  python3 -m tests.test_ravitaillement_mulch
"""
from fields import init_eco
from fields.ecofields import NATURES_MULCH, PAILLAGE_DOSE
from sim import actions as ACT
from sim import outils, vigueur

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


P = "joueur_test"


def _gs(vig: float = 100.0):
    """game_state jouet minimal : une tranche Vigueur amorcée, pas de tick."""
    gs = {}
    st = vigueur.ensure_player(gs, P)
    st["courante"] = vig
    return gs


def _masse_tendre(eco, r, c):
    return sum(p.masse for p in eco.litiere[r][c] if p.tissu in ACT.TISSUS_GLANABLES)


def _masse_tissu(eco, r, c, tissu):
    return sum(p.masse for p in eco.litiere[r][c] if p.tissu == tissu)


# ---------------------------------------------------------------------------
# A. Glaner (canal 1) : litière tendre → stock feuilles
# ---------------------------------------------------------------------------

def test_glaner_credite_stock():
    gs = _gs()
    eco = init_eco("T0", 4, 4)
    eco.deposer_litiere(1, 1, "feuille", 2.0)
    eco.deposer_litiere(1, 1, "herbace", 0.5)
    eco.deposer_litiere(1, 1, "bois", 3.0)            # ligneux → DOIT rester au sol
    v_avant = vigueur.ensure_player(gs, P)["courante"]
    credit = ACT.glaner(gs, P, eco, 1, 1)
    stock = ACT.mulch_stock(gs)
    check("A1 — glaner crédite la masse tendre (2.5) au stock feuilles",
          abs(credit - 2.5) < 1e-9 and abs(stock["feuilles"] - 2.5) < 1e-9,
          f"credit={credit}, stock={stock['feuilles']}")
    check("A2 — litière tendre RETIRÉE du sol après glanage",
          _masse_tendre(eco, 1, 1) == 0.0, f"tendre={_masse_tendre(eco, 1, 1)}")
    check("A3 — le bois RESTE au sol (non glanable)",
          abs(_masse_tissu(eco, 1, 1, "bois") - 3.0) < 1e-9,
          f"bois={_masse_tissu(eco, 1, 1, 'bois')}")
    check("A4 — Vigueur débitée du coût glaner (FAIBLE)",
          vigueur.ensure_player(gs, P)["courante"] < v_avant,
          f"{v_avant} → {vigueur.ensure_player(gs, P)['courante']}")


def test_glaner_sol_propre_refuse_sans_depense():
    gs = _gs()
    eco = init_eco("T0", 4, 4)
    eco.deposer_litiere(2, 2, "bois", 3.0)            # que du bois → rien de tendre
    v_avant = vigueur.ensure_player(gs, P)["courante"]
    credit = ACT.glaner(gs, P, eco, 2, 2)
    check("A5 — plot sans litière tendre → refus (crédit 0)", credit == 0.0,
          f"credit={credit}")
    check("A6 — aucune Vigueur dépensée au refus",
          vigueur.ensure_player(gs, P)["courante"] == v_avant,
          f"{v_avant} → {vigueur.ensure_player(gs, P)['courante']}")


# ---------------------------------------------------------------------------
# B. Nature feuilles au registre
# ---------------------------------------------------------------------------

def test_nature_feuilles_presente():
    check("B1 — nature 'feuilles' dans NATURES_MULCH", "feuilles" in NATURES_MULCH)
    check("B2 — feuilles = mulch tendre (decay 1.0), NON ligneux (vers_bois 0)",
          NATURES_MULCH["feuilles"]["decay"] == 1.0
          and NATURES_MULCH["feuilles"]["vers_bois"] == 0.0)


# ---------------------------------------------------------------------------
# C. Chaîne glaner → pailler
# ---------------------------------------------------------------------------

def test_pailler_apres_glaner():
    gs = _gs()
    eco = init_eco("T0", 4, 4)
    eco.deposer_litiere(0, 0, "feuille", PAILLAGE_DOSE * 2)   # de quoi pailler
    ACT.glaner(gs, P, eco, 0, 0)
    ok = ACT.stock_disponible(gs, "feuilles", PAILLAGE_DOSE)
    check("C1 — après glaner, le stock feuilles couvre PAILLAGE_DOSE", ok,
          f"stock={ACT.mulch_stock(gs)['feuilles']}, dose={PAILLAGE_DOSE}")


# ---------------------------------------------------------------------------
# D. Acheter_materiau (canal 3) : import Atelier
# ---------------------------------------------------------------------------

DOSE = outils.MATERIAUX["botte_paille"]["dose"]
COUT = outils.MATERIAUX["botte_paille"]["cout_vigueur"]


def test_acheter_materiau_credite_paille():
    gs = _gs(COUT + 1.0)
    ok = outils.acquerir_materiau(gs, P, "botte_paille")
    stock = ACT.mulch_stock(gs)
    check("D1 — botte_paille acquise : stock paille += dose",
          ok and abs(stock["paille"] - DOSE) < 1e-9,
          f"ok={ok}, paille={stock['paille']}")
    check("D2 — Vigueur débitée du cout_vigueur",
          abs(vigueur.ensure_player(gs, P)["courante"] - 1.0) < 1e-9,
          f"{vigueur.ensure_player(gs, P)['courante']}")


def test_acheter_materiau_fonds_insuffisants():
    gs = _gs(COUT - 5.0)                               # pas de quoi payer
    ok = outils.acquerir_materiau(gs, P, "botte_paille")
    check("D3 — fonds insuffisants → refus, stock paille intact (0)",
          not ok and ACT.mulch_stock(gs)["paille"] == 0.0,
          f"ok={ok}, paille={ACT.mulch_stock(gs)['paille']}")


def test_acheter_materiau_hors_offre():
    gs = _gs()
    ok = outils.acquerir_materiau(gs, P, "materiau_bidon")
    check("D4 — matériau hors offre → refus sans effet", not ok, f"ok={ok}")


def main() -> int:
    print("=== test_ravitaillement_mulch (moyens d'agir ③) ===")
    for fn in (test_glaner_credite_stock, test_glaner_sol_propre_refuse_sans_depense,
               test_nature_feuilles_presente, test_pailler_apres_glaner,
               test_acheter_materiau_credite_paille,
               test_acheter_materiau_fonds_insuffisants,
               test_acheter_materiau_hors_offre):
        fn()
    ko = [n for n, ok in _results if not ok]
    if ko:
        print(f"[ravitaillement] FAIL — {len(ko)} échec(s) : {ko}")
        return 1
    print(f"[ravitaillement] PASS — {len(_results)} vérifs OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
