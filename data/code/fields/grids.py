"""
SYMBIOSE — fields/grids.py
Grille 2D générique (voisinage hexagonal, diffusion) + champ de perturbation
spatiale. Constantes de perturbation biotique de fond.
"""

from __future__ import annotations

from fields.noise import _hash_noise

# Perturbations écologiques
MORTALITY_RATE      = 0.010   # probabilité d'affaiblissement spontané/semaine
HERBIVORY_BASE      = 0.050   # pression herbivore de base (monoculture non régulée mord)
DISTURBANCE_INERTIA = 0.900   # inertie du champ de perturbation spatial

# ---------------------------------------------------------------------------
# GRIDFIELD
# ---------------------------------------------------------------------------

class GridField:
    """Grille 2D de floats avec voisinage hexagonal."""

    def __init__(self, rows: int, cols: int,
                 initial: float = 0.0, max_val: float = 3.0):
        self.rows    = rows
        self.cols    = cols
        self.max_val = max_val
        self.data: list[list[float]] = [
            [float(initial)] * cols for _ in range(rows)
        ]

    def get(self, r: int, c: int) -> float:
        return self.data[r][c]

    def set(self, r: int, c: int, v: float) -> None:
        self.data[r][c] = max(0.0, min(self.max_val, v))

    def add(self, r: int, c: int, delta: float) -> None:
        self.set(r, c, self.data[r][c] + delta)

    def at_plot(self, r: int, c: int) -> float:
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return self.data[r][c]
        return 0.0

    def total(self) -> float:
        return sum(v for row in self.data for v in row)

    def average(self) -> float:
        n = self.rows * self.cols
        return self.total() / n if n else 0.0

    def hex_neighbors(self, r: int, c: int) -> list[tuple[int, int]]:
        if r % 2 == 0:
            deltas = [(-1,-1),(-1,0),(0,-1),(0,1),(1,-1),(1,0)]
        else:
            deltas = [(-1,0),(-1,1),(0,-1),(0,1),(1,0),(1,1)]
        return [(r+dr, c+dc) for dr,dc in deltas
                if 0 <= r+dr < self.rows and 0 <= c+dc < self.cols]

    def diffuse(self, inertia: float = 0.7) -> None:
        """Double buffer — diffusion isotrope stable."""
        old = [row[:] for row in self.data]
        for r in range(self.rows):
            for c in range(self.cols):
                nb = self.hex_neighbors(r, c)
                avg = sum(old[nr][nc] for nr,nc in nb) / len(nb) if nb else old[r][c]
                self.data[r][c] = max(0.0, min(
                    self.max_val,
                    old[r][c] * inertia + avg * (1.0 - inertia)
                ))

    def ascii_map(self, precision: int = 2) -> str:
        lines = []
        for r, row in enumerate(self.data):
            prefix = "  " if r % 2 == 1 else ""
            lines.append(prefix + " ".join(f"{v:.{precision}f}" for v in row))
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"GridField({self.rows}×{self.cols}) avg={self.average():.3f}"


# ---------------------------------------------------------------------------
# DISTURBANCEFIELD — champ de perturbation spatiale
# ---------------------------------------------------------------------------

class DisturbanceField(GridField):
    """
    Champ de perturbation écologique spatiale.
    Mis à jour hebdomadairement par intégration lente du bruit :
        disturbance[r][c] = disturbance*0.9 + noise*0.1
    Crée des zones chroniquement fragiles et des refuges écologiques stables.
    """

    def __init__(self, rows: int, cols: int):
        super().__init__(rows, cols, initial=0.05, max_val=1.0)

    def tick(self, seed: int, week: int) -> None:
        """Intègre un tick de bruit déterministe dans le champ."""
        for r in range(self.rows):
            for c in range(self.cols):
                noise = _hash_noise(seed, week, r, c)
                current = self.data[r][c]
                self.data[r][c] = (
                    current * DISTURBANCE_INERTIA +
                    noise * (1.0 - DISTURBANCE_INERTIA)
                )

    def local(self, r: int, c: int) -> float:
        """Intensité de perturbation locale normalisée [0, 1]."""
        return self.at_plot(r, c)
