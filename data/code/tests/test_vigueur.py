"""
SYMBIOSE — tests/test_vigueur.py
Golden JOUEUR de la couche Vigueur (D11, sous-sprint 1) — distinct du golden
ÉCOLOGIQUE (`tests/test_golden.py`).

La couche Vigueur joueur vit dans `game_state["vigueur"]`, AU-DESSUS du tick, et
ne doit JAMAIS faire avancer la simulation écologique (CONCEPTION_VIGUEUR.md
§0/§5). Deux familles de vérifications :

  A. Contrats de la couche (déterministes, sans RNG) :
     1. No-op golden : un `game_state` SANS clé `vigueur` ne se voit JAMAIS
        injecter de Vigueur par le tick (c'est ce qui garde le golden écolo
        intact — si ce contrat casse, le golden bouge).
     2. Régen plafonnée : +REGEN_BASE/semaine, jamais au-dessus de vigueur_max.
     3. Refill saison : `courante = vigueur_max` quel que soit l'état antérieur.
     4. Interface paliers stubbée : palier_bonus == 1.0 ; vigueur_max / regen_rate
        en dépendent.

  B. Golden de trajectoire : on pilote une vraie boucle `engine` sur une fenêtre
     qui traverse une frontière de saison (régen sur la pente + snap du refill),
     et on hashe la trajectoire `courante` semaine par semaine. Toute dérive du
     cadencement du hook (mauvaise semaine de refill, double régen…) casse le
     hash.

Usage (depuis data/code/) :
  python3 -m tests.test_vigueur            # vérifie contre vigueur_hash.txt
  python3 -m tests.test_vigueur --capture  # (re)capture le hash de référence
"""
import sys
import os
import hashlib

from world import Tile
from plants import Tomato, Basil, Bean
from fields import init_eco, DENSITE_PAR_SPRITE
from sim.engine import Engine
from sim import vigueur as V
from sim import actions as ACT
from sim import vigueur_plante as VP
from sim import vigueur_macro as VM

SEED = 0x5AB1057E
HASH_FILE = os.path.join(os.path.dirname(__file__), "vigueur_hash.txt")
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _minimal_state(week=1):
    """Monde minimal (1 tuile, 3 plantes) — assez pour tourner le tick à coût
    négligeable. Sert de support à l'intégration de la couche Vigueur."""
    tile = Tile(tile_id="T0", soil_type="terre")
    eco = init_eco("T0", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
    tile.add_plant(Tomato, 2, 2)
    tile.add_plant(Basil, 2, 4)
    tile.add_plant(Bean, 4, 2)
    return {
        "tiles": [tile], "eco": {"T0": eco}, "scores": {},
        "current_player": "joueur_1", "week": week, "log": [], "seed": SEED,
    }


# ---------------------------------------------------------------------------
# A1. No-op golden : pas de joueur ⇒ le tick n'injecte JAMAIS de Vigueur
# ---------------------------------------------------------------------------

def test_noop_sans_joueur():
    print("\n[A1] sans couche joueur, le tick reste un no-op strict")
    gs = _minimal_state()
    eng = Engine(gs)
    for _ in range(20):
        eng.tick_semaine()
    check("aucune clé `vigueur` créée par le tick", "vigueur" not in gs,
          f"clés={sorted(gs.keys())}")


# ---------------------------------------------------------------------------
# A2. Régen plafonnée
# ---------------------------------------------------------------------------

def test_regen_plafonnee():
    print("\n[A2] régen passive +REGEN_BASE/semaine, plafonnée à vigueur_max")
    gs = {}
    st = V.ensure_player(gs, "joueur_1")
    st["courante"] = 0.0
    V.tick_player_vigueur(gs)
    check("première semaine : 0 → REGEN_BASE", st["courante"] == V.REGEN_BASE,
          f"courante={st['courante']}")
    # On régénère jusqu'au plafond et on vérifie qu'on n'overshoote pas.
    for _ in range(50):
        V.tick_player_vigueur(gs)
    cap = V.vigueur_max(gs, "joueur_1")
    check("plafonnée à vigueur_max (pas d'overshoot)", st["courante"] == cap,
          f"courante={st['courante']} cap={cap}")


# ---------------------------------------------------------------------------
# A3. Refill saison
# ---------------------------------------------------------------------------

def test_refill_saison():
    print("\n[A3] passage de saison : courante = vigueur_max")
    gs = {}
    st = V.ensure_player(gs, "joueur_1")
    st["courante"] = 12.5
    V.refill_saison(gs)
    check("refill → vigueur_max", st["courante"] == V.vigueur_max(gs, "joueur_1"),
          f"courante={st['courante']}")


# ---------------------------------------------------------------------------
# A4. Interface paliers stubbée
# ---------------------------------------------------------------------------

def test_interface_paliers():
    print("\n[A4] interface paliers (D12) stubbée à 1.0")
    check("palier_bonus == 1.0", V.palier_bonus("joueur_1") == 1.0)
    gs = {}
    V.ensure_player(gs, "joueur_1")
    check("vigueur_max == max_base × palier_bonus",
          V.vigueur_max(gs, "joueur_1") == V.MAX_BASE * V.palier_bonus("joueur_1"))
    check("regen_rate == REGEN_BASE × palier_bonus",
          V.regen_rate(gs, "joueur_1") == V.REGEN_BASE * V.palier_bonus("joueur_1"))


# ---------------------------------------------------------------------------
# A5. Primitives de transaction spend / gain (sous-sprint 2)
# ---------------------------------------------------------------------------

def test_primitives_spend_gain():
    print("\n[A5] primitives spend (ratio d'effort) / gain (plafonné)")
    gs = {}
    st = V.ensure_player(gs, "j")
    st["courante"] = 50.0
    r = V.spend(gs, "j", 30.0)
    check("spend couvert → ratio 1.0", r == 1.0, f"ratio={r}")
    check("débit exact", st["courante"] == 20.0, f"courante={st['courante']}")
    r = V.spend(gs, "j", 40.0)
    check("spend partiel → ratio = courante/cost", r == 0.5, f"ratio={r}")
    check("drainé à 0 (pas de dette)", st["courante"] == 0.0,
          f"courante={st['courante']}")
    check("spend coût nul → ratio 1.0, no-op", V.spend(gs, "j", 0.0) == 1.0)
    V.gain(gs, "j", 1000.0)
    check("gain plafonné à vigueur_max", st["courante"] == V.vigueur_max(gs, "j"),
          f"courante={st['courante']}")


# ---------------------------------------------------------------------------
# A6. recolter — action graduée : net positif sur mûr, plante vivante, Qi exporté
# ---------------------------------------------------------------------------

def test_recolter():
    print("\n[A6] recolter : net positif sur mûr, plante vivante, Qi exporté")
    gs = _minimal_state()
    tile = gs["tiles"][0]; eco = gs["eco"]["T0"]
    plant = tile.plants[0]
    plant.current_stage = len(plant.plant_class.growth_stages) - 1   # pleinement mûr
    V.ensure_player(gs, "joueur_1")["courante"] = 50.0
    om_avant = eco.summary()["om_fresh"]
    ratio = ACT.recolter(gs, "joueur_1", plant, eco)
    cour = gs["vigueur"]["joueur_1"]["courante"]
    attendu = 50.0 - ACT.HARVEST_VIGUEUR_COST + ACT.HARVEST_GAIN_FULL * 1.0
    check("effort plein (ratio 1.0)", ratio == 1.0, f"ratio={ratio}")
    check("récolte mûre = net positif", cour == attendu and cour > 50.0,
          f"courante={cour} attendu={attendu}")
    check("plante reste vivante", plant.is_alive)
    check("Qi exporté → résidu déposé (om_fresh ↑)",
          eco.summary()["om_fresh"] > om_avant)


# ---------------------------------------------------------------------------
# A7. deraciner — action binaire : net négatif, Qi au sol, échec à vide
# ---------------------------------------------------------------------------

def test_deraciner():
    print("\n[A7] deraciner : binaire, net négatif, Qi au sol, échec à vide")
    gs = _minimal_state()
    tile = gs["tiles"][0]; eco = gs["eco"]["T0"]
    plant = tile.plants[0]
    plant.current_stage = len(plant.plant_class.growth_stages) - 1
    st = V.ensure_player(gs, "joueur_1"); st["courante"] = 50.0
    om_avant = eco.summary()["om_fresh"]
    ok = ACT.deraciner(gs, "joueur_1", plant, eco)
    check("déracinage payé → succès", ok)
    check("plante morte", not plant.is_alive)
    check("coût ÉLEVÉ débité, aucun gain", st["courante"] == 50.0 - ACT.ELEVE,
          f"courante={st['courante']}")
    check("Qi retourne au sol (om_fresh ↑)", eco.summary()["om_fresh"] > om_avant)
    # Échec à vide : Vigueur < ÉLEVÉ → plante survit, drainée à 0, rien accompli.
    plant2 = tile.plants[1]
    st["courante"] = 10.0
    ok2 = ACT.deraciner(gs, "joueur_1", plant2, eco)
    check("déracinage à vide → échec", not ok2)
    check("plante survit à l'échec", plant2.is_alive)
    check("Vigueur drainée à 0", st["courante"] == 0.0, f"courante={st['courante']}")


# ---------------------------------------------------------------------------
# A8. ecraser — comptabilité seule + multiplicateur d'urgence
# ---------------------------------------------------------------------------

def test_ecraser():
    print("\n[A8] ecraser : retire UN quantum de ravageur + multiplicateur d'urgence")
    gs = _minimal_state(); eco = gs["eco"]["T0"]
    st = V.ensure_player(gs, "joueur_1"); st["courante"] = 100.0
    eco.populations["ravageur"].set(2, 2, 0.30)   # densité ciblée connue
    ok = ACT.ecraser(gs, "joueur_1", eco, 2, 2, urgence=True)
    check("écrasement urgent payé", ok)
    check("coût MODERE × URGENCE débité",
          st["courante"] == 100.0 - ACT.MODERE * ACT.URGENCE_MULT,
          f"courante={st['courante']}")
    check("un quantum de ravageur retiré (exactement)",
          abs(eco.populations["ravageur"].at_plot(2, 2) - (0.30 - DENSITE_PAR_SPRITE)) < 1e-9,
          f"densité={eco.populations['ravageur'].at_plot(2, 2)}")
    st["courante"] = 100.0
    ACT.ecraser(gs, "joueur_1", eco, 2, 2, urgence=False)
    check("hors urgence = MODERE sec", st["courante"] == 100.0 - ACT.MODERE,
          f"courante={st['courante']}")
    # Échec à vide : binaire — Vigueur insuffisante → AUCUN quantum retiré.
    eco.populations["ravageur"].set(3, 3, 0.30)
    st["courante"] = 5.0
    ok_vide = ACT.ecraser(gs, "joueur_1", eco, 3, 3, urgence=True)
    check("écrasement à vide → échec (binaire)", not ok_vide)
    check("aucun quantum retiré à l'échec",
          eco.populations["ravageur"].at_plot(3, 3) == 0.30,
          f"densité={eco.populations['ravageur'].at_plot(3, 3)}")
    check("Vigueur drainée à 0", st["courante"] == 0.0, f"courante={st['courante']}")


# ---------------------------------------------------------------------------
# A9. Non-régression : enchaîner des actions ne crée jamais d'état écolo fantôme
#     (les actions vivent AU-DESSUS du tick — golden écolo testé à part)
# ---------------------------------------------------------------------------

def test_actions_hors_tick():
    print("\n[A9] les actions ne polluent pas l'état écolo hors de leur cible")
    gs = _minimal_state()
    tile = gs["tiles"][0]; eco = gs["eco"]["T0"]
    V.ensure_player(gs, "joueur_1")["courante"] = 100.0
    # Une séquence dépense+gain ne touche ni `week` ni `seed` ni le nombre de
    # plantes vivantes au-delà de la cible explicitement déracinée.
    n_avant = sum(1 for p in tile.plants if p.is_alive)
    week_avant = gs["week"]
    ACT.recolter(gs, "joueur_1", tile.plants[0], eco)   # cible vivante
    ACT.ecraser(gs, "joueur_1", eco, 0, 0, urgence=True)   # cible un plot
    check("la récolte ne tue pas la cible", n_avant ==
          sum(1 for p in tile.plants if p.is_alive))
    check("aucune avance de tick (week inchangé)", gs["week"] == week_avant)


# ---------------------------------------------------------------------------
# C. Façade vigueur_plante (sous-sprint 3) — lecture PURE read-only, jamais
#    pilote. Déterministe sans RNG : on lit des états posés à la main.
# ---------------------------------------------------------------------------

def _mature(plant):
    """Place une plante à son dernier stade (maturité = 1)."""
    plant.current_stage = len(plant.plant_class.growth_stages) - 1
    return plant


def test_facade_purete():
    print("\n[C1] façade vigueur_plante : lecture PURE (aucune écriture)")
    gs = _minimal_state()
    eco = gs["eco"]["T0"]
    plant = _mature(gs["tiles"][0].plants[0])
    eco_avant = eco.summary()
    sante_av, stage_av, health_av = plant.health, plant.current_stage, plant.health
    v1 = VP.vigueur_plante(plant, eco)
    v2 = VP.vigueur_plante(plant, eco)
    check("déterministe (même entrée → même sortie)", v1 == v2, f"{v1}=={v2}")
    check("aucune mutation de l'état écolo", eco.summary() == eco_avant)
    check("aucune mutation de la plante",
          (plant.health, plant.current_stage) == (health_av, stage_av))


def test_facade_sante():
    print("\n[C2] facteur santé : health 3..0 normalisé, mort → Vigueur nulle")
    gs = _minimal_state()
    eco = gs["eco"]["T0"]
    plant = _mature(gs["tiles"][0].plants[0])
    plant.health = 3
    check("santé pleine → 1.0", VP.sante(plant) == 1.0)
    v_sain = VP.vigueur_plante(plant, eco)
    plant.health = 0
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


# ---------------------------------------------------------------------------
# D. Action « manger » (sous-sprint 4, tandem D19) — ressourcement gratuit.
#    Coût NUL, gain ∝ vigueur_plante (façade = modulateur de valeur, §1), plante
#    vivante, no-op écolo. Event-driven hors tick ⇒ déterministe sans RNG.
# ---------------------------------------------------------------------------

def test_manger_gain_organe():
    print("\n[D1] manger : gain = HARVEST_GAIN_FULL × vigueur_plante, coût NUL")
    gs = _minimal_state()
    eco = gs["eco"]["T0"]
    plant = _mature(gs["tiles"][0].plants[0]); plant.health = 3
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
    plant = _mature(tile.plants[0]); plant.health = 3
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


# ---------------------------------------------------------------------------
# E. Vie macroscopique (D31.3) — façades vigueur_macro (read-only) + 3 gestes
#    (favoriser / écraser réel / bêcher vs grelinette). Event-driven hors tick,
#    déterministe sans RNG. N'étend JAMAIS le golden écolo.
# ---------------------------------------------------------------------------

def test_macro_facade_densite_ressource():
    print("\n[E1] façade vigueur_macro : densité × ressource trophique")
    gs = _minimal_state(); eco = gs["eco"]["T0"]
    aux = eco.populations["auxiliaire"]
    aux.set(2, 2, 0.8); aux.activite_grid[2][2] = 0.5   # densité + ressource connues
    v = VM.vigueur_auxiliaire(2, 2, eco)
    check("vigueur = densité × activite (ressource trophique)",
          abs(v - 0.8 * 0.5) < 1e-9, f"v={v}")
    aux.set(2, 2, 0.4)
    v_moins = VM.vigueur_auxiliaire(2, 2, eco)
    check("croît avec la densité (ressource constante)", v > v_moins, f"{v} > {v_moins}")
    aux.activite_grid[2][2] = 0.9
    v_res = VM.vigueur_auxiliaire(2, 2, eco)
    check("croît avec la ressource trophique (densité constante)",
          v_res > v_moins, f"{v_res} > {v_moins}")


def test_macro_facade_purete():
    print("\n[E2] façade vigueur_macro : lecture PURE (aucune écriture)")
    gs = _minimal_state(); eco = gs["eco"]["T0"]
    eco.populations["ravageur"].set(1, 1, 0.5)
    dens_avant = eco.populations["ravageur"].at_plot(1, 1)
    eco_avant = eco.summary()
    a = VM.vigueur_nuisible(1, 1, eco); b = VM.vigueur_nuisible(1, 1, eco)
    check("déterministe (même entrée → même sortie)", a == b, f"{a}=={b}")
    check("aucune mutation du champ lu",
          eco.populations["ravageur"].at_plot(1, 1) == dens_avant)
    check("aucune mutation de l'état écolo", eco.summary() == eco_avant)


def test_macro_descripteur():
    print("\n[E3] descripteur de population qualitatif (philo #5 — pas de chiffre)")
    check("0 (hiver/non installée) → absente", VM.decrire_vigueur_pop(0.0) == "absente")
    check("faible → clairsemée", VM.decrire_vigueur_pop(0.1) == "clairsemée")
    check("moyen → vigoureuse", VM.decrire_vigueur_pop(0.35) == "vigoureuse")
    check("fort → florissante", VM.decrire_vigueur_pop(0.8) == "florissante")
    ordre = ["absente", "clairsemée", "vigoureuse", "florissante"]
    bandes = [VM.decrire_vigueur_pop(v) for v in (0.0, 0.1, 0.35, 0.8)]
    check("bandes monotones croissantes", bandes == ordre, f"{bandes}")


def test_favoriser_auxiliaire():
    print("\n[E4] favoriser_auxiliaire : pose une rondelle habitat (coût MODÉRÉ)")
    gs = _minimal_state(); tile = gs["tiles"][0]
    st = V.ensure_player(gs, "joueur_1"); st["courante"] = 100.0
    avant = tile.get_rondelle_count("auxiliaire")
    ok = ACT.favoriser_auxiliaire(gs, "joueur_1", tile)
    check("payé → succès", ok)
    check("coût MODÉRÉ débité", st["courante"] == 100.0 - ACT.MODERE,
          f"courante={st['courante']}")
    check("une rondelle auxiliaire posée (habitat persistant)",
          tile.get_rondelle_count("auxiliaire") == avant + 1)
    # Échec à vide : Vigueur insuffisante → aucune rondelle ajoutée.
    st["courante"] = 5.0
    avant2 = tile.get_rondelle_count("auxiliaire")
    ok_vide = ACT.favoriser_auxiliaire(gs, "joueur_1", tile)
    check("à vide → échec, aucune rondelle ajoutée",
          not ok_vide and tile.get_rondelle_count("auxiliaire") == avant2)


def test_becher_vs_grelinette():
    print("\n[E5] bêcher tue vers + microbiome ; grelinette préserve (contraste)")
    gs = _minimal_state(); eco = gs["eco"]["T0"]
    st = V.ensure_player(gs, "joueur_1"); st["courante"] = 100.0
    eco.populations["vers_de_terre"].set(2, 2, 0.30)
    eco.microbiome.set(2, 2, 2.0)   # assez haut pour que le malus ne soit pas clampé
    micro_avant = eco.microbiome.at_plot(2, 2)
    ok = ACT.becher(gs, "joueur_1", eco, 2, 2)
    check("bêchage payé (FAIBLE)", ok and st["courante"] == 100.0 - ACT.FAIBLE,
          f"courante={st['courante']}")
    check("un quantum de vers retiré (sprites de vers disparaissent)",
          abs(eco.populations["vers_de_terre"].at_plot(2, 2) - (0.30 - DENSITE_PAR_SPRITE)) < 1e-9)
    check("microbiome local abaissé (dette différée)",
          abs(eco.microbiome.at_plot(2, 2) - (micro_avant - ACT.BECHAGE_MICROBIOME_MALUS)) < 1e-9,
          f"micro={eco.microbiome.at_plot(2, 2)}")
    # Grelinette : jumeau qui préserve — ni vers ni microbiome touchés.
    vers_avant = eco.populations["vers_de_terre"].at_plot(2, 2)
    micro2 = eco.microbiome.at_plot(2, 2)
    st["courante"] = 100.0
    okg = ACT.grelinette(gs, "joueur_1")
    check("grelinette payée (MODÉRÉ)", okg and st["courante"] == 100.0 - ACT.MODERE,
          f"courante={st['courante']}")
    check("grelinette NE tue PAS les vers",
          eco.populations["vers_de_terre"].at_plot(2, 2) == vers_avant)
    check("grelinette préserve le microbiome", eco.microbiome.at_plot(2, 2) == micro2)


def test_ecraser_pression_revient():
    print("\n[E6] écraser : la pression REVIENT depuis la ressource (philo #1)")
    gs = _minimal_state(); eco = gs["eco"]["T0"]; tile = gs["tiles"][0]
    _mature(gs["tiles"][0].plants[0]).health = 3   # feuillage-hôte du ravageur
    plants = tile.plants
    # Laisse le ravageur s'installer sur le feuillage (relaxation déterministe).
    for _ in range(12):
        eco.tick_populations(tile, plants)
    rav = eco.populations["ravageur"]
    r, c = max(((rr, cc) for rr in range(rav.rows) for cc in range(rav.cols)),
               key=lambda rc: rav.at_plot(*rc))
    d_eq = rav.at_plot(r, c)
    st = V.ensure_player(gs, "joueur_1"); st["courante"] = 100.0
    ACT.ecraser(gs, "joueur_1", eco, r, c, urgence=False)
    d_apres = rav.at_plot(r, c)
    check("densité de fond installée > 1 quantum", d_eq > DENSITE_PAR_SPRITE,
          f"d_eq={d_eq:.4f}")
    check("un quantum retiré exactement", abs(d_apres - (d_eq - DENSITE_PAR_SPRITE)) < 1e-9,
          f"d_apres={d_apres:.4f}")
    for _ in range(4):     # quelques semaines plus tard…
        eco.tick_populations(tile, plants)
    d_recover = rav.at_plot(r, c)
    check("la pression revient (densité remonte au-dessus du post-écrasement)",
          d_recover > d_apres, f"d_apres={d_apres:.4f} d_recover={d_recover:.4f}")


# ---------------------------------------------------------------------------
# B. Golden de trajectoire (hash) — cadencement régen vs refill via l'engine
# ---------------------------------------------------------------------------

def _trajectoire() -> list[float]:
    """Pilote l'engine de la semaine 2 à la 29 (traverse été@14 et automne@27).
    `max_base` volontairement haut (régen ne sature pas dans la fenêtre) → le
    snap du refill est visiblement distinct de la pente de régen."""
    gs = _minimal_state(week=2)
    st = V.ensure_player(gs, "joueur_1")
    st["max_base"] = 1000.0
    st["courante"] = 0.0
    eng = Engine(gs)
    traj = []
    for _ in range(28):
        eng.tick_semaine()
        traj.append(round(gs["vigueur"]["joueur_1"]["courante"], 6))
    return traj


def _compute_hash() -> str:
    traj = _trajectoire()
    h = hashlib.sha256()
    h.update(repr(traj).encode("utf-8"))
    return h.hexdigest()


def test_golden_trajectoire():
    print("\n[B] golden de trajectoire (hash de la courbe de Vigueur)")
    traj = _trajectoire()
    # Sanity diégétique avant le hash : pente +10, snap aux frontières de saison.
    # Semaines 2..13 = régen (0→10→…→120), semaine 14 (été) = refill@1000.
    check("régen linéaire +REGEN_BASE en début de fenêtre",
          traj[0] == 10.0 and traj[1] == 20.0 and traj[2] == 30.0,
          f"début={traj[:3]}")
    # Index 12 = semaine 14 (été, début de saison) → refill au plafond.
    check("refill au passage de saison (été)", traj[12] == 1000.0,
          f"traj[12]={traj[12]}")

    digest = _compute_hash()
    capture = "--capture" in sys.argv
    if capture or not os.path.exists(HASH_FILE):
        with open(HASH_FILE, "w") as f:
            f.write(digest + "\n")
        check(f"hash de référence capturé", True, digest)
        return
    with open(HASH_FILE) as f:
        ref = f.read().strip()
    check("hash de trajectoire == référence", digest == ref,
          digest if digest == ref else f"attendu {ref} obtenu {digest}")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Golden JOUEUR Vigueur (D11, sous-sprint 1)")
    print("=" * 60)
    test_noop_sans_joueur()
    test_regen_plafonnee()
    test_refill_saison()
    test_interface_paliers()
    test_primitives_spend_gain()
    test_recolter()
    test_deraciner()
    test_ecraser()
    test_actions_hors_tick()
    test_facade_purete()
    test_facade_sante()
    test_facade_maturite()
    test_facade_qi_local()
    test_facade_gene_enveloppe()
    test_facade_descripteur()
    test_manger_gain_organe()
    test_manger_modulation_facade()
    test_manger_no_op_ecolo()
    test_manger_plafond()
    test_macro_facade_densite_ressource()
    test_macro_facade_purete()
    test_macro_descripteur()
    test_favoriser_auxiliaire()
    test_becher_vs_grelinette()
    test_ecraser_pression_revient()
    test_golden_trajectoire()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
