"""
SYMBIOSE — tests/test_palette.py
Golden JOUEUR du LAYOUT de palette + MACROS (palette de gestes, tronçon ⑤). Distinct
du golden ÉCOLOGIQUE (`tests/test_golden.py`) : cette couche vit dans
`game_state["palette"]`, AU-DESSUS du tick, et ne fait JAMAIS avancer la simulation
(miroir de `test_deblocage.py`). Déterministe SANS RNG : on POSE un layout par appel
d'API, puis on vérifie la validation de cohérence de cible + la persistance.

Vérifie :
  1. Cohérence de cible : famille par verbe ; macro mono-famille OK, mixte refusée ;
     vide / 1 geste trivialement cohérente ; verbe absent = sa propre famille.
  2. Nouvel avatar → layout par défaut (slots vides, macros vides).
  3. Persistance : `definir_palette` écrit slots + macros (curation complète = REMPLACE).
  4. Transaction : une macro incohérente refuse EN BLOC, rien n'est écrit.
  5. Validation de forme : slots non-str refusés, macro sans séquence refusée.
  6. Lecture pure `palette_layout` : un avatar sans couche → défaut SANS écrire.
  7. No-op golden : lectures pures ne créent aucune clé `palette`.
"""
from __future__ import annotations

from sim.actions import palette as P

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def test_familles():
    print("\n[1] cohérence de cible : familles par verbe")
    check("planter → plot", P.famille_cible("planter") == "plot")
    check("recolter → plante", P.famille_cible("recolter") == "plante")
    check("grelinette → global", P.famille_cible("grelinette") == "global")
    check("verbe inconnu = sa propre famille",
          P.famille_cible("verbe_x") == "verbe_x")
    check("macro mono-famille (plot) cohérente",
          P.macro_coherente(["planter", "pailler", "arroser"]))
    check("macro mixte (plot+plante) INCOHÉRENTE",
          not P.macro_coherente(["planter", "recolter"]))
    check("macro vide triviale", P.macro_coherente([]))
    check("macro 1 geste triviale", P.macro_coherente(["planter"]))


def test_defaut():
    print("\n[2] nouvel avatar → layout par défaut")
    gs = {}
    lay = P.init_palette(gs, "j1")
    check("slots vides + macros vides", lay == {"slots": [], "macros": []},
          f"{lay}")


def test_persistance():
    print("\n[3] persistance : slots + macros écrits (curation = REMPLACE)")
    gs = {}
    ok, msg = P.definir_palette(gs, "j1", slots=["planter", "arroser"],
                                macros=[{"nom": "trou",
                                         "sequence": ["planter", "pailler"]}])
    check("écriture cohérente ok", ok, msg)
    lay = P.palette_layout(gs, "j1")
    check("slots persistés", lay["slots"] == ["planter", "arroser"])
    check("macro persistée", lay["macros"] == [{"nom": "trou",
                                                "sequence": ["planter", "pailler"]}])
    # curation COMPLÈTE : un nouvel appel slots=[…] REMPLACE (pas de patch).
    P.definir_palette(gs, "j1", slots=["manger"])
    check("slots remplacés (curation complète)",
          P.palette_layout(gs, "j1")["slots"] == ["manger"])
    check("macros intactes (arg None = clé inchangée)",
          P.palette_layout(gs, "j1")["macros"] == [{"nom": "trou",
                                                    "sequence": ["planter", "pailler"]}])


def test_transaction():
    print("\n[4] transaction : macro incohérente refusée EN BLOC")
    gs = {}
    P.definir_palette(gs, "j1", slots=["planter"])
    ok, msg = P.definir_palette(gs, "j1", slots=["arroser"],
                                macros=[{"nom": "x",
                                         "sequence": ["planter", "recolter"]}])
    check("refus (macro mixte)", not ok, msg)
    check("rien écrit : slots inchangés",
          P.palette_layout(gs, "j1")["slots"] == ["planter"])


def test_forme():
    print("\n[5] validation de forme")
    gs = {}
    ok, _ = P.definir_palette(gs, "j1", slots=["planter", 3])
    check("slots non-str refusés", not ok)
    ok, _ = P.definir_palette(gs, "j1", macros=[{"nom": "x", "sequence": []}])
    check("macro sans séquence refusée", not ok)
    ok, _ = P.definir_palette(gs, "j1", macros=["pas un objet"])
    check("macro non-objet refusée", not ok)


def test_lecture_pure():
    print("\n[6] lecture pure : avatar sans couche → défaut SANS écrire")
    gs = {}
    lay = P.palette_layout(gs, "j1")
    check("défaut renvoyé", lay == {"slots": [], "macros": []})
    check("aucune clé palette créée", "palette" not in gs)


def test_noop_golden():
    print("\n[7] no-op golden : lectures pures ne créent aucune clé")
    gs = {}
    _ = P.palette_layout(gs, "j1")
    _ = P.macro_coherente(["planter", "arroser"])
    check("aucune clé palette après lectures pures", "palette" not in gs)


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Golden JOUEUR Palette de gestes (macros ⑤)")
    print("=" * 60)
    test_familles()
    test_defaut()
    test_persistance()
    test_transaction()
    test_forme()
    test_lecture_pure()
    test_noop_golden()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
