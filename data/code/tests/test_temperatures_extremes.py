"""
SYMBIOSE — tests/test_temperatures_extremes.py
Températures EXTRÊMES de la semaine (D139, sprint niche thermique ①) : nuit la plus
froide (`t_min_nuit_at`), jour le plus chaud (`t_max_jour`), feuille (`t_feuille`).

Helpers PURS, exercés hors golden sur des EcoFields à conditions forcées.

Usage (depuis data/code/) :
  python3 -m tests.test_temperatures_extremes
"""
import sys

from world import Tile
from plants import Zucchini
from fields import init_eco
from fields.ecofields.thermique import t_min_nuit_at, t_min_nuit_type_at, t_max_jour
from sim.engine.feuille import t_feuille, ECHAUFF_FEUILLE

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'OK ' if cond else 'XX '} {name}" + (f" — {detail}" if detail else ""))


def _eco(humidite=1.2):
    return init_eco("T0", 6, 6, humidite=humidite, microbiome=0.0, soil_type="terre")


def test_nuit_la_plus_froide():
    print("\n[1] nuit la plus froide ≤ nuit type ; couverts réchauffent toujours")
    eco = _eco()
    for t_air in (-3.0, 2.0, 8.0):
        for neb in (0.0, 0.5, 1.0):
            froide = t_min_nuit_at(eco, 1, 1, t_air, neb)
            type_ = t_min_nuit_type_at(eco, 1, 1, t_air, neb)
            check(f"T={t_air} neb={neb} : froide ≤ type ≤ T_air",
                  froide <= type_ <= t_air, f"{froide:.2f} ≤ {type_:.2f}")
    nu = t_min_nuit_at(eco, 1, 1, 1.0, 0.0)
    eco.deposer_litiere(2, 2, "diffus", 5.0)                   # paillage
    eco.poser_couvert(3, 3, 0.6)                               # voile
    check("paillage réchauffe la nuit la plus froide",
          t_min_nuit_at(eco, 2, 2, 1.0, 0.0) > nu)
    check("voile réchauffe la nuit la plus froide",
          t_min_nuit_at(eco, 3, 3, 1.0, 0.0) > nu)
    eco.snow = 1.0                                             # manteau neigeux plein
    check("neige pleine : nuit la plus froide = T_air (effet igloo)",
          abs(t_min_nuit_at(eco, 1, 1, 1.0, 0.0) - 1.0) < 1e-9)


def test_jour_le_plus_chaud():
    print("\n[2] jour le plus chaud ≥ T_air, couvert l'écrase")
    for t_air in (-2.0, 12.0, 24.9):
        for neb in (0.0, 0.5, 1.0):
            check(f"T={t_air} neb={neb} : t_max ≥ T_air", t_max_jour(t_air, neb) >= t_air)
    check("ciel couvert : t_max = T_air", t_max_jour(20.0, 1.0) == 20.0)
    canicule = t_max_jour(24.9, 0.08)
    check("canicule la plus chaude [seed 42] dans 33-40 °C", 33.0 <= canicule <= 40.0,
          f"{canicule:.1f} °C")


def _plante(humidite):
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = _eco(humidite)
    return eco, tile.add_plant(Zucchini, 3, 3)


def test_feuille():
    print("\n[3] T_feuille : ombre ≈ t_max ; assoiffée au soleil > arrosée")
    t_air, neb = 24.0, 0.1
    t_max = t_max_jour(t_air, neb)
    eco_sec, p_sec = _plante(0.0)
    eco_eau, p_eau = _plante(2.0)
    eco_sec.lumiere.received[id(p_sec)] = 1.0
    eco_eau.lumiere.received[id(p_eau)] = 1.0
    f_sec = t_feuille(p_sec, eco_sec, t_air, neb)
    f_eau = t_feuille(p_eau, eco_eau, t_air, neb)
    check("plante arrosée au soleil = t_max (transpire)", abs(f_eau - t_max) < 1e-9)
    check("plante assoiffée au soleil > arrosée", f_sec > f_eau,
          f"{f_sec:.1f} > {f_eau:.1f}")
    check("sol sec plein soleil : +ECHAUFF_FEUILLE", abs(f_sec - t_max - ECHAUFF_FEUILLE) < 1e-9)
    eco_sec.lumiere.received[id(p_sec)] = 0.0
    check("plante assoiffée à l'ombre = t_max",
          abs(t_feuille(p_sec, eco_sec, t_air, neb) - t_max) < 1e-9)
    eco_sec.lumiere.received[id(p_sec)] = 1.0
    check("déterminisme", t_feuille(p_sec, eco_sec, t_air, neb) == f_sec)


if __name__ == "__main__":
    test_nuit_la_plus_froide()
    test_jour_le_plus_chaud()
    test_feuille()
    ko = [n for n, ok in _results if not ok]
    print(f"\n{len(_results) - len(ko)}/{len(_results)} OK")
    sys.exit(1 if ko else 0)
