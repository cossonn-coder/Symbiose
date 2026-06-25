"""
SYMBIOSE — tests/test_mycelium.py
Tests ciblés du tronçon ① du sprint mycélium & interconnexions : le champ scalaire
`mycelium` (`EcoFields.mycelium`) + sa dynamique pure `tick_mycelium` (croissance sur
le bois humide tempéré, déclin au sec / substrat épuisé, bornage [0,1], déterminisme).

Tronçon FONDATION : le champ existe et tique, mais AUCUN rôle §2 n'est branché
(saprophyte/mycorhize/faune) → le golden ÉCOLOGIQUE reste l'autorité du déterminisme,
ici on exerce uniquement la dynamique propre du champ, hors golden.

Usage (depuis data/code/) :
  python3 -m tests.test_mycelium
"""
import sys

from fields import init_eco
from fields.ecofields import MYCEL_SUBSTRAT_REF, MYCEL_TEMP_OPT

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


# --- A. Champ présent + NUL à l'init ---
eco0 = init_eco("nul", 2, 2)
check("champ mycelium déclaré", eco0.mycelium is not None)
check("get_field('mycelium') == champ", eco0.get_field("mycelium") is eco0.mycelium)
check("mycelium nul partout à l'init",
      all(eco0.mycelium.data[r][c] == 0.0 for r in range(2) for c in range(2)))


def _tick_n(eco, n):
    for _ in range(n):
        eco.tick_mycelium()


# --- B. Croissance sur un plot jouet (bois + humide + tempéré → MONTE) ---
eco = init_eco("pousse", 1, 1, humidite=2.4)         # humide (sur [0,3])
eco.temperature_sol.set(0, 0, MYCEL_TEMP_OPT)        # plein régime thermique
eco.deposer_litiere(0, 0, "bois", MYCEL_SUBSTRAT_REF)  # substrat saturé en bois
before = eco.mycelium.data[0][0]
_tick_n(eco, 5)
after = eco.mycelium.data[0][0]
check("mycelium MONTE en conditions favorables (bois+humide+tempéré)",
      after > before, detail=f"{before:.4f} → {after:.4f}")


# --- C. Déclin (sec + sans bois → REDESCEND) ---
eco_sec = init_eco("sec", 1, 1, humidite=0.1)        # quasi sec
eco_sec.temperature_sol.set(0, 0, MYCEL_TEMP_OPT)
eco_sec.mycelium.set(0, 0, 0.8)                      # réseau préexistant à dégrader
top = eco_sec.mycelium.data[0][0]
_tick_n(eco_sec, 5)
low = eco_sec.mycelium.data[0][0]
check("mycelium REDESCEND au sec sans substrat", low < top,
      detail=f"{top:.4f} → {low:.4f}")


# --- D. Bornage [0,1] ---
eco_max = init_eco("max", 1, 1, humidite=3.0)
eco_max.temperature_sol.set(0, 0, MYCEL_TEMP_OPT)
eco_max.deposer_litiere(0, 0, "bois", 10.0)          # substrat largement saturé
eco_max.mycelium.set(0, 0, 0.99)
_tick_n(eco_max, 200)
check("mycelium plafonne à 1.0 (jamais > max_val)",
      eco_max.mycelium.data[0][0] <= 1.0,
      detail=f"{eco_max.mycelium.data[0][0]:.6f}")
eco_floor = init_eco("floor", 1, 1, humidite=0.0)
eco_floor.mycelium.set(0, 0, 0.01)
_tick_n(eco_floor, 200)
check("mycelium plancher à 0.0 (jamais < 0)",
      eco_floor.mycelium.data[0][0] >= 0.0,
      detail=f"{eco_floor.mycelium.data[0][0]:.6f}")


# --- E. Déterminisme (h1 == h2 sur deux runs identiques) ---
def _run():
    e = init_eco("det", 2, 2, humidite=2.0)
    for r in range(2):
        for c in range(2):
            e.temperature_sol.set(r, c, MYCEL_TEMP_OPT - 2.0 * (r + c))
            e.deposer_litiere(r, c, "bois", 1.5 + 0.3 * (r + c))
    _tick_n(e, 8)
    return tuple(e.mycelium.data[r][c] for r in range(2) for c in range(2))


check("déterminisme : deux runs identiques → état identique", _run() == _run())


# --- F. Repos NEUTRE : sans bois ni mycélium, le champ reste à 0 ---
eco_neutre = init_eco("repos", 1, 1, humidite=2.0)
eco_neutre.temperature_sol.set(0, 0, MYCEL_TEMP_OPT)
_tick_n(eco_neutre, 20)
check("repos sans substrat ni réseau préexistant → reste 0",
      eco_neutre.mycelium.data[0][0] == 0.0,
      detail=f"{eco_neutre.mycelium.data[0][0]:.6f}")


# --- Bilan ---
fails = [n for n, ok in _results if not ok]
if fails:
    print(f"\n[test_mycelium] FAIL — {len(fails)}/{len(_results)} rouges : {fails}")
    sys.exit(1)
print(f"\n[test_mycelium] PASS — {len(_results)}/{len(_results)} OK")
