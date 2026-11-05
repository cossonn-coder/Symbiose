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
from dataclasses import dataclass
from plants import PLANT_CATALOGUE
from fields import (_hash_noise, ABSCISSION_MIN, ABSCISSION_MAX, CHUTE_SEMAINES,
                    PRECIP_NORM, PLUIE_APPORT)
from fields.ecofields.thermique import t_min_nuit_at  # gel nocturne localisé (⑥)
from fields.peripherie import tick_repousse, tick_ouvrages  # ceinture : repousse (④) + ouvrages d'eau (⑤)
from fields.apiculture import tick_ruches   # ruches : capture essaim + miel (⑥, §H/§I)
from fields.alarme import tick_alarme       # phéromone d'alarme apienne : décroissance (⑦, §J)
from sim.effects import resolve_plant_turn, apply_disturbances
from sim.reproduction import is_seed_bearing, child_expression
from sim.seeds import Seed
from sim.succession import succession
from sim.weather import weather_state, K_PEST, TEMP_DRIVEN, patch_local, humidite_air
from .transpiration import demande_climatique   # transpiration foliaire (D111 ①)
from sim.wind import wind_at, gust_profile
from sim.vigueur import tick_player_vigueur, refill_saison
from sim.growth import grow_plant
from sim.grimpe import chercher_support, relais_appui
from sim.clonal import emettre_ramets
from .calendrier import (SAISONS, saison_de, est_debut_saison, est_fin_saison,
                        est_phase_floraison, est_phase_recolte)
from .aleas import (appliquer_alea, ALEAS_RAVAGEURS, WEATHER_ALEA, ORAGE_VENT,
                    TEMP_FROST_DAMAGE, FROST_SEVERITY_REF, HAIL_SEVERITY_REF)
from .croissance import CroissanceMixin
from .mortalite import MortaliteMixin
from .decompo import DecompoMixin, deposer_bois_tombe
from .branches import mort_des_branches
from .ceinture_bois import bois_de_lisiere
from .floraison import FloraisonMixin
from .butineurs import ButineurMixin
from .anemophilie import AnemophilieMixin
from .carnivore import CarnivoreMixin

# Pont récolte → banque-joueur (D17) : classe → clé catalogue (inverse).
_SPECIES_KEY = {cls: key for key, cls in PLANT_CATALOGUE.items()}


@dataclass
class Engine(CroissanceMixin, MortaliteMixin, DecompoMixin, FloraisonMixin,
             ButineurMixin, AnemophilieMixin, CarnivoreMixin):
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
        # État météo consolidé (événement + T_air + nébulosité) via le helper PUR
        # partagé avec le snapshot (serialize §A) — un seul calcul, jamais deux qui
        # dérivent. T_air = normale saisonnière + delta transitoire ; nébulosité ④.
        # `pluie_forcee` : banc de TEST `pluie_continue` SEULEMENT (D111 ①e) — clé
        # absente en jeu/golden → False → météo pure inchangée.
        pluie_forcee  = self.game_state.get("pluie_forcee", False)
        event, temp_now, nebul = weather_state(seed, week, pluie_forcee)
        # Vent de MASSE D'AIR de la semaine (sprint VENT & ÉVAPOTRANSPIRATION ①/②/③).
        # Scalaire uniforme sur le monde (comme T_air/nébulosité), fonction PURE O(1).
        # `force` pilote l'évaporation (②) ; `direction` oriente le sillage d'abri (③).
        # Au ③ le champ d'abri `eco.vent` SPATIALISE cette masse d'air par plot (sillage
        # sous le vent des obstacles, venturi) → l'évaporation et le wind chill lisent
        # désormais `eco.vent[r,c]` au lieu du scalaire uniforme.
        wind          = wind_at(seed, week)
        vent_force    = wind.force
        vent_dir      = wind.direction
        # Pic de RISÉE intra-journalière (④, §5.2) : la rafale qui CASSE le tissu
        # étiolé (≠ la perte hydrique moyenne du ②). Scalaire uniforme par tick comme
        # le reste de la masse d'air ; multiplie le vent LOCAL dans `_wind_damage`.
        gust_peak     = max(gust_profile(seed, week))
        is_neige      = (event.kind == "Neige")            # ⑦ : pilote l'accumulation du manteau
        # Apport d'eau météo MÉDIÉ (sprint météo→champs ①, §2.2). Uniforme par tuile
        # (dépend du seul `event.kind`), infiltré ∝ structure dans tick_hydrology ci-
        # dessous. Remplace les deltas plats humidité retirés de WEATHER_ALEA. 0 hors
        # pluie/sécheresse → ces semaines-là l'hydrologie est inchangée.
        pluie_event   = PLUIE_APPORT.get(event.kind, 0.0)
        # Sprint « le sol qui respire » ① (D111) : humidité de l'AIR océanique (lue
        # par la rosée à la place de l'humidité du sol) et DEMANDE climatique de
        # transpiration (chaleur × ciel × vent, lue par l'uptake d'eau). Scalaires
        # uniformes PURS, calculés une fois par tick comme T_air/nébulosité.
        hr_air        = humidite_air(seed, week, event)
        demande_eau   = demande_climatique(temp_now, nebul, vent_force)
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
                                             severity_fn=frost_sev,
                                             cause="gel")

        if event.kind != "Beau temps":
            log.append(f"  🌤  {event.kind} (T≈{temp_now:.1f}°C, i={event.intensity:.2f})")
            if event.kind == "Grêle":
                # Grêle : impact physique LOCALISÉ sur le feuillage exposé. Médiée
                # par la protection (paillage), pas par le froid (aucun gène) ;
                # sévérité ∝ intensité de l'événement. Remplace la voie `health`.
                # ① : `scope="local"` (§2) est ENFIN honoré — un PATCH déterministe
                # (patch_local, canaux sentinelles) sélectionne le coin frappé ; un
                # plot HORS patch est épargné (sév 0) → variance spatiale de survie
                # (philo #7 : le jardin ne meurt plus d'un bloc). `scope="global"`
                # (grêle importée d'un futur catalogue) frappe toute la tuile.
                hail_sev = event.intensity / HAIL_SEVERITY_REF
                for tile in self.tiles:
                    eco = self._eco(tile)
                    if event.scope == "local":
                        in_patch = patch_local(seed, week, eco.rows, eco.cols)
                        sev_fn = lambda p, s=hail_sev, f=in_patch: (
                            s if f(*p.position) else 0.0)
                        log += self._mediated_damage(
                            tile, eco, 0.0, "grêle (feuillage)", cause="grele",
                            severity_fn=sev_fn, species_base="hail_resistance_base")
                    else:
                        log += self._mediated_damage(
                            tile, eco, hail_sev, "grêle (feuillage)", cause="grele",
                            species_base="hail_resistance_base")
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

        # 1c. Repousse de la CEINTURE (sprint PÉRIPHÉRIE ④, D73, §4.4) — O(4), une
        # fois par monde (la ceinture n'appartient à aucune tuile), AVANT la boucle :
        # lumière (2) et abri (2a) doivent lire la hauteur/densité de CE tick. Fait
        # vieillir les seules coupes en cours : trogne 5 ans, taillis 10, canopée 30.
        # Déterministe, aucun tirage. **No-op strict sans ceinture** (cas du golden)
        # ou sans coupe en cours → aucune écriture → digest intact.
        tick_repousse(self.game_state.get("ceinture"))

        # 1c-bis. Vieillissement des OUVRAGES d'eau (PÉRIPHÉRIE ⑤, D73, §4.4) — même
        # place, même coût O(4), pour la même raison : la ligne d'eau doit être à jour
        # AVANT que `tick_berge` (2e) ne la lise. Un barrage non entretenu rompt vers
        # 8 ans et l'eau reprend son cours (marqueur 🚧 au ledger) — l'artefact demande
        # un entretien perpétuel, cohérent avec le run éternel (#4). Déterministe (un
        # seuil sur une horloge). **No-op strict sans ceinture ni ouvrage** → golden
        # intact.
        log += tick_ouvrages(self.game_state.get("ceinture"))

        for tile in self.tiles:
            eco = self._eco(tile)
            log.append(f"  [{tile.tile_id}]")

            # 2. Lumière directionnelle (avant tout le reste). La maison (si posée
            # dans le monde) projette son ombre/albédo dans CETTE tuile selon son
            # offset monde (tronçon 2). Absente → lumière historique inchangée.
            # PÉRIPHÉRIE ② : la `ceinture` (4 secteurs, `game_state["ceinture"]`)
            # ajoute ses lisières boisées/rocheuses comme occulteurs GLOBAUX du même
            # type que la maison — ombre partielle, saisonnalité produite par la
            # géométrie solaire seule. Absente (cas du golden) → inchangé.
            lum_log = eco.tick_light(tile.plants, saison,
                                     house=self.game_state.get("house"),
                                     tile_origin=(tile.origin_x_cm, tile.origin_y_cm),
                                     ceinture=self.game_state.get("ceinture"))
            log += lum_log

            # 2-bis. Ombrières posées (effondrement météo ③) — ATTÉNUENT la lumière-sol
            #     que `tick_light` vient de recalculer, AVANT la thermique/l'hydrologie
            #     (qui la lisent). Un plot sous ombrière chauffe moins et évapore moins
            #     → mitige canicule/sécheresse PAR LE MILIEU (philo #1). No-op STRICT
            #     sans ombrière posée (`ombre_pose is None`) → lumière-sol bit-identique
            #     → golden NEUTRE.
            eco.appliquer_ombrieres()

            # 2a. Champ d'abri spatial (sprint VENT & ÉVAPOTRANSPIRATION ③, §4) —
            #     APRÈS la lumière (les obstacles/hauteurs sont à jour), AVANT la
            #     thermique/l'hydrologie (qui lisent `eco.vent`). Spatialise la masse
            #     d'air uniforme : un obstacle (maison, plante haute) abrite son sillage
            #     sous le vent, un goulet accélère (venturi). CACHE sur (obstacles,
            #     direction discrétisée) → coût ≈ 0 en régime permanent (§7B). À
            #     `vent_force=0` → champ NUL → évaporation/wind chill inchangés.
            #     PÉRIPHÉRIE ② : la ceinture entre comme obstacle POREUX (φ = 1 −
            #     densité) → réduction du vent moyen LINÉAIRE + `eco.turbulence`
            #     (rafale locale) QUADRATIQUE. Absente → `turbulence` reste None.
            eco.tick_abri(tile.plants, vent_dir, vent_force,
                          house=self.game_state.get("house"),
                          tile_origin=(tile.origin_x_cm, tile.origin_y_cm),
                          ceinture=self.game_state.get("ceinture"))

            # 2a-bis. Champ de LISIÈRE (sprint PÉRIPHÉRIE ③, D73, §4.2) — publie
            #     `eco.lisiere` (gradient d'effet de lisière depuis les bords, porté
            #     par le TYPE de secteur). Groupé ici avec les autres couplages de la
            #     ceinture ; l'appel est MÉMOÏSÉ sur les types de secteurs (quasi
            #     statiques) donc quasi gratuit, et il précède de loin son unique
            #     lecteur (`tick_populations`, vie macro). Sans ceinture le champ reste
            #     None → capacité de charge des guildes bit-identique.
            eco.maj_lisiere(self.game_state.get("ceinture"),
                            tile_origin=(tile.origin_x_cm, tile.origin_y_cm))
            # Colonies de fleurs des bords (LISIÈRE NUE ①, D124) : même patron, lu par
            # la ressource des butineurs dans `tick_populations`.
            eco.maj_fleurs_bord(self.game_state.get("ceinture"), seed, week_in_year,
                                tile_origin=(tile.origin_x_cm, tile.origin_y_cm))

            # 2b. Microclimat de surface T_sol (sprint thermique ①) — APRÈS la
            #     lumière (il la lit), AVANT l'hydrologie (qui lit T_sol). Surchauffe
            #     solaire par plot + inertie ; T_air (champ `temperature`) inchangé →
            #     croissance et gel toujours sur T_air jusqu'aux tronçons ⑤/⑥.
            #     ④ : la nébulosité de l'événement du tick bride le gain solaire.
            eco.tick_thermique(saison, nebul)

            # 2c. Rosée & gelée blanche nocturnes (sprint météo→champs ②, §3) —
            #     ENTRE la thermique (2b) et l'hydrologie (3). Relit le thermomètre
            #     nocturne `t_min_nuit_at` + l'humidité du sol pour déposer la rosée
            #     (>0 °C → `humidite +`) ou accumuler/fondre le givre (≤0 °C → carte
            #     `eco.givre`, fonte différée au réchauffement). Le dépôt est ensuite
            #     drainé/diffusé normalement par l'hydrologie. Émet 💧/❄ (signe
            #     diégétique, philo #5). No-op si aucune condensation → golden-safe ;
            #     les nuits claires/froides du smoke (hiver) en produisent → re-figeage
            #     MAÎTRISÉ (humidité matinale en hausse).
            log += eco.tick_rosee(temp_now, nebul, humidite_air=hr_air)

            # 2d. Couverture du sol (sprint LUXURIANCE ①, D65 §2.1) — SCATTER des
            #     empreintes des plantes BASSES (sol+basse) vers le champ scalaire
            #     `couverture_sol`. Placé ICI, AVANT ses deux lecteurs : l'évaporation
            #     (étape 3 — sol couvert perd moins d'eau) et la germination férale
            #     (succession, étape 13 — couvert dense étouffe les adventices). Un
            #     seul balayage des plantes/tick (jamais un sweep de grille). Tuile
            #     sans plante basse → champ nul → lecteurs neutres. La tuile 2 du golden
            #     porte du Clover → couverture > 0 → RE-FIGEAGE MAÎTRISÉ ANNONCÉ.
            eco.tick_couverture(tile.plants, saison)

            # 2e. Nappe de BERGE (sprint PÉRIPHÉRIE ③, D73, §3.4) — JUSTE AVANT
            #     l'hydrologie, pour que l'eau poussée (ou retirée) par un secteur
            #     `riviere` suive TOUT le circuit existant sans une ligne de plus :
            #     capture du surplus > HUM_CAP en lame de surface (étape 3), puis
            #     ruissellement (3b) et mémoire de marais (3c). Le marécage de berge
            #     ÉMERGE donc, il n'est nulle part scripté. Il n'existe AUCUNE grille
            #     hydraulique hors jardin : c'est une condition aux limites, pas une
            #     rivière simulée. Sans ceinture → no-op strict.
            eco.tick_berge(self.game_state.get("ceinture"),
                           tile_origin=(tile.origin_x_cm, tile.origin_y_cm))
            # 2e-ter. SOURCES ponctuelles (SOL NOURRICIER ④) — même patron que la
            #     berge, en un point : la nappe qui affleure au fond d'une mare
            #     alimente les pores puis la lame ; le marais émerge du circuit.
            #     Aucune source (smoke, bancs) → no-op strict → golden intact.
            eco.tick_source()

            # 2e-bis. ÉROSION de bordure (PÉRIPHÉRIE ⑤, D73, §4.5) — un secteur dénudé
            #     (coupe rase) ou une falaise entaillée dépose ses colluvions sur les
            #     3 premiers plots du bord : `structure_sol` déstructurée, `om_stable`
            #     dilué. Groupé ici avec les autres couplages de ceinture et placé
            #     AVANT l'hydrologie (3), qui lit `structure_sol` pour l'infiltration →
            #     la conséquence est immédiate et lisible. Ce n'est pas un malus mais un
            #     flux de matière : tout le reste (infiltration ↓, asphyxie ↑, uptake ↓)
            #     émerge des lecteurs existants (philo #2). L'érosion CESSE d'elle-même
            #     quand la repousse ramène le couvert ; une entaille de falaise, elle,
            #     ne se referme jamais. Émet 🪨 (signe diégétique, une fois par épisode).
            #     Sans ceinture ni secteur dénudé → no-op strict → golden intact.
            log += eco.tick_erosion(self.game_state.get("ceinture"),
                                    tile_origin=(tile.origin_x_cm, tile.origin_y_cm))

            # 3. Hydrologie : évaporation → pluie de fond → rétention → drainage
            #    (le drainage dépend du type de sol de la tuile, §2.3 a). L'apport
            #    météo `pluie_event` (①, §2.2) y est infiltré ∝ structure du sol.
            eco.tick_hydrology(tile.soil_type, pluie_event=pluie_event,
                               nebulosite=nebul, vent_masse_air=vent_force,
                               vent_field=eco.vent)
            # 3b. Ruissellement latéral (sprint hydrologie & marécages ②) : la lame
            #     d'eau de surface capturée à l'étape 3 (surplus de saturation) dévale
            #     la surface hydraulique (altitude + épaisseur) vers les plots plus bas,
            #     s'infiltre, s'évapore. Double buffer → déterministe. No-op strict tant
            #     qu'aucun plot ne déborde (eau_surface nulle). Re-figeage LARGE ANNONCÉ
            #     (l'eau circule enfin → bilan hydrique par plot modifié aux cuvettes).
            eco.tick_ruissellement()
            # 3c. Marécage (sprint hydrologie & marécages ③) : une flaque qui DURE
            #     intègre `marais_memory` vers 1 (hystérèse d'état). APRÈS le
            #     ruissellement (qui pose la lame de surface) et AVANT décompo/pH,
            #     qui LISENT la mémoire du tick (anaérobie → tourbe, acidification).
            #     No-op strict tant qu'aucune flaque ne dure → golden NEUTRE hors banc.
            eco.tick_marais()
            # 3d. Glace sur l'eau libre (MARE VIVANTE ①) : prend par nuits de gel,
            #     fond au dégel, sur la lame du tick (posée en 3/3b). Lue par la vue
            #     SEULE (bloc `marais` du pont) → aucun effet en retour, golden NEUTRE.
            eco.tick_glace(temp_now, nebul)

            # 4. Décomposition biogéochimique (OM → fertilite, pertes C)
            eco.tick_decomposition()
            # 4b. Maturation confinée des structures posées (⑤B, §5.2). No-op
            #     strict si aucune structure n'est posée → golden NEUTRE.
            eco.tick_structures()

            # 4c. Dérive décennale du pH (sprint physico-chimie ①) — APRÈS la
            #     décompo (elle lit la litière `om_fresh_at`). ⑥ : la présence
            #     d'une rondelle d'amendement sur la tuile pousse la cible —
            #     `chaux` (+) remonte le pH, `soufre` (−) l'acidifie. Présence
            #     binaire signée {−1,0,+1} (philo : on pousse une cible, le sol
            #     répond avec inertie). Aucune rondelle chaux/soufre au smoke →
            #     amend_dir=0 → golden NEUTRE.
            net_amend = (tile.get_rondelle_count("chaux")
                         - tile.get_rondelle_count("soufre"))
            amend_dir = (net_amend > 0) - (net_amend < 0)
            eco.tick_ph(amend_dir)

            # 4d. Dérive lente de la structure du sol (sprint physico-chimie ⑧) —
            #     APRÈS la décompo (elle lit la litière `om_fresh_at` pour le couvert
            #     anti-battance). `pluie_norm` = violence d'impact de l'événement météo
            #     du tick (PRECIP_NORM ; 0 hors pluie frappante → aucune battance). Les
            #     gestes becher/grelinette mutent `structure_sol` ailleurs (en direct).
            pluie_norm = PRECIP_NORM.get(event.kind, 0.0)
            eco.tick_structure(tile.plants, pluie_norm)

            # 4e. Réseau fongique (sprint mycélium & interconnexions ①) — APRÈS la
            #     structure (le champ lit une litière `bois_fresh_at`/humidité/T_sol
            #     déjà à jour ce tick), AVANT la diffusion. Croissance sur le bois
            #     humide non travaillé, déclin au sec/substrat épuisé. Au tronçon ①
            #     les rôles §2 (saprophyte/mycorhize/faune) sont DÉBRANCHÉS : personne
            #     ne lit `mycelium` → aucun effet en retour. Mycélium nul au repos +
            #     pas de bois colonisable notable dans le smoke → golden NEUTRE.
            eco.tick_mycelium()

            # 4f. Allélopathie racinaire (sprint ALLÉLOPATHIE ①) — décroissance
            #     LABILE du champ `allelopathie` (perte spontanée + détox ∝ microbiome),
            #     APRÈS le mycélium, AVANT la diffusion. Le champ est ALIMENTÉ par les
            #     émetteurs via `inject_field` (effets weekly, plus bas). Au tronçon ①
            #     les rôles (germination ②, croissance ③) sont DÉBRANCHÉS : personne ne
            #     lit `allelopathie` → aucun effet en retour. Champ nul au repos + aucune
            #     espèce ne l'émet encore (tronçon ⑤) → golden NEUTRE.
            eco.tick_allelopathie()

            # 4g. Mémoire d'inoculum du sol (sprint mémoire d'inoculum ①) —
            #     décroissance passive des buckets d'inoculum (× INOC_DECAY) rabattue
            #     par le microbiome suppressif. Placé près des autres décroissances de
            #     champs ; l'ordre est SANS IMPORTANCE (personne ne lit `inoculum` ce
            #     tronçon — DORMANT). L'alimentation (2 canaux CONSÉQUENCE) se fait dans
            #     la passe maladie (étape 13, apply_disturbances/deposer_mort). Champ VIDE
            #     au repos (aucun plot infecté) → boucle sparse vide → golden INTACT.
            eco.inoculum.tick_decay(eco)

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
            log += self._apply_uptake(tile, eco, saison, week_in_year, demande_eau)

            # 8b. Exsudats racinaires — boucle rhizosphère (chantier A)
            log += self._apply_exudates(tile, eco)

            # 9. Mise à jour mémoire physiologique. `nebul`/`pluie_event` (météo du
            #    tick, cf. lignes 95/114) alimentent l'humectation foliaire (①).
            self._update_physiology(tile, eco, nebulosite=nebul, pluie_event=pluie_event)

            # 9b. Remise à plat de l'aspersion foliaire (sprint HUMECTATION FOLIAIRE ③) —
            #     carte transiente `eco.aspersion_last` posée par `arroser(feuillage=True)`.
            #     APRÈS `_update_physiology` (son SEUL lecteur), PAS avant : le geste
            #     s'applique ENTRE deux ticks (hors tick, invariant H2 — cmd_action /
            #     automate après `tick_semaine`), donc l'aspersion est déjà écrite quand ce
            #     tick démarre ; un reset en TÊTE de tick l'effacerait AVANT que l'humectation
            #     la lise (le geste n'aurait jamais d'effet). En la remettant à plat ICI,
            #     l'aspersion vit exactement le tick qui suit le geste, comme une transiente
            #     (patron `rosee_last`, mais reset côté CONSOMMATEUR car le producteur est
            #     hors tick). `fill(0.0)` écrit des 0 dans un champ que personne d'autre ne
            #     lit → aucun effet de bord ; nul au repos (aucun geste) → golden INTACT.
            if getattr(eco, "aspersion_last", None) is not None:
                eco.aspersion_last.fill(0.0)

            # 9c. Croissance de structure (D29 réorienté). Phototropisme branché
            # (sprint maison, tronçon 3) : l'apex se penche vers le gradient de la
            # lumière-sol du tick (eco.lumiere, déjà recalculée à l'étape 2). Pour
            # une espèce procédurale (Tomato, AppleTree) la structure biaisée nourrit
            # l'empreinte → re-figeage maîtrisé du golden ; les autres restent INERTES.
            # 9c-bis. Accroche des grimpantes (D49 volet A, tronçon ②) — JUSTE avant
            # la croissance : une grimpante libre au-dessus de sa hauteur
            # autoportante cherche un support proche (structures de la tuile + mur
            # maison) et s'y accroche (état persistant). No-op sans grimpante libre
            # concernée ni support compatible → golden NEUTRE (le haricot du smoke
            # est `vrille_volubile`, aucun support posé, mur nu refusé).
            house = self.game_state.get("house")
            for plant in tile.plants:
                if plant.is_alive:
                    chercher_support(plant, tile, house)
                    relais_appui(plant, tile, house, week)   # HOUPPIER ② : no-op sans `rigidite_tige`
                    # D111 ② : les branches élaguées d'un LIGNEUX tombent en litière
                    # `bois` sous elles (no-op pour les herbacées / rien d'élagué).
                    tombes = grow_plant(plant, seed, week, eco.lumiere)
                    if deposer_bois_tombe(plant, tombes, eco) > 1e-4:
                        log.append(f"    🪵 Branche morte tombée {plant.name}"
                                   f"@{plant.position}")
            # 9c-ter. Les branches MEURENT (D111 ②bis) : ombre (cladoptose), tempête,
            #     neige, bois sec des arbustes → litière `bois` (même relais que 9c).
            log += mort_des_branches(tile, eco, saison, week, week_in_year, seed,
                                     gust_peak, is_neige)
            # 9c-quater. La LISIÈRE boisée lâche du bois mort sur les plots de bord
            #     (D111 ⑦bis) : flux continu, plus fort l'automne-hiver et en tempête.
            #     Sans ceinture (golden/smoke) → no-op strict.
            log += bois_de_lisiere(tile, eco, self.game_state.get("ceinture"), saison,
                                   seed, week, vent_force, gust_peak)

            # 9b. Mortalité réaliste — sénescence + santé dynamique (D27)
            log += self._tick_senescence_health(tile, eco)

            # 9b-bis. Dégât MÉCANIQUE du vent (thigmomorphogénèse, vent ④, §5.2) —
            #     APRÈS la croissance (l'étiolement et le port_trapu du tick sont à
            #     jour) et la sénescence. Lit `eco.vent` (champ d'abri ③) × la risée :
            #     un coup de vent casse le semis ÉTIOLÉ de serre, le semis endurci
            #     (port trapu) encaisse. No-op les semaines calmes → golden NEUTRE.
            log += self._wind_damage(tile, eco, gust_peak)

            # 9d. Floraison RÉELLE (phénologie, arc pollinisation ①). Double porte
            # GDD + photopériode → état floral scalaire `floraison`. INERTE : n'écrit
            # que floraison/gdd_accum et n'émet aucun log → golden NEUTRE. B/C/F
            # liront `floraison` aux tronçons suivants (la « phase floraison » proxy
            # ci-dessous, étape 10, reste en place jusqu'à la reconnexion ②/③).
            self._tick_floraison(tile, eco, week_in_year)

            # 9e. Densification clonale (D65 §2.2, tronçon ②) — APRÈS croissance/
            # vigueur/sénescence (maturité et santé du tick à jour) et le recalcul
            # du champ `couverture_sol` (étape 2d). Une clonale mature émet un ramet
            # (clone génétique) borné par le gate de couverture (auto-limitation +
            # cap perf) et le gate de lumière au sol (stolon/drageon). Déterministe.
            # NEUTRE hors trèfle stolonifère du smoke → golden RE-FIGÉ maîtrisé.
            log += emettre_ramets(tile, eco, seed, week)

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
                        # Plasticité ④ : la graine récoltée EST un descendant → elle
                        # emporte le priming maternel (`child_expression`, atténué par
                        # PRIMING_FRAC). Filtré aux entrées non-neutres → graine d'une
                        # mère non acclimatée = neutre (save lisible).
                        if player_bank is not None and is_seed_bearing(plant):
                            key = _SPECIES_KEY.get(plant.plant_class)
                            if key:
                                expr = {g: v for g, v in child_expression(plant).items()
                                        if abs(v - 1.0) > 1e-9}
                                player_bank.add(Seed(key, dict(plant.genes), expr))

            # 11b. Reproduction génétique (D17+D22) — saison des graines (automne).
            # Anémochorie (⑤, §5.3) : `vent_dir`/`vent_force` décalent le dépôt
            # génétique des espèces à graine ailée SOUS LE VENT (graine voyage).
            if saison == "automne" and est_phase_recolte(week_in_year, saison):
                rlog = self._reproduction(tile, eco, week, vent_dir, vent_force)
                if rlog: log += rlog

            # 12. Conflits
            clog = self._resoudre_conflits(tile, eco)
            if clog: log += clog

            # 13. Perturbations écologiques de fond
            seed = self.game_state.get("seed", 42)
            year_fraction = (week - 1) / 52.0
            eco.tick_disturbance(seed, week)
            # vent_dir/vent_force (①) : la maladie fongique (⑥, §5.4) module sa
            # pression par le vent LOCAL (assèchement protecteur, eco.vent ③) et
            # disperse l'inoculum SOUS LE VENT depuis les foyers infectés au vent.
            dlog = apply_disturbances(tile, eco, self.game_state,
                                      seed, week, year_fraction, saison,
                                      vent_dir, vent_force)
            if dlog: log += dlog

            # 13b. Vie macroscopique (D31.1) — champs de population (ravageur,
            # auxiliaire, pollinisateur, vers). CALCULÉS après les champs dont ils
            # dépendent (température, perturbation), mais RIEN dans la santé/les
            # services ne les LIT encore (câblage = D31.2). Aucun log produit
            # → golden INTACT.
            eco.tick_populations(tile, tile.plants, week_in_year)

            # 13b-ter. Puits carnivore → `moustique` (hydrologie & marécages ⑥) —
            # APRÈS tick_populations (le champ `moustique` du tick est à jour) : la
            # Drosera prélève une fraction de la nuée sur son empreinte foliaire → la
            # faune de mare se raréfie localement (flux plante→faune, philo #2), et son
            # azote « interne » (proies) la libère de la faim d'azote via `qi_local`
            # (lecture). Premier couplage PLANTE → champ FAUNE. NEUTRE : aucune Drosera
            # au smoke → boucle vide → digest inchangé.
            clog = self._tick_carnivore(tile, eco)
            if clog: log += clog

            # 13b-bis. Épaisseur de sol visible (D57, ①a) — APRÈS tous les
            # consommateurs de MO du tick (décompo 4, structures 4b, mycélium 4e,
            # populations 13b) : la cible bulk-density reflète ainsi la consommation
            # de la SEMAINE ENTIÈRE (l'épaisseur SUIT la MO, ne la consomme pas). Un
            # éventuel lecteur en retour (l'hydrologie ①b) lira l'épaisseur du tick
            # PRÉCÉDENT → décalage d'1 tick uniforme et déterministe, sans boucle
            # instantanée (préparé pour ①b). Lu par PERSONNE ce tronçon → golden
            # NEUTRE (le champ n'entre dans aucune grandeur du digest/summary).
            eco.tick_epaisseur()

            # 13c. Butineurs déterministes (arc pollinisation §F, tronçon ③) —
            # échantillonnés sur les champs pollinisateurs FRAÎCHEMENT mis à jour,
            # ils marchent de fleur en fleur et déposent le pollen conspécifique
            # dans `pollen_recu` (lu par la nouaison §B au tronçon ④). N'écrit que
            # pollen_recu (hors digest) + eco.foragers (transient), aucun log →
            # golden NEUTRE. À 0 pollinisateur (0 agent), pollen_recu reste 0.
            self._tick_butineurs(tile, eco, seed, week_in_year)

            # 13c-bis. Pollinisation ANÉMOPHILE (sprint VENT ⑤, §5.3) — APRÈS les
            # butineurs (voie entomophile), à côté d'eux : le vent dépose du
            # `pollen_recu` sur les fleurs `wind` ∝ vent local × congénères en
            # AMONT (direction du vent). Voie de nouaison PARALLÈLE, sans insecte.
            # Lit `eco.vent` (champ d'abri ③) et `vent_dir` (masse d'air ①). N'écrit
            # que `pollen_recu` (hors digest), aucun log → golden NEUTRE (aucun
            # fruitier anémophile mûr dans le smoke). Calme → no-op strict.
            self._tick_anemophilie(tile, eco, vent_dir, vent_force)

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

            # 14. Banque de graines (vieillissement + enrichissement). La PLUIE DE
            # GRAINES de la périphérie (③) s'y ajoute : la matrice ensemence les plots
            # de bord (canal d'acquisition #3, jusqu'ici sans support mécanique).
            # Placée AVANT la succession (15) : une graine tombée cette semaine peut
            # lever cette semaine, comme les enrichissements internes.
            eco.tick_seed_bank(tile.plants, seed=seed, week=week,
                               ceinture=self.game_state.get("ceinture"),
                               tile_origin=(tile.origin_x_cm, tile.origin_y_cm))

            # 15. Succession écologique
            slog = succession(self.game_state, tile, eco, week)
            if slog: log += slog

            # 15b. Abscission d'automne (②C.1 ; DÉSYNC PHÉNOLOGIE ①) — caducs
            # vivants → litière feuille. Fenêtre d'automne complète : chaque plante
            # largue à SA semaine propre (gène-tempo), pas au rendez-vous global, et
            # sur CHUTE_SEMAINES (AUTOMNE VISIBLE ③), d'où la borne haute élargie.
            if saison == "automne" and (ABSCISSION_MIN <= week_in_year
                                        <= ABSCISSION_MAX + CHUTE_SEMAINES - 1):
                alog = self._abscission(tile, eco, week_in_year)
                if alog: log += alog

            # 15c. Organes-fruits (③ + nouaison pollinisée ④) — nouaison EN FIN DE
            # FLORAISON par plante (lit `floraison` + `pollen_recu` + mode) +
            # maturation + chute des sur-mûrs → litière `fruit`. Gate fruitier+âge+
            # floraison à l'intérieur (golden NEUTRE hors maturité/floraison) ;
            # appelé chaque semaine (le front de floraison est détecté par plante).
            flog = self._tick_fruits(tile, eco, week_in_year)
            if flog: log += flog

            # 15d. Transport ÉOLIEN de la litière (sprint VENT ⑦, §5.6) — APRÈS tous
            # les dépôts de litière du tick (décompo 4, abscission 15b, fruits 15c) :
            # le vent CHARRIE la litière légère (feuille/herbace) des plots exposés
            # vers leur voisin plus abrité SOUS LE VENT (`eco.vent` ③ + `vent_dir` ①)
            # → un coin de brise-vent accumule la matière (philo #2 : flux → contrainte
            # → hétérogénéité du sol). PASSE CONDITIONNELLE : sautée les semaines calmes
            # (`vent_force < TRANSPORT_SEUIL`) → coût nul (levier perf §7B). Re-figeage
            # MAÎTRISÉ ANNONCÉ (la litière de surface se redistribue). Émet 🍃 (signe
            # diégétique consommé HORS tick par le ledger des voix).
            tlog = eco.tick_transport(vent_dir, vent_force)
            if tlog: log += tlog

            # 15e. Paillage (sprint équilibre invasion ③, D69) — DÉCROISSANCE du mulch
            #      posé par le geste `pailler`, reversée à l'humus `om_stable`. Placé
            #      APRÈS ses lecteurs de la semaine (évaporation étape 3, vieillissement
            #      de banque étape 14, germination férale étape 15) : ceux-ci voient la
            #      profondeur que le joueur a déposée AVANT ce tick, puis le mulch se
            #      décompose d'un cran. Champ NUL au repos (le smoke ne paille jamais) →
            #      no-op strict (décompo=0, rien reversé) → golden INTACT.
            eco.tick_paillage()

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
                # 17a. Autotoxicité / fatigue du sol (sprint ALLÉLOPATHIE ④) — cadence
                #      SAISONNIÈRE (le ressort est pluriannuel, pas hebdo) : la même
                #      espèce émettrice qui ré-occupe un plot fait monter `autotox`, la
                #      rotation le fait redescendre (détox ∝ microbiome). Lu par la SEULE
                #      espèce traceée via `allelo_effectif` (②/③). Aucune espèce n'émet
                #      encore (`allelopathie_emission=0` avant le ⑤) → le traceur ne
                #      s'arme jamais → `autotox` reste nul → golden NEUTRE.
                eco.tick_autotoxicite(tile.plants)
                s = eco.summary()
                log.append(f"  🌍 Soil memory updated → {s['soil_memory']:.3f}")

            # Résumé
            alive = [p for p in tile.plants if p.is_alive]
            s = eco.summary()
            stress_avg = sum(p.stress_memory for p in alive) / len(alive) if alive else 0
            log.append(
                f"  → {len(alive)} plante(s) | "
                f"hum={s['humidite']:.2f} npk={s['n']:.2f}/{s['p']:.2f}/{s['k']:.2f} "
                f"micro={s['microbiome']:.3f} "
                f"om(f/a/s)={s['om_fresh']:.2f}/{s['om_active']:.2f}/{s['om_stable']:.2f} "
                f"soil={s['soil_memory']:.3f} vit={s['vitalite']:.3f} "
                f"stress={stress_avg:.3f}"
            )

        # 17b. Conteneurs (sprint pots/bacs ②+③) — pots/bacs posés par le joueur,
        # chacun un mini-sol `EcoFields` qui ticke SA chimie ISOLÉE (drainage du
        # substrat, décompo de la litière pré-chargée, pH/structure/soil_memory,
        # lumière à sa position) PUIS l'uptake + croissance de ses plantes (③ :
        # confinement racinaire hybride = effet nain). APRÈS la boucle des tuiles (la
        # maison du monde et la météo du tick sont prêtes), AVANT la couche Vigueur
        # joueur / snapshot. **No-op STRICT si la liste est vide** (le smoke ne pose
        # AUCUN conteneur) : `for` sur `[]` → zéro écriture → golden NEUTRE.
        # Déterministe : ordre d'insertion de la liste, zéro RNG.
        for ctn in self.game_state.get("containers", []):
            ctn.tick(saison, seed, week,
                     house=self.game_state.get("house"),
                     nebulosite=nebul)

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
