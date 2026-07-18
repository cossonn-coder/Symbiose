# SYMBIOSE — tools/jardinier_auto/boucle.py
# Le CHEF D'ORCHESTRE : la boucle de décision en cinq étapes (§3), un passage par
# tick de semaine. Invoquée ENTRE deux ticks, côté APPELANT (banc, sim_server) —
# JAMAIS depuis `tick_semaine` (invariant H2) → golden intact par construction.
#
#   1. Percevoir   (perception.percevoir)
#   2. Diagnostiquer (diagnostic.facteur_limitant)
#   3. Proposer    (regles.regle_pour)
#   4. Prioriser   (tri stable — priorité puis clé de départage totale)
#   5. Exécuter    (execution.executer) + consigner (trace)
#
# DÉTERMINISME (philo #3, §10) : itération sur des LISTES (engine.tiles, puis
# tile.plants), jamais sur un set ni un dict ; le tri final porte une clé de
# départage TOTALE `(tile_id, plant.y_cm, plant.x_cm)` — pas d'uid sur
# PlantInstance, mais les positions continues sont uniques. Zéro RNG.

from __future__ import annotations

from .perception import percevoir
from .diagnostic import facteur_limitant
from .regles import regle_pour
from .execution import executer
from .trace import consigner, entree


def sous_tutelle(plant) -> bool:
    """La plante est-elle prise en charge par l'automate ?

    Cible visée (Q3) = les plantes CULTIVÉES. Mais après lecture du moteur
    (2026-07-18), il n'existe AUCUN attribut `cultive` sur `PlantInstance` : la
    distinction cultivé/féral vit dans le dict de détection de maîtrise, comme un
    ensemble de ZONES `(tile_id, r, c)` (`maitrise_detection.marquer_replante`),
    pas un champ de plante. Le kickoff ① interdit d'inventer un attribut → on se
    RABAT sur « toutes les plantes vivantes », signalé dans 00_etat.md comme point
    à durcir au ② (croiser avec le set `replante` par plot-foyer)."""
    return plant.is_alive


class JardinierAutomate:
    """Un automate déterministe piloté par un `ProfilAutomate`. Sans état narratif
    propre (§12) : ni Vigueur, ni sprite — c'est un « doigt », pas un être vivant.
    Le seul état porté entre ticks est la trace, qui vit dans `game_state`."""

    def __init__(self, profil):
        self.profil = profil

    def _candidats(self, engine) -> list:
        """Étapes 1→3 : parcourt le monde (listes → déterministe), perçoit,
        diagnostique et propose un geste pour chaque plante sous tutelle. Renvoie
        des tuples enrichis d'une clé de tri stable pour l'étape 4."""
        candidats = []
        for tile in engine.tiles:
            eco = engine._eco(tile)
            for plant in tile.plants:
                if not sous_tutelle(plant):
                    continue
                facteur = facteur_limitant(percevoir(plant, eco, self.profil))
                if facteur is None:
                    continue
                regle = regle_pour(facteur)
                if regle is None:
                    continue                      # impasse (câblée au ②)
                cle_tri = (tile.tile_id, plant.y_cm, plant.x_cm)
                candidats.append((regle.priorite, cle_tri, tile, eco, plant,
                                  facteur, regle))
        return candidats

    def jouer_tick(self, engine) -> None:
        """Un passage complet de la boucle sur l'état courant de `engine`.
        À appeler APRÈS `engine.tick_semaine()`, côté appelant."""
        gs = engine.game_state
        player = gs["current_player"]
        semaine = engine.week

        candidats = self._candidats(engine)
        # Étape 4 — prioriser : priorité DÉCROISSANTE, puis clé de départage totale
        # et stable (déterminisme). `sort` de Python est stable, mais la clé rend
        # l'ordre total → indépendant de l'ordre d'apparition.
        candidats.sort(key=lambda x: (-x[0], x[1]))

        # Étape 5 — exécuter + consigner.
        for _prio, _cle, tile, eco, plant, facteur, regle in candidats:
            cible = f"{plant.name}@{plant.position}"
            resultat = executer(gs, player, eco, plant, regle)
            consigner(gs, entree(semaine, tile.tile_id, cible, facteur,
                                 regle.verbe, resultat))
