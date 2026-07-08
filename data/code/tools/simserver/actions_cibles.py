"""
SYMBIOSE — tools/simserver/actions_cibles.py
Résolution de la DÉSIGNATION d'un geste : traduire ce que la vue a cliqué
(un point x_cm/y_cm continu, un plot r/c, une plante par position, un
squelette de bois mort) en l'objet moteur correspondant. Scindé de
`actions.py` (routeur) au refactor de taille du sprint équilibre-invasion —
le routage et la résolution de cible sont deux responsabilités distinctes.

Mixin de `SimServer` (comme `ActionsMixin`) : ses méthodes sont appelées via
`self.` depuis le routeur, le MRO les résout. Aucune règle de jeu ici — que
de la géométrie de désignation (la position est l'identité, kickoff §8).
"""
from __future__ import annotations

from constants import PLOT_CM     # échelle plot (position continue → plot-foyer)

from .version import PLANT_EPSILON_CM
from .maitrise_pont import noter_geste_pont  # hook C (imputation, voix ①)


class CiblesMixin:
    """La résolution des cibles d'un geste (position → plante/plot/squelette)."""

    def _noter_geste_maitrise(self, verb, target: dict) -> None:
        """Hook C (voix ①) : enregistre le geste sur son PLOT (zone (tile_id, r, c))
        dans la fenêtre d'imputation de la maîtrise. Le plot se résout depuis le
        `target` — soit {r, c} direct (gestes sur plot), soit {x_cm, y_cm} continu
        (planter/arroser/plante-par-position), via `_plot_at` (canon plot-foyer).
        Geste sans tuile ni plot résoluble (ex. `acheter_magazine`) → no-op : rien
        à imputer à une zone. PUR (lecture du target + écriture état joueur)."""
        gs = self.engine.game_state
        tiles = {t.tile_id: t for t in gs["tiles"]}
        tile = tiles.get(target.get("tile"))
        if tile is None:
            return
        r, c = target.get("r"), target.get("c")
        if (isinstance(r, int) and not isinstance(r, bool)
                and isinstance(c, int) and not isinstance(c, bool)
                and 0 <= r < tile.grid_rows and 0 <= c < tile.grid_cols):
            rc = (r, c)
        else:
            rc = self._plot_at(tile, target.get("x_cm"), target.get("y_cm"))
        if rc is None:
            return
        noter_geste_pont(gs, gs["current_player"], gs["week"] - 1,
                         (tile.tile_id, rc[0], rc[1]), verb=verb)

    @staticmethod
    def _plant_at(tile, x_cm, y_cm, eps: float = PLANT_EPSILON_CM):
        """La plante VIVANTE de la tuile à ±eps de (x_cm, y_cm) locale, ou None.
        La position est l'identité (kickoff §8) : pas d'id inventé."""
        if not isinstance(x_cm, (int, float)) or not isinstance(y_cm, (int, float)):
            return None
        for p in tile.plants:
            if (p.is_alive and p.x_cm is not None
                    and abs(p.x_cm - x_cm) <= eps
                    and abs(p.y_cm - y_cm) <= eps):
                return p
        return None

    @staticmethod
    def _skeleton_at(tile, x_cm, y_cm, eps: float = PLANT_EPSILON_CM):
        """Le SQUELETTE (plante MORTE avec `bois_restant > 0`) de la tuile à ±eps de
        (x_cm, y_cm) locale, ou None. Miroir de `_plant_at` pour la cible de `broyer`
        (les morts persistent au snapshot avec `dead=true`, cf. serialize) : `_plant_at`
        ne retient que les VIVANTES, il faut donc un résolveur dédié au bois à broyer."""
        if not isinstance(x_cm, (int, float)) or not isinstance(y_cm, (int, float)):
            return None
        for p in tile.plants:
            if (not p.is_alive and getattr(p, "bois_restant", 0.0) > 0.0
                    and p.x_cm is not None
                    and abs(p.x_cm - x_cm) <= eps
                    and abs(p.y_cm - y_cm) <= eps):
                return p
        return None

    @staticmethod
    def _plot_at(tile, x_cm, y_cm):
        """Le plot-foyer (r, c) d'une position LOCALE continue, ou None si hors
        tuile. Même convention que `PlantInstance.plot_foyer` (canon moteur) :
        `(int(y // PLOT_CM), int(x // PLOT_CM))` — y→ligne, x→colonne. Sert aux
        gestes de milieu désignés par point (planter·arroser). NB : bool est un
        sous-type d'int → exclu (un `true` JSON n'est pas une coordonnée)."""
        if (not isinstance(x_cm, (int, float)) or isinstance(x_cm, bool)
                or not isinstance(y_cm, (int, float)) or isinstance(y_cm, bool)):
            return None
        r, c = int(y_cm // PLOT_CM), int(x_cm // PLOT_CM)
        if 0 <= r < tile.grid_rows and 0 <= c < tile.grid_cols:
            return (r, c)
        return None
