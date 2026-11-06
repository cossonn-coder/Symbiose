"""
SYMBIOSE — sim/engine/floraison.py
Phénologie florale : met à jour l'état floral scalaire `floraison ∈ [0,1]` de
chaque plante vivante (arc pollinisation ; grappe D84/D86 corrigée par le sprint
FLORAISON & FRUCTIFICATION ①).

Modèle = FORÇAGE THERMIQUE ÉVÉNEMENTIEL (CONCEPTION_FLORAISON_FRUCTIFICATION §2 —
remplace l'ancienne DOUBLE PORTE GDD+photopériode) :
  1. FORÇAGE THERMIQUE CONTINU — un accumulateur PAR plante `gdd_accum` engrange
     chaque tick `max(0, T_locale − T_BASE_FLORAISON)` (T_locale = météo + ombre/
     ensoleillement du plot → une année chaude accumule plus vite, une plante à
     l'ombre plus lentement) ; remis à 0 au passage d'année (déterministe).
  2. ÉVÉNEMENT DE FLORAISON — au tick où `gdd_accum` FRANCHIT le seuil individuel
     `gdd_eff`, on ARME `bloom_week = week_in_year` (1×/an). La plante fleurit
     ensuite pendant `bloom_duration` semaines PUIS FANE — durée BORNÉE.
Gate de MATURITÉ en plus (réutilise `is_seed_bearing` : âge pour les fruitiers,
stade mature pour les annuelles) — une plante trop jeune ne fleurit pas.

DEUX corrections structurelles vs l'ancien modèle (D84/D86) : (1) la floraison
est un ÉVÉNEMENT de durée bornée (armé au FRANCHISSEMENT, fane après
`bloom_duration`) → plus de floraison éternelle NI de fugacité ; (2) le seuil
`bloom_forcing_gdd` BAS et par saison-cible remplace la porte photopériode
(`bloom_daylen_min/max` SUPPRIMÉE), qui créait le recouvrement nul de S34 → chaque
espèce fleurit dans SA saison (bas → printemps, haut → automne). Limite assumée
(§2.5) : les fleurisseurs de jours courts (aster, lierre) sont approximés par un
seuil ÉLEVÉ franchi en automne — mécanisme non photopériodique, résultat juste.

En fleur → `floraison` RELAXE vers 1 (montée douce) ; hors fenêtre → relaxe vers 0
(fanaison plus vive). La relaxation (et non un créneau dur) lisse l'ouverture/la
fanaison. La vue C# dessine une fleur au-delà de `floraison ≥ 0.5`.

Déterminisme (philo #3) : tout dérive de la température hebdo (météo pure) + les
seuils d'espèce + le gène-tempo (canaux de hash existants), jamais de RNG vivant.
Couches : `sim` peut lire `sim.reproduction` (is_seed_bearing) — respect de
`plants ← fields ← sim`.
"""

from __future__ import annotations
from sim.reproduction import is_seed_bearing

# Base thermique du forçage floral (°C) — esprit de T_COLD_ZERO (population.py) :
# en deçà, aucun degré-jour utile. Knob de calibrage (post-test).
T_BASE_FLORAISON = 6.0
# Vitesses de relaxation de l'intensité florale. Montée (ouverture) plus douce que
# la descente (fanaison plus vive) — knobs de calibrage (CONCEPTION §2).
FLORAISON_MONTEE   = 0.35
FLORAISON_DESCENTE = 0.50
# Décalage du seuil de forçage thermique floral par le gène `phenologie_florale`
# (sprint DÉSYNC PHÉNOLOGIE — désynchronise la floraison DANS la fenêtre d'espèce).
# Le seuil effectif est `bloom_forcing_gdd − FLORA_GENE_SHIFT·(gène − 1)`. Un gène
# > 1 abaisse le seuil → l'individu fleurit PLUS TÔT ; < 1 le relève → plus tard.
# Neutre 1.0 ⇒ aucun décalage (à SHIFT=0 comme à gène=1.0, la sim est STRICTEMENT
# identique au démarrage). L'étalement des dates ÉMERGE du pool-sol (variance à la
# levée férale + héritage) → nectar soutenu, SÉLECTION DARWINIENNE sans code dédié.
# CALIBRAGE (sprint FLORAISON & FRUCTIFICATION ①) : recalibré 200 → 20. L'ancien
# 200 était dimensionné pour des seuils GDD hauts (≥ 200) ; face aux nouveaux
# seuils BAS et par saison-cible (pommier 8, tournesol ~55), 200 rendrait un pied
# précoce (g > 1) NÉGATIF (seuil sous 0 → floraison dès S1). ~20 donne ±~2 sem à
# ±σ (σ≈0.10) tout en gardant `gdd_eff` positif partout — étalement visible.
FLORA_GENE_SHIFT   = 20.0


class FloraisonMixin:
    def _tick_floraison(self, tile, eco, week_in_year: int) -> None:
        """Met à jour `floraison`/`gdd_accum`/`bloom_week` de chaque plante vivante.

        Appelée une fois par tuile et par semaine (boucle.py), après la
        croissance. N'écrit que l'état floral (hors `_PLANT_ATTRS`)."""
        for plant in tile.plants:
            if not plant.is_alive:
                continue
            cls = plant.plant_class
            r, c = plant.position
            temp = eco.temperature.at_plot(r, c)
            # Forçage thermique : reset annuel PUIS accumulation de la semaine.
            if week_in_year == 1:
                plant.gdd_accum = 0.0
                plant.bloom_week = -1
            plant.gdd_accum += max(0.0, temp - T_BASE_FLORAISON)
            # Seuil INDIVIDUEL : le gène `phenologie_florale` (désync) DÉCALE le
            # seuil de forçage propre à l'individu (gène > 1 → seuil abaissé →
            # fleurit plus tôt). Neutre 1.0 ⇒ `gdd_eff == cls.bloom_forcing_gdd`.
            gene = plant.gene("phenologie_florale")
            gdd_eff = cls.bloom_forcing_gdd - FLORA_GENE_SHIFT * (gene - 1.0)
            # ARMEMENT (1×/an) : au FRANCHISSEMENT du seuil par une plante MÛRE, on
            # fige la semaine de floraison → événement de durée bornée.
            if (plant.bloom_week < 0 and is_seed_bearing(plant)
                    and plant.gdd_accum >= gdd_eff):
                plant.bloom_week = week_in_year
            en_fleur = (plant.bloom_week >= 0
                        and week_in_year < plant.bloom_week + cls.bloom_duration)
            cible = 1.0 if en_fleur else 0.0
            # Montée PAR ESPÈCE si l'espèce la règle (arbres, VERGER VIVANT ②), sinon
            # la commune. La fanaison reste commune.
            montee = cls.floraison_montee or FLORAISON_MONTEE
            taux = montee if cible > plant.floraison else FLORAISON_DESCENTE
            plant.floraison += (cible - plant.floraison) * taux
