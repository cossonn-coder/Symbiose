"""
SYMBIOSE — tests/test_journal.py
Test du LEDGER d'événements (sprint Voix narratives, tronçon ②).
Spec : `docs/narration/voix/conception_voix_narratives.md` §1.3/§1.4 + kickoff
`sprints/narration/voix/sprint_voix_narratives/02_journal.md`.

Trois propriétés (les trois exigées par la « Définition de done » du kickoff) :
  A. OPT-IN — `consigner` sur un game_state SANS appel préalable n'écrit la clé
     `journal` que parce que c'est `consigner` lui-même qui la crée ; surtout,
     un game_state qu'on ne touche pas reste SANS clé (preuve du no-op golden).
  B. ACCUMULATION — à partir d'un log jouet, les entrées s'ajoutent au bon joueur,
     portent (semaine, zone, kind, cause, espèce).
  C. BORNAGE — au-delà de JOURNAL_MAX, la plus ancienne se replie dans
     `resume[(kind, cause)]` et `entries` ne croît plus.

Logs JOUETS au format EXACT du moteur (cf. tests/test_evenements.py). Parsing pur,
aucun RNG → déterminisme total.

Usage (depuis data/code/) :
  python3 -m tests.test_journal
"""
from sim import journal as J

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


# --- Fabriques de lignes au FORMAT RÉEL du moteur (réutilise le format ①) -----
def _entete(tid="T0"):
    return f"  [{tid}]"


def _l_avance(nom, r, c):
    return f"    🌱 {nom}@({r}, {c}) → [pousse] (hum=0.50 lum=0.80 t=18.0°C)"


def _l_stagne_sec(nom, r, c):
    return f"    ⏸  {nom}@({r}, {c}) stagne (sec hum=0.10)"


# ---------------------------------------------------------------------------
# A. Opt-in / no-op golden
# ---------------------------------------------------------------------------

def test_opt_in_no_op():
    print("\n[A] opt-in : pas de joueur consigné → pas de clé journal (no-op golden)")
    gs = {}                                       # game_state vierge (≈ golden écolo)
    check("game_state vierge n'a AUCUNE clé journal", "journal" not in gs)
    # `palier`/lecture pure ne doit jamais créer la clé non plus : ici on n'appelle
    # que ce qui DOIT rester no-op. `consigner`, lui, est le geste explicite du
    # driver (un joueur existe) — il crée la clé, c'est attendu.
    J.consigner(gs, "joueur_1", [], 1)            # log vide → aucune entrée
    check("consigner avec joueur crée la tranche (opt-in du driver)",
          "journal" in gs and "joueur_1" in gs["journal"])
    st = gs["journal"]["joueur_1"]
    check("log vide → 0 entrée, resume vide",
          st["entries"] == [] and st["resume"] == {}, f"{st}")


# ---------------------------------------------------------------------------
# B. Accumulation
# ---------------------------------------------------------------------------

def test_accumulation():
    print("\n[B] accumulation : un log jouet → des entrées datées et typées")
    gs = {}
    log_s10 = [_entete("T0"), _l_avance("Tomate", 2, 2), _l_stagne_sec("Basilic", 3, 1)]
    n1 = J.consigner(gs, "joueur_1", log_s10, 10)
    check("2 événements consignés", n1 == 2, f"n1={n1}")
    log_s11 = [_entete("T1"), _l_avance("Haricot", 0, 0)]
    n2 = J.consigner(gs, "joueur_1", log_s11, 11)
    check("la semaine suivante s'ajoute (append-only)", n2 == 1)
    st = gs["journal"]["joueur_1"]
    check("3 entrées au total", len(st["entries"]) == 3, f"{len(st['entries'])}")
    e0 = st["entries"][0]
    check("entrée 0 datée semaine 10, zone (T0,2,2)",
          e0["semaine"] == 10 and e0["zone"] == ("T0", 2, 2), f"{e0}")
    check("entrée 0 = germination tomate",
          e0["kind"] == "germination" and e0["espece"] == "tomate", f"{e0}")
    e1 = st["entries"][1]
    check("entrée 1 = stagnation sec basilic",
          e1["kind"] == "stagnation" and e1["cause"] == "sec"
          and e1["espece"] == "basilic", f"{e1}")
    e2 = st["entries"][2]
    check("entrée 2 datée semaine 11, zone (T1,0,0)",
          e2["semaine"] == 11 and e2["zone"] == ("T1", 0, 0), f"{e2}")
    # Isolation par avatar : un autre joueur a sa propre tranche.
    J.consigner(gs, "joueur_2", log_s10, 10)
    check("joueur_2 a sa propre tranche, joueur_1 inchangé",
          len(gs["journal"]["joueur_2"]["entries"]) == 2
          and len(gs["journal"]["joueur_1"]["entries"]) == 3)


# ---------------------------------------------------------------------------
# C. Bornage → resume
# ---------------------------------------------------------------------------

def test_bornage():
    print("\n[C] bornage : au-delà de JOURNAL_MAX, la plus ancienne se replie")
    gs = {}
    st = J.ensure_player(gs, "joueur_1")
    # On injecte JOURNAL_MAX + 3 germinations de tomate (cause None), une par
    # semaine, en passant par _appender (chemin de bornage testé directement).
    total = J.JOURNAL_MAX + 3
    for sem in range(total):
        J._appender(st, {"semaine": sem, "zone": ("T0", 0, 0),
                         "kind": "germination", "cause": None, "espece": "tomate"})
    check("entries plafonné à JOURNAL_MAX",
          len(st["entries"]) == J.JOURNAL_MAX, f"{len(st['entries'])}")
    check("3 plus anciennes repliées dans resume[(germination, None)]",
          st["resume"].get(("germination", None)) == 3, f"{st['resume']}")
    check("la plus ancienne entrée RESTANTE est la semaine 3 (0,1,2 repliées)",
          st["entries"][0]["semaine"] == 3, f"{st['entries'][0]}")
    check("la plus récente est la dernière injectée",
          st["entries"][-1]["semaine"] == total - 1, f"{st['entries'][-1]}")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Ledger d'événements (Voix narratives ②)")
    print("=" * 60)
    test_opt_in_no_op()
    test_accumulation()
    test_bornage()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
