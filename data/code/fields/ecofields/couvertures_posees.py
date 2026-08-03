"""
SYMBIOSE — fields/ecofields/couvertures_posees.py
Responsabilité : les deux champs scalaires des COUVERTURES POSÉES par le joueur
(sprint effondrement météo ③, `docs/champs/climat/conception_effondrement_meteo.md`
§4/§7) — l'appareil de PRÉPARATION contre l'effondrement (tronçon ①) :

  • `couvert_pose`  ∈ [0,1] par plot — écran physique du VOILE d'hivernage (zone)
    et de la CLOCHE (un plot). Il s'AJOUTE au couvert de litière/neige lu par le
    gel nocturne (`thermique.t_min_nuit_at`) → protège du GEL ; il apporte aussi
    une protection LOCALE lue par la grêle (`mortalite._mediated_damage`).
  • `ombre_pose`   ∈ [0,1] par plot — occultation de l'OMBRIÈRE (zone). Elle
    ATTÉNUE la lumière-sol du tick (`appliquer_ombrieres`, après `tick_light`) →
    moins de gain solaire dans la thermique → sol plus frais → MOINS d'évaporation
    (mitige CANICULE / SÉCHERESSE). Agir par le MILIEU (philo #1/#2) : on baisse un
    champ du sol, la plante répond — jamais un multiplicateur direct sur la plante.

⚠️ À NE PAS confondre avec `couverture.py` (champ `couverture_sol`, la couverture
VÉGÉTALE émergente des plantes basses). Ici ce sont des STRUCTURES POSÉES.

Mixin de comportement d'`EcoFields` (comme paillage/couverture). Les deux champs
sont alloués PARESSEUSEMENT (None au repos → zéro RAM, lecteurs neutres) et POSÉS
hors tick par les gestes `poser_voile`/`poser_cloche`/`poser_ombriere`
(`sim/actions/couvertures.py`, event-driven). Aucun tick propre : une couverture
posée PERSISTE (structure durable, pas un mulch qui se décompose). NULS partout au
repos (le smoke ne pose aucune couverture) → tous les lecteurs neutres → golden
NEUTRE par construction. Déterministe, zéro RNG (philo #3).
"""

from __future__ import annotations

import math

from fields.grids import GridField


class CouverturePoseeMixin:
    """Champs `couvert_pose` / `ombre_pose` + leurs readers (mixin d'`EcoFields`)."""

    # --- Readers neutres (None au repos → 0.0) -------------------------------
    def couvert_at(self, r: int, c: int) -> float:
        """Écran physique posé au plot (r,c) ∈ [0,1] — voile/cloche. 0.0 tant
        qu'aucune couverture n'est posée (champ None) OU hors grille. Lu par le gel
        (`t_min_nuit_at`) et la grêle (`_mediated_damage`)."""
        f = self.couvert_pose
        return f.at_plot(r, c) if f is not None else 0.0

    def ombre_at(self, r: int, c: int) -> float:
        """Occultation d'ombrière posée au plot (r,c) ∈ [0,1]. 0.0 au repos (champ
        None) OU hors grille. Lu par `appliquer_ombrieres`."""
        f = self.ombre_pose
        return f.at_plot(r, c) if f is not None else 0.0

    # --- Pose (hors tick, appelée par les gestes) ----------------------------
    def _disque(self, r: int, c: int, rayon_plots: float):
        """Plots (rr,cc) de la grille dans le disque de centre (r,c) et de rayon
        `rayon_plots` (en plots). Rayon 0 → seulement (r,c) (empreinte 1×1, cloche).
        Déterministe (parcours ordonné), zéro RNG."""
        rint = int(math.floor(rayon_plots))
        for dr in range(-rint, rint + 1):
            for dc in range(-rint, rint + 1):
                rr, cc = r + dr, c + dc
                if (0 <= rr < self.rows and 0 <= cc < self.cols
                        and math.hypot(dr, dc) <= rayon_plots):
                    yield rr, cc

    def poser_couvert(self, r: int, c: int, dose: float,
                      rayon_plots: float = 0.0) -> None:
        """Pose un écran physique `dose` ∈ [0,1] sur le disque (r,c, rayon_plots) —
        VOILE (zone) ou CLOCHE (rayon 0). Alloue le champ à la première pose
        (paresseux). On prend le MAX avec l'existant (superposer voile + cloche ne
        dépasse pas 1, borné par le GridField), jamais une addition qui saturerait
        artificiellement."""
        if self.couvert_pose is None:
            self.couvert_pose = GridField(self.rows, self.cols, max_val=1.0)
        f = self.couvert_pose
        for rr, cc in self._disque(r, c, rayon_plots):
            f.set(rr, cc, max(f.data[rr][cc], dose))

    def poser_ombre(self, r: int, c: int, dose: float,
                    rayon_plots: float = 0.0) -> None:
        """Pose une occultation `dose` ∈ [0,1] sur le disque (r,c, rayon_plots) —
        OMBRIÈRE (zone). Alloue le champ à la première pose (paresseux). MAX avec
        l'existant (comme `poser_couvert`)."""
        if self.ombre_pose is None:
            self.ombre_pose = GridField(self.rows, self.cols, max_val=1.0)
        f = self.ombre_pose
        for rr, cc in self._disque(r, c, rayon_plots):
            f.set(rr, cc, max(f.data[rr][cc], dose))

    # --- Effet ombrière sur la lumière-sol (dans la boucle, après tick_light) -
    def appliquer_ombrieres(self) -> None:
        """ATTÉNUE `eco.lumiere` (lumière-sol) par `ombre_pose` — à appeler dans la
        boucle JUSTE APRÈS `tick_light` (qui recalcule la lumière de zéro) et AVANT
        ses lecteurs thermique/hydrologie. Un plot sous ombrière reçoit moins de gain
        solaire → `tick_thermique` chauffe moins le sol → `tick_hydrology` évapore
        moins : la sécheresse/canicule sont mitigées PAR LE MILIEU, sans toucher la
        plante (philo #1/#2). No-op STRICT au repos (`ombre_pose is None`) → la
        lumière-sol reste bit-identique → golden NEUTRE."""
        f = self.ombre_pose
        if f is None:
            return
        lum = self.lumiere
        for r in range(self.rows):
            for c in range(self.cols):
                o = f.data[r][c]
                if o > 0.0:
                    lum.set(r, c, lum.data[r][c] * (1.0 - o))
