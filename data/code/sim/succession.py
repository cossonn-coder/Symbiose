"""
SYMBIOSE — sim/succession.py
Succession écologique : choix d'archétype ∝ maturité du sol, germination des
adventices sur niches libres, pulse de germination printanière (spring flush).

Extrait d'engine.py (Sprint refactor structurel) — les méthodes Engine
`_succession`/`_spring_flush` sont devenues des fonctions prenant explicitement
`game_state` (seul attribut de `self` qu'elles lisaient). Comportement inchangé.
"""

from __future__ import annotations

from plants import WEED_CATALOGUE
from fields import SEED_ARCHETYPES


def choisir_archetype(candidates: list[str],
                      soil_deep: float, fertilite: float) -> str:
    """
    Choix de l'archétype qui germe parmi les candidats, ∝ maturité du sol.

    Gradient de succession (rang = index dans SEED_ARCHETYPES) :
        pioneer(0) → nitrogen_fixer(1) → grass(2) → competitor(3)
    Rang cible = soil_deep * 3 (continu → bascule douce, pas de seuil dur).
    On choisit le candidat dont le rang est le plus proche du rang cible
    (tie-break déterministe : le plus avancé dans la succession).

    Filet conservé : sur sol pauvre en azote (fertilite < 0.3), la fixatrice
    prime si elle a germé — biologiquement, l'azote limitant la sélectionne.
    """
    if fertilite < 0.3 and "nitrogen_fixer" in candidates:
        return "nitrogen_fixer"
    rang_cible = soil_deep * (len(SEED_ARCHETYPES) - 1)
    return min(candidates,
               key=lambda a: (abs(SEED_ARCHETYPES.index(a) - rang_cible),
                              -SEED_ARCHETYPES.index(a)))


def succession(game_state: dict, tile, eco, week: int) -> list[str]:
    """
    Succession écologique — germination des adventices sur niches libres.

    Pour chaque plot sans plante vivante :
      1. Calcule l'indice de niche (lumière, racines, perturbation, sol)
      2. Tirage déterministe via hash(seed, week, r, c)
      3. Si germination → spawn de l'adventice correspondante

    Ordre de priorité des archétypes :
      sol pauvre → nitrogen_fixer prioritaire
      sol nu     → pioneer
      sol stable → grass puis competitor
    """
    log = []
    seed = game_state.get("seed", 42)

    # Index des plots occupés (racinaire)
    occupied_roots: set[tuple] = set()
    for p in tile.plants:
        if p.is_alive:
            occupied_roots.update(p.root_plots)
            occupied_roots.add(p.position)

    for r in range(tile.grid_rows):
        for c in range(tile.grid_cols):
            # Plot déjà occupé → pas de germination
            if (r, c) in occupied_roots:
                continue
            if not tile.is_valid_plot(r, c):
                continue

            # Densité racinaire voisine normalisée
            neighbors = tile.neighbors(r, c)
            root_density = sum(
                1 for nr, nc in neighbors if (nr, nc) in occupied_roots
            ) / max(len(neighbors), 1)

            light       = eco.lumiere.at_plot(r, c)
            disturbance = eco.disturbance.at_plot(r, c)
            soil_deep   = eco.soil_memory_deep.at_plot(r, c)
            fertilite   = eco.fertilite.at_plot(r, c)

            niche = eco.seed_bank.niche_index(
                r, c, light, root_density, disturbance, soil_deep
            )

            if niche < 0.01:
                continue

            # Priorité écologique : sol pauvre → fixatrice, sinon ordre standard
            candidates = eco.seed_bank.germination_candidates(
                r, c, seed, week, niche
            )

            if not candidates:
                continue

            # Choisir l'archétype ∝ maturité du sol (gradient succession)
            chosen = choisir_archetype(candidates, soil_deep, fertilite)

            plant_class = WEED_CATALOGUE.get(chosen)
            if not plant_class:
                continue

            # Vérifier qu'il n'y a pas déjà une plante sur ce plot exact
            if any(p.position == (r, c) for p in tile.plants if p.is_alive):
                continue

            # Germination — gènes échantillonnés du pool génétique du plot
            # (banque-sol féral). Pool vide → gènes neutres (rétro-compatible).
            new_plant = tile.add_plant(plant_class, r, c)
            if new_plant:
                g = eco.seed_bank.sample_genes(r, c, plant_class, seed, week)
                if g:
                    new_plant.genes = g
                log.append(
                    f"    🌿 Germination : {plant_class.name} @({r},{c}) "
                    f"[niche={niche:.3f} arch={chosen}]"
                )

    return log


def spring_flush(game_state: dict, tile, eco, week: int) -> list[str]:
    """
    Pulse de germination printanière — semaine 1 de chaque année.
    Multiplicateur ×2.5 sur le niche index.
    Simule : lumière ↑ + sols ouverts + banque de graines accumulée.
    """
    log = []
    seed = game_state.get("seed", 42)

    occupied_roots: set[tuple] = set()
    for p in tile.plants:
        if p.is_alive:
            occupied_roots.update(p.root_plots)
            occupied_roots.add(p.position)

    germinations = 0
    for r in range(tile.grid_rows):
        for c in range(tile.grid_cols):
            if (r, c) in occupied_roots:
                continue
            if not tile.is_valid_plot(r, c):
                continue

            neighbors = tile.neighbors(r, c)
            root_density = sum(
                1 for nr, nc in neighbors if (nr, nc) in occupied_roots
            ) / max(len(neighbors), 1)

            light       = eco.lumiere.at_plot(r, c)
            disturbance = eco.disturbance.at_plot(r, c)
            soil_deep   = eco.soil_memory_deep.at_plot(r, c)
            fertilite   = eco.fertilite.at_plot(r, c)

            niche = eco.seed_bank.niche_index(
                r, c, light, root_density, disturbance, soil_deep
            ) * 2.5   # spring flush multiplier

            if niche < 0.01:
                continue

            candidates = eco.seed_bank.germination_candidates(
                r, c, seed, week * 100, niche   # seed différent du tick normal
            )

            if not candidates:
                continue

            chosen = choisir_archetype(candidates, soil_deep, fertilite)

            plant_class = WEED_CATALOGUE.get(chosen)
            if not plant_class:
                continue

            if any(p.position == (r, c) for p in tile.plants if p.is_alive):
                continue

            new_plant = tile.add_plant(plant_class, r, c)
            if new_plant:
                g = eco.seed_bank.sample_genes(r, c, plant_class, seed, week * 100)
                if g:
                    new_plant.genes = g
                log.append(
                    f"    🌸 Spring flush : {plant_class.name} @({r},{c}) "
                    f"[niche={niche:.3f} arch={chosen}]"
                )
                germinations += 1

    if germinations > 0:
        log.insert(0, f"  🌱 Spring flush — {germinations} germination(s)")
    return log
