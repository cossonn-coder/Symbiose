"""
SYMBIOSE — tests/vigueur/facades.py
C. Façade `vigueur_plante` (sous-sprint 3) — lecture PURE read-only, jamais
pilote. Déterministe sans RNG : on lit des états posés à la main (santé,
maturité, Qi local, gène enveloppé, descripteur diégétique).
"""
from world import Tile
from plants import Tomato
from fields import init_eco
from sim import vigueur_plante as VP
from sim import actions as ACT

from .harness import check, _minimal_state, _mature


def test_facade_purete():
    print("\n[C1] façade vigueur_plante : lecture PURE (aucune écriture)")
    gs = _minimal_state()
    eco = gs["eco"]["T0"]
    plant = _mature(gs["tiles"][0].plants[0])
    eco_avant = eco.summary()
    sante_av, stage_av, health_av = plant.vitalite, plant.current_stage, plant.vitalite
    v1 = VP.vigueur_plante(plant, eco)
    v2 = VP.vigueur_plante(plant, eco)
    check("déterministe (même entrée → même sortie)", v1 == v2, f"{v1}=={v2}")
    check("aucune mutation de l'état écolo", eco.summary() == eco_avant)
    check("aucune mutation de la plante",
          (plant.vitalite, plant.current_stage) == (health_av, stage_av))


def test_facade_sante():
    print("\n[C2] facteur santé : vitalite [0,1], mort → Vigueur nulle")
    gs = _minimal_state()
    eco = gs["eco"]["T0"]
    plant = _mature(gs["tiles"][0].plants[0])
    plant.vitalite = 1.0
    check("santé pleine → 1.0", VP.sante(plant) == 1.0)
    v_sain = VP.vigueur_plante(plant, eco)
    plant.vitalite = 0.0
    check("santé nulle → 0.0", VP.sante(plant) == 0.0)
    check("plante morte → Vigueur dérivée nulle",
          VP.vigueur_plante(plant, eco) == 0.0)
    check("santé module la Vigueur (sain > mort)", v_sain > 0.0, f"v_sain={v_sain}")


def test_facade_maturite():
    print("\n[C3] facteur maturité : semis ≈ 0, adulte = 1 (mutualisé actions.py)")
    gs = _minimal_state()
    plant = gs["tiles"][0].plants[0]
    plant.current_stage = 0
    semis = VP.maturite(plant)
    _mature(plant)
    adulte = VP.maturite(plant)
    check("maturité croît avec le stade (semis < adulte)", semis < adulte,
          f"semis={semis} adulte={adulte}")
    check("maturité adulte = 1.0", adulte == 1.0)
    check("identique à l'helper réimporté par actions.py",
          VP.maturite(plant) == ACT.maturite(plant))


def test_facade_qi_local():
    print("\n[C4] facteur Qi local : sol riche > sol pauvre, borné [0,1]")
    tile = Tile(tile_id="T0", soil_type="terre")
    tile.add_plant(Tomato, 2, 2)
    plant = _mature(tile.plants[0])
    pauvre = init_eco("T0", 6, 8, fertilite=1.0, microbiome=0.3)
    riche = init_eco("T0", 6, 8, fertilite=3.0, microbiome=3.0)
    q_pauvre = VP.qi_local(plant, pauvre)
    q_riche = VP.qi_local(plant, riche)
    check("Qi croît avec fertilité/microbiome (riche > pauvre)", q_riche > q_pauvre,
          f"pauvre={q_pauvre:.4f} riche={q_riche:.4f}")
    check("Qi borné à 1.0 sur sol saturé", q_riche == 1.0, f"q_riche={q_riche}")
    check("Qi ∈ ]0,1] sur sol modeste", 0.0 < q_pauvre <= 1.0, f"q_pauvre={q_pauvre}")


def test_facade_gene_enveloppe():
    print("\n[C5] gène `vigueur` (D22b) enveloppé tel quel — modulateur linéaire")
    gs = _minimal_state()
    eco = gs["eco"]["T0"]
    plant = _mature(gs["tiles"][0].plants[0])
    plant.genes = {}                       # neutre = 1.0
    v_neutre = VP.vigueur_plante(plant, eco)
    plant.genes = {"vigueur": 1.2}
    v_gene = VP.vigueur_plante(plant, eco)
    check("le gène module linéairement la façade (×1.2)",
          abs(v_gene - v_neutre * 1.2) < 1e-9, f"neutre={v_neutre} gène={v_gene}")


def test_facade_descripteur():
    print("\n[C6] descripteur diégétique qualitatif (philo #5 — pas de chiffre)")
    check("0 (mort/semis) → imperceptible", VP.decrire_vigueur(0.0) == "imperceptible")
    check("faible → chétif", VP.decrire_vigueur(0.1) == "chétif")
    check("moyen → vigoureux", VP.decrire_vigueur(0.35) == "vigoureux")
    check("fort → éclatant", VP.decrire_vigueur(0.8) == "éclatant")
    # Monotonie : la bande ne régresse jamais quand la Vigueur monte.
    ordre = ["imperceptible", "chétif", "vigoureux", "éclatant"]
    bandes = [VP.decrire_vigueur(v) for v in (0.0, 0.1, 0.35, 0.8)]
    check("bandes monotones croissantes", bandes == ordre, f"{bandes}")
