"""
SYMBIOSE — bancs/climatique.py
Bancs d'essai CLIMATIQUES (stress hydrique, ombre, acclimatation).

Tronçon ① : `secheresse_sable`, livré de bout en bout pour valider la chaîne
init→step→signe. Tronçon ③ : `acclimatation` (durcissement plastique visible) et
`ombre_dense` (carence lumineuse installée). Tous réutilisent `build_banc_tile` /
`force_memoire` / la maison haute — AUCUNE mécanique nouvelle, golden NEUTRE.
"""
from __future__ import annotations

from plants import Basil
from world import House
from fields.seedbank import GrainEnAttente
from sim.seeds import semer_fondateur
from sim.actions.couvertures import VOILE_COUVERT
from .base import build_banc_tile, monde, force_memoire

# Pré-charge de `drought_memory` au-DELÀ du seuil de dégât (DROUGHT_DAMAGE_THRESHOLD
# = 0.6, cf. sim/effects/perturbations + sim/semiologie.secheresse). Pourquoi
# pré-charger plutôt que laisser le déficit s'installer « naturellement » : avec le
# seed déterministe du serveur, une pluie de fond ramène l'humidité vers la
# semaine 16 et PLAFONNE drought_memory à ~0.52 — le seuil 0.6 n'est jamais franchi.
# Le banc pose donc le stress DÉJÀ installé (accélération assumée, cf. base.py) ; le
# sable drainant + l'humidité basse le MAINTIENNENT au-dessus du seuil pendant toute
# la fenêtre d'observation. 0.8 → signe `secheresse` d'intensité ~0.5 dès la sem. 1.
DROUGHT_PRECHARGE = 0.8

# Humidité initiale du sable : assez basse pour que le `drought_stress`
# (hum < 0.5 → stress) reste actif et entretienne la mémoire pré-chargée.
HUM_SABLE_SEC = 0.1


def secheresse_sable():
    """Banc « sécheresse sur sable » : une tuile sableuse petite et sèche, un
    basilic (NON xérophile) au centre, AUCUN arrosage. Le tissu montre le signe
    `secheresse` (turgescence perdue) dès la première semaine et le garde tant que
    le sol reste sec. Oracle associé : tests/bancs/test_climatique.py."""
    tile, eco = build_banc_tile("SECHERESSE", "sable", 8, 8,
                                humidite=HUM_SABLE_SEC, fertilite=0.6,
                                microbiome=0.2)
    plante = tile.add_plant(Basil, 4, 4)
    force_memoire(plante, "drought_memory", DROUGHT_PRECHARGE)
    return monde([tile], {tile.tile_id: eco})


# ────────────────────────── 2. acclimatation (durcissement) ──────────────────
# Stress DOUX mais soutenu : un déficit hydrique SOUS le seuil de dégât
# (DROUGHT_DAMAGE_THRESHOLD = 0.6) — assez pour sur-exprimer les gènes adaptogènes
# (le tissu s'endurcit, teinte glauque), pas assez pour abîmer le limbe. C'est le
# point délicat du banc : si le stress blesse, `secheresse` (signe de DÉGÂT,
# priorité 1) masque `acclimatation` (RÉPONSE, priorité 9). On vise donc une bande
# étroite. `drought_memory` pré-chargée à 0.40 (< 0.6) + humidité de terre modérée
# qui MAINTIENT le déficit doux : la mémoire culmine ~0.48 puis redescend quand la
# pluie de fond saisonnière revient (cf. piège de calibration ①) — jamais 0.6.
HUM_DOUX = 0.30            # humidité de terre : drought_stress doux, sous le seuil
DROUGHT_DOUX = 0.40       # mémoire pré-chargée SOUS DROUGHT_DAMAGE_THRESHOLD (0.6)
# Expression plastique pré-posée pour rendre le durcissement IMMÉDIAT (sinon elle
# glisse lentement depuis 1.0 à TAU_UP=0.08/sem). 1.12 = cible stable pour une
# mémoire ~0.40 (cible = 1 + EXPR_GAIN·mémoire = 1 + 0.30·0.40 = 1.12) → la dynamique
# d'expression du tick ne la fait ni monter ni chuter : signe `acclimatation` franc
# et stable dès la 1re semaine. La sur-expression porte sur le gène apparié à
# `drought_memory` (cf. ADAPTOGENIC_GENES / _EXPR_MEMOIRE).
GENE_ACCLIM = "tolerance_secheresse"
EXPR_ACCLIM = 1.12


def acclimatation():
    """Banc « durcissement plastique » : un basilic sous déficit hydrique DOUX et
    prolongé (terre peu humide, pas d'arrosage). Le stress reste sous le seuil de
    dégât → AUCUN signe de souffrance, mais la plante sur-exprime sa tolérance à la
    sécheresse : feuillage plus coriace/glauque, signe `acclimatation` SEUL. Oracle :
    tests/bancs/test_climatique.py (signe présent ET aucun signe de dégât)."""
    tile, eco = build_banc_tile("ACCLIM", "terre", 8, 8,
                                humidite=HUM_DOUX, fertilite=0.8, microbiome=0.2)
    plante = tile.add_plant(Basil, 4, 4)
    force_memoire(plante, "drought_memory", DROUGHT_DOUX)
    plante.expression[GENE_ACCLIM] = EXPR_ACCLIM
    return monde([tile], {tile.tile_id: eco})


# ─────────────────────────────── 3. ombre dense ──────────────────────────────
# Banc ISOLÉ (décision « mixte ») : une ombre installée dense étouffe toute la
# végétation autour, impossible à mêler aux autres bancs sans tout fausser. Une
# maison HAUTE et PROCHE projette une ombre INSTALLÉE (pas un nuage passager) sur
# une tuile collée à son flanc NORD ; sous cette ombre la lumière plafonne au
# plancher diffus (~0.15) → `shade_memory` converge vers ~0.85, bien au-delà de
# SHADE_DAMAGE_THRESHOLD (0.6) → le tissu s'étiole, signe `ombre`.
# Géométrie : maison height 1500 cm (ombre longue et profonde), centrée en x sur la
# tuile (largeur 800 couvre les 400 cm de la tuile) ; tuile posée au nord (oy=350,
# y croissant vers le SUD → nord = petit y), juste dans la bande d'ombre de midi.
HOUSE_OMBRE = House(center_x_cm=200.0, center_y_cm=1000.0,
                    width_cm=800.0, depth_cm=800.0, height_cm=1500.0)
TILE_OY_NORD = 350.0      # origine y de la tuile au flanc nord (dans l'ombre projetée)
# La convergence naturelle de shade_memory vers 0.85 est LENTE (lerp 0.10/sem →
# ~12 sem pour franchir 0.6). Accélération sanctionnée (cf. base.py) : on pré-charge
# au-dessus du seuil, l'ombre maintenue (light ≈ 0.15) garde la mémoire là sans la
# laisser retomber. 0.80 → signe `ombre` d'intensité ~0.5 dès la 1re semaine.
SHADE_PRECHARGE = 0.80


def ombre_dense():
    """Banc « carence lumineuse » : un basilic (héliophile) sous l'ombre INSTALLÉE
    d'une maison haute collée à son flanc nord. Lumière au plancher → `shade_memory`
    au-delà du seuil de dégât → le feuillage pâlit/file, signe `ombre`. Oracle :
    tests/bancs/test_climatique.py.

    ⚠️ RENDU C# MANQUANT (dette 0.5.2) : le moteur ÉMET `ombre` mais `PlantRenderer`
    n'a pas encore son mapping couleur/texture. Au F5 ce banc est donc MUET à l'écran
    alors que l'oracle est vert — c'est précisément le cas-école du tri D47 (bug
    RENDU, pas carte). Rappel au bilan ⑤ (lever la dette 0.5.2)."""
    tile, eco = build_banc_tile("OMBRE", "terre", 8, 8, 0.0, TILE_OY_NORD,
                                humidite=1.2, fertilite=1.0, microbiome=0.4)
    plante = tile.add_plant(Basil, 4, 4)
    force_memoire(plante, "shade_memory", SHADE_PRECHARGE)
    return monde([tile], {tile.tile_id: eco}, house=HOUSE_OMBRE)


# ─────────────────────── 4. pluie thermique (couplage amont, ①) ───────────────
# Banc-SONDE du correctif amont du sprint germination thermique ① : prouver la
# chaîne pluie → air → sol. Avant le correctif, `temperature_delta` rendait 0.0
# pour `Pluie prolongée`/`Orage` → une averse laissait l'air aussi chaud (trou). On
# a alimenté `TEMP_DELTA_BASE` d'un delta froid ; ce banc l'OBSERVE. À la différence
# des bancs foliaires (signes lus par la vue), celui-ci s'observe par les CHAMPS
# (T_air, T_sol, humidité) : son oracle lit `eco.temperature`/`temperature_sol`/
# `humidite`, pas `leaf_symptoms`. Aucune mécanique nouvelle — il COMPOSE un monde et
# laisse la météo SEEDÉE du serveur (déterministe) faire tomber l'averse ; l'oracle
# trace la fenêtre où le seed pose une `Pluie prolongée` (cf. tests/bancs).
# Humidité de terre MODÉRÉE : assez basse pour que la pluie de fond saisonnière ne
# sature pas (le freinage de la baisse sous averse reste visible), assez haute pour un
# microclimat réaliste. Un basilic au centre = sujet présent (cohérence visuelle F5) ;
# l'observation porte sur le SOL, pas sur son feuillage.
HUM_PLUIE = 0.6


def pluie_thermique():
    """Banc « couplage pluie → air → sol » : une tuile de terre sous le climat
    seedé du serveur, observée à travers la fenêtre où tombe une averse-état
    (`Pluie prolongée`). Le delta froid amont (correctif ①) refroidit l'air ; le
    sol suit (inertie). L'oracle (tests/bancs/test_climatique.py) asserte le SENS
    des couplages : T_air plus bas sous averse, T_sol qui baisse, baisse d'humidité
    FREINÉE par l'apport d'eau. Tendances/bornes, pas d'égalité fragile."""
    tile, eco = build_banc_tile("PLUIE", "terre", 8, 8,
                                humidite=HUM_PLUIE, fertilite=0.8, microbiome=0.2)
    tile.add_plant(Basil, 4, 4)
    return monde([tile], {tile.tile_id: eco})


# ─────────────── 5. germination multifacteur (banc de CALIBRAGE, ⑥) ────────────
# BANC-SONDE de calibrage des portes de germination (sprint germination thermique).
# À la différence des bancs foliaires (un signe à observer) ou de `semis_tempere`
# (qui ISOLE pour répondre oui/non), celui-ci BALAYE un facteur à la fois, toutes
# choses égales par ailleurs, sur un PEUPLEMENT (12×12 plots tous ensemencés) →
# le TAUX DE LEVÉE par tuile devient un proxy statistique stable de la porte de
# niche (qui embarque la cloche thermique ②③④ et la cloche pH ⑤). Sert à régler
# `t_germ_opt/tol`, `T_GERM_FLOOR`, `GERM_GENE_SHIFT` et les pentes pH/lumière.
#
# Couple FRILEUSE × RUSTIQUE pour exhiber la sélectivité thermique : la tomate
# (Solanaceae, t_germ_opt 22 / tol 7, étroite) lève tard et peu au frais ; la
# carotte (Apiaceae rustique, opt 13 / tol 10) lève dès le sol frais. À T_sol
# intermédiaire, la rustique DOIT devancer la frileuse — c'est le cœur de l'oracle.
#
# ⚠️ FENÊTRE D'OBSERVATION = 1 TICK. T_sol forcée à l'init RELAXE vers l'équilibre
# air-piloté (THERMAL_INERTIA 0.5 → ~6 sem pour converger, cf. `tick_thermique`) :
# le gradient n'est NET qu'au 1er tick, avant que la thermique ne le gomme. La
# lumière, elle, est ENTIÈREMENT RECALCULÉE par `tick_light` chaque tick → un
# forçage de `eco.lumiere` est écrasé : la sensibilité lumière n'est donc PAS
# balayée par l'engine ici, l'oracle l'asserte par LECTURE DIRECTE de la porte de
# niche (pure, cf. `seed_bank.niche_index` — « cohérent avec les portes
# existantes »). pH et T_sol passent par l'engine (1 tick), pH étant chimie lente
# non recalculée. Toujours pure composition de l'état moteur → golden NEUTRE.
GMF_ROWS = GMF_COLS = 12      # 144 plots/tuile : échantillon statistique du taux de levée
GMF_FRILEUSE = "tomate"      # Solanaceae : t_germ_opt 22 / tol 7 (étroite, lève tard/chaud)
GMF_RUSTIQUE = "carotte"     # Apiaceae rustique : opt 13 / tol 10 (lève au sol frais)
GMF_T_SWEEP  = [0.0, 5.0, 8.0, 11.0, 14.0, 18.0, 22.0, 26.0, 30.0]   # °C de T_sol forcée
GMF_PH_SWEEP = [4.0, 5.0, 6.0, 6.8, 7.5, 8.5]                        # pH forcé (opt espèce 6.8)
GMF_PH_T     = 18.0          # T_sol confortable pour le balayage pH (isole le facteur pH)


def _gmf_tile(label: str, espece: str, *, temperature_sol: float, ph: float,
              ox: float):
    """Une tuile de banc multifacteur : niche OUVERTE (pleine lumière, sol remué,
    sol jeune), succession férale COUPÉE (seuls les grains plantés lèvent), et un
    grain de `espece` DÉPOSÉ sur CHAQUE plot. Le facteur balayé (`temperature_sol`
    ou `ph`) est forcé uniformément ; tout le reste est tenu identique d'une tuile
    à l'autre (toutes choses égales par ailleurs). `label` encode facteur+valeur+
    espèce pour que l'oracle retrouve la tuile par son `tile_id`."""
    tile, eco = build_banc_tile(label, "terre", GMF_ROWS, GMF_COLS, ox, 0.0,
                                humidite=1.0, fertilite=0.8, microbiome=0.2,
                                temperature_sol=temperature_sol, ph=ph)
    eco.lumiere.fill(1.0)            # pleine lumière (sera recalculée par tick_light)
    eco.disturbance.fill(1.0)        # sol fraîchement remué → niche pionnière large
    eco.soil_memory_deep.fill(0.0)   # sol jeune → pas de frein de maturité
    eco.seed_bank.germination_candidates = lambda *a, **k: []   # ISOLE : zéro adventice
    for r in range(GMF_ROWS):
        for c in range(GMF_COLS):
            tile.grains_en_attente.setdefault((r, c), []).append(
                GrainEnAttente(species=espece, cultive=False, player="joueur_1"))
    return tile, eco


# ─────────────── 6. effondrement (banc F5 du composé catastrophe, ④) ───────────
# BANC D'OBSERVATION F5 du sprint effondrement météo (tronçon ④). À la différence
# des bancs foliaires (un signe à lire) ou de calibrage (un facteur balayé), celui-ci
# met en scène le SCÉNARIO complet du collapse pour que Nico VOIE, à l'écran, la
# chaîne des trois tronçons : l'encart « état du ciel » VIRE AU PLOMB à l'approche
# (convergence ②), puis la ZONE ABRITÉE survit pendant que l'EXPOSÉE est frappée
# (impact hétérogène ① + couvertures ③). Le collapse est celui, DÉTERMINISTE, de
# `seed 12345` : la Grêle sévère (i≈1.94) tombe SEMAINE 1310 (an 26, s10) et son
# `scope="local"` la confine à un PATCH de la tuile (tronçon ①). Ce banc DOIT donc
# tourner avec ce seed (BANC_SEED) et démarre juste avant (BANC_WEEK_DEPART), pour
# que les quelques pas de simulation traversent la fenêtre de convergence (le ciel
# s'assombrit aux semaines 1307-1309) avant la frappe.
#
# Hétérogénéité mise en scène : une tuile 16×11 entièrement SEMÉE de basilics
# fondateurs (`semer_fondateur` → tissu tendre déjà segmenté, donc DESSINÉ, et
# fragile face à la grêle, comme dans tests/test_couvertures) ; la MOITIÉ GAUCHE
# (colonnes < 6) est ABRITÉE sous un VOILE d'hivernage posé (`couvert_pose`,
# tronçon ③) — la vue y dessine le placeholder de voile ET la grêle médiée y est
# amortie ; la moitié droite reste NUE. Le patch de grêle (seed 12345, semaine 1310)
# STRADDLE les deux moitiés → là où il recouvre le voile la plante tient, là où il
# frappe la terre nue elle est fauchée : « l'exposé flanche, l'abrité tient et
# re-sème ». Bien ARROSÉE (humidite=1.5) pour que la sécheresse/le froid ne
# CONFONDENT pas le signal grêle (le seul stress discriminant reste la grêle × voile).
# AUCUNE mécanique nouvelle (compose l'état moteur + pose une couverture par la
# façade éco) → golden NEUTRE (jamais monté pour smoke/full ; le golden tourne hors
# serveur). ⚠️ CALIBRAGE F5 : la fenêtre départ (BANC_WEEK_DEPART=1309) est un
# compromis — assez tôt pour que le ciel soit déjà lourd à l'arrivée (convergence
# 1.94), assez tard pour que les semis n'aient pas durci avant la frappe (chaque
# tick de croissance les rend plus résistants → le contraste mort/vif se dilue).
# Reculer le départ montre le ciel VIRER (clair→plomb) mais adoucit la fauche ;
# Nico ajuste au F5.
EFF_ROWS, EFF_COLS = 16, 11
EFF_ABRI_COLS = 6         # colonnes 0..5 sous voile (moitié gauche abritée)
EFF_FOUNDER_SEED = 42     # graine des gènes fondateurs (déterministe)


def effondrement():
    """Banc « l'hiver de tous les dangers » (effondrement météo ④) : une tuile 16×11
    de basilics fondateurs, moitié gauche ABRITÉE sous voile, moitié droite NUE, sous
    le collapse déterministe du seed 12345 (Grêle locale sévère semaine 1310). À
    l'écran : l'encart du ciel est déjà au plomb à l'arrivée (convergence ②) et le
    reste, puis la zone voilée garde un noyau vivant là où la nue est fauchée (impact
    hétérogène ① + couvertures ③). Banc F5 (pas d'oracle dédié : la MÉCANIQUE est
    couverte par tests/test_meteo_heterogene + test_couvertures ; ici on COMPOSE le
    décor observable). DOIT tourner avec seed 12345 (BANC_SEED) ; démarre semaine 1309
    (BANC_WEEK_DEPART) — deux pas avant la frappe, ciel déjà lourd."""
    tile, eco = build_banc_tile("EFFONDREMENT", "terre", EFF_ROWS, EFF_COLS,
                                humidite=1.5, fertilite=1.0, microbiome=0.3)
    for r in range(EFF_ROWS):
        for c in range(EFF_COLS):
            semer_fondateur(tile, Basil, r, c, EFF_FOUNDER_SEED)
            if c < EFF_ABRI_COLS:                       # moitié gauche : voile posé
                eco.poser_couvert(r, c, VOILE_COUVERT, 0.0)
    return monde([tile], {tile.tile_id: eco})


def germination_multifacteur():
    """Banc « calibrage de germination » (sprint germination thermique ⑥) : un
    DAMIER de tuiles identiques sauf UN facteur balayé. Deux balayages :
      • T_sol ∈ GMF_T_SWEEP × {tomate frileuse, carotte rustique} ;
      • pH ∈ GMF_PH_SWEEP × {carotte} (à T_sol confortable).
    Chaque tuile porte 144 grains ; l'oracle (tests/bancs/test_climatique.py) lit le
    TAUX DE LEVÉE par tuile au 1er tick et asserte le SENS des réponses (croît avec
    T_sol jusqu'à l'optimum puis décroît, nul sous T_GERM_FLOOR, frileuse < rustique
    au frais, cloche pH). NE modifie RIEN au moteur — golden NEUTRE."""
    tiles, ecos, ox = [], {}, 0.0
    for t in GMF_T_SWEEP:
        for espece in (GMF_FRILEUSE, GMF_RUSTIQUE):
            tile, eco = _gmf_tile(f"GMF_T_{t:g}_{espece}", espece,
                                  temperature_sol=t, ph=6.8, ox=ox)
            tiles.append(tile); ecos[tile.tile_id] = eco
            ox += 800.0          # tuiles bien séparées (aucun ombrage inter-tuile)
    for ph in GMF_PH_SWEEP:
        tile, eco = _gmf_tile(f"GMF_PH_{ph:g}_{GMF_RUSTIQUE}", GMF_RUSTIQUE,
                              temperature_sol=GMF_PH_T, ph=ph, ox=ox)
        tiles.append(tile); ecos[tile.tile_id] = eco
        ox += 800.0
    return monde(tiles, ecos)
