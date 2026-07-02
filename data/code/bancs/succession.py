"""
SYMBIOSE — bancs/succession.py
Banc d'essai de SUCCESSION (dynamique de la banque-sol, tronçon ② du sprint
« bugs d'émergence »). Une famille à part : il ne s'observe pas par un signe
foliaire ni sur une seule saison, mais par la TRAJECTOIRE de composition d'un
peuplement sur ~15 ans — c'est un banc de TENDANCE, comme `pluie_thermique`
observe des couplages de champs plutôt qu'un limbe.

Il prouve le déverrouillage de S3 : sans facilitation OM, un monde pionnier
dérive en monoculture Capsella (pioneer sature, tardifs au plancher, cultivées
effacées) ; avec la facilitation OM (tronçon ②), les pionnières bâtissent l'humus
qui amorce fixatrice/graminée/competitor dans la banque et BRIDE le pioneer → la
succession bascule vers la prairie. Aucune mécanique nouvelle : pure composition
d'un monde pionnier, la bascule ÉMERGE du flux OM (philo #2). Golden NEUTRE (ce
banc n'est jamais monté pour smoke/full).

Oracle : tests/bancs/test_succession.py (tendances/bornes, pas de hash figé).
"""
from __future__ import annotations

from .base import build_banc_tile, monde

# Une tuile pionnière ASSEZ GRANDE pour un échantillon statistique stable de la
# composition (144 plots) sans exploser le coût du banc (15 ans × 52 sem). Sol de
# terre nu, fraîchement remué (disturbance haute → niche pionnière large), sol
# JEUNE (soil_memory_deep bas) : le point de départ classique d'une friche.
SUCC_ROWS = SUCC_COLS = 12
SUCC_DISTURBANCE = 0.6    # sol remué : le pioneer afflue (comme sur la carte réelle)
SUCC_FERTILITE   = 0.6    # friche modeste (école « sol modeste »)
SUCC_MICROBIOME  = 0.2    # vie microbienne de départ faible (friche)


def succession_bascule():
    """Banc « bascule pionnier → prairie » : une friche de terre nue et remuée,
    laissée à la succession spontanée (aucune plante posée — tout part de la
    banque-sol). L'oracle (tests/bancs/test_succession.py) simule ~15 ans et
    asserte EN TENDANCE : le pioneer culmine puis DÉCROÎT (ne sature pas), les
    tardifs (fixatrice + graminée + competitor) montent et dépassent le pioneer,
    et la banque-sol des tardifs se garnit. Pas de hash figé — un banc décrit un
    monde, l'oracle décide quoi observer."""
    tile, eco = build_banc_tile("SUCCESSION", "terre", SUCC_ROWS, SUCC_COLS,
                                humidite=0.9, fertilite=SUCC_FERTILITE,
                                microbiome=SUCC_MICROBIOME)
    eco.disturbance.fill(SUCC_DISTURBANCE)   # friche remuée → niche pionnière large
    eco.soil_memory_deep.fill(0.0)           # sol jeune (départ de succession)
    return monde([tile], {tile.tile_id: eco})
