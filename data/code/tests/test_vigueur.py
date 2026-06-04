"""
SYMBIOSE — tests/test_vigueur.py
Golden JOUEUR de la couche Vigueur (D11, sous-sprint 1) — distinct du golden
ÉCOLOGIQUE (`tests/test_golden.py`).

La couche Vigueur joueur vit dans `game_state["vigueur"]`, AU-DESSUS du tick, et
ne doit JAMAIS faire avancer la simulation écologique (CONCEPTION_VIGUEUR.md
§0/§5). Deux familles de vérifications :

  A. Contrats de la couche (déterministes, sans RNG) :
     1. No-op golden : un `game_state` SANS clé `vigueur` ne se voit JAMAIS
        injecter de Vigueur par le tick (c'est ce qui garde le golden écolo
        intact — si ce contrat casse, le golden bouge).
     2. Régen plafonnée : +REGEN_BASE/semaine, jamais au-dessus de vigueur_max.
     3. Refill saison : `courante = vigueur_max` quel que soit l'état antérieur.
     4. Interface paliers stubbée : palier_bonus == 1.0 ; vigueur_max / regen_rate
        en dépendent.

  B. Golden de trajectoire : on pilote une vraie boucle `engine` sur une fenêtre
     qui traverse une frontière de saison (régen sur la pente + snap du refill),
     et on hashe la trajectoire `courante` semaine par semaine. Toute dérive du
     cadencement du hook (mauvaise semaine de refill, double régen…) casse le
     hash.

Usage (depuis data/code/) :
  python3 -m tests.test_vigueur            # vérifie contre vigueur_hash.txt
  python3 -m tests.test_vigueur --capture  # (re)capture le hash de référence
"""
import sys
import os
import hashlib

from world import Tile
from plants import Tomato, Basil, Bean
from fields import init_eco
from sim.engine import Engine
from sim import vigueur as V

SEED = 0x5AB1057E
HASH_FILE = os.path.join(os.path.dirname(__file__), "vigueur_hash.txt")
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _minimal_state(week=1):
    """Monde minimal (1 tuile, 3 plantes) — assez pour tourner le tick à coût
    négligeable. Sert de support à l'intégration de la couche Vigueur."""
    tile = Tile(tile_id="T0", soil_type="terre")
    eco = init_eco("T0", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
    tile.add_plant(Tomato, 2, 2)
    tile.add_plant(Basil, 2, 4)
    tile.add_plant(Bean, 4, 2)
    return {
        "tiles": [tile], "eco": {"T0": eco}, "scores": {},
        "current_player": "joueur_1", "week": week, "log": [], "seed": SEED,
    }


# ---------------------------------------------------------------------------
# A1. No-op golden : pas de joueur ⇒ le tick n'injecte JAMAIS de Vigueur
# ---------------------------------------------------------------------------

def test_noop_sans_joueur():
    print("\n[A1] sans couche joueur, le tick reste un no-op strict")
    gs = _minimal_state()
    eng = Engine(gs)
    for _ in range(20):
        eng.tick_semaine()
    check("aucune clé `vigueur` créée par le tick", "vigueur" not in gs,
          f"clés={sorted(gs.keys())}")


# ---------------------------------------------------------------------------
# A2. Régen plafonnée
# ---------------------------------------------------------------------------

def test_regen_plafonnee():
    print("\n[A2] régen passive +REGEN_BASE/semaine, plafonnée à vigueur_max")
    gs = {}
    st = V.ensure_player(gs, "joueur_1")
    st["courante"] = 0.0
    V.tick_player_vigueur(gs)
    check("première semaine : 0 → REGEN_BASE", st["courante"] == V.REGEN_BASE,
          f"courante={st['courante']}")
    # On régénère jusqu'au plafond et on vérifie qu'on n'overshoote pas.
    for _ in range(50):
        V.tick_player_vigueur(gs)
    cap = V.vigueur_max(gs, "joueur_1")
    check("plafonnée à vigueur_max (pas d'overshoot)", st["courante"] == cap,
          f"courante={st['courante']} cap={cap}")


# ---------------------------------------------------------------------------
# A3. Refill saison
# ---------------------------------------------------------------------------

def test_refill_saison():
    print("\n[A3] passage de saison : courante = vigueur_max")
    gs = {}
    st = V.ensure_player(gs, "joueur_1")
    st["courante"] = 12.5
    V.refill_saison(gs)
    check("refill → vigueur_max", st["courante"] == V.vigueur_max(gs, "joueur_1"),
          f"courante={st['courante']}")


# ---------------------------------------------------------------------------
# A4. Interface paliers stubbée
# ---------------------------------------------------------------------------

def test_interface_paliers():
    print("\n[A4] interface paliers (D12) stubbée à 1.0")
    check("palier_bonus == 1.0", V.palier_bonus("joueur_1") == 1.0)
    gs = {}
    V.ensure_player(gs, "joueur_1")
    check("vigueur_max == max_base × palier_bonus",
          V.vigueur_max(gs, "joueur_1") == V.MAX_BASE * V.palier_bonus("joueur_1"))
    check("regen_rate == REGEN_BASE × palier_bonus",
          V.regen_rate(gs, "joueur_1") == V.REGEN_BASE * V.palier_bonus("joueur_1"))


# ---------------------------------------------------------------------------
# B. Golden de trajectoire (hash) — cadencement régen vs refill via l'engine
# ---------------------------------------------------------------------------

def _trajectoire() -> list[float]:
    """Pilote l'engine de la semaine 2 à la 29 (traverse été@14 et automne@27).
    `max_base` volontairement haut (régen ne sature pas dans la fenêtre) → le
    snap du refill est visiblement distinct de la pente de régen."""
    gs = _minimal_state(week=2)
    st = V.ensure_player(gs, "joueur_1")
    st["max_base"] = 1000.0
    st["courante"] = 0.0
    eng = Engine(gs)
    traj = []
    for _ in range(28):
        eng.tick_semaine()
        traj.append(round(gs["vigueur"]["joueur_1"]["courante"], 6))
    return traj


def _compute_hash() -> str:
    traj = _trajectoire()
    h = hashlib.sha256()
    h.update(repr(traj).encode("utf-8"))
    return h.hexdigest()


def test_golden_trajectoire():
    print("\n[B] golden de trajectoire (hash de la courbe de Vigueur)")
    traj = _trajectoire()
    # Sanity diégétique avant le hash : pente +10, snap aux frontières de saison.
    # Semaines 2..13 = régen (0→10→…→120), semaine 14 (été) = refill@1000.
    check("régen linéaire +REGEN_BASE en début de fenêtre",
          traj[0] == 10.0 and traj[1] == 20.0 and traj[2] == 30.0,
          f"début={traj[:3]}")
    # Index 12 = semaine 14 (été, début de saison) → refill au plafond.
    check("refill au passage de saison (été)", traj[12] == 1000.0,
          f"traj[12]={traj[12]}")

    digest = _compute_hash()
    capture = "--capture" in sys.argv
    if capture or not os.path.exists(HASH_FILE):
        with open(HASH_FILE, "w") as f:
            f.write(digest + "\n")
        check(f"hash de référence capturé", True, digest)
        return
    with open(HASH_FILE) as f:
        ref = f.read().strip()
    check("hash de trajectoire == référence", digest == ref,
          digest if digest == ref else f"attendu {ref} obtenu {digest}")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Golden JOUEUR Vigueur (D11, sous-sprint 1)")
    print("=" * 60)
    test_noop_sans_joueur()
    test_regen_plafonnee()
    test_refill_saison()
    test_interface_paliers()
    test_golden_trajectoire()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
