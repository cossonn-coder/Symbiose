"""
SYMBIOSE — tests/test_rejets_souche.py
Test ciblé, lancé À LA DEMANDE (hors smoke test). Sprint FREIN REJETS FIGUIER ②.

La souche rejette à la mort de l'arbre (`sim/souche.py`), si elle est restée
vivante (`sim.effects.perturbations.souche_vivante`, figé par `deposer_mort`) :
  (a) figuier mort de vieillesse (mémoires basses), au printemps → rejets au pied
      (≤ RAYON_REJET_CM), clones (gènes, form_seed) ;
  (b) même figuier mort avec `shade_memory` au-dessus de `seuil_ombre` → 0 rejet ;
  (c) sapin mort → 0 rejet (`rejet_souche` = 0) ;
  (d) mort en HIVER → rien avant la 1ʳᵉ semaine de printemps, la vague y part,
      et c'est la seule ;
  (e) figuier vivant mûr, 200 semaines → 0 rejet (plus d'émission de fond).

Lancement (depuis data/code/) :
  python3 -m tests.test_rejets_souche
"""

import math
import sys

from calendrier import saison_de, wiy_de
from world import Tile
from fields import init_eco
from plants import Fig, FirTree
from sim.clonal import emettre_ramets
from sim.effects import deposer_mort
from sim.effects.perturbations import seuil_ombre
from sim.souche import emettre_rejets_souche, nombre_rejets, RAYON_REJET_CM

SEED = 42
S_PRINTEMPS = 5          # une semaine de printemps (wiy 5)
S_HIVER = 45             # une semaine d'hiver de la 1ʳᵉ année


def _monde(cls=Fig):
    """Un arbre mûr au centre d'une tuile 20×20, plein soleil imposé."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=20, grid_cols=20)
    eco = init_eco("T0", 20, 20, humidite=1.0, fertilite=1.0, microbiome=0.3)
    arbre = tile.add_plant(cls, 10, 10)
    arbre.age_years = cls.maturity_years + 20.0
    arbre.genes = {k: v * 1.01 for k, v in arbre.genes.items()}   # marqueur de clone
    arbre.form_seed = 12345
    eco.lumiere.at_plot = lambda r, c: 0.9
    return tile, eco, arbre


def _tuer(arbre, eco):
    arbre.vitalite = 0.0
    deposer_mort(arbre, eco)


def _rejets(tile, arbre):
    return [p for p in tile.plants if p is not arbre and p.is_alive]


def test_mort_de_vieillesse():
    tile, eco, fig = _monde()
    _tuer(fig, eco)
    assert fig.souche_vivante, "souche jugée morte alors que les mémoires sont basses"
    log = emettre_rejets_souche(tile, SEED, S_PRINTEMPS)
    rejets = _rejets(tile, fig)
    assert len(rejets) == nombre_rejets(Fig) >= 1, f"{len(rejets)} rejet(s)"
    assert len(log) == 1 and "Rejet de souche" in log[0], log
    for p in rejets:
        d = math.hypot(p.x_cm - fig.x_cm, p.y_cm - fig.y_cm)
        assert d <= RAYON_REJET_CM + 1e-9, f"rejet à {d:.0f} cm"
        assert p.genes == fig.genes and p.form_seed == fig.form_seed, "pas un clone"
    print(f"[souche (a)] PASS — {len(rejets)} rejets au pied, clones : {log[0].strip()}")


def test_souche_epuisee_par_ombre():
    tile, eco, fig = _monde()
    fig.shade_memory = seuil_ombre(fig) + 0.05
    _tuer(fig, eco)
    n = len(emettre_rejets_souche(tile, SEED, S_PRINTEMPS))
    assert not fig.souche_vivante and n == 0 and not _rejets(tile, fig)
    print("[souche (b)] PASS — mort d'ombre : 0 rejet")


def test_sapin():
    tile, eco, sapin = _monde(FirTree)
    _tuer(sapin, eco)
    emettre_rejets_souche(tile, SEED, S_PRINTEMPS)
    assert not sapin.souche_vivante and not _rejets(tile, sapin)
    print("[souche (c)] PASS — sapin : 0 rejet")


def test_mort_en_hiver():
    tile, eco, fig = _monde()
    _tuer(fig, eco)
    vagues = []
    for wk in range(S_HIVER, S_HIVER + 30):
        if emettre_rejets_souche(tile, SEED, wk):
            vagues.append(wk)
    assert len(vagues) == 1, f"vagues aux semaines {vagues}"
    wk = vagues[0]
    assert saison_de(wiy_de(wk)) == "printemps" and saison_de(wiy_de(wk - 1)) == "hiver", \
        f"vague semaine {wk} ({saison_de(wiy_de(wk))}), pas la 1re de printemps"
    print(f"[souche (d)] PASS — mort semaine {S_HIVER} (hiver) : une vague, semaine {wk}")


def test_figuier_vivant_sans_rejet():
    tile, eco, fig = _monde()
    n = 0
    for wk in range(1, 201):
        n += len(emettre_ramets(tile, eco, SEED, wk))
        n += len(emettre_rejets_souche(tile, SEED, wk))
    assert n == 0 and not _rejets(tile, fig), f"{n} émission(s) d'un figuier vivant"
    print("[souche (e)] PASS — figuier vivant mûr : 0 rejet en 200 semaines")


if __name__ == "__main__":
    tests = [test_mort_de_vieillesse, test_souche_epuisee_par_ombre, test_sapin,
             test_mort_en_hiver, test_figuier_vivant_sans_rejet]
    echecs = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            echecs += 1
            print(f"[souche] FAIL {t.__name__} : {e}")
    sys.exit(1 if echecs else 0)
