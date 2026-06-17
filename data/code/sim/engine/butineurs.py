"""
SYMBIOSE — sim/engine/butineurs.py
Butineurs déterministes & dépôt de pollen conspécifique (arc pollinisation,
tronçon ③ — CONCEPTION_POLLINISATION §F).

Le basculement assumé (§F.1) : une PART de la perception devient MÉCANIQUE. Les
agents butineurs (échantillonnés depuis les champs pollinisateurs par type)
marchent de fleur en fleur et DÉPOSENT réellement le pollen → `pollen_recu` des
plantes (lu par la nouaison §B au tronçon ④). La constance florale est mécanique :
un agent ne dépose que sur une fleur de l'espèce qu'il transporte.

Répartition des rôles (respect des couches `plants ← fields ← sim`) :
  - `fields.population.sample_foragers` (couche fields) échantillonne et fait
    MARCHER les agents — PURE & déterministe, ne touche aucune plante, rend des
    `deposits` ;
  - CE mixin (couche sim) construit la « carte des fleurs » par type depuis les
    plantes, applique les `deposits` à `pollen_recu`, et range les agents dans
    `eco.foragers` pour le snapshot.

GOLDEN NEUTRE (tronçon ③) : on n'écrit QUE `pollen_recu` (hors `_PLANT_ATTRS` du
golden, et lu par PERSONNE à ce tronçon) et `eco.foragers` (transient, hors
digest), AUCUN log. Déterminisme (philo #3) : tout dérive de `seed` + `_hash_noise`
+ la floraison du tick, jamais de RNG vivant. À 0 pollinisateur (0 agent),
`pollen_recu` reste 0 → comportement identique à l'absence d'insectes (§F.6).
"""

from __future__ import annotations
from fields import (sample_foragers, build_pollinator_registry,
                    POLLINATOR_NAMES)


def _build_flower_maps(plants, rows, cols, attractivite, defaut):
    """Construit, pour UN type de pollinisateur, la « carte des fleurs » perçue
    (floraison conspécifique × attractivité du type) ET l'index plot→plantes pour
    appliquer les dépôts.

    Retourne (species_grids, plants_at) :
      - species_grids : {nom_espèce → grille[r][c]} pondérée par l'attractivité
        (les familles d'attractivité nulle — anémophiles — sont écartées : le type
        ne les butine pas) ;
      - plants_at     : {nom_espèce → {(r,c) → [(plante, floraison), …]}} pour
        répartir un dépôt entre les plantes conspécifiques d'un plot, ∝ floraison.
    """
    species_grids: dict = {}
    plants_at: dict = {}
    for p in plants:
        if not p.is_alive or p.floraison <= 0.0:
            continue
        w = attractivite.get(p.plant_class.family, defaut)
        if w <= 0.0:
            continue
        key = p.plant_class.name
        grid = species_grids.get(key)
        if grid is None:
            grid = [[0.0] * cols for _ in range(rows)]
            species_grids[key] = grid
            plants_at[key] = {}
        contrib = p.floraison * w
        for (r, c) in p.foliar_plots:
            if 0 <= r < rows and 0 <= c < cols:
                grid[r][c] += contrib
                plants_at[key].setdefault((r, c), []).append((p, p.floraison))
    return species_grids, plants_at


def _apply_deposits(deposits, plants_at):
    """Applique les dépôts d'un type à `pollen_recu`. Un dépôt (espèce, r, c,
    charge) est réparti entre les plantes conspécifiques du plot ∝ leur floraison
    (la plante la plus fleurie en capte le plus)."""
    for (species, r, c, amount) in deposits:
        bucket = plants_at.get(species, {}).get((r, c))
        if not bucket:
            continue
        total = sum(fl for (_, fl) in bucket)
        if total <= 0.0:
            continue
        for (plant, fl) in bucket:
            plant.pollen_recu += amount * (fl / total)


class ButineurMixin:
    def _tick_butineurs(self, tile, eco, seed: int, week_in_year: int) -> None:
        """Fait marcher les butineurs de chaque type, dépose le pollen
        conspécifique et range les agents dans `eco.foragers` (§F).

        N'émet aucun log et n'écrit que `pollen_recu`/`eco.foragers` → golden
        NEUTRE. Appelée une fois par tuile et par semaine (boucle.py), APRÈS le
        tick des champs de population (les agents s'échantillonnent sur la densité
        fraîche)."""
        registre = {ps.name: ps for ps in build_pollinator_registry()}
        agents_all = []
        for name in POLLINATOR_NAMES:
            field = eco.populations.get(name) if eco.populations else None
            ps = registre.get(name)
            if field is None or ps is None:
                continue
            species_grids, plants_at = _build_flower_maps(
                tile.plants, eco.rows, eco.cols,
                ps.attractivite, ps.attractivite_defaut)
            if not species_grids:
                continue
            agents, deposits = sample_foragers(
                field, species_grids, ps.forager, seed, week_in_year)
            _apply_deposits(deposits, plants_at)
            agents_all.extend(agents)
        eco.foragers = agents_all
