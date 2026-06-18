"""
SYMBIOSE — sim/engine/boucle.py
La boucle de tick — orchestrateur du moteur.

`Engine` recombine les mixins thématiques (croissance, mortalité, décompo) et
ordonne le pas hebdomadaire `tick_semaine` : météo → lumière → hydrologie →
décompo → diffusion → stades → effets → uptake → physiologie → croissance →
mortalité → floraison/récolte → reproduction → conflits → perturbations →
banque → succession → litière → hiver → squelettes → soil memory.

Tick order (résumé) :
  1. Aléas (début de saison)        6. Uptake racinaire
  2. Lumière directionnelle         7. Floraison / Récolte
  3. Diffusion écologique           8. Conflits spatiaux
  4. Avancement des stades          9. Soil memory (fin de saison)
  5. Effets weekly

L'ORDRE de cette boucle est la clé du déterminisme (golden) — il n'a pas changé
au refactor en paquet. Les implémentations de chaque phase vivent dans les
mixins frères (croissance.py / mortalite.py / decompo.py).
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from plants import PLANT_CATALOGUE
from fields import _hash_noise, ABSCISSION_WEEKS
from fields.ecofields.constants import NEBULOSITE   # table météo→nébulosité (④)
from fields.ecofields.thermique import t_min_nuit_at  # gel nocturne localisé (⑥)
from fields.apiculture import tick_ruches   # ruches : capture essaim + miel (⑥, §H/§I)
from fields.alarme import tick_alarme       # phéromone d'alarme apienne : décroissance (⑦, §J)
from sim.effects import resolve_plant_turn, apply_disturbances
from sim.reproduction import is_seed_bearing
from sim.seeds import Seed
from sim.succession import succession, spring_flush
from sim.weather import (weather_at, K_PEST, temp_norm, temperature_delta,
                         TEMP_DRIVEN)
from sim.vigueur import tick_player_vigueur, refill_saison
from sim.growth import grow_plant
from .calendrier import (SAISONS, saison_de, est_debut_saison, est_fin_saison,
                        est_phase_floraison, est_phase_recolte)
from .aleas import (appliquer_alea, ALEAS_RAVAGEURS, WEATHER_ALEA, ORAGE_VENT,
                    TEMP_FROST_DAMAGE, FROST_SEVERITY_REF, HAIL_SEVERITY_REF)
from .croissance import CroissanceMixin
from .mortalite import MortaliteMixin
from .decompo import DecompoMixin
from .floraison import FloraisonMixin
from .butineurs import ButineurMixin

# Pont récolte → banque-joueur (D17) : classe → clé catalogue (inverse).
_SPECIES_KEY = {cls: key for key, cls in PLANT_CATALOGUE.items()}


@dataclass
class Engine(CroissanceMixin, MortaliteMixin, DecompoMixin, FloraisonMixin,
             ButineurMixin):
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
        nebul         = NEBULOSITE.get(event.kind, 0.10)   # ④ : ciel couvert → moins de surchauffe solaire (défaut ≈ clair)
        is_neige      = (event.kind == "Neige")            # ⑦ : pilote l'accumulation du manteau
        for tile in self.tiles:
            eco = self._eco(tile)
            eco.temperature.fill(temp_now)
            # ⑦ : manteau neigeux AVANT le gel (le gel lit `eco.snow` via t_min_nuit_at).
            # Accumule si Neige, fond sinon (∝ température). Scalaire par tuile.
            eco.tick_snow(temp_now, is_neige)

        # Gel : dégât tissulaire MÉDIÉ, piloté par le MILIEU (température < 0), pas
        # par le nom de l'événement (sous-sprint 03). Que le froid vienne d'une
        # gelée tardive ou d'une dérive interannuelle froide, le tissu tendre
        # souffre — modulé par le gène `rusticite_froid` × le paillage local.
        # ⑥ : le gel est désormais LOCALISÉ au plot. T_air reste uniforme, mais
        # T_min_nuit descend plus bas sur un coin nu/sous ciel clair (rayonnement)
        # que sur un coin paillé (litière) ou sous nuages → un coin abrité peut
        # rester au-dessus du seuil (sév 0, épargné) pendant qu'un coin nu gèle.
        if temp_now < TEMP_FROST_DAMAGE:
            for tile in self.tiles:
                eco = self._eco(tile)
                def frost_sev(p, eco=eco):
                    r, c = p.position
                    t_min = t_min_nuit_at(eco, r, c, temp_now, nebul)
                    return max(0.0, (TEMP_FROST_DAMAGE - t_min) / FROST_SEVERITY_REF)
                sevs = [frost_sev(p) for p in tile.plants
                        if p.is_alive and p.stage.name == "semis"]
                if sevs:
                    log.append(f"  ❄  gel [{tile.tile_id}] t_air={temp_now:.1f}°C "
                               f"sév {min(sevs):.2f}→{max(sevs):.2f}")
                log += self._mediated_damage(tile, eco, 0.0,
                                             "gel (tissu tendre)",
                                             gene_name="rusticite_froid",
                                             severity_fn=frost_sev)

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
                # ⑦ Orage = composite : la pluie (WEATHER_ALEA ci-dessus) PUIS le
                # vent (paillage dispersé), appliqués en séquence.
                if event.kind == "Orage":
                    for tile in self.tiles:
                        log += appliquer_alea(ORAGE_VENT, tile, self._eco(tile), self.game_state)

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

            # 2b. Microclimat de surface T_sol (sprint thermique ①) — APRÈS la
            #     lumière (il la lit), AVANT l'hydrologie (qui lit T_sol). Surchauffe
            #     solaire par plot + inertie ; T_air (champ `temperature`) inchangé →
            #     croissance et gel toujours sur T_air jusqu'aux tronçons ⑤/⑥.
            #     ④ : la nébulosité de l'événement du tick bride le gain solaire.
            eco.tick_thermique(saison, nebul)

            # 3. Hydrologie : évaporation → pluie de fond → rétention → drainage
            #    (le drainage dépend du type de sol de la tuile, §2.3 a).
            eco.tick_hydrology(tile.soil_type)

            # 4. Décomposition biogéochimique (OM → fertilite, pertes C)
            eco.tick_decomposition()
            # 4b. Maturation confinée des structures posées (⑤B, §5.2). No-op
            #     strict si aucune structure n'est posée → golden NEUTRE.
            eco.tick_structures()

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

            # 9d. Floraison RÉELLE (phénologie, arc pollinisation ①). Double porte
            # GDD + photopériode → état floral scalaire `floraison`. INERTE : n'écrit
            # que floraison/gdd_accum et n'émet aucun log → golden NEUTRE. B/C/F
            # liront `floraison` aux tronçons suivants (la « phase floraison » proxy
            # ci-dessous, étape 10, reste en place jusqu'à la reconnexion ②/③).
            self._tick_floraison(tile, eco, week_in_year)

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
            eco.tick_populations(tile, tile.plants, week_in_year)

            # 13c. Butineurs déterministes (arc pollinisation §F, tronçon ③) —
            # échantillonnés sur les champs pollinisateurs FRAÎCHEMENT mis à jour,
            # ils marchent de fleur en fleur et déposent le pollen conspécifique
            # dans `pollen_recu` (lu par la nouaison §B au tronçon ④). N'écrit que
            # pollen_recu (hors digest) + eco.foragers (transient), aucun log →
            # golden NEUTRE. À 0 pollinisateur (0 agent), pollen_recu reste 0.
            self._tick_butineurs(tile, eco, seed, week_in_year)

            # 13d. Ponts de cycle de vie (arc pollinisation §D, tronçon ⑤) — APRÈS
            # les guildes (13b) et les butineurs (13c), ordre §K.2. Ponte/maturation/
            # famine/métamorphose des larves (chenille→papillon, syrphe_larve→syrphe).
            # La chenille s'ajoute à l'herbivorie, la syrphe_larve prédate le ravageur
            # (lus au tick SUIVANT → décalage proie-prédateur). Re-figeage MAÎTRISÉ :
            # à larves=0 (aucun adulte/hors fenêtre), comportement inchangé (§D.6).
            eco.tick_lifecycle_bridges(tile, tile.plants, week_in_year)

            # 13e. Ruches (arc pollinisation ⑥, §H/§I — couche joueur) — APRÈS les
            # guildes (13b) : la capture d'essaim lit le champ `abeille` FRAÎCHEMENT
            # mis à jour, le miel l'intègre via le nectar local. No-op STRICT si
            # aucune ruche n'est posée → golden NEUTRE (§H.3 ; le smoke n'en pose pas).
            tick_ruches(eco, tile, tile.plants)

            # 13f. Alarme apienne (arc pollinisation ⑦, §J) — décroissance hebdo de la
            # phéromone posée par une action directe (écraser une abeille / récolter
            # sans équipement). PUR PUITS lu par le snapshot (Godot anime la piqûre
            # temps réel) : ne touche QUE `eco.alarme`, jamais un champ figé → no-op de
            # fait quand aucune alarme n'est posée (le smoke n'en pose pas) → golden NEUTRE.
            tick_alarme(eco)

            # 14. Banque de graines (vieillissement + enrichissement)
            eco.tick_seed_bank(tile.plants, seed=seed, week=week)

            # 15. Succession écologique
            slog = succession(self.game_state, tile, eco, week)
            if slog: log += slog

            # 15b. Abscission d'automne (②C.1) — caducs vivants → litière feuille.
            if saison == "automne" and week_in_year in ABSCISSION_WEEKS:
                alog = self._abscission(tile, eco)
                if alog: log += alog

            # 15c. Organes-fruits (③ + nouaison pollinisée ④) — nouaison EN FIN DE
            # FLORAISON par plante (lit `floraison` + `pollen_recu` + mode) +
            # maturation + chute des sur-mûrs → litière `fruit`. Gate fruitier+âge+
            # floraison à l'intérieur (golden NEUTRE hors maturité/floraison) ;
            # appelé chaque semaine (le front de floraison est détecté par plante).
            flog = self._tick_fruits(tile, eco, week_in_year)
            if flog: log += flog

            # 16. Transition hivernale (semaines 48-52)
            if saison == "hiver" and week_in_year in SAISONS["hiver"] and (week_in_year - SAISONS["hiver"].start) >= 9:
                wlog = self._winter_transition(tile, eco, week)
                if wlog: log += wlog

            # 16b. Squelettes post-mortem (②B) — APRÈS tous les sites de mort du tick
            # (gel pré-boucle, sénescence, conflits, perturbations, hiver). Seul point
            # de retrait des morts ; fragmente le bois (litière décomposée au tick+1).
            sklog = self._tick_skeletons(tile, eco)
            if sklog: log += sklog

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
