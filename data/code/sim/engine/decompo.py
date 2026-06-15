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
from .calendrier import FRUIT_NOUAISON_WEEK


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
        """Organes-fruits traçables (décompo·compost ③, absorbe D19). Donne aux
        fruits un VRAI état moteur (≠ proxy de rendu). Trois temps :
          1. Nouaison annuelle (semaine FRUIT_NOUAISON_WEEK) pour les espèces
             `fruitier` parvenues à `maturity_years` : on installe un fruit vert
             (maturité 0) à chaque site reproducteur (`organ_sites`, borné à
             MAX_ORGANS). Les fruits non récoltés de l'an passé chutent d'abord
             en litière `fruit` (on ne ré-empile pas une cohorte sur l'autre).
          2. Maturation hebdomadaire : `maturite += FRUIT_DMAT`.
          3. Chute (§2.4) : un fruit dont la maturité dépasse MATURITE_CHUTE est
             sur-mûr → tombe en litière `fruit` (déclenche la cascade fertilité).

        Le geste `manger` ciblé (sim.actions, D19) retire un fruit précis hors de
        ce pas. Déterministe : gate annuel fixe (pas de RNG), `organ_sites` itère
        en ordre trié, itération en ordre `tile.plants`. NEUTRE pour le golden
        tant qu'aucune espèce `fruitier` n'atteint `maturity_years` dans la
        fenêtre (AppleTree : maturity_years=5 > 2 ans simulés)."""
        log = []
        for plant in tile.plants:
            if not plant.is_alive:
                continue
            cls = plant.plant_class
            if not getattr(cls, "fruitier", False):
                continue
            r, c = plant.position
            # 1. Nouaison annuelle (gate âge inclus → golden NEUTRE hors maturité).
            if (week_in_year == FRUIT_NOUAISON_WEEK
                    and plant.age_years >= cls.maturity_years):
                for f in plant.fruits:          # cohorte précédente non récoltée
                    eco.deposer_litiere(r, c, "fruit", f.masse)
                sites = organ_sites(plant)
                plant.fruits = [Fruit(seg_id, 0.0, FRUIT_MASSE)
                                for seg_id, _pos in sites]
                if plant.fruits:
                    log.append(f"    🍎 Nouaison {plant.name}@{plant.position} "
                               f"→ {len(plant.fruits)} fruits")
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
