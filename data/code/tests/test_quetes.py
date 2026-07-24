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
    `objectifs.sert`). On évite ainsi tout montage de monde. Les conditions d'état
    (②) lisent en plus `is_alive` / `current_height` (cm) / `floraison` — attributs
    plats posés ici en duck-typing (le vrai `PlantInstance` les expose en propriétés)."""

    def __init__(self, cle, is_alive=True, current_height=0.0, floraison=0.0):
        self.plant_class = PLANT_CATALOGUE[cle]
        self.is_alive = is_alive
        self.current_height = current_height
        self.floraison = floraison


class _FakeTile:
    """Tuile-snapshot minimale : `evaluer_etat` n'itère que `tile.plants`."""

    def __init__(self, plants):
        self.plants = list(plants)


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


# ---------------------------------------------------------------------------
# 6. hauteur_min : snapshot, prédicat current_height (cm), mètres → cm
# ---------------------------------------------------------------------------

def _gs_snapshot(plants, week=3):
    return {"week": week, "log": [], "tiles": [_FakeTile(plants)]}


def test_hauteur_min():
    print("\n[6] hauteur_min(tournesol, 2 m) sur snapshot")
    q = Q.Quete(id="q_h", donneur="Léa",
                condition=("hauteur_min", "tournesol", 2.0))
    # En deçà (1 m = 100 cm < 200) → non accomplie, phrase diégétique sans chiffre.
    gs = _gs_snapshot([_FakePlante("tournesol", current_height=100.0)])
    Q.ajouter_quete(gs, q)
    Q.evaluer_etat(gs)
    check("1 m < 2 m → non accomplie", not Q.est_accomplie(gs, "q_h"))
    phrase = Q.avancement(gs, "q_h")
    check("phrase diégétique non vide et sans chiffre",
          phrase and not any(ch.isdigit() for ch in phrase), f"phrase={phrase!r}")
    # Au-delà (2,5 m = 250 cm ≥ 200) → accomplie après évaluation.
    gs = _gs_snapshot([_FakePlante("tournesol", current_height=250.0)])
    Q.ajouter_quete(gs, q)
    Q.evaluer_etat(gs)
    check("2,5 m ≥ 2 m → accomplie", Q.est_accomplie(gs, "q_h"))
    check("événement ✉ émis", any("✉" in l for l in gs["log"]))
    check("avancement d'une quête close = phrase de clôture",
          Q.avancement(gs, "q_h") and not any(c.isdigit() for c in Q.avancement(gs, "q_h")))


# ---------------------------------------------------------------------------
# 7. floraison_min : compte les pieds EN FLEUR (floraison ≥ SEUIL_FLEURI)
# ---------------------------------------------------------------------------

def test_floraison_min():
    print("\n[7] floraison_min(trefle, 3) : 3 trèfles en fleur")
    q = Q.Quete(id="q_f", donneur="Oncle",
                condition=("floraison_min", "trefle", 3))
    # 2 fleuris + 1 en dessous du seuil → non.
    gs = _gs_snapshot([_FakePlante("trefle", floraison=0.8),
                       _FakePlante("trefle", floraison=0.6),
                       _FakePlante("trefle", floraison=0.2)])
    Q.ajouter_quete(gs, q)
    Q.evaluer_etat(gs)
    check("2 < 3 fleuris → non accomplie", not Q.est_accomplie(gs, "q_f"),
          f"phrase={Q.avancement(gs, 'q_f')!r}")
    # 3 pieds au seuil → oui.
    gs = _gs_snapshot([_FakePlante("trefle", floraison=0.5) for _ in range(3)])
    Q.ajouter_quete(gs, q)
    Q.evaluer_etat(gs)
    check("3 fleuris (≥ 0.5) → accomplie", Q.est_accomplie(gs, "q_f"))


# ---------------------------------------------------------------------------
# 8. nombre_vivant_min : un mort ne compte pas
# ---------------------------------------------------------------------------

def test_nombre_vivant_min():
    print("\n[8] nombre_vivant_min(trefle, 4) : un mort ne compte pas")
    q = Q.Quete(id="q_n", donneur="Léa",
                condition=("nombre_vivant_min", "trefle", 4))
    gs = _gs_snapshot([_FakePlante("trefle") for _ in range(3)]
                      + [_FakePlante("trefle", is_alive=False)])
    Q.ajouter_quete(gs, q)
    Q.evaluer_etat(gs)
    check("3 vivants + 1 mort < 4 → non accomplie", not Q.est_accomplie(gs, "q_n"))
    gs = _gs_snapshot([_FakePlante("trefle") for _ in range(4)])
    Q.ajouter_quete(gs, q)
    Q.evaluer_etat(gs)
    check("4 vivants → accomplie", Q.est_accomplie(gs, "q_n"))


# ---------------------------------------------------------------------------
# 9. Cible absente du catalogue → non accomplie, phrase dédiée
# ---------------------------------------------------------------------------

def test_cible_absente():
    print("\n[9] cible hors catalogue (kiwi, D26) → non accomplie")
    q = Q.Quete(id="q_k", donneur="Enfant",
                condition=("hauteur_min", "kiwi", 5.0))
    gs = _gs_snapshot([])
    Q.ajouter_quete(gs, q)
    Q.evaluer_etat(gs)
    check("cible inconnue → jamais accomplie", not Q.est_accomplie(gs, "q_k"))
    check("phrase 'pas encore trouvé sa place'",
          "place" in Q.avancement(gs, "q_k"), f"phrase={Q.avancement(gs, 'q_k')!r}")


# ---------------------------------------------------------------------------
# 10. evaluer_etat : opt-in strict + n'écrit rien pour recolte_cumulee
# ---------------------------------------------------------------------------

def test_evaluer_etat_neutre():
    print("\n[10] evaluer_etat : opt-in + ignore recolte_cumulee")
    gs = {"week": 1, "log": [], "tiles": []}
    Q.evaluer_etat(gs)                       # aucune quête
    check("aucune clé 'quetes' créée", "quetes" not in gs)
    gs = _gs_snapshot([])
    Q.ajouter_quete(gs, Q.Quete(id="q", donneur="M",
                    condition=("recolte_cumulee", "recolter", 2, "tomate")))
    Q.evaluer_etat(gs)
    check("evaluer_etat ne clôt pas une quête cumulée",
          not Q.est_accomplie(gs, "q"))


def main():
    print("=== test_quetes (D79 ①②) ===")
    test_accomplissement_et_evenement()
    test_autre_espece_ignoree()
    test_autre_verbe_ignore()
    test_ordre_deterministe()
    test_opt_in_strict()
    test_hauteur_min()
    test_floraison_min()
    test_nombre_vivant_min()
    test_cible_absente()
    test_evaluer_etat_neutre()

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
