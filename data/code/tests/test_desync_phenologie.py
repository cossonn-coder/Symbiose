"""
SYMBIOSE — tests/test_desync_phenologie.py
Test du tronçon ① — DÉSYNCHRONISATION PHÉNOLOGIQUE.

Le golden re-figé ne PROUVE pas la désync (il constate juste un changement de
digest). Ce test-ci est la garde CIBLÉE et INDÉPENDANTE : il sème une cohorte
d'individus d'une même espèce (variance génétique fondatrice, `semer_fondateur`)
et vérifie que les TROIS horloges phénologiques — floraison, fanaison
(abscission), onset de sénescence — sont ÉTALÉES entre individus (écart-type > 0).
Il capte donc une régression si un futur refactor ré-annulait la désync (ré-
synchronisation = étalement nul).

Les trois horloges dérivent du MÊME gène-tempo `phenologie_florale` (g > 1 =
individu précoce partout), via des formules ∝ (g − 1) :
  - floraison : seuil effectif `gdd_floraison − FLORA_GENE_SHIFT·(g − 1)` ;
  - abscission : semaine `round(ABSCISSION_BASE − ABSCISSION_JITTER·(g − 1))`
    bornée [ABSCISSION_MIN, ABSCISSION_MAX] (= `semaine_abscission`) ;
  - sénescence : onset `clamp(SENESCENCE_ONSET − SEN_ONSET_JITTER·(g − 1), …)`.

On teste au NIVEAU FORMULE (environnement-indépendant, robuste et court) : c'est
le gène qui désynchronise, pas le climat. Déterministe (philo #3) : `semer_
fondateur` tire les gènes par hash de position, aucun RNG vivant — SEED fixe.

Neutralité à g = 1.0 : chaque formule redonne la valeur de base (aucun décalage).

Lancement (depuis data/code/) : python3 -m tests.test_desync_phenologie
"""

import sys
import statistics as st

from world import Tile
from fields import (init_eco, SENESCENCE_ONSET, SEN_ONSET_JITTER)
from sim.engine.floraison import FLORA_GENE_SHIFT
from sim.engine.decompo import semaine_abscission
from sim.seeds import semer_fondateur
from plants import Sunflower, Vaccinium

SEED = 0x5EED
# Cohorte de ~10 positions DISTINCTES → 10 patrimoines fondateurs distincts.
POSITIONS = [(0, 0), (0, 2), (0, 4), (0, 6), (2, 0),
             (2, 2), (2, 4), (2, 6), (4, 0), (4, 2)]

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _cohorte(plant_class):
    """Sème une cohorte fondatrice de `plant_class` sur une tuile neuve et renvoie
    la liste des instances vivantes (chacune a son gène `phenologie_florale`)."""
    tile = Tile(tile_id="T", soil_type="terre", origin_x_cm=0.0, origin_y_cm=0.0)
    init_eco("T", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3,
             soil_type="terre", heterogene=True)
    plants = []
    for r, c in POSITIONS:
        p = semer_fondateur(tile, plant_class, r, c, SEED)
        if p is not None:
            plants.append(p)
    return plants


def test_variance_gene_tempo():
    """La cohorte fondatrice porte bien une VARIANCE du gène-tempo (sinon les trois
    horloges seraient neutres — préalable indispensable à la désync)."""
    plants = _cohorte(Sunflower)
    genes = [p.gene("phenologie_florale") for p in plants]
    sd = st.pstdev(genes)
    check("cohorte peuplée", len(plants) >= 8, f"{len(plants)} individus")
    check("gène-tempo étalé (σ>0)", sd > 0.0,
          f"σ={sd:.4f} min={min(genes):.3f} max={max(genes):.3f}")


def test_spread_floraison():
    """Étalement de la floraison : le seuil GDD EFFECTIF de floraison
    (`gdd_floraison − FLORA_GENE_SHIFT·(g − 1)`) est DISTINCT entre individus → ils
    ne fleurissent pas la même semaine (c'est le knob FLORA_GENE_SHIFT recalibré à
    200 qui rend l'écart perceptible)."""
    plants = _cohorte(Sunflower)
    base = Sunflower.gdd_floraison
    seuils = [base - FLORA_GENE_SHIFT * (p.gene("phenologie_florale") - 1.0)
              for p in plants]
    sd = st.pstdev(seuils)
    check("seuil floraison étalé (σ>0)", sd > 0.0,
          f"σ={sd:.2f} GDD, min={min(seuils):.0f} max={max(seuils):.0f}")


def test_spread_abscission():
    """Étalement de la fanaison : les semaines de largage propres à chaque caduc
    (`semaine_abscission`) ne sont PAS toutes identiques (variance > 0)."""
    plants = _cohorte(Vaccinium)   # espèce caduque
    weeks = [semaine_abscission(p) for p in plants]
    sd = st.pstdev(weeks)
    check("semaines d'abscission distinctes (σ>0)", sd > 0.0,
          f"σ={sd:.3f} sem, semaines={sorted(set(weeks))}")


def test_spread_onset_senescence():
    """Étalement de l'onset de sénescence : l'onset propre à chaque individu
    (`clamp(SENESCENCE_ONSET − SEN_ONSET_JITTER·(g − 1), …)`) est étalé."""
    plants = _cohorte(Sunflower)
    onsets = [max(0.05, min(0.95,
                  SENESCENCE_ONSET - SEN_ONSET_JITTER
                  * (p.gene("phenologie_florale") - 1.0)))
              for p in plants]
    sd = st.pstdev(onsets)
    check("onset de sénescence étalé (σ>0)", sd > 0.0,
          f"σ={sd:.4f}, min={min(onsets):.3f} max={max(onsets):.3f}")


def test_neutralite_gene_1():
    """À g = 1.0, les trois horloges redonnent EXACTEMENT leur valeur de base
    (aucun décalage) — garantit qu'un individu neutre n'est pas perturbé."""
    g = 1.0
    seuil = Sunflower.gdd_floraison - FLORA_GENE_SHIFT * (g - 1.0)
    onset = max(0.05, min(0.95, SENESCENCE_ONSET - SEN_ONSET_JITTER * (g - 1.0)))
    check("floraison neutre à g=1", seuil == Sunflower.gdd_floraison)
    check("onset neutre à g=1", onset == SENESCENCE_ONSET)


def main():
    print("=" * 60)
    print("DÉSYNCHRONISATION PHÉNOLOGIQUE — étalement des 3 horloges")
    print("=" * 60)
    test_variance_gene_tempo()
    test_spread_floraison()
    test_spread_abscission()
    test_spread_onset_senescence()
    test_neutralite_gene_1()
    ok = sum(1 for _, c in _results if c)
    print("=" * 60)
    print(f"RÉSULTAT : {ok}/{len(_results)} vérifications passées")
    print("=" * 60)
    return 0 if ok == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
