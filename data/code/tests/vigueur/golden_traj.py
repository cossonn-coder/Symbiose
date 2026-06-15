"""
SYMBIOSE — tests/vigueur/golden_traj.py
B. Golden de trajectoire (hash) — cadencement régen vs refill via l'engine. On
pilote une vraie boucle sur une fenêtre qui traverse une frontière de saison
(régen sur la pente + snap du refill) et on hashe la trajectoire `courante`
semaine par semaine : toute dérive du cadencement du hook casse le hash.
"""
import os
import sys
import hashlib

from sim.engine import Engine
from sim import vigueur as V

from .harness import check, _minimal_state

# Le fichier de référence vit dans tests/ (parent de ce paquet) — chemin stable
# malgré l'éclatement (l'ex-monolithe le posait au même endroit).
HASH_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vigueur_hash.txt")


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
