"""
SYMBIOSE — fields/ecofields/couverture.py
Responsabilité : le champ scalaire `couverture_sol` (fraction du sol couverte par
le feuillage des strates BASSES, ∈ [0,1] par plot), recalculé chaque tick par
SCATTER depuis les empreintes des plantes — le SOCLE de la luxuriance par
stratification (sprint LUXURIANCE, tronçon ①, D65 §2.1).

Mixin de comportement d'`EcoFields` (comme hydrologie/ticks). Aucun état propre :
opère sur `self`. Un SEUL balayage des plantes/tick (jamais un sweep de grille —
perf : le LightField pèse déjà 53 % du CPU). Le champ est LU par :
  (a) l'évaporation (`hydrologie.tick_hydrology`) — sol couvert = moins d'évaporation ;
  (b) la germination férale (`sim/succession`) — couvert dense = adventices étouffées ;
  (c) [tronçon ②] le gate d'établissement du clonal (auto-limitation + cap perf).

Règle de couches : `fields` n'importe pas `sim`. Les plantes sont passées en
argument (comme `tick_light`) ; on ne lit d'elles QUE de la géométrie et la strate
du stade — aucune décision de gameplay ici.
"""

from __future__ import annotations

from plants.base import _plots_in_radius

# Strates qui comptent dans la couverture au SOL. Les strates moyenne/haute/
# grimpante forment le volume aérien (déjà géré par la lumière verticale) — elles
# n'étouffent PAS le sol, seul le tapis bas le fait (décision D2).
_STRATES_SOL = ("sol", "basse")


class CouvertureMixin:
    """Champ `couverture_sol` par scatter des empreintes des plantes basses."""

    def tick_couverture(self, plants: list, saison: str | None = None) -> None:
        """Recalcule `couverture_sol` : pour chaque plante VIVANTE de strate `sol`
        ou `basse`, stampe sa densité de feuillage sur les plots de son empreinte au
        sol (`_plots_in_radius` sur `canopy_r`) et accumule. Le champ (créé à
        `max_val=1.0`) écrête automatiquement chaque `add` à [0,1] → pas de clamp final.

        Recalcul COMPLET chaque tick (repart de 0) : la couverture suit fidèlement la
        croissance/mort/déplacement des plantes, sans mémoire parasite. Déterministe,
        zéro RNG (philo #3). À placer AVANT ses lecteurs dans la boucle (évaporation,
        germination). Tuile SANS plante basse → champ nul → lecteurs neutres."""
        cov = self.couverture_sol
        cov.fill(0.0)
        for p in plants:
            if not p.is_alive:
                continue
            cls = p.plant_class
            if p.stage.strate not in _STRATES_SOL:
                continue
            # Densité de feuillage de la strate (opacité au sol) × empreinte de canopée.
            # `foliage_density_at` retourne 0 pour un caduc en hiver → un tapis nu ne
            # couvre plus (cohérent avec l'ombre verticale). `canopy_radius_at` dérive du
            # rayon de couronne du stade (empreinte au sol réelle de la plante basse).
            density = cls.foliage_density_at(p, saison)
            if density <= 0.0:
                continue
            radius = cls.canopy_radius_at(p)
            for (r, c) in _plots_in_radius(p.x_cm, p.y_cm, radius):
                # `_plots_in_radius` peut déborder de la grille (empreinte en bord de
                # tuile) → on filtre (add() indexe `data[r][c]` sans garde de bornes).
                if 0 <= r < cov.rows and 0 <= c < cov.cols:
                    cov.add(r, c, density)
