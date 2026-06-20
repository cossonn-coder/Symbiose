"""
SYMBIOSE — tests/test_stress_chronique.py
Test ciblé, lancé À LA DEMANDE (hors smoke test).

Couvre la « mort par stress chronique » : un facteur défavorable INSTALLÉ (pas un
coup passager) ne doit pas seulement STAGNER la croissance, il doit STAGNER PUIS
TUER — symétrie réclamée par le terrain (Nico : « les plantes trop longtemps en
conditions défavorables, dont l'OMBRE, stagnent et meurent »).

Deux voies, toutes deux miroir de `drought_stress_damage` (mémoire lente → santé,
médiée par un gène → pression de sélection émergente, philo #2/#7) :
  ① CARENCE LUMINEUSE  : `shade_memory` → santé, médiée par `tolerance_ombre`.
                         Un HÉLIOPHILE (tolérance basse) meurt à l'ombre, un
                         SCIAPHILE (tolérance haute) survit.
  ② CARENCE ÉDAPHIQUE  : `starvation_memory` (1 − qi_local : Liebig NPK + pH) →
                         santé, médiée par `vigueur`. (tronçon ②)

Climat de LABORATOIRE pour isoler le facteur testé (cf. tests/diag_morts_field.py) :
météo douce constante (ni pluie → pas d'asphyxie, ni gel), germination spontanée
coupée, aléas ravageurs neutralisés. L'ombre est imposée en surchargeant
`eco.lumiere.light_received` (le champ lumière est recalculé à chaque tick par
`tick_light` → clamper le champ ne suffit pas, on force la lecture).

Lancement (depuis data/code/) :
  python3 -m tests.test_stress_chronique
"""

import sys

from world import Tile
from plants import Zucchini
from fields import init_eco
from sim.engine import Engine
import sim.engine.boucle as _boucle
from sim.weather import CALME

MAX_WEEKS = 46   # < 49 : on s'arrête AVANT la mort hivernale de l'annuelle
_T_DOUCE = 15.0
_NEBUL_CLAIR = 0.1


def _meteo_labo(seed, week):
    """Beau temps doux constant : pas de précipitation (→ pas d'asphyxie), 15 °C
    (→ pas de gel). Isole le facteur testé de tout aléa météo global."""
    return CALME, _T_DOUCE, _NEBUL_CLAIR


def _lab_tile():
    """Tuile 6×6 terre + éco de labo, germination et aléas ravageurs neutralisés."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("T0", 6, 6, humidite=1.2, fertilite=1.2, microbiome=0.3)
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    _boucle.weather_state = _meteo_labo
    _boucle.ALEAS_RAVAGEURS = [a for a in _boucle.ALEAS_RAVAGEURS
                               if a.nom == "Calme"] or _boucle.ALEAS_RAVAGEURS[:1]
    return tile, eco


def _mort(plant) -> bool:
    """Morte quelle que soit la voie (santé à 0 OU drapeau squelette `morte`)."""
    return plant.morte or plant.health <= 0


def run_shade(tol_ombre: float, light: float = 0.1, weeks: int = MAX_WEEKS):
    """Une courgette plongée dans une ombre INSTALLÉE (`light` constant bas), au
    génotype `tolerance_ombre` imposé (autres gènes neutres = 1.0). Renvoie
    (semaine_de_mort | None, santé_finale, shade_memory_finale)."""
    tile, eco = _lab_tile()
    plant = tile.add_plant(Zucchini, 3, 3)
    plant.genes = {"tolerance_ombre": tol_ombre}   # autres gènes → défaut 1.0
    # Ombre imposée : on force la lumière REÇUE (l'objet LightField est muté en
    # place par tick_light, donc cette surcharge d'instance persiste).
    eco.lumiere.light_received = lambda p, _l=light: _l
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "j1", "week": 1, "log": []}
    engine = Engine(gs)
    for wk in range(weeks):
        eco.lumiere.light_received = lambda p, _l=light: _l
        engine.tick_semaine()
        if _mort(plant):
            return wk + 1, plant.health, plant.shade_memory
        gs["log"].clear()
    return None, plant.health, plant.shade_memory


def test_shade_kills_heliophile_spares_sciaphile():
    """À ombre identique, l'héliophile (tolérance basse) meurt, le sciaphile
    (tolérance haute) survit avec plus de santé : la mort par l'ombre existe ET
    est sous contrôle génétique (sélection émergente de la sciaphilie)."""
    h_week, h_health, h_sm = run_shade(tol_ombre=0.4)   # héliophile
    s_week, s_health, s_sm = run_shade(tol_ombre=1.6)   # sciaphile

    assert h_sm > 0.6, (
        f"l'ombre ne s'installe pas (shade_memory héliophile {h_sm:.2f} ≤ 0.6)")
    assert h_week is not None, (
        f"l'héliophile SURVIT à l'ombre (santé {h_health}, shade_memory {h_sm:.2f}) "
        f"— la voie carence lumineuse ne mord pas")
    assert s_health > h_health or s_week is None, (
        f"le sciaphile ne résiste pas mieux : héliophile santé={h_health} "
        f"(mort S{h_week}) vs sciaphile santé={s_health} (mort S{s_week})")
    print(f"[stress-chronique ①] PASS — héliophile mort S{h_week} "
          f"(shade_memory {h_sm:.2f}) ; sciaphile santé={s_health} "
          f"(mort S{s_week}, shade_memory {s_sm:.2f})")


if __name__ == "__main__":
    try:
        test_shade_kills_heliophile_spares_sciaphile()
    except AssertionError as e:
        print(f"[stress-chronique ①] FAIL — {e}")
        sys.exit(1)
    sys.exit(0)
