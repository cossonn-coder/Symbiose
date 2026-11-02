"""
SYMBIOSE — tests/test_neige_ordinaire.py
Neige ordinaire (D125) : plus fréquente, pure, et sans déplacer les autres événements.

Usage (depuis data/code/) : python3 -m tests.test_neige_ordinaire
"""
import sys

from sim import weather as W

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'OK ' if cond else 'XX '} {name}" + (f" — {detail}" if detail else ""))


def _avant(seed, week):
    """Le tirage d'avant D125, canal neige coupé."""
    garde = W.P_NEIGE_ORDINAIRE
    W.P_NEIGE_ORDINAIRE = 0.0
    try:
        return W.weather_at(seed, week)
    finally:
        W.P_NEIGE_ORDINAIRE = garde


def main():
    graines, semaines = range(1, 31), range(1, 261)
    ajouts, hors_calme, hors_fenetre, somme = 0, 0, 0, 0
    _, _, _, (debut, fin) = W._NEIGE_CATALOGUE
    for s in graines:
        for w in semaines:
            apres, avant = W.weather_at(s, w), _avant(s, w)
            somme += apres.kind == "Neige"
            if apres == avant:
                continue
            ajouts += 1
            hors_calme += avant != W.CALME
            hors_fenetre += not debut <= (w - 1) % 52 + 1 <= fin
    par_an = somme / (len(graines) * 5)
    check("la neige n'occupe que des semaines calmes", hors_calme == 0, f"{hors_calme}")
    check("la neige reste dans sa fenêtre", hors_fenetre == 0, f"{hors_fenetre}")
    check("environ une semaine de neige par an", 0.8 <= par_an <= 1.3, f"{par_an:.2f}")
    check("le canal ajoute bien de la neige", ajouts > 0, f"{ajouts}")
    check("déterminisme", W.weather_at(42, 96) == W.weather_at(42, 96))
    n_ok = sum(1 for _, ok in _results if ok)
    print(f"\n[test_neige_ordinaire] {n_ok}/{len(_results)} OK")
    if n_ok != len(_results):
        print("ÉCHECS : " + ", ".join(name for name, ok in _results if not ok))
        sys.exit(1)
    print("[test_neige_ordinaire] PASS")


if __name__ == "__main__":
    main()
