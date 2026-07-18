"""
SYMBIOSE — bancs/biotique.py
Bancs d'essai BIOTIQUES (le vivant : faune ravageuse, chaîne de pollinisation,
germination potagère). Tronçon ④ du sprint « bancs d'essai » — dernière famille.

Trois mondes paramétrés qui FORCENT un phénomène du vivant au-delà de son seuil,
chacun avec son oracle (tests/bancs/test_biotique.py), et trois diagnostics D47
tranchés (criblage fantôme C3, chaîne floraison muette C4, Solanaceae qui ne
lèvent pas C5). Pure COMPOSITION de l'état moteur (champs de faune, état floral,
graines déposées, paillage) — AUCUNE mécanique nouvelle, donc golden NEUTRE (ces
fabriques ne sont jamais montées pour smoke/full, cf. `cmd_init`).

Comme partout dans `bancs/`, un signe ne MENT jamais : l'oracle le lit via
`sim.semiologie` (ravageurs) ou via l'état moteur réel (fruits, plantules), au
même endroit que la vue Godot.
"""
from __future__ import annotations

from plants import (Basil, AppleTree, Phacelia, Bean, Sunflower, Ivy, Jasmine,
                    Tomato, Pepper)
from plants.genetics import clamp_gene
from fields.seedbank import GrainEnAttente
from sim.seeds import PlayerSeedBank, Seed
from world import House, Support, MUR
from .base import build_banc_tile, monde, force_faune, vieillir

# ─────────────────────────── 1. infestation ravageur ─────────────────────────
# Densité `puceron` (catégorie `ravageur`) pré-chargée BIEN au-dessus du floor du
# signe (RAVAGEURS_FLOOR ≈ 0.025, cf. sim/semiologie). On reste sous une infestation
# foudroyante : le banc montre un limbe CRIBLÉ sur un hôte VIVANT, pas un cadavre.
# La densité forcée DÉCROÎT au tick (hiver → warmth=0 → cible 0 → décrue 0.55/sem,
# cf. force_faune) : c'est un FORÇAGE-PULSE qui s'observe TÔT (oracle à 2 sem). Le
# microbiome est tenu HAUT pour éviter la bascule LÉTALE de l'herbivorie
# (HERBIVORY_LETHAL_MICRO = 0.20, soit micro_norm = micro/3 ≥ 0.20 → micro ≥ 0.6) :
# l'hôte est mordu (criblé) sans être tué dans la fenêtre d'observation.
RAVAGEUR_ESPECE  = "puceron"
RAVAGEUR_DENSITE = 0.5
MICRO_NON_LETAL  = 1.0     # micro_norm ≈ 0.33 > 0.20 → herbivorie NON doublée (hôte survit)


def infestation_ravageur():
    """Banc « criblage » (tranche D47-C3) : DEUX basilics jumeaux, l'un sous une
    densité `puceron` forcée (limbe criblé/troué → signe `ravageurs`, signe de
    FORME), l'autre témoin SANS forçage (limbe sain). Isole le VRAI criblage du
    rendu normal des feuilles (« petits points » ≠ criblage). Oracle :
    tests/bancs/test_biotique.py (observation TÔT, le forçage-pulse décroît)."""
    infeste, eco_i = build_banc_tile("INFESTE", "terre", 8, 8,
                                     humidite=1.3, fertilite=1.1,
                                     microbiome=MICRO_NON_LETAL)
    temoin, eco_t = build_banc_tile("TEMOIN", "terre", 8, 8, 500.0, 0.0,
                                    humidite=1.3, fertilite=1.1,
                                    microbiome=MICRO_NON_LETAL)
    infeste.add_plant(Basil, 4, 4)
    temoin.add_plant(Basil, 4, 4)
    force_faune(eco_i, RAVAGEUR_ESPECE, RAVAGEUR_DENSITE)
    return monde([infeste, temoin],
                 {infeste.tile_id: eco_i, temoin.tile_id: eco_t})


# ──────────────────────────── 2. verger en floraison ─────────────────────────
# Chaîne floraison → pollen → butineurs → nouaison → fruits (tranche D47-C4). Le
# banc force les conditions IDÉALES et l'ACCÉLÈRE par deux pré-charges sanctionnées :
#   • pommiers pré-vieillis à maturity_years (mêmes que `cmd_init` config "full") →
#     fructifient dès cette saison au lieu de l'an 5 ;
#   • état floral pré-armé `floraison=1.0` + `a_fleuri=True` : la fenêtre
#     photopériodique réelle (jours ≥ 13.5 h) n'ouvre qu'à la sem. ~15, donc plutôt
#     que d'attendre la montée NATURELLE, on pose la PLEINE floraison et on laisse la
#     FANAISON se dérouler vraiment (relaxe vers 0 hors fenêtre, ~3 sem). La nouaison
#     se déclenche quand `floraison < SEUIL_NOUAISON` (0.2) → fruits.
# Pollinisateurs PRÉ-CHARGÉS (`abeille`, attractive sur Rosaceae) : les butineurs
# MARCHENT réellement sur les fleurs ouvertes et DÉPOSENT le pollen (pollen_recu),
# que la nouaison entomophile lit (g(pollen), sans plancher). Chaque maillon est donc
# EXERCÉ par le moteur, pas court-circuité. Humidité HAUTE : le pommier procédural à
# racines concentrées meurt vite de soif sinon (cf. AppleTree.foliage_halfwidth).
VERGER_AGE       = 6.0     # > maturity_years (5) → is_seed_bearing + gate d'âge nouaison
ABEILLE_PRECHARGE = 1.0    # présence butineuse immédiate sur les fleurs ouvertes
VERGER_PLOTS     = [(2, 2), (2, 5), (5, 3)]   # petit verger de 3 pommiers


def verger_floraison():
    """Banc « verger en fleurs » (tranche D47-C4) : 3 pommiers mûrs pré-armés en
    pleine floraison, pollinisés par des abeilles pré-chargées. La fanaison
    déclenche la nouaison entomophile (pollen reçu → fruits). Vérifie la chaîne
    complète floraison→pollen→butineurs→nouaison→fruits sur un monde IDÉAL : un
    maillon rompu ici = régression moteur (≠ artefact carte). Oracle :
    tests/bancs/test_biotique.py (butineurs vus pendant la floraison + fruits noués)."""
    tile, eco = build_banc_tile("VERGER", "terre", 8, 8,
                                humidite=2.0, fertilite=1.5, microbiome=0.5)
    for (r, c) in VERGER_PLOTS:
        arbre = tile.add_plant(AppleTree, r, c)
        vieillir(arbre, VERGER_AGE)
        arbre.floraison = 1.0      # pleine floraison armée ; la FANAISON (réelle) nouera
        arbre.a_fleuri = True      # « est passé par la pleine floraison » → prêt à nouer
    force_faune(eco, "abeille", ABEILLE_PRECHARGE)
    return monde([tile], {tile.tile_id: eco})


# ───────────────────────────── 3. semis tempéré ──────────────────────────────
# Germination Solanaceae (tranche D47-C5) — banc ISOLÉ : on NEUTRALISE les deux
# tueurs qui empêchent tomate/poivron de s'installer sur la carte `full`, pour ne
# tester QUE la porte de germination de `planter` :
#   • le MILDIOU familial Solanaceae frappe dès qu'une rondelle `maladie` est posée
#     (un aléa météo/ravageur en pose au passage de saison) → on SATURE toutes les
#     tiges de `paillage` : plus aucune tige libre, donc l'aléa ne peut AJOUTER de
#     rondelle `maladie` (cf. resolution.apply_mutations) → zéro mildiou ;
#   • le FROID de démarrage (gelée tardive sur tissu tendre) → le même paillage
#     saturé protège à 100 % (PAILLAGE_PROTECT 0.25 × ≥4 → cap 1.0).
# Niche rendue FAVORABLE (pleine lumière, sol perturbé, sol jeune) pour une levée
# fiable, et succession spontanée COUPÉE (banc isolé : seuls les grains plantés
# lèvent). Le grain est DÉPOSÉ directement (ce que fait `planter` en interne :
# append d'un GrainEnAttente) car `cmd_init` n'a pas encore de game_state pour jouer
# le geste — la porte testée (`_lever_grains_en_attente`) est identique.
SEMIS_ESPECES = [("tomate", (3, 3)), ("poivron", (5, 5))]


def semis_tempere():
    """Banc « semis potager » (tranche D47-C5) : une tuile tempérée, paillée et à
    niche favorable, où l'on plante tomate ET poivron. Le mildiou familial et le
    froid étant neutralisés (paillage saturé) et la succession isolée, les grains
    LÈVENT et la plantule SURVIT. Tranche si « les Solanaceae ne lèvent pas » vient
    de la porte de `planter` (ce banc le réfute) ou de la fragilité de la carte
    `full`. Oracle : tests/bancs/test_biotique.py."""
    # Depuis la germination thermique (③), la levée exige un SOL CHAUD (le poivron,
    # t_germ_opt=24, est la Solanaceae la plus thermophile). C'est une porte à part
    # entière que ce banc ne cherche PAS à tester : il l'ouvre en se faisant OBSERVER
    # en plein été — l'oracle monte le banc à un `week_depart` estival (cf.
    # tests/bancs/test_biotique.py), où la T_air chaude tient la T_sol dans la fenêtre
    # de levée. Forcer `temperature_sol` à l'init ne servirait à rien : l'inertie
    # thermique la relaxe vers T_air dès le 1er tick (d'où le démarrage saisonnier).
    tile, eco = build_banc_tile("SEMIS", "terre", 8, 8,
                                humidite=1.3, fertilite=1.2, microbiome=0.5)
    eco.lumiere.fill(1.0)            # pleine lumière → niche de germination ouverte
    eco.disturbance.fill(1.0)        # sol fraîchement remué (pionnier favorisé)
    eco.soil_memory_deep.fill(0.0)   # sol jeune → niche large pour le potager
    eco.seed_bank.germination_candidates = lambda *a, **k: []   # banc ISOLÉ : pas d'adventice
    for stake in tile.stakes:        # sature le paillage : pas de tige libre → pas de rondelle maladie
        while stake.add("paillage"):
            pass
    banque = PlayerSeedBank()
    for espece, (r, c) in SEMIS_ESPECES:
        banque.add(Seed(species=espece))   # graine du joueur (re-semis possible au F5)
        tile.grains_en_attente.setdefault((r, c), []).append(
            GrainEnAttente(species=espece, cultive=True, player="joueur_1"))
    return monde([tile], {tile.tile_id: eco}, banque=banque)


# ─────────────────────── 4. étalement de floraison (S2) ───────────────────────
# Banc de la DÉSYNCHRONISATION florale (sprint bugs d'émergence, S2). Il prouve que
# le gène `phenologie_florale` (tronçon ③) ÉTALE les dates de floraison au lieu d'un
# créneau synchrone unique — le trou S2 (« toutes les plantes fleurissent la même
# semaine ») fermé par une VARIABILITÉ intra-espèce, pure sélection/héritage (philo
# #2), sans mécanique nouvelle. Comme `verger_floraison`, il compose un monde et
# LAISSE le moteur (`_tick_floraison`) convertir chaque gène en un seuil de forçage
# floral propre (`gdd_eff = gdd_floraison − FLORA_GENE_SHIFT·(gène−1)`) → l'individu
# « lève-tôt » franchit la porte florale AVANT le « lève-tard ». Golden NEUTRE.
#
# Monde MONO-ESPÈCE DENSE : un tapis de phacélie (engrais vert annuel très
# mellifère, cycle éclair). Chaque pied reçoit un `phenologie_florale` ÉTALÉ
# déterministiquement sur [ETAL_GENE_LO, ETAL_GENE_HI] (un damier de lignées, comme
# un pool-sol à variance réelle, sans dépendre d'un tirage). Deux ACCÉLÉRATIONS
# sanctionnées (cf. base.py), qui posent le phénomène « prêt à s'ouvrir » sans
# dérouler la montée entière :
#   • plants posés d'emblée au stade seed-bearing (`current_stage` = mature) → le
#     gate de MATURITÉ est franchi dès le 1er tick, si bien que c'est le SEUIL DE
#     FORÇAGE thermique par lignée (`gdd_eff`) qui devient la contrainte BINDANTE ;
#   • `gdd_accum` PRÉ-CHARGÉ JUSTE SOUS le plus bas des seuils (ETAL_GDD_PRECHARGE)
#     → l'accumulation naturelle balaie ensuite la plage des seuils par lignée
#     `gdd_eff = bloom_forcing_gdd − FLORA_GENE_SHIFT·(gène−1)` (Phacelia : ~29→47
#     pour genes 1.45→0.55) sur plusieurs semaines → l'individu « lève-tôt » (seuil
#     abaissé) FRANCHIT AVANT le « lève-tard » → étalement des dates. Recalibré au
#     sprint FLORAISON & FRUCTIFICATION ① (forçage événementiel : plus de porte
#     photopériode, seuils BAS → l'ancien précharge 100 overshootait tout).
# La phacélie est déjà au catalogue et à l'encyclopédie (concept `phenologie_florale`
# ajouté au ④) → aucune espèce neuve (règle catalogue/voix respectée).
ETAL_ROWS = ETAL_COLS = 8       # 64 pieds : échantillon statistique stable des dates
ETAL_GENE_LO = 0.55            # lignées « lève-tard » (seuil floral relevé)
ETAL_GENE_HI = 1.45            # lignées « lève-tôt » (seuil floral abaissé)
ETAL_GDD_PRECHARGE = 20.0      # forçage pré-armé JUSTE SOUS le plus bas seuil (~29) → balayage progressif


def etalement_floraison():
    """Banc « étalement de floraison » (S2) : un tapis dense de phacélies d'une
    même espèce, mais dont les lignées portent un `phenologie_florale` ÉTALÉ. Le
    moteur ouvre chaque fleur à sa propre semaine → les dates de franchissement de
    `floraison > 0.5` se RÉPARTISSENT sur plusieurs semaines (variance non nulle),
    jamais un créneau unique. Oracle : tests/bancs/test_biotique.py (en tendance :
    ≥ 3 semaines de franchissement distinctes, variance > 0 — pas de hash figé)."""
    tile, eco = build_banc_tile("ETALEMENT", "terre", ETAL_ROWS, ETAL_COLS,
                                humidite=1.4, fertilite=1.2, microbiome=0.5)
    total = ETAL_ROWS * ETAL_COLS
    k = 0
    for r in range(ETAL_ROWS):
        for c in range(ETAL_COLS):
            plante = tile.add_plant(Phacelia, r, c)
            # Stade mature d'emblée → seed-bearing (gate de maturité franchi), pour que
            # le SEUIL de forçage par lignée soit la contrainte bindante (cf. en-tête).
            plante.current_stage = len(Phacelia.growth_stages) - 1
            # Gène ÉTALÉ déterministiquement (damier de lignées) : la fraction couvre
            # [LO, HI] de bout en bout → variance de dates garantie sans RNG (philo #3).
            frac = (k + 0.5) / total
            gene = clamp_gene(ETAL_GENE_LO + (ETAL_GENE_HI - ETAL_GENE_LO) * frac)
            plante.genes = {"phenologie_florale": gene}
            plante.gdd_accum = ETAL_GDD_PRECHARGE   # forçage pré-armé (accélération)
            k += 1
    return monde([tile], {tile.tile_id: eco})


# ─────────────────────────── 5. grimpantes (D49 volet A) ──────────────────────
# Banc D'OBSERVATION de la grimpe (sprint grimpantes ⑥) — instrument pour voir au
# F5 les QUATRE voies d'accroche à côté d'un champ potager frileux. À la différence
# des bancs à seuil (qui forcent UN signe), c'est un jardin composé où la grimpe
# ÉMERGE de la géométrie sur la saison (décision A : hauteur = vraie max_z des
# segments, pas un scalaire) — Nico calibre à l'œil (hauteurs de supports, vrilles).
#
# Trois accroches sont PRÉ-ARMÉES (comme les autres bancs posent l'état « déjà
# installé ») pour être lisibles TÔT sans dérouler des semaines de croissance :
#   • un haricot pré-attaché à un TUTEUR posé (vrille_volubile → tuteur, ④) ;
#   • un jasmin PALISSÉ sur un treillis (sarmenteux : seule accroche = le geste, ④) ;
#   • un lierre COLLÉ au mur sud de la maison (crampon → MUR, espalier, ②).
# La 4ᵉ voie — grimpe sur HÔTE VIVANT (③) — est laissée ÉMERGENTE : un haricot planté
# JUSTE À CÔTÉ d'un tournesol l'enroulera quand le tournesol dépassera sa hauteur
# autoportante (35 cm), puis l'ombragera en le dépassant (étranglement émergent,
# LightField, philo #2). C'est le cœur observable du banc → non pré-armé exprès.
# Pure COMPOSITION de l'état moteur (plantes + `tile.supports` + `plant.support`) —
# AUCUNE mécanique nouvelle → golden NEUTRE (jamais monté pour smoke/full).
SOLANACEAE_SUD = [(Tomato, 2, 2), (Basil, 2, 4), (Pepper, 4, 3), (Tomato, 4, 5)]


def grimpantes():
    """Banc « grimpantes » (sprint D49 ⑥, observation F5) : les 4 voies d'accroche
    (tuteur, treillis palissé, mur maison, hôte vivant) réunies sur une tuile, plus
    un champ de Solanaceae au sud (ensoleillé/chaud). Trois accroches pré-armées, la
    grimpe sur hôte laissée émergente (haricot ↔ tournesol). Instrument d'observation,
    pas d'oracle à seuil : on REGARDE la géométrie monter/s'affaler au F5."""
    house = House()                                  # maison par défaut, centrée (600–1400)
    # Tuile principale : les 4 voies de grimpe côte à côte. Humidité haute (le
    # haricot procédural boit ; on veut de la croissance, pas un stress hydrique).
    grimpe, eco_g = build_banc_tile("GRIMPE", "terre", 8, 8,
                                    humidite=1.6, fertilite=1.2, microbiome=0.7)
    eco_g.lumiere.fill(1.0)                          # plein soleil → grimpe vers la lumière

    # (a) HÔTE VIVANT (③, émergent) : haricot JUSTE À CÔTÉ d'un tournesol. Le haricot
    # l'enroulera dès que le tournesol dépassera 35 cm — puis l'ombragera (étranglement).
    grimpe.add_plant(Sunflower, 2, 2)
    grimpe.add_plant(Bean, 2, 3)

    # (b) TUTEUR (②, pré-armé) : un haricot au pied d'un pieu, accroche déjà posée.
    bean_t = grimpe.add_plant(Bean, 5, 2)
    tuteur = Support(support_type="tuteur", x_cm=2 * 50 + 25, y_cm=5 * 50 + 25,
                     height_cm=200.0, finesse="fin")
    grimpe.supports.append(tuteur)
    bean_t.support = (tuteur, tuteur.height_cm)       # vrille_volubile → tuteur (④)

    # (c) TREILLIS PALISSÉ (④, pré-armé) : jasmin sarmenteux attaché à la main (son
    # SEUL canal d'accroche — aucune saisie automatique).
    jasmin = grimpe.add_plant(Jasmine, 5, 5)
    treillis = Support(support_type="treillis", x_cm=5 * 50 + 25, y_cm=5 * 50 + 25,
                       height_cm=180.0, finesse="surface")
    grimpe.supports.append(treillis)
    jasmin.support = (treillis, treillis.height_cm)   # palissage (④)

    # (d) MUR MAISON (②, pré-armé) : tuile plaquée contre le mur SUD (y=1400), un
    # lierre crampon en espalier. Origine choisie pour que le pied du lierre tombe
    # dans le rayon d'accroche du rectangle-empreinte (clamp du point le plus proche).
    mur_tile, eco_m = build_banc_tile("MUR_SUD", "terre", 8, 8,
                                      ox=600.0, oy=1400.0,
                                      humidite=1.4, fertilite=1.0, microbiome=0.7)
    lierre = mur_tile.add_plant(Ivy, 0, 1)            # près du mur, plein sud
    lierre.support = (MUR, house.height_cm)           # crampon → mur (espalier)

    # Champ de Solanaceae au SUD (origin_y grand) : secteur ensoleillé/chaud, frileuses
    # favorisées (ambiance du banc, pas de grimpe). Plein soleil + humidité potagère.
    sud, eco_s = build_banc_tile("POTAGER_SUD", "terre", 8, 8,
                                 ox=1000.0, oy=1600.0,
                                 humidite=1.5, fertilite=1.3, microbiome=0.7)
    eco_s.lumiere.fill(1.0)
    for cls, r, c in SOLANACEAE_SUD:
        sud.add_plant(cls, r, c)

    # Banc ISOLÉ + anti-gel (retour F5 Nico, 2026-07-04). C'est un INSTRUMENT
    # d'observation de la grimpe, pas un jardin de succession :
    #   • succession spontanée COUPÉE — sinon des pionnières lèvent de la SeedBank-sol
    #     et évincent les plantes de démo par compétition intra-plot (le jasmin (5,5)
    #     « cède la place au plus vigoureux ») ;
    #   • paillage SATURÉ — protège du gel : les gelées tardives de printemps rabattent
    #     sinon le haricot frileux au collet à répétition (28 cm → 5 cm).
    # Patron `semis_tempere`. Le froid de DÉMARRAGE (T<5 °C, sous le seuil de croissance)
    # est traité en amont par un départ MI-PRINTEMPS (`BANC_WEEK_DEPART["grimpantes"]`,
    # cf. `cmd_init`) — le paillage protège du gel mais ne réchauffe pas la croissance.
    # Microbiome tenu à 0.7 (≥ 0.6) sur les 3 tuiles : `micro_norm = 0.7/3 ≈ 0.23 >
    # HERBIVORY_LETHAL_MICRO (0.20)` désarme la bascule LÉTALE de l'herbivorie (patron
    # `infestation_ravageur`). Mitigation PARTIELLE seulement : l'hôte tournesol meurt
    # encore d'une mort‑éclair à faible densité de ravageurs → problème SYSTÉMIQUE
    # (létalité trop brutale), suivi en dette D64, hors périmètre du banc.
    for tuile, eco in ((grimpe, eco_g), (mur_tile, eco_m), (sud, eco_s)):
        eco.seed_bank.germination_candidates = lambda *a, **k: []   # banc ISOLÉ
        for stake in tuile.stakes:                                  # paillage → anti-gel
            while stake.add("paillage"):
                pass

    return monde([grimpe, mur_tile, sud],
                 {grimpe.tile_id: eco_g, mur_tile.tile_id: eco_m,
                  sud.tile_id: eco_s},
                 house=house)
