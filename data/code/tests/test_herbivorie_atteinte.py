"""
SYMBIOSE — tests/test_herbivorie_atteinte.py
Banc de calibration de l'HERBIVORIE PAR ATTEINTE (D140 G, sprint plante vivante ③,
`sim/effects/herbivorie.py`, conception §4).

Champs de ravageurs CONSTANTS posés à la main (faux `eco` minimal : densités par
espèce, microbiome sain, auxiliaires présents → pas de bascule létale), plante
seule sur ses plots. On mesure la perte de feuillage d'UNE semaine, appliquée par
la vraie résolution (`apply_mutations`) :
  (a) semis seul sur un plot à limace 0,10 : perd 10-25 %/sem ; sans refaire ses
      feuilles, il est nu en quelques semaines (il mourra alors par le bilan) ;
  (b) basilic et haricot mûrs, ravageurs 0,10 : feuillage entamé, vivants ;
  (c) chêne de 25 ans, ravageurs 0,15 partout : perte < 2 %/sem, ne meurt pas ;
  (d) la limace n'entame pas un feuillage au-dessus de 40 cm (part bornée) ;
  (e) le puceron vole des sucres (réserves), le doryphore ne mange que les
      Solanacées, la bascule létale double, l'appétence/la coriacité modulent.

Lancement (depuis data/code/) : python3 -m tests.test_herbivorie_atteinte
"""

import sys

from plants import PlantInstance
from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from sim.effects import apply_mutations
from sim.effects.herbivorie import (sommes_feuillage, herbivorie_atteinte,
                                    atteinte_limace, LIMACE_HAUTEUR_CM)
from sim.monde_complet import pre_croitre, _mettre_adulte

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


class _Champ:
    def __init__(self, d):
        self.d = d

    def at_plot(self, r, c):
        return self.d


class _Eco:
    """Faux eco : densités constantes par ravageur, sol sain, auxiliaires présents."""
    def __init__(self, puceron=0.0, limace=0.0, doryphore=0.0, chenille=0.0,
                 aux=0.5, micro=0.3):
        self.populations = {"puceron": _Champ(puceron), "limace": _Champ(limace),
                            "doryphore": _Champ(doryphore)}
        self.larvae = {"chenille": _Champ(chenille)}
        self.microbiome = _Champ(micro)
        self._aux = aux

    def category_density(self, cat, r, c):
        return self._aux if cat == "auxiliaire" else 0.0


class _Tuile:
    def __init__(self, *plantes):
        self.plants = list(plantes)


def _cls(cle):
    return PLANT_CATALOGUE.get(cle) or PERENNIAL_CATALOGUE[cle]


def _herbacee(cle, adulte=True, stade=0):
    p = PlantInstance(_cls(cle), (5, 5))
    p.x_cm = p.y_cm = 275.0
    if adulte:
        _mettre_adulte(p, 42, 20)
    else:
        p.current_stage = stade
    return p


def _chene():
    p = PlantInstance(_cls("chene"), (10, 10))
    p.x_cm = p.y_cm = 525.0
    pre_croitre(p, 42, 25.0)
    p.age_years = 25.0
    return p


def _semaine(p, eco, saison="ete"):
    """Une semaine d'herbivorie résolue ; renvoie (perte de feuillage, perte de réserves)."""
    f0, r0 = p.feuillage, p.reserves
    tuile = _Tuile(p)
    muts = herbivorie_atteinte(p, eco, sommes_feuillage(tuile, eco, saison), saison)
    apply_mutations(muts, {"tiles": [], "eco": {}})
    return f0 - p.feuillage, r0 - p.reserves


def test_semis():
    print("\n[a] semis seul, limace 0,10")
    p = _herbacee("tournesol", adulte=False)
    perte, _ = _semaine(p, _Eco(limace=0.10))
    check("perd 10-25 % de feuillage la 1re semaine", 0.10 <= perte <= 0.25, f"{perte:.3f}")
    for _ in range(11):
        _semaine(p, _Eco(limace=0.10))
    check("sans refaire ses feuilles, nu en 12 semaines", p.feuillage < 0.10,
          f"feuillage {p.feuillage:.3f}")


def test_herbacees_mures():
    print("\n[b] herbacées mûres, ravageurs 0,10")
    for cle in ("basilic", "haricot"):
        p = _herbacee(cle)
        perte, _ = _semaine(p, _Eco(puceron=0.10, limace=0.10, chenille=0.10))
        check(f"{cle} : feuillage entamé mais pas rasé", 0.01 < perte < 0.25,
              f"{perte:.3f}")
        check(f"{cle} : vivant", p.is_alive)


def test_chene():
    print("\n[c] chêne de 25 ans, ravageurs 0,15 partout")
    p = _chene()
    eco = _Eco(puceron=0.15, limace=0.15, doryphore=0.15, chenille=0.15)
    pertes = [_semaine(p, eco)[0] for _ in range(10)]
    check("perte < 2 %/sem", max(pertes) < 0.02, f"max {max(pertes):.4f}")
    check("ne meurt pas", p.is_alive, f"réserves {p.reserves:.3f}")


def test_limace_hauteur():
    print("\n[d] la limace n'atteint que le feuillage bas")
    p = _herbacee("tournesol")
    h = p.current_height
    perte, _ = _semaine(p, _Eco(limace=1.0))
    borne = LIMACE_HAUTEUR_CM / h
    check("plante haute : perte ≤ part sous 40 cm", h > LIMACE_HAUTEUR_CM and perte <= borne + 1e-9,
          f"h {h:.0f} cm, perte {perte:.3f} ≤ {borne:.3f}")
    check("chêne : la limace atteint < 10 % de son feuillage", atteinte_limace(_chene()) < 0.1)


def test_effets():
    print("\n[e] sucres du puceron, doryphore spécialiste, bascule, goût")
    p = _herbacee("basilic")
    df, dr = _semaine(p, _Eco(puceron=0.3))
    check("puceron : vole plus de réserves qu'il ne défolie", dr > df > 0.0,
          f"réserves {dr:.3f}, feuillage {df:.3f}")
    check("puceron : rien l'hiver", _semaine(_herbacee("haricot"), _Eco(puceron=0.15),
                                             saison="hiver") == (0.0, 0.0))
    check("doryphore : épargne le haricot",
          _semaine(_herbacee("haricot"), _Eco(doryphore=0.3))[0] == 0.0)
    check("doryphore : mange la tomate",
          _semaine(_herbacee("tomate"), _Eco(doryphore=0.3))[0] > 0.0)
    normal = _semaine(_herbacee("haricot"), _Eco(chenille=0.1))[0]
    letal = _semaine(_herbacee("haricot"), _Eco(chenille=0.1, aux=0.0, micro=0.0))[0]
    check("bascule létale : consommation × 2", abs(letal - 2 * normal) < 1e-9,
          f"{letal:.4f} = 2 × {normal:.4f}")

    def perte_gene(**genes):
        q = _herbacee("haricot")
        q.genes = dict(genes)
        return _semaine(q, _Eco(chenille=0.1))[0]
    check("appétence : un feuillage savoureux est plus mangé",
          perte_gene(appetence_feuille=0.6) > perte_gene(appetence_feuille=-0.6))
    check("coriacité : une feuille dure est moins mangée",
          perte_gene(coriacite_feuille=1.5) < perte_gene(coriacite_feuille=0.6))


def test_partage():
    print("\n[f] la consommation se partage entre les feuillages du plot")
    seul = _herbacee("haricot")
    perte_seul = _semaine(seul, _Eco(chenille=0.1))[0]
    a, b = _herbacee("haricot"), _herbacee("haricot")
    eco = _Eco(chenille=0.1)
    sommes = sommes_feuillage(_Tuile(a, b), eco, "ete")
    apply_mutations(herbivorie_atteinte(a, eco, sommes, "ete"), {"tiles": [], "eco": {}})
    check("à deux sur le plot, chacun perd moins", 1.0 - a.feuillage < perte_seul,
          f"{1.0 - a.feuillage:.4f} < {perte_seul:.4f}")


if __name__ == "__main__":
    for t in (test_semis, test_herbacees_mures, test_chene, test_limace_hauteur,
              test_effets, test_partage):
        t()
    ko = [n for n, ok in _results if not ok]
    print(f"\n{len(_results) - len(ko)}/{len(_results)} OK")
    sys.exit(1 if ko else 0)
