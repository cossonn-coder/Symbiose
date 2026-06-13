"""
SYMBIOSE — sim/succession.py
Succession écologique : choix d'archétype ∝ maturité du sol, germination des
adventices sur niches libres, pulse de germination printanière (spring flush).

Extrait d'engine.py (Sprint refactor structurel) — les méthodes Engine
`_succession`/`_spring_flush` sont devenues des fonctions prenant explicitement
`game_state` (seul attribut de `self` qu'elles lisaient). Comportement inchangé.
"""

from __future__ import annotations

from plants import WEED_CATALOGUE, PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from fields import SEED_ARCHETYPES, _hash_noise


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


def _lever_grains_en_attente(game_state: dict, tile, eco, week: int, seed: int,
                             occupied_roots: set, niche_mult: float,
                             hash_canal: int) -> list[str]:
    """Lève les graines DÉPOSÉES par le joueur (`planter`) AVANT le balayage des
    adventices. Pour chaque plot LIBRE portant un `GrainEnAttente` et dont la niche
    est favorable, lève la PLUS ANCIENNE (FIFO) : crée la plante via
    `tile.add_plant`, lui donne ses gènes PROPRES (PAS de `sample_genes`) et
    transmet le tag `cultive` (`marquer_replante`, par avatar — cultivé vs féral,
    §9.4). Déterministe (réutilise le hash de niche, aucun RNG). Un plot occupé → la
    graine PATIENTE (Q4) ; elle lèvera quand le plot se libérera.

    `occupied_roots` est MUTÉ (les plots de la plante levée s'y ajoutent) → le
    balayage adventices qui suit ne re-germe pas sur le plot pris. VIDE au repos
    (`grains_en_attente` vide) → court-circuit immédiat, golden inchangé."""
    if not tile.grains_en_attente:
        return []                              # cas nominal du golden : rien à lever
    # Import local : couplage event-driven (uniquement sur le chemin « planté »),
    # garde l'en-tête de succession « écologie pure » et évite tout ordre de
    # chargement fragile (succession est importée avant engine dans sim/__init__).
    from sim.maitrise_detection import marquer_replante

    log = []
    for (r, c), grains in tile.grains_en_attente.items():
        if not grains:
            continue
        if not tile.is_valid_plot(r, c):
            continue
        # Verrou d'occupation LEVÉ (compétition intra-plot, Q1/Q4) : un grain lève
        # même sur plot occupé — la cohabitation est décidée par les champs réels
        # (lumière-sol ombragée + sol établi déjà dans niche_index), pas par un
        # terme « occupation » artificiel. `occupied_roots` reste lu pour la
        # densité racinaire voisine et MUTÉ après chaque levée (anti
        # double-germination intra-tick sur la même position).

        neighbors = tile.neighbors(r, c)
        root_density = sum(
            1 for nr, nc in neighbors if (nr, nc) in occupied_roots
        ) / max(len(neighbors), 1)

        light       = eco.lumiere.at_plot(r, c)
        disturbance = eco.disturbance.at_plot(r, c)
        soil_deep   = eco.soil_memory_deep.at_plot(r, c)

        grain = grains[0]
        plant_class = (PLANT_CATALOGUE.get(grain.species)
                       or PERENNIAL_CATALOGUE.get(grain.species))
        if plant_class is None:
            grains.pop(0)                      # espèce inconnue (ne devrait pas arriver) → grain jeté
            continue

        niche = eco.seed_bank.niche_index(
            r, c, light, root_density, disturbance, soil_deep
        ) * niche_mult

        # Escompte la lumière requise par la tolérance à l'ombre du grain (Q6,
        # même frein que la succession) : base d'espèce × gène propre du grain.
        if light > 0.0:
            tol = plant_class.shade_tolerance_base() * grain.genes.get("tolerance_ombre", 1.0)
            niche *= min(1.0, light * tol) / light

        if niche < 0.01:
            continue                           # niche trop pauvre → pas encore le bon moment

        # Tirage déterministe sur un canal de hash DISTINCT des adventices : une
        # graine plantée lève à proba = niche (sans l'escompte de densité féral des
        # adventices → un semis délibéré prend plus volontiers qu'une graine férale).
        if _hash_noise(seed, hash_canal, r, c) >= niche:
            continue

        new_plant = tile.add_plant(plant_class, r, c)
        if new_plant is None:
            continue
        grains.pop(0)                          # FIFO : la plus ancienne levée
        new_plant.genes = dict(grain.genes)    # gènes PROPRES (≠ sample_genes du féral)
        occupied_roots.update(new_plant.root_plots)
        occupied_roots.add(new_plant.position)
        if grain.cultive:
            marquer_replante(game_state, grain.player, tile.tile_id, r, c)
        log.append(
            f"    🌱 Levée (planté) : {plant_class.name} @({r},{c}) "
            f"[niche={niche:.3f}]"
        )
    return log


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

    # Tolérance à l'ombre par archétype (compétition intra-plot, Q6) — escompte la
    # lumière requise à la germination, par espèce candidate (cf. germination_candidates).
    arch_tolerance = {a: cls.shade_tolerance_base()
                      for a, cls in WEED_CATALOGUE.items()}

    # Index des plots occupés (racinaire)
    occupied_roots: set[tuple] = set()
    for p in tile.plants:
        if p.is_alive:
            occupied_roots.update(p.root_plots)
            occupied_roots.add(p.position)

    # Levée des graines plantées (event-driven) AVANT les adventices : un grain
    # déposé a priorité sur la germination spontanée du plot.
    log += _lever_grains_en_attente(game_state, tile, eco, week, seed,
                                    occupied_roots, niche_mult=1.0,
                                    hash_canal=week * 7 + 50)

    for r in range(tile.grid_rows):
        for c in range(tile.grid_cols):
            # Verrou d'occupation LEVÉ (Q1) : on ne saute plus les plots occupés.
            # Le frein vient des champs réels (lumière-sol ombragée + sol établi
            # déjà dans niche_index) — pas d'un terme « occupation » artificiel.
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
                r, c, seed, week, niche, light=light, arch_tolerance=arch_tolerance
            )

            if not candidates:
                continue

            # Choisir l'archétype ∝ maturité du sol (gradient succession)
            chosen = choisir_archetype(candidates, soil_deep, fertilite)

            plant_class = WEED_CATALOGUE.get(chosen)
            if not plant_class:
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

    arch_tolerance = {a: cls.shade_tolerance_base()
                      for a, cls in WEED_CATALOGUE.items()}

    occupied_roots: set[tuple] = set()
    for p in tile.plants:
        if p.is_alive:
            occupied_roots.update(p.root_plots)
            occupied_roots.add(p.position)

    # Levée des graines plantées (même priorité qu'en succession normale), avec le
    # boost printanier ×2.5 sur la niche — le printemps est un bon moment pour lever.
    log += _lever_grains_en_attente(game_state, tile, eco, week, seed,
                                    occupied_roots, niche_mult=2.5,
                                    hash_canal=week * 100 + 50)

    germinations = 0
    for r in range(tile.grid_rows):
        for c in range(tile.grid_cols):
            # Verrou d'occupation LEVÉ (Q1) — cf. succession().
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
                r, c, seed, week * 100, niche,   # seed différent du tick normal
                light=light, arch_tolerance=arch_tolerance
            )

            if not candidates:
                continue

            chosen = choisir_archetype(candidates, soil_deep, fertilite)

            plant_class = WEED_CATALOGUE.get(chosen)
            if not plant_class:
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
