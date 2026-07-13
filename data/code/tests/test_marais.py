"""
SYMBIOSE — tests/test_marais.py
Tests ciblés de la MÉMOIRE DE MARÉCAGE (sprint hydrologie & marécages ③).
Exercent `EcoFields.tick_marais`, `est_marais`, et les effets sur la décompo
(`decomp_speed`) et le pH (`tick_ph`), hors golden, sur des champs forcés.

Couvre :
  1. ENTRÉE : une flaque (eau_surface > SEUIL_FLAQUE) entretenue fait MONTER
     `marais_memory` vers 1 ; passé MARAIS_ON, `est_marais` bascule à True.
  2. HYSTÉRÈSE : une fois installé, le marais ne RESSORT qu'une fois la mémoire
     retombée sous MARAIS_OFF (zone morte [OFF, ON) → pas de clignotement). Entre
     les seuils, l'état PRÉCÉDENT est conservé.
  3. LENTEUR : la bascule prend plusieurs ticks (MARAIS_LERP lent) — pas d'averse.
  4. REPOS NEUTRE : eau_surface nulle + mémoire nulle → tick no-op (golden neutre).
  5. EFFET DÉCOMPO : `decomp_speed` est raboté ∝ marais_memory (anaérobie).
  6. EFFET pH : `tick_ph` tire le pH vers l'acide (PH_TOURBE) en marais.

Usage (depuis data/code/) : python3 -m tests.test_marais
"""
import sys

from fields import EcoFields
from fields.ecofields.ph import tick_ph
from fields.ecofields.constants import (SEUIL_FLAQUE, MARAIS_ON, MARAIS_OFF,
                                        PH_TOURBE)

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _eco(rows=3, cols=3):
    """EcoFields nu (construction directe : marais_memory nulle, eau_surface nulle)."""
    return EcoFields(tile_id="M0", rows=rows, cols=cols)


# ---------------------------------------------------------------------------
# 1. Entrée en marais + 3. lenteur de la bascule
# ---------------------------------------------------------------------------
def test_entree_marais():
    print("\n[1/3] entrée en marais : une flaque entretenue fait monter la mémoire (lentement)")
    eco = _eco()
    eco.eau_surface.fill(1.0)                 # flaque franche, entretenue à chaque tick
    # 1 seul tick ne suffit PAS à franchir MARAIS_ON (bascule lente).
    eco.tick_marais()
    m1 = eco.marais_memory.at_plot(1, 1)
    check("bascule LENTE : 1 tick ne fait pas encore un marais", not eco.est_marais(1, 1),
          f"marais_memory={m1:.3f} après 1 tick")
    check("la mémoire MONTE dès le 1er tick", m1 > 0.0, f"m1={m1:.4f}")
    # Assez de ticks (flaque maintenue) → la mémoire franchit MARAIS_ON.
    for _ in range(60):
        eco.eau_surface.fill(1.0)             # la flaque persiste
        eco.tick_marais()
    m2 = eco.marais_memory.at_plot(1, 1)
    check("flaque durable → mémoire > MARAIS_ON", m2 > MARAIS_ON, f"marais_memory={m2:.3f}")
    check("est_marais bascule à True", eco.est_marais(1, 1), f"est_marais={eco.est_marais(1, 1)}")


# ---------------------------------------------------------------------------
# 2. Hystérèse : sortie retardée
# ---------------------------------------------------------------------------
def test_hysterese():
    print("\n[2] hystérèse : un marais installé ne ressort qu'une fois la mémoire sous MARAIS_OFF")
    eco = _eco()
    # Marais DÉJÀ installé (mémoire au-dessus de ON, état vrai).
    eco.marais_memory.fill(0.9)
    eco.eau_surface.fill(1.0)
    eco.tick_marais()
    check("marais installé au départ", eco.est_marais(1, 1))
    # On coupe la flaque : la mémoire redescend, mais l'état RESTE vrai tant que
    # marais_memory ∈ [MARAIS_OFF, MARAIS_ON) — zone morte anti-clignotement.
    eco.eau_surface.fill(0.0)
    encore_marais_en_zone_morte = None
    for _ in range(200):
        eco.tick_marais()
        m = eco.marais_memory.at_plot(1, 1)
        if MARAIS_OFF <= m < MARAIS_ON and encore_marais_en_zone_morte is None:
            encore_marais_en_zone_morte = eco.est_marais(1, 1)
        if m < MARAIS_OFF:
            break
    check("en zone morte [OFF, ON), l'état RESTE marais (hystérèse)",
          encore_marais_en_zone_morte is True,
          f"observé={encore_marais_en_zone_morte}")
    check("sous MARAIS_OFF, le marais RESSORT enfin",
          not eco.est_marais(1, 1),
          f"marais_memory={eco.marais_memory.at_plot(1, 1):.3f}, est_marais={eco.est_marais(1, 1)}")


# ---------------------------------------------------------------------------
# 4. Repos NEUTRE
# ---------------------------------------------------------------------------
def test_repos_neutre():
    print("\n[4] repos NEUTRE : aucune flaque + mémoire nulle → tick no-op")
    eco = _eco()
    eco.tick_marais()   # eau_surface nulle, marais_memory nulle
    tot = sum(v for row in eco.marais_memory.data for v in row)
    check("marais_memory reste nulle partout", tot == 0.0, f"total={tot}")
    check("aucun plot en marais", not any(
        eco.est_marais(r, c) for r in range(eco.rows) for c in range(eco.cols)))


# ---------------------------------------------------------------------------
# 5. Effet DÉCOMPO (anaérobie)
# ---------------------------------------------------------------------------
def test_effet_decompo():
    print("\n[5] anaérobie : le marais rabote decomp_speed ∝ marais_memory")
    eco = _eco()
    eco.microbiome.fill(1.5)               # même sol vivant sur les deux plots testés
    sec = eco.decomp_speed(0, 0)           # marais_memory=0 → vitesse de référence
    eco.marais_memory.set(1, 1, 1.0)       # marais PLEIN sur (1,1)
    marais = eco.decomp_speed(1, 1)
    check("decomp_speed du marais < sol sec (anaérobie)", marais < sec,
          f"marais={marais:.3f} < sec={sec:.3f}")
    check("marais plein rabote fortement la décompo", marais < sec * 0.6,
          f"ratio={marais / sec:.3f}")


# ---------------------------------------------------------------------------
# 6. Effet pH (acidification tourbeuse)
# ---------------------------------------------------------------------------
def test_effet_ph():
    print("\n[6] acidification : le pH d'un plot en marais est tiré vers PH_TOURBE")
    eco = _eco()
    eco.ph.fill(6.8)                       # pH de départ neutre partout
    eco.marais_memory.set(1, 1, 1.0)       # (1,1) en marais plein ; (0,0) sec (référence)
    for _ in range(300):                   # dérive décennale lente → plusieurs ticks
        tick_ph(eco)
    ph_sec = eco.ph.at_plot(0, 0)
    ph_marais = eco.ph.at_plot(1, 1)
    check("pH du marais < pH du plot sec (acidification)", ph_marais < ph_sec,
          f"marais={ph_marais:.3f} < sec={ph_sec:.3f}")
    check("pH du marais tend vers PH_TOURBE (acide)", ph_marais < 6.0,
          f"ph_marais={ph_marais:.3f}, PH_TOURBE={PH_TOURBE}")


if __name__ == "__main__":
    print("=" * 64)
    print("SYMBIOSE — tests marécage (mémoire + hystérèse + effets ③)")
    print("=" * 64)
    test_entree_marais()
    test_hysterese()
    test_repos_neutre()
    test_effet_decompo()
    test_effet_ph()
    print("\n" + "=" * 64)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 64)
    sys.exit(0 if passed == total else 1)
