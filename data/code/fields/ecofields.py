"""
SYMBIOSE — fields/ecofields.py
Conteneur EcoFields : tous les champs écologiques continus d'une tuile
(hydrologie, OM tri-compartiment, microbiome, soil memory, lumière, perturbation,
banque de graines) + constantes de calibration écologique.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field

from fields.grids import GridField, DisturbanceField
from fields.light import LightField
from fields.seedbank import SeedBank
from fields.population import PopulationField, build_population_specs

# ---------------------------------------------------------------------------
# CONSTANTES ÉCOLOGIQUES
# ---------------------------------------------------------------------------

HUMIDITY_INERTIA  = 0.55

# Hydrologie
FERTILITY_INERTIA = 0.85
MICROBE_INERTIA   = 0.92   # plus diffusif pour aura basilic

BASE_RAIN      = 0.015
EVAPORATION    = 0.997
DRAINAGE       = 0.993   # drainage de référence (terre) — conservé comme fallback
SOIL_RETENTION = 0.010

# Drainage par type de sol (CONCEPTION_PLANTER_ARROSER §2.3 (a), Q8/Q11). Plus
# proche de 1 = MOINS d'eau évacuée par tick = sol qui RETIENT. La terre garde la
# valeur historique (0.993) → tuile terre du golden bit-identique. L'argile retient
# (s'engorge → asphyxie facile), le sable/roche drainent vite (asphyxie rare). Le
# remède au sur-arrosage = connaître son sol, PAS un geste `drainer` (Q8).
DRAINAGE_PAR_SOL = {
    "terre":  0.993,   # référence — VALEUR ACTUELLE inchangée
    "argile": 0.997,   # retient → s'engorge
    "sable":  0.985,   # draine vite → sèche vite
    "roche":  0.975,   # ruisselle → très drainant
}

# Modèle « eau » — asphyxie par excès (CONCEPTION_PLANTER_ARROSER §2.3 (b), Q11).
# Versant HAUT, miroir de la gradation sécheresse existante (engine `drought_*`).
# Échelle humidité = [0, 3]. Valeurs de DÉPART (calibrage post-test, cf. §4).
HUM_EXCES = 2.3   # seuil palier 1 : au-dessus, les racines boivent mal (anoxie) → uptake↓
HUM_NOYE  = 2.6   # seuil stagnation « noyé » (miroir haut du seuil « sec ») → ok_hum faux
ASPHYXIE_UPTAKE_MALUS = 0.5   # réduction max d'uptake à excès plein (hum=3) — palier 1, doux/réversible
ASPHYXIE_UPTAKE_FLOOR = 0.5   # plancher du facteur d'uptake (jamais 0 : racines réduites, pas mortes)
ASPHYXIE_MEMORY_LERP  = 0.05  # intégration lente de l'asphyxie — IDENTIQUE à drought_memory (symétrie)
ASPHYXIE_HEALTH_SEUIL = 0.10  # mémoire au-delà de laquelle la santé peut chuter (palier 2, « si ça dure »)
ASPHYXIE_RATE         = 0.04  # pente de la pression santé (proba/sem) — miroir de SEN_RATE

# Température ambiante (sous-sprint météo 02) — champ ambiant écrit chaque semaine
# par l'engine (normale saisonnière + deltas météo), lu par le gate de croissance
# et par l'évaporation ci-dessous.
T_AMBIENT_INIT = 11.0    # °C — initialisation (= T_MOY) avant la 1re écriture météo
TEMP_MIN       = -20.0   # plancher physique du champ (gel sévère)
TEMP_MAX       = 45.0    # plafond physique
# Couplage évaporation ↔ température : au-dessus d'une référence, plus il fait
# chaud, plus le sol perd d'humidité (canicule → stress hydrique émergent).
EVAP_TEMP_REF  = 11.0    # °C — référence (aucun surplus d'évaporation en dessous)
EVAP_TEMP_COEF = 0.0008  # perte d'humidité supplémentaire par °C au-dessus de la réf
EVAP_MIN       = 0.975   # borne basse du multiplicateur (n'assèche jamais brutalement)

# Cycle biogéochimique — OM v4 tri-compartiment (cascade fresh → active → stable)
# Taux de décomposition hebdomadaire par compartiment (avant modulation microbiome).
OM_FRESH_DECAY   = 0.080   # débris récents / sucres : rapide (semaines)
OM_ACTIVE_DECAY  = 0.018   # MO partiellement digérée : vitesse moyenne (mois)
OM_STABLE_DECAY  = 0.0006  # humus : très lent (décennies)

# Câblage D31.2 (option SOBRE du point ouvert vers de terre) : la bioturbation
# accélère « un poil » la décomposition/minéralisation locale. C'est le SEUL
# service rendu par le champ `vers_de_terre` à la sim pour l'instant ; le système
# complet structure/aération/infiltration du sol reste DIFFÉRÉ à D30. Borné et
# léger pour ne pas inventer D30 ici (cf. kickoff #4, CONCEPTION_VIE_MACRO.md §7).
WORM_DECOMP_BONUS = 0.25   # densité ver [0,1] → bonus additif à `speed` (knob, D31.2)

# Devenir de la masse décomposée de chaque compartiment.
# Trois destinations : humification (→ compartiment suivant), minéralisation
# (→ fertilite), respiration (→ CO₂, perte nette). Les trois somment à 1.0 :
# aucune création de matière, le reste est respiré.
OM_FRESH_HUMIF   = 0.45    # fresh → active
OM_FRESH_MINER   = 0.25    # fresh → fertilite
OM_ACTIVE_HUMIF  = 0.25    # active → stable
OM_ACTIVE_MINER  = 0.45    # active → fertilite (minéralisation principale)
OM_STABLE_MINER  = 0.40    # stable → fertilite (minéralisation lente)

# Constitution → cinétique de décomposition de la couche FRAÎCHE
# (CONCEPTION_DECOMPOSITION_COMPOST §1.2). La couche fraîche n'est plus un
# scalaire `om_fresh` mais une liste de PARCELLES par plot (cf. Parcelle).
# Colonnes : (decay base/sem, humifie→om_active, minéralise→fertilite) ; le
# reste (1 − humif − miner) est respiré (CO₂, perte nette — modèle v4 conservé).
#
# `diffus` (exsudats racinaires) REPREND les valeurs historiques de l'ancien
# `om_fresh` (OM_FRESH_DECAY/HUMIF/MINER) → sur le flux dominant le tick reste
# BIT-IDENTIQUE, et la dérive golden se limite aux tissus episodiques
# (nécromasse/injections en `herbace`). Les autres tissus = placeholders §1.2
# (calibrage post-test ; le doc conception propose diffus 0.50/0.15/0.55, à
# basculer une fois l'équivalence golden levée).
TISSU = {
    # tissu      decay                humif            miner
    "diffus":  (OM_FRESH_DECAY, OM_FRESH_HUMIF, OM_FRESH_MINER),  # = ancien om_fresh
    "feuille": (0.25,           0.30,           0.45),
    "fleur":   (0.30,           0.20,           0.50),
    "herbace": (0.15,           0.35,           0.35),
    "fruit":   (0.28,           0.20,           0.50),
    "bois":    (0.02,           0.55,           0.10),
}
# Ordre d'itération STABLE (déterminisme philo #3 : jamais dépendre de l'ordre
# d'insertion des dépôts). La fusion par tissu garantit ≤ 6 parcelles/plot.
TISSU_ORDER = ("diffus", "feuille", "fleur", "herbace", "fruit", "bois")

LEACHING_LOSS    = 0.999   # lessivage nutriments (perte fertilite/semaine)
BIOMASS_EXPORT   = 0.20    # fraction exportée à la récolte (le reste = nécromasse)

# Puits microbien — mortalité modulée par la disponibilité de carbone frais.
# Sans nourriture (om_fresh bas), les microbes respirent leurs réserves et
# meurent : le microbiome devient un solde apports (exsudats/OM) − pertes.
MICROBE_FOOD_REF  = 1.0    # om_fresh au-dessus duquel les microbes sont rassasiés
MICROBE_DECAY_MAX = 0.006  # déclin hebdomadaire max du microbiome à famine totale

# Boucle rhizosphère — exsudats racinaires (chantier A)
EXUDATE_BASE     = 0.060   # dépôt total à pleine photosynthèse (microbiome + om_fresh)
EXUDATE_OM_SHARE = 0.15    # part de l'exsudat versée à om_fresh (le reste → microbiome)
UPTAKE_MICRO_BONUS = 0.40  # bonus d'uptake fertilité à microbiome saturé (rétroaction)

# Vitalité dérivée — pondérations (cf. vitalite()), somme des positifs = 1.0
VIT_W_MICRO     = 0.35
VIT_W_ACTIVE    = 0.25
VIT_W_FERT      = 0.20
VIT_W_STRUCTURE = 0.20
VIT_W_DISTURB   = 0.15     # pénalité (soustraite)

# Soil memory
SOIL_FAST_RATE   = 0.15    # intégration rapide (annuelle)
SOIL_DEEP_RATE   = 0.02    # intégration lente (décennale)

# Mortalité réaliste (D27) — sénescence + santé dynamique
SENESCENCE_ONSET = 0.70   # début du déclin (× longévité)
SEN_RATE         = 0.04   # pente de la pression de sénescence (proba/sem à sen=1)
HEAL_RATE        = 0.06   # proba de remontée de santé/sem en bon milieu (Q=1)
HEAL_SEN_CUTOFF  = 0.50   # au-delà de cette sénescence, la guérison se coupe

# Mortalité réaliste (D27) — passe 2 : fonte, fongique, renouvellement, nécromasse
DAMPOFF_BASE      = 0.08   # fonte des semis (damping-off), base avant modulation
DAMPOFF_HUM_SEUIL = 0.50   # humidité normalisée au-delà de laquelle la fonte démarre
FUNGAL_BASE       = 0.04   # maladies fongiques adultes, base avant modulation
RESEED_RADIUS_CM  = 150.0  # rayon de dispersion du renouvellement (M7)
NECROMASS_PER_CM  = 0.03   # nécromasse déposée par cm de hauteur à la mort

# Litière `bois` déposée par cm de segment coupé (décompo·compost ②, kickoff §A.1).
# Aligné sur l'esprit de NECROMASS_PER_CM (proxy longueur ; le diamètre = raffinage
# futur). Knob, calibrage post-test. La taille (`tailler`) et l'écimage NET
# (`ecraser_plante`) déposent `Σ length_cm × BOIS_PAR_CM` du sous-arbre retiré.
BOIS_PAR_CM       = 0.03

# --- Squelette post-mortem (décompo·compost ②, phase B) --------------------
# À la mort, une plante ne disparaît plus : ses tissus MOUS tombent tout de suite
# (litière feuille/herbace, cf. tissu_mort), et sa part LIGNEUSE reste en squelette
# debout (`seche`) puis couché (`couchee`) qui se fragmente en litière `bois`
# semaine après semaine. Seules les plantes LIGNEUSES (PerennialWoody, reconnues
# par `age_curve`) ont une part de bois ; les herbacées/annuelles → 0 (retrait
# immédiat, équivalent à l'ancien filtre). Knobs, calibrage post-test.
FRAC_BOIS_MORT    = 0.45   # part ligneuse de la nécromasse d'une plante ligneuse
T_SECHE           = 6      # semaines debout (`seche`) avant de tomber (`couchee`)
FRAG_RATE         = 0.04   # fraction de `bois_restant` libérée/semaine (× vitesse locale)
ECRASER_FRAG_BOOST = 0.50  # part de `bois_restant` libérée d'un coup quand on écrase
                           # un squelette (phase C.2 : on le pousse au sol et on casse)

# --- Abscission d'automne (décompo·compost ②, phase C) ---------------------
# Les caducs (deciduous, PerennialWoody) larguent leur feuillage en fin d'automne
# → litière `feuille`. Événement léger, borné, déterministe (aucun RNG).
ABSCISSION_WEEKS  = (38, 39)   # 2 dernières semaines d'automne (saison = 27..39)
ABSCISSION_FRAC   = 0.15       # part de la nécromasse-hauteur larguée par semaine d'abscission

# --- Organes-fruits traçables (décompo·compost ③, absorbe D19) --------------
# Un fruit devient un état moteur : il NOUE (une fois/an, début d'été), MÛRIT
# chaque semaine, puis TOMBE en litière `fruit` s'il n'est pas cueilli (chute →
# cascade fertilité). Knobs CONSERVATIFS (la dérive golden doit rester petite),
# calibrage post-test. Déterministe : aucun RNG, sites triés (cf. organ_sites).
FRUIT_MASSE       = 0.15   # masse d'un fruit = litière `fruit` déposée à la chute (placeholder)
FRUIT_DMAT        = 0.08   # maturation/semaine : atteint 1.0 (mûr) en ~12-13 sem (été→automne)
MATURITE_CHUTE    = 1.3    # sur-maturité : au-delà, le fruit non cueilli tombe (fermentation = ④)

# Uptake racinaire par stade
UPTAKE = {
    "humidite":  {0: 0.05, 1: 0.10, 2: 0.18, 3: 0.12},
    "fertilite": {0: 0.02, 1: 0.05, 2: 0.08, 3: 0.05},
    "microbiome":{0: 0.00, 1: 0.01, 2: 0.02, 3: 0.01},
}

# Signature sol par famille (laissée après chaque saison)
SOIL_SIGNATURE = {
    "Fabaceae":   {"microbiome": +0.15, "fertilite": +0.10},
    "Solanaceae": {"microbiome": -0.05},
    "Asteraceae": {"microbiome": +0.05, "fertilite": +0.05},
    "Lamiaceae":  {"microbiome": +0.08},
}


# ---------------------------------------------------------------------------
# PARCELLE DE LITIÈRE — unité de stockage de la couche fraîche (remplace om_fresh)
# ---------------------------------------------------------------------------

@dataclass
class Parcelle:
    """Tas de litière d'un `tissu` donné sur un plot (CONCEPTION §1.1).

    La somme des masses des parcelles d'un plot = l'ancien `om_fresh` (lecture
    dérivée via `EcoFields.om_fresh_at`). `age_sem` (semaines depuis dépôt) sert
    aux sous-sprints ③④ (maturité fruit, signal animal) — non lu en ①.
    """
    tissu:   str
    masse:   float
    age_sem: float = 0.0


# ---------------------------------------------------------------------------
# ECOFIELDS — conteneur complet
# ---------------------------------------------------------------------------

@dataclass
class EcoFields:
    tile_id:    str
    rows:       int
    cols:       int

    humidite:         GridField = field(default=None)
    fertilite:        GridField = field(default=None)
    microbiome:       GridField = field(default=None)
    lumiere:          LightField = field(default=None)
    soil_memory:      GridField = field(default=None)   # mémoire effective (composite)
    soil_memory_fast: GridField = field(default=None)   # annuelle (lerp 0.15)
    soil_memory_deep: GridField = field(default=None)   # décennale (lerp 0.02)
    litiere:          list = field(default=None)        # parcelles fraîches par plot (remplace om_fresh)
    om_active:        GridField = field(default=None)   # MO partiellement digérée (réserve)
    om_stable:        GridField = field(default=None)   # humus (structure, rétention, mémoire)
    disturbance:      DisturbanceField = field(default=None)
    seed_bank:        SeedBank = field(default=None)
    temperature:      GridField = field(default=None)   # °C ambiant (météo 02)
    # Vie macroscopique observable (D31.1) — 4 champs de population déterministes
    # (ravageur, auxiliaire, pollinisateur, vers_de_terre). CALCULÉS mais PAS
    # encore lus par la santé/les services → golden INTACT (le câblage est D31.2).
    populations:      dict = field(default=None)

    def __post_init__(self):
        if self.humidite    is None: self.humidite    = GridField(self.rows, self.cols)
        if self.fertilite   is None: self.fertilite   = GridField(self.rows, self.cols)
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
        if self.populations is None:
            self.populations = {
                spec.name: PopulationField(spec, self.rows, self.cols)
                for spec in build_population_specs()
            }
        # Ordre de tick = ordre trophique (ravageur d'abord ; cf. build_population_specs).
        self._population_order = list(self.populations.keys())

    def get_field(self, name: str) -> GridField | None:
        return {
            "humidite":    self.humidite,
            "fertilite":   self.fertilite,
            "microbiome":  self.microbiome,
            "lumiere":     self.lumiere,
            "soil_memory": self.soil_memory,
            "disturbance":      self.disturbance,
            "om_active":        self.om_active,
            "om_stable":        self.om_stable,
            "soil_memory_fast": self.soil_memory_fast,
            "soil_memory_deep": self.soil_memory_deep,
            "temperature":      self.temperature,
        }.get(name)

    # --- Litière (couche fraîche : parcelles, remplace om_fresh) ---

    def om_fresh_at(self, r: int, c: int) -> float:
        """Σ des masses de parcelles du plot = ancien `om_fresh.at_plot(r,c)`."""
        return sum(p.masse for p in self.litiere[r][c])

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

        Fusion par tissu (bornage déterministe, §1.1) : si une parcelle de même
        `tissu` existe au plot → masse cumulée, `age_sem` = moyenne pondérée par
        la masse (le dépôt neuf, d'âge 0, rajeunit le tas). Sinon append.
        """
        if masse <= 0.0:
            return
        for p in self.litiere[r][c]:
            if p.tissu == tissu:
                total = p.masse + masse
                p.age_sem = (p.age_sem * p.masse) / total if total > 0 else 0.0
                p.masse = total
                return
        self.litiere[r][c].append(Parcelle(tissu, masse))

    # --- Tick diffusion ---

    def tick_diffusion(self) -> None:
        """
        Diffusion spatiale des champs continus.
        Microbiome inertie 0.92 → aura progressive des aromatiques.
        """
        self.humidite.diffuse(inertia=HUMIDITY_INERTIA)
        self.fertilite.diffuse(inertia=FERTILITY_INERTIA)
        self.microbiome.diffuse(inertia=MICROBE_INERTIA)

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
                temp = self.temperature.data[r][c]
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

    def tick_populations(self, tile, plants) -> None:
        """
        Ticke les 4 champs de population dans l'ordre trophique. Le ravageur
        d'abord (il lit l'auxiliaire de la semaine précédente → décalage proie-
        prédateur), puis l'auxiliaire lit le ravageur fraîchement mis à jour.

        À appeler APRÈS les autres champs (température, perturbation à jour).
        Pure lecture des champs existants : n'écrit QUE sur les champs de
        population, ne produit aucun log → golden INTACT (D31.1).
        """
        for name in self._population_order:
            popfield = self.populations[name]
            predator_fields = [self.populations[p]
                               for p in popfield.spec.predators
                               if p in self.populations]
            popfield.tick(self, tile, plants, predator_fields)

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
                fert  = min(1.0, self.fertilite.at_plot(r, c) / 3.0)
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
        facteur partagé par `tick_decomposition` (inline, golden figé) et la
        fragmentation des squelettes (`engine._tick_skeletons`, ②B). Même formule
        que la boucle de décompo → un bois de squelette se fragmente au rythme du
        sol vivant local."""
        micro = self.microbiome.at_plot(r, c) / 3.0
        speed = 0.5 + micro * 0.5
        worms = self.populations["vers_de_terre"] if self.populations else None
        if worms is not None:
            speed += WORM_DECOMP_BONUS * worms.at_plot(r, c)
        return speed

    def tick_decomposition(self) -> None:
        """
        Cycle biogéochimique hebdomadaire — cascade OM v4 (fresh → active → stable).

        Chaque compartiment se décompose à son propre rythme, modulé par le
        microbiome (sol vivant = recyclage rapide). La masse décomposée se
        répartit en trois : humification (compartiment suivant), minéralisation
        (→ fertilite), respiration (CO₂, perte nette). Aucune création de matière.

          fresh  ──décompose──┬─ humifie → active
                              ├─ minéralise → fertilite
                              └─ respire (perdu)
          active ──décompose──┬─ humifie → stable
                              ├─ minéralise → fertilite (∝ microbiome)
                              └─ respire (perdu)
          stable ──décompose──┬─ minéralise → fertilite
                              └─ respire (perdu)

        Puis lessivage lent de la fertilité.
        """
        worms = self.populations["vers_de_terre"] if self.populations else None
        for r in range(self.rows):
            for c in range(self.cols):
                micro = self.microbiome.at_plot(r, c) / 3.0
                speed = 0.5 + micro * 0.5   # sol vivant décompose jusqu'à 2× plus vite
                # Bioturbation des vers : accélère « un poil » la décomposition
                # locale (D31.2, option sobre ; structure/aération = D30 différé).
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
                fresh_miner = 0.0
                survivors = []
                for p in cell:
                    decay, humif, miner = TISSU[p.tissu]
                    d = p.masse * decay * speed
                    p.masse  -= d
                    p.age_sem += 1.0
                    fresh_humif += d * humif
                    fresh_miner += d * miner
                    # (le reste est respiré — perte nette)
                    if p.tissu == "diffus" or p.masse > 1e-9:
                        survivors.append(p)   # `diffus` permanente même à masse 0
                self.litiere[r][c] = survivors

                # 2. Active   3. Stable
                d_active = active * OM_ACTIVE_DECAY * speed
                d_stable = stable * OM_STABLE_DECAY * speed

                self.om_active.add(r, c, -d_active + fresh_humif)
                self.om_stable.add(r, c, -d_stable + d_active * OM_ACTIVE_HUMIF)

                released = (fresh_miner +
                            d_active * OM_ACTIVE_MINER +
                            d_stable * OM_STABLE_MINER)
                self.fertilite.add(r, c, released)

                # Puits microbien : sans carbone frais, les microbes meurent.
                # famine ∈ [0,1] : nulle si litière abondante, maximale si épuisée.
                famine = 1.0 - min(1.0, fresh / MICROBE_FOOD_REF)
                if famine > 0.0:
                    self.microbiome.data[r][c] *= (1.0 - MICROBE_DECAY_MAX * famine)

                # Lessivage nutriments
                self.fertilite.data[r][c] *= LEACHING_LOSS

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
            elif var == "fertilite":
                # Microbiome riche → meilleure assimilation des nutriments
                amount *= 1.0 + micro_norm * UPTAKE_MICRO_BONUS
            f = self.get_field(var)
            real = min(amount, f.at_plot(r, c))
            if real > 0:
                f.add(r, c, -real)
                consumed[var] = round(real, 3)
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
        fert      = min(1.0, self.fertilite.at_plot(r, c) / 3.0)
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
            "fertilite":   round(self.fertilite.average(),        3),
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
                f"hum={s['humidite']} fert={s['fertilite']} "
                f"micro={s['microbiome']} om={s['organic_mat']} "
                f"soil={s['soil_memory']}")

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def init_eco(tile_id: str, rows: int, cols: int,
             humidite: float = 0.0, fertilite: float = 0.0,
             microbiome: float = 0.0) -> EcoFields:
    eco = EcoFields(tile_id=tile_id, rows=rows, cols=cols)
    for r in range(rows):
        for c in range(cols):
            eco.humidite.set(r, c, humidite)
            eco.fertilite.set(r, c, fertilite)
            eco.microbiome.set(r, c, microbiome)
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
