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

from constants import PLOT_CM
from plants import WEED_CATALOGUE, PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from fields import (SEED_ARCHETYPES, GRADIENT_ARCHETYPES, _hash_noise,
                    founder_genes, form_seed_at)
from fields.lifecycle import _smoothstep
from fields.ecofields import (bell, T_GERM_FLOOR, GERM_GENE_SHIFT,
                              COUVERTURE_ADVENTICE_SEUIL, PAILLAGE_GERM_SEUIL,
                              ALLELO_GERM_K, INOC_MOLENE_SEUIL)
from sim.capacite import recrutement_bloque

# Vis A (sprint PERF ③) — raideur de la réponse graduée « couverture → germination
# férale ». Le facteur appliqué à `niche` est (1 − couverture)**COUVERTURE_GERM_EXP :
# exposant 1 = décroissance linéaire ; > 1 = fenêtre qui se ferme PLUS VITE dès que
# le tapis s'épaissit (le couvert étouffe plus tôt). CALIBRÉ au ③ (sweeps 2 tuiles ×
# 10-14 ans) : exposant 4 + seuil dur abaissé à 0.5 amènent N à un PLATEAU stable
# (~190 pour 2 tuiles, oscillation saisonnière ~15 %, non croissante) là où
# exposant 2 laissait N dériver vers le haut. Le plateau VARIE par tuile
# (NO ~100 / N ~80 : fertilité/lumière → #7 préservée). Plot nu (couverture=0) →
# facteur 1.0 quel que soit l'exposant → golden neutre au démarrage.
COUVERTURE_GERM_EXP = 4.0

# Pression férale de base (sprint équilibre invasion ②, D69) — scalaire GLOBAL
# multipliant la probabilité de levée férale (`niche` → seuil de germination). La
# vis A (exposant couverture) ne mord que sur les plots MOYENNEMENT couverts ; la
# banque féral SATURE (density ≈ 1 sur sol mûr) donc la germination est limitée par
# la NICHE, pas par les taux d'enrichissement — d'où l'insensibilité des SEED_*_GAIN.
# Ce scalaire est le VRAI knob de plateau (« base de la vague de printemps ») : le
# baisser sous 1 réduit UNIFORMÉMENT la pression férale → onset plus lent (friche en
# ~2-3 saisons, pas < 1) ET plateau de N borné à l'échelle réelle 8 tuiles (~650 vs
# 1043+), SANS toucher le cutoff dur ni buffer les cultivées (philo #2 : on borne la
# PRESSION férale, flux → contrainte, pas de bonus direct sur les plantes). Calibré
# 8 tuiles (tools/diag_population + _mesure) → voir CONCEPTION_EQUILIBRE_INVASION §7.
# 1.0 = comportement historique (2 tuiles) ; < 1 = pression réduite.
GERM_PRESSION_FERALE = 0.30

# Placement sous-plot des germinations FÉRALES (sprint MODÈLE SPATIAL ①). Marge en
# cm garantissant que le plot-foyer reste inchangé : l'offset est borné à
# [OFFSET_MIN, PLOT_CM − OFFSET_MIN] → `floor(pos / PLOT_CM)` = plot d'origine → la
# CHIMIE du sol échantillonnée à 50 cm ne bouge pas. Fini le centrage systématique
# des semis spontanés (chantier A du sprint).
OFFSET_MIN = 10.0


def _offset_subplot(plant, seed: int, week: int) -> None:
    """Décale une plante DANS son plot-foyer, de façon DÉTERMINISTE (philo #3,
    zéro RNG). Positions bornées [OFFSET_MIN, PLOT_CM − OFFSET_MIN] dans chaque axe
    → `floor(pos / PLOT_CM)` reste le plot d'origine → chimie du sol stable (la
    position exacte raffine seulement QUELS plots la racine touche, gratuitement).

    Deux canaux de hash DÉDIÉS (`week × 53` / `week × 59`) décorrélés des autres
    usages de `_hash_noise` dans la succession (germination : `week × 7 + arch` ;
    grains : `hash_canal`) → l'offset ne biaise aucun autre tirage. `_hash_noise`
    renvoie ∈ [0, 1) → position ∈ [OFFSET_MIN, PLOT_CM − OFFSET_MIN)."""
    r, c = plant.position
    span = PLOT_CM - 2.0 * OFFSET_MIN
    u1 = _hash_noise(seed, week * 53, r, c)
    u2 = _hash_noise(seed, week * 59, r, c)
    plant.x_cm = c * PLOT_CM + OFFSET_MIN + u1 * span
    plant.y_cm = r * PLOT_CM + OFFSET_MIN + u2 * span


def _f_allelo(allelo: float, sensibilite: float) -> float:
    """Facteur d'escompte de niche à la germination sous allélopathie (sprint
    ALLÉLOPATHIE ②, D2/D6). RAMPE DOUCE continue, pas de seuil dur :

        rampe(x) = x / (x + ALLELO_GERM_K)          (Monod, saturante)
        f_allelo = 1 − sensibilite · rampe(allelo)  (borné [0,1])

    `allelo` = concentration du plot (`eco.allelopathie`), `sensibilite` = trait
    d'espèce `allelopathie_sensibilite` (1 = sensible standard, 0 = tolérant).
    INVARIANT GOLDEN : `allelo = 0` ⇒ `rampe(0) = 0` ⇒ `f_allelo = 1` ⇒ niche
    STRICTEMENT inchangée quelle que soit la sensibilité (K>0, aucun /0). Pur,
    déterministe, zéro RNG (philo #3). Court-circuit à 1.0 si le plot est propre
    (chemin du golden au repos) → aucun calcul superflu."""
    if allelo <= 0.0:
        return 1.0
    rampe = allelo / (allelo + ALLELO_GERM_K)
    return max(0.0, 1.0 - sensibilite * rampe)


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

    Priorité molène (sprint MÉMOIRE D'INOCULUM ③) : `disease_indicator` n'est un
    candidat QUE si la porte `arch_inoculum` s'est ouverte (inoculum du plot élevé) —
    sa seule présence signale une terre viciée, elle prime donc sur le gradient (elle
    prospère là où les autres tombent). Le rang cible se calcule sur `GRADIENT_ARCHETYPES`
    seul (les 4 classiques) → l'ajout de l'indicatrice ne déplace AUCUN choix des 4
    (golden INTACT) ; elle est de toute façon absente des candidats sur sol sain.
    """
    if "disease_indicator" in candidates:
        return "disease_indicator"
    if fertilite < 0.3 and "nitrogen_fixer" in candidates:
        return "nitrogen_fixer"
    rang_cible = soil_deep * (len(GRADIENT_ARCHETYPES) - 1)
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

        # Inhibition ALLÉLOPATHIQUE de la levée (tronçon ②) : un grain planté dans un
        # sol chargé d'allélochimiques (voisinage d'un noyer/armoise…) voit sa niche
        # escomptée par sa sensibilité d'espèce (rampe douce Monod). L'allélopathie
        # EFFECTIVE (④) = ambiant + AUTOTOXICITÉ du plot SI ce grain est de l'espèce
        # fatigante récurrente (la monoculture s'auto-inhibe la levée). Champ nul
        # (golden, aucun émetteur avant le ⑤ → autotox jamais armé) ⇒ f_allelo=1 ⇒
        # inchangé ; chemin event-driven de toute façon (grains_en_attente vide au
        # golden). Philo #2 : c'est le MILIEU (le champ de sol) qui bride la levée,
        # jamais un malus direct sur la plante.
        niche *= _f_allelo(eco.allelo_effectif(r, c, plant_class),
                           plant_class.allelopathie_sensibilite)

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
        # Placement sous-plot (① MODÈLE SPATIAL) — AVANT toute lecture de
        # root_plots/foliar_plots (mémoïsés sur (x_cm, y_cm, rayon) : écrire la
        # position ici invalide le cache par changement de clé). Un grain PLANTÉ
        # porte le pixel cliqué → on l'y place PILE ; un grain de test (sans pixel)
        # retombe sur l'offset féral déterministe.
        if grain.x_cm is not None and grain.y_cm is not None:
            new_plant.x_cm, new_plant.y_cm = grain.x_cm, grain.y_cm   # pixel cliqué exact
        else:
            _offset_subplot(new_plant, seed, week)                    # grain sans pixel → féral
        # Identité morphologique (② MODÈLE SPATIAL) : posée dès que la position est
        # connue → un clone de cette plante héritera de ce patron de branches.
        new_plant.form_seed = form_seed_at(seed, new_plant.x_cm, new_plant.y_cm, week)
        if grain.genes:
            new_plant.genes = dict(grain.genes)  # gènes PROPRES (≠ sample_genes du féral)
        else:
            # Graine SANS lignée (sachet magazine / démo) → tirage FONDATEUR (sprint
            # DIVERSITÉ FONDATRICE ①), plus un clone neutre. Une graine RÉCOLTÉE
            # (gènes hérités présents) garde les siens (branche ci-dessus).
            new_plant.genes = founder_genes(plant_class, seed, week, r, c,
                                            new_plant.x_cm, new_plant.y_cm)
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

    # Backstop PUR-perf (sprint PERF ③) : si la tuile a atteint le cap dur, on gèle
    # TOUT recrutement de ce tick (grains plantés + adventices férales). Disjoncteur
    # anti-pathologie, jamais atteint en jeu normal (cf. sim/capacite.py) → en
    # régime calibré ce court-circuit ne se prend pas, golden neutre.
    if recrutement_bloque(tile):
        log.append(f"    ⚠ cap perf tuile {tile.tile_id} atteint (recrutement gelé)")
        return log

    # Levée des graines plantées (event-driven) AVANT les adventices : un grain
    # déposé a priorité sur la germination spontanée du plot.
    log += _lever_grains_en_attente(game_state, tile, eco, week, seed,
                                    occupied_roots, niche_mult=1.0,
                                    hash_canal=week * 7 + 50)

    # Banc « monde propre » (sprint équilibre invasion ①, D69) : coupe la
    # germination férale SPONTANÉE. Les grains PLANTÉS ont déjà levé ci-dessus —
    # seule la vague férale du plot est gelée. Flag posé UNIQUEMENT par le preset
    # `config="propre"` du serveur ; ABSENT en smoke/full/bancs → `False` →
    # aucun court-circuit → golden inchangé (le moteur golden tourne hors serveur).
    if game_state.get("feral_off"):
        return log

    for r in range(tile.grid_rows):
        for c in range(tile.grid_cols):
            # Verrou d'occupation LEVÉ (Q1) : on ne saute plus les plots occupés.
            # Le frein vient des champs réels (lumière-sol ombragée + sol établi
            # déjà dans niche_index) — pas d'un terme « occupation » artificiel.
            if not tile.is_valid_plot(r, c):
                continue

            # Gate COUVERTURE DU SOL (sprint LUXURIANCE ①, D65 §2.1 ; RESSERRÉ au
            # sprint PERF ③, vis A). Un plot tapissé par un couvre-sol ÉTOUFFE la
            # levée SPONTANÉE des adventices — bénéfice permacole réel (le couvert
            # supprime la concurrence pionnière) ET frein de recrutement qui borne N
            # (arbitrage A). La réponse est désormais GRADUÉE (philo #2 : le flux
            # « ombre au sol du couvert » → la contrainte « fenêtre de germination
            # rétrécie » de façon continue, non plus un seuil binaire) : au-dessus du
            # seuil la levée reste totalement étouffée (cutoff dur conservé) ; EN
            # DESSOUS, `niche` est atténuée par (1 − couverture) → plus le tapis se
            # ferme, plus la fenêtre se resserre, jusqu'à l'extinction au seuil.
            # Déterministe (zéro RNG). N'affecte QUE la germination férale (les grains
            # PLANTÉS, geste délibéré, sont levés plus haut). Couverture nulle (golden
            # au démarrage, plots nus) → facteur 1.0 → germination inchangée.
            couverture = eco.couverture_sol.at_plot(r, c)
            if couverture >= COUVERTURE_ADVENTICE_SEUIL:
                continue

            # Gate PAILLAGE (sprint équilibre invasion ③, D69) — le LEVIER PERMACOLE
            # posé par le joueur : un plot MULCHÉ étouffe la levée férale (la graine
            # ne trouve ni lumière ni sol nu sous la couche de paille/BRF). Même patron
            # que la couverture (flux `paillage` → contrainte « fenêtre de germination
            # fermée », philo #2) : au-delà de PAILLAGE_GERM_SEUIL, cutoff DUR ; en
            # dessous, `niche` atténuée graduellement par (1 − paillage) plus bas. NE
            # touche QUE la germination férale (les grains PLANTÉS, geste délibéré, sont
            # levés plus haut). Paillage NUL (golden, aucun geste `pailler`) → passe →
            # facteur 1.0 → germination inchangée.
            paillage = eco.paillage.at_plot(r, c)
            if paillage >= PAILLAGE_GERM_SEUIL:
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

            # Vis A — frein de recrutement GRADUÉ par la couverture (sprint PERF ③) :
            # sous le seuil dur, la fenêtre de germination férale rétrécit avec le
            # couvert établi, en (1 − couverture)**COUVERTURE_GERM_EXP (raideur
            # calibrée). Plot nu (couverture=0) → ×1.0 (golden neutre au démarrage) ;
            # tapis dense → fenêtre quasi fermée bien avant le seuil dur.
            niche *= (1.0 - couverture) ** COUVERTURE_GERM_EXP
            niche *= GERM_PRESSION_FERALE   # base de la vague férale (②, D69)
            # Frein GRADUÉ du paillage (③, D69) — sous le seuil dur, la fenêtre de
            # germination férale rétrécit ∝ (1 − paillage) : plus le mulch est épais,
            # moins la graine férale lève, jusqu'à l'extinction au seuil. Paillage=0
            # (golden) → ×1.0. Le geste `pailler` du joueur borne ainsi l'invasion en
            # agissant sur le MILIEU (philo #1/#2), sans buffer les cultivées.
            niche *= (1.0 - paillage)
            # Frein ALLÉLOPATHIQUE de la nature (④, D9) — les aiguilles de conifère
            # libèrent des composés qui inhibent la levée EN PLUS de la barrière
            # physique : `niche *= 1 − allelo·paillage`. Paille/BRF → allelo 0 → ×1.0 ;
            # repos (nature "") → NATURE_NEUTRE → ×1.0 → golden INTACT.
            niche *= (1.0 - eco.nature_at(r, c)["allelo"] * paillage)

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

            # Inhibition ALLÉLOPATHIQUE par espèce candidate (tronçon ②, EFFECTIVE au
            # ④) : escompte de niche `f_allelo = 1 − sensibilité · rampe(allelo)` (rampe
            # douce Monod, cf. _f_allelo) → porte dans germination_candidates, patron
            # symétrique à arch_ph/arch_temp. L'allélopathie EFFECTIVE est lue PAR
            # ESPÈCE (`allelo_effectif`, ④) = ambiant + AUTOTOXICITÉ du plot si le
            # candidat EST l'espèce fatigante récurrente (une adventice émettrice qui
            # squatte le plot depuis des saisons voit SA propre levée bridée, pas celle
            # des autres). Défaut de sensibilité NEUTRE (1.0) à ce tronçon (calibrage
            # ⑤). Champ nul (golden, aucun émetteur → autotox jamais armé) ⇒ f=1.0 pour
            # tous ⇒ germination férale STRICTEMENT inchangée. Philo #2 : le champ de sol
            # referme la niche, pas de malus direct sur la plante.
            arch_allelo = {a: _f_allelo(eco.allelo_effectif(r, c, cls),
                                        cls.allelopathie_sensibilite)
                           for a, cls in WEED_CATALOGUE.items()}

            # Porte de RELÂCHE de la molène (sprint MÉMOIRE D'INOCULUM ③) : SEUL
            # l'archétype `disease_indicator` (bouillon-blanc, indicatrice de terre
            # malade) voit sa niche s'ouvrir ∝ inoculum TOTAL du plot ; tous les autres
            # restent à 1.0 neutre (elle ne REFERME jamais la niche des autres — patron
            # inverse de arch_ph/temp/allelo). smoothstep(total, SEUIL, 2·SEUIL) : ~0 sur
            # sol sain (inoculum nul → molène ne lève pas → golden INTACT), →1 sur un plot
            # durablement vicié. Rampe bornée au double du seuil (§10, calage F5).
            arch_inoculum = {a: 1.0 for a in WEED_CATALOGUE}
            arch_inoculum["disease_indicator"] = _smoothstep(
                eco.inoculum.total(r, c), INOC_MOLENE_SEUIL, 2.0 * INOC_MOLENE_SEUIL)

            # Priorité écologique : sol pauvre → fixatrice, sinon ordre standard
            candidates = eco.seed_bank.germination_candidates(
                r, c, seed, week, niche, light=light,
                arch_tolerance=arch_tolerance, arch_ph=arch_ph, arch_temp=arch_temp,
                arch_allelo=arch_allelo, arch_inoculum=arch_inoculum
            )

            if not candidates:
                continue

            # Choisir l'archétype ∝ maturité du sol (gradient succession)
            chosen = choisir_archetype(candidates, soil_deep, fertilite)

            plant_class = WEED_CATALOGUE.get(chosen)
            if not plant_class:
                continue

            # Germination — gènes échantillonnés du pool génétique du plot
            # (banque-sol féral). Pool vide → tirage FONDATEUR (sprint DIVERSITÉ
            # FONDATRICE ①) : la plante née sans lignée n'est plus un clone neutre,
            # elle reçoit sa variance propre déterministe (position continue,
            # philo #3). La mutation par génération prend ensuite le relais.
            new_plant = tile.add_plant(plant_class, r, c)
            if new_plant:
                # Placement sous-plot féral (① MODÈLE SPATIAL) — AVANT founder_genes
                # (qui LIT x_cm/y_cm) : la lignée fondatrice suit la position RÉELLE,
                # pas la position centrée. Plot-foyer inchangé (offset borné).
                _offset_subplot(new_plant, seed, week)
                # Identité morphologique héritable (② MODÈLE SPATIAL) — après la
                # position férale, avant la génétique (indépendantes).
                new_plant.form_seed = form_seed_at(seed, new_plant.x_cm,
                                                   new_plant.y_cm, week)
                g = eco.seed_bank.sample_genes(r, c, plant_class, seed, week)
                if not g:
                    g = founder_genes(plant_class, seed, week, r, c,
                                      new_plant.x_cm, new_plant.y_cm)
                new_plant.genes = g
                e = eco.seed_bank.sample_expression(r, c, plant_class)
                if e:
                    new_plant.expression.update(e)   # priming hérité (④)
                log.append(
                    f"    🌿 Germination : {plant_class.name} @({r},{c}) "
                    f"[niche={niche:.3f} arch={chosen}]"
                )

    return log
