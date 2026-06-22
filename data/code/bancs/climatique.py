"""
SYMBIOSE — bancs/climatique.py
Bancs d'essai CLIMATIQUES (stress hydrique, ombre, acclimatation).

Tronçon ① : un seul banc, `secheresse_sable`, livré de bout en bout pour valider
la chaîne init→step→signe. Les bancs `acclimatation` et `ombre_dense` arrivent au
tronçon ③ (ils réutiliseront `build_banc_tile` / `force_memoire` / la maison haute).
"""
from __future__ import annotations

from plants import Basil
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
