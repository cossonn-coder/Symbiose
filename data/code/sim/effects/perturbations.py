"""
SYMBIOSE — sim/effects/perturbations.py
Perturbations écologiques de fond : nécromasse & squelette à la mort
(`deposer_mort`), fonte des semis (M4), maladies fongiques (M5), stress
hydrique sévère, herbivorie médiée par le champ ravageur visible (D31.2),
micro-mortalité déterministe, et l'orchestrateur `apply_disturbances`.

Toutes les morts passent par `deposer_mort` (squelette persistant, ②B) — point
d'entrée UNIQUE de la mort ; le retrait effectif est centralisé dans
`engine._tick_skeletons`. Déterminisme : tirages par `_hash_noise` (canaux
week·11 / week·13 / week·37 / week, décorrélés). Identique à l'ancien effects.py.
"""

from __future__ import annotations

from plants import PlantInstance
from world import Tile
import math

from fields import (_hash_noise, MORTALITY_RATE, climate_stress,
                    DAMPOFF_BASE, DAMPOFF_HUM_SEUIL, FUNGAL_BASE,
                    FUNGAL_VENT_DRY, FUNGAL_SPORE_GAIN, FUNGAL_INOC_SEUIL,
                    OIDIUM_BASE, OIDIUM_T_REF, OIDIUM_T_SPAN,
                    INOC_DEPOT_SEUIL, INOC_FROM_MEMORY, INOC_FROM_DEATH,
                    NECROMASS_PER_CM, FRAC_BOIS_MORT, VITALITE_STEP)
from .mutations import ReduceHealth, Mutation
from .resolution import apply_mutations


def necromass_biomass(plant: PlantInstance) -> float:
    """
    Nécromasse déposée à la mort ∝ hauteur (D27, décision #5). Un chêne mort
    rend bien plus de MO et ouvre une grande trouée qu'un semis. Remplace l'ancien
    barème par stade pour TOUTES les morts (pas la récolte, qui exporte).
    """
    return plant.current_height * NECROMASS_PER_CM


def tissu_mort(plant: PlantInstance) -> str:
    """Tissu de litière des parties MOLLES déposées à la mort (décompo·compost ②,
    kickoff §A.2). Un OVERRIDE d'espèce `litter_tissue` prime (sprint HYDROLOGIE ⑤ :
    la sphaigne dépose du `mousse`/tourbe, décompo quasi nulle). Sinon : les caducs
    (`deciduous`, perennials.py) larguent du `feuille` (décompo rapide), les autres de
    l'`herbace` (annuelles, tiges molles). Le bois du squelette se fragmente lentement
    (phase B) — pas ici. Golden NEUTRE : `litter_tissue` est None sur tout le catalogue
    hors sphaigne (jamais dans le smoke)."""
    override = plant.plant_class.litter_tissue
    if override is not None:
        return override
    return "feuille" if plant.plant_class.deciduous else "herbace"


def frac_bois_mort(plant: PlantInstance) -> float:
    """Fraction LIGNEUSE de la nécromasse (décompo·compost ②, phase B). Seules les
    plantes ligneuses (PerennialWoody, reconnues par l'attribut `age_curve`) laissent
    un squelette de bois qui se fragmente ; les herbacées/annuelles → 0 (tout en
    tissu mou, retrait immédiat — équivalent à l'ancien filtre is_alive)."""
    return FRAC_BOIS_MORT if getattr(plant.plant_class, "age_curve", None) else 0.0


def deposer_mort(plant: PlantInstance, eco) -> float:
    """Mort d'une plante → squelette persistant (CONCEPTION §2.2, phase B). Point
    d'entrée UNIQUE de la mort, remplace `add_necromass(∝ hauteur)` à tous les sites.

      1. dépose IMMÉDIATEMENT les tissus mous (litière typée, ∝ hauteur) au plot ;
      2. marque le squelette `seche` et réserve la part ligneuse dans `bois_restant`
         (fragmentée ensuite par `engine._tick_skeletons`) ;
      3. ne retire PAS la plante (le retrait est centralisé dans `_tick_skeletons`).

    IDEMPOTENT : si la plante est déjà `morte` (vue par un autre site de mort le même
    tick, ou un tick suivant), no-op → aucun double dépôt. Retourne la masse molle
    déposée (0.0 si déjà morte), pour les logs."""
    if plant.morte:
        return 0.0
    r, c = plant.position
    # Canal 2 — PULSE de résidu à la mort (mémoire d'inoculum ①, §2). Une plante
    # infectée qui meurt hiverne son inoculum dans ses débris → la terre reste malade
    # APRÈS la disparition de l'hôte (leçon sanitation : ne pas composter du matériel
    # malade). Déposé AVANT de perdre la référence, dans le bucket FAMILLE du plot.
    # Idempotent via le garde `plant.morte` ci-dessus (un seul dépôt). DORMANT au ① :
    # `inoculum` n'est lu par personne → golden INTACT.
    if plant.infection_memory > 0.0:
        eco.inoculum.deposit(r, c, plant.plant_class.family,
                             INOC_FROM_DEATH * plant.infection_memory)
    biomass = necromass_biomass(plant)
    fb = frac_bois_mort(plant)
    mous = biomass * (1.0 - fb)
    eco.deposer_litiere(r, c, tissu_mort(plant), mous)
    plant.morte = True
    plant.stade_mort = "seche"
    plant.bois_restant = biomass * fb
    plant.semaines_mort = 0
    return mous


def _local_density(plant: PlantInstance, tile: Tile, same_family: bool = False) -> float:
    """Densité de plantes vivantes voisines [0,1] (option : même famille seulement)."""
    r, c = plant.position
    # Voisinage 1-connexe calculé UNE fois (set → appartenance O(1)). Avant, la
    # comprehension ré-exécutait la BFS `plots_within_radius` à CHAQUE plante testée
    # (recalcul dans le tick + `in` sur une liste) → O(N²) sur une tuile dense. Le
    # set préserve l'ensemble ET l'ordre de `nearby` → résultat bit-identique.
    voisinage = set(tile.plots_within_radius(r, c, 1))
    nearby = [p for p in tile.plants
              if p.is_alive and p is not plant
              and p.position in voisinage]
    if same_family:
        n = sum(1 for p in nearby
                if p.plant_class.family == plant.plant_class.family)
    else:
        n = len(nearby)
    return min(1.0, n / 6.0)


def damping_off(plant: PlantInstance, tile: Tile, eco,
                seed: int, week: int, saison: str) -> list[Mutation]:
    """
    Fonte des semis (M4) — mort des semis en sol trop humide / dense / froid,
    atténuée par un microbiome vivant. Leçon permaculture : ne pas semer serré
    dans un sol froid et détrempé ; un sol vivant protège.
    """
    if not plant.is_alive or plant.stage.name != "semis":
        return []
    r, c = plant.position
    hum_norm = min(1.0, eco.humidite.at_plot(r, c) / 3.0)
    excess = max(0.0, hum_norm - DAMPOFF_HUM_SEUIL)
    if excess <= 0.0:
        return []
    density = _local_density(plant, tile)
    saison_factor = 1.0 if saison in ("printemps", "automne") else 0.4
    # Protection microbiome via la logistique existante (disease_probability).
    # `family` (inoculum ②) : la terre chargée de la MÊME famille aggrave la fonte
    # (mémoire édaphique hôte-spécifique). Plot vierge → amplif neutre (golden-safe).
    p = eco.disease_probability(r, c, base_rate=DAMPOFF_BASE,
                                family=plant.plant_class.family)
    p *= excess * (0.3 + density) * saison_factor
    # resistance_pathogene : un semis au phénotype résistant succombe moins (1/gène
    # EXPRIMÉ — un semis dont la lignée a vécu l'infection est primé, plasticité ②).
    p /= plant.expressed_gene("resistance_pathogene")
    if _hash_noise(seed, week * 11, r, c) < p:
        # Fonte = voie AIGÜE : tue net. L'amount (échelle entière) est calé pour que
        # `× VITALITE_STEP` en résolution retire toute la vitalité restante → mort.
        return [ReduceHealth(plant, plant.vitalite / VITALITE_STEP, reason="fonte des semis")]
    return []


def _spore_load(plant: PlantInstance, tile: Tile, wind_vec: tuple[float, float]) -> float:
    """Inoculum fongique reçu d'un FOYER infecté placé AU VENT (sprint VENT ⑥, §5.4).

    Le vent disperse les spores : une plante capte l'inoculum des voisins infectés
    situés DANS LA DIRECTION D'OÙ VIENT LE VENT (`wind_vec` = vecteur unitaire vers
    la source, convention `anemophilie._wind_from_vector`). Un voisin est « au vent »
    de la cible si (voisin − cible)·wind_vec > 0 → ses spores voyagent SOUS LE VENT
    jusqu'à la cible. On somme `infection_memory` (la charge pathogène VÉCUE = foyer
    actif) des voisins au-delà de `FUNGAL_INOC_SEUIL`, dans le MÊME voisinage 1-conn
    déjà calculé par `_local_density` (zéro nouvelle passe spatiale, garde-fou perf).

    À vent nul / aucun foyer au vent → 0.0 → pression fongique inchangée (rétro-compat
    golden : sans direction de vent passée, `wind_vec`=(0,0) annule tout terme)."""
    wx, wy = wind_vec
    if wx == 0.0 and wy == 0.0:
        return 0.0
    r, c = plant.position
    # Même voisinage 1-connexe que `_local_density`, calculé UNE fois (set → O(1)) :
    # avant, la BFS était ré-exécutée à chaque plante de la boucle (recalcul dans le
    # tick). Ensemble et parcours inchangés → charge d'inoculum bit-identique.
    voisinage = set(tile.plots_within_radius(r, c, 1))
    load = 0.0
    for p in tile.plants:
        if (not p.is_alive or p is plant
                or p.infection_memory < FUNGAL_INOC_SEUIL
                or p.position not in voisinage):
            continue
        dx, dy = p.x_cm - plant.x_cm, p.y_cm - plant.y_cm
        if dx * wx + dy * wy > 0.0:        # le foyer p est AU VENT de la cible
            load += p.infection_memory
    return load


def fungal_disease(plant: PlantInstance, tile: Tile, eco,
                   seed: int, week: int,
                   vent_local: float = 0.0,
                   wind_vec: tuple[float, float] = (0.0, 0.0)) -> list[Mutation]:
    """
    Maladies fongiques généralisées (M5) — pression ∝ humidité × densité de la
    MÊME famille (la monoculture propage) × susceptibilité familiale, atténuée
    par le microbiome. Le mildiou Solanacées (rondelle) reste un cas à part :
    ces familles ont juste la susceptibilité la plus élevée.

    Vent (sprint VENT ⑥, §5.4) — double tranchant, philo #2 (flux → contrainte) :
      • ASSÈCHEMENT protecteur : un feuillage bien venté sèche → pression × (1 −
        FUNGAL_VENT_DRY·vent_local). La ventilation (espacement, taille, brise-vent
        ajouré) devient un REMÈDE émergent → pédagogie aération permaculture.
      • DISPERSION des spores : un foyer infecté AU VENT (`_spore_load`) ajoute de
        l'inoculum → pression × (1 + FUNGAL_SPORE_GAIN·spore_load). Le mal voyage
        SOUS LE VENT (direction !).
    Défauts neutres (vent_local=0, wind_vec=(0,0)) → bit-identique à l'avant-⑥.
    """
    if not plant.is_alive or plant.stage.name == "semis":
        return []
    susc = getattr(plant.plant_class, "fungal_susceptibility", 0.5)
    if susc <= 0.0:
        return []
    # resistance_pathogene (phénotype individuel = génotype × expression) module la
    # susceptibilité familiale : gène EXPRIMÉ >1 → moins sensible. Deux sujets de la
    # même famille réagissent différemment (sélection émergente des lignées
    # résistantes, philo #2/#7) ET un sujet déjà infecté monte sa SAR (plasticité ②).
    susc /= plant.expressed_gene("resistance_pathogene")
    r, c = plant.position
    # HUMECTATION FOLIAIRE (sprint humectation ②) : le vrai signal de germination des
    # spores est l'eau LIQUIDE posée sur la feuille pendant des heures, pas l'humidité
    # du SOL. On lisait `humidite/3` — un proxy faux qui faisait monter la maladie quand
    # le joueur arrosait AU PIED (l'inverse de la règle permacole, philo #6). L'assèchement
    # direct du vent (FUNGAL_VENT_DRY, plus bas) est CONSERVÉ : léger double comptage du
    # vent assumé (il sèche aussi le feuillage dans wetness_memory ①) — le ⑥ calibrera.
    wet = plant.wetness_memory
    density = _local_density(plant, tile, same_family=True)
    # `family` (inoculum ②) : l'inoculum persistant de CETTE famille amplifie la
    # pression fongique (résidus hivernants). Rotation vers une autre famille échappe
    # à la charge (émergent). Plot vierge / INOC_GAIN=0 → amplif neutre (golden-safe).
    p = eco.disease_probability(r, c, base_rate=FUNGAL_BASE,
                                family=plant.plant_class.family)
    p *= wet * (0.4 + density) * susc
    # Vent (⑥) : assèchement protecteur PUIS apport de spores du foyer au vent.
    p *= max(0.0, 1.0 - FUNGAL_VENT_DRY * min(1.0, vent_local))
    spore = _spore_load(plant, tile, wind_vec)
    if spore > 0.0:
        p *= 1.0 + FUNGAL_SPORE_GAIN * spore
    if _hash_noise(seed, week * 13, r, c) < p:
        return [ReduceHealth(plant, 1, reason="maladie fongique", cause="maladie")]
    return []


def oidium_disease(plant: PlantInstance, tile: Tile, eco,
                   seed: int, week: int,
                   vent_local: float = 0.0) -> list[Mutation]:
    """
    Oïdium — la SECONDE guilde cryptogamique (sprint HUMECTATION FOLIAIRE ④, §2.4),
    biologiquement OPPOSÉE au mildiou. Presque toutes les cryptogames du feuillage
    (mildiou, rouille, tavelure, botrytis) exigent un FILM D'EAU liquide ; l'oïdium
    est l'exception notoire : il germe SANS eau libre, préfère un air humide avec un
    feuillage SEC, et l'eau libre lui est défavorable (elle fait éclater ses conidies).
    Son climat : nuits humides + journées chaudes et sèches, typiquement la fin d'été.

    SIGNAL INVERSE de `fungal_disease` : (1 − wetness_memory) × chaleur. Aérer et garder
    le feuillage sec écrase le mildiou MAIS ouvre la porte à l'oïdium ; asperger fait
    l'inverse → aucun geste universellement bon (le dilemme, philo #2/#6). Défaut
    `oidium_susceptibility = 0.0` → sortie immédiate (coût nul, golden neutre).

    Note : PAS de FUNGAL_VENT_DRY ici — le vent ne protège pas de l'oïdium (il aide
    même à disperser ses conidies). `vent_local` est accepté pour l'homogénéité de
    l'appel mais non consommé (ne pas ajouter d'assèchement protecteur : il tuerait
    le dilemme). Canal de bruit `week·47` (décorrélé de `fungal_disease`, week·13).
    """
    if not plant.is_alive or plant.stage.name == "semis":
        return []
    susc = getattr(plant.plant_class, "oidium_susceptibility", 0.0)
    if susc <= 0.0:
        return []                      # défaut 0.0 → sortie immédiate, coût nul
    # resistance_pathogene (D22b) médie les DEUX guildes — pas de gène neuf.
    susc /= plant.expressed_gene("resistance_pathogene")
    r, c = plant.position
    t_air = eco.temperature.at_plot(r, c)
    chaleur = max(0.0, min(1.0, (t_air - OIDIUM_T_REF) / OIDIUM_T_SPAN))
    if chaleur <= 0.0:
        return []                      # sous OIDIUM_T_REF : aucune pression (froid)
    # SIGNAL INVERSE du mildiou : feuillage SEC (1 − humectation) × chaleur.
    oidium_sig = (1.0 - plant.wetness_memory) * chaleur
    density = _local_density(plant, tile, same_family=True)
    p = eco.disease_probability(r, c, base_rate=OIDIUM_BASE,
                                family=plant.plant_class.family)
    p *= oidium_sig * (0.4 + density) * susc
    if _hash_noise(seed, week * 47, r, c) < p:
        return [ReduceHealth(plant, 1, reason="oïdium", cause="maladie")]
    return []


# --- Stress hydrique sévère (voie sécheresse → santé, Sprint gènes du vecteur) ---
# La sécheresse ne faisait jusqu'ici que STAGNER la croissance (gate ok_hum). On
# ajoute une voie de DÉGÂT : une sécheresse sévère ET prolongée (drought_memory
# élevée) abîme le tissu, médiée par le génotype — comme le gel. Donne une vraie
# pression de sélection sur tolerance_secheresse (philo #2/#7), sans bonus direct.
DROUGHT_DAMAGE_THRESHOLD = 0.6   # drought_memory au-delà de laquelle le tissu souffre
DROUGHT_DAMAGE_RATE      = 0.10  # probabilité de base à mémoire de stress saturée


def drought_stress_damage(plant: PlantInstance, eco,
                          seed: int, week: int) -> list[Mutation]:
    """
    Dégât du stress hydrique sévère prolongé (Sprint gènes du vecteur).

        sévérité = (drought_memory − seuil) / (1 − seuil)   [0,1] au-delà du seuil
        effectif = DROUGHT_DAMAGE_RATE × sévérité × (1 / tolerance_secheresse)

    drought_memory intègre lentement le déficit hydrique (_update_physiology) :
    seul un stress installé (pas une semaine sèche isolée) franchit le seuil. Le
    gène `tolerance_secheresse` réduit la susceptibilité (>1 → tissu plus résistant).
    Déterministe (_hash_noise, canal week·37, décorrélé des autres tirages du tick).
    """
    if not plant.is_alive:
        return []
    dm = plant.drought_memory
    if dm <= DROUGHT_DAMAGE_THRESHOLD:
        return []
    sev = (dm - DROUGHT_DAMAGE_THRESHOLD) / (1.0 - DROUGHT_DAMAGE_THRESHOLD)
    p = DROUGHT_DAMAGE_RATE * sev / plant.expressed_gene("tolerance_secheresse")
    r, c = plant.position
    if _hash_noise(seed, week * 37, r, c) < p:
        return [ReduceHealth(plant, 1, reason="stress hydrique sévère")]
    return []


# --- Carence lumineuse chronique (voie ombre → santé, miroir de la sécheresse) ---
# Symétrie réclamée par le terrain (Nico) : une plante laissée trop longtemps à
# l'ombre ne doit pas SEULEMENT stagner (gate ok_light, croissance.py) — elle doit
# stagner PUIS MOURIR, comme la sécheresse sévère. `shade_memory` intègre déjà
# lentement l'ombre vécue (_update_physiology) : seul un déficit lumineux INSTALLÉ
# franchit le seuil. La susceptibilité est l'INVERSE de la tolérance à l'ombre :
# un HÉLIOPHILE (tolérance < 1, ex. plante de pleine lumière) dépérit à l'ombre,
# un SCIAPHILE (> 1) tient. Médiée par le gène `tolerance_ombre` × la base d'espèce
# → vraie pression de sélection sur la sciaphilie (philo #2/#7), sans bonus direct.
# RESSERRÉ au sprint PERF ③ (vis B, self-thinning) : l'auto-éclaircie concourt au
# plafonnement de N (§4.1, loi de Yoda). Seuil LÉGÈREMENT abaissé (0.6→0.55 : un
# dominé entre en souffrance un peu plus tôt sous une ombre installée). Le TAUX
# reste 0.10, BORNÉ PAR HAUT par un invariant de design (test_stress_chronique) :
# un SCIAPHILE (tolérance à l'ombre haute) doit SURVIVRE à l'ombre profonde tandis
# qu'un héliophile y meurt (sélection émergente #7). Toute hausse du taux tue AUSSI
# le sciaphile (marge nulle mesurée au ③) → on n'y touche pas. AUCUN comptage de
# voisins : c'est la lumière reçue (déjà baissée par les dominantes via l'ombre
# LightField) qui porte la contrainte — flux → contrainte → réponse (philo #2). Les
# adventices férales sont d'ailleurs SCIAPHILES (base 1.25) → la vis B mord peu sur
# elles : le gros du plafonnement vient de la vis A (couverture→germination graduée),
# pas d'ici. On n'avance le curseur d'onset que dans la marge que l'invariant tolère.
SHADE_DAMAGE_THRESHOLD = 0.55  # shade_memory au-delà de laquelle le tissu souffre
SHADE_DAMAGE_RATE      = 0.10  # probabilité de base (plafonnée par l'invariant sciaphile, §test_stress_chronique)


def shade_stress_damage(plant: PlantInstance, eco,
                        seed: int, week: int) -> list[Mutation]:
    """
    Dégât de la carence lumineuse chronique (miroir de `drought_stress_damage`).

        sévérité = (shade_memory − seuil) / (1 − seuil)        [0,1] au-delà du seuil
        suscept. = 1 / (shade_tolerance_base × gene("tolerance_ombre"))
        effectif = SHADE_DAMAGE_RATE × sévérité × suscept.

    shade_memory intègre lentement le déficit lumineux (_update_physiology, lerp
    0.10) : une ombre passagère ne tue pas, seule une ombre INSTALLÉE franchit le
    seuil. Déterministe (_hash_noise, canal week·41, décorrélé des autres tirages).
    """
    if not plant.is_alive:
        return []
    sm = plant.shade_memory
    if sm <= SHADE_DAMAGE_THRESHOLD:
        return []
    tol = (plant.plant_class.shade_tolerance_base()
           * plant.expressed_gene("tolerance_ombre"))
    if tol <= 0.0:
        return []
    sev = (sm - SHADE_DAMAGE_THRESHOLD) / (1.0 - SHADE_DAMAGE_THRESHOLD)
    p = SHADE_DAMAGE_RATE * sev / tol
    r, c = plant.position
    if _hash_noise(seed, week * 41, r, c) < p:
        return [ReduceHealth(plant, 1, reason="carence lumineuse")]
    return []


# --- Herbivorie : la pression vient du champ RAVAGEUR visible (D31.2) ---
# Câblage D31.2 (docs/faune/vie_macro/conception_vie_macro.md §1/§2.2) : on referme la boucle vu↔agi.
# Avant, la pression était reconstruite d'un proxy (biomasse × diversité ×
# microbiome) et la régulation d'un second proxy `predator` (biodiv + rondelles +
# stabilité) — aucune entité visible. Désormais c'est le RAVAGEUR VISIBLE (le
# champ de population qui dessine les sprites) qui mord ; le champ qui DESSINE est
# le champ qui AGIT.
HERBIVORY_GAIN         = 0.20  # densité ravageur [0,1] → pression sur la santé (knob de calibrage, §8)
HERBIVORY_LETHAL_AUX   = 0.20  # densité auxiliaire en dessous de laquelle un foyer non régulé tourne au létal
HERBIVORY_LETHAL_MICRO = 0.20  # microbiome normalisé en dessous duquel le sol mort ne tamponne plus


def herbivory_pressure(plant: PlantInstance, tile: Tile,
                       game_state: dict, eco) -> list[Mutation]:
    """
    Pression herbivore = densité LOCALE du champ `ravageur` + de la `chenille`
    (larve du papillon, pont §D) (D31.2 + arc pollinisation ⑤).

        pression = (ravageur[r,c] + chenille[r,c]) · HERBIVORY_GAIN

    Le champ ravageur intègre DÉJÀ sa régulation par les auxiliaires (sa survie
    est rabotée par la densité du champ `auxiliaire` à chaque tick, cf.
    fields/population.py) → lire le ravageur, c'est lire une pression DÉJÀ
    régulée : pas de second multiplicateur (donc pas de double comptage de
    l'auxiliaire). L'auxiliaire est lu DIRECTEMENT seulement pour la bascule
    LÉTALE (un foyer non régulé sur sol mort).

    Boucle d'apprentissage (docs/faune/vie_macro/conception_vie_macro.md §1) : je vois les ravageurs →
    mes plantes souffrent là où leur densité est haute → j'installe de l'habitat →
    les auxiliaires arrivent → le champ ravageur reflue → mes plantes récupèrent.
    """
    if not plant.is_alive:
        return []

    r, c = plant.position
    rav = eco.category_density("ravageur", r, c) if eco else 0.0
    # Pont de cycle de vie §D (tronçon ⑤) : la chenille (larve du papillon) broute
    # le feuillage → s'AJOUTE à la pression du ravageur. À chenille=0 (aucune ponte)
    # → +0 → pression strictement inchangée vs avant ⑤ (invariant golden §D.6).
    chen = (eco.larvae["chenille"].at_plot(r, c)
            if eco and "chenille" in getattr(eco, "larvae", {}) else 0.0)
    pressure = (rav + chen) * HERBIVORY_GAIN

    # ───────── SUPPLANTÉ D31.2 — conservé pour mémoire ─────────
    # Ancien modèle (proxies sans entité visible). La pression dérivait de la
    # biomasse locale ; la régulation d'un terme `predator` agrégé (biodiversité +
    # rondelles pollinisateur/auxiliaire + stabilité). Les deux sont remplacés par
    # la lecture directe des champs de population (ravageur ci-dessus, auxiliaire
    # pour la bascule létale ci-dessous). Cf. docs/faune/vie_macro/conception_vie_macro.md §1/§2.2, D27.
    #
    # nearby = [p for p in tile.plants
    #           if p.is_alive and p.current_stage >= 2
    #           and p.position in tile.plots_within_radius(r, c, 1) + [plant.position]]
    # biomass_local = len(nearby) / 6.0
    # families = {p.plant_class.family for p in nearby}
    # biodiversity_index = min(1.0, len(families) / 4.0)
    # pollin    = min(1.0, tile.get_rondelle_count("pollinisateur") / 3.0)
    # aux_rond  = min(1.0, tile.get_rondelle_count("auxiliaire") / 3.0)
    # stability = 1.0 - (eco.disturbance.at_plot(r, c) if eco else 0.5)
    # predator  = min(1.0, 0.4 * biodiversity_index + 0.2 * pollin
    #                      + 0.15 * stability + 0.4 * aux_rond)
    # pressure  = (biomass_local * HERBIVORY_BASE
    #              * max(0.0, 1.0 - micro_norm)
    #              * max(0.0, 1.0 - predator))
    # ───────────────────────────────────────────────────────────

    if pressure < 0.005:
        return []

    # Microbiome + auxiliaire locaux → bascule LÉTALE (lecture directe des champs).
    micro_norm = min(1.0, eco.microbiome.at_plot(r, c) / 3.0) if eco else 0.3
    aux = eco.category_density("auxiliaire", r, c) if eco else 0.0

    # Application probabiliste sur la santé
    mutations = []
    if pressure > plant.stress_memory * 0.5:
        # La plante stressée résiste mieux (paradoxe biologique)
        effective_pressure = pressure * max(0.3, 1.0 - plant.stress_memory * 0.5)
        if effective_pressure > 0.015:
            # Ravageurs LÉTAUX (M6) : foyer non régulé (peu d'auxiliaires) sur sol
            # mort (microbiome bas) → dégâts doublés, mort possible.
            lethal = (aux < HERBIVORY_LETHAL_AUX
                      and micro_norm < HERBIVORY_LETHAL_MICRO)
            mutations.append(ReduceHealth(
                plant, 2 if lethal else 1,
                reason=f"herbivorie p={pressure:.3f}"
            ))
    return mutations


# --- Herbivorie RACINAIRE : le champ herbivore_vertebre (campagnol) ronge sous terre ---
# Canal DÉDIÉ (sommet trophique ①, Q3), distinct de `herbivory_pressure` : le
# campagnol broute racines/bulbes/écorce, PAS le feuillage. Sa pression lit la
# catégorie `herbivore_vertebre` (agrégée comme `ravageur`) sur l'empreinte du plot
# de la plante. Sprint SANTÉ & RÉSILIENCE ③ (§3) : l'usure chronique ne passe PLUS
# par un `ReduceHealth` plat (avalé par `_cap_chronique`, philo #2 bafouée). Le
# campagnol AFFAME la plante — racines rongées → perte d'UPTAKE (mémoire
# `root_herbivory_memory` → `plant_uptake`) → souffrance par les voies eau/azote
# EXISTANTES. Cette fonction ne conserve donc QUE la bascule LÉTALE d'annélation
# (écorce du jeune ligneux tranchée tout autour → sève coupée), traitée en mort
# MÉCANIQUE directe (`vitalite = 0`, bypass `erode` : un sectionnement ne se divise
# pas par la constitution). Signe visible propre : `rongeur_racinaire` (semiologie,
# lit la densité, INCHANGÉ). À densité `herbivore_vertebre` nulle (aucun campagnol)
# → aucune mutation, aucune mort → golden NEUTRE. Placeholders, calibrage post-test.
ROOT_HERBIVORY_LETHAL = 0.55  # densité campagnol au-delà de laquelle un JEUNE ligneux annelé meurt
LIGNEUX_ANNELE_CM     = 250.0 # hauteur en deçà de laquelle l'écorce est annelable (miroir LIGNEUX_JEUNE_CM)


def root_herbivory(plant: PlantInstance, tile: Tile,
                   game_state: dict, eco, seed: int, week: int) -> list[Mutation]:
    """Annélation LÉTALE du campagnol (sprint santé & résilience ③, §3).

    L'usure chronique de l'herbivorie racinaire est repliée sur l'UPTAKE
    (`root_herbivory_memory` → `plant_uptake`, philo #2 : le campagnol affame par un
    FLUX réduit, pas par un malus de santé plat). Il ne reste ICI que le régime AIGU :
    un JEUNE ligneux (écorce annelable) sous FORTE densité (≥ LETHAL) voit son collet
    rongé tout autour → la sève est coupée → mort CERTAINE et MÉCANIQUE. On met
    `vitalite = 0` DIRECT (bypass `erode` : un sectionnement ne se divise pas par la
    constitution d'espèce, cf. gestes joueur). La plante devient `not is_alive` → sa
    nécromasse est déposée par le balayage `deposer_mort` de fin de tick (point de
    mort UNIQUE). Ne renvoie donc PLUS aucune mutation. Flux respecté (#1/#2)."""
    if not plant.is_alive or eco is None:
        return []
    r, c = plant.position
    dens = eco.category_density("herbivore_vertebre", r, c)
    # Annélation létale : jeune ligneux (écorce tendre) sous forte densité — certaine.
    jeune_ligneux = (getattr(plant.plant_class, "age_curve", None)
                     and plant.current_height <= LIGNEUX_ANNELE_CM)
    if jeune_ligneux and dens >= ROOT_HERBIVORY_LETHAL:
        plant.vitalite = 0.0   # mort mécanique directe (sectionnement) — bypass erode
    return []


def background_mortality(plant: PlantInstance, eco,
                         seed: int, week: int) -> list[Mutation]:
    """
    Micro-mortalité aléatoire déterministe.
    Bruit spatial → affaiblissement spontané (pas de mort brutale).

    noise = hash(seed, week, r, c)
    if noise < MORTALITY_RATE → health *= 0.7 (arrondi à l'entier inférieur)

    Prevents perfect optimization — le jardin reste imprévisible.
    """
    if not plant.is_alive:
        return []

    r, c = plant.position
    noise = _hash_noise(seed, week, r, c)

    # Le stress mémorisé réduit la mortalité (plante endurcie) ; les sujets
    # ÉTABLIS (grande taille) résistent fortement — la mortalité de fond frappe
    # surtout les jeunes/petits (démographie végétale réaliste, D27). Un arbre
    # adulte ne meurt donc quasi que de sénescence.
    establishment = min(1.0, plant.current_height / 200.0)
    adjusted_rate = (MORTALITY_RATE
                     * max(0.2, 1.0 - plant.stress_memory * 0.6)
                     * (1.0 - 0.8 * establishment))

    if noise < adjusted_rate:
        # Affaiblissement déterministe : ancien effet ×0.7 sur la santé → on retire
        # 30 % de la vitalité courante. Amount à l'échelle entière (÷ VITALITE_STEP)
        # pour que la résolution le reconvertisse. Plus de plancher `int()` : l'usure
        # est fractionnaire (une plante déjà basse peut passer à 0 → mort, comme avant).
        perte = plant.vitalite * 0.3 / VITALITE_STEP
        if perte > 0:
            return [ReduceHealth(
                plant,
                perte,
                reason=f"mortalité de fond (noise={noise:.3f})"
            )]
    return []


def _cap_chronique(chronic_muts: list[Mutation]) -> list[Mutation]:
    """Borne à −1 santé/tick/plante le cumul des voies de fond CHRONIQUES
    (② sprint « usure, pas punition », philo #6).

    Sur l'échelle santé entière 0-3, plusieurs `ReduceHealth` indépendants
    empilés dans un même tick pouvaient passer 3→0 (mort-éclair). Ici, pour
    chaque plante, on ne garde QU'UN seul `ReduceHealth` d'`amount=1` — le
    premier de la plante, en PRIVILÉGIANT un coup porteur de `cause` non vide
    (pour préserver la marque foliaire de la sémiologie ②). L'ordre de la liste
    est préservé (déterminisme, zéro RNG). Les voies aiguës (fonte des semis)
    ne passent PAS par ici → restent décisives."""
    retenu: dict[int, ReduceHealth] = {}       # id(plante) → coup conservé
    for m in chronic_muts:
        pid = id(m.plant)
        garde = retenu.get(pid)
        # Premier coup de la plante, OU premier coup à `cause` non vide qui
        # remplace un coup sans cause déjà retenu (préserve la sémiologie).
        if garde is None or (not garde.cause and m.cause):
            retenu[pid] = ReduceHealth(m.plant, 1, reason=m.reason, cause=m.cause)
    return list(retenu.values())


def apply_disturbances(tile, eco, game_state: dict,
                       seed: int, week: int,
                       year_fraction: float, saison: str = "",
                       vent_dir: float = 0.0,
                       vent_force: float = 0.0) -> list[str]:
    """
    Applique toutes les perturbations de fond pour un tick.
    Appelée après la croissance et les effets biotiques.

    Order :
      1. Oscillation climatique (modifie evaporation in-tick via growth_modifier)
      2. Herbivorie diffuse + ravageurs létaux (M6)
      3. Fonte des semis (M4) + maladies fongiques (M5)
      4. Micro-mortalité déterministe
      5. Mise à jour stress_memory des plantes
      6. Nécromasse ∝ hauteur (D27) pour les morts du tick, puis nettoyage
    """
    log = []

    # 1. Stress climatique de fond (influence affichée si notable)
    c_stress = climate_stress(year_fraction)
    if abs(c_stress) > 0.04:
        sign = "↑" if c_stress > 0 else "↓"
        log.append(f"    🌡 Oscillation climatique : {c_stress:+.3f} "
                   f"(croissance {sign})")

    # Vecteur de vent (⑥, §5.4) : unité vers la SOURCE du vent (convention
    # anemophilie._wind_from_vector), utilisé par fungal_disease pour repérer le
    # foyer infecté AU VENT. Vent nul → (0,0) → aucun transport de spores → la
    # maladie fongique reste strictement à l'avant-⑥ (assèchement = 0 aussi).
    wind_vec = ((math.cos(vent_dir), math.sin(vent_dir))
                if vent_force > 0.0 else (0.0, 0.0))

    # 2 & 3. Perturbations par plante
    # Deux flux SÉPARÉS (② cap létalité chronique, sprint « usure, pas punition ») :
    #   • AIGU (fonte des semis) → passe INTACT, une fonte peut emporter un semis ;
    #   • CHRONIQUE (herbivorie, fongique, sécheresse, ombre, mortalité de fond) →
    #     borné à −1 santé/tick/plante (cf. `_cap_chronique`) → une plante saine
    #     (health 3) tient ≥ 3 ticks de fond avant de mourir = usure (philo #6),
    #     jamais 3→0 d'un coup. L'ordre d'APPEL des fonctions est INCHANGÉ (les
    #     tirages `_hash_noise` restent corrélés au golden) : seule la VENTILATION
    #     des mutations produites dans deux listes change.
    acute_muts = []
    chronic_muts = []
    for plant in list(tile.plants):
        if not plant.is_alive:
            continue
        # Herbivorie + ravageurs létaux (chronique)
        chronic_muts += herbivory_pressure(plant, tile, game_state, eco)
        # Herbivorie RACINAIRE (campagnol, canal dédié — sprint santé & résilience ③).
        # L'usure chronique est repliée sur l'UPTAKE (root_herbivory_memory, philo #2) ;
        # il ne reste ici que l'annélation LÉTALE, appliquée en mort mécanique DIRECTE
        # (vitalite=0, aucune mutation renvoyée). À densité `herbivore_vertebre` nulle →
        # aucune mort → invariant golden pour ce terme.
        root_herbivory(plant, tile, game_state, eco, seed, week)
        # Fonte des semis (AIGU, non capé) + maladies fongiques (chronique)
        acute_muts += damping_off(plant, tile, eco, seed, week, saison)
        vl = eco.vent.at_plot(*plant.position) if eco and eco.vent else 0.0
        chronic_muts += fungal_disease(plant, tile, eco, seed, week, vl, wind_vec)
        # Oïdium — SECONDE guilde, signal INVERSE (feuillage SEC × chaleur). Chronique
        # (capée comme le mildiou). À `oidium_susceptibility` nulle (défaut catalogue)
        # → sortie immédiate → invariant golden pour ce terme.
        chronic_muts += oidium_disease(plant, tile, eco, seed, week, vl)
        # Stress hydrique sévère (voie sécheresse → santé, médiée par génotype)
        chronic_muts += drought_stress_damage(plant, eco, seed, week)
        # Carence lumineuse chronique (voie ombre → santé, médiée par tolerance_ombre)
        chronic_muts += shade_stress_damage(plant, eco, seed, week)
        # Mortalité de fond (chronique)
        chronic_muts += background_mortality(plant, eco, seed, week)
        # Canal 1 — dépôt CONTINU de la mémoire d'inoculum (①, §2). Une plante
        # infectée vivante (infection_memory au-dessus du seuil) vicie SON plot dans
        # le bucket de SA famille, ∝ l'excès de charge. Piggyback sur cette passe
        # par-plante déjà existante (zéro nouvelle boucle spatiale, garde-fou perf).
        # DORMANT au ① : `inoculum` n'est lu par personne → golden INTACT.
        if eco is not None and plant.infection_memory > INOC_DEPOT_SEUIL:
            r, c = plant.position
            eco.inoculum.deposit(
                r, c, plant.plant_class.family,
                INOC_FROM_MEMORY * (plant.infection_memory - INOC_DEPOT_SEUIL))

    log += apply_mutations(acute_muts + _cap_chronique(chronic_muts), game_state)

    # 4. Mise à jour stress_memory (intégration lente)
    for plant in tile.plants:
        if not plant.is_alive:
            continue
        r, c = plant.position
        disturbance_local = eco.disturbance.local(r, c) if eco else 0.1
        # Paradoxe biologique : stress↑ → résistance↑ à terme
        plant.stress_memory += (disturbance_local - plant.stress_memory) * 0.08
        plant.stress_memory = max(0.0, min(1.0, plant.stress_memory))

    # Morts du tick (fond / fonte / fongique / ravageurs) → squelette persistant
    # (②B). `deposer_mort` est idempotent : un sujet déjà marqué mort plus tôt dans
    # le tick (sénescence, conflit…) est ignoré ici (zéro double dépôt). Aucun
    # retrait : le seul point de retrait est `engine._tick_skeletons`.
    for plant in tile.plants:
        if not plant.is_alive:
            deposer_mort(plant, eco)

    return log
