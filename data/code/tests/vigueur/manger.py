"""
SYMBIOSE — tests/vigueur/manger.py
D. Action « manger » (sous-sprint 4, tandem D19) — ressourcement gratuit. Coût
NUL, gain ∝ vigueur_plante (façade = modulateur de valeur, §1), plante vivante,
no-op écolo. Event-driven hors tick ⇒ déterministe sans RNG.
"""
from world import Tile
from plants import Tomato
from fields import init_eco
from sim import vigueur as V
from sim import vigueur_plante as VP
from sim import actions as ACT

from .harness import check, _minimal_state, _mature


def test_manger_gain_organe():
    print("\n[D1] manger : gain = HARVEST_GAIN_FULL × vigueur_plante, coût NUL")
    gs = _minimal_state()
    eco = gs["eco"]["T0"]
    plant = _mature(gs["tiles"][0].plants[0]); plant.vitalite = 1.0
    st = V.ensure_player(gs, "joueur_1"); st["max_base"] = 1000.0; st["courante"] = 100.0
    vp = VP.vigueur_plante(plant, eco)
    gagne = ACT.manger(gs, "joueur_1", plant, eco)
    check("gain renvoyé = HARVEST_GAIN_FULL × vigueur_plante",
          abs(gagne - ACT.HARVEST_GAIN_FULL * vp) < 1e-9, f"gagne={gagne} vp={vp}")
    check("coût NUL : courante = 100 + gain (aucune dépense)",
          abs(st["courante"] - (100.0 + gagne)) < 1e-9, f"courante={st['courante']}")
    check("organe mûr vivant → gain strictement positif", gagne > 0.0, f"gagne={gagne}")


def test_manger_modulation_facade():
    print("\n[D2] manger : la façade pilote la valeur (éclatant > chétif)")
    # Même espèce mûre et saine, deux sols opposés → seule la façade change.
    tile = Tile(tile_id="T0", soil_type="terre"); tile.add_plant(Tomato, 2, 2)
    plant = _mature(tile.plants[0]); plant.vitalite = 1.0
    pauvre = init_eco("T0", 6, 8, fertilite=1.0, microbiome=0.3)
    riche = init_eco("T0", 6, 8, fertilite=3.0, microbiome=3.0)
    gs = {}
    st = V.ensure_player(gs, "j"); st["max_base"] = 1000.0; st["courante"] = 100.0
    g_pauvre = ACT.manger(gs, "j", plant, pauvre)
    g_riche = ACT.manger(gs, "j", plant, riche)
    check("organe éclatant (sol riche) rapporte plus qu'un chétif", g_riche > g_pauvre,
          f"pauvre={g_pauvre:.3f} riche={g_riche:.3f}")


def test_manger_no_op_ecolo():
    print("\n[D3] manger : plante vivante, aucune mutation écolo, hors tick")
    gs = _minimal_state()
    eco = gs["eco"]["T0"]
    plant = _mature(gs["tiles"][0].plants[0])
    V.ensure_player(gs, "joueur_1")["courante"] = 50.0
    eco_avant = eco.summary(); week_avant = gs["week"]; seed_avant = gs["seed"]
    ACT.manger(gs, "joueur_1", plant, eco)
    check("plante reste vivante (≠ déraciner)", plant.is_alive)
    check("aucune mutation écolo (organe consommé par le joueur, pas de nécromasse)",
          eco.summary() == eco_avant)
    check("hors tick : week & seed inchangés",
          gs["week"] == week_avant and gs["seed"] == seed_avant)


def test_manger_plafond():
    print("\n[D4] manger : gain plafonné à vigueur_max (pas d'overshoot)")
    gs = _minimal_state()
    eco = gs["eco"]["T0"]
    plant = _mature(gs["tiles"][0].plants[0])
    st = V.ensure_player(gs, "joueur_1")
    st["courante"] = V.vigueur_max(gs, "joueur_1")   # déjà au plafond
    ACT.manger(gs, "joueur_1", plant, eco)
    check("manger au plafond ne dépasse jamais vigueur_max",
          st["courante"] == V.vigueur_max(gs, "joueur_1"), f"courante={st['courante']}")
