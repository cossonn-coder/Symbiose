"""
SYMBIOSE — tests/test_neige_ordinaire.py
Neige (D125) : une pluie assez froide tombe en neige ; rien d'autre ne change.

Usage (depuis data/code/) : python3 -m tests.test_neige_ordinaire
"""
import sys

from sim import weather as W

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'OK ' if cond else 'XX '} {name}" + (f" — {detail}" if detail else ""))


def _avant(seed, week):
    """Le tirage sans la règle : seuil si bas qu'aucune pluie ne gèle."""
    garde = W.SEUIL_NEIGE_C
    W.SEUIL_NEIGE_C = -100.0
    try:
        return W.weather_at(seed, week)
    finally:
        W.SEUIL_NEIGE_C = garde


def main():
    graines, semaines = range(1, 31), range(1, 261)
    ajouts, hors_pluie, trop_chaud, somme = 0, 0, 0, 0
    for s in graines:
        phase = (s & 0xFFFF) / 0xFFFF * 6.283185307179586
        for w in semaines:
            apres, avant = W.weather_at(s, w), _avant(s, w)
            somme += apres.kind == "Neige"
            if apres == avant:
                continue
            ajouts += 1
            hors_pluie += avant.kind != "Pluie prolongée"
            t = W.temp_norm((w - 1) % 52 + 1, (w - 1) / 52.0, phase) + W.temperature_delta(avant)
            trop_chaud += t >= W.SEUIL_NEIGE_C
    par_an = somme / (len(graines) * 5)
    check("seule une pluie devient neige", hors_pluie == 0, f"{hors_pluie}")
    check("seulement par temps froid", trop_chaud == 0, f"{trop_chaud}")
    check("environ une semaine de neige par an", 0.8 <= par_an <= 1.3, f"{par_an:.2f}")
    check("la règle joue vraiment", ajouts > 0, f"{ajouts}")
    check("déterminisme", W.weather_at(42, 96) == W.weather_at(42, 96))
    n_ok = sum(1 for _, ok in _results if ok)
    print(f"\n[test_neige_ordinaire] {n_ok}/{len(_results)} OK")
    if n_ok != len(_results):
        print("ÉCHECS : " + ", ".join(name for name, ok in _results if not ok))
        sys.exit(1)
    print("[test_neige_ordinaire] PASS")


if __name__ == "__main__":
    main()
