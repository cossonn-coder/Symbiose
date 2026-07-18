# SYMBIOSE — tools/jardinier_auto/boucle.py
# Le CHEF D'ORCHESTRE : la boucle de décision en cinq étapes (§3), un passage par
# tick de semaine. Invoquée ENTRE deux ticks, côté APPELANT (banc, sim_server) —
# JAMAIS depuis `tick_semaine` (invariant H2) → golden intact par construction.
#
#   1. Percevoir      (perception.percevoir — plante + voisinage)
#   2. Diagnostiquer  (diagnostic.facteur_limitant — loi de Liebig)
#   3. Proposer       (proposition.proposer → Plan jouable OU Impasse §7)
#   4. Prioriser      (part_recoltee, puis tri stable, puis budget de Vigueur)
#   5. Exécuter       (execution.executer) + consigner (trace : gestes ET impasses)
#
# DÉTERMINISME (philo #3, §10) : itération sur des LISTES (engine.tiles, puis
# tile.plants), jamais sur un set ni un dict pour un tri ; tout tri final porte une
# clé de départage TOTALE `(tile_id, plant.y_cm, plant.x_cm)` — pas d'uid sur
# PlantInstance, mais les positions continues sont uniques. Zéro RNG.

from __future__ import annotations

from sim.actions.couts import cout_action
from sim import vigueur as V

from .perception import percevoir
from .diagnostic import facteur_limitant
from .proposition import proposer
from .impasses import Impasse
from .execution import executer
from .trace import consigner, entree, entree_impasse
from .tutelle import zones_cultivees, sous_tutelle

# Verbes dont la clé de coût diffère du nom (budget) : `recolter_paille` est tarifé
# comme `recolter`. Tous les autres verbes SONT des clés de `COUTS`.
_COUT_KEY = {"recolter_paille": "recolter"}


class JardinierAutomate:
    """Un automate déterministe piloté par un `ProfilAutomate`. Sans état narratif
    propre (§12) : ni Vigueur, ni sprite — c'est un « doigt », pas un être vivant.
    Le seul état porté entre ticks est la trace, qui vit dans `game_state`."""

    def __init__(self, profil):
        self.profil = profil

    def _collecter(self, engine, cultivees):
        """Étapes 1→3 : perçoit, diagnostique et propose pour chaque CULTIVÉE (tutelle
        = zones `replante`, §3/Q3). Renvoie `(plans, impasses)` :
          - plans   : `(cle_tri, tile, eco, plant, Plan)` — gestes jouables ;
          - impasses: `(cle_tri, tile_id, Impasse)` — trous de gameplay (§7)."""
        plans, impasses = [], []
        gs = engine.game_state
        for tile in engine.tiles:
            eco = engine._eco(tile)
            voisins = tile.plants                      # voisinage LOCAL (même tuile)
            for plant in tile.plants:
                if not sous_tutelle(plant, tile.tile_id, cultivees):
                    continue
                percept = percevoir(plant, eco, self.profil, voisins,
                                    tile.tile_id, cultivees)
                facteur = facteur_limitant(percept)
                if facteur is None:
                    continue
                prop = proposer(gs, plant, voisins, tile.tile_id, facteur, percept)
                cle = (tile.tile_id, plant.y_cm, plant.x_cm)
                if isinstance(prop, Impasse):
                    impasses.append((cle, tile.tile_id, prop))
                else:
                    plans.append((cle, tile, eco, plant, prop))
        return plans, impasses

    def _appliquer_part_recoltee(self, plans):
        """Slider `part_recoltee` (§4/Q5) : ne garder que `round(part×n)` des récoltes
        (ordre stable) ; le reste TOMBE (fruit non cueilli → faune/décompo). Défaut
        1.0 → tout gardé (comportement ①). N'affecte QUE les gestes `recolter`."""
        recoltes = sorted((p for p in plans if p[4].verbe == "recolter"),
                          key=lambda p: p[0])
        garde = self.profil.n_a_recolter(len(recoltes))
        a_retirer = {id(p) for p in recoltes[garde:]}
        return [p for p in plans if id(p) not in a_retirer]

    def _couper_au_budget(self, gs, player, plans):
        """Étape 4bis (mode `paie_vigueur`) : parcourt les plans TRIÉS (priorité déjà
        appliquée) et ne retient que ceux qui tiennent dans le solde de Vigueur, le
        décrémentant au fil de l'eau. Un geste trop cher est REPORTÉ (non exécuté ce
        tick) — un geste moins cher plus loin peut encore passer. En mode LIBRE, non
        appelé : tous les plans passent (le refus interne des gestes fait foi)."""
        solde = V.ensure_player(gs, player)["courante"]
        retenus = []
        for p in plans:
            verbe = p[4].verbe
            cout = cout_action(gs, player, _COUT_KEY.get(verbe, verbe), None)
            if cout <= solde:
                retenus.append(p)
                solde -= cout
        return retenus

    def jouer_tick(self, engine) -> None:
        """Un passage complet de la boucle sur l'état courant de `engine`.
        À appeler APRÈS `engine.tick_semaine()`, côté appelant."""
        gs = engine.game_state
        player = gs["current_player"]
        semaine = engine.week
        cultivees = zones_cultivees(gs, player)

        plans, impasses = self._collecter(engine, cultivees)
        plans = self._appliquer_part_recoltee(plans)
        # Étape 4 — prioriser : priorité DÉCROISSANTE, puis clé de départage totale.
        plans.sort(key=lambda p: (-p[4].priorite, p[0]))
        if self.profil.paie_vigueur:
            plans = self._couper_au_budget(gs, player, plans)

        # Étape 5 — exécuter + consigner les gestes.
        for _cle, tile, eco, plant, plan in plans:
            cible = f"{plant.name}@{plant.position}"
            resultat = executer(gs, player, eco, plant, plan)
            consigner(gs, entree(semaine, tile.tile_id, cible, plan.facteur,
                                 plan.verbe, resultat))
        # Consigner les IMPASSES (signalement — n'interrompt jamais la boucle, §7),
        # dans l'ordre stable de la clé de départage.
        for _cle, tile_id, imp in sorted(impasses, key=lambda x: x[0]):
            consigner(gs, entree_impasse(semaine, tile_id, imp.cible,
                                         imp.facteur, imp.cause))
