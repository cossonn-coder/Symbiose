"""
SYMBIOSE — tests/test_embolie.py
Sécheresse : stomates fermés + DÉFAILLANCE HYDRAULIQUE (D140 G, sprint stress au
bilan ①, `sim/embolie.py`).

  [modérée]  sol sous le seuil sec mais au-dessus du seuil extrême : la photosynthèse
             s'arrête (stomates fermés), la plante vit sur ses réserves SANS emboliser,
             puis repart (réserves qui remontent) à la pluie ;
  [extrême]  sol à sec prolongé : les vaisseaux cavitent → un chêne adulte meurt
             desséché en quelques semaines, réserves encore pleines (ce n'est PAS la
             famine) ; le log porte « meurt de dessèchement », lu `secheresse` ;
  [tolérante] même sol très sec : une plante au gène `tolerance_secheresse` haut tient
             plus longtemps qu'une plante neutre ;
  [bois neuf] une embolie partielle ne se répare qu'avec la croissance, lentement.

Simulation isolée (fonctions pures + `_update_physiology` sur une tuile labo) : rapide,
déterministe. Lancement (depuis data/code/) : python3 -m tests.test_embolie
"""

import sys

from plants import PlantInstance
from plants.catalogue import PERENNIAL_CATALOGUE
from world import Tile
from fields import init_eco
from sim.engine import Engine
from sim.bilan import semaine_bilan
from sim.embolie import maj_embolie, seuil_extreme, SEUIL_EMBOLIE, SEUIL_SEC
from sim.evenements import evenements

ETE = dict(saison="ete", presence=1.0, light_eff=1.0, temp=18.0, t_feuille=24.0,
           t_air=18.0, f_nut=1.0, f_allelo=1.0)


def _chene(tol=1.0):
    cls = PERENNIAL_CATALOGUE["chene"]
    p = PlantInstance(cls, (0, 0))
    p.current_stage = len(cls.growth_stages) - 1
    p.age_years = float(cls.maturity_years) + 5.0
    p.genes["tolerance_secheresse"] = tol
    return p


def _semaine(p, hum):
    """Une semaine d'été dans l'ordre du moteur : bilan, puis hydraulique."""
    surplus = semaine_bilan(p, hum_percue=hum, **ETE)
    return maj_embolie(p, hum, 1.0, surplus)


def test_moderee():
    p = _chene()
    hum = 0.8 * SEUIL_SEC                      # stomates fermés, au-dessus de l'extrême
    assert hum > seuil_extreme(p)
    for _ in range(10):
        assert not _semaine(p, hum)
    bas = p.reserves
    assert p.embolie == 0.0 and p.is_alive and bas < 1.0, (p.embolie, bas)
    for _ in range(4):
        _semaine(p, 0.8)                       # la pluie revient
    assert p.reserves > bas, (bas, p.reserves)
    print(f"[modérée] PASS — 10 sem stomates fermés : réserves {bas:.2f}, embolie 0 ; "
          f"pluie → {p.reserves:.2f}")


def test_extreme_et_tolerante():
    def survie(tol, hum):
        p = _chene(tol)
        for sem in range(1, 60):
            if _semaine(p, hum):
                return sem, p.reserves
        return None, p.reserves
    sem, res = survie(1.0, 0.0)
    assert sem is not None and sem <= 8 and res > 0.5, (sem, res)
    print(f"[extrême] PASS — chêne à sol sec : mort hydraulique en {sem} sem, "
          f"réserves encore {res:.2f}")
    hum = 0.03
    s_neutre, _ = survie(1.0, hum)
    s_tol, _ = survie(1.5, hum)
    assert s_neutre is not None and (s_tol is None or s_tol > s_neutre), (s_neutre, s_tol)
    print(f"[tolérante] PASS — sol à {hum} : neutre {s_neutre} sem, "
          f"tolérante {s_tol or '> 59'} sem")


def test_bois_neuf():
    p = _chene()
    p.embolie = 0.5
    p.reserves = 1.0
    for _ in range(4):
        _semaine(p, 0.8)
    assert 0.35 < p.embolie < 0.5, p.embolie          # baisse, lentement
    q = _chene()
    q.embolie = 0.5
    for _ in range(4):
        semaine_bilan(q, hum_percue=0.8, **{**ETE, "saison": "hiver", "presence": 0.0})
        maj_embolie(q, 0.8, 0.0, None)
    assert q.embolie == 0.5                           # pas de bois neuf : rien ne bouge
    print(f"[bois neuf] PASS — 4 sem de croissance : 0,50 → {p.embolie:.2f} ; dormant : 0,50")


def test_tick_log_et_cause():
    """Le vrai `_update_physiology` : chêne sur sol épinglé à 0 → mort desséchée,
    ligne 🪦 lue `secheresse` par `sim.evenements` (carnet, chronique)."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("T0", 6, 6, humidite=1.2, fertilite=1.2, microbiome=0.3)
    chene = tile.add_plant(PERENNIAL_CATALOGUE["chene"], 3, 3)
    chene.current_stage = len(chene.plant_class.growth_stages) - 1
    chene.age_years = 30.0
    eco.humidite.at_plot = lambda r, c: 0.0
    eco.temperature.at_plot = lambda r, c: 18.0
    eco.temperature_sol.at_plot = lambda r, c: 16.0
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "j1", "week": 26, "log": []}
    eng = Engine(gs)                   # semaine lue dans game_state (été)
    log = []
    for _ in range(12):
        log += ["[T0]"] + eng._update_physiology(tile, eco)
        if not chene.is_alive:
            break
    assert not chene.is_alive and chene.embolie >= SEUIL_EMBOLIE, chene.embolie
    morts = [e for e in evenements(log) if e.kind == "mort"]
    assert morts and morts[0].cause == "secheresse", morts
    print(f"[tick] PASS — {[l.strip() for l in log if '🪦' in l][0]}")


if __name__ == "__main__":
    for t in (test_moderee, test_extreme_et_tolerante, test_bois_neuf,
              test_tick_log_et_cause):
        t()
    sys.exit(0)
