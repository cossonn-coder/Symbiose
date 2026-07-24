"""
SYMBIOSE — tests/test_quetes.py
Golden JOUEUR du SYSTÈME DE QUÊTES (D79, tronçon ①) — famille de conditions
`recolte_cumulee`, comptée par HOOK sur le geste joueur.

Distinct du golden ÉCOLOGIQUE (`test_golden.py`) : le moteur tourne sans joueur ni
quête → `notifier_geste` n'est jamais appelé → golden NEUTRE (vérifié à part).

Vérifie (kickoff ①) :
  1. `recolte_cumulee(recolter, 3, "tomate")` : 3 récoltes → accomplie + événement
     émis au log (canal ledger).
  2. Une récolte d'une AUTRE espèce n'incrémente pas.
  3. Un geste d'un AUTRE verbe n'incrémente pas.
  4. Ordre déterministe (quêtes actives triées par `id`).
  5. Opt-in strict : aucune quête → aucune clé `quetes` → notifier no-op.

Usage (depuis data/code/) :
  python3 -m tests.test_quetes
"""
from sim import quetes as Q
from plants.catalogue import PLANT_CATALOGUE

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


class _FakePlante:
    """Plante-cible minimale : le hook ne lit que `plant_class` (comme
    `objectifs.sert`). On évite ainsi tout montage de monde."""

    def __init__(self, cle):
        self.plant_class = PLANT_CATALOGUE[cle]


# ---------------------------------------------------------------------------
# 1. 3 récoltes de tomate → accomplie + événement émis
# ---------------------------------------------------------------------------

def test_accomplissement_et_evenement():
    print("\n[1] recolte_cumulee(recolter, 3, tomate) : 3 récoltes → accomplie + log")
    gs = {"week": 5, "log": []}
    q = Q.Quete(id="q_patates", donneur="Marcel",
                condition=("recolte_cumulee", "recolter", 3, "tomate"))
    Q.ajouter_quete(gs, q)
    tomate = _FakePlante("tomate")
    for i in range(2):
        Q.notifier_geste(gs, "j", "recolter", tomate)
        check(f"après {i + 1} récolte(s), pas encore accomplie",
              not Q.est_accomplie(gs, "q_patates"),
              f"progression={Q.progression(gs, 'q_patates')}")
    Q.notifier_geste(gs, "j", "recolter", tomate)   # la 3ᵉ
    check("3ᵉ récolte → accomplie", Q.est_accomplie(gs, "q_patates"),
          f"progression={Q.progression(gs, 'q_patates')}")
    check("événement ✉ émis au log", any("✉" in l for l in gs["log"]),
          f"log={gs['log']}")
    check("quête accomplie sortie des actives", Q.quetes_actives(gs) == [])
    # Une récolte SUPPLÉMENTAIRE ne ré-incrémente pas (fenêtre close).
    Q.notifier_geste(gs, "j", "recolter", tomate)
    check("après clôture, la progression est figée",
          Q.progression(gs, "q_patates") == 3,
          f"progression={Q.progression(gs, 'q_patates')}")
    check("un seul événement émis (pas de re-déclenchement)",
          sum("✉" in l for l in gs["log"]) == 1)


# ---------------------------------------------------------------------------
# 2. Autre espèce → pas d'incrément
# ---------------------------------------------------------------------------

def test_autre_espece_ignoree():
    print("\n[2] récolte d'une AUTRE espèce → pas d'incrément")
    gs = {"week": 1, "log": []}
    Q.ajouter_quete(gs, Q.Quete(id="q", donneur="M",
                    condition=("recolte_cumulee", "recolter", 2, "tomate")))
    Q.notifier_geste(gs, "j", "recolter", _FakePlante("basilic"))
    check("basilic ne sert pas une quête de tomate",
          Q.progression(gs, "q") == 0, f"progression={Q.progression(gs, 'q')}")


# ---------------------------------------------------------------------------
# 3. Autre verbe → pas d'incrément
# ---------------------------------------------------------------------------

def test_autre_verbe_ignore():
    print("\n[3] geste d'un AUTRE verbe → pas d'incrément")
    gs = {"week": 1, "log": []}
    Q.ajouter_quete(gs, Q.Quete(id="q", donneur="M",
                    condition=("recolte_cumulee", "recolter", 2, "tomate")))
    Q.notifier_geste(gs, "j", "manger", _FakePlante("tomate"))
    check("manger ne sert pas une quête de récolte",
          Q.progression(gs, "q") == 0, f"progression={Q.progression(gs, 'q')}")


# ---------------------------------------------------------------------------
# 4. Ordre déterministe des quêtes actives
# ---------------------------------------------------------------------------

def test_ordre_deterministe():
    print("\n[4] quetes_actives triées par id (déterminisme)")
    gs = {"week": 1, "log": []}
    for qid in ("q_c", "q_a", "q_b"):
        Q.ajouter_quete(gs, Q.Quete(id=qid, donneur="M",
                        condition=("recolte_cumulee", "recolter", 1, "tomate")))
    ids = [q.id for q in Q.quetes_actives(gs)]
    check("ordre trié par id", ids == ["q_a", "q_b", "q_c"], f"ids={ids}")


# ---------------------------------------------------------------------------
# 5. Opt-in strict : aucune quête → notifier no-op
# ---------------------------------------------------------------------------

def test_opt_in_strict():
    print("\n[5] opt-in strict : aucune quête → aucune clé, notifier no-op")
    gs = {"week": 1, "log": []}
    Q.notifier_geste(gs, "j", "recolter", _FakePlante("tomate"))
    check("aucune clé 'quetes' créée par le seul hook", "quetes" not in gs)
    check("aucun événement émis", gs["log"] == [])


def main():
    print("=== test_quetes (D79 ①) ===")
    test_accomplissement_et_evenement()
    test_autre_espece_ignoree()
    test_autre_verbe_ignore()
    test_ordre_deterministe()
    test_opt_in_strict()

    total = len(_results)
    ok = sum(1 for _, c in _results if c)
    print(f"\n{ok}/{total} checks OK")
    if ok != total:
        for name, c in _results:
            if not c:
                print(f"  ÉCHEC : {name}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
