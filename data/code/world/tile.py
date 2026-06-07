"""
SYMBIOSE — world/tile.py
Tuile de jeu : géométrie de la grille hexagonale, tiges et rondelles,
plantes, détection des conflits spatiaux.
"""

from __future__ import annotations
from dataclasses import dataclass, field

from plants.base import PlantInstance, ConflictNotification

# ---------------------------------------------------------------------------
# TIGES ET RONDELLES
# ---------------------------------------------------------------------------

RONDELLE_TYPES = frozenset(["fertilite", "humidite", "lombric", "maladie", "pollinisateur", "paillage", "auxiliaire"])

@dataclass
class StakeSlot:
    slot_id: int                                              # 0–9
    rondelles: list[str] = field(default_factory=list)       # max 3 rondelles du même type

    @property
    def variable(self) -> str | None:
        """Type de rondelle sur cette tige (toutes identiques)."""
        return self.rondelles[0] if self.rondelles else None

    @property
    def count(self) -> int:
        return len(self.rondelles)

    @property
    def is_bonus(self) -> bool:
        """Bonus homogène : 3 rondelles identiques."""
        return self.count == 3

    def add(self, rondelle_type: str) -> bool:
        """
        Ajoute une rondelle. Refuse si plein ou si type différent.
        Retourne True si réussi.
        """
        if rondelle_type not in RONDELLE_TYPES:
            raise ValueError(f"Type inconnu : {rondelle_type}")
        if self.count >= 3:
            return False
        if self.rondelles and self.rondelles[0] != rondelle_type:
            return False  # types mixtes interdits
        self.rondelles.append(rondelle_type)
        return True

    def remove_top(self) -> str | None:
        """Retire la rondelle du dessus. Retourne son type ou None."""
        return self.rondelles.pop() if self.rondelles else None

    def __repr__(self) -> str:
        return f"Tige#{self.slot_id} [{self.variable or '—'} ×{self.count}]"

# ---------------------------------------------------------------------------
# TUILE
# ---------------------------------------------------------------------------

@dataclass
class Tile:
    tile_id: str
    soil_type: str                                             # "terre","argile","sable","roche"
    grid_rows: int = 6
    grid_cols: int = 8                                         # 48 plots en quinconce
    # Offset monde (sprint maison, tronçon 1) : position du plot (0,0) de cette
    # tuile dans le repère monde, en cm. origin_x_cm ↔ col (est-ouest, x),
    # origin_y_cm ↔ row (nord-sud, y). INERTE ce tronçon (stocké, jamais lu par le
    # moteur) : il situe la tuile vs la maison pour l'injection d'ombre du tronçon 2.
    origin_x_cm: float = 0.0
    origin_y_cm: float = 0.0
    plants: list[PlantInstance] = field(default_factory=list)
    stakes: list[StakeSlot] = field(
        default_factory=lambda: [StakeSlot(i) for i in range(10)]
    )
    conflicts: list[ConflictNotification] = field(default_factory=list)

    # --- Accès aux rondelles ---

    def get_rondelle_count(self, variable: str) -> int:
        """Total de rondelles d'un type sur toutes les tiges."""
        return sum(s.count for s in self.stakes if s.variable == variable)

    def get_bonus_variables(self) -> list[str]:
        """Variables avec 3 rondelles identiques (bonus homogène actif)."""
        return [s.variable for s in self.stakes if s.is_bonus and s.variable]

    # --- Géométrie de la grille ---

    def is_valid_plot(self, row: int, col: int) -> bool:
        return 0 <= row < self.grid_rows and 0 <= col < self.grid_cols

    def neighbors(self, row: int, col: int) -> list[tuple]:
        """
        6 voisins hexagonaux (grille quinconce).
        La parité de la ligne détermine le décalage horizontal.
        """
        if row % 2 == 0:
            deltas = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
        else:
            deltas = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
        return [
            (row + dr, col + dc)
            for dr, dc in deltas
            if self.is_valid_plot(row + dr, col + dc)
        ]

    def plots_within_radius(self, row: int, col: int, radius: int) -> list[tuple]:
        """
        Retourne tous les plots dans un rayon donné (BFS sur les voisins).
        """
        visited = set()
        frontier = {(row, col)}
        for _ in range(radius):
            next_frontier = set()
            for r, c in frontier:
                for nb in self.neighbors(r, c):
                    if nb not in visited:
                        next_frontier.add(nb)
            visited |= frontier
            frontier = next_frontier
        visited |= frontier
        visited.discard((row, col))  # exclut le plot central
        return list(visited)

    # --- Plantes ---

    def plants_at(self, row: int, col: int, layer: str = "both") -> list[PlantInstance]:
        """
        Plantes dont le footprint inclut le plot (row, col).
        layer : "foliar", "root" ou "both"
        """
        result = []
        for p in self.plants:
            if not p.is_alive:
                continue
            if layer in ("foliar", "both") and (row, col) in p.foliar_plots:
                result.append(p)
            elif layer == "root" and (row, col) in p.root_plots:
                result.append(p)
        return result

    def add_plant(self, plant_class: type, row: int, col: int) -> PlantInstance | None:
        """
        Plante une espèce sur ce plot.
        Retourne l'instance créée, ou None si le plot est invalide.
        """
        if not self.is_valid_plot(row, col):
            return None
        instance = PlantInstance(plant_class=plant_class, position=(row, col))
        self.plants.append(instance)
        return instance

    def remove_plant(self, instance: PlantInstance) -> None:
        """Retire une plante de la tuile (ex: mort, compost)."""
        if instance in self.plants:
            self.plants.remove(instance)

    # --- Conflits ---

    def detect_conflicts(self) -> list[ConflictNotification]:
        """
        Détecte les nouveaux conflits spatiaux sur la tuile.
        Un conflit = plusieurs plantes vivantes qui partagent un plot
        dans la même couche (foliar ou root), et pas encore signalé.
        """
        new_conflicts = []
        alive = [p for p in self.plants if p.is_alive]

        for layer, get_plots in [("foliar", lambda p: p.foliar_plots),
                                   ("root", lambda p: p.root_plots)]:
            # Index : plot → liste de plantes qui l'occupent
            plot_map: dict[tuple, list[PlantInstance]] = {}
            for p in alive:
                for plot in get_plots(p):
                    if self.is_valid_plot(*plot):
                        plot_map.setdefault(plot, []).append(p)

            # Plots occupés par 2+ plantes
            for plot, occupants in plot_map.items():
                if len(occupants) < 2:
                    continue
                # Vérifier si ce conflit est déjà signalé
                already = any(
                    c.conflict_type == layer
                    and len(c.plants) == len(occupants)
                    and all(p in occupants for p in c.plants)
                    for c in self.conflicts
                    if not c.resolved
                )
                if not already:
                    nc = ConflictNotification(
                        plants=occupants,
                        plots=[plot],
                        conflict_type=layer
                    )
                    new_conflicts.append(nc)
                    self.conflicts.append(nc)

        return new_conflicts

    def __repr__(self) -> str:
        alive = [p for p in self.plants if p.is_alive]
        return (
            f"Tuile[{self.tile_id}] sol={self.soil_type} "
            f"plantes={len(alive)} conflits={len([c for c in self.conflicts if not c.resolved])}"
        )
