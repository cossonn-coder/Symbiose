"""
SYMBIOSE — tests/vigueur/macro.py
E. Vie macroscopique (D31.3) — façades vigueur_macro (read-only) + 3 gestes
(favoriser / écraser réel / bêcher vs grelinette) + retour de pression depuis la
ressource. Event-driven hors tick, déterministe sans RNG. N'étend JAMAIS le
golden écolo.
"""
from fields import DENSITE_PAR_SPRITE
from sim import vigueur as V
from sim import vigueur_macro as VM
from sim import actions as ACT

from .harness import check, _minimal_state, _mature


def test_macro_facade_densite_ressource():
    print("\n[E1] façade vigueur_macro : densité × ressource trophique")
    gs = _minimal_state(); eco = gs["eco"]["T0"]
    # `auxiliaire` est une CATÉGORIE depuis ④c : on pose une espèce membre
    # (coccinelle) et on lit la façade de catégorie `vigueur_auxiliaire` (agrégat).
    aux = eco.populations["coccinelle"]
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
    eco.populations["puceron"].set(1, 1, 0.5)
    dens_avant = eco.populations["puceron"].at_plot(1, 1)
    eco_avant = eco.summary()
    a = VM.vigueur_nuisible(1, 1, eco); b = VM.vigueur_nuisible(1, 1, eco)
    check("déterministe (même entrée → même sortie)", a == b, f"{a}=={b}")
    check("aucune mutation du champ lu",
          eco.populations["puceron"].at_plot(1, 1) == dens_avant)
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
    eco.populations["lombric"].set(2, 2, 0.30)
    eco.microbiome.set(2, 2, 2.0)   # assez haut pour que le malus ne soit pas clampé
    micro_avant = eco.microbiome.at_plot(2, 2)
    ok = ACT.becher(gs, "joueur_1", eco, 2, 2)
    check("bêchage payé (FAIBLE)", ok and st["courante"] == 100.0 - ACT.FAIBLE,
          f"courante={st['courante']}")
    check("un quantum de vers retiré (sprites de vers disparaissent)",
          abs(eco.populations["lombric"].at_plot(2, 2) - (0.30 - DENSITE_PAR_SPRITE)) < 1e-9)
    check("microbiome local abaissé (dette différée)",
          abs(eco.microbiome.at_plot(2, 2) - (micro_avant - ACT.BECHAGE_MICROBIOME_MALUS)) < 1e-9,
          f"micro={eco.microbiome.at_plot(2, 2)}")
    # Grelinette (⑧) : jumeau qui PRÉSERVE+AÈRE — FAVORISE les vers, ne touche pas le
    # microbiome, et fait REMONTER la structure du sol de GRELINETTE_GAIN (plein effet).
    vers_avant = eco.populations["lombric"].at_plot(2, 2)
    micro2 = eco.microbiome.at_plot(2, 2)
    eco.structure_sol.set(2, 2, 0.5)   # valeur mi-course → +GRELINETTE_GAIN sans clamp
    struct_avant = eco.structure_sol.at_plot(2, 2)
    st["courante"] = 100.0
    okg = ACT.grelinette(gs, "joueur_1", eco, 2, 2)
    check("grelinette payée (MODÉRÉ)", okg and st["courante"] == 100.0 - ACT.MODERE,
          f"courante={st['courante']}")
    check("grelinette FAVORISE les vers (un quantum ajouté)",
          abs(eco.populations["lombric"].at_plot(2, 2) - (vers_avant + DENSITE_PAR_SPRITE)) < 1e-9)
    check("grelinette préserve le microbiome", eco.microbiome.at_plot(2, 2) == micro2)
    check("grelinette remonte la structure du sol de GRELINETTE_GAIN",
          abs(eco.structure_sol.at_plot(2, 2) - (struct_avant + ACT.GRELINETTE_GAIN)) < 1e-9,
          f"struct={eco.structure_sol.at_plot(2, 2)}")


def test_ecraser_pression_revient():
    print("\n[E6] écraser : la pression REVIENT depuis la ressource (philo #1)")
    gs = _minimal_state(); eco = gs["eco"]["T0"]; tile = gs["tiles"][0]
    _mature(gs["tiles"][0].plants[0]).vitalite = 1.0   # feuillage-hôte du ravageur
    plants = tile.plants
    # Laisse le ravageur s'installer sur le feuillage (relaxation déterministe).
    for _ in range(12):
        eco.tick_populations(tile, plants)
    rav = eco.populations["puceron"]
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
