"""
SYMBIOSE — tests/test_eau.py
Tests ciblés du geste `arroser` + du modèle « eau » au tick (Session B du sprint
planter/arroser) : drainage par `soil_type` et asphyxie par paliers (uptake puis
santé), miroir HAUT de la gradation sécheresse existante.

Couvre (critères Session B) :
  1. arroser : le champ monte (+DOSE, cap 3.0, cumulatif), coût MODÉRÉ, × urgence
     en saison, refus si Vigueur insuffisante (binaire).
  2. arroser → tick : l'apport REDESCEND (évaporation × drainage).
  3. drainage par sol : terre (0.993) vs argile (0.997, retient) — contraste.
  4. asphyxie palier 1 (uptake) : au-dessus de HUM_EXCES l'uptake baisse ∝ excès,
     RÉVERSIBLE (assèchement → uptake restauré), inerte sous le seuil.
  5. asphyxie palier 2 (santé) : asphyxie_memory soutenue → santé ↓ ; un
     assèchement lève la pression (mémoire retombe).
  6. stagnation « noyé » : ok_hum faux par le HAUT au-delà de HUM_NOYE.

Le golden ÉCOLOGIQUE reste l'autorité du déterminisme ; ici on exerce le modèle
eau hors golden (scénarios d'humidité forcée).

Usage (depuis data/code/) :
  python3 -m tests.test_eau
"""
import sys

from world import Tile
from plants import Tomato
from fields import (init_eco, DRAINAGE, DRAINAGE_PAR_SOL,
                    HUM_EXCES, HUM_NOYE, ASPHYXIE_UPTAKE_FLOOR)
from sim import actions as ACT
from sim import vigueur as V

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _state(soil="terre", humidite=1.5):
    tile = Tile(tile_id="T0", soil_type=soil)
    eco = init_eco("T0", 4, 4, humidite=humidite, fertilite=1.0, microbiome=0.3)
    eco.lumiere.fill(1.0)
    gs = {
        "tiles": [tile], "eco": {"T0": eco}, "scores": {},
        "current_player": "joueur_1", "week": 10, "log": [], "seed": 0x5EED,
    }
    V.ensure_player(gs, "joueur_1")
    return gs, tile, eco


# ---------------------------------------------------------------------------
# 1. arroser : champ monte, cap, cumulatif, coûts
# ---------------------------------------------------------------------------
def test_arroser_champ_et_couts():
    print("\n[1] arroser : champ monte (+DOSE, cap 3, cumulatif), coût MODÉRÉ × urgence")
    gs, tile, eco = _state(humidite=1.0)
    avant = gs["vigueur"]["joueur_1"]["courante"]

    ok = ACT.arroser(gs, "joueur_1", eco, 1, 1)
    apres = gs["vigueur"]["joueur_1"]["courante"]
    check("arroser renvoie True", ok)
    check("humidité montée de +DOSE_ARROSAGE", abs(eco.humidite.at_plot(1, 1) - (1.0 + ACT.DOSE_ARROSAGE)) < 1e-9,
          f"hum={eco.humidite.at_plot(1, 1):.3f}")
    check("coût MODÉRÉ débité (planification, pas d'urgence)",
          abs((avant - apres) - ACT.MODERE) < 1e-9, f"débit={avant - apres:.2f}")

    # cumulatif + cap 3.0
    for _ in range(10):
        ACT.arroser(gs, "joueur_1", eco, 1, 1)
    check("dose CUMULATIVE plafonnée à 3.0", eco.humidite.at_plot(1, 1) == 3.0,
          f"hum={eco.humidite.at_plot(1, 1):.3f}")

    # urgence (phase saison) → × URGENCE_MULT
    gs2, _, eco2 = _state(humidite=1.0)
    a2 = gs2["vigueur"]["joueur_1"]["courante"]
    ACT.arroser(gs2, "joueur_1", eco2, 1, 1, urgence=True)
    debit = a2 - gs2["vigueur"]["joueur_1"]["courante"]
    check("coût × URGENCE_MULT en saison", abs(debit - ACT.MODERE * ACT.URGENCE_MULT) < 1e-9,
          f"débit={debit:.2f} attendu={ACT.MODERE * ACT.URGENCE_MULT}")


def test_arroser_refus_vigueur():
    print("\n[1b] arroser : refus binaire si Vigueur insuffisante (champ intact)")
    gs, tile, eco = _state(humidite=1.0)
    gs["vigueur"]["joueur_1"]["courante"] = 1.0   # < MODERE
    ok = ACT.arroser(gs, "joueur_1", eco, 1, 1)
    check("arroser renvoie False (Vigueur insuffisante)", ok is False)
    check("champ humidité INTACT", eco.humidite.at_plot(1, 1) == 1.0,
          f"hum={eco.humidite.at_plot(1, 1):.3f}")


# ---------------------------------------------------------------------------
# 2. L'apport redescend au tick (évaporation × drainage)
# ---------------------------------------------------------------------------
def test_arroser_transitoire():
    print("\n[2] l'apport REDESCEND au tick (transitoire, usure de la solution facile)")
    gs, tile, eco = _state(humidite=1.0)
    ACT.arroser(gs, "joueur_1", eco, 1, 1)
    pic = eco.humidite.at_plot(1, 1)
    eco.tick_hydrology(tile.soil_type)
    apres = eco.humidite.at_plot(1, 1)
    check("après le tick, l'humidité a baissé (évaporation × drainage)", apres < pic,
          f"pic={pic:.3f} → après tick={apres:.3f}")


# ---------------------------------------------------------------------------
# 3. Drainage par sol — contraste terre / argile
# ---------------------------------------------------------------------------
def test_drainage_par_sol():
    print("\n[3] drainage par sol : argile retient plus que terre")
    # même humidité de départ, on désactive la rétention soil_memory pour isoler
    # le seul effet du coefficient de drainage.
    def hum_apres_tick(soil):
        gs, tile, eco = _state(soil=soil, humidite=2.0)
        eco.soil_memory.fill(0.0)
        eco.temperature.fill(11.0)   # pas de surplus d'évaporation (= EVAP_TEMP_REF)
        eco.tick_hydrology(soil)
        return eco.humidite.at_plot(1, 1)

    h_terre = hum_apres_tick("terre")
    h_argile = hum_apres_tick("argile")
    check("terre utilise bien le drainage de référence (0.993)",
          DRAINAGE_PAR_SOL["terre"] == DRAINAGE)
    check("argile retient PLUS que terre (humidité plus haute après tick)",
          h_argile > h_terre, f"terre={h_terre:.4f} argile={h_argile:.4f}")
    # défaut/inconnu → terre
    gs, tile, eco = _state(soil="terre", humidite=2.0)
    eco.soil_memory.fill(0.0); eco.temperature.fill(11.0)
    eco.tick_hydrology("sol_inexistant")
    check("soil_type inconnu → drainage de référence (fallback terre)",
          abs(eco.humidite.at_plot(1, 1) - h_terre) < 1e-9)


# ---------------------------------------------------------------------------
# 4. Asphyxie palier 1 — uptake ↓ ∝ excès, réversible, inerte sous le seuil
# ---------------------------------------------------------------------------
def test_asphyxie_uptake():
    print("\n[4] asphyxie palier 1 : uptake ↓ au-dessus de HUM_EXCES, réversible")
    # uptake d'eau d'une plante au stade 2 (croissance), à humidité variable.
    def uptake_eau(hum):
        gs, tile, eco = _state(humidite=hum)
        return eco.plant_uptake(1, 1, stage_index=2).get("humidite", 0.0)

    sain = uptake_eau(HUM_EXCES - 0.3)        # sous le seuil → pas d'asphyxie
    bord = uptake_eau(HUM_EXCES + 0.01)       # juste au-dessus
    noye = uptake_eau(3.0)                     # excès plein
    check("sous HUM_EXCES : uptake non pénalisé par l'asphyxie", sain > 0.0)
    check("au-dessus de HUM_EXCES : uptake RÉDUIT vs régime sain", noye < sain,
          f"sain={sain:.4f} excès-plein={noye:.4f}")
    check("réduction GRADUÉE (excès plein < bord de seuil)", noye < bord,
          f"bord={bord:.4f} plein={noye:.4f}")
    check("plancher d'uptake respecté (jamais 0 : racines réduites, pas mortes)",
          noye >= sain * ASPHYXIE_UPTAKE_FLOOR - 1e-9)
    # réversibilité : assécher restaure l'uptake (effet sur l'excès COURANT, pas mémoire)
    check("RÉVERSIBLE : revenu sous le seuil, uptake = régime sain",
          abs(uptake_eau(HUM_EXCES - 0.3) - sain) < 1e-9)


# ---------------------------------------------------------------------------
# 5. Asphyxie palier 2 — santé chute si soutenu, réversible
# ---------------------------------------------------------------------------
def test_asphyxie_sante():
    print("\n[5] asphyxie palier 2 : santé ↓ si engorgement SOUTENU, réversible")
    from sim.engine import Engine
    gs, tile, eco = _state(humidite=2.95)     # engorgement net et constant
    plant = tile.add_plant(Tomato, 1, 1)
    plant.health = 3
    eng = Engine(gs)

    # on force l'humidité à rester très haute chaque semaine (sol gorgé soutenu),
    # et on ticke ~40 semaines : la mémoire monte (lerp 0.05) → santé finit par chuter.
    sante_initiale = plant.health
    morte_ou_affaiblie = False
    mem_pic = 0.0
    for w in range(10, 60):
        gs["week"] = w
        eco.humidite.fill(2.95)               # maintient l'engorgement
        eng.tick_semaine()
        mem_pic = max(mem_pic, plant.asphyxie_memory)
        if plant.health < sante_initiale:
            morte_ou_affaiblie = True
            break
    check("asphyxie_memory monte sous engorgement soutenu", mem_pic > 0.0,
          f"mem_pic={mem_pic:.3f}")
    check("santé chute après un engorgement soutenu (palier 2)", morte_ou_affaiblie,
          f"santé={plant.health}/{sante_initiale} mem={plant.asphyxie_memory:.3f}")

    # réversibilité de la mémoire : assécher la fait retomber
    if plant.is_alive:
        for w in range(60, 90):
            gs["week"] = w
            eco.humidite.fill(0.8)            # sol asséché
            eng.tick_semaine()
        check("mémoire d'asphyxie RETOMBE une fois le sol asséché",
              plant.asphyxie_memory < mem_pic, f"mem={plant.asphyxie_memory:.3f} (pic {mem_pic:.3f})")


# ---------------------------------------------------------------------------
# 6. Stagnation « noyé » — ok_hum faux par le haut
# ---------------------------------------------------------------------------
def test_stagnation_noye():
    print("\n[6] stagnation « noyé » : croissance bloquée par le HAUT au-delà de HUM_NOYE")
    from sim.engine import Engine
    gs, tile, eco = _state(humidite=HUM_NOYE + 0.2)
    plant = tile.add_plant(Tomato, 1, 1)
    eco.temperature.fill(20.0)   # chaud → ce n'est PAS un blocage température
    eng = Engine(gs)
    gs["week"] = 20
    eco.humidite.fill(HUM_NOYE + 0.2)
    log = eng._avancer_stades(tile, eco)
    noye = any("noyé" in l for l in log)
    check("un message de stagnation « noyé » apparaît", noye,
          f"log={[l for l in log if 'stagne' in l]}")


def main():
    test_arroser_champ_et_couts()
    test_arroser_refus_vigueur()
    test_arroser_transitoire()
    test_drainage_par_sol()
    test_asphyxie_uptake()
    test_asphyxie_sante()
    test_stagnation_noye()
    n_ok = sum(1 for _, ok in _results if ok)
    n = len(_results)
    print(f"\n[test_eau] {n_ok}/{n} OK")
    if n_ok != n:
        echecs = [name for name, ok in _results if not ok]
        print("ÉCHECS : " + ", ".join(echecs))
        sys.exit(1)
    print("[test_eau] PASS")


if __name__ == "__main__":
    main()
