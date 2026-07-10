"""
SYMBIOSE — tests/test_deblocage.py
Golden JOUEUR du DÉBLOCAGE des gestes (palette de gestes, tronçon ①). Distinct du
golden ÉCOLOGIQUE (`tests/test_golden.py`) : cette couche vit dans
`game_state["gestes_debloques"]`, AU-DESSUS du tick, et ne fait JAMAIS avancer la
simulation (miroir de `test_maitrise.py`). Déterministe SANS RNG : on POSE l'état
(palier de maîtrise / action réalisée / marqueur écolo) par appel d'API, puis on
vérifie que le hook `evaluer_deblocages` ouvre les bons gestes.

Vérifie :
  1. Nouvel avatar → `gestes_debloques` = set de BASE, rien de plus.
  2. Voie SAVOIR (maîtrise) : palier `compostage` ≥ 1 → ouvre `poser_bac`/`poser_pile`.
  3. Voie ACTION : `marquer_action("poser_bac")` → ouvre `composter`/`retourner`/`epandre`.
  4. Chaîne D12 sécateur→couper→tailler (voie action en cascade).
  5. Condition COMPOSÉE (`et`) : bouturer = taille niv.2 ET semis niv.2.
  6. Voie ÉVÉNEMENT émergente : marqueur `bouture_spontanee` → ouvre `bouturer`.
  7. Idempotence : un geste déjà ouvert n'est jamais re-signalé.
  8. Un geste GATED verrouillé n'est pas `est_debloque` ; un geste de BASE l'est
     toujours (même sans couche).
"""
from __future__ import annotations

from sim import maitrise as M
from sim.actions import deblocage as D

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _poser_palier(gs, player, objet, palier):
    """Force le palier d'un objet de maîtrise (injection directe, sans RNG)."""
    st = M.ensure_player_maitrise(gs, player)
    st["objets"][objet] = {"palier": palier, "preuves": 0}


def test_base():
    print("\n[1] nouvel avatar → set de BASE, rien de plus")
    gs = {}
    ouverts = D.init_gestes_debloques(gs, "j1")
    check("BASE exact", ouverts == set(D.GESTES_BASE), f"{sorted(ouverts)}")
    check("planter dans BASE", "planter" in ouverts)
    check("poser_bac PAS dans BASE (gated)", "poser_bac" not in ouverts)
    check("gestes_debloques() = BASE triée",
          D.gestes_debloques(gs, "j1") == sorted(D.GESTES_BASE))


def test_voie_savoir():
    print("\n[2] voie savoir : maîtrise compostage ≥ 1 → poser_bac/poser_pile")
    gs = {}
    D.init_gestes_debloques(gs, "j1")
    check("avant palier : poser_bac fermé", not D.est_debloque(gs, "j1", "poser_bac"))
    _poser_palier(gs, "j1", "compostage", 1)
    nouveaux = D.evaluer_deblocages(gs, "j1")
    check("poser_bac ouvert", "poser_bac" in nouveaux)
    check("poser_pile ouvert", "poser_pile" in nouveaux)
    check("composter PAS encore (attend l'action poser_bac)",
          "composter" not in nouveaux)


def test_voie_action():
    print("\n[3] voie action : poser_bac réalisé → composter/retourner/epandre")
    gs = {}
    D.init_gestes_debloques(gs, "j1")
    D.marquer_action(gs, "j1", "poser_bac")
    nouveaux = D.evaluer_deblocages(gs, "j1")
    for v in ("composter", "retourner", "epandre"):
        check(f"{v} ouvert", v in nouveaux)
    check("empiler_bois PAS ouvert (attend poser_pile)",
          "empiler_bois" not in nouveaux)


def test_chaine_secateur():
    print("\n[4] chaîne D12 : sécateur → couper → tailler")
    gs = {}
    D.init_gestes_debloques(gs, "j1")
    check("tailler PAS dans BASE (D12)", not D.est_debloque(gs, "j1", "tailler"))
    D.marquer_action(gs, "j1", "posseder_secateur")
    n1 = D.evaluer_deblocages(gs, "j1")
    check("couper ouvert par le sécateur", "couper" in n1)
    D.marquer_action(gs, "j1", "couper")
    n2 = D.evaluer_deblocages(gs, "j1")
    check("tailler ouvert en coupant", "tailler" in n2)


def test_condition_composee():
    print("\n[5] condition composée : bouturer = taille niv.2 ET semis niv.2")
    gs = {}
    D.init_gestes_debloques(gs, "j1")
    _poser_palier(gs, "j1", "taille", 2)
    n1 = D.evaluer_deblocages(gs, "j1")
    check("un seul palier : bouturer fermé", "bouturer" not in n1)
    _poser_palier(gs, "j1", "semis", 2)
    n2 = D.evaluer_deblocages(gs, "j1")
    check("les deux paliers : bouturer ouvert", "bouturer" in n2)


def test_voie_evenement():
    print("\n[6] voie émergente : marqueur bouture_spontanee → bouturer")
    gs = {}
    D.init_gestes_debloques(gs, "j1")
    D.marquer_evenement(gs, "j1", "bouture_spontanee")
    nouveaux = D.evaluer_deblocages(gs, "j1")
    check("bouturer ouvert par l'événement", "bouturer" in nouveaux)


def test_idempotence():
    print("\n[7] idempotence : un geste ouvert n'est plus re-signalé")
    gs = {}
    D.init_gestes_debloques(gs, "j1")
    _poser_palier(gs, "j1", "compostage", 1)
    n1 = D.evaluer_deblocages(gs, "j1")
    n2 = D.evaluer_deblocages(gs, "j1")
    check("1ᵉ éval ouvre poser_bac", "poser_bac" in n1)
    check("2ᵉ éval ne re-signale rien de déjà ouvert", "poser_bac" not in n2)


def test_est_debloque():
    print("\n[8] est_debloque : BASE toujours, GATED seulement après ouverture")
    gs = {}
    check("BASE ouvert même sans couche", D.est_debloque(gs, "j1", "planter"))
    check("GATED fermé sans couche", not D.est_debloque(gs, "j1", "greffer"))
    _poser_palier(gs, "j1", "greffe", 1)
    D.evaluer_deblocages(gs, "j1")
    check("greffer ouvert après palier greffe", D.est_debloque(gs, "j1", "greffer"))


def test_noop_golden():
    print("\n[9] no-op golden : sans opt-in joueur, aucune clé créée")
    gs = {}
    # lecture pure : ne doit RIEN créer dans game_state (préserve le no-op golden)
    _ = D.est_debloque(gs, "j1", "planter")
    _ = D.gestes_debloques(gs, "j1")
    check("aucune clé gestes_debloques après lectures pures",
          "gestes_debloques" not in gs)


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Golden JOUEUR Déblocage des gestes (palette ①)")
    print("=" * 60)
    test_base()
    test_voie_savoir()
    test_voie_action()
    test_chaine_secateur()
    test_condition_composee()
    test_voie_evenement()
    test_idempotence()
    test_est_debloque()
    test_noop_golden()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
