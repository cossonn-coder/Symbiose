"""
SYMBIOSE — tools/simserver/perf_annees.py
Bilan par année du rapport perf : une ligne par an, pour lire une TENDANCE.

📖 Les pires ticks ne montrent que les extrêmes, et leurs comptes par espèce sont
biaisés : ils ne décrivent que des semaines déjà anormales. Ici chaque année est
relevée à la même date, sa dernière semaine, donc les années se comparent.

`plots_neufs` répond à « le tapis se déplace-t-il ? » : part des plots de l'espèce
dominante absents de ses plots de l'an précédent. Rien n'est recalculé après coup :
un bilan par an, mémoire bornée à `MAX_ANNEES` lignes, coût nul le reste de l'année.

Golden NEUTRE : le golden tourne hors serveur.
"""
from __future__ import annotations

import statistics
from collections import Counter, deque

from .perf import rss_mo

MAX_ANNEES = 60


class HistoriqueAnnees:
    """Alimenté après chaque tick par `ajouter` ; `lignes()` rend le bilan."""

    def __init__(self):
        self.bilans: deque = deque(maxlen=MAX_ANNEES)
        self._ms: list[float] = []
        self._cpu = 0.0
        self._gc = 0.0
        self._plots_avant: tuple[str, set] | None = None

    def ajouter(self, engine, ms_tick: float, mesure: dict) -> None:
        self._ms.append(ms_tick)
        self._cpu += mesure["cpu_ms"]
        self._gc += mesure["gc_ms"]
        semaine = engine.game_state["week"] - 1   # `week` est déjà incrémenté
        if semaine % 52 == 0:
            self.bilans.append(self._cloturer(engine, semaine))
            self._ms, self._cpu, self._gc = [], 0.0, 0.0

    def _cloturer(self, engine, semaine: int) -> dict:
        par_espece: Counter = Counter()
        plots: dict[str, set] = {}
        for tile in engine.game_state["tiles"]:
            for p in tile.plants:
                if p.is_alive:
                    nom = p.plant_class.__name__
                    par_espece[nom] += 1
                    plots.setdefault(nom, set()).add((tile.tile_id, *p.position))
        n = sum(par_espece.values())
        dominante = par_espece.most_common(1)[0][0] if n else None
        ici = plots.get(dominante, set())
        return {
            "an": semaine // 52,
            "tick_median_ms": round(statistics.median(self._ms), 1),
            "tick_max_ms": round(max(self._ms), 1),
            "total_s": round(sum(self._ms) / 1000.0, 1),
            "cpu_s": round(self._cpu / 1000.0, 1),
            "gc_s": round(self._gc / 1000.0, 1),
            "rss_mo": rss_mo(),
            "plantes": n,
            "especes": len(par_espece),
            "top": [[nom, k] for nom, k in par_espece.most_common(3)],
            "dominante_plots": len(ici),
            "plots_neufs_pct": self._part_neuve(dominante, ici),
        }

    def _part_neuve(self, dominante: str | None, ici: set) -> int | None:
        """% des plots de la dominante absents de l'an passé. None la première année,
        ou si la dominante a changé : la comparaison n'aurait pas de sens."""
        avant = self._plots_avant
        self._plots_avant = (dominante, ici)
        if avant is None or avant[0] != dominante or not ici:
            return None
        return round(100.0 * len(ici - avant[1]) / len(ici))

    def lignes(self) -> list:
        return list(self.bilans)
