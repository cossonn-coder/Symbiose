"""
SYMBIOSE — fields/ecofields/constants.py
Constantes de calibration écologique du conteneur EcoFields : hydrologie,
cascade OM tri-compartiment, microbiome, soil memory, mortalité, litière typée,
organes-fruits, uptake et signatures de sol par famille.

Valeurs PURES (aucune dépendance) — isolées ici pour que le conteneur
(`container.py`) reste lisible. Toute valeur historique est conservée à
l'identique (golden bit-identique).
"""

from __future__ import annotations

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

# --- Microclimat de surface T_sol (sprint thermique-microclimat, tronçon ①) ---
# Le champ `temperature_sol` (par plot) spatialise la thermique : un plot au soleil
# surchauffe au-dessus de T_air, un plot à l'ombre (maison/canopée) reste frais. La
# cible thermique est lissée temporellement (inertie du sol) vers laquelle T_sol
# converge tick après tick. Les termes refroidissement évaporatif (②), isolation par
# le couvert (③) et nébulosité (④) viendront s'ajouter à la cible aux tronçons suivants.
GAIN_SOLAIRE    = 15.0   # °C — surchauffe max d'un plot en plein soleil d'été (lum=1, été)
THERMAL_INERTIA = 0.5    # lissage temporel de T_sol vers sa cible (1 = pas d'inertie ; petit = sol très tamponné)
# Fraction du rayonnement d'été par saison : un soleil d'hiver chauffe moins le sol.
INTENSITE_SAISON = {"hiver": 0.35, "printemps": 0.70, "automne": 0.60, "ete": 1.0}
# Refroidissement évaporatif (tronçon ②) : l'eau qui s'évapore prend de l'énergie au
# sol (chaleur latente). Un sol saturé (hum=3 → norm=1) reste plus frais de REFROID_EVAP
# °C. C'est le terme qui crée le CERCLE VICIEUX de la sécheresse : sec → moins de
# refroidissement → plus chaud → évapore plus → encore plus sec (émergent recherché).
REFROID_EVAP    = 6.0    # °C — refroidissement max d'un sol saturé
# Isolation par le couvert (tronçon ③) : une litière dense (paillis naturel issu de
# la décompo) tamponne le sol et l'isole de la surchauffe solaire diurne. C'est le
# pendant thermique du paillage permacole, et une illustration de l'interconnexion
# des acteurs (la litière de la décompo agit sur la thermique). La masse de litière
# du plot (`om_fresh_at`) est normalisée par LITIERE_REF : au-delà, le couvert sature.
ISOLATION_COUVERT = 4.0  # °C — tampon max d'une litière dense saturée
LITIERE_REF       = 2.0  # masse de litière au-dessus de laquelle le couvert sature
# Nébulosité (tronçon ④) : un ciel couvert bloque le soleil → le sol chauffe moins.
# C'est le 1er terme où la MÉTÉO (événement `weather_at`) entre dans la carte T_sol.
# `nébulosité ∈ [0,1]` (0 = ciel clair, 1 = couvert total), lue dans la table
# NEBULOSITE indexée par `event.kind` (donnée PURE, pas d'import inverse vers `sim`).
# K_NEBUL_DIURNE = part de la surchauffe annulée par un ciel TOTALEMENT couvert :
# à nébulosité=1 il reste 20 % du gain solaire (les nuages ne sont pas opaques).
# La nébulosité est un scalaire PAR TICK (météo uniforme sur le monde, comme T_air)
# → passé en argument à `tick_thermique`, jamais un champ par plot.
K_NEBUL_DIURNE = 0.8
NEBULOSITE = {
    "Beau temps": 0.10, "Sécheresse": 0.05, "Canicule": 0.10, "Gelée tardive": 0.05,
    "Redoux": 0.60, "Pluie prolongée": 0.90, "Tempête": 0.80, "Grêle": 0.70,
    "Orage": 0.85, "Neige": 0.70,   # Orage/Neige réservés à ⑦ (inoffensifs ici)
}

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
