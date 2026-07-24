"""
SYMBIOSE — bancs/edaphique.py
Bancs d'essai ÉDAPHIQUES (stress du SOL : chlorose pH, asphyxie, carence NPK).

Tronçon ② du sprint « bancs d'essai ». Trois mondes paramétrés qui FORCENT un
stress racinaire au-delà de son seuil, chacun avec son signe foliaire observable
et son oracle (tests/bancs/test_edaphique.py). Pure composition de l'état moteur
(sol, champs éco, mémoires physiologiques) — AUCUNE mécanique nouvelle, donc
golden NEUTRE (ces fabriques ne sont jamais montées pour smoke/full, cf.
`cmd_init`).

Servent d'INSTRUMENT DE TRI pour D47 : un oracle vert + un écran muet ⇒ le bug
est dans le rendu C#, pas dans la carte ni le moteur. Ce tronçon tranche en
particulier D47-C2 (asphyxie muette malgré l'arrosage) et D47-C6 (heatmaps NPK
uniformément pauvres).
"""
from __future__ import annotations

from plants import Vaccinium, Basil, Sunflower, Tomato, Pepper, Bean
from .base import build_banc_tile, monde, force_memoire

# ───────────────────────────── 1. chlorose pH ────────────────────────────────
# pH forcé bien au-DELÀ de CHLOROSE_PH (7.6) et proche de PH_MAX (8.5) : la rampe
# de `semiologie.chlorose` est quasi saturée → signe franc dès la 1re semaine. La
# myrtille (Vaccinium, ph_opt=4.8, calcifuge strict) est l'acidophile témoin : sur
# ce sol alcalin le fer se bloque, le limbe jaunit entre les nervures.
PH_ALCALIN = 8.2


def chlorose_acidophile():
    """Banc « chlorose ferrique » : une myrtille acidophile posée sur un sol
    UNIFORMÉMENT ALCALIN (pH ≈ 8.2). Espèce calcifuge + pH > CHLOROSE_PH ⇒ le
    signe `chlorose` apparaît (et la plante reste vivante — c'est une carence
    fonctionnelle, pas une mort). Oracle : tests/bancs/test_edaphique.py."""
    tile, eco = build_banc_tile("CHLOROSE", "terre", 8, 8,
                                humidite=1.2, fertilite=1.0, microbiome=0.4,
                                ph=PH_ALCALIN)
    tile.add_plant(Vaccinium, 4, 4)
    return monde([tile], {tile.tile_id: eco})


# ───────────────────────────── 2. asphyxie ───────────────────────────────────
# Argile GORGÉE (humidité > HUM_EXCES = 2.3, l'argile RETIENT → l'excès se
# maintient) + pré-charge de `asphyxie_memory` au-delà de ASPHYXIE_HEALTH_SEUIL
# (0.10). Même logique d'accélération que la sécheresse (cf. climatique.py) : on
# pose l'engorgement DÉJÀ installé, et le sol retenant l'eau l'ENTRETIENT.
# Diagnostic D47-C2 : au F5, le signe `asphyxie` restait muet malgré arrosage
# répété — ce banc prouve que le moteur SAIT l'émettre quand l'excès est soutenu.
HUM_ARGILE_GORGEE = 2.9
ASPHYXIE_PRECHARGE = 0.5


def asphyxie_argile():
    """Banc « asphyxie racinaire » : un basilic (non hygrophile) sur argile gorgée
    d'eau. Racines en anoxie → feuillage terne, jaunissement mou : le signe
    `asphyxie` apparaît dès la 1re semaine et persiste tant que le sol reste
    engorgé. Oracle : tests/bancs/test_edaphique.py."""
    tile, eco = build_banc_tile("ASPHYXIE", "argile", 8, 8,
                                humidite=HUM_ARGILE_GORGEE, fertilite=1.0,
                                microbiome=0.3)
    plante = tile.add_plant(Basil, 4, 4)
    force_memoire(plante, "asphyxie_memory", ASPHYXIE_PRECHARGE)
    return monde([tile], {tile.tile_id: eco})


# ───────────────────────────── 3. carence NPK ────────────────────────────────
# DEUX tuiles JUMELLES (même sol, même tournesol gourmand, même humidité) ne
# différant QUE par la nutrition : CARENCE (n=p=k ≈ 0.05) vs TEMOIN (riche). La loi
# de Liebig (qi_local = min(N,P,K)/3) bride le Qi de la tuile carencée → croissance
# avortée, mesurable contre le témoin. Pas de signe de MORT ici : la mort édaphique
# chronique reste bloquée (D41, qi_local épuisé). Diagnostic D47-C6 : ce banc montre
# que « heatmaps NPK uniformément pauvres » est le symptôme NORMAL d'un sol carencé,
# pas un bug de la carte.
NPK_CARENCE = 0.05
NPK_RICHE = 2.5


def carence_npk():
    """Banc « carence NPK » : deux tournesols jumeaux, l'un sur sol épuisé
    (n=p=k≈0.05), l'autre sur sol riche (témoin). Rend la carence OBSERVABLE
    (champs n/p/k pauvres, croissance bridée par Liebig) sans tuer. Oracle :
    tests/bancs/test_edaphique.py compare la biomasse au témoin."""
    carence, eco_c = build_banc_tile("CARENCE", "terre", 8, 8,
                                     humidite=1.2, fertilite=NPK_CARENCE,
                                     microbiome=0.3)
    temoin, eco_t = build_banc_tile("TEMOIN", "terre", 8, 8, 500.0, 0.0,
                                    humidite=1.2, fertilite=NPK_RICHE,
                                    microbiome=0.3)
    carence.add_plant(Sunflower, 4, 4)
    temoin.add_plant(Sunflower, 4, 4)
    return monde([carence, temoin],
                 {carence.tile_id: eco_c, temoin.tile_id: eco_t})


# ──────────────────── 4. mémoire d'inoculum & rotation ────────────────────────
# DEUX planches JUMELLES (même sol, même humidité) qui ne diffèrent QUE par
# l'HISTOIRE culturale, pour démontrer la mémoire d'inoculum de tuile (sprint
# éponyme, §11) et la pédagogie de rotation (philo #2/#6) :
#   · MONOCULT : Solanacées répétées (tomate + poivron) sur un sol déjà VICIÉ —
#     l'inoculum `Solanaceae` est pré-chargé au-dessus du seuil molène (patron
#     `force_memoire` : on pose la mémoire édaphique DÉJÀ installée, comme après
#     plusieurs saisons de monoculture malade). Sous F5, le couplage ② amplifie
#     la maladie sur toute nouvelle Solanacée, et la porte de niche `arch_inoculum`
#     laisse la MOLÈNE coloniser la planche (indicatrice de sol vicié).
#   · ROTATION : familles ALTERNÉES (basilic Lamiaceae, tournesol Asteraceae,
#     haricot Fabaceae) sur un sol PROPRE — aucun inoculum. Rien à amplifier :
#     la maladie ne monte pas, aucune molène ne germe. C'est le témoin sain.
# Pré-charge édaphique déterministe (zéro RNG) ; ce banc n'est jamais monté pour
# smoke/full → golden NEUTRE.
INOC_VICIE = 0.7          # > INOC_MOLENE_SEUIL (0.4) : molène candidate, heatmap rouge
INFECTION_PRECHARGE = 0.6  # mémoire d'infection vécue → dépôt continu + amplification


def rotation_inoculum():
    """Banc « mémoire d'inoculum & rotation » : une planche de Solanacées répétées
    sur sol vicié (inoculum `Solanaceae` pré-chargé, maladie qui s'aggrave, molène
    qui colonise) VS une planche tournée (familles alternées, sol sain). Démontre
    §11 : la terre garde la mémoire hôte-spécifique de la maladie, tourner de
    famille y échappe. Observation F5 (pas d'oracle : phénomène temps réel)."""
    # Planche viciée — Solanacées répétées sur terre déjà malade.
    mono, eco_m = build_banc_tile("MONOCULT", "terre", 8, 8,
                                  humidite=1.6, fertilite=1.0, microbiome=0.3)
    solanacees = [(Tomato, 2, 2), (Pepper, 2, 5), (Tomato, 5, 2), (Pepper, 5, 5)]
    for espece, r, c in solanacees:
        plante = mono.add_plant(espece, r, c)
        force_memoire(plante, "infection_memory", INFECTION_PRECHARGE)
    # Sol vicié : inoculum Solanaceae au-dessus du seuil molène sur tout le lit.
    for r in range(eco_m.rows):
        for c in range(eco_m.cols):
            eco_m.inoculum.deposit(r, c, "Solanaceae", INOC_VICIE)
    # Planche tournée — familles alternées, sol propre (aucun inoculum).
    rot, eco_r = build_banc_tile("ROTATION", "terre", 8, 8, 500.0, 0.0,
                                 humidite=1.6, fertilite=1.0, microbiome=0.5)
    for espece, r, c in [(Basil, 2, 2), (Sunflower, 2, 5),
                         (Bean, 5, 2), (Basil, 5, 5)]:
        rot.add_plant(espece, r, c)
    return monde([mono, rot],
                 {mono.tile_id: eco_m, rot.tile_id: eco_r})
