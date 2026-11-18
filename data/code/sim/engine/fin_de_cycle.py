"""
SYMBIOSE — sim/engine/fin_de_cycle.py
Sénescence de FIN DE CYCLE des annuelles et bisannuelles (D139 niche thermique ③).

📖 Pédagogie — pourquoi une annuelle meurt :
  Une annuelle ne meurt pas « parce que c'est l'hiver ». Elle meurt parce qu'elle a
  fini son travail : une fois ses graines mûres, elle retire ses réserves des feuilles
  vers les graines et s'éteint (sénescence monocarpique). Un basilic semé tôt finit
  en août ; une mâche semée en septembre passe l'hiver en rosette et ne s'éteint
  qu'après ses graines du printemps. Le froid, lui, tue à part (gel, froid sans gel,
  `reponse_thermique.py`) — mais seulement les frileuses.

  Horloge PROPRE à la plante (décision T1 « le moteur ne tue pas, la plante meurt ») :
      fin = 1ʳᵉ floraison (`floraison_abs`, semaine absolue)
            + durée de floraison de l'espèce (`bloom_duration`)
            + maturation des graines (`fruit_semaines_maturation`, défaut 6 semaines)
  Au-delà, `_tick_senescence_health` (mortalite.py) décrémente la vitalité d'un cran
  par semaine. Une plante qui n'a jamais fleuri n'a pas d'horloge : pas de filet de
  vieillesse arbitraire (T1).

  Bisannuelle : sa 1ʳᵉ floraison est celle de l'an 2 (le gate de montaison la tient en
  rosette l'an 1, `croissance._bolt_bloque`) → même mécanisme, la règle « âge ≥ 2 ans
  à l'hiver » est retirée.

Pur, zéro RNG (philo #3). Couche `sim.engine`.
"""

from __future__ import annotations

from sim.reproduction import find_father, heredite, child_expression, graine_fertile

# Maturation des graines par défaut (semaines) pour une espèce sans
# `fruit_semaines_maturation` : ordre de grandeur d'une herbacée (fleur → graine
# sèche en 4-8 semaines) [conception §5, choix].
MATURATION_DEFAUT = 6

CYCLES_MONOCARPIQUES = ("annual", "biennial")


def fin_de_cycle(plant, week: int) -> bool:
    """Vrai si l'annuelle/bisannuelle a passé sa floraison ET la maturation de ses
    graines (`week` = semaine absolue du moteur)."""
    cls = plant.plant_class
    if cls.life_cycle not in CYCLES_MONOCARPIQUES or plant.floraison_abs < 0:
        return False
    maturation = cls.fruit_semaines_maturation or MATURATION_DEFAUT
    return week >= plant.floraison_abs + cls.bloom_duration + maturation


def semer_fin_de_cycle(plant, tile, eco, seed: int, week: int) -> None:
    """Pluie de graines de la plante qui s'éteint → banque-sol, AVEC ses gènes.

    Mesuré au banc (`mesures/banc_reponse_mort.py graines`) : sans ce dépôt, une
    annuelle qui finit son cycle en été ne laisse AUCUNE graine — la reproduction
    génétique (`_reproduction`) ne passe qu'en fin d'automne (s39), quand la mort
    calendaire la gardait encore en vie. On dépose donc ici, par la même voie que
    `_reproduction` (père à portée, hérédité, priming maternel) : la lignée et sa
    sélection continuent (la tolérance au froid des survivantes se transmet).
    Plus le dépôt d'ARCHÉTYPE de l'ancienne mort calendaire, à l'identique.
    Au pied de la mère (pas de dérive sous le vent ici)."""
    cls = plant.plant_class
    rate = getattr(cls, "reproduction_rate", 0.02)
    arch = getattr(cls, "archetype", None)
    if arch:
        eco.seed_bank.add(*plant.position, arch, rate)
    if rate <= 0.0 or not graine_fertile(cls):
        return
    father = find_father(plant, tile.plants, tile, eco, seed, week)
    genes, F = heredite(plant, father, seed, week)
    eco.seed_bank.add_species(*plant.position, cls, rate, genes,
                              child_expression(plant), F)
