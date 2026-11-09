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
from fields import (_hash_noise, SENESCENCE_ONSET, SEN_ONSET_JITTER, SEN_RATE,
                    HEAL_RATE, HEAL_SEN_CUTOFF, ASPHYXIE_HEALTH_SEUIL,
                    ASPHYXIE_RATE, RESEED_RADIUS_CM, VITALITE_STEP)
from sim.effects import apply_mutations, ReduceHealth, deposer_mort
from sim.effects.perturbations import SEUIL_SEMIS
from sim.reproduction import (find_father, child_genes, child_expression,
                              is_seed_bearing, graine_fertile,
                              recrue_par_fruits)
from sim.capacite import recrutement_bloque
from sim.growth import est_etiole
from .racines import eau_percue
from .aleas import (PAILLAGE_PROTECT, DAMAGE_STEP, WIND_DAMAGE_SEUIL,
                    WIND_SEVERITY_REF, WIND_ETIOLE_SUSCEPT)

# Anémochorie (sprint VENT ⑤, §5.3) : portée de dépôt SOUS LE VENT d'une graine
# ailée/plumée (`seed_dispersal == "anemochore"`), en PLOTS, à force de vent 1.
# Le dépôt génétique de `_reproduction` glisse de `ANEMOCHORIE_PORTEE_PLOTS × force`
# plots dans la direction du vent (clamp à la tuile) → la lignée féral migre sous le
# vent, élargit/oriente la succession (philo #2 : flux vent → où s'installe la suite).
ANEMOCHORIE_PORTEE_PLOTS = 4.0


def _plot_sous_le_vent(pr: int, pc: int, wind_dir: float, wind_force: float) -> tuple:
    """Plot d'atterrissage d'une graine anémochore lâchée en (pr, pc) : décalé SOUS
    LE VENT (opposé à `wind_dir`, qui est la direction d'OÙ vient le vent) d'une
    distance ∝ `wind_force`, exprimée directement en PLOTS. Vent nul → (pr, pc)
    inchangé (golden NEUTRE : dépôt au pied, comme une barochore)."""
    dist = ANEMOCHORIE_PORTEE_PLOTS * wind_force
    # Sous le vent = -(vecteur d'origine) : le vent vient de `wind_dir`, le pollen/la
    # graine part dans le sens opposé.
    dr = -dist * math.sin(wind_dir)
    dc = -dist * math.cos(wind_dir)
    return (pr + round(dr), pc + round(dc))


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
            # Sénescence par âge. Onset PROPRE à l'individu (DÉSYNC PHÉNOLOGIE ①) :
            # le gène-tempo `phenologie_florale` décale le début du déclin (gène > 1
            # = précoce → sénesce plus tôt). Neutre 1.0 ⇒ onset == SENESCENCE_ONSET.
            # MIROIR EXACT dans semiologie.senescence (même gène, même formule).
            sen = 0.0
            if L != math.inf:
                g = plant.gene("phenologie_florale")
                onset = max(0.05, min(0.95,
                            SENESCENCE_ONSET - SEN_ONSET_JITTER * (g - 1.0)))
                denom = (1.0 - onset) * L
                if denom > 0:
                    sen = max(0.0, min(1.0,
                              (plant.age_years - onset * L) / denom))
                if sen > 0.0 and _hash_noise(seed, week * 3, r, c) < sen * SEN_RATE:
                    # Sénescence = horloge INTERNE de vieillissement (pas un stress
                    # subi) → décrément DIRECT, hors `erode`/résilience (décision D5).
                    # Snap anti-poussière (comme `erode`) : 1.0 − 3×(1/3) ≠ 0 en
                    # flottant ; sans lui une plante « morte de vieillesse » lingérerait
                    # à ~1e-16 (is_alive vrai). La vieillesse qui atteint le fond TUE.
                    v = plant.vitalite - VITALITE_STEP
                    plant.vitalite = v if v > 1e-9 else 0.0
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
            # MULTIPLIÉ par la tolérance CONSTITUTIVE d'espèce `asphyxie_tolerance_base`
            # (hélophytes ⑤ : aulne/sphaigne survivent au sol gorgé qui noie le pommier).
            # Défaut 1.0 → dénominateur inchangé. Branche ARMÉE seulement quand le sol
            # est durablement gorgé (jamais dans le smoke) → golden inchangé.
            if plant.asphyxie_memory > ASPHYXIE_HEALTH_SEUIL:
                tol = (plant.expressed_gene("tolerance_asphyxie")
                       * plant.plant_class.asphyxie_tolerance_base)
                pression = (plant.asphyxie_memory - ASPHYXIE_HEALTH_SEUIL) / tol
                if _hash_noise(seed, week * 7, r, c) < pression * ASPHYXIE_RATE:
                    # Insulte EXTERNE (excès d'eau) → passe par `erode` (la médiation
                    # `tolerance_asphyxie` reste en amont sur la PRESSION ci-dessus).
                    plant.erode(VITALITE_STEP)
                    if not plant.is_alive:
                        deaths.append(plant)
                        log.append(f"    🪦 {plant.name}@{plant.position} meurt "
                                   f"asphyxié (excès d'eau soutenu)")
                        continue
            # Guérison (convalescence) — coupée en fin de vie
            if plant.etat != "sain" and sen < HEAL_SEN_CUTOFF:
                light   = eco.lumiere.light_received(plant)
                # Eau RESSENTIE (D111 ④) : racines pourries/rongées → convalescence ↓.
                hum     = eau_percue(plant, eco, eco.humidite.at_plot(r, c))
                disturb = eco.disturbance.local(r, c)
                Q = light * min(1.0, hum) * max(0.0, 1.0 - disturb)
                # vigueur accélère la convalescence (gène >1 → guérit plus vite) ;
                # le coût de défense (plasticité ③) la freine : la vigueur re-routée
                # vers la défense cicatrise moins vite (neutre = 1.0 sans sur-expression).
                heal = Q * HEAL_RATE * plant.gene("vigueur") * plant.cout_defense()
                # Coût de robustesse de l'étiolement (Q7) : un héliophile étiolé
                # convalesce −10 % — la tige grêle est fragile ; s'il n'atteint pas
                # la lumière (qui lèverait l'étiolement), il se rétablit moins bien
                # et dépérit par le déclin existant. Émergent, pas un verdict.
                if est_etiole(plant, eco.lumiere):
                    heal *= 0.90
                if _hash_noise(seed, week * 5, r, c) < heal:
                    # GAIN par pas 1/3 (décision ① : on garde le pas d'antan pour la
                    # neutralité d'échelle — la finesse continue vient des dégâts
                    # médiés, pas de la convalescence). Récupération pilotée par la
                    # vigueur (dans `heal` ci-dessus), pas par la constitution.
                    plant.vitalite = min(1.0, plant.vitalite + VITALITE_STEP)
        for plant in deaths:
            deposited = deposer_mort(plant, eco)
            log.append(f"    🍂 Nécromasse +{deposited:.2f} OM @{plant.position}")
        # Pas de retrait ici (②B) : le mort devient squelette, retiré par
        # _tick_skeletons une fois son bois épuisé (herbacée → dès ce tick).
        return log

    def _reproduction(self, tile, eco, week, wind_dir: float = 0.0,
                      wind_force: float = 0.0):
        """
        Reproduction génétique (D17 + D22) — REMPLACE le renouvellement provisoire
        M7. Pour chaque parent en âge de porter des graines qui fructifie ce tick
        (p = reproduction_rate, hash) :

          1. Appariement biparental : père compatible (même famille) à portée de
             pollinisation, modulée par les auxiliaires → vecteur de gènes enfant
             (moyenne parents + mutation ; autofécondation à défaut ; introgression
             inter-espèces décalant les gènes sans changer d'espèce).
          2. Pont « chute → banque-sol » : les graines (gènes hérités) entrent
             dans le pool génétique du plot (succession féral future). ANÉMOCHORIE
             (⑤, §5.3) : une espèce à graine ailée/plumée (`seed_dispersal ==
             "anemochore"` : pissenlit, graminée, ortie) dépose ce pool SOUS LE
             VENT (`_plot_sous_le_vent`, décalage ∝ `wind_force`) au lieu d'au pied
             → la lignée féral migre dans la direction du vent, orientant la
             succession future. Barochore (défaut) ou vent nul → dépôt au pied.
          3. Recrutement direct : seulement pour ce que la succession par archétype
             ne germe PAS (vivaces/arbres SANS archétype, ex-domaine de M7). Les
             archétypes se ressèment via _succession, qui échantillonne le pool.

        Le recrutement reste gated par la lumière (un semis a besoin d'un gap ;
        sous canopée fermée → auto-limitation, pas de climax galopant).
        Déterministe (_hash_noise / hash_gauss).
        """
        log = []
        # Backstop PUR-perf (sprint PERF ③) : tuile au cap dur → aucune reproduction
        # (ni dépôt banque-sol, ni recrutement direct) ce tick. Disjoncteur jamais
        # atteint en jeu normal (cf. sim/capacite.py) → golden neutre en régime calibré.
        if recrutement_bloque(tile):
            return [f"    ⚠ cap perf tuile {tile.tile_id} atteint (reproduction gelée)"]
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
            # Graine stérile sous ce climat (figuier sans blastophage, relève ③) :
            # ni dépôt banque-sol ni recrue directe ; la relève passe par les rejets.
            if not graine_fertile(cls):
                continue
            # Fruitier pérenne (zoochorie ②, D42) : sa relève naît de ses VRAIS fruits
            # qui tombent (`decompo.semer_chute`) → ni pool banque-sol ni recrue directe.
            if recrue_par_fruits(cls):
                continue
            rate = getattr(cls, "reproduction_rate", 0.0)
            if rate <= 0.0:
                continue
            pr, pc = parent.position
            if _hash_noise(seed, week * 17, pr, pc) >= rate:
                continue   # le parent ne fructifie pas ce tick

            # 1+2. Héritage biparental → dépôt génétique dans la banque-sol.
            # Priming transgénérationnel (plasticité ④) : l'état d'expression de la
            # MÈRE voyage avec la graine (`e_child`, déjà atténué par PRIMING_FRAC)
            # → la lignée éprouvée naît pré-armée à la germination (sample_expression).
            father = find_father(parent, tile.plants, tile, eco, seed, week)
            g_child = child_genes(parent, father, seed, week)
            e_child = child_expression(parent)
            # Anémochorie (⑤) : graine ailée → pool déposé SOUS LE VENT (clampé à la
            # tuile) ; barochore ou calme → au pied (dr, dc) = (pr, pc).
            dr, dc = pr, pc
            if getattr(cls, "seed_dispersal", "barochore") == "anemochore" and wind_force > 0.0:
                tr, tc = _plot_sous_le_vent(pr, pc, wind_dir, wind_force)
                if tile.is_valid_plot(tr, tc):
                    dr, dc = tr, tc
            eco.seed_bank.add_species(dr, dc, cls, rate, g_child, e_child)

            # 3. Recrutement direct, domaine ex-M7 uniquement
            is_tree = hasattr(cls, "age_curve")
            if not is_tree and (cls.life_cycle != "perennial"
                                or cls.archetype is not None):
                continue
            # Pose COHÉRENTE (relève ligneuse ②, D130). Arbre : le fruit tombe sous
            # la COURONNE du parent (rayon de chute = rayon de couronne, +1 plot de
            # roulé) et le semis ne s'installe que là où il SURVIT à l'ombre : seuil
            # = 1 − SEUIL_SEMIS, la lumière qui tient la `shade_memory` d'un semis
            # sous son seuil de dégât (①). Avant : rayon fixe 150 cm < couronne d'un
            # adulte et seuil 0,35 sous le seuil de dégât d'un héliophile → le moteur
            # posait la recrue là où il la tuait ensuite. Non-arbre : inchangé.
            # Le plot le plus lumineux gagne : abstraction « parmi les graines tombées,
            # celle la mieux placée s'installe » (pas de multi-semis à suivre).
            if is_tree:
                rayon = int(cls.canopy_radius_at(parent) // 50) + 1
                best, best_light = None, 1.0 - SEUIL_SEMIS
            else:
                rayon = radius_plots
                best, best_light = None, 0.35   # seuil de viabilité d'un semis
            for (r, c) in sorted(tile.plots_within_radius(pr, pc, rayon)):
                if (r, c) in occupied or not tile.is_valid_plot(r, c):
                    continue
                light = eco.lumiere.at_plot(r, c)
                if light > best_light:
                    best_light, best = light, (r, c)
            if best:
                child = tile.add_plant(cls, *best)
                if child:
                    child.genes = g_child
                    child.expression.update(e_child)   # priming direct (mère vivante, ④)
                    occupied.add(best)
                    occupied.update(child.root_plots)
                    tag = "auto" if father is None else (
                        "introgr." if father.plant_class is not cls else "biparental")
                    log.append(f"    🌰 Reproduction : {cls.name} @{best} "
                               f"[lum={best_light:.2f} h={g_child.get('hauteur', 1.0):.2f} "
                               f"{tag}]")
        return log

    def _resoudre_conflits(self, tile, eco):
        """
        Conflit spatial = NOTIFICATION diégétique, PAS un verdict de mort (①
        sprint usure/létalité ; aligne le code sur CONCEPTION_COMPETITION_INTRAPLOT
        §Q3 : « la mort du perdant ÉMERGE du déclin de santé — jamais de mortalité
        verdict »). La détection reste (le joueur voit deux plantes se disputer un
        plot) mais la résolution n'inflige PLUS rien : plus de `loser.regress()`
        (qui, au stade 0, mettait `health = 0` = mort sèche d'une plante saine),
        plus de dépôt de nécromasse par ce chemin. Le dominé décline via les voies
        continues DÉJÀ en place (ombrage LightField → `shade_stress_damage`, ponction
        racinaire partagée, sénescence) — usure progressive, pas punition (philo #6).

        Seule tâche restante : borner la liste `tile.conflicts` en marquant
        `resolved` les conflits PÉRIMÉS (une plante morte, ou chevauchement disparu)
        pour qu'ils soient élaguables. `resolved` ne scelle plus aucune mort — il
        signale juste un conflit caduc. Le pruning ne touche QUE `conflicts`, jamais
        l'état des plantes (golden re-figé = suppression des morts par conflit, rien
        d'autre ne bouge).
        """
        log = []
        for c in tile.detect_conflicts():
            log.append(f"    ⚠ Conflit : {c}")
        for c in tile.conflicts:
            if c.resolved:
                continue
            c.tick()
            if self._conflit_perime(tile, c):
                c.resolved = True
        # Pas de mortalité, pas de retrait : la mort du dominé émerge du stress/
        # sénescence (_tick_senescence_health + voies continues).
        return log

    @staticmethod
    def _conflit_perime(tile, c) -> bool:
        """Un conflit est périmé (élaguable) dès qu'une de ses plantes est morte OU
        que le chevauchement litigieux a disparu (les plots ne sont plus co-occupés
        dans la couche du conflit). Lecture seule — ne modifie aucune plante."""
        if any(not p.is_alive for p in c.plants):
            return True
        get_plots = ((lambda p: p.foliar_plots) if c.conflict_type == "foliar"
                     else (lambda p: p.root_plots))
        for plot in c.plots:
            occupants = sum(1 for p in c.plants if plot in get_plots(p))
            if occupants >= 2:
                return False   # au moins un plot litigieux reste co-occupé
        return True

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
                         severity_fn=None, cause="", species_base=None):
        """
        Dégât MÉDIÉ sur le tissu tendre exposé (stade « semis »), conforme à la
        philo #2 (docs/champs/climat/conception_meteo.md §2.3) — remplace la voie `health` plate pour
        le gel et la grêle.

            effectif = sévérité × susceptibilité_gène × (1 − protection_paillage)

        - `gene_name` : gène de rusticité (>1 ⇒ susceptibilité < 1, plus résistant).
          None ⇒ dégât physique pur médié par la NICHE d'espèce (cf. `species_base`).
        - `species_base` : nom d'un attribut de classe de NICHE (couche 1, base
          d'ESPÈCE, PAS un gène) qui médie la source quand aucun gène ne s'applique
          — aujourd'hui `hail_resistance_base` pour la grêle (>1 ⇒ feuillage coriace
          → susceptibilité < 1). Lu uniquement si `gene_name is None`. Se compose
          proprement avec la CONSTITUTION `resilience_base` (couche 2, appliquée EN
          AVAL par `erode` dans la résolution du ReduceHealth) : la niche filtre la
          SOURCE (grêle), la constitution amortit la MAGNITUDE → pas de double-compte.
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
            if gene_name:
                suscept = 1.0 / p.expressed_gene(gene_name)
            elif species_base:
                # Niche d'espèce (grêle) : coriace (>1) ⇒ susceptibilité < 1.
                suscept = 1.0 / getattr(p.plant_class, species_base, 1.0)
            else:
                suscept = 1.0
            # Protection LOCALE = paillage-rondelle (tuile) + écran POSÉ au plot
            # (voile/cloche, effondrement météo ③) : un plot voilé encaisse la grêle
            # là où le paillage seul (uniforme) laisserait passer. `couvert_at` = 0 au
            # repos → protection inchangée → golden NEUTRE.
            prot_local = min(1.0, protection + eco.couvert_at(*p.position))
            effective = sev * suscept * (1.0 - prot_local)
            # Amount CONTINU (plus de plancher entier `int()` : l'érosion
            # fractionnaire est fidèle à la sévérité). La résolution applique
            # `amount * VITALITE_STEP` et `erode` borne à 0 → pas de `min(p.health…)`.
            amount = effective / DAMAGE_STEP
            if amount > 0:
                log += apply_mutations([ReduceHealth(p, amount, reason, cause=cause)], self.game_state)
                if not p.is_alive:
                    newly_dead.append(p)
        # Mort → squelette persistant (②B). `deposer_mort` est idempotent : les
        # morts antérieures encore présentes (squelettes) ne sont pas re-déposées.
        for p in newly_dead:
            deposer_mort(p, eco)
        return log

    def _wind_damage(self, tile, eco, gust_peak):
        """
        Dégât MÉCANIQUE du vent sur le tissu tendre étiolé (thigmomorphogénèse, vent ④,
        §5.2) — frère de `_mediated_damage`, mais lit le VENT LOCAL spatialisé
        (`eco.vent[r,c]`, champ d'abri du ③) et MÉDIE par l'étiolement :

            sév     = max(0, vent_local·risée − SEUIL) / SEVERITY_REF
            suscept = (étiolé ? WIND_ETIOLE_SUSCEPT : 1.0) / expressed_gene("port_trapu")
            effectif = sév × suscept × (1 − paillage)

        - `gust_peak` (pic de risée du tick, `max(gust_profile)`) amplifie le vent local
          → c'est la RAFALE qui casse, pas la brise moyenne. À `eco.vent` nul (calme /
          aucun obstacle / pots) → sév 0 partout → no-op (golden NEUTRE les semaines
          calmes ; re-figeage localisé aux semaines de coup de vent sur semis étiolés).
        - une tige ÉTIOLÉE (`est_etiole`, bras de levier grêle) est PLUS susceptible ;
          un port TRAPU (`port_trapu` exprimé par le vent vécu) encaisse → la boucle
          plasticité se referme (le semis endurci protège réellement).
        - vise le vrai stade « semis » (tissu tendre), même garde-fou que
          `_mediated_damage` (on n'abîme pas le stade perpétuel des pérennes ligneuses).
        """
        log = []
        vent = getattr(eco, "vent", None)
        if vent is None or gust_peak <= 0.0:
            return log
        # TURBULENCE de lisière (périphérie ②) : multiplicateur de rafale LOCALE
        # posé par `tick_abri` derrière un secteur peu poreux — le flux décroche
        # par-dessus le rideau dense et retombe en rafales. `None` au repos (aucune
        # ceinture) → aucune multiplication → casse mécanique bit-identique.
        turb = getattr(eco, "turbulence", None)
        protection = min(1.0, tile.get_rondelle_count("paillage") * PAILLAGE_PROTECT)
        newly_dead = []
        for p in tile.plants:
            if not p.is_alive or p.stage.name != "semis":
                continue
            # Grimpante accrochée/palissée : le support la PORTE → exempte de la
            # casse mécanique du vent (grimpantes ④, §6 ; le tuteur ne casse pas,
            # écarté). Golden INTACT (aucun support posé dans le smoke → personne
            # n'est exempté ; l'exemption ne peut fuir vers une plante libre).
            if getattr(p, "support", None) is not None:
                continue
            vent_local = vent.at_plot(*p.position) * gust_peak
            if turb is not None:
                vent_local *= turb.at_plot(*p.position)
            sev = max(0.0, vent_local - WIND_DAMAGE_SEUIL) / WIND_SEVERITY_REF
            if sev <= 0.0:
                continue
            fragilite = WIND_ETIOLE_SUSCEPT if est_etiole(p, eco.lumiere) else 1.0
            suscept   = fragilite / p.expressed_gene("port_trapu")
            effective = sev * suscept * (1.0 - protection)
            # Amount CONTINU (cf. `_mediated_damage`) : plus de plancher entier.
            amount = effective / DAMAGE_STEP
            if amount > 0:
                log += apply_mutations([ReduceHealth(p, amount,
                                        "vent (tige cassée)", cause="")], self.game_state)
                if not p.is_alive:
                    newly_dead.append(p)
        for p in newly_dead:
            deposer_mort(p, eco)
        return log
