"""
SYMBIOSE — tests/test_unites_compromis.py
Test ciblé du D139 ③ — VRAIES UNITÉS et COMPROMIS précocité ↔ taille.

Ce que le golden re-figé ne prouve pas (il constate seulement une dérive), ce test
le garde :
  1. `phenologie_florale` est une avance en SEMAINES et UNE SEULE conversion
     (`sim/tempo.py`) sert les trois horloges + le miroir sémiologique : le signe
     de sénescence visible et la mort du moteur lisent le même onset ;
  2. une avance de floraison RÉDUIT la hauteur (`facteur_hauteur`), un retard
     l'augmente, l'avance 0 ne change rien ;
  3. `germination_thermique` est lu en °C : la moyenne du pool-sol est l'abaissement
     d'optimum lui-même (plus de `GERM_GENE_SHIFT·(g − 1)`) ;
  4. le TRI THERMIQUE à la levée férale (`_levee_triee`) : un sol froid fait lever
     les lève-tôt, un sol chaud les lève-tard.

Lancement (depuis data/code/) : python3 -m tests.test_unites_compromis
"""

import sys

from plants import PlantInstance, Sunflower, AppleTree, Tomato
from plants.genetics import K_PREC
from fields import (init_eco, SENESCENCE_ONSET, SEN_ONSET_JITTER,
                    ABSCISSION_BASE, ABSCISSION_JITTER)
from sim.tempo import (seuil_floraison, semaine_abscission, onset_senescence,
                       gdd_par_semaine, SEMAINES_PAR_TEMPO)
from sim.semiologie import senescence
from sim.succession import _germ_gene_mean

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


def _plante(cls, avance=None, **genes):
    p = PlantInstance(plant_class=cls, position=(0, 0))
    if avance is not None:
        genes["phenologie_florale"] = avance
    p.genes = genes
    return p


def test_conversion_partagee():
    print("\n[1] une avance en semaines, une conversion pour les trois horloges")
    p = _plante(Sunflower, avance=1.0)
    rate = gdd_par_semaine(Sunflower)
    check("floraison : seuil abaissé d'une semaine de forçage",
          abs(seuil_floraison(p) - (Sunflower.bloom_forcing_gdd - rate)) < 1e-12,
          f"{seuil_floraison(p):.2f} °C·j (taux {rate:.2f} °C·j/sem)")
    # Abscission et sénescence : même écart « ancienne échelle » avance / 10.
    e = 1.0 / SEMAINES_PAR_TEMPO
    check("abscission : même écart que la sénescence (avance / SEMAINES_PAR_TEMPO)",
          semaine_abscission(p) == round(ABSCISSION_BASE - ABSCISSION_JITTER * e))
    check("sénescence : onset = SENESCENCE_ONSET − JITTER · avance / 10",
          abs(onset_senescence(p) - (SENESCENCE_ONSET - SEN_ONSET_JITTER * e)) < 1e-12)
    # Sens commun : précoce partout.
    t = _plante(Sunflower, avance=-1.0)
    check("précoce PARTOUT (floraison, abscission, sénescence)",
          seuil_floraison(p) < seuil_floraison(t)
          and semaine_abscission(p) <= semaine_abscission(t)
          and onset_senescence(p) < onset_senescence(t))
    # Taux propre à l'époque de floraison : un pommier (printemps) < tournesol (été).
    check("°C·j par semaine propres à l'espèce (pommier < tournesol)",
          gdd_par_semaine(AppleTree) < gdd_par_semaine(Sunflower),
          f"{gdd_par_semaine(AppleTree):.2f} < {gdd_par_semaine(Sunflower):.2f}")


def test_miroir_semiologie():
    print("\n[2] miroir EXACT : signe de sénescence == pression du moteur")
    for av in (-3.0, 0.0, 2.5):
        a = _plante(AppleTree, avance=av)
        a.age_years = 55.0
        L = AppleTree.longevity()
        onset = onset_senescence(a)
        attendu = max(0.0, min(1.0, (a.age_years - onset * L) / ((1.0 - onset) * L)))
        check(f"avance {av:+.1f} : signe == formule moteur",
              senescence(a, None, None) == attendu, f"{attendu:.4f}")


def test_compromis_taille():
    print("\n[3] compromis précocité ↔ taille")
    n = _plante(Tomato).facteur_hauteur()
    pre = _plante(Tomato, avance=2.0).facteur_hauteur()
    tar = _plante(Tomato, avance=-2.0).facteur_hauteur()
    check("avance 0 → facteur 1 exact", n == 1.0)
    check("précoce (+2 sem.) → plus petite de 2·K_PREC",
          abs(pre - (1.0 - 2 * K_PREC)) < 1e-12, f"{pre:.3f}")
    check("tardive (−2 sem.) → plus grande", tar > 1.0, f"{tar:.3f}")
    h0 = Tomato.height_at(_plante(Tomato))
    h1 = Tomato.height_at(_plante(Tomato, avance=2.0))
    check("height_at lit le compromis", h1 < h0, f"{h1:.2f} < {h0:.2f} cm")
    hg = _plante(Tomato, avance=2.0, hauteur=1.2).facteur_hauteur()
    check("compose avec le gène hauteur", abs(hg - 1.2 * (1 - 2 * K_PREC)) < 1e-12)


def test_germination_celsius():
    print("\n[4] germination_thermique lue en °C")
    eco = init_eco("T", 4, 4, humidite=1.0, fertilite=1.0, microbiome=0.3)
    check("pool vide → neutre 0 °C", _germ_gene_mean(eco, 0, 0, Tomato) == 0.0)
    eco.seed_bank.add_species(0, 0, Tomato, 1.0, {"germination_thermique": 2.0})
    check("pool à +2 °C → abaissement de 2 °C (lu tel quel)",
          _germ_gene_mean(eco, 0, 0, Tomato) == 2.0)


def test_tri_levee():
    print("\n[5] tri thermique à la levée (semis féral)")
    from importlib import import_module
    succ = import_module("sim.succession")      # `sim.succession` = la fonction
    eco = init_eco("T", 4, 4, humidite=1.0, fertilite=1.0, microbiome=0.3)
    opt = Tomato.t_germ_opt

    def levee(t_sol, g=0.0):
        genes = {"germination_thermique": g}
        succ._levee_triee(genes, eco, 0, 0, Tomato, t_sol, False)
        return genes["germination_thermique"]
    check("sol plus froid que l'optimum → semis lève-tôt (> 0)", levee(opt - 6) > 0.0,
          f"{levee(opt - 6):+.3f} °C")
    check("sol plus chaud → semis lève-tard (< 0)", levee(opt + 6) < 0.0,
          f"{levee(opt + 6):+.3f} °C")
    check("sol à l'optimum → pas de tri du centre", levee(opt) == 0.0)
    check("ordre des tirages conservé (z plus grand → valeur plus grande)",
          levee(opt - 6, 1.0) > levee(opt - 6, -1.0))


def main():
    print("=" * 60)
    print("D139 ③ — vraies unités et compromis")
    print("=" * 60)
    test_conversion_partagee()
    test_miroir_semiologie()
    test_compromis_taille()
    test_germination_celsius()
    test_tri_levee()
    ok = sum(1 for _, c in _results if c)
    print("=" * 60)
    print(f"RÉSULTAT : {ok}/{len(_results)} vérifications passées")
    print("=" * 60)
    return 0 if ok == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
