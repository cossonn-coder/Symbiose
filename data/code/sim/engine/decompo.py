"""
SYMBIOSE — sim/engine/decompo.py
Litière issue du vivant (décompo·compost ②③) : squelettes post-mortem (seul
point de RETRAIT des plantes mortes), abscission d'automne des caducs, et
organes-fruits traçables (nouaison/maturation/chute).

Regroupés en `DecompoMixin` — le thème « ce que les plantes (mortes ou vivantes)
rendent au sol sous forme de litière ». Hérité par l'`Engine` (boucle.py).
Comportement identique à l'ancien engine.py.
"""

from __future__ import annotations
from plants import Fruit, organ_sites
from fields import (T_SECHE, FRAG_RATE, NECROMASS_PER_CM, ABSCISSION_FRAC,
                    FRUIT_MASSE, FRUIT_DMAT, MATURITE_CHUTE)

# Nouaison « en fin de floraison, par plante » (arc pollinisation ④ — §B.2).
# `floraison` (état floral ∈[0,1], écrit par engine._tick_floraison) monte vers 1
# pendant la fenêtre de floraison puis retombe vers 0 (fanaison). On arme la
# plante quand elle dépasse SEUIL_FLEURI (« en fleurs »), on NOUE quand elle
# repasse sous SEUIL_NOUAISON (« fleurs fanées »). Knobs de calibrage (post-test).
SEUIL_FLEURI   = 0.5
SEUIL_NOUAISON = 0.2
# Demi-saturation de la rampe douce g(pollen_recu) = pollen / (pollen + POLLEN_DEMI)
# ∈ [0,1[ (Monod) : dose faible → quelques fruits, dose forte → nouaison ≈ pleine,
# JAMAIS de plancher (0 pollen → 0 fruit). Knob de calibrage (post-test, §B.2).
POLLEN_DEMI    = 2.0


def frac_nouaison(pollen_recu: float) -> float:
    """g(pollen_recu) : fraction de sites qui nouent, rampe douce saturante
    (Monod). Sans plancher (pollen=0 → 0) → un fruitier entomophile sans
    butineur ne fait pas de fruit (pression écologique assumée, §B.2)."""
    return pollen_recu / (pollen_recu + POLLEN_DEMI)


class DecompoMixin:
    def _tick_skeletons(self, tile, eco):
        """Squelettes post-mortem (décompo·compost ②, phase B). SEUL point de retrait
        des plantes mortes. Pour chaque morte :
          1. `seche` debout : `semaines_mort += 1` ; ≥ T_SECHE → bascule `couchee` ;
          2. fragmentation : libère `bois_restant × FRAG_RATE × vitesse_locale` en
             litière `bois` au plot (vitesse = décompo locale, comme tick_decomposition) ;
          3. retrait centralisé en fin de pass : morte à bois épuisé OU non ligneuse
             (bois=0 d'emblée → retrait dès ce tick, équivalent à l'ancien filtre).
        Filet de sécurité : une plante morte NON marquée (chemin de dégât hebdo qui
        n'est jamais passé par deposer_mort) est retirée silencieusement, comme le
        faisait l'ancien filtre is_alive de la sénescence.

        Déterministe : itération en ordre `tile.plants`, fragmentation = pur calcul,
        zéro RNG. La litière déposée ici est décomposée au tick SUIVANT (cohérence
        de cascade : _tick_skeletons tourne en fin de tick, après tick_decomposition)."""
        log = []
        for plant in tile.plants:
            if plant.is_alive or not plant.morte:
                continue
            r, c = plant.position
            if plant.stade_mort == "seche":
                plant.semaines_mort += 1
                if plant.semaines_mort >= T_SECHE:
                    plant.stade_mort = "couchee"
            if plant.bois_restant > 1e-9:
                d = min(plant.bois_restant,
                        plant.bois_restant * FRAG_RATE * eco.decomp_speed(r, c))
                eco.deposer_litiere(r, c, "bois", d)
                plant.bois_restant -= d
                if d > 1e-4:
                    log.append(f"    🪵 Fragmentation +{d:.3f} bois @{plant.position} "
                               f"(reste {plant.bois_restant:.2f})")
        # Retrait : vivantes conservées ; mortes conservées TANT QU'il reste du bois.
        tile.plants = [p for p in tile.plants
                       if p.is_alive or (p.morte and p.bois_restant > 1e-9)]
        return log

    def _abscission(self, tile, eco):
        """Abscission d'automne (décompo·compost ②, phase C.1) : les caducs VIVANTS
        (deciduous, PerennialWoody) larguent leur feuillage en fin d'automne →
        litière `feuille` (∝ nécromasse-hauteur). Événement léger, borné, sans RNG.
        Appelé seulement aux ABSCISSION_WEEKS. Persistants : rien."""
        log = []
        for plant in tile.plants:
            if not plant.is_alive or not plant.plant_class.deciduous:
                continue
            r, c = plant.position
            masse = plant.current_height * NECROMASS_PER_CM * ABSCISSION_FRAC
            if masse > 0.0:
                eco.deposer_litiere(r, c, "feuille", masse)
                log.append(f"    🍂 Abscission {plant.name}@{plant.position} "
                           f"→ feuille +{masse:.3f}")
        return log

    def _tick_fruits(self, tile, eco, week_in_year):
        """Organes-fruits traçables (décompo·compost ③, absorbe D19 ; nouaison
        POLLINISÉE ④ — §B). Donne aux fruits un VRAI état moteur (≠ proxy de
        rendu). Trois temps :
          1. Nouaison EN FIN DE FLORAISON, par plante (remplace le rendez-vous
             global FRUIT_NOUAISON_WEEK) : une fruitière mûre s'arme quand sa
             `floraison` dépasse SEUIL_FLEURI puis NOUE quand sa floraison
             retombe sous SEUIL_NOUAISON (fleurs fanées). La fraction de sites
             qui nouent dépend du MODE de pollinisation : `self` court-circuite
             (frac=1, nouaison pleine sans vecteur) ; `insect` lit la dose
             `pollen_recu` des butineurs (§F), `wind` celle du panache anémophile
             (⑤, §5.3) — les deux via g() SANS plancher (0 dose → 0 fruit, §B.2).
             On pose un fruit vert
             (maturité 0) sur les `round(frac × |sites|)` premiers sites
             reproducteurs (`organ_sites`, borné MAX_ORGANS) ; `pollen_recu` est
             remis à 0 (cohorte suivante repart de zéro). Les fruits non récoltés
             de l'an passé chutent d'abord en litière `fruit`.
          2. Maturation hebdomadaire : `maturite += FRUIT_DMAT`.
          3. Chute (§2.4) : un fruit dont la maturité dépasse MATURITE_CHUTE est
             sur-mûr → tombe en litière `fruit` (déclenche la cascade fertilité).

        Le geste `manger` ciblé (sim.actions, D19) retire un fruit précis hors de
        ce pas. Déterministe : `floraison`/`pollen_recu`/`organ_sites` dérivent de
        la météo pure et des butineurs déterministes (zéro RNG), itération en
        ordre `tile.plants`. NEUTRE pour le golden tant qu'aucune espèce
        `fruitier` mûre ne fleurit dans la fenêtre (tomate : meurt w2-3 ;
        AppleTree : maturity_years=5 > 2 ans simulés → floraison nulle)."""
        log = []
        for plant in tile.plants:
            if not plant.is_alive:
                continue
            cls = plant.plant_class
            if not getattr(cls, "fruitier", False):
                continue
            r, c = plant.position
            # 1. Armement à la pleine floraison, nouaison à la fanaison (par plante).
            if plant.floraison >= SEUIL_FLEURI:
                plant.a_fleuri = True
            if (plant.a_fleuri and plant.floraison < SEUIL_NOUAISON
                    and plant.age_years >= cls.maturity_years):
                for f in plant.fruits:          # cohorte précédente non récoltée
                    eco.deposer_litiere(r, c, "fruit", f.masse)
                # Fraction nouée selon le mode (philo #2 : flux de pollinisation →
                # contrainte → fruits). `insect` lit la dose des butineurs (§F),
                # `wind` lit la dose ANÉMOPHILE déposée par le vent (⑤, §5.3) — les
                # deux via g() SANS plancher (0 dose → 0 fruit). Seule l'autogamie
                # (`self`) court-circuite (frac=1, nouaison pleine sans vecteur).
                frac = (1.0 if cls.pollination_mode == "self"
                        else frac_nouaison(plant.pollen_recu))
                sites = organ_sites(plant)
                n = round(frac * len(sites))
                plant.fruits = [Fruit(seg_id, 0.0, FRUIT_MASSE)
                                for seg_id, _pos in sites[:n]]
                plant.a_fleuri = False          # cohorte posée → ré-armée l'an prochain
                plant.pollen_recu = 0.0         # nouvelle cohorte repart de zéro (§B.1)
                if plant.fruits:
                    log.append(f"    🍎 Nouaison {plant.name}@{plant.position} "
                               f"→ {len(plant.fruits)} fruits (frac {frac:.2f})")
            # 2-3. Maturation + chute des sur-mûrs.
            if plant.fruits:
                survivors = []
                for f in plant.fruits:
                    f.maturite += FRUIT_DMAT
                    if f.maturite > MATURITE_CHUTE:
                        eco.deposer_litiere(r, c, "fruit", f.masse)
                        log.append(f"    🍂 Chute fruit (mûr {f.maturite:.2f}) "
                                   f"{plant.name}@{plant.position} → fruit +{f.masse:.3f}")
                    else:
                        survivors.append(f)
                plant.fruits = survivors
        return log
