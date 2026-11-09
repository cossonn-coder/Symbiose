"""
SYMBIOSE — tests/test_dormance_clonale.py
Test ciblé, lancé À LA DEMANDE (hors smoke test). Sprint FREIN REJETS FIGUIER ①.

Dormance clonale : rien ne s'enracine en hiver (stolon, rhizome, drageon). Même
clonale mature (framboisier, drageon — le figuier n'est plus clonal depuis le
② : il rejette de souche à la perte, `sim/souche.py`), mêmes champs ouverts
(plein soleil imposé, sol nu) :
  (a) toutes les semaines d'HIVER sur 4 ans → 0 ramet ;
  (b) les semaines de végétation sur 4 ans → au moins un ramet (l'émission
      reste possible hors dormance).

Lancement (depuis data/code/) :
  python3 -m tests.test_dormance_clonale
"""

import sys

from calendrier import saison_de, wiy_de
from world import Tile
from fields import init_eco
from plants.species.sauvages import Raspberry
from sim.clonal import emettre_ramets

ANNEES = 4


def _ramets(en_hiver: bool) -> int:
    """Ramets émis par un framboisier mûr sur les semaines d'hiver (ou les autres).
    Tuile neuve à chaque appel → les deux mesures partent du même état."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=20, grid_cols=20)
    eco = init_eco("T0", 20, 20, humidite=1.0, fertilite=1.0, microbiome=0.3)
    fram = tile.add_plant(Raspberry, 10, 10)
    fram.current_stage = len(Raspberry.growth_stages) - 1   # dernier stade = mûr
    eco.lumiere.at_plot = lambda r, c: 0.9
    n = 0
    for wk in range(1, 52 * ANNEES + 1):
        if (saison_de(wiy_de(wk)) == "hiver") == en_hiver:
            n += len(emettre_ramets(tile, eco, 42, wk))
    return n


def test_dormance_hiver():
    n_hiver = _ramets(en_hiver=True)
    n_actif = _ramets(en_hiver=False)
    assert n_hiver == 0, f"{n_hiver} ramet(s) émis en hiver"
    assert n_actif >= 1, "aucun ramet hors hiver : l'émission est coupée partout"
    print(f"[dormance] PASS — hiver : 0 ramet ; saisons actives : {n_actif} "
          f"ramet(s) en {ANNEES} ans")


if __name__ == "__main__":
    try:
        test_dormance_hiver()
    except AssertionError as e:
        print(f"[dormance] FAIL : {e}")
        sys.exit(1)
