"""
SYMBIOSE — tests/test_automate_determinisme.py
Verrous de DÉTERMINISME du jardinier automate (tronçon ①, philo #3).
Spec : docs/conception/CONCEPTION_JARDINIER_AUTOMATE.md §10 + kickoff
sprints/sprint_jardinier_auto/01_socle.md.

Trois propriétés :
  A. REJEU IDENTIQUE — deux moteurs neufs, même seed, joués N ticks avec un
     automate frais chacun → journaux JSON strictement égaux (aucun RNG, tri
     stable à clé totale).
  B. AUTOMATE OFF = GOLDEN — le simple fait d'importer le paquet ne bouge pas le
     hash golden (l'automate n'est jamais dans le tick : invariant H2). On
     recalcule le hash golden APRÈS import et on le compare à la référence figée.
  C. PAS D'EFFET DE BORD — ticker un moteur SANS appeler l'automate ne crée jamais
     la clé de journal `automate_journal` (opt-in strict).

Usage (depuis data/code/) :
  python3 -m tests.test_automate_determinisme
"""
from __future__ import annotations
import json

from tools.jardinier_auto import JardinierAutomate, LIBRE
from tools.jardinier_auto.trace import CLE_JOURNAL, journal

_SEED = 0x5AB1057E
_WEEKS = 60

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _build_engine():
    """Monte le monde 'full' via SimServer (fabrique du F5), déterministe pour
    un seed donné."""
    from tools.simserver.server import SimServer
    srv = SimServer()
    rep = srv.cmd_init({"config": "full", "seed": _SEED})
    assert rep.get("ok"), rep
    return srv.engine


def _jouer(weeks: int) -> list:
    """Un moteur neuf joué `weeks` ticks avec un automate LIBRE frais ; renvoie
    le journal consigné."""
    engine = _build_engine()
    automate = JardinierAutomate(LIBRE)
    for _ in range(weeks):
        engine.tick_semaine()
        automate.jouer_tick(engine)
    return journal(engine.game_state)


def test_rejeu_identique():
    j1 = _jouer(_WEEKS)
    j2 = _jouer(_WEEKS)
    s1, s2 = json.dumps(j1, sort_keys=True), json.dumps(j2, sort_keys=True)
    check("A. rejeu identique", s1 == s2,
          f"{len(j1)} entrées, journaux {'égaux' if s1 == s2 else 'DIVERGENTS'}")


def test_automate_off_golden():
    """Le paquet est déjà importé en tête de module. On recalcule le hash golden
    et on le compare à la référence figée : import ⇒ zéro effet sur le tick."""
    from tests.test_golden import compute_hash, HASH_FILE
    with open(HASH_FILE) as f:
        ref = f.read().strip()
    got = compute_hash()
    check("B. automate OFF = golden bit-identique", got == ref,
          f"{got[:16]}… vs {ref[:16]}…")


def test_pas_effet_de_bord():
    engine = _build_engine()
    for _ in range(4):
        engine.tick_semaine()          # AUCUN jouer_tick
    absent = CLE_JOURNAL not in engine.game_state
    check("C. pas d'effet de bord (opt-in strict)", absent,
          "clé de journal absente sans appel de l'automate")


def main() -> int:
    print("=== test_automate_determinisme (tronçon ①) ===")
    test_rejeu_identique()
    test_pas_effet_de_bord()
    test_automate_off_golden()
    ko = [n for n, ok in _results if not ok]
    if ko:
        print(f"[determinisme] FAIL — {len(ko)} échec(s) : {ko}")
        return 1
    print(f"[determinisme] PASS — {len(_results)} vérifs OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
