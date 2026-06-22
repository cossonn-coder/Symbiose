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
from fields import (_hash_noise, MORTALITY_RATE, climate_stress,
                    DAMPOFF_BASE, DAMPOFF_HUM_SEUIL, FUNGAL_BASE,
                    NECROMASS_PER_CM, FRAC_BOIS_MORT)
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
    kickoff §A.2). Les caducs (`deciduous`, perennials.py) larguent du `feuille`
    (décompo rapide), les autres de l'`herbace` (annuelles, tiges molles). Le bois
    du squelette se fragmente lentement (phase B) — pas ici."""
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
    nearby = [p for p in tile.plants
              if p.is_alive and p is not plant
              and p.position in tile.plots_within_radius(r, c, 1)]
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
    # Protection microbiome via la logistique existante (disease_probability)
    p = eco.disease_probability(r, c, base_rate=DAMPOFF_BASE)
    p *= excess * (0.3 + density) * saison_factor
    # resistance_pathogene : un semis au phénotype résistant succombe moins (1/gène
    # EXPRIMÉ — un semis dont la lignée a vécu l'infection est primé, plasticité ②).
    p /= plant.expressed_gene("resistance_pathogene")
    if _hash_noise(seed, week * 11, r, c) < p:
        return [ReduceHealth(plant, plant.health, reason="fonte des semis")]
    return []


def fungal_disease(plant: PlantInstance, tile: Tile, eco,
                   seed: int, week: int) -> list[Mutation]:
    """
    Maladies fongiques généralisées (M5) — pression ∝ humidité × densité de la
    MÊME famille (la monoculture propage) × susceptibilité familiale, atténuée
    par le microbiome. Le mildiou Solanacées (rondelle) reste un cas à part :
    ces familles ont juste la susceptibilité la plus élevée.
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
    hum_norm = min(1.0, eco.humidite.at_plot(r, c) / 3.0)
    density = _local_density(plant, tile, same_family=True)
    p = eco.disease_probability(r, c, base_rate=FUNGAL_BASE)
    p *= hum_norm * (0.4 + density) * susc
    if _hash_noise(seed, week * 13, r, c) < p:
        return [ReduceHealth(plant, 1, reason="maladie fongique", cause="maladie")]
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
SHADE_DAMAGE_THRESHOLD = 0.6   # shade_memory au-delà de laquelle le tissu souffre
SHADE_DAMAGE_RATE      = 0.10  # probabilité de base à mémoire d'ombre saturée


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
# Câblage D31.2 (CONCEPTION_VIE_MACRO.md §1/§2.2) : on referme la boucle vu↔agi.
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

    Boucle d'apprentissage (CONCEPTION_VIE_MACRO.md §1) : je vois les ravageurs →
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
    # pour la bascule létale ci-dessous). Cf. CONCEPTION_VIE_MACRO.md §1/§2.2, D27.
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
        # Affaiblissement déterministe. Plancher levé (D27) : sur une plante déjà
        # à health=1, le coup peut atteindre 0 → mort. Reste rare (modulé par
        # stress_memory) et ne touche en pratique que les sujets déjà affaiblis.
        new_health = int(plant.health * 0.7)
        if new_health < plant.health:
            return [ReduceHealth(
                plant,
                plant.health - new_health,
                reason=f"mortalité de fond (noise={noise:.3f})"
            )]
    return []


def apply_disturbances(tile, eco, game_state: dict,
                       seed: int, week: int,
                       year_fraction: float, saison: str = "") -> list[str]:
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

    # 2 & 3. Perturbations par plante
    all_mutations = []
    for plant in list(tile.plants):
        if not plant.is_alive:
            continue
        # Herbivorie + ravageurs létaux
        all_mutations += herbivory_pressure(plant, tile, game_state, eco)
        # Fonte des semis + maladies fongiques
        all_mutations += damping_off(plant, tile, eco, seed, week, saison)
        all_mutations += fungal_disease(plant, tile, eco, seed, week)
        # Stress hydrique sévère (voie sécheresse → santé, médiée par génotype)
        all_mutations += drought_stress_damage(plant, eco, seed, week)
        # Carence lumineuse chronique (voie ombre → santé, médiée par tolerance_ombre)
        all_mutations += shade_stress_damage(plant, eco, seed, week)
        # Mortalité de fond
        all_mutations += background_mortality(plant, eco, seed, week)

    log += apply_mutations(all_mutations, game_state)

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
