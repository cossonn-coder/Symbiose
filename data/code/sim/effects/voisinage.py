"""
SYMBIOSE — sim/effects/voisinage.py
Index « plantes par plot » d'une tuile, construit UNE fois par passe de
perturbations (sprint FLUIDITÉ AN 2 ②) et lu par `_local_density` / `_spore_load`.

📖 Pédagogie (perf) : avant, pour CHAQUE plante testée, on reparcourait TOUTES les
plantes de la tuile pour garder celles du voisinage 1-connexe → O(N²) par tuile
(~650 plantes en an 2). Ici on range les plantes dans des « casiers » par plot
(dictionnaire), puis chaque requête ne visite que les ≤ 6 casiers voisins → O(N).
C'est la même idée qu'une table de hachage spatiale (« spatial hashing »).

Bit-identique par construction :
- on indexe TOUTES les plantes (vivantes ou non) : `is_alive` peut basculer au
  milieu de la passe (annélation létale du campagnol) → le filtre « vivante »
  reste fait par l'appelant AU MOMENT de la requête, comme avant ;
- les voisins sont rendus dans l'ORDRE de `tile.plants` (tri par rang) : la
  somme flottante de `_spore_load` additionne dans le même ordre qu'avant ;
- même voisinage (`tile.plots_within_radius(r, c, 1)`, plot central exclu).
L'index suppose que `tile.plants` et les positions ne changent pas pendant sa
vie (une passe `apply_disturbances` : aucune plante n'y naît ni ne se déplace).
"""

from __future__ import annotations


class IndexVoisinage:
    """Plantes d'une tuile rangées par plot, avec leur rang dans `tile.plants`."""

    def __init__(self, tile):
        self.tile = tile
        self.par_plot: dict[tuple, list] = {}
        for rang, p in enumerate(tile.plants):
            self.par_plot.setdefault(p.position, []).append((rang, p))
        # Voisinage 1-connexe mémoïsé par plot (plusieurs plantes partagent un plot).
        self._voisinages: dict[tuple, list] = {}

    def voisins(self, plant) -> list:
        """Plantes (vivantes ou non) du voisinage 1-connexe de `plant`, hors
        `plant` elle-même, dans l'ordre de `tile.plants`."""
        pos = plant.position
        plots = self._voisinages.get(pos)
        if plots is None:
            plots = self.tile.plots_within_radius(pos[0], pos[1], 1)
            self._voisinages[pos] = plots
        candidats = []
        for plot in plots:
            casier = self.par_plot.get(plot)
            if casier:
                candidats.extend(casier)
        candidats.sort(key=_rang)
        return [p for _, p in candidats if p is not plant]


def _rang(entree: tuple) -> int:
    return entree[0]
