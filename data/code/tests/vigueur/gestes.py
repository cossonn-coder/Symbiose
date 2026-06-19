"""
SYMBIOSE — tests/vigueur/gestes.py
A5–A9. Primitives de transaction (spend/gain) + gestes sur le vivant
(recolter/deraciner/tailler/ecraser/ecraser_plante) + non-régression « actions
hors tick ». Le golden ÉCOLO est testé à part (`tests/test_golden.py`) : ici on
vérifie les CONTRATS Vigueur (coût/binaire/gain) et la réponse émergente.
"""
from plants import Basil, Bean, Sunflower, PoaAnnua
from fields import DENSITE_PAR_SPRITE
from sim.growth import grow_plant, f_lignification, COUPE_NETTE, SEUIL_DEGAT
from sim import vigueur as V
from sim import actions as ACT

from .harness import check, SEED, _minimal_state, _gs_with, _construire


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
# A7b. tailler — action binaire : coût MODÉRÉ, gain ∝ maturité, appelle le seam
#      structurel (§F). La RÉPONSE (débourrement) est testée côté structure dans
#      test_croissance ; ici on vérifie le CONTRAT Vigueur (coût/binaire/gain/objets).
# ---------------------------------------------------------------------------

def test_tailler():
    print("\n[A7b] tailler : binaire, coût MODÉRÉ, gain ∝ maturité, seam appelé")
    gs = _minimal_state()
    tile = gs["tiles"][0]; eco = gs["eco"]["T0"]
    plant = tile.plants[0]   # Tomato → clé "tomate"
    st = V.ensure_player(gs, "joueur_1"); st["courante"] = 100.0
    # Coût : sur une plante IMMATURE (maturité 0 → gain nul), tailler débite MODERE net.
    plant.current_stage = 0
    ok = ACT.tailler(gs, "joueur_1", plant, eco)
    check("tailler payé → succès", ok)
    check("coût MODÉRÉ débité (immature → gain nul)",
          st["courante"] == 100.0 - ACT.MODERE, f"courante={st['courante']}")
    # Gain : sur une plante MÛRE, le gain ∝ maturité remonte la Vigueur au-dessus du
    # seul débit du coût (reste net coûteux : gain < coût).
    plant.current_stage = len(plant.plant_class.growth_stages) - 1   # mûr → maturité 1
    st["courante"] = 100.0
    ACT.tailler(gs, "joueur_1", plant, eco)
    attendu = 100.0 - ACT.MODERE + ACT.HARVEST_GAIN_FULL * 1.0 * ACT.GAIN_TAILLE_RATIO
    check("gain ∝ maturité ajouté (mûr → net > coût seul)",
          abs(st["courante"] - attendu) < 1e-9 and st["courante"] > 100.0 - ACT.MODERE,
          f"courante={st['courante']} attendu={attendu}")
    # Binaire : Vigueur < coût → échec, structure inchangée, Vigueur drainée à 0.
    plant2 = tile.plants[1]
    n2 = len(plant2.segments)
    st["courante"] = 5.0
    ok_vide = ACT.tailler(gs, "joueur_1", plant2, eco)
    check("tailler à vide → échec (binaire)", not ok_vide)
    check("structure inchangée à l'échec", len(plant2.segments) == n2,
          f"len={len(plant2.segments)}")
    check("Vigueur drainée à 0", st["courante"] == 0.0, f"courante={st['courante']}")
    # Objets touchés : technique + outil + clé d'espèce (cible vivante dynamique).
    objets = ACT._objets_action("tailler", plant)
    check("objets = taille + sécateur + clé d'espèce",
          "taille" in objets and "sécateur" in objets and "tomate" in objets,
          f"objets={objets}")


# ---------------------------------------------------------------------------
# A8. ecraser — comptabilité seule + multiplicateur d'urgence
# ---------------------------------------------------------------------------

def test_ecraser():
    print("\n[A8] ecraser : retire UN quantum de ravageur + multiplicateur d'urgence")
    gs = _minimal_state(); eco = gs["eco"]["T0"]
    st = V.ensure_player(gs, "joueur_1"); st["courante"] = 100.0
    eco.populations["puceron"].set(2, 2, 0.30)   # densité ciblée connue
    ok = ACT.ecraser(gs, "joueur_1", eco, 2, 2, urgence=True)
    check("écrasement urgent payé", ok)
    check("coût MODERE × URGENCE débité",
          st["courante"] == 100.0 - ACT.MODERE * ACT.URGENCE_MULT,
          f"courante={st['courante']}")
    check("un quantum de ravageur retiré (exactement)",
          abs(eco.populations["puceron"].at_plot(2, 2) - (0.30 - DENSITE_PAR_SPRITE)) < 1e-9,
          f"densité={eco.populations['puceron'].at_plot(2, 2)}")
    st["courante"] = 100.0
    ACT.ecraser(gs, "joueur_1", eco, 2, 2, urgence=False)
    check("hors urgence = MODERE sec", st["courante"] == 100.0 - ACT.MODERE,
          f"courante={st['courante']}")
    # Échec à vide : binaire — Vigueur insuffisante → AUCUN quantum retiré.
    eco.populations["puceron"].set(3, 3, 0.30)
    st["courante"] = 5.0
    ok_vide = ACT.ecraser(gs, "joueur_1", eco, 3, 3, urgence=True)
    check("écrasement à vide → échec (binaire)", not ok_vide)
    check("aucun quantum retiré à l'échec",
          eco.populations["puceron"].at_plot(3, 3) == 0.30,
          f"densité={eco.populations['puceron'].at_plot(3, 3)}")
    check("Vigueur drainée à 0", st["courante"] == 0.0, f"courante={st['courante']}")
    # Maladresse (retour F5 2026-06-12) : écraser le sprite cliqué QUELLE QUE
    # soit sa guilde — un auxiliaire cliqué meurt, le ravageur n'est PAS touché.
    st["courante"] = 100.0
    eco.populations["auxiliaire"].set(4, 4, 0.30)
    eco.populations["puceron"].set(4, 4, 0.20)
    ok_aux = ACT.ecraser(gs, "joueur_1", eco, 4, 4, guilde="auxiliaire", urgence=False)
    check("écraser un auxiliaire payé", ok_aux)
    check("un quantum d'auxiliaire retiré",
          abs(eco.populations["auxiliaire"].at_plot(4, 4) - (0.30 - DENSITE_PAR_SPRITE)) < 1e-9,
          f"aux={eco.populations['auxiliaire'].at_plot(4, 4)}")
    check("ravageur co-localisé INTACT (on n'a écrasé QUE l'auxiliaire)",
          eco.populations["puceron"].at_plot(4, 4) == 0.20,
          f"rav={eco.populations['puceron'].at_plot(4, 4)}")
    # Guilde inconnue → refus AVANT toute dépense (erreur de protocole).
    st["courante"] = 100.0
    ko = ACT.ecraser(gs, "joueur_1", eco, 4, 4, guilde="licorne", urgence=False)
    check("guilde inconnue → échec sans effet", not ko)
    check("guilde inconnue → AUCUNE Vigueur dépensée", st["courante"] == 100.0,
          f"courante={st['courante']}")


# ---------------------------------------------------------------------------
# A8b. ecraser_plante (écraser·volet 2) — réponse ÉMERGENTE des plantes :
#      déformation (DOUX) / écimage (NET) / mort par santé (sentier, Q3),
#      modulée par les deux traits d'espèce (résistance × âge, stimulation).
# ---------------------------------------------------------------------------

def test_ecraser_plante():
    print("\n[A8b] ecraser_plante : déformation / écimage / mort (sentier), par traits")
    gs, tile, eco = _gs_with((PoaAnnua, 1, 1), (Sunflower, 2, 2),
                             (Basil, 3, 3), (Bean, 4, 4))
    st = V.ensure_player(gs, "joueur_1"); st["max_base"] = 10_000.0; st["courante"] = 10_000.0

    # (a) DOUX — pâturin ÉTABLI (résistance 0.9 × âge plein) : intensité 0.1 < seuil.
    #     Structure intacte, auxine du collet baissée, santé NON touchée.
    poa = tile.plants[0]
    grow_plant(poa, SEED, 1)                       # donne une auxine réelle au collet
    for s in poa.segments:
        s.age_weeks = 60                           # établi → f_lignification ≈ 1
    aux_av, n_av, sante_av = poa.segments[0].auxin, len(poa.segments), poa.health
    intensite_poa = 1.0 * (1.0 - 0.9 * f_lignification(60))
    check("pâturin établi → régime DOUX (intensité < COUPE_NETTE)",
          intensite_poa < COUPE_NETTE, f"intensité={intensite_poa:.3f}")
    ok = ACT.ecraser_plante(gs, "joueur_1", poa, eco)
    check("écraser un pâturin établi → payé", ok)
    check("DOUX : structure intacte (rien d'écimé)", len(poa.segments) == n_av)
    check("DOUX : auxine du collet baissée (déformation → ramification émergente)",
          poa.segments[0].auxin < aux_av, f"{aux_av:.3f} → {poa.segments[0].auxin:.3f}")
    check("DOUX : santé NON touchée", poa.health == sante_av)

    # (b) NET — tournesol jeune (résistance 0.15) avec une chaîne de segments :
    #     écimage du sous-arbre ciblé ET santé entamée (stimulation 0.05 < épargne).
    sun = _construire(tile.plants[1], 12)
    check("tournesol a une chaîne de segments (≥ 2)", len(sun.segments) >= 2,
          f"{len(sun.segments)} segments")
    vise = next(i for i, s in enumerate(sun.segments) if s.parent is not None)
    n_av, sante_av = len(sun.segments), sun.health
    age_sun = max(s.age_weeks for s in sun.segments)
    intensite_sun = 1.0 * (1.0 - 0.15 * f_lignification(age_sun))
    check("tournesol jeune → régime NET (intensité ≥ COUPE_NETTE)",
          intensite_sun >= COUPE_NETTE, f"intensité={intensite_sun:.3f}")
    ok = ACT.ecraser_plante(gs, "joueur_1", sun, eco, segment_id=vise)
    check("NET : écimage (le sous-arbre ciblé a disparu)", len(sun.segments) < n_av,
          f"{n_av} → {len(sun.segments)}")
    check("NET + stimulation basse (tournesol 0.05) → santé entamée (−1)",
          sun.health == sante_av - 1, f"santé {sante_av} → {sun.health}")

    # (c) NET — basilic (résistance 0.4) ÉPARGNÉ : écimé MAIS santé intacte car il
    #     PROFITE (stimulation 0.85 ≥ seuil d'épargne) → le pincement.
    bas = _construire(tile.plants[2], 10)
    check("(1 − stim basilic) sous le seuil de dégât (épargné)",
          (1.0 - 0.85) < SEUIL_DEGAT)
    vise_b = next(i for i, s in enumerate(bas.segments) if s.parent is not None)
    n_av, sante_av = len(bas.segments), bas.health
    ok = ACT.ecraser_plante(gs, "joueur_1", bas, eco, segment_id=vise_b)
    check("basilic écimé (NET)", len(bas.segments) < n_av, f"{n_av} → {len(bas.segments)}")
    check("basilic ÉPARGNÉ : santé intacte (repart buissonnant = pincement)",
          bas.health == sante_av, f"santé={bas.health}")

    # (d) SENTIER (Q3) — semis fragile (tournesol non poussé : réduit au collet) :
    #     3 écrasements du COLLET → santé 3→0 → mort. Le collet est PROTÉGÉ (jamais
    #     retiré) : c'est la SANTÉ qui réalise la mort, pas la structure (rejet de
    #     souche n'a donc rien à ressusciter).
    semis = tile.plants[3]                          # Haricot jeune (fragile), 1 segment (collet)
    n_seg0 = len(semis.segments)
    for i in range(3):
        ACT.ecraser_plante(gs, "joueur_1", semis, eco)   # cible défaut = collet
    check("semis : 3 écrasements du collet → santé tombée à 0", semis.health == 0,
          f"santé={semis.health}")
    check("semis : mort émergente (is_alive False)", not semis.is_alive)
    check("collet protégé : structure JAMAIS retirée (mort par santé, pas structure)",
          len(semis.segments) == n_seg0, f"{n_seg0} → {len(semis.segments)}")

    # (e) Coût = celui de `tailler` (× urgence), binaire (effet QUE si payé).
    gs2, tile2, eco2 = _gs_with((Basil, 1, 1))
    plant2 = _construire(tile2.plants[0], 6)
    st2 = V.ensure_player(gs2, "joueur_1")
    cout_nominal = ACT.cout_action(gs2, "joueur_1", "tailler",
                                   ACT._objets_action("tailler", plant2))
    check("coût nominal = base tailler (MODÉRÉ, sans maîtrise)",
          cout_nominal == ACT.MODERE, f"coût={cout_nominal}")
    st2["courante"] = cout_nominal - 1.0            # insuffisant
    n_av, sante_av = len(plant2.segments), plant2.health
    ok_vide = ACT.ecraser_plante(gs2, "joueur_1", plant2, eco2)
    check("écraser à vide → échec (binaire)", not ok_vide)
    check("échec : structure ET santé inchangées",
          len(plant2.segments) == n_av and plant2.health == sante_av)
    check("échec binaire : Vigueur drainée à 0", st2["courante"] == 0.0,
          f"courante={st2['courante']}")
    st2["courante"] = 1000.0
    ACT.ecraser_plante(gs2, "joueur_1", plant2, eco2, urgence=True)
    check("urgence : coût = MODÉRÉ × URGENCE débité",
          st2["courante"] == 1000.0 - ACT.MODERE * ACT.URGENCE_MULT,
          f"courante={st2['courante']}")


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
