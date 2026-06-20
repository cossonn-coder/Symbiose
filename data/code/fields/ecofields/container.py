"""
SYMBIOSE — fields/ecofields/container.py
Conteneur EcoFields : tous les champs écologiques continus d'une tuile
(hydrologie, OM tri-compartiment, microbiome, soil memory, lumière, perturbation,
banque de graines, populations) + les ticks qui les font évoluer.

Le cœur du moteur écologique. Les constantes de calibration vivent dans
`constants.py`, les types de litière/structures dans `litiere.py`. Comportement
identique à l'ancien `ecofields.py`.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field

from fields.grids import GridField, DisturbanceField
from fields.light import LightField
from fields.seedbank import SeedBank
from fields.population import (PopulationField, build_population_specs,
                               build_pollinator_specs, build_lifecycle_bridges,
                               POLLINATOR_NAMES, daylength)
from fields.lifecycle import larval_field_names, tick_bridges
from .constants import *          # constantes de calibration écologique
from .litiere import *            # Parcelle, Structure, STRUCTURE_ACCEPTE, MATUR_*…
from .litiere import _fusion_parcelle, _lisser_ages   # helpers privés (hors import *)
from .thermique import tick_thermique as _tick_thermique   # calcul pur T_sol (①)
from .thermique import snow_next as _snow_next              # manteau neigeux pur (⑦)
from .ph import tick_ph as _tick_ph                         # dérive pure du pH (physico-chimie ①)
from .nutriments import split_miner, cec_norm_at, leach_factor, dispo, immobilise_n   # chimie N/P/K pure (physico-chimie ③/④/⑦)


@dataclass
class EcoFields:
    tile_id:    str
    rows:       int
    cols:       int
    # Type de sol de la tuile porteuse (roche-mère). Sert d'HÉRITAGE au champ `ph`
    # (sprint physico-chimie ①, table PH_PAR_SOL) et reste disponible pour les
    # futurs lecteurs de la chimie du sol. Défaut "terre" → compat des appels
    # historiques qui construisaient EcoFields sans le préciser (tuile terre).
    soil_type:  str = "terre"

    humidite:         GridField = field(default=None)
    microbiome:       GridField = field(default=None)
    lumiere:          LightField = field(default=None)
    soil_memory:      GridField = field(default=None)   # mémoire effective (composite)
    soil_memory_fast: GridField = field(default=None)   # annuelle (lerp 0.15)
    soil_memory_deep: GridField = field(default=None)   # décennale (lerp 0.02)
    litiere:          list = field(default=None)        # parcelles fraîches par plot (remplace om_fresh)
    structures:       list = field(default=None)        # bac à compost / pile à bois posés (⑤, §5)
    om_active:        GridField = field(default=None)   # MO partiellement digérée (réserve)
    om_stable:        GridField = field(default=None)   # humus (structure, rétention, mémoire)
    disturbance:      DisturbanceField = field(default=None)
    seed_bank:        SeedBank = field(default=None)
    temperature:      GridField = field(default=None)   # °C ambiant T_air (météo 02, rempli uniforme)
    # Microclimat de surface T_sol (sprint thermique ①) — surchauffe solaire par
    # plot avec inertie, calculée par `tick_thermique` depuis lumiere + T_air.
    # Lu par l'évaporation (`tick_hydrology`) ; spatialise l'assèchement soleil/ombre.
    temperature_sol:  GridField = field(default=None)
    # Manteau neigeux (sprint thermique ⑦) — scalaire d'état PAR TUILE ∈ [0,1] :
    # la neige tombe sur toute la tuile (pas un GridField). S'accumule les semaines
    # de Neige, fond ensuite (cf. `tick_snow`). Lu par `t_min_nuit_at` (gel nocturne)
    # où il s'ajoute au couvert de litière → effet igloo. À 0 au repos (golden NEUTRE
    # tant que le smoke ne neige pas, mais le catalogue météo décale les tirages → ⑦
    # re-fige LARGE par ailleurs).
    snow:             float = 0.0
    # Vie macroscopique observable (D31.1) — champs de population déterministes,
    # NOMMÉS par espèce (scission ④b/c/d) regroupés en catégories : ravageur
    # (puceron/limace/doryphore), auxiliaire (coccinelle/chrysope/carabe/merle/
    # hérisson), detritivore (lombric/cloporte) + N pollinisateurs PAR TYPE (abeille,
    # syrphe, papillon + bourdon/osmie ajoutés au catalogue ⑤ — registre §E, arc
    # pollinisation ②, remplacent l'ancien champ agrégé `pollinisateur`). Lus par
    # pollinator_reach (brassage, D31.2) et
    # la Vigueur macro via `pollinator_density`.
    populations:      dict = field(default=None)
    # Champs larvaires des ponts de cycle de vie (§D, tronçon ⑤) :
    # `chenille`/`chenille_nourrie` (→ papillon) et `syrphe_larve`/
    # `syrphe_larve_nourrie` (→ syrphe). Densité + maturité moyenne ∈[0,1] par
    # plot, PERSISTANTS. Pas un PopulationField (pas une guilde trophique : un
    # STADE traité à part) ; `chenille` est lu par l'herbivorie (perturbations),
    # `syrphe_larve` entre comme prédateur du ravageur (cf. _predator_field).
    larvae:           dict = field(default=None)
    # Butineurs du tick courant (arc pollinisation §F, tronçon ③) — agents
    # échantillonnés/marchés par engine._tick_butineurs depuis les champs
    # pollinisateurs. État TRANSIENT (recalculé chaque tick, pas de persistance
    # inter-tick, §F.2) : sert UNIQUEMENT au snapshot (rendu Godot). Hors golden.
    foragers:         list = field(default=None)
    # Phéromone d'alarme apienne (arc pollinisation ⑦, §J). Posée au plot d'une
    # action directe coûteuse (écraser une abeille / récolter sans équipement),
    # décroît au tick (`fields.alarme.tick_alarme`). PUR PUITS lu par le snapshot :
    # Godot anime la piqûre temps réel ; le moteur n'y réinjecte aucun champ figé →
    # golden NEUTRE (§J.4).
    alarme:           GridField = field(default=None)
    # pH du sol (sprint physico-chimie ①) — maître-régulateur de la chimie.
    # INITIALISÉ PAR HÉRITAGE du `soil_type` (PH_PAR_SOL) puis dérive décennale
    # (`tick_ph`, frère de soil_memory_deep). Au tronçon ① POSÉ mais lu par
    # PERSONNE → golden NEUTRE ; les lecteurs (lockout uptake, fenêtres d'espèce,
    # chlorose) arrivent aux tronçons ④/⑤.
    ph:               GridField = field(default=None)
    # Nutriments N/P/K (sprint physico-chimie ②→③) — éclatement du proxy
    # `fertilite` (SUPPRIMÉ au ③) pour porter la loi de Liebig (le minimum, pas
    # la somme). INITIALISÉS PAR HÉRITAGE du `soil_type` (NUTRIENT_INIT_PAR_SOL).
    # Depuis le ③ ils sont ACTIFS : nourris par la minéralisation splittée
    # (`tick_decomposition`), prélevés par l'uptake (`BESOIN` + Liebig), lessivés
    # différemment (`leach_factor`, N≫K>P) et fixés par les Fabaceae (effet famille
    # redirigé vers `n`). Les lecteurs lisent soit le `min` (Liebig, Vigueur) soit
    # l'index lisse `fertilite_index` (soil_memory/vitalité/succession).
    n:                GridField = field(default=None)
    p:                GridField = field(default=None)
    k:                GridField = field(default=None)

    def __post_init__(self):
        if self.humidite    is None: self.humidite    = GridField(self.rows, self.cols)
        if self.microbiome  is None: self.microbiome  = GridField(self.rows, self.cols)
        if self.lumiere     is None: self.lumiere     = LightField(self.rows, self.cols)
        if self.soil_memory is None:
            self.soil_memory = GridField(self.rows, self.cols, max_val=1.0)
        if self.soil_memory_fast is None:
            self.soil_memory_fast = GridField(self.rows, self.cols, max_val=1.0)
        if self.soil_memory_deep is None:
            self.soil_memory_deep = GridField(self.rows, self.cols, max_val=1.0)
        if self.litiere is None:
            # Grille de listes (un nouvel objet par plot, jamais partagé). Chaque
            # plot porte d'emblée sa parcelle `diffus` PERMANENTE (masse 0) qui
            # reçoit les exsudats et ne disparaît jamais (§1.1).
            self.litiere = [[[Parcelle("diffus", 0.0)] for _ in range(self.cols)]
                            for _ in range(self.rows)]
        if self.structures is None:
            self.structures = []          # aucune structure posée au repos (⑤A)
        if self.om_active is None:
            self.om_active = GridField(self.rows, self.cols, initial=0.0, max_val=10.0)
        if self.om_stable is None:
            self.om_stable = GridField(self.rows, self.cols, initial=0.0, max_val=10.0)
        if self.disturbance is None:
            self.disturbance = DisturbanceField(self.rows, self.cols)
        if self.seed_bank is None:
            self.seed_bank = SeedBank(self.rows, self.cols)
        if self.temperature is None:
            self.temperature = GridField(self.rows, self.cols,
                                         initial=T_AMBIENT_INIT,
                                         max_val=TEMP_MAX, min_val=TEMP_MIN)
        if self.temperature_sol is None:
            self.temperature_sol = GridField(self.rows, self.cols,
                                             initial=T_AMBIENT_INIT,
                                             max_val=TEMP_MAX, min_val=TEMP_MIN)
        if self.populations is None:
            # Guildes trophiques PUIS pollinisateurs par type (registre §E). Les
            # pollinisateurs sont sans prédateur/proie → leur ordre est neutre.
            specs = build_population_specs() + build_pollinator_specs()
            self.populations = {
                spec.name: PopulationField(spec, self.rows, self.cols)
                for spec in specs
            }
        # Ordre de tick = ordre trophique (ravageur d'abord ; cf. build_population_specs).
        self._population_order = list(self.populations.keys())
        if self.larvae is None:
            # Une grille par champ larvaire des ponts (§D) : densité + maturité,
            # bornées [0,1]. Démarrent à 0 → invariant golden (§D.6) tant qu'aucun
            # adulte ne pond.
            self.larvae = {name: GridField(self.rows, self.cols, max_val=1.0)
                           for name in larval_field_names(build_lifecycle_bridges())}
        if self.foragers is None:
            self.foragers = []          # aucun butineur tant que le tick n'a pas tourné
        if self.alarme is None:
            self.alarme = GridField(self.rows, self.cols, max_val=1.0)   # ⑦ §J, à 0 au repos
        if self.ph is None:
            # Héritage roche-mère : tout le plot d'une même tuile part au pH de son
            # `soil_type` (uniforme à l'init ; la dérive per-plot creuse ensuite des
            # écarts via litière/humidité). Borné [PH_MIN, PH_MAX] par le GridField.
            self.ph = GridField(self.rows, self.cols,
                                initial=PH_PAR_SOL.get(self.soil_type, PH_PAR_SOL["terre"]),
                                max_val=PH_MAX, min_val=PH_MIN)
        # Héritage roche-mère des trois nutriments (②) : (N, P, K) tirés de
        # NUTRIENT_INIT_PAR_SOL selon le `soil_type`, fallback "terre". Inertes au
        # ② (aucun tick), donc constants à leur valeur d'init.
        n0, p0, k0 = NUTRIENT_INIT_PAR_SOL.get(self.soil_type,
                                               NUTRIENT_INIT_PAR_SOL["terre"])
        if self.n is None: self.n = GridField(self.rows, self.cols, initial=n0, max_val=3.0)
        if self.p is None: self.p = GridField(self.rows, self.cols, initial=p0, max_val=3.0)
        if self.k is None: self.k = GridField(self.rows, self.cols, initial=k0, max_val=3.0)

    def get_field(self, name: str) -> GridField | None:
        return {
            "humidite":    self.humidite,
            "microbiome":  self.microbiome,
            "lumiere":     self.lumiere,
            "soil_memory": self.soil_memory,
            "disturbance":      self.disturbance,
            "om_active":        self.om_active,
            "om_stable":        self.om_stable,
            "soil_memory_fast": self.soil_memory_fast,
            "soil_memory_deep": self.soil_memory_deep,
            "temperature":      self.temperature,
            "temperature_sol":  self.temperature_sol,
            "ph":               self.ph,
            "n":                self.n,
            "p":                self.p,
            "k":                self.k,
        }.get(name)

    def fertilite_index(self, r: int, c: int) -> float:
        """Index nutritif LISSE dérivé (③) = moyenne des trois champs N/P/K, sur la
        même échelle [0,3] que l'ancien `fertilite`. Distinct du `min` de Liebig
        (que ressent la croissance/Vigueur) : c'est une grandeur stable pour les
        lecteurs qui veulent une fertilité agrégée (soil_memory, vitalité,
        succession) → seuils/normalisations historiques intacts en FORME."""
        return (self.n.at_plot(r, c)
                + self.p.at_plot(r, c)
                + self.k.at_plot(r, c)) / 3.0

    # --- Litière (couche fraîche : parcelles, remplace om_fresh) ---

    def om_fresh_at(self, r: int, c: int) -> float:
        """Σ des masses de parcelles du plot = ancien `om_fresh.at_plot(r,c)`."""
        return sum(p.masse for p in self.litiere[r][c])

    def bois_fresh_at(self, r: int, c: int) -> float:
        """Σ des masses de litière C-riche fraîche d'un plot (tissus `FAIM_N_TISSUS`
        = `bois`/BRF + `substrat` usé de champignons) — pilote la faim d'azote (⑦,
        §2.7). `substrat` reste INERTE tant qu'aucun acteur champignon ne le dépose
        (jamais dans le smoke) → cet accesseur ne voit que le `bois` aujourd'hui."""
        return sum(p.masse for p in self.litiere[r][c] if p.tissu in FAIM_N_TISSUS)

    def om_fresh_average(self) -> float:
        """Moyenne par plot de la litière fraîche = ancien `om_fresh.average()`."""
        n = self.rows * self.cols
        if not n:
            return 0.0
        total = sum(p.masse
                    for row in self.litiere for cell in row for p in cell)
        return total / n

    def deposer_litiere(self, r: int, c: int, tissu: str, masse: float) -> None:
        """Point d'entrée UNIQUE pour tout écrivain de matière fraîche.

        Fusion par tissu (`_fusion_parcelle`, §1.1) : masse cumulée, `age_sem`
        moyenné par la masse (le dépôt neuf, d'âge 0, rajeunit le tas). No-op si
        `masse ≤ 0`.
        """
        if masse <= 0.0:
            return
        _fusion_parcelle(self.litiere[r][c], tissu, masse)

    def deposer_dans_structure(self, struct: "Structure",
                               tissu: str, masse: float) -> None:
        """Ajoute de la matière au `contenu` d'une structure (miroir de
        `deposer_litiere`, même fusion par tissu). No-op si `masse ≤ 0` ou si le
        tissu est REFUSÉ par la structure (garde-fou §5 ; le geste pré-filtre)."""
        if masse <= 0.0 or not struct.accepte(tissu):
            return
        _fusion_parcelle(struct.contenu, tissu, masse)

    # --- Tick diffusion ---

    def tick_diffusion(self) -> None:
        """
        Diffusion spatiale des champs continus.
        Microbiome inertie 0.92 → aura progressive des aromatiques.
        """
        self.humidite.diffuse(inertia=HUMIDITY_INERTIA)
        # Les trois nutriments diffusent à la même inertie que l'ancien `fertilite`
        # (③ : le proxy unique éclaté en N/P/K, dynamique spatiale conservée).
        self.n.diffuse(inertia=FERTILITY_INERTIA)
        self.p.diffuse(inertia=FERTILITY_INERTIA)
        self.k.diffuse(inertia=FERTILITY_INERTIA)
        self.microbiome.diffuse(inertia=MICROBE_INERTIA)

    # --- Microclimat de surface (T_sol) ---

    def tick_thermique(self, saison: str, nebulosite: float = 0.0) -> None:
        """Recalcule `temperature_sol` (solaire·nébulosité − latente − isolation, ④).
        `nebulosite` = scalaire météo du tick (0 = ciel clair). Délègue au helper
        pur `thermique.tick_thermique` (container déjà dense)."""
        _tick_thermique(self, saison, nebulosite)

    def tick_ph(self, amend_dir: int = 0) -> None:
        """Fait dériver `ph` (décennal) vers sa cible héritée/acidifiée (physico-
        chimie ①). Délègue au helper PUR `ph.tick_ph` (container déjà dense). À
        appeler APRÈS la décompo (il lit la litière `om_fresh_at`). `amend_dir`
        = direction d'amendement de la tuile (⑥ : +1 chaux / −1 soufre / 0 sinon),
        calculée par la boucle (couche `fields` n'importe pas `world`). 0 par
        défaut → golden NEUTRE (aucune rondelle chaux/soufre dans le smoke)."""
        _tick_ph(self, amend_dir=amend_dir)

    def tick_snow(self, temp_now: float, is_neige: bool) -> None:
        """Met à jour le manteau neigeux `eco.snow` (⑦). Délègue au helper PUR
        `thermique.snow_next` (container déjà dense). Accumule si l'événement du
        tick est `Neige`, fond sinon (∝ température). À appeler AVANT le gel
        nocturne (qui lit `snow` via `t_min_nuit_at`)."""
        self.snow = _snow_next(self.snow, temp_now, is_neige)

    # --- Hydrologie ---

    def tick_hydrology(self, soil_type: str = "terre") -> None:
        """
        Cycle hydrologique complet. Ordre strict :
          1. Évaporation atmosphérique (couplée à la température : chaud → +)
          2. Pluie de fond (apport diffus constant)
          3. Rétention sol (couplage soil_memory)
          4. Drainage naturel — fonction du `soil_type` (§2.3 a, Q11)
        L'uptake racinaire est géré séparément dans engine.

        `soil_type` (passé par l'engine, qui porte la `Tile`) choisit le drainage
        dans `DRAINAGE_PAR_SOL` ; défaut/inconnu → `DRAINAGE` (terre = 0.993,
        valeur historique) → la tuile terre du golden reste bit-identique.
        """
        drainage = DRAINAGE_PAR_SOL.get(soil_type, DRAINAGE)
        for r in range(self.rows):
            for c in range(self.cols):
                h = self.humidite.data[r][c]
                # 1. Évaporation : multiplicateur de base diminué quand il fait
                # chaud (au-dessus de EVAP_TEMP_REF), borné par EVAP_MIN.
                # Lit DÉSORMAIS la T_sol microclimatique (sprint thermique ①) : un
                # plot ensoleillé surchauffe et s'assèche, un plot ombragé reste frais.
                temp = self.temperature_sol.data[r][c]
                evap = EVAPORATION - EVAP_TEMP_COEF * max(0.0, temp - EVAP_TEMP_REF)
                if evap < EVAP_MIN:
                    evap = EVAP_MIN
                h *= evap                                           # 1. évaporation
                h += BASE_RAIN                                      # 2. pluie de fond
                h += self.soil_memory.at_plot(r, c) * SOIL_RETENTION  # 3. rétention
                h *= drainage                                       # 4. drainage (par sol)
                self.humidite.set(r, c, h)

    # --- Lumière ---

    def tick_light(self, plants: list, saison: str,
                   house=None, tile_origin: tuple = (0.0, 0.0)) -> list[str]:
        """Recalcule le champ de lumière pour ce tick (+ ombre/albédo de la maison
        si `house` est fournie ; `tile_origin` = offset monde de la tuile)."""
        return self.lumiere.compute(plants, saison,
                                    house=house, tile_origin=tile_origin)

    # --- Perturbations ---

    def tick_disturbance(self, seed: int, week: int) -> None:
        """Met à jour le champ de perturbation spatiale (bruit déterministe)."""
        self.disturbance.tick(seed, week)

    # --- Vie macroscopique (D31.1) ---

    def tick_populations(self, tile, plants, week_in_year: int = 25) -> None:
        """
        Ticke les 4 champs de population dans l'ordre trophique. Le ravageur
        d'abord (il lit l'auxiliaire de la semaine précédente → décalage proie-
        prédateur), puis l'auxiliaire lit le ravageur fraîchement mis à jour.

        `week_in_year` pilote la porte saisonnière photopériodique des guildes
        (dormance hivernale / réveil printanier — CONCEPTION_SAISONNALITE_VIE_MACRO).
        Défaut 25 (plein été) pour les appels de test sans saison.

        À appeler APRÈS les autres champs (température, perturbation à jour).
        Pure lecture des champs existants : n'écrit QUE sur les champs de
        population, ne produit aucun log.
        """
        for name in self._population_order:
            popfield = self.populations[name]
            predator_fields = [pf for p in popfield.spec.predators
                               if (pf := self._predator_field(p)) is not None]
            popfield.tick(self, tile, plants, predator_fields, week_in_year)

    def _predator_field(self, name: str):
        """Résout un champ prédateur par nom : d'abord une guilde (`populations`),
        sinon un champ larvaire (`larvae`) — le syrphe_larve prédate le ravageur
        (§D.3.2) sans être une guilde. Retourne un objet `.at_plot`-compatible ou
        None. À densité nulle, contribue +0 → invariant golden (§D.6)."""
        f = self.populations.get(name)
        return f if f is not None else self.larvae.get(name)

    def tick_lifecycle_bridges(self, tile, plants, week_in_year: int = 25) -> None:
        """Ticke les ponts de cycle de vie (§D, tronçon ⑤) — APRÈS les guildes et
        les butineurs (ordre §K.2). Délègue au tick PUR `fields.lifecycle.tick_bridges`
        (ponte/maturation/famine/métamorphose), en lui passant la photopériode du
        moment (`daylength(week_in_year)`). N'écrit que `eco.larvae` + le terme-source
        de métamorphose dans les champs adultes (papillon/syrphe). Aucun log.

        No-op STRICT si aucun pont (registre vide) ou si chaque pont reste à 0
        (aucun adulte, ou hors fenêtre de ponte) → golden inchangé (§D.6)."""
        tick_bridges(self, tile, plants, build_lifecycle_bridges(),
                     daylength(week_in_year))

    def pollinator_density(self, r: int, c: int) -> float:
        """Densité pollinisatrice TOTALE en un plot = somme des champs par type
        (abeille + syrphe + papillon, §C/§E). Remplace l'ancien champ agrégé unique
        `pollinisateur` ; lue par `pollinator_reach` (brassage génétique) et la
        Vigueur macro. Bornée par la somme, non re-clampée (les lecteurs saturent)."""
        return sum(self.populations[n].at_plot(r, c)
                   for n in POLLINATOR_NAMES if n in self.populations)

    # --- Agrégation par CATÉGORIE (modèle B, CONCEPTION_FAUNE_DEDIEE.md §1.2) ---
    # La guilde n'est plus un champ stocké mais une VUE : la somme des espèces qui
    # partagent l'étiquette `spec.category`. Les consommateurs « par guilde » (santé
    # des plantes, vigueur macro) lisent ces agrégats au lieu de `populations[nom]`.
    # Tant qu'une catégorie n'a qu'un membre (④a), l'agrégat == le champ unique →
    # golden NEUTRE. Les pollinisateurs (PollinatorSpec, sans `category`) en sont
    # naturellement exclus (getattr → None).

    def category_fields(self, category: str) -> list:
        """Champs de population membres d'une CATÉGORIE (étiquette `spec.category`)."""
        return [pf for pf in self.populations.values()
                if getattr(pf.spec, "category", None) == category]

    def category_density(self, category: str, r: int, c: int) -> float:
        """Densité agrégée d'une catégorie = somme des densités des espèces membres.
        Remplace la lecture directe `populations["ravageur"].at_plot(...)`."""
        return sum(pf.at_plot(r, c) for pf in self.category_fields(category))

    # --- Banque de graines ---

    def tick_seed_bank(self, plants: list, seed: int = 0, week: int = 0) -> None:
        """Mise à jour hebdomadaire de la banque de graines."""
        self.seed_bank.tick_aging()
        self.seed_bank.tick_species_aging()
        self.seed_bank.tick_disturbance_enrichment(self.disturbance)
        self.seed_bank.tick_late_succession_enrichment(self.soil_memory_deep)
        self.seed_bank.tick_plant_production(plants)

    # --- Soil memory ---

    def tick_soil_memory(self, plants: list) -> None:
        """
        Mémoire du sol double temps :
          soil_memory_fast : lerp 0.15 — changements annuels (activité biologique)
          soil_memory_deep : lerp 0.02 — changements décennaux (structure, mycorhizes)
          soil_memory      : 0.7*fast + 0.3*deep (mémoire effective)

        Le sol ne peut pas être réinitialisé instantanément.
        """
        for r in range(self.rows):
            for c in range(self.cols):
                micro = self.microbiome.at_plot(r, c) / 3.0
                fert  = min(1.0, self.fertilite_index(r, c) / 3.0)
                om    = min(1.0, (self.om_fresh_at(r, c) +
                                  self.om_active.at_plot(r, c) +
                                  self.om_stable.at_plot(r, c)) / 5.0)

                # Signature des plantes sur ce plot
                sig = 0.0
                for p in plants:
                    if not p.is_alive:
                        continue
                    if (r, c) == p.position or (r, c) in p.root_plots:
                        family_sig = SOIL_SIGNATURE.get(p.plant_class.family, {})
                        sig += family_sig.get("microbiome", 0.0) * 0.5
                sig = max(-0.2, min(0.2, sig))

                # Cible écologique
                target = (micro * 0.4 + fert * 0.2
                          + om * 0.2 + (0.5 + sig) * 0.2)
                target = max(0.0, min(1.0, target))

                # Mémoire rapide (annuelle)
                fast = self.soil_memory_fast.at_plot(r, c)
                fast += (target - fast) * SOIL_FAST_RATE
                self.soil_memory_fast.set(r, c, fast)

                # Mémoire profonde (décennale)
                deep = self.soil_memory_deep.at_plot(r, c)
                deep += (target - deep) * SOIL_DEEP_RATE
                self.soil_memory_deep.set(r, c, deep)

                # Mémoire effective composite
                effective = fast * 0.7 + deep * 0.3
                self.soil_memory.set(r, c, effective)

    def decomp_speed(self, r: int, c: int) -> float:
        """Vitesse locale de décomposition (microbiome + bioturbation des vers) —
        facteur de la fragmentation des squelettes (`engine._tick_skeletons`, ②B) :
        un bois de squelette se fragmente au rythme du sol vivant local.

        NB : depuis le ④, `tick_decomposition` (inline) module EN PLUS la part
        biologique par la cloche pH `dispo(ph,"micro")` ; pas ici — la fragmentation
        mécanique/fongique du bois mort est moins sensible au pH que la
        minéralisation bactérienne (divergence assumée, calibrage post-test)."""
        micro = self.microbiome.at_plot(r, c) / 3.0
        speed = 0.5 + micro * 0.5
        worms = self.populations["lombric"] if self.populations else None
        if worms is not None:
            speed += WORM_DECOMP_BONUS * worms.at_plot(r, c)
        return speed

    def tick_decomposition(self) -> None:
        """
        Cycle biogéochimique hebdomadaire — cascade OM v4 (fresh → active → stable).

        Chaque compartiment se décompose à son propre rythme, modulé par le
        microbiome (sol vivant = recyclage rapide). La masse décomposée se
        répartit en trois : humification (compartiment suivant), minéralisation
        (→ N/P/K SPLITTÉE par tissu, §2.2), respiration (CO₂, perte nette).
        Aucune création de matière.

          fresh  ──décompose──┬─ humifie → active
                              ├─ minéralise → split_miner(tissu) → n/p/k
                              └─ respire (perdu)
          active ──décompose──┬─ humifie → stable
                              ├─ minéralise → split_miner("humus") → n/p/k
                              └─ respire (perdu)
          stable ──décompose──┬─ minéralise → split_miner("humus") → n/p/k
                              └─ respire (perdu)

        La litière feuillue nourrit surtout l'azote, le fruit la potasse, le bois
        peu (immobilisation). Puis lessivage DIFFÉRENCIÉ par nutriment, modulé par
        la CEC dérivée (texture + humus) : N≫K>P (§2.4/§2.5).
        """
        worms = self.populations["lombric"] if self.populations else None
        for r in range(self.rows):
            for c in range(self.cols):
                micro = self.microbiome.at_plot(r, c) / 3.0
                # ④ LOCKOUT pH : l'activité bactérienne suit une cloche autour du
                # neutre (ph → microbiome → minéralisation, couplage indirect sans
                # champ neuf). Module la part BIOLOGIQUE de la vitesse uniquement —
                # pas le socle abiotique (0.5) ni la bioturbation mécanique du ver.
                micro *= dispo(self.ph.at_plot(r, c), "micro")
                speed = 0.5 + micro * 0.5   # sol vivant décompose jusqu'à 2× plus vite
                # Bioturbation du LOMBRIC (④d : le ver, pas le cloporte, brasse l'humus
                # du sol) : accélère « un poil » la décompo locale (D31.2, option sobre ;
                # structure/aération = D30 différé). Cloporte = litière (dette si littéral).
                if worms is not None:
                    speed += WORM_DECOMP_BONUS * worms.at_plot(r, c)

                # Lectures AVANT toute mutation (ordre historique : d_active se
                # calcule sur l'active d'AVANT l'humification du frais → équivalence).
                fresh  = self.om_fresh_at(r, c)   # Σ parcelles, avant décompo (famine)
                active = self.om_active.data[r][c]
                stable = self.om_stable.data[r][c]

                # 1. Couche fraîche = parcelles de litière (§1.3). Chaque parcelle
                #    décompose à la cinétique de son tissu ; on accumule les flux
                #    humif/miner pour les appliquer en UN add (comme l'ancien fresh).
                cell = self.litiere[r][c]
                cell.sort(key=lambda p: TISSU_ORDER.index(p.tissu))
                fresh_humif = 0.0
                fresh_n = fresh_p = fresh_k = 0.0   # minéral splitté PAR tissu (§2.2)
                survivors = []
                for p in cell:
                    decay, humif, miner = TISSU[p.tissu]
                    d = p.masse * decay * speed
                    p.masse  -= d
                    p.age_sem += 1.0
                    fresh_humif += d * humif
                    dn, dp, dk = split_miner(p.tissu, d * miner)
                    fresh_n += dn; fresh_p += dp; fresh_k += dk
                    # (le reste est respiré — perte nette)
                    if p.tissu == "diffus" or p.masse > 1e-9:
                        survivors.append(p)   # `diffus` permanente même à masse 0
                self.litiere[r][c] = survivors

                # 2. Active   3. Stable
                d_active = active * OM_ACTIVE_DECAY * speed
                d_stable = stable * OM_STABLE_DECAY * speed

                self.om_active.add(r, c, -d_active + fresh_humif)
                self.om_stable.add(r, c, -d_stable + d_active * OM_ACTIVE_HUMIF)

                # Minéral issu des compartiments humifiés (sans tissu propre) :
                # ratio NPK « humus » moyen (§2.2). Bilan : frais splitté par tissu
                # + humus splitté → n/p/k (le reste respiré a déjà été ôté).
                humus_miner = d_active * OM_ACTIVE_MINER + d_stable * OM_STABLE_MINER
                dn, dp, dk = split_miner("humus", humus_miner)
                self.n.add(r, c, fresh_n + dn)
                self.p.add(r, c, fresh_p + dp)
                self.k.add(r, c, fresh_k + dk)

                # Puits microbien : sans carbone frais, les microbes meurent.
                # famine ∈ [0,1] : nulle si litière abondante, maximale si épuisée.
                famine = 1.0 - min(1.0, fresh / MICROBE_FOOD_REF)
                if famine > 0.0:
                    self.microbiome.data[r][c] *= (1.0 - MICROBE_DECAY_MAX * famine)

                # Lessivage DIFFÉRENCIÉ (§2.4) modulé par la CEC dérivée (§2.5) :
                # texture (CEC_PAR_SOL) + humus stable normalisé /5.0 (même échelle
                # que vitalité). N très mobile, P quasi nul, K moyen.
                om_n = min(1.0, self.om_stable.at_plot(r, c) / 5.0)
                cn = cec_norm_at(self.soil_type, om_n)
                self.n.data[r][c] *= leach_factor("N", cn)
                self.p.data[r][c] *= leach_factor("P", cn)
                self.k.data[r][c] *= leach_factor("K", cn)

    def tick_structures(self) -> None:
        """Maturation hebdomadaire du contenu des structures (⑤ phase B, §5.2).

        Décompo CONFINÉE, miroir de `tick_decomposition` : chaque parcelle du
        contenu mûrit à la cinétique de son tissu (`TISSU[tissu]`), la fraction
        humifiée+minéralisée s'accumule dans `compost_mur` (compost mûr, jauge
        mesurée §5.3 — épandable en phase C), le reste est respiré (perte nette)
        et vieillit (`age_sem++`). Le bac mûrit vite (tendres), la pile très
        lentement (`bois`). `retourner` (drapeau `retourne_restant`) MULTIPLIE la
        vitesse et LISSE les âges du contenu pendant `RETOURNE_DUREE` semaines.

        Aucun champ du sol n'est touché (philo #2) : la maturation reste confinée
        à la structure ; c'est `epandre` (phase C) qui restitue au sol. **No-op
        STRICT si `structures == []`** (invariant golden ⑤ : boucle vide → zéro
        écriture). Déterministe : structures dans l'ordre d'insertion, contenu
        trié `TISSU_ORDER`, zéro RNG.
        """
        for struct in self.structures:
            base = MATUR_BAC if struct.kind == "bac" else MATUR_PILE
            retourne = struct.retourne_restant > 0.0
            mult = MATUR_RETOURNE_MULT if retourne else 1.0
            struct.contenu.sort(key=lambda p: TISSU_ORDER.index(p.tissu))
            survivors = []
            for p in struct.contenu:
                decay, humif, miner = TISSU[p.tissu]
                d = p.masse * decay * base * mult
                p.masse  -= d
                p.age_sem += 1.0
                struct.compost_mur += d * (humif + miner)   # le reste est respiré
                if p.masse > 1e-9:
                    survivors.append(p)
            struct.contenu = survivors
            if retourne:
                _lisser_ages(struct.contenu)
                struct.retourne_restant -= 1.0

    def add_necromass(self, r: int, c: int,
                      biomass: float, harvested: bool = False,
                      tissu: str = "herbace") -> float:
        """
        Ajoute de la nécromasse au plot lors d'une mort ou récolte.
        harvested=True : une fraction est exportée (récolte) → moins de retour sol.
        Retourne la quantité effectivement déposée.

        `tissu` (décompo·compost ②, kickoff §A.2) : la couche fraîche est typée par
        constitution. Défaut `herbace` (tiges molles, résidus de récolte) → compat
        bit-identique avec ① ; les appelants raffinent (`feuille` pour les caducs
        via `sim.effects.tissu_mort`). Le `bois` du squelette mort se déposera
        lentement par fragmentation (phase B), PAS ici (la mort ne dépose que mou).
        """
        # Récolte exporte BIOMASS_EXPORT, mort laisse tout sur place.
        # La nécromasse fraîche entre par la litière (cascade ensuite).
        export_fraction = BIOMASS_EXPORT if harvested else 0.0
        deposited = biomass * (1.0 - export_fraction)
        self.deposer_litiere(r, c, tissu, deposited)
        return deposited

    # --- Météo ---

    def apply_weather(self, variable: str, delta: float,
                      row: int = None, col: int = None) -> None:
        f = self.get_field(variable)
        if f is None:
            return
        if row is not None:
            f.add(row, col, delta)
        else:
            for r in range(self.rows):
                for c in range(self.cols):
                    f.add(r, c, delta)

    # --- Uptake racinaire ---

    def plant_uptake(self, r: int, c: int, stage_index: int,
                      shade_memory: float = 0.0,
                      drought_memory: float = 0.0,
                      share: float = 1.0) -> dict[str, float]:
        """
        Consommation racinaire modulée par la mémoire physiologique.

        shade_memory  → réduit la transpiration (plante étiolée, moins de surface foliaire)
        drought_memory → réduit la consommation d'eau (racines adaptées, stomates fermés)
        share         → fraction prélevée sur CE plot (1/nb plots de l'empreinte
                        racinaire), pour répartir l'uptake sur root_plots sans
                        multiplier la quantité totale (chantier B).

        Rétroaction rhizosphère : un microbiome riche améliore l'assimilation des
        nutriments (bonus borné UPTAKE_MICRO_BONUS) — la boucle vertueuse côté plante.
        """
        micro_norm = min(1.0, self.microbiome.at_plot(r, c) / 3.0)
        # Asphyxie palier 1 (§2.3 b, doux & RÉVERSIBLE) : au-dessus de HUM_EXCES, le
        # sol gorgé devient anoxique → les racines boivent mal → l'uptake de TOUT
        # baisse ∝ l'excès courant (≠ mémoire : se lève dès que le sol s'assèche).
        # En dessous du seuil (toute la tuile terre) → facteur 1.0, aucun effet.
        hum_local = self.humidite.at_plot(r, c)
        excess_norm = min(1.0, max(0.0, (hum_local - HUM_EXCES) / (3.0 - HUM_EXCES)))
        asphyxie_factor = max(ASPHYXIE_UPTAKE_FLOOR,
                              1.0 - excess_norm * ASPHYXIE_UPTAKE_MALUS)
        consumed = {}
        for var, by_stage in UPTAKE.items():
            amount = by_stage.get(stage_index, 0.0) * share * asphyxie_factor
            if amount <= 0:
                continue
            if var == "humidite":
                # Ombre réduit la transpiration
                light = self.lumiere.at_plot(r, c)
                shade_factor = 1.0 - shade_memory * 0.2
                amount *= (0.5 + light * 0.5) * shade_factor
                # Stress hydrique adaptatif (plante économise l'eau)
                amount *= max(0.5, 1.0 - drought_memory * 0.3)
            f = self.get_field(var)
            real = min(amount, f.at_plot(r, c))
            if real > 0:
                f.add(r, c, -real)
                consumed[var] = round(real, 3)

        # Nutriments N/P/K (③) — prélèvement par BESOIN[stade] (REMPLACE
        # UPTAKE["fertilite"]). Chaque nutriment est plafonné par le champ local
        # (loi de Liebig : un sol carencé limite naturellement le prélèvement, sans
        # gate de croissance neuf — portage fidèle). Microbiome riche → meilleure
        # assimilation (bonus borné, ex-branche fertilite).
        # ④ LOCKOUT pH : le besoin est aussi modulé par la cloche dispo(ph, nut) — un
        # nutriment EN STOCK n'est pas forcément ASSIMILABLE (P bloqué hors zone
        # neutre, N peu sensible). Module un FLUX, pas la plante (philo #2).
        # ⑦ FAIM D'AZOTE : la litière C-riche fraîche (bois/BRF + substrat) immobilise
        # une part de l'azote LOCAL → seul `n − immob` est assimilable ce tick. Le
        # champ `n` n'est PAS amputé (on retire seulement le `real` réellement prélevé) :
        # le bridage est RECALCULÉ chaque tick depuis la masse de bois présente, donc
        # auto-réversible (bois mûri ⇒ immob → 0 ⇒ azote de nouveau disponible). La
        # plante ressent via l'uptake Liebig (③) qui plafonne sur ce N réduit → jaunit.
        ph_local = self.ph.at_plot(r, c)
        immob = immobilise_n(self.bois_fresh_at(r, c))
        for nut, fld in (("N", self.n), ("P", self.p), ("K", self.k)):
            besoin = (BESOIN[nut].get(stage_index, 0.0) * share * asphyxie_factor
                      * (1.0 + micro_norm * UPTAKE_MICRO_BONUS)
                      * dispo(ph_local, nut))
            if besoin <= 0:
                continue
            dispo_stock = fld.at_plot(r, c)
            if nut == "N":
                dispo_stock = max(0.0, dispo_stock - immob)   # part immobilisée non assimilable
            real = min(besoin, dispo_stock)
            if real > 0:
                fld.add(r, c, -real)
                consumed[nut.lower()] = round(real, 3)
        return consumed

    # --- Probabilité de maladie (hybride probabiliste) ---

    def disease_probability(self, r: int, c: int, base_rate: float = 0.3) -> float:
        """
        Probabilité de propagation maladie — réponse logistique.

        La réponse logistique produit :
          microbiome faible  → presque aucune protection
          microbiome moyen   → phase critique (grande sensibilité)
          microbiome mature  → protection forte et stable

        logistic(x, k=6) = 1 / (1 + exp(-k*(x-0.5)))
        protection = logistic(microbiome_normalisé)
        p = base_rate * (1 - protection)
        """
        micro_norm = min(1.0, self.microbiome.at_plot(r, c) / 3.0)
        protection = 1.0 / (1.0 + math.exp(-6.0 * (micro_norm - 0.5)))
        return base_rate * max(0.02, 1.0 - protection)

    # --- Vitalité (grandeur dérivée, non stockée) ---

    def vitalite(self, r: int, c: int) -> float:
        """
        Vitalité du sol en un plot — grandeur DÉRIVÉE calculée à la demande,
        jamais stockée (décision #2 : le Qi territorial = les champs existants).

        Synthèse lisible de la santé du sol vivant : vie microbienne, réserve de
        fertilité (om_active + fertilite), structure (humus), moins la perturbation.
        Bornée [0, 1]. Préfigure la Vigueur (D11) que plantes et joueur puiseront.
        """
        micro     = min(1.0, self.microbiome.at_plot(r, c) / 3.0)
        active    = min(1.0, self.om_active.at_plot(r, c) / 5.0)
        fert      = min(1.0, self.fertilite_index(r, c) / 3.0)
        structure = min(1.0, self.om_stable.at_plot(r, c) / 5.0)
        disturb   = self.disturbance.at_plot(r, c)
        v = (micro     * VIT_W_MICRO +
             active    * VIT_W_ACTIVE +
             fert      * VIT_W_FERT +
             structure * VIT_W_STRUCTURE -
             disturb   * VIT_W_DISTURB)
        return max(0.0, min(1.0, v))

    def vitalite_average(self) -> float:
        n = self.rows * self.cols
        if not n:
            return 0.0
        total = sum(self.vitalite(r, c)
                    for r in range(self.rows) for c in range(self.cols))
        return total / n

    # --- Résumé ---

    def summary(self) -> dict:
        om_total = (self.om_fresh_average() +
                    self.om_active.average() +
                    self.om_stable.average())
        return {
            "humidite":    round(self.humidite.average(),         3),
            "n":           round(self.n.average(),                3),
            "p":           round(self.p.average(),                3),
            "k":           round(self.k.average(),                3),
            "microbiome":  round(self.microbiome.average(),       3),
            "om_fresh":    round(self.om_fresh_average(),         3),
            "om_active":   round(self.om_active.average(),        3),
            "om_stable":   round(self.om_stable.average(),        3),
            "organic_mat": round(om_total,                        3),
            "lumiere_moy": round(self.lumiere.average(),          3),
            "soil_fast":   round(self.soil_memory_fast.average(), 3),
            "soil_deep":   round(self.soil_memory_deep.average(), 3),
            "soil_memory": round(self.soil_memory.average(),      3),
            "disturbance": round(self.disturbance.average(),      3),
            "vitalite":    round(self.vitalite_average(),         3),
        }

    def __repr__(self) -> str:
        s = self.summary()
        return (f"EcoFields[{self.tile_id}] "
                f"hum={s['humidite']} npk={s['n']}/{s['p']}/{s['k']} "
                f"micro={s['microbiome']} om={s['organic_mat']} "
                f"soil={s['soil_memory']}")


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def init_eco(tile_id: str, rows: int, cols: int,
             humidite: float = 0.0, fertilite: float = None,
             microbiome: float = 0.0, soil_type: str = "terre") -> EcoFields:
    """`fertilite` est un PARAM DE COMPAT (③ : le champ unique a disparu). Si fourni,
    il initialise les trois nutriments à la MÊME valeur uniforme (n=p=k=fertilite) ;
    si None (défaut), n/p/k gardent leur héritage `soil_type` (NUTRIENT_INIT_PAR_SOL)."""
    eco = EcoFields(tile_id=tile_id, rows=rows, cols=cols, soil_type=soil_type)
    for r in range(rows):
        for c in range(cols):
            eco.humidite.set(r, c, humidite)
            eco.microbiome.set(r, c, microbiome)
            if fertilite is not None:
                eco.n.set(r, c, fertilite)
                eco.p.set(r, c, fertilite)
                eco.k.set(r, c, fertilite)
    return eco


def inject_patch(eco: EcoFields, variable: str,
                 center_row: int, center_col: int,
                 value: float, radius: int = 1) -> None:
    f = eco.get_field(variable)
    if f is None:
        return
    f.add(center_row, center_col, value)
    for nr, nc in f.hex_neighbors(center_row, center_col):
        if radius >= 1:
            f.add(nr, nc, value * 0.4)
