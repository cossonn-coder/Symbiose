"""
SYMBIOSE — sim/engine/mortalite.py
Mort, renouvellement et dégât du vivant : sénescence + santé dynamique (D27),
reproduction génétique (D17+D22), résolution des conflits spatiaux, transition
hivernale et dégât MÉDIÉ (gel/grêle, philo #2).

Regroupés en `MortaliteMixin` — le thème « qui meurt, qui renaît, qui souffre ».
Hérité par l'`Engine` (boucle.py). Toutes les morts passent par
`deposer_mort` (squelette persistant, ②B) ; le retrait effectif est centralisé
dans `_tick_skeletons` (decompo.py). Comportement identique à l'ancien engine.py.
"""

from __future__ import annotations
import math
from fields import (_hash_noise, SENESCENCE_ONSET, SEN_RATE, HEAL_RATE,
                    HEAL_SEN_CUTOFF, ASPHYXIE_HEALTH_SEUIL, ASPHYXIE_RATE,
                    RESEED_RADIUS_CM)
from sim.effects import apply_mutations, ReduceHealth, deposer_mort
from sim.reproduction import find_father, child_genes, is_seed_bearing
from sim.growth import est_etiole
from .aleas import PAILLAGE_PROTECT, DAMAGE_STEP


class MortaliteMixin:
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
            # Asphyxie soutenue (palier 2, §2.3 b) — miroir HAUT de la sénescence :
            # quand la mémoire d'excès d'eau dépasse ASPHYXIE_HEALTH_SEUIL (« si ça
            # dure »), la santé chute par paliers, même forme probabiliste que le
            # déclin sénescent (flux week·7, décorrélé de week·3/·5). Réversible : un
            # assèchement vide la mémoire (§2.3) → la pression retombe. Sous le seuil
            # (terre/sol drainant : asphyxie_memory reste 0) → strictement inerte.
            # MÉDIÉ par le gène EXPRIMÉ `tolerance_asphyxie` (premier consommateur du
            # gène créé au ① ; plasticité ②) : phénotype >1 → tissu mieux aéré (racines
            # adventices/aérenchyme) → pression réduite. Neutre à 1.0 → inchangé.
            if plant.asphyxie_memory > ASPHYXIE_HEALTH_SEUIL:
                pression = ((plant.asphyxie_memory - ASPHYXIE_HEALTH_SEUIL)
                            / plant.expressed_gene("tolerance_asphyxie"))
                if _hash_noise(seed, week * 7, r, c) < pression * ASPHYXIE_RATE:
                    plant.health = max(0, plant.health - 1)
                    if not plant.is_alive:
                        deaths.append(plant)
                        log.append(f"    🪦 {plant.name}@{plant.position} meurt "
                                   f"asphyxié (excès d'eau soutenu)")
                        continue
            # Guérison (convalescence) — coupée en fin de vie
            if plant.health < 3 and sen < HEAL_SEN_CUTOFF:
                light   = eco.lumiere.light_received(plant)
                hum     = eco.humidite.at_plot(r, c)
                disturb = eco.disturbance.local(r, c)
                Q = light * min(1.0, hum) * max(0.0, 1.0 - disturb)
                # vigueur accélère la convalescence (gène >1 → guérit plus vite).
                heal = Q * HEAL_RATE * plant.gene("vigueur")
                # Coût de robustesse de l'étiolement (Q7) : un héliophile étiolé
                # convalesce −10 % — la tige grêle est fragile ; s'il n'atteint pas
                # la lumière (qui lèverait l'étiolement), il se rétablit moins bien
                # et dépérit par le déclin existant. Émergent, pas un verdict.
                if est_etiole(plant, eco.lumiere):
                    heal *= 0.90
                if _hash_noise(seed, week * 5, r, c) < heal:
                    plant.health = min(3, plant.health + 1)
        for plant in deaths:
            deposited = deposer_mort(plant, eco)
            log.append(f"    🍂 Nécromasse +{deposited:.2f} OM @{plant.position}")
        # Pas de retrait ici (②B) : le mort devient squelette, retiré par
        # _tick_skeletons une fois son bois épuisé (herbacée → dès ce tick).
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
                    deposited = deposer_mort(loser, eco)
                    log.append(f"    🍂 Nécromasse +{deposited:.2f} OM @{loser.position}")
                else:
                    log.append(f"    ↓ {loser.name}@{loser.position} → [{loser.stage.name}] (conflit).")
                c.resolved = True
        # Pas de retrait ici (②B) : squelette → _tick_skeletons.
        return log

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

        for plant in list(tile.plants):
            if not plant.is_alive:
                continue

            # Monocarpie bisannuelle (M3) : floraison/graines l'an 2 puis mort.
            if (plant.plant_class.life_cycle == "biennial"
                    and plant.age_years >= 2.0):
                arch = getattr(plant.plant_class, "archetype", None)
                rate = getattr(plant.plant_class, "reproduction_rate", 0.02)
                if arch:
                    eco.seed_bank.add(*plant.position, arch, rate)
                deposited = deposer_mort(plant, eco)   # squelette (②B), pas de retrait
                log.append(
                    f"    ✿ {plant.plant_class.name}@{plant.position} meurt "
                    f"(bisannuelle, an 2) — nécromasse +{deposited:.2f} OM"
                )
                continue

            ws = plant.plant_class.winter_strategy

            if ws == "die":
                # Graines dans la banque + mort → squelette persistant (②B)
                arch = getattr(plant.plant_class, "archetype", None)
                rate = getattr(plant.plant_class, "reproduction_rate", 0.02)
                if arch:
                    eco.seed_bank.add(*plant.position, arch, rate)
                deposited = deposer_mort(plant, eco)
                log.append(
                    f"    ❄ {plant.plant_class.name}@{plant.position} "
                    f"meurt (annual) — nécromasse +{deposited:.2f} OM"
                )

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

        # Pas de retrait ici (②B) : les morts hivernaux sont des squelettes,
        # retirés par _tick_skeletons (herbacées sans bois → dès ce tick).
        return log

    def _mediated_damage(self, tile, eco, severity, reason, gene_name=None,
                         severity_fn=None, cause=""):
        """
        Dégât MÉDIÉ sur le tissu tendre exposé (stade « semis »), conforme à la
        philo #2 (CONCEPTION_METEO.md §2.3) — remplace la voie `health` plate pour
        le gel et la grêle.

            effectif = sévérité × susceptibilité_gène × (1 − protection_paillage)

        - `gene_name` : gène de rusticité (>1 ⇒ susceptibilité < 1, plus résistant).
          None ⇒ dégât physique pur (grêle : le froid n'aide pas).
        - `cause` : enum de symptôme foliaire ÉVÉNEMENTIEL (sémiologie ②) — "gel"
          ou "grele" selon l'appelant (boucle.py). Propagé au ReduceHealth → laisse
          une marque décroissante sur le feuillage de la plante touchée.
        - `severity_fn` : sévérité LOCALISÉE au plot (gel nocturne ⑥). Si fournie,
          chaque plante reçoit `severity_fn(p)` (calculée depuis T_min_nuit à SON
          plot) au lieu du scalaire `severity` uniforme — un coin paillé/sous-nuages
          (sév 0) est épargné quand un coin nu/clair gèle. Grêle/canicule passent
          toujours un scalaire (severity_fn=None) → chemin de dégât inchangé.
        - protection : le paillage RONDELLE local amortit (chaque rondelle
          −PAILLAGE_PROTECT). ⚠️ Le paillage agit désormais à DEUX échelles : la
          rondelle (geste joueur, ici) ET la litière `om_fresh` (couvert émergent,
          dans T_min_nuit côté severity_fn). Les deux jouent — c'est voulu.
        - mappage déterministe `effectif → points de santé` par division entière
          (DAMAGE_STEP) : aucun RNG, deux runs identiques (philo #3). La granularité
          entière de `health` fait que le gène départage surtout aux seuils (une
          plante rustique encaisse 0 là où une fragile perd 1).

        On vise le vrai stade « semis » (pas l'index 0) pour ne pas frapper le
        stade perpétuel des pérennes ligneuses (même garde-fou que appliquer_alea).
        """
        log = []
        if severity_fn is None and severity <= 0:
            return log
        protection = min(1.0, tile.get_rondelle_count("paillage") * PAILLAGE_PROTECT)
        newly_dead = []
        for p in tile.plants:
            if not p.is_alive or p.stage.name != "semis":
                continue
            sev = severity_fn(p) if severity_fn is not None else severity
            if sev <= 0:
                continue
            suscept   = (1.0 / p.expressed_gene(gene_name)) if gene_name else 1.0
            effective = sev * suscept * (1.0 - protection)
            lost      = min(p.health, int(effective / DAMAGE_STEP))
            if lost > 0:
                log += apply_mutations([ReduceHealth(p, lost, reason, cause=cause)], self.game_state)
                if p.health == 0:
                    newly_dead.append(p)
        # Mort → squelette persistant (②B). `deposer_mort` est idempotent : les
        # morts antérieures encore présentes (squelettes) ne sont pas re-déposées.
        for p in newly_dead:
            deposer_mort(p, eco)
        return log
