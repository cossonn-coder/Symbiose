"""
SYMBIOSE — fields/ecofields/paillage.py
Responsabilité : le champ scalaire `paillage` (profondeur/densité du mulch au sol,
∈ [0,1] par plot) et sa dynamique de tick — le LEVIER PERMACOLE central contre
l'invasion d'adventices (sprint équilibre invasion ③, D69).

Mixin de comportement d'`EcoFields` (comme couverture/hydrologie/ticks). Aucun état
propre : opère sur `self`. Le champ est POSÉ par le geste joueur `pailler`
(`sim/actions/gestes.py`, event-driven) et LU par :
  (a) la germination férale (`sim/succession`) — mulch dense = adventices étouffées ;
  (b) le vieillissement des graines enfouies (`fields/seedbank.tick_aging`) — sous
      mulch la banque locale s'épuise plus vite ;
  (c) l'évaporation (`hydrologie.tick_hydrology`) — mulch = barrière d'évaporation,
      le sol reste plus frais/humide.
Ici on ne fait QUE la dynamique propre du champ : décroissance (le mulch se décompose
/ s'incorpore) et REVERSEMENT de la part décomposée à l'humus `om_stable` (le mulch
qui disparaît nourrit le sol). La rétention d'humidité est LUE côté hydrologie (pas
un écrit ici) → un seul lecteur écrit `humidite`, pas de double comptage.

NUL partout au repos (le smoke ne paille jamais) → tous les lecteurs neutres →
golden INTACT. Déterministe, zéro RNG (philo #3). C'est un FLUX (philo #2) : on
écrit un CHAMP du milieu, jamais un bonus direct sur une plante.
"""

from __future__ import annotations

from .constants import PAILLAGE_DECAY, PAILLAGE_OM_W


class PaillageMixin:
    """Champ `paillage` + sa décroissance→humus (mixin d'`EcoFields`)."""

    def tick_paillage(self) -> None:
        """Fait DÉCROÎTRE le mulch de chaque plot (`paillage *= 1 − PAILLAGE_DECAY`)
        et reverse la part décomposée à l'humus `om_stable` (`décompo · PAILLAGE_OM_W`).

        Le mulch n'est pas éternel : il se décompose et s'incorpore semaine après
        semaine → il faut RE-pailler pour maintenir l'effet (usure de la solution
        facile, philo #1). Ce qui disparaît n'est pas perdu : il NOURRIT le sol
        (flux → contrainte → réponse, philo #2), exactement comme la litière.

        Recalcul par plot, borné par les GridField (paillage ∈ [0,1], om_stable ≤ 10).
        Champ NUL partout (repos) → `décompo = 0` → aucun écrit sur `om_stable` →
        golden INTACT tant que le joueur ne paille pas. À placer dans la boucle APRÈS
        les lecteurs qui ont besoin de la valeur du tick (germination, évaporation) —
        cf. `sim/engine/boucle.py` : la décroissance de la semaine s'applique après
        que les effets de la semaine ont été calculés."""
        p = self.paillage
        for r in range(self.rows):
            for c in range(self.cols):
                depth = p.data[r][c]
                if depth <= 0.0:
                    continue
                decompose = depth * PAILLAGE_DECAY
                p.set(r, c, depth - decompose)
                self.om_stable.add(r, c, decompose * PAILLAGE_OM_W)
