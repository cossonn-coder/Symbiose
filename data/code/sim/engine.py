"""
SYMBIOSE — sim/engine.py v3
Moteur de simulation écologique — 52 semaines, 4 saisons.

Tick order :
  1. Aléas (début de saison)
  2. Lumière directionnelle (projection ombres)
  3. Diffusion écologique (humidité > fertilité > microbiome)
  4. Avancement des stades (conditionné lumière + humidité)
  5. Effets weekly (flux écologiques + discrets probabilistes)
  6. Uptake racinaire
  7. Floraison / Récolte
  8. Conflits spatiaux
  9. Soil memory (fin de saison uniquement)
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from world import Tile
from plants import (PlantInstance, Tomato, Basil, Bean, Clover,
                    Sunflower, Pepper, PLANT_CATALOGUE)
from sim.effects import (resolve_plant_turn, apply_mutations, AddRondelle,
                         RemoveRondelle, ReduceHealth, InjectField,
                         apply_disturbances, necromass_biomass)
from fields import (EcoFields, init_eco, inject_patch,
                    EXUDATE_BASE, EXUDATE_OM_SHARE,
                    _hash_noise, SENESCENCE_ONSET, SEN_RATE,
                    HEAL_RATE, HEAL_SEN_CUTOFF, RESEED_RADIUS_CM)
from sim.reproduction import find_father, child_genes, is_seed_bearing
from sim.seeds import Seed
from sim.succession import succession, spring_flush
from sim.weather import (weather_at, WeatherEvent, K_PEST,
                         temp_norm, temperature_delta, TEMP_DRIVEN)
from sim.vigueur import tick_player_vigueur, refill_saison
from sim.growth import grow_plant

# Pont récolte → banque-joueur (D17) : classe → clé catalogue (inverse).
_SPECIES_KEY = {cls: key for key, cls in PLANT_CATALOGUE.items()}

SAISONS = {
    "printemps": range(1,  14),
    "ete":       range(14, 27),
    "automne":   range(27, 40),
    "hiver":     range(40, 53),
}
PHASES_ACTIVES = {"printemps", "ete", "automne"}

def saison_de(week):
    for nom, r in SAISONS.items():
        if week in r: return nom
    return "hiver"

def est_debut_saison(week):
    return any(week == r.start for r in SAISONS.values())

def est_fin_saison(week):
    return any(week == r.stop - 1 for r in SAISONS.values())

def est_phase_floraison(week, saison):
    if saison not in PHASES_ACTIVES: return False
    r = SAISONS[saison]
    return week == r.start + len(r) // 2

def est_phase_recolte(week, saison):
    if saison not in PHASES_ACTIVES: return False
    return week == SAISONS[saison].stop - 1

@dataclass
class Alea:
    nom: str; description: str
    variable: str; delta: float; mode: str = "field"

# Ancien catalogue météo, conservé pour mémoire. SUPPLANTÉ (sous-sprint 01) par
# weather_at(seed, week) + WEATHER_ALEA ci-dessous : le tirage n'est plus un
# random.choice live mais une fonction pure déterministe (CONCEPTION_METEO.md §0).
ALEAS_METEO = [
    Alea("Canicule",     "Humidité chute.",    "humidite",  -0.4, "field"),
    Alea("Pluies",       "Humidité monte.",     "humidite",  +0.5, "field"),
    Alea("Gelée tardive","Semis touchés.",      "",          -1.0, "health"),
    Alea("Beau temps",   "Aucun effet.",        "",           0.0, "none"),
    Alea("Vent fort",    "Paillage dispersé.",  "paillage",  -1,   "rondelle"),
    Alea("Brouillard",   "Risque maladie.",     "maladie",   +1,   "rondelle"),
]

# Couplage PROVISOIRE (sous-sprint 01) : WeatherEvent.kind → effet Alea EXISTANT.
# On réutilise STRICTEMENT les effets déjà en place (humidité/paillage/santé)
# pour préserver le couplage le temps de la déterminisation. Plusieurs kinds du
# catalogue §1.3 mappent sur le même effet faute de mieux (Sécheresse≈Canicule,
# Grêle≈dégât santé, Redoux=neutre) : la température (02) et les réponses médiées
# par gène (03) remplaceront ces mappings approximatifs.
WEATHER_ALEA = {
    "Beau temps":      Alea("Beau temps",      "Aucun effet.",       "",         0.0, "none"),
    "Gelée tardive":   Alea("Gelée tardive",   "Semis touchés.",     "",        -1.0, "health"),
    "Canicule":        Alea("Canicule",        "Humidité chute.",    "humidite", -0.4, "field"),
    "Sécheresse":      Alea("Sécheresse",      "Humidité chute.",    "humidite", -0.4, "field"),
    "Tempête":         Alea("Tempête",         "Paillage dispersé.", "paillage", -1,   "rondelle"),
    # Grêle : SUPPLANTÉ (sous-sprint 03). Ne passe plus par la voie `health` plate ;
    # routé via _mediated_damage (impact physique × exposition × protection). Entrée
    # conservée pour mémoire — n'est plus consultée par tick_semaine (cf. CLAUDE.md
    # « ne jamais jeter de code »).
    "Grêle":           Alea("Grêle",           "Feuillage abîmé.",   "",        -1.0, "health"),
    "Pluie prolongée": Alea("Pluie prolongée", "Humidité monte.",    "humidite", +0.5, "field"),
    "Redoux":          Alea("Redoux",          "Aucun effet.",       "",         0.0, "none"),
}
ALEAS_RAVAGEURS = [
    Alea("Pucerons",  "Fertilité réduite.", "fertilite", -0.3, "field"),
    Alea("Limaces",   "Semis grignotés.",   "",          -1.0, "health"),
    Alea("Doryphores","Maladie augmente.",  "maladie",    +1,  "rondelle"),
    Alea("Calme",     "Aucun ravageur.",    "",            0.0, "none"),
    Alea("Chenilles", "Feuillage abîmé.",  "",           -1.0, "health"),
]

# --- Réponses médiées par le milieu (CONCEPTION_METEO.md §2.3) -------------
# Gel et grêle ne frappent plus « à plat » (ancienne voie `health`, à la limite
# de la philo #2). Le dégât subi par un individu ÉMERGE de son état et de son
# génotype :
#     dégât = sévérité_milieu × susceptibilité_génétique × (1 − protection)
# Deux semis voisins réagissent différemment selon leur gène de rusticité et le
# paillage local. Conséquence émergente recherchée : sur plusieurs générations,
# le gel élague les lignées peu rustiques → sélection naturelle du froid (philo
# #2/#7), sans aucun bonus/malus direct.
TEMP_FROST_DAMAGE  = 0.0    # °C — sous ce seuil, le tissu tendre exposé gèle
FROST_SEVERITY_REF = 6.0    # °C sous 0 donnant une sévérité de référence ≈ 1
HAIL_SEVERITY_REF  = 1.45   # intensité (σ) de grêle donnant une sévérité ≈ 1
PAILLAGE_PROTECT   = 0.25   # chaque rondelle paillage retire 25 % du dégât (cap 1)
DAMAGE_STEP        = 0.55   # dégât effectif → points de santé perdus (floor)


def appliquer_alea(alea, tile, eco, game_state):
    log = []
    if alea.mode == "none": return log
    if alea.mode == "field":
        eco.apply_weather(alea.variable, alea.delta)
        sign = "+" if alea.delta > 0 else ""
        log.append(f"    → {alea.variable} {sign}{alea.delta:.2f} (champ)")
    elif alea.mode == "rondelle":
        amt = int(abs(alea.delta))
        muts = []
        if alea.delta > 0:
            muts.append(AddRondelle(tile.tile_id, alea.variable, amt, alea.nom))
        else:
            cur = tile.get_rondelle_count(alea.variable)
            if cur > 0:
                muts.append(RemoveRondelle(tile.tile_id, alea.variable, min(amt,cur), alea.nom))
        log += apply_mutations(muts, game_state)
    elif alea.mode == "health":
        # Cible les vrais semis (stade nommé "semis"), pas l'index 0 — sinon le
        # stade perpétuel des pérennes ligneuses ("arbre", index 0) serait frappé
        # comme un semis fragile à chaque saison (D27).
        muts = [ReduceHealth(p, 1, alea.nom)
                for p in tile.plants if p.is_alive and p.stage.name == "semis"]
        log += apply_mutations(muts, game_state)
        # Mort éventuelle → nécromasse ∝ hauteur
        for p in tile.plants:
            if p.health == 0:
                eco.add_necromass(*p.position, necromass_biomass(p), harvested=False)
    return log

@dataclass
class Engine:
    game_state: dict

    def __post_init__(self):
        self.game_state.setdefault("week", 1)
        self.game_state.setdefault("scores", {})
        self.game_state.setdefault("current_player", "joueur_1")
        self.game_state.setdefault("log", [])
        self.game_state.setdefault("eco", {})
        self.game_state.setdefault("seed", 0x5AB1057E)  # seed global déterministe

    @property
    def week(self): return self.game_state["week"]
    @property
    def tiles(self): return self.game_state["tiles"]
    def _eco(self, tile): return self.game_state["eco"][tile.tile_id]
    def _log(self, l): self.game_state["log"].append(l)

    def _avancer_stades(self, tile, eco):
        log = []
        saison = saison_de(self.week)
        for plant in tile.plants:
            if not plant.is_alive: continue
            plant.age_weeks += 1
            plant.age_years += 1.0 / 52.0   # âge total (courbe d'âge des pérennes)
            stage = plant.stage
            if stage.duration_weeks == 0: continue
            r, c = plant.position
            hum   = eco.humidite.at_plot(r, c)
            light = eco.lumiere.light_received(plant)   # lumière reçue (canopée, auto-ombrage exclu)
            temp  = eco.temperature.at_plot(r, c)       # température ambiante (météo 02)
            # Seuils de croissance : humidité ET lumière ET température suffisantes.
            # tolerance_secheresse abaisse le seuil d'humidité (gène >1 → la plante
            # continue de croître en sol plus sec avant de stagner).
            ok_hum   = hum   >= 0.15 / plant.gene("tolerance_secheresse")
            ok_light = light >= 0.2   # trop d'ombre = stagnation
            ok_temp  = temp  >= plant.plant_class.temp_min_growth   # trop froid = stagnation
            can_grow = ok_hum and ok_light and ok_temp
            # vigueur accélère l'avancement de stade (gène >1 → durée requise réduite).
            needed = stage.duration_weeks / plant.gene("vigueur")
            if plant.age_weeks >= needed and can_grow:
                if plant.advance_stage():
                    log.append(f"    🌱 {plant.name}@{plant.position} → [{plant.stage.name}] "
                               f"(hum={hum:.2f} lum={light:.2f} t={temp:.1f}°C)")
            elif not ok_temp:
                log.append(f"    ❄ {plant.name}@{plant.position} stagne (froid t={temp:.1f}°C)")
            elif not ok_light:
                log.append(f"    🌑 {plant.name}@{plant.position} stagne (ombre lum={light:.2f})")
            elif not ok_hum:
                log.append(f"    ⏸  {plant.name}@{plant.position} stagne (sec hum={hum:.2f})")
        return log

    def _apply_uptake(self, tile, eco):
        """
        Uptake racinaire SPATIAL (chantier B) : la plante puise sur toute son
        empreinte racinaire `root_plots`, pas seulement le plot central. La
        quantité prélevée est répartie (share = 1/nb plots) — on ne duplique
        pas la consommation. La compétition souterraine entre voisines devient
        alors émergente : deux empreintes qui se chevauchent puisent le même sol.
        """
        log = []
        for plant in tile.plants:
            if not plant.is_alive: continue
            plots = [(r, c) for (r, c) in plant.root_plots
                     if 0 <= r < eco.rows and 0 <= c < eco.cols]
            if not plots:
                plots = [plant.position]
            share = 1.0 / len(plots)
            total = {}
            for r, c in plots:
                consumed = eco.plant_uptake(r, c, plant.current_stage,
                                            shade_memory=plant.shade_memory,
                                            drought_memory=plant.drought_memory,
                                            share=share)
                for k, v in consumed.items():
                    total[k] = round(total.get(k, 0.0) + v, 3)
            if total:
                parts = " ".join(f"{v}↓{d:.3f}" for v, d in total.items())
                log.append(f"    🌿 {plant.name}@{plant.position} ×{len(plots)}plt : {parts}")
        return log

    def _apply_exudates(self, tile, eco):
        """
        Boucle rhizosphère (chantier A) — exsudats racinaires.

        Chaque plante vivante « paie » le sol en carbone : elle dépose des
        exsudats proportionnels à sa photosynthèse (lumière reçue × surface
        foliaire × santé) sur son empreinte racinaire. L'essentiel nourrit le
        microbiome local, une fraction l'om_fresh.

        Borne (anti-emballement, piège n°1) : le dépôt de microbiome décroît à
        mesure que le microbiome local sature (×(1 − micro_norm)). La boucle
        exsudats → microbiome → santé/uptake → exsudats converge, n'explose pas.
        """
        log = []
        deposited_total = 0.0
        for plant in tile.plants:
            if not plant.is_alive:
                continue
            # Photosynthèse : lumière reçue (canopée, auto-ombrage exclu) × surface × santé
            light = eco.lumiere.light_received(plant)
            leaf_factor = min(1.0, len(plant.foliar_plots) / 5.0)
            health_factor = plant.health / 3.0
            photo = light * leaf_factor * health_factor
            if photo <= 0.0:
                continue

            exudate = EXUDATE_BASE * photo
            roots = [(r, c) for (r, c) in plant.root_plots
                     if 0 <= r < eco.rows and 0 <= c < eco.cols]
            if not roots:
                roots = [plant.position]
            micro_share = exudate * (1.0 - EXUDATE_OM_SHARE) / len(roots)
            om_share    = exudate * EXUDATE_OM_SHARE / len(roots)
            for r, c in roots:
                micro_norm = min(1.0, eco.microbiome.at_plot(r, c) / 3.0)
                eco.microbiome.add(r, c, micro_share * (1.0 - micro_norm))
                eco.om_fresh.add(r, c, om_share)
                deposited_total += micro_share * (1.0 - micro_norm) + om_share

        if deposited_total > 0.001:
            log.append(f"    🦠 Exsudats → microbiome/om +{deposited_total:.3f} "
                       f"(boucle rhizosphère)")
        return log

    def _update_physiology(self, tile, eco):
        """
        Mise à jour des mémoires physiologiques des plantes.
        Appelée après l'uptake, chaque semaine.
        shade_memory  = lerp(actuel, 1 - lumiere_locale, 0.10)
        drought_memory = lerp(actuel, stress_hydrique, 0.05)
        """
        for plant in tile.plants:
            if not plant.is_alive: continue
            r, c = plant.position
            light = eco.lumiere.light_received(plant)
            hum   = eco.humidite.at_plot(r, c)
            # Shade memory : intégration lente de l'ombre vécue
            plant.shade_memory += (1.0 - light - plant.shade_memory) * 0.10
            plant.shade_memory  = max(0.0, min(1.0, plant.shade_memory))
            # Drought memory : stress quand humidité < 0.5
            drought_stress = max(0.0, 1.0 - hum / 0.5) if hum < 0.5 else 0.0
            plant.drought_memory += (drought_stress - plant.drought_memory) * 0.05
            plant.drought_memory  = max(0.0, min(1.0, plant.drought_memory))
            # Growth factor : la lumière reçue module la hauteur (feedback → ombre)
            target_g = 0.6 + 0.4 * light
            plant.growth_factor += (target_g - plant.growth_factor) * 0.10
            plant.growth_factor  = max(0.3, min(1.0, plant.growth_factor))

    def _tick_senescence_health(self, tile, eco):
        """
        Mortalité réaliste (D27) — santé dynamique.

          Sénescence : au-delà de SENESCENCE_ONSET·longévité, une pression de
                       déclin croissante ∝ âge fait chuter la santé ; mort à 0.
                       Sautée pour les annuelles (longévité = ∞, elles meurent
                       à l'hiver).
          Guérison   : en bon milieu (lumière × humidité, peu de perturbation)
                       et hors fin de vie (sen < HEAL_SEN_CUTOFF), la santé
                       remonte → fini les « zombies » bloqués à 1/3.

        Déterministe via _hash_noise (flux week·3 déclin / week·5 guérison,
        décorrélés). Les sujets tués déposent leur nécromasse avant nettoyage.
        """
        log = []
        seed = self.game_state.get("seed", 42)
        week = self.week
        deaths = []
        for plant in tile.plants:
            if not plant.is_alive:
                continue
            r, c = plant.position
            L = plant.plant_class.longevity()
            # Sénescence par âge
            sen = 0.0
            if L != math.inf:
                denom = (1.0 - SENESCENCE_ONSET) * L
                if denom > 0:
                    sen = max(0.0, min(1.0,
                              (plant.age_years - SENESCENCE_ONSET * L) / denom))
                if sen > 0.0 and _hash_noise(seed, week * 3, r, c) < sen * SEN_RATE:
                    plant.health = max(0, plant.health - 1)
                    if not plant.is_alive:
                        deaths.append(plant)
                        log.append(f"    🪦 {plant.name}@{plant.position} meurt de "
                                   f"sénescence (âge={plant.age_years:.0f}/{L:.0f} ans)")
                        continue
            # Guérison (convalescence) — coupée en fin de vie
            if plant.health < 3 and sen < HEAL_SEN_CUTOFF:
                light   = eco.lumiere.light_received(plant)
                hum     = eco.humidite.at_plot(r, c)
                disturb = eco.disturbance.local(r, c)
                Q = light * min(1.0, hum) * max(0.0, 1.0 - disturb)
                # vigueur accélère la convalescence (gène >1 → guérit plus vite).
                if _hash_noise(seed, week * 5, r, c) < Q * HEAL_RATE * plant.gene("vigueur"):
                    plant.health = min(3, plant.health + 1)
        for plant in deaths:
            deposited = eco.add_necromass(*plant.position,
                                          necromass_biomass(plant), harvested=False)
            log.append(f"    🍂 Nécromasse +{deposited:.2f} OM @{plant.position}")
        if deaths:
            tile.plants = [p for p in tile.plants if p.is_alive]
        return log

    def _reproduction(self, tile, eco, week):
        """
        Reproduction génétique (D17 + D22) — REMPLACE le renouvellement provisoire
        M7. Pour chaque parent en âge de porter des graines qui fructifie ce tick
        (p = reproduction_rate, hash) :

          1. Appariement biparental : père compatible (même famille) à portée de
             pollinisation, modulée par les auxiliaires → vecteur de gènes enfant
             (moyenne parents + mutation ; autofécondation à défaut ; introgression
             inter-espèces décalant les gènes sans changer d'espèce).
          2. Pont « chute → banque-sol » : les graines (gènes hérités) entrent
             dans le pool génétique du plot (succession féral future).
          3. Recrutement direct : seulement pour ce que la succession par archétype
             ne germe PAS (vivaces/arbres SANS archétype, ex-domaine de M7). Les
             archétypes se ressèment via _succession, qui échantillonne le pool.

        Le recrutement reste gated par la lumière (un semis a besoin d'un gap ;
        sous canopée fermée → auto-limitation, pas de climax galopant).
        Déterministe (_hash_noise / hash_gauss).
        """
        log = []
        seed = self.game_state.get("seed", 42)
        occupied: set[tuple] = set()
        for p in tile.plants:
            if p.is_alive:
                occupied.update(p.root_plots)
                occupied.add(p.position)
        radius_plots = int(RESEED_RADIUS_CM // 50) + 1

        for parent in list(tile.plants):
            if not parent.is_alive or not is_seed_bearing(parent):
                continue
            cls = parent.plant_class
            rate = getattr(cls, "reproduction_rate", 0.0)
            if rate <= 0.0:
                continue
            pr, pc = parent.position
            if _hash_noise(seed, week * 17, pr, pc) >= rate:
                continue   # le parent ne fructifie pas ce tick

            # 1+2. Héritage biparental → dépôt génétique dans la banque-sol
            father = find_father(parent, tile.plants, tile, eco, seed, week)
            g_child = child_genes(parent, father, seed, week)
            eco.seed_bank.add_species(pr, pc, cls, rate, g_child)

            # 3. Recrutement direct, domaine ex-M7 uniquement
            is_tree = hasattr(cls, "age_curve")
            if not is_tree and (cls.life_cycle != "perennial"
                                or cls.archetype is not None):
                continue
            best, best_light = None, 0.35   # seuil de viabilité d'un semis
            for (r, c) in sorted(tile.plots_within_radius(pr, pc, radius_plots)):
                if (r, c) in occupied or not tile.is_valid_plot(r, c):
                    continue
                light = eco.lumiere.at_plot(r, c)
                if light > best_light:
                    best_light, best = light, (r, c)
            if best:
                child = tile.add_plant(cls, *best)
                if child:
                    child.genes = g_child
                    occupied.add(best)
                    occupied.update(child.root_plots)
                    tag = "auto" if father is None else (
                        "introgr." if father.plant_class is not cls else "biparental")
                    log.append(f"    🌰 Reproduction : {cls.name} @{best} "
                               f"[lum={best_light:.2f} h={g_child.get('hauteur', 1.0):.2f} "
                               f"{tag}]")
        return log

    def _resoudre_conflits(self, tile, eco):
        log = []
        for c in tile.detect_conflicts():
            log.append(f"    ⚠ Conflit : {c}")
        for c in tile.conflicts:
            if c.resolved: continue
            c.tick()
            loser = c.loser()
            if c.weeks_active >= loser.plant_class.space_tolerance_weeks:
                mort = loser.regress()
                if mort:
                    log.append(f"    ✗ {loser.name}@{loser.position} meurt (conflit).")
                    deposited = eco.add_necromass(*loser.position,
                                                  necromass_biomass(loser), harvested=False)
                    log.append(f"    🍂 Nécromasse +{deposited:.2f} OM @{loser.position}")
                else:
                    log.append(f"    ↓ {loser.name}@{loser.position} → [{loser.stage.name}] (conflit).")
                c.resolved = True
        tile.plants = [p for p in tile.plants if p.is_alive]
        return log

    # -----------------------------------------------------------------------
    # CYCLE SAISONNIER
    # -----------------------------------------------------------------------

    def _winter_transition(self, tile, eco, week: int) -> list[str]:
        """
        Transition hivernale — déclenchée semaines 48-52.

        Annual  → mort + nécromasse + injection seed_bank
        Dormant → métabolisme réduit, root_density relâchée
        Evergreen → légère réduction métabolique

        La libération progressive des racines (×0.85/semaine) ouvre les niches
        pour la succession printanière.
        """
        log = []
        to_remove = []

        for plant in list(tile.plants):
            if not plant.is_alive:
                continue

            # Monocarpie bisannuelle (M3) : floraison/graines l'an 2 puis mort.
            if (plant.plant_class.life_cycle == "biennial"
                    and plant.age_years >= 2.0):
                deposited = eco.add_necromass(*plant.position,
                                              necromass_biomass(plant), harvested=False)
                arch = getattr(plant.plant_class, "archetype", None)
                rate = getattr(plant.plant_class, "reproduction_rate", 0.02)
                if arch:
                    eco.seed_bank.add(*plant.position, arch, rate)
                log.append(
                    f"    ✿ {plant.plant_class.name}@{plant.position} meurt "
                    f"(bisannuelle, an 2) — nécromasse +{deposited:.2f} OM"
                )
                to_remove.append(plant)
                continue

            ws = plant.plant_class.winter_strategy

            if ws == "die":
                # Biomasse → nécromasse ∝ hauteur + graines dans la banque
                deposited = eco.add_necromass(*plant.position,
                                              necromass_biomass(plant), harvested=False)
                # Injection graines
                arch = getattr(plant.plant_class, "archetype", None)
                rate = getattr(plant.plant_class, "reproduction_rate", 0.02)
                if arch:
                    eco.seed_bank.add(*plant.position, arch, rate)
                log.append(
                    f"    ❄ {plant.plant_class.name}@{plant.position} "
                    f"meurt (annual) — nécromasse +{deposited:.2f} OM"
                )
                to_remove.append(plant)

            elif ws == "dormant":
                # Métabolisme minimal — on marque via stress_memory élevé
                plant.stress_memory = min(1.0, plant.stress_memory + 0.15)
                plant.shade_memory  = max(0.0, plant.shade_memory  - 0.05)
                # Racines restent mais compétition relâchée progressivement
                log.append(
                    f"    💤 {plant.plant_class.name}@{plant.position} dormance"
                )

            elif ws == "evergreen":
                plant.stress_memory = min(1.0, plant.stress_memory + 0.05)

        for p in to_remove:
            tile.remove_plant(p)

        return log

    def _mediated_damage(self, tile, eco, severity, reason, gene_name=None):
        """
        Dégât MÉDIÉ sur le tissu tendre exposé (stade « semis »), conforme à la
        philo #2 (CONCEPTION_METEO.md §2.3) — remplace la voie `health` plate pour
        le gel et la grêle.

            effectif = sévérité × susceptibilité_gène × (1 − protection_paillage)

        - `gene_name` : gène de rusticité (>1 ⇒ susceptibilité < 1, plus résistant).
          None ⇒ dégât physique pur (grêle : le froid n'aide pas).
        - protection : le paillage local amortit (chaque rondelle −PAILLAGE_PROTECT).
        - mappage déterministe `effectif → points de santé` par division entière
          (DAMAGE_STEP) : aucun RNG, deux runs identiques (philo #3). La granularité
          entière de `health` fait que le gène départage surtout aux seuils (une
          plante rustique encaisse 0 là où une fragile perd 1).

        On vise le vrai stade « semis » (pas l'index 0) pour ne pas frapper le
        stade perpétuel des pérennes ligneuses (même garde-fou que appliquer_alea).
        """
        log = []
        if severity <= 0:
            return log
        protection = min(1.0, tile.get_rondelle_count("paillage") * PAILLAGE_PROTECT)
        newly_dead = []
        for p in tile.plants:
            if not p.is_alive or p.stage.name != "semis":
                continue
            suscept   = (1.0 / p.gene(gene_name)) if gene_name else 1.0
            effective = severity * suscept * (1.0 - protection)
            lost      = min(p.health, int(effective / DAMAGE_STEP))
            if lost > 0:
                log += apply_mutations([ReduceHealth(p, lost, reason)], self.game_state)
                if p.health == 0:
                    newly_dead.append(p)
        # Mort → nécromasse ∝ hauteur (uniquement les morts de CE dégât, pas de
        # double-comptage des morts antérieures encore présentes sur la tuile).
        for p in newly_dead:
            eco.add_necromass(*p.position, necromass_biomass(p), harvested=False)
        return log

    def tick_semaine(self):
        week         = self.week
        week_in_year = ((week - 1) % 52) + 1   # 1-52 cyclique
        saison       = saison_de(week_in_year)
        log          = [f"\n{'='*54}", f"S{week_in_year:02d}/Y{(week-1)//52+1} — {saison.upper()}"]

        # 1. Météo HEBDOMADAIRE (sous-sprint 02) — fonction PURE de (seed, week).
        # Chaque semaine on écrit la TEMPÉRATURE ambiante (normale saisonnière +
        # delta transitoire de l'événement) dans chaque tuile, AVANT la boucle
        # par tuile : l'hydrologie (évaporation) et le gate de croissance la
        # liront. Gel/canicule/redoux agissent désormais PAR la température ; les
        # autres événements gardent leur effet milieu via WEATHER_ALEA
        # (remplacement progressif des mappings approximatifs, sous-sprint 03).
        seed          = self.game_state.get("seed", 42)
        event         = weather_at(seed, week)
        year_fraction = (week - 1) / 52.0
        phase         = (seed & 0xFFFF) / 0xFFFF * 2.0 * math.pi   # caractère d'année dérivé du seed
        temp_now      = temp_norm(week_in_year, year_fraction, phase) + temperature_delta(event)
        for tile in self.tiles:
            self._eco(tile).temperature.fill(temp_now)

        # Gel : dégât tissulaire MÉDIÉ, piloté par le MILIEU (température < 0), pas
        # par le nom de l'événement (sous-sprint 03). Que le froid vienne d'une
        # gelée tardive ou d'une dérive interannuelle froide, le tissu tendre
        # souffre — modulé par le gène `rusticite_froid` × le paillage local.
        if temp_now < TEMP_FROST_DAMAGE:
            frost_sev = (TEMP_FROST_DAMAGE - temp_now) / FROST_SEVERITY_REF
            log.append(f"  ❄  gel t={temp_now:.1f}°C (sév={frost_sev:.2f})")
            for tile in self.tiles:
                log += self._mediated_damage(tile, self._eco(tile), frost_sev,
                                             "gel (tissu tendre)",
                                             gene_name="rusticite_froid")

        if event.kind != "Beau temps":
            log.append(f"  🌤  {event.kind} (T≈{temp_now:.1f}°C, i={event.intensity:.2f})")
            if event.kind == "Grêle":
                # Grêle : impact physique LOCALISÉ sur le feuillage exposé. Médiée
                # par la protection (paillage), pas par le froid (aucun gène) ;
                # sévérité ∝ intensité de l'événement. Remplace la voie `health`.
                hail_sev = event.intensity / HAIL_SEVERITY_REF
                for tile in self.tiles:
                    log += self._mediated_damage(tile, self._eco(tile), hail_sev,
                                                 "grêle (feuillage)")
            elif event.kind not in TEMP_DRIVEN:
                meteo = WEATHER_ALEA[event.kind]
                for tile in self.tiles:
                    log += appliquer_alea(meteo, tile, self._eco(tile), self.game_state)

        # 1b. Ravageur — début de saison, canal séparé décorrélé de la météo.
        if est_debut_saison(week_in_year):
            pidx     = int(_hash_noise(seed, week, *K_PEST) * len(ALEAS_RAVAGEURS)) % len(ALEAS_RAVAGEURS)
            ravageur = ALEAS_RAVAGEURS[pidx]
            log.append(f"  🐛  {ravageur.nom} : {ravageur.description}")
            for tile in self.tiles:
                log += appliquer_alea(ravageur, tile, self._eco(tile), self.game_state)

        # Spring flush — première semaine du printemps
        if week_in_year == SAISONS["printemps"].start:
            for tile in self.tiles:
                eco = self._eco(tile)
                slog = spring_flush(self.game_state, tile, eco, week)
                if slog: log += slog

        for tile in self.tiles:
            eco = self._eco(tile)
            log.append(f"  [{tile.tile_id}]")

            # 2. Lumière directionnelle (avant tout le reste). La maison (si posée
            # dans le monde) projette son ombre/albédo dans CETTE tuile selon son
            # offset monde (tronçon 2). Absente → lumière historique inchangée.
            lum_log = eco.tick_light(tile.plants, saison,
                                     house=self.game_state.get("house"),
                                     tile_origin=(tile.origin_x_cm, tile.origin_y_cm))
            log += lum_log

            # 3. Hydrologie : évaporation → pluie de fond → rétention → drainage
            eco.tick_hydrology()

            # 4. Décomposition biogéochimique (OM → fertilite, pertes C)
            eco.tick_decomposition()

            # 5. Diffusion spatiale (humidité, fertilité, microbiome)
            eco.tick_diffusion()

            # 6. Avancement stades (conditionné lumière + humidité)
            log += self._avancer_stades(tile, eco)

            # 7. Effets weekly des plantes (flux écologiques + discrets probabilistes)
            for plant in list(tile.plants):
                if not plant.is_alive: continue
                _, elog = resolve_plant_turn(plant, tile, self.game_state, "weekly")
                log += [l for l in elog if l.strip()]

            # 8. Uptake racinaire (après effets, avant physiologie)
            log += self._apply_uptake(tile, eco)

            # 8b. Exsudats racinaires — boucle rhizosphère (chantier A)
            log += self._apply_exudates(tile, eco)

            # 9. Mise à jour mémoire physiologique
            self._update_physiology(tile, eco)

            # 9c. Croissance de structure (D29 réorienté). Phototropisme branché
            # (sprint maison, tronçon 3) : l'apex se penche vers le gradient de la
            # lumière-sol du tick (eco.lumiere, déjà recalculée à l'étape 2). Pour
            # une espèce procédurale (Tomato, AppleTree) la structure biaisée nourrit
            # l'empreinte → re-figeage maîtrisé du golden ; les autres restent INERTES.
            for plant in tile.plants:
                if plant.is_alive:
                    grow_plant(plant, seed, week, eco.lumiere)

            # 9b. Mortalité réaliste — sénescence + santé dynamique (D27)
            log += self._tick_senescence_health(tile, eco)

            # 10. Floraison
            if est_phase_floraison(week_in_year, saison):
                log.append("  🌸 Floraison :")
                for plant in list(tile.plants):
                    if plant.is_alive:
                        _, fl = resolve_plant_turn(plant, tile, self.game_state, "floraison")
                        log += fl

            # 11. Récolte
            if est_phase_recolte(week_in_year, saison):
                log.append("  🍎 Récolte :")
                player_bank = self.game_state.get("player_seed_bank")
                for plant in list(tile.plants):
                    if plant.is_alive:
                        _, rl = resolve_plant_turn(plant, tile, self.game_state, "recolte")
                        log += rl
                        # Fraction de biomasse retourne au sol (résidus de récolte)
                        biomass = (plant.current_stage + 1.0) * 0.4
                        deposited = eco.add_necromass(*plant.position,
                                                      biomass, harvested=True)
                        # Pont récolte → banque-joueur (D17) : graines sélectionnées
                        # (génétique préservée). Inerte si aucune banque-joueur
                        # n'est attachée au game_state (ex: main.py).
                        if player_bank is not None and is_seed_bearing(plant):
                            key = _SPECIES_KEY.get(plant.plant_class)
                            if key:
                                player_bank.add(Seed(key, dict(plant.genes)))

            # 11b. Reproduction génétique (D17+D22) — saison des graines (automne)
            if saison == "automne" and est_phase_recolte(week_in_year, saison):
                rlog = self._reproduction(tile, eco, week)
                if rlog: log += rlog

            # 12. Conflits
            clog = self._resoudre_conflits(tile, eco)
            if clog: log += clog

            # 13. Perturbations écologiques de fond
            seed = self.game_state.get("seed", 42)
            year_fraction = (week - 1) / 52.0
            eco.tick_disturbance(seed, week)
            dlog = apply_disturbances(tile, eco, self.game_state,
                                      seed, week, year_fraction, saison)
            if dlog: log += dlog

            # 13b. Vie macroscopique (D31.1) — champs de population (ravageur,
            # auxiliaire, pollinisateur, vers). CALCULÉS après les champs dont ils
            # dépendent (température, perturbation), mais RIEN dans la santé/les
            # services ne les LIT encore (câblage = D31.2). Aucun log produit
            # → golden INTACT.
            eco.tick_populations(tile, tile.plants)

            # 14. Banque de graines (vieillissement + enrichissement)
            eco.tick_seed_bank(tile.plants, seed=seed, week=week)

            # 15. Succession écologique
            slog = succession(self.game_state, tile, eco, week)
            if slog: log += slog

            # 16. Transition hivernale (semaines 48-52)
            if saison == "hiver" and week_in_year in SAISONS["hiver"] and (week_in_year - SAISONS["hiver"].start) >= 9:
                wlog = self._winter_transition(tile, eco, week)
                if wlog: log += wlog

            # 17. Soil memory (fin de saison)
            if est_fin_saison(week_in_year):
                eco.tick_soil_memory(tile.plants)
                s = eco.summary()
                log.append(f"  🌍 Soil memory updated → {s['soil_memory']:.3f}")

            # Résumé
            alive = [p for p in tile.plants if p.is_alive]
            s = eco.summary()
            stress_avg = sum(p.stress_memory for p in alive) / len(alive) if alive else 0
            log.append(
                f"  → {len(alive)} plante(s) | "
                f"hum={s['humidite']:.2f} fert={s['fertilite']:.3f} "
                f"micro={s['microbiome']:.3f} "
                f"om(f/a/s)={s['om_fresh']:.2f}/{s['om_active']:.2f}/{s['om_stable']:.2f} "
                f"soil={s['soil_memory']:.3f} vit={s['vitalite']:.3f} "
                f"stress={stress_avg:.3f}"
            )

        sc = self.game_state.get("scores", {})
        if any(sum(v.values()) > 0 for v in sc.values()):
            for pid, s in sc.items():
                log.append(f"  📊 {pid} R:{s.get('recolte',0)} "
                           f"L:{s.get('luxuriance',0)} B:{s.get('biodiversite',0)}")

        # Couche Vigueur JOUEUR (D11) — event-driven, AU-DESSUS du tick écolo.
        # GARDÉE : no-op strict si aucune couche joueur (le golden n'a pas de clé
        # `vigueur` → hash intact). Plein au passage de saison, sinon régen passive.
        if "vigueur" in self.game_state:
            if est_debut_saison(week_in_year):
                refill_saison(self.game_state)
            else:
                tick_player_vigueur(self.game_state)

        self.game_state["week"] += 1
        for line in log: self._log(line)
        return log

    def run_year(self, verbose=True):
        return self.run_years(1, verbose=verbose)

    def run_years(self, n_years: int = 1, verbose: bool = True):
        """Simule n_years années (n_years × 52 semaines)."""
        for year in range(n_years):
            if verbose:
                print(f"\n{'#'*54}")
                print(f"# ANNÉE {year + 1}/{n_years}")
                print(f"{'#'*54}")
            for _ in range(52):
                log = self.tick_semaine()
                if verbose:
                    for line in log: print(line)
        return self.game_state
