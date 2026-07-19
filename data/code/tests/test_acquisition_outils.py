"""
SYMBIOSE — tests/test_acquisition_outils.py
Suite ciblée du tronçon ② « acquisition des moyens d'agir » : l'ATELIER et le
registre `OUTILS` (`sim/outils.py`) — CŒUR de la dette D82. On vérifie que
`acquerir_outil` POSE le marqueur `posseder_secateur` que RIEN ne posait, et que
la chaîne taille (`couper`→`tailler`) s'en trouve DÉVERROUILLÉE.
Spec : `docs/conception/CONCEPTION_ACQUISITION_OUTILS.md` §B + kickoff
`sprints/sprint_acquisition_outils/02_atelier_secateur.md`.

Propriétés exigées (« Tests ciblés » du kickoff) :
  A. ÉTAT INITIAL — `couper`/`tailler` VERROUILLÉS (chaîne morte, D82).
  B. OFFRE — l'Atelier présente `["secateur"]` (Vigueur seule, aucune maîtrise).
  C. ACQUISITION VALIDE — marqueur posé, `couper` ouvert, Vigueur débitée du
     `cout_vigueur` ; puis, une fois `couper` RÉALISÉ (voie action de la chaîne),
     `tailler` s'ouvre à son tour (`tailler` gate `("action", "couper")`, pas la
     seule ouverture — la coupe doit être PRATIQUÉE, `GESTE_UNLOCK`).
  D. FONDS INSUFFISANTS — refus, marqueur NON posé, chaîne toujours morte.
  E. IDEMPOTENCE — ré-acquérir un outil possédé ne re-débite pas.
  F. HORS OFFRE — outil inconnu → refus sans effet.

Event-driven HORS TICK → déterminisme total, aucun RNG. La Vigueur est posée
directement (raccourci de test, comme test_magazine).

Usage (depuis data/code/) :
  python3 -m tests.test_acquisition_outils
"""
from sim import outils, vigueur
from sim.actions import deblocage

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


P = "joueur_test"
COUT = outils.OUTILS["secateur"]["cout_vigueur"]


def _gs(vig: float):
    """game_state jouet minimal : une tranche Vigueur amorcée, pas de tick."""
    gs = {}
    st = vigueur.ensure_player(gs, P)
    st["courante"] = vig
    return gs


# ---------------------------------------------------------------------------
# A. État initial : couper/tailler verrouillés (chaîne morte, D82)
# ---------------------------------------------------------------------------

def test_etat_initial_verrouille():
    print("\n[②A] état initial — chaîne taille MORTE (D82)")
    gs = _gs(100.0)
    check("couper verrouillé au départ",
          not deblocage.est_debloque(gs, P, "couper"))
    check("tailler verrouillé au départ",
          not deblocage.est_debloque(gs, P, "tailler"))
    ouverts = deblocage.gestes_debloques(gs, P)
    check("couper/tailler absents de la palette ouverte",
          "couper" not in ouverts and "tailler" not in ouverts, f"{ouverts}")


# ---------------------------------------------------------------------------
# B. Offre : l'Atelier présente le sécateur (Vigueur seule)
# ---------------------------------------------------------------------------

def test_offre():
    print("\n[②B] offre de l'Atelier — sécateur, aucune maîtrise requise")
    gs = _gs(0.0)   # même sans Vigueur, l'offre est présentée (le paiement échoue après)
    check("offre = ['secateur']", outils.offre_outils(gs, P) == ["secateur"],
          f"{outils.offre_outils(gs, P)}")


# ---------------------------------------------------------------------------
# C. Acquisition valide : marqueur posé, chaîne ouverte, Vigueur débitée
# ---------------------------------------------------------------------------

def test_acquisition_valide():
    print("\n[②C] acquisition valide — sécateur → couper, puis couper → tailler")
    gs = _gs(100.0)
    ok = outils.acquerir_outil(gs, P, "secateur")
    check("acquisition réussie (Vigueur suffisante)", ok)
    check("Vigueur débitée du cout_vigueur",
          vigueur.ensure_player(gs, P)["courante"] == 100.0 - COUT,
          f"courante={vigueur.ensure_player(gs, P)['courante']} (coût {COUT})")
    check("couper DÉVERROUILLÉ par l'acquisition", deblocage.est_debloque(gs, P, "couper"))
    check("tailler ENCORE fermé (attend une coupe PRATIQUÉE)",
          not deblocage.est_debloque(gs, P, "tailler"))
    # Voie action de la chaîne : PRATIQUER `couper` ouvre `tailler`
    # (`GESTE_UNLOCK["tailler"] = [("action", "couper")]`). C'est le pont qui
    # marque l'action après un `couper` réussi ; on le simule ici.
    deblocage.marquer_action(gs, P, "couper")
    deblocage.evaluer_deblocages(gs, P)
    check("tailler DÉVERROUILLÉ après une coupe pratiquée",
          deblocage.est_debloque(gs, P, "tailler"))


# ---------------------------------------------------------------------------
# D. Fonds insuffisants : refus, marqueur NON posé, chaîne morte
# ---------------------------------------------------------------------------

def test_fonds_insuffisants():
    print("\n[②D] Vigueur insuffisante — refus, chaîne toujours morte")
    gs = _gs(COUT - 1.0)   # juste en-dessous du coût
    ok = outils.acquerir_outil(gs, P, "secateur")
    check("acquisition REFUSÉE (fonds insuffisants)", not ok)
    check("couper toujours verrouillé",
          not deblocage.est_debloque(gs, P, "couper"))


# ---------------------------------------------------------------------------
# E. Idempotence : ré-acquérir un outil possédé ne re-débite pas
# ---------------------------------------------------------------------------

def test_idempotence():
    print("\n[②E] idempotence — pas de seconde dépense")
    gs = _gs(100.0)
    outils.acquerir_outil(gs, P, "secateur")
    apres_1 = vigueur.ensure_player(gs, P)["courante"]
    ok2 = outils.acquerir_outil(gs, P, "secateur")
    apres_2 = vigueur.ensure_player(gs, P)["courante"]
    check("2e acquisition refusée (déjà possédé)", not ok2)
    check("aucune seconde dépense", apres_2 == apres_1,
          f"{apres_1} → {apres_2}")


# ---------------------------------------------------------------------------
# F. Hors offre : outil inconnu → refus sans effet
# ---------------------------------------------------------------------------

def test_hors_offre():
    print("\n[②F] outil inconnu — refus sans effet")
    gs = _gs(100.0)
    ok = outils.acquerir_outil(gs, P, "greffoir")   # pas au registre
    check("acquisition d'un outil inconnu refusée", not ok)
    check("aucune Vigueur débitée",
          vigueur.ensure_player(gs, P)["courante"] == 100.0)


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Acquisition des outils (Atelier, D82 ②)")
    print("=" * 60)
    test_etat_initial_verrouille()
    test_offre()
    test_acquisition_valide()
    test_fonds_insuffisants()
    test_idempotence()
    test_hors_offre()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
