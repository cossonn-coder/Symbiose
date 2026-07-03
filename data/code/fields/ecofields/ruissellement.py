"""
SYMBIOSE — fields/ecofields/ruissellement.py
Responsabilité : le RUISSELLEMENT latéral de la lame d'eau de surface
(`eau_surface`) d'une tuile — l'eau dévale la surface hydraulique (altitude +
épaisseur de sol) du haut vers le bas, s'infiltre dans les pores si le sol peut
boire, s'évapore. Une cuvette accumule (flaque), une bosse s'assèche.

Mixin de comportement de `EcoFields` (sprint hydrologie & marécages ②). Appelé
par la boucle JUSTE APRÈS `tick_hydrology` (qui capture le surplus de saturation
dans `eau_surface`) et AVANT `tick_decomposition`. Aucun état propre : opère sur
`self`.

DÉTERMINISME (philo #3) : la redistribution lit `eau_surface` sur un DOUBLE BUFFER
(instantané figé en début de tick, écriture dans une grille neuve) → le résultat
NE dépend PAS de l'ordre de balayage (sinon direction privilégiée = RNG déguisé).
Zéro RNG. Conservation de masse À L'INTÉRIEUR de la tuile ; l'eau qui sort par un
bord du monde est perdue (exutoire implicite, pas de tuile voisine simulée).
"""

from __future__ import annotations

from .constants import *   # HUM_CAP, RUISSELLEMENT_FRACTION, INFILTRATION_SURFACE, EVAP_SURFACE

# Voisinage von Neumann (4 voisins orthogonaux) — c'est la grille du RUISSELLEMENT
# (l'eau ne diagonale pas d'un plot). ≠ `hex_neighbors` des champs biologiques : ici
# on modélise un écoulement cartésien sur la topographie du sol.
_VOISINS_4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


class RuissellementMixin:
    """Écoulement latéral de la lame d'eau de surface sur le micro-relief."""

    def tick_ruissellement(self) -> None:
        """Un tick d'écoulement de `eau_surface` sur la surface hydraulique
        `S = altitude + epaisseur_sol`. Étapes (cf. kickoff §Modèle) :
          1. Snapshot `src` de la lame (double buffer) ; `dst` = grille neuve.
          2. Pour chaque plot, distribuer `RUISSELLEMENT_FRACTION · src` vers les
             voisins von Neumann PLUS BAS, réparti ∝ la pente (multiple-flow) ; le
             reste demeure. L'eau qui sort par un bord est perdue (exutoire).
          3. Infiltration : une part de la lame redescend dans `humidite` si le sol
             peut encore boire (bornée par `HUM_CAP − humidite` et la structure).
          4. Évaporation de surface : `dst *= (1 − EVAP_SURFACE)`.
          5. `eau_surface = dst`.

        No-op strict si `eau_surface` est NULLE partout (aucune saturation dépassée
        au tick d'hydrologie) → golden NEUTRE tant qu'aucun plot ne gorge.
        """
        rows, cols = self.rows, self.cols
        # 1. Double buffer : on lit TOUT sur `src` figé, on écrit sur `dst` neuf →
        # l'ordre de balayage n'influence rien (déterminisme, philo #3).
        src = [row[:] for row in self.eau_surface.data]
        dst = [[0.0] * cols for _ in range(rows)]

        # 2. Redistribution ∝ pente vers les voisins descendants (multiple-flow).
        for r in range(rows):
            for c in range(cols):
                lame = src[r][c]
                if lame <= 0.0:
                    continue
                s_ici = (self.altitude.data[r][c]
                         + self.epaisseur_sol.data[r][c])
                # Dénivelés vers les voisins PLUS BAS (Δ > 0) ; on mémorise le voisin
                # (None au bord du monde = exutoire, l'eau y part sans destinataire).
                deltas = []
                somme = 0.0
                for dr, dc in _VOISINS_4:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        s_voisin = (self.altitude.data[nr][nc]
                                    + self.epaisseur_sol.data[nr][nc])
                        delta = s_ici - s_voisin
                    else:
                        # Bord du monde : on écoule vers le vide (surface hydraulique
                        # nulle hors terrain), l'eau part à l'exutoire = perdue.
                        delta = s_ici
                        nr = nc = None
                    if delta > 0.0:
                        deltas.append((nr, nc, delta))
                        somme += delta
                if somme <= 0.0:
                    # Aucun voisin plus bas (creux local) : toute la lame reste.
                    dst[r][c] += lame
                    continue
                flux = RUISSELLEMENT_FRACTION * lame
                dst[r][c] += lame - flux                      # le reste demeure
                for nr, nc, delta in deltas:
                    part = flux * (delta / somme)
                    if nr is not None:                        # voisin interne : reçoit
                        dst[nr][nc] += part
                    # else : bord du monde → part perdue (exutoire, non conservée)

        # 3. Infiltration dans les pores (∝ structure du sol) + 4. évaporation.
        for r in range(rows):
            for c in range(cols):
                lame = dst[r][c]
                if lame > 0.0:
                    place = HUM_CAP - self.humidite.data[r][c]   # ce que le sol peut boire
                    if place > 0.0:
                        # Un sol grumeleux (structure→1) réabsorbe la flaque, un sol
                        # battu/argileux (structure→0) la garde en surface (interconnexion).
                        capacite = INFILTRATION_SURFACE * self.structure_sol.at_plot(r, c)
                        infil = min(lame, capacite, place)
                        if infil > 0.0:
                            self.humidite.add(r, c, infil)
                            lame -= infil
                    lame *= (1.0 - EVAP_SURFACE)                  # 4. évaporation de surface
                # 5. On écrit la lame résiduelle (le GridField borne [0, HUM_CAP]).
                self.eau_surface.set(r, c, lame)
