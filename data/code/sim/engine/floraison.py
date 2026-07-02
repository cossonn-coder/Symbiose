"""
SYMBIOSE — sim/engine/floraison.py
Phénologie florale : met à jour l'état floral scalaire `floraison ∈ [0,1]` de
chaque plante vivante (arc pollinisation, tronçon ① — CONCEPTION_POLLINISATION §A).

Modèle = DOUBLE PORTE, calque du couple `phenology`/`warmth` des guildes
(fields/population.py) :
  1. FORÇAGE THERMIQUE (GDD) — « la plante est prête » : un accumulateur PAR
     plante `gdd_accum` engrange chaque tick `max(0, T − T_BASE_FLORAISON)` ;
     remis à 0 au passage d'année (déterministe). Porte franchie quand
     `gdd_accum ≥ gdd_floraison(espèce)`.
  2. PHOTOPÉRIODE — « c'est la saison » : `daylength(wiy)` dans la fenêtre
     `[bloom_daylen_min, bloom_daylen_max]` de l'espèce (réutilise `daylength`,
     pure → déterministe).
Gate de MATURITÉ en plus (réutilise `is_seed_bearing` : âge pour les fruitiers,
stade mature pour les annuelles) — une plante trop jeune ne fleurit pas.

Les deux portes ouvertes + mature → `floraison` RELAXE vers 1 ; une porte qui
retombe (jour trop court, fin de chaleur, plante non mature) → relaxe vers 0. La
relaxation (et non un créneau dur) lisse l'ouverture/la fanaison.

GOLDEN NEUTRE (tronçon ①) : ce pas n'écrit QUE `floraison`/`gdd_accum` (hors
`_PLANT_ATTRS` du golden) et N'ÉMET AUCUN LOG (le LOG complet est haché). B/C/F
brancheront la lecture de `floraison` aux tronçons suivants. Déterminisme (philo
#3) : tout dérive de la température hebdo (météo pure) + `daylength` + les seuils
d'espèce, jamais de RNG vivant.

Couches : `sim` peut lire `fields` (daylength) et `sim.reproduction`
(is_seed_bearing) — respect de `plants ← fields ← sim`.
"""

from __future__ import annotations
from fields import daylength
from sim.reproduction import is_seed_bearing

# Base thermique du forçage floral (°C) — esprit de T_COLD_ZERO (population.py) :
# en deçà, aucun degré-jour utile. Knob de calibrage (post-test).
T_BASE_FLORAISON = 6.0
# Vitesses de relaxation de l'intensité florale. Montée (ouverture) plus douce que
# la descente (fanaison plus vive) — knobs de calibrage (CONCEPTION §A.3).
FLORAISON_MONTEE   = 0.35
FLORAISON_DESCENTE = 0.50
# Décalage du seuil de forçage thermique floral par le gène `phenologie_florale`
# (sprint bugs d'émergence ③, S2 — désynchronise la floraison). Miroir EXACT de
# `GERM_GENE_SHIFT` (germination) mais sur la porte FLORALE : le seuil effectif de
# GDD floral est `gdd_floraison − FLORA_GENE_SHIFT·(gène − 1)`. Un gène > 1 abaisse
# le seuil → l'individu fleurit PLUS TÔT ; < 1 le relève → plus tard. Neutre 1.0 ⇒
# aucun décalage (à SHIFT=0 comme à gène=1.0, la sim est STRICTEMENT identique au
# démarrage — seule la clé s'ajoute au vecteur sérialisé). L'étalement des dates
# ÉMERGE ensuite du pool-sol (variance à la levée férale + héritage) → nectar
# soutenu, SÉLECTION DARWINIENNE sans code dédié. Déterministe (philo #3) : le gène
# est tiré/hérité par des canaux de hash existants, pas de RNG vivant. PLACEHOLDER
# de calibrage (analogue GERM_GENE_SHIFT=3.5, ici en unités de GDD).
FLORA_GENE_SHIFT   = 40.0


class FloraisonMixin:
    def _tick_floraison(self, tile, eco, week_in_year: int) -> None:
        """Met à jour `floraison`/`gdd_accum` de chaque plante vivante (§A).

        N'émet aucun log et n'écrit que l'état floral → golden NEUTRE. Appelée
        une fois par tuile et par semaine (boucle.py), après la croissance."""
        jour = daylength(week_in_year)
        for plant in tile.plants:
            if not plant.is_alive:
                continue
            cls = plant.plant_class
            r, c = plant.position
            temp = eco.temperature.at_plot(r, c)
            # Forçage thermique : reset annuel PUIS accumulation de la semaine.
            if week_in_year == 1:
                plant.gdd_accum = 0.0
            plant.gdd_accum += max(0.0, temp - T_BASE_FLORAISON)
            # Double porte + maturité. Gène `phenologie_florale` (③) : DÉCALE le
            # seuil de forçage floral PROPRE à l'individu (gène > 1 → seuil abaissé
            # → fleurit plus tôt). Neutre 1.0 ⇒ `gdd_eff == cls.gdd_floraison`
            # (miroir exact de `germination_thermique` en succession).
            gene = plant.gene("phenologie_florale")
            gdd_eff = cls.gdd_floraison - FLORA_GENE_SHIFT * (gene - 1.0)
            porte_chaleur = plant.gdd_accum >= gdd_eff
            porte_jour    = cls.bloom_daylen_min <= jour <= cls.bloom_daylen_max
            cible = 1.0 if (porte_chaleur and porte_jour
                            and is_seed_bearing(plant)) else 0.0
            taux = FLORAISON_MONTEE if cible > plant.floraison else FLORAISON_DESCENTE
            plant.floraison += (cible - plant.floraison) * taux
