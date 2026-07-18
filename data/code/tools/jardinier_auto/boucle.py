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
from sim.engine.calendrier import saison_de

from .perception import percevoir
from .diagnostic import facteur_limitant
from .proposition import proposer
from .impasses import Impasse, GESTE_VERROUILLE, OBJECTIF_INATTEIGNABLE
from .execution import executer
from .trace import consigner, entree, entree_impasse, entree_consequence
from .tutelle import zones_cultivees, sous_tutelle
from . import comptabilite as CPT
from . import objectifs as OBJ

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
        saison = saison_de(engine.week)   # requis par la perception semiologique (⑦)
        for tile in engine.tiles:
            eco = engine._eco(tile)
            voisins = tile.plants                      # voisinage LOCAL (même tuile)
            for plant in tile.plants:
                if not sous_tutelle(plant, tile.tile_id, cultivees):
                    continue
                percept = percevoir(plant, eco, self.profil, voisins,
                                    tile.tile_id, cultivees, saison)
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

        # Comptabilité ③ — références AVANT gestes (pour diff des conséquences).
        vivantes_avant = CPT.snapshot_vivantes(engine)
        paliers_avant = (CPT.snapshot_paliers(gs, player)
                         if self.profil.credite_maitrise else {})

        # Objectifs actifs (④, §8) : snapshot AVANT gestes → biais de priorisation +
        # comptage. Liste vide (défaut opt-in) ⇒ bonus nul ⇒ comportement ①-③ intact.
        actifs = OBJ.objectifs_actifs(gs)

        plans, impasses = self._collecter(engine, cultivees)
        plans = self._appliquer_part_recoltee(plans)
        # Étape 4 — prioriser : priorité DÉCROISSANTE, puis clé de départage totale. Un
        # geste servant un objectif actif reçoit BONUS_OBJECTIF (biais, pas exclusivité :
        # le tri reste stable, les autres soins passent ensuite).
        def _prio(p):
            bonus = OBJ.BONUS_OBJECTIF if OBJ.objectifs_servis(actifs, p[4].verbe, p[3]) else 0
            return (-(p[4].priorite + bonus), p[0])
        plans.sort(key=_prio)
        # Étape 4bis — comptabilité (§4). Mode payé : écarter les gestes VERROUILLÉS
        # (→ impasses) avant de couper au budget de Vigueur. Mode libre : garantir un
        # solde non borné pour ne pas noyer le journal d'échecs par épuisement.
        verrous = []
        if self.profil.paie_vigueur:
            plans, verrous = CPT.separer_verrouilles(gs, player, plans)
            plans = self._couper_au_budget(gs, player, plans)
        else:
            CPT.assurer_solde_libre(gs, player)

        # Étape 5 — exécuter + consigner les gestes. Un geste servant un objectif porte
        # son `objectif_id` (clé de l'onglet) et, s'il RÉUSSIT, incrémente la
        # progression de tous les objectifs qu'il sert (④, §8). `resultat != "echec"` :
        # un geste tronqué (récolte graduée) a tout de même produit → il compte.
        for _cle, tile, eco, plant, plan in plans:
            cible = f"{plant.name}@{plant.position}"
            resultat = executer(gs, player, eco, plant, plan)
            servis = OBJ.objectifs_servis(actifs, plan.verbe, plant)
            oid = servis[0].id if servis else None
            consigner(gs, entree(semaine, tile.tile_id, cible, plan.facteur,
                                 plan.verbe, resultat, oid))
            if resultat != "echec":
                for o in servis:
                    if OBJ.incrementer(gs, o.id):
                        consigner(gs, entree_consequence(semaine, "objectif",
                                                         f"{o.id}:accompli"))
        # Consigner les IMPASSES (signalement — n'interrompt jamais la boucle, §7),
        # dans l'ordre stable de la clé de départage.
        for _cle, tile_id, imp in sorted(impasses, key=lambda x: x[0]):
            consigner(gs, entree_impasse(semaine, tile_id, imp.cible,
                                         imp.facteur, imp.cause))
        # Impasses de GESTE VERROUILLÉ (mode payé) — même journal, ordre stable.
        for _cle, tile, _eco, plant, plan in sorted(verrous, key=lambda p: p[0]):
            cible = f"{plant.name}@{plant.position}"
            consigner(gs, entree_impasse(semaine, tile.tile_id, cible,
                                         plan.facteur, GESTE_VERROUILLE))
        # Impasse OBJECTIF INATTEIGNABLE (④, §8) : cible absente ET sans moyen de
        # l'obtenir → signalée UNE fois (ordre stable = actifs déjà trié par id).
        for o in actifs:
            if (not OBJ.est_atteignable(gs, o)
                    and OBJ.marquer_inatteignable_signale(gs, o.id)):
                consigner(gs, entree_impasse(semaine, "-", f"{o.cible}#{o.id}",
                                             o.geste, OBJECTIF_INATTEIGNABLE))

        # Étape 6 (③) — consigner les CONSÉQUENCES du tick (§6). Déblocages/paliers
        # seulement si `credite_maitrise` (sinon on ne mute PAS la maîtrise) ; morts
        # toujours (diff des vivantes avant/après les gestes, corrèle un deraciner).
        conseq = []
        if self.profil.credite_maitrise:
            conseq += CPT.consequences_maitrise(gs, player, paliers_avant)
        conseq += CPT.consequences_morts(vivantes_avant, CPT.snapshot_vivantes(engine))
        for type_, detail in conseq:
            consigner(gs, entree_consequence(semaine, type_, detail))
