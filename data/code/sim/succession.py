"""
SYMBIOSE — sim/succession.py
Succession écologique : choix d'archétype ∝ maturité du sol, germination des
adventices sur niches libres. La vague de printemps ÉMERGE désormais du
réchauffement du sol via la porte thermique (tronçons ②③④) — l'ancien pulse
calendaire printanier (×2.5 en semaine 1) a été supprimé au tronçon ⑤.

Extrait d'engine.py (Sprint refactor structurel) — la méthode Engine
`_succession` est devenue une fonction prenant explicitement `game_state`
(seul attribut de `self` qu'elle lisait). Comportement inchangé.
"""

from __future__ import annotations

from plants import WEED_CATALOGUE, PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from fields import SEED_ARCHETYPES, _hash_noise
from fields.ecofields import bell, T_GERM_FLOOR, GERM_GENE_SHIFT


def _germ_gene_mean(eco, r: int, c: int, plant_class: type) -> float:
    """Moyenne du gène `germination_thermique` dans le pool-sol féral du plot pour
    cette espèce (`GeneStat.mean`). DÉFAUT 1.0 (neutre) si le plot n'a pas encore de
    pool de l'espèce ou si le gène n'y est pas tracé — chemin du golden au démarrage
    (pool vide ⇒ aucun décalage). Lecture pure, déterministe, sans RNG.

    C'est le pont SÉLECTION : le réensemencement (`add_species`, fields/seedbank)
    écrit déjà la valeur du gène des plantes qui grènent dans `GeneStat` — ici on la
    relit pour décaler l'optimum, donc le pool se durcit là où le froid mord."""
    rec = eco.seed_bank.species[r][c].get(plant_class)
    if not rec:
        return 1.0
    stat = rec["genes"].get("germination_thermique")
    return stat.mean if stat is not None else 1.0


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

        # Porte pH d'espèce (tronçon ⑤) : un grain planté HORS de sa fenêtre
        # d'acidité ne lève pas (une myrtille ne lève pas sur calcaire). Défaut
        # d'espèce NEUTRE (`ph_tol` large) ⇒ facteur ≈ 1.0. Chemin event-driven
        # (grains_en_attente VIDE au golden) → zéro impact golden.
        niche *= bell(eco.ph.at_plot(r, c), plant_class.ph_opt, plant_class.ph_tol)

        # Porte thermique de levée (tronçon ②, typée au ③) : un grain ne lève pas si la
        # T_sol est hors de sa fenêtre de germination. Plancher froid `T_GERM_FLOOR` (③)
        # AVANT la cloche : sous ~5 °C, court-circuit dur — aucune levée même pour une
        # espèce à `tol` large (zéro de végétation, pas de germination hivernale). Au-
        # dessus, cloche `bell(T_sol, t_germ_opt, t_germ_tol)` mordante selon le typage.
        # Gène `germination_thermique` (tronçon ④) : DÉCALE l'optimum effectif du
        # grain PROPRE (gène > 1 → optimum abaissé → lève plus au froid). Neutre 1.0
        # ⇒ `t_opt_eff == t_germ_opt` (chemin event-driven, grain absent au golden).
        t_sol = eco.temperature_sol.at_plot(r, c)
        if t_sol < T_GERM_FLOOR:
            continue                           # trop froid → la graine PATIENTE (FIFO conservé)
        gene = grain.genes.get("germination_thermique", 1.0)
        t_opt_eff = plant_class.t_germ_opt - GERM_GENE_SHIFT * (gene - 1.0)
        niche *= bell(t_sol, t_opt_eff, plant_class.t_germ_tol)

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
        if grain.expression:                   # priming hérité (④) : la graine naît pré-armée
            new_plant.expression.update(grain.expression)
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
            fertilite   = eco.fertilite_index(r, c)

            niche = eco.seed_bank.niche_index(
                r, c, light, root_density, disturbance, soil_deep
            )

            if niche < 0.01:
                continue

            # Fenêtre pH par espèce candidate (tronçon ⑤) : cloche de l'archétype
            # au pH LOCAL → porte de niche dans germination_candidates. Construite
            # par plot (le facteur dépend du pH du plot). Défaut NEUTRE (`ph_tol`
            # large) ⇒ ≈ 1.0 pour les adventices non spécifiées.
            ph = eco.ph.at_plot(r, c)
            arch_ph = {a: bell(ph, cls.ph_opt, cls.ph_tol)
                       for a, cls in WEED_CATALOGUE.items()}

            # Fenêtre thermique par espèce candidate (tronçon ②, typée au ③) : cloche de
            # l'archétype à la T_sol LOCALE → porte de niche dans germination_candidates.
            # Patron symétrique à arch_ph. Plancher froid `T_GERM_FLOOR` (③) : sous ~5 °C,
            # TOUS les archétypes à 0.0 (court-circuit dur, aucune levée férale hivernale) ;
            # au-dessus, cloche mordante selon le typage du catalogue.
            # Gène `germination_thermique` du POOL FÉRAL (tronçon ④) : l'optimum
            # effectif de chaque archétype candidat est décalé par la MOYENNE du
            # gène dans la banque-sol locale (`GeneStat.mean`, défaut 1.0 si le pool
            # / la clé est absent — pool féral encore neutre). C'est ce qui fait
            # ÉMERGER la sélection : un plot froid voit son pool dériver vers les
            # lève-tôt (gène > 1), donc son `t_opt_eff` s'abaisse saison après saison.
            t_sol = eco.temperature_sol.at_plot(r, c)
            if t_sol < T_GERM_FLOOR:
                arch_temp = {a: 0.0 for a in WEED_CATALOGUE}
            else:
                arch_temp = {
                    a: bell(t_sol,
                            cls.t_germ_opt - GERM_GENE_SHIFT
                            * (_germ_gene_mean(eco, r, c, cls) - 1.0),
                            cls.t_germ_tol)
                    for a, cls in WEED_CATALOGUE.items()}

            # Priorité écologique : sol pauvre → fixatrice, sinon ordre standard
            candidates = eco.seed_bank.germination_candidates(
                r, c, seed, week, niche, light=light,
                arch_tolerance=arch_tolerance, arch_ph=arch_ph, arch_temp=arch_temp
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
                e = eco.seed_bank.sample_expression(r, c, plant_class)
                if e:
                    new_plant.expression.update(e)   # priming hérité (④)
                log.append(
                    f"    🌿 Germination : {plant_class.name} @({r},{c}) "
                    f"[niche={niche:.3f} arch={chosen}]"
                )

    return log
