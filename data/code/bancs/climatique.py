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
