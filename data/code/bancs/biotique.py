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

from plants import Basil, AppleTree
from fields.seedbank import GrainEnAttente
from sim.seeds import PlayerSeedBank, Seed
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
