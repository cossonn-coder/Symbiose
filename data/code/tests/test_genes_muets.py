"""
SYMBIOSE — tests/test_genes_muets.py
Test ciblé du D140 A+B (sprint départ du jardin ①).

  1. GÈNES MUETS : un caractère coûteux que NULLE mécanique ne lit pour l'espèce
     (nectar d'une anémophile, fixation d'azote d'une non-fixatrice…) est gratuit
     dans `cout_genetique` ; le même excès chez une espèce qui l'EXPRIME coûte.
     Le gène reste porté (le vecteur n'est pas touché, seul le prix disparaît).
  2. PÂTURIN : anémophile et autogame (≈ 0,9) → sa fécondation n'est plus bloquée
     par l'absence de butineur.

Lancement (depuis data/code/) : python3 -m tests.test_genes_muets
"""

import sys

from plants import (PlantInstance, PoaAnnua, Tomato, Bean, Phacelia, Nettle,
                    Basil, Carrot, Clover)
from plants.caracteres import CARACTERES_COUTEUX, couteux_exprimes, neutre
from sim.engine.decompo import feconder

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


def _p(cls, **genes):
    p = PlantInstance(plant_class=cls, position=(0, 0))
    p.genes = dict(genes)
    return p


def _exprime(cls):
    return {nom for nom, _ in couteux_exprimes(cls)}


def test_cout_muet():
    print("\n[1] un gène muet ne coûte rien")
    anemo = _p(Nettle, nectar=1.6)
    ento = _p(Phacelia, nectar=1.6)
    check("anémophile à nectar élevé : coût 1,0", anemo.cout_genetique() == 1.0)
    check("entomophile au même nectar : coût < 1", ento.cout_genetique() < 1.0,
          f"{ento.cout_genetique():.3f}")
    check("gène toujours porté", anemo.genes["nectar"] == 1.6)
    check("non-fixatrice à fixation_azote élevée : 1,0",
          _p(Carrot, fixation_azote=1.6).cout_genetique() == 1.0)
    check("fixatrice à fixation_azote élevée : < 1",
          _p(Bean, fixation_azote=1.6).cout_genetique() < 1.0)
    check("sans exsudat, allelopathie gratuite",
          _p(Carrot, allelopathie=1.6).cout_genetique() == 1.0)
    check("basilic (exsudat) paie son allelopathie",
          _p(Basil, allelopathie=1.6).cout_genetique() < 1.0)
    check("trèfle non tropical : limite_froid gratuite",
          _p(Clover, limite_froid=3.0).cout_genetique() == 1.0)
    check("tomate tropicale : limite_froid coûte",
          _p(Tomato, limite_froid=3.0).cout_genetique() < 1.0)


def test_qui_exprime_quoi():
    print("\n[2] expression lecteur par lecteur")
    tom, ort, pha = _exprime(Tomato), _exprime(Nettle), _exprime(Phacelia)
    check("tomate : pas de nectar, mais pollen vibré et attrait",
          "nectar" not in tom and {"pollen", "taille_fleur", "guide_nectar"} <= tom)
    check("phacélie : nectar exprimé, pollen muet (ni vent ni vibré)",
          "nectar" in pha and "pollen" not in pha)
    check("ortie (vent) : pollen exprimé, fleur à insectes muette",
          "pollen" in ort and not {"nectar", "taille_fleur", "guide_nectar"} & ort)
    universels = {"rusticite_froid", "limite_chaud", "parfum", "coriacite_feuille",
                  "mycorhization"}
    check("caractères universels exprimés partout",
          all(universels <= _exprime(c) for c in (Tomato, Nettle, Phacelia, PoaAnnua)))
    check("espèce moyenne (None) : tous", len(couteux_exprimes(None)) == len(CARACTERES_COUTEUX))


def test_paturin():
    print("\n[3] pâturin anémophile et autogame")
    check("mode vent", PoaAnnua.pollination_mode == "wind")
    a = neutre("autofecondation", PoaAnnua)
    check("autofécondation neutre ≈ 0,9", abs(a - 0.9) < 1e-12, f"{a}")
    p = _p(PoaAnnua)
    p.pollen_recu = 0.0                 # aucun pollen reçu (pire cas)
    fec = feconder(p)
    check("fécondation ≥ 0,9 même sans pollen reçu", fec >= 0.9, f"{fec:.3f}")
    check("pollen exprimé (vent), nectar muet",
          "pollen" in _exprime(PoaAnnua) and "nectar" not in _exprime(PoaAnnua))


def main():
    test_cout_muet()
    test_qui_exprime_quoi()
    test_paturin()
    print("\n" + "=" * 60)
    ok = sum(1 for _, c in _results if c)
    print(f"départ du jardin ① — gènes muets : {ok}/{len(_results)} OK")
    return 0 if ok == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
