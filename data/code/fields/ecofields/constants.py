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
# Évapotranspiration enrichie (sprint VENT & ÉVAPOTRANSPIRATION ②, §3) : on donne à
# l'évaporation les DEUX pilotes qui lui manquaient — le rayonnement (ciel clair) et
# le vent — sans quoi la rosée (apport des nuits claires) montait de façon monotone
# jusqu'à l'asphyxie (D39, pommier asphyxié à 19,5 ans). Termes ADDITIFS à la perte,
# greffés dans `tick_hydrology` (zéro nouvelle traversée).
#  • RAYONNEMENT : ciel clair (nébulosité→0) ⇒ forte évaporation diurne. C'est le
#    CONTRE-FLUX EXACT de la rosée — le même ciel clair qui condense la nuit assèche
#    le jour. C'est le terme dominant du rééquilibrage (le climat labo de
#    `test_senescence` est clair → ce terme y porte presque toute la correction).
#  • VENT : la masse d'air (uniforme, `wind_at` ①) balaie la couche limite humide au
#    ras du sol → évaporation ↑ (effet « dessèchement » de D37). Au tronçon ② c'est la
#    force de masse d'air uniforme ; le champ d'abri spatial par plot arrive au ③.
# Knobs post-test (calibrés pour faire repasser `test_senescence` au vert SANS
# assécher le jardin — `EVAP_MIN` reste le garde-fou anti-assèchement brutal).
EVAP_RAD_COEF  = 0.0042  # perte supplémentaire à ciel TOTALEMENT clair (nébulosité=0)
EVAP_WIND_COEF = 0.0035  # perte supplémentaire à vent de masse d'air force 1

# --- Champ d'abri spatial (sprint VENT & ÉVAPOTRANSPIRATION ③, §4/§2.4) ---
# `eco.vent` spatialise la masse d'air uniforme (②) : un obstacle (mur de maison,
# plante haute) projette une zone abritée SOUS LE VENT, force réduite, portée ∝
# hauteur. Les knobs ci-dessous gouvernent la géométrie (helper PUR `fields.abri`).
# Seule la MAISON et les plantes HAUTES comptent comme obstacles → tant que le smoke
# n'a pas de plante ≥ seuil, seul l'abri de la maison structure le champ (re-figeage
# golden MAÎTRISÉ, localisé au sillage de la maison).
ABRI_HAUTEUR_MIN_CM = 80.0    # une plante n'abrite qu'au-dessus de ce port (haie utile)
ABRI_PORTEE_HAUTEUR = 10.0    # longueur du sillage abrité = 10× la hauteur (règle réelle)
ABRI_REDUCTION_MAX  = 0.6     # part max de vent coupée juste sous l'obstacle (∈ [0,1[)
ABRI_RAYON_FRAC     = 0.5     # rayon mini de capsule-plante en fraction de PLOT_CM
ABRI_ANGULAR_STEP   = 0.262   # ~15° — grain du cache directionnel (recalcul si franchi)
ABRI_VENTURI_BOOST  = 0.15    # surcroît de vent dans le goulet en frange de sillage

# Refroidissement éolien — wind chill (sprint VENT & ÉVAPOTRANSPIRATION ③, §5.5) :
# le vent abaisse la température RESSENTIE nocturne (un abri RÉCHAUFFE la nuit,
# cohérent avec le brise-vent §4). Terme `−WINDCHILL_COEF·vent_local` ajouté à
# `t_min_nuit_at`. Lit `eco.vent[r,c]` spatialisé → un coin abrité gèle moins.
WINDCHILL_COEF = 0.6     # °C retirés à la T_min nocturne par unité de vent local

# --- Microclimat de surface T_sol (sprint thermique-microclimat, tronçon ①) ---
# Le champ `temperature_sol` (par plot) spatialise la thermique : un plot au soleil
# surchauffe au-dessus de T_air, un plot à l'ombre (maison/canopée) reste frais. La
# cible thermique est lissée temporellement (inertie du sol) vers laquelle T_sol
# converge tick après tick. Les termes refroidissement évaporatif (②), isolation par
# le couvert (③) et nébulosité (④) viendront s'ajouter à la cible aux tronçons suivants.
# Plancher froid de GERMINATION (sprint germination thermique, tronçon ③). Sous ce
# seuil de T_sol, AUCUNE graine ne lève, quelle que soit l'espèce : c'est le « zéro de
# végétation » (sous ~5 °C l'eau circule mal, les enzymes dorment). Porte BINAIRE
# multiplicative AVANT la cloche `bell(T_sol, t_germ_opt, t_germ_tol)` (cf.
# succession.py) — court-circuit dur qui empêche même une espèce à `tol` large de
# lever l'hiver. Lecteur côté `sim` (succession), pas `plants` (règle de couches : les
# `t_germ_opt/tol` restent littéraux sur PlantBase). Nommage cohérent avec
# `temp_min_growth=5.0` (familles.py). PLACEHOLDER, calibrage au banc ⑥.
T_GERM_FLOOR    = 5.0    # °C — sous ce seuil de T_sol, aucune germination (zéro de végétation)
# Décalage d'optimum thermique de germination par le gène `germination_thermique`
# (sprint germination thermique, tronçon ④). Le gène donne une VARIABILITÉ
# intra-espèce à la fenêtre de levée : `t_opt_eff = t_germ_opt − GERM_GENE_SHIFT·
# (gène − 1)`. Un gène > 1 abaisse l'optimum → la lignée lève plus au froid ; < 1
# le relève → lève plus tard. Neutre 1.0 ⇒ aucun décalage. C'est le ressort de la
# SÉLECTION DARWINIENNE ÉMERGENTE (zéro code dédié) : sur un plot froid, les
# lève-tôt grènent plus → le pool-sol dérive vers le froid au fil des saisons. Lu
# côté `sim` (succession), comme T_GERM_FLOOR (les `t_germ_opt/tol` restent
# littéraux sur PlantBase — règle de couches). PLACEHOLDER, calibrage au banc ⑥.
GERM_GENE_SHIFT = 3.5    # °C — abaissement d'optimum de germination par unité de gène
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

# T ressentie par la plante (tronçon ⑤) : le gate de croissance ne lit plus
# T_air nu mais un mélange air/sol local. α = poids de T_air ; (1−α) = poids
# de temperature_sol (microclimat déjà spatialisé). À α=0.5, air et sol pèsent
# autant. C'est ce qui spatialise ENFIN la croissance (GDD locaux émergents).
T_PLANTE_ALPHA = 0.5

# Gel nocturne (tronçon ⑥) : la nuit le soleil ne chauffe plus ; les zones
# DÉCOUVERTES rayonnent vers le ciel clair et gèlent le plus. T_min_nuit
# descend sous T_air d'autant que le sol est nu (1−couvert) et le ciel clair
# (1−nébulosité). La logique s'INVERSE par rapport au diurne : on ne réutilise
# PAS temperature_sol (le soleil ne joue plus la nuit), on calcule une carte
# nocturne séparée. RAYONNEMENT_NOCTURNE = chute max (ciel clair, sol nu).
RAYONNEMENT_NOCTURNE = 5.0

# Manteau neigeux (tronçon ⑦) : la neige s'accumule en un état persistant `eco.snow`
# ∈ [0,1] (manteau uniforme par tuile) qui ISOLE le sol — effet igloo. Un manteau
# épais s'ajoute au couvert de litière dans T_min_nuit : sous la neige, le sol ne
# rayonne plus → il ne gèle plus (contre-intuitif mais réel). Le manteau s'accumule
# les semaines de Neige et FOND ensuite, lentement au froid, vite au dégel (couplage
# température). Scalaire par tuile (la modulation par canopée = raffinage futur).
SNOW_ACCUM     = 0.5     # accumulation par semaine de Neige (manteau plein en ~2 sem)
SNOW_MELT_BASE = 0.05    # fonte de fond hebdomadaire, même au froid (sublimation/tassement)
SNOW_MELT_WARM = 0.03    # fonte supplémentaire par °C au-dessus de 0 (dégel)

# --- Transport éolien de la litière (sprint VENT & ÉVAPOTRANSPIRATION ⑦, §5.6) ---
# Le vent CHARRIE la litière LÉGÈRE de surface et la dépose SOUS LE VENT, là où le
# flux ralentit (zone abritée, faible `eco.vent`). Émergence : un coin au pied d'un
# brise-vent s'enrichit en matière organique (congère de feuilles). Helper PUR
# `fields/ecofields/transport.py`, passe CONDITIONNELLE (sautée les jours calmes).
#  - TRANSPORT_SEUIL : force de masse d'air (`wind_at`) sous laquelle la passe est
#    SAUTÉE (jour calme → coût nul, levier perf §7B). Sert AUSSI de seuil de masse
#    nette au-dessus duquel on émet le marqueur diégétique 🍃 (signe perçu).
#  - TRANSPORT_FRAC : fraction de litière transportable déplacée par unité de
#    DIFFÉRENTIEL de vent (vent[exposé] − vent[abrité]) vers le voisin sous le vent.
#    Petit : le vent EFFRITE le tas exposé, il ne le balaye pas d'un coup.
#  - TRANSPORT_TISSUS : seuls les tissus LÉGERS volent (feuilles mortes, brins
#    secs) ; bois/fruits/exsudats (`diffus`) restent au sol.
# Au smoke, le vent peut transporter de la litière abscission/herbacée → re-figeage
# golden MAÎTRISÉ ANNONCÉ (la litière de surface se redistribue par plot).
# PLACEHOLDERS, calibrage F5 / bancs d'essai.
TRANSPORT_SEUIL  = 0.35   # force de masse d'air sous laquelle on ne transporte rien (jour calme)
TRANSPORT_FRAC   = 0.20   # part de litière légère déplacée par unité de différentiel de vent
TRANSPORT_TISSUS = ("feuille", "herbace")   # tissus assez légers pour être charriés
TRANSPORT_LOG_SEUIL = 0.05   # masse nette charriée au-delà de laquelle on émet le signe 🍃

# --- Rosée & gelée blanche (sprint météo→champs ②, §3) ---------------------
# Face DOUCE du gel nocturne : on relit le MÊME thermomètre `t_min_nuit_at` (helper
# `rosee.tick_rosee`). Un point de rosée local est dérivé de l'humidité du SOL (pas
# de champ « humidité de l'air » dédié) ; la condensation déposée est de l'eau liquide
# (>0 °C → `humidite +`) ou du givre (≤0 °C → carte `eco.givre`, fonte DIFFÉRÉE quand
# T repasse > 0). Le sol nu + un peu humide + nuit claire est le grand capteur du
# matin → la rosée FREINE la spirale de dessèchement sans ressusciter un désert (§3.6).
#   t_rosée = T_air − ECART_ROSEE_SEC + GAIN_HUM_ROSEE · min(1, humidite/3)
#   cond    = max(0, t_rosée − t_min_nuit) · ROSEE_PAR_DEGRE
# - ECART_ROSEE_SEC : écart air↔point-de-rosée d'un sol totalement SEC (grand → peu de
#   rosée sur sol sec, point de rosée bas, §3.6).
# - GAIN_HUM_ROSEE : remontée du point de rosée avec l'humidité du sol ; à hum_norm=1
#   le point de rosée n'est plus qu'à (ECART_ROSEE_SEC − GAIN_HUM_ROSEE) sous T_air →
#   rosée FACILE sur sol frais.
# - ROSEE_PAR_DEGRE : eau condensée par °C SOUS le point de rosée (PETIT : un levier de
#   survie, pas une fontaine — calibrer pour que ce soit sensible sans noyer l'eau).
# - ROSEE_LOG_SEUIL : condensation/fonte totale par tuile au-dessus de laquelle on émet
#   le marqueur de log diégétique (filtre le bruit ; signe perçu le matin, philo #5).
# - GIVRE_SEVERITY_REF : RÉSERVÉE pour l'OPTION dégât foliaire (§3.5), DIFFÉRÉE au ②
#   (cf. note en fin de `rosee.py` — le socle ② = dépôt + fonte, sûr). Sévérité FAIBLE
#   (réf élevée → dégât plancher) si on la branche un jour.
# PLACEHOLDERS, calibrage F5 / bancs d'essai.
ECART_ROSEE_SEC   = 6.0     # °C — écart air↔point de rosée sur sol totalement sec
GAIN_HUM_ROSEE    = 5.0     # °C — remontée du point de rosée à humidité de sol pleine
ROSEE_PAR_DEGRE   = 0.010   # humidité déposée par °C sous le point de rosée
ROSEE_LOG_SEUIL   = 0.02    # condensation/fonte cumulée/tuile pour émettre un marqueur
GIVRE_SEVERITY_REF = 8.0    # réf de sévérité du dégât foliaire de givre (option §3.5, différée)

# --- Interconnexions vivantes de la rosée (sprint météo→champs ⑤, §6) ---
# La rosée du matin RELIE le vivant (règle « tout coexiste », 2026-06-16). Deux
# couplages SOBRES, bornés, déterministes, branchés sur la carte transiente
# `eco.rosee_last` (eau liquide déposée ce tick par `tick_rosee`, normalisée par
# ROSEE_SURFACE_REF) :
#  (A) FAUNE ABREUVÉE — la faune du MATIN (limace/cloporte) gagne un plancher
#      d'habitat les semaines à forte rosée (cf. `fields/population.py`, où vivent ses
#      constantes propres : la couche `fields/population` n'importe pas `ecofields`).
#  (B) CAPTATION FOLIAIRE — une canopée intercepte la rosée → le feuillage hydraté
#      ALLÈGE le stress hydrique de la plante (`_update_physiology`, sim/engine). On
#      RABOTE le `drought_stress` du tick ∝ rosée déposée sur l'empreinte foliaire,
#      normalisée par ROSEE_SURFACE_REF, borné par ROSEE_FOLIAIRE_MAX (effet marginal
#      mais réel, cohérent avec le poids « significatif » de la rosée sur le sol, §3.6).
#      Reste un LEVIER, pas une pluie.
# Invariant : `rosee_last` NUL partout (nuit douce/couverte) ⇒ aucun terme ne joue →
# comportement antérieur. La rosée DU SMOKE en pose → golden léger ANNONCÉ.
# PLACEHOLDERS, calibrage F5 / bancs d'essai.
ROSEE_SURFACE_REF     = 0.03   # eau liquide/plot saturant le signal de surface [→1]
ROSEE_FOLIAIRE_MAX    = 0.35   # raboteur max du stress hydrique foliaire (B), ∝ canopée

# --- Lessivage NPK AMPLIFIÉ par la pluie (sprint météo→champs ③, §4) ---
# Le lessivage passif existe DÉJÀ (`tick_decomposition` : `champ *= leach_factor(...)`,
# rétention modulée par la CEC = texture + humus). Ce tronçon NE LE RECRÉE PAS : il
# l'AMPLIFIE ∝ l'eau qui DRAINE réellement ce tick (la pluie qui s'écoule au fond
# emporte les ions mobiles). `tick_hydrology` retourne déjà la perte de drainage par
# plot ; on la mémorise (`_drainage_last`), on la normalise, et on élève le facteur de
# rétention à la puissance `facteur_pluie = 1 + LESSIVAGE_PLUIE_K · drainage_norm` :
#   facteur_pluie = 1   → leach_factor inchangé (= comportement ①, lessivage passif)
#   facteur_pluie > 1   → rétention^p < rétention → ON LESSIVE PLUS (orage drainant)
# Hiérarchie de mobilité N≫K>P (§2.4) : N pleine puissance, K atténué, P ÉPARGNÉ
# (puissance 1, jamais amplifié — le phosphore est quasi immobile).
# - DRAINAGE_PERTE_REF : perte de drainage (unités d'humidité) jugée « forte pluie qui
#   s'écoule » → normalise `drainage_norm = min(1, perte / réf)`. Réf basse car la
#   perte de fond d'un sol terre est petite (h·(1−0.993) ≈ 0.007·h).
# - FACTEUR_PLUIE_CAP : plafond DUR du facteur (un orage ne doit JAMAIS vider l'azote
#   en un seul tick — garde-fou du kickoff §B/Pièges).
# À LESSIVAGE_PLUIE_K=0 → comportement ① strictement inchangé (utile pour isoler la
# dérive golden). PLACEHOLDERS, calibrage F5 / bancs d'essai.
LESSIVAGE_PLUIE_K  = 1.5     # ampleur de l'amplification du lessivage par drainage
DRAINAGE_PERTE_REF = 0.02    # perte de drainage (unité humidité) → drainage_norm = 1
FACTEUR_PLUIE_CAP  = 3.0     # plafond dur du facteur_pluie (anti-vidage en un tick)
LESSIVAGE_K_ATTENUATION = 0.4  # part de l'amplification reçue par K (N=1, P=0)

# Cycle biogéochimique — OM v4 tri-compartiment (cascade fresh → active → stable)
# Taux de décomposition hebdomadaire par compartiment (avant modulation microbiome).
OM_FRESH_DECAY   = 0.080   # débris récents / sucres : rapide (semaines)
OM_ACTIVE_DECAY  = 0.018   # MO partiellement digérée : vitesse moyenne (mois)
OM_STABLE_DECAY  = 0.0006  # humus : très lent (décennies)

# Câblage D31.2 (option SOBRE du point ouvert vers de terre) : la bioturbation
# accélère « un poil » la décomposition/minéralisation locale. C'est le SEUL
# service rendu par le champ `lombric` (④d ; ex-`vers_de_terre`) à la sim ; le système
# complet structure/aération/infiltration du sol reste DIFFÉRÉ à D30. Borné et
# léger pour ne pas inventer D30 ici (cf. kickoff #4, docs/faune/vie_macro/conception_vie_macro.md §7).
WORM_DECOMP_BONUS = 0.25   # densité ver [0,1] → bonus additif à `speed` (knob, D31.2)

# --- Couverture du sol (sprint LUXURIANCE PAR STRATIFICATION ①, D65 §2.1) -----
# Champ scalaire `couverture_sol` ∈ [0,1] par plot = FRACTION du sol couverte par le
# feuillage des strates BASSES (sol + basse). Alimenté par SCATTER (stamp d'empreinte
# des plantes basses, cf. `couverture.py`), jamais par un sweep de grille. Socle du
# tronçon ② (gate d'établissement du clonal). Deux consommateurs écologiques ici
# (philo #2 : flux → contrainte, jamais de malus direct plante) :
#  (a) ÉVAPORATION — un sol couvert perd MOINS d'eau (l'eau reste sous le tapis).
#      `tick_hydrology` rapproche le multiplicateur d'évaporation de 1.0 (rétention)
#      ∝ couverture : `evap += (1−evap)·COUVERTURE_EVAP_FRAC·couverture`. La tuile 2
#      du golden porte du Clover (strate basse) → couverture > 0 → RE-FIGEAGE ANNONCÉ.
#  (b) GERMINATION D'ADVENTICES — au-dessus de COUVERTURE_ADVENTICE_SEUIL, le couvre-sol
#      ÉTOUFFE la levée spontanée des pionnières (`succession`) : bénéfice permacole réel.
#      Gate DÉTERMINISTE (pas de RNG) sur la seule germination férale (pas les grains
#      plantés, qui restent un geste délibéré du joueur).
# PLACEHOLDERS, calibrage F5 / bancs d'essai.
COUVERTURE_EVAP_FRAC     = 0.4   # part du chemin evap→1.0 (rétention) à couverture pleine
COUVERTURE_ADVENTICE_SEUIL = 0.5  # couverture au-delà de laquelle la germination férale est ÉTOUFFÉE (cutoff dur). ABAISSÉ 0.6→0.5 au sprint PERF ③ (vis A) : combiné à la réponse graduée (1−couverture)**COUVERTURE_GERM_EXP de `succession`, resserre le recrutement jusqu'au plateau de N (capacité de charge émergente, cf. sim/succession)
# Seuil de PERCEPTION du tapis pour la vue (sprint LUXURIANCE ⑥, exposition au pont) :
# le bloc creux `couverture` du snapshot n'inscrit que les plots dont la couverture
# dépasse ce plancher (sous quoi le tapis est invisible à l'œil). Purement cosmétique
# (aucun tick ne le lit) — comme SEUIL_FLAQUE pour l'eau de surface.
COUVERTURE_RENDU_SEUIL   = 0.05

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
    # `substrat` usé de culture de champignons (sprint pots/bacs ②, substrat
    # `mycelium_use`) : C-riche pré-digéré par le mycélium → décompo LENTE (entre
    # le bois et l'herbacé) mais déjà bien humifiée. Membre de `FAIM_N_TISSUS`
    # → immobilise l'azote tant qu'il est frais (faim d'azote initiale), PUIS se
    # minéralise lentement (§2 : « faim d'azote initiale forte PUIS libération »).
    # AJOUT golden-NEUTRE : aucune parcelle `substrat` n'existe dans le smoke
    # (seul un conteneur `mycelium_use` en pose, et le smoke n'en pose aucun).
    "substrat": (0.04,          0.45,           0.20),
    # Nécromasse de SPHAIGNE (sprint HYDROLOGIE & MARÉCAGES ⑤) : la tourbe. Tissu
    # quasi-INDÉCOMPOSABLE (phénols antiseptiques + anaérobie) → `decay` le plus BAS
    # du catalogue (< bois), forte humification, minéralisation infime. C'est le flux
    # (c) de l'ingénieur sphaigne : sa litière s'accumule sans se défaire → la MO
    # grossit → épaisseur/tourbe ÉMERGENT (aucun code neuf, `tick_epaisseur` existant).
    # AJOUT golden-NEUTRE : aucune parcelle `mousse` n'existe dans le smoke (la
    # sphaigne, `archetype=None`, n'y est jamais posée). Placé APRÈS `substrat` →
    # l'ordre des tissus tuile du golden est inchangé.
    "mousse":   (0.008,         0.60,           0.05),
}
# Ordre d'itération STABLE (déterminisme philo #3 : jamais dépendre de l'ordre
# d'insertion des dépôts). La fusion par tissu garantit ≤ 7 parcelles/plot.
# `substrat` placé EN FIN (après `bois`) : il n'apparaît que dans les mini-sols de
# conteneur, jamais sur une tuile → l'ordre des tissus tuile est inchangé (golden).
TISSU_ORDER = ("diffus", "feuille", "fleur", "herbace", "fruit", "bois", "substrat",
               "mousse")

LEACHING_LOSS    = 0.999   # lessivage nutriments (perte fertilite/semaine)
BIOMASS_EXPORT   = 0.20    # fraction exportée à la récolte (le reste = nécromasse)

# Puits microbien — mortalité modulée par la disponibilité de carbone frais.
# Sans nourriture (om_fresh bas), les microbes respirent leurs réserves et
# meurent : le microbiome devient un solde apports (exsudats/OM) − pertes.
MICROBE_FOOD_REF  = 1.0    # om_fresh au-dessus duquel les microbes sont rassasiés
MICROBE_DECAY_MAX = 0.006  # déclin hebdomadaire max du microbiome à famine totale

# --- Microbiome CLIMATIQUE (sprint météo→champs ④, CONCEPTION_METEO_CHAMPS §5) ---
# L'activité microbienne ne dépend pas que de la nourriture (famine) et du pH
# (lockout) : elle suit aussi le CLIMAT. Terme MULTIPLICATIF `f_clim = f_temp · f_hum`
# (PAS de champ neuf — on module le champ `microbiome` existant via la vitesse de
# décompo) calculé PUREMENT dans `thermique.py::microbe_clim_factor`. À f_clim=1
# (sol doux et frais), comportement strictement INCHANGÉ.
#
# - f_temp : CLOCHE gaussienne centrée sur l'optimum. Tombe vers 0 au gel (dormance)
#   ET à la canicule (stress thermique). exp(−((T_sol−OPT)/TOL)²).
# - f_hum  : ~0 au sol SEC (dormance des microbes), monte à 1 au sol FRAIS optimal,
#   puis REDESCEND un peu en saturation (anoxie → « léger ↓ » de la Pluie prolongée).
#   Échelle hum_norm = min(1, humidite/3), IDENTIQUE à `tick_thermique`.
# Conséquence émergente : sol chaud+humide recycle vite ; sol gelé/desséché stocke la
# litière sans la digérer (accumulation hivernale/sécheresse — voulu, pas un bug).
# Valeurs = PLACEHOLDERS calibrage F5 / bancs d'essai.
MICROBE_T_OPT      = 20.0   # °C — optimum d'activité microbienne (sommet de la cloche)
MICROBE_T_TOL      = 12.0   # °C — demi-largeur de la cloche (gel/canicule → f_temp → 0)
MICROBE_HUM_OPT    = 0.55   # hum_norm de l'optimum (sol frais) ; en deçà = sec → dormance
MICROBE_HUM_SAT_FLOOR = 0.7  # f_hum résiduel en SATURATION (hum_norm=1) — anoxie, léger ↓
MICROBE_CLIM_FLOOR = 0.05   # plancher de f_clim (jamais 0 dur : décompo abiotique persiste)

# Boucle rhizosphère — exsudats racinaires (chantier A)
EXUDATE_BASE     = 0.060   # dépôt total à pleine photosynthèse (microbiome + om_fresh)
EXUDATE_OM_SHARE = 0.15    # part de l'exsudat versée à om_fresh (le reste → microbiome)
UPTAKE_MICRO_BONUS = 0.40  # bonus d'uptake fertilité à microbiome saturé (rétroaction)

# Références d'EFFET « plein régime » du sol vivant (sprint CALIBRATION RÉALISTE ①).
# La métrique de vitalité SOL divisait le microbiome par 3.0 et l'om_active par 5.0 —
# des dénominateurs hérités de la SATURATION du champ (borne anti-emballement), PAS de
# sa plage d'OPÉRATION réelle. Résultat : même un plot au pic lisait « mort » (~0.01).
# On sépare ici l'échelle d'EFFET (lue par la VUE) de l'échelle de SATURATION (dynamique
# du champ, inchangée) — cf. 00_etat.md « Séparer deux références homonymes ».
#  • MICROBE_EFFECT_REF : microbiome « plein effet ». Plage réelle : équilibre moy ~0.05,
#    plot riche ~0.3-0.5 → un plot riche rend ≈0.7 d'effet à cette réf.
#  • OM_ACTIVE_REF : om_active « plein effet ». Plafond réel mesuré ~0.67 (÷5 l'écrasait).
# om_stable reste sur /5.0 (accumulateur centennal, jeune sol lit bas = VOULU, philo #7).
MICROBE_EFFECT_REF = 0.6
OM_ACTIVE_REF      = 1.0

# Vitalité dérivée — pondérations (cf. vitalite()), somme des positifs = 1.0.
# RÉÉQUILIBRÉ au sprint CALIBRATION RÉALISTE ① (ancien 0.35/0.25/0.20/0.20, disturb
# 0.15). Deux pathologies mesurées au banc justifiaient la dérive (kickoff §D, autorisé
# quand disturbance écrase la bande) :
#  (1) le microbiome (ex-poids DOMINANT 0.35) suit le flux de carbone et RELAXE vers son
#      équilibre bas (~0.03) : lourdement pondéré, il faisait lire un sol MÛR plus BAS
#      qu'un sol JEUNE (inversion — la métrique n'discriminait plus la maturité) ;
#  (2) `disturbance` sur ce monde reste ~0.5 CONSTANT (jeune comme mûr, dense comme
#      lâche) : à 0.15 c'était une taxe PLATE mangeant >40 % du signal, aplatissant tout.
# On transfère le poids vers les ACCUMULATEURS qui, eux, croissent avec la richesse du
# sol : om_active (signal dominant, humus actif qui nourrit) + om_stable (humus
# centennal, récompense le sol âgé). Résultat au banc : bande monotone et lisible
# (dense jeune ~0.12 → dense mûr ~0.26 → lâche dégradé ~0.04 ; grimpe encore avec
# l'accumulateur om_stable sur les décennies, philo #7 « jeune sol lit bas »).
VIT_W_MICRO     = 0.15
VIT_W_ACTIVE    = 0.45
VIT_W_FERT      = 0.15
VIT_W_STRUCTURE = 0.25
VIT_W_DISTURB   = 0.08     # pénalité (soustraite) — abaissée : taxe plate non discriminante

# Soil memory
SOIL_FAST_RATE   = 0.15    # intégration rapide (annuelle)
SOIL_DEEP_RATE   = 0.02    # intégration lente (décennale)

# Vitalité continue (sprint SANTÉ & RÉSILIENCE ①) — remplace l'ancienne santé
# entière `health` 0-3 par `vitalite ∈ [0,1]`. Pas de conversion : chaque ancien
# décrément/gain entier `±1` devient `±VITALITE_STEP`, si bien qu'à résilience
# neutre la vitalité SUIT exactement `health/3` d'antan (golden préservé sauf sur
# les voies où l'ancien `int()` arrondissait — cf. dégâts médiés).
VITALITE_STEP = 1.0 / 3.0

# Mortalité réaliste (D27) — sénescence + santé dynamique
SENESCENCE_ONSET = 0.70   # début du déclin (× longévité)
# Désynchronisation de l'ONSET de sénescence par le gène `phenologie_florale`
# (sprint DÉSYNC PHÉNOLOGIE ①). Même tempo de vie que la floraison/l'abscission :
# l'onset propre est `clamp(SENESCENCE_ONSET − SEN_ONSET_JITTER·(gène − 1), 0.05,
# 0.95)`. Un gène > 1 (individu PRÉCOCE) abaisse l'onset → il sénesce plus tôt ;
# < 1 le relève → plus tard. Neutre 1.0 ⇒ onset == SENESCENCE_ONSET (aucun
# décalage). ±σ(0.10) sur le gène ⇒ ±0.05 de fraction de longévité. Déterministe
# (le gène dérive d'un hash de position, aucun RNG vivant). Départ de calibrage.
SEN_ONSET_JITTER = 0.5
SEN_RATE         = 0.04   # pente de la pression de sénescence (proba/sem à sen=1)
HEAL_RATE        = 0.06   # proba de remontée de santé/sem en bon milieu (Q=1)
HEAL_SEN_CUTOFF  = 0.50   # au-delà de cette sénescence, la guérison se coupe

# Mortalité réaliste (D27) — passe 2 : fonte, fongique, renouvellement, nécromasse
DAMPOFF_BASE      = 0.08   # fonte des semis (damping-off), base avant modulation
DAMPOFF_HUM_SEUIL = 0.50   # humidité normalisée au-delà de laquelle la fonte démarre
FUNGAL_BASE       = 0.04   # maladies fongiques adultes, base avant modulation
# Vent × maladies fongiques (sprint VENT & ÉVAPOTRANSPIRATION ⑥, §5.4). Double
# tranchant : (1) le vent ASSÈCHE le feuillage → réduit la pression locale (le
# champignon a besoin d'eau ; la ventilation est un remède, pédagogie aération) ;
# (2) le vent DISPERSE les spores → une plante SOUS LE VENT d'un foyer infecté
# reçoit de l'inoculum (transport contaminant). Net = arbitrage local.
FUNGAL_VENT_DRY   = 0.7    # fraction max de pression fongique retirée par un feuillage bien venté
FUNGAL_SPORE_GAIN = 0.8    # gain de pression par unité d'inoculum reçu sous le vent
FUNGAL_INOC_SEUIL = 0.4    # infection_memory d'un voisin au-delà de laquelle il est un FOYER émetteur
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
# Sprint DÉSYNC PHÉNOLOGIE ① : le largage n'est plus un rendez-vous GLOBAL ; chaque
# caduc largue à SA propre semaine, dérivée du gène-tempo `phenologie_florale` :
# `w = round(ABSCISSION_BASE − ABSCISSION_JITTER·(gène − 1))`, bornée à
# [ABSCISSION_MIN, ABSCISSION_MAX]. Un gène > 1 (précoce) largue plus tôt. Dépôt
# UNIQUE annuel (au lieu de 2 semaines) → l'ordre de grandeur du total reste
# proche. ABSCISSION_WEEKS conservé (non utilisé par le nouveau chemin, gardé pour
# l'import public). Déterministe : le gène vient d'un hash, aucun RNG.
ABSCISSION_WEEKS  = (38, 39)   # (héritage) 2 dernières semaines d'automne (saison = 27..39)
ABSCISSION_FRAC   = 0.15       # part de la nécromasse-hauteur larguée à l'abscission
ABSCISSION_BASE   = 38         # semaine-pivot du largage (dans l'automne 27..39)
ABSCISSION_JITTER = 15.0       # ±σ(0.10) sur le gène ⇒ ±1.5 sem de décalage
ABSCISSION_MIN, ABSCISSION_MAX = 34, 39   # fenêtre d'automne bornée du largage
# Sprint DÉSYNC PHÉNOLOGIE ② (pont) : rampe de COLORATION automnale par-plante,
# hint PUR RENDU exporté par le snapshot (serialize.py). `automne ∈ [0,1]` monte
# linéairement sur les AUTOMNE_RAMP semaines qui PRÉCÈDENT la semaine d'abscission
# propre du caduc (semaine_abscission), atteint 1 juste avant le largage. Zéro
# effet moteur (la vue seule la lit) → golden NEUTRE.
AUTOMNE_RAMP      = 6           # semaines de virage foliaire avant l'abscission

# --- Organes-fruits traçables (décompo·compost ③, absorbe D19) --------------
# Un fruit devient un état moteur : il NOUE (une fois/an, début d'été), MÛRIT
# chaque semaine, puis TOMBE en litière `fruit` s'il n'est pas cueilli (chute →
# cascade fertilité). Knobs CONSERVATIFS (la dérive golden doit rester petite),
# calibrage post-test. Déterministe : aucun RNG, sites triés (cf. organ_sites).
FRUIT_MASSE       = 0.15   # masse d'un fruit = litière `fruit` déposée à la chute (placeholder)
FRUIT_DMAT        = 0.08   # maturation/semaine : atteint 1.0 (mûr) en ~12-13 sem (été→automne)
MATURITE_CHUTE    = 1.3    # sur-maturité : au-delà, le fruit non cueilli tombe (fermentation = ④)

# Uptake racinaire par stade (hors nutriments N/P/K, gérés à part par BESOIN +
# loi de Liebig depuis le tronçon ③ — la clé `fertilite` a disparu d'ici).
UPTAKE = {
    "humidite":  {0: 0.05, 1: 0.10, 2: 0.18, 3: 0.12},
    "microbiome":{0: 0.00, 1: 0.01, 2: 0.02, 3: 0.01},
}

# --- pH du sol (sprint physico-chimie, tronçon ①) -------------------------
# Le pH est le MAÎTRE-RÉGULATEUR de la chimie du sol : il décide quelle plante
# pousse où et combien d'un nutriment présent est réellement disponible (lockout,
# tronçon ④). Champ `ph` par plot, plage [PH_MIN, PH_MAX], INITIALISÉ PAR HÉRITAGE
# du `soil_type` (roche-mère, table PH_PAR_SOL) et dérivant DÉCENNALEMENT (lerp à
# très forte inertie, frère de soil_memory_deep) vers une cible acidifiée par la
# matière organique fraîche (acides humiques) et le lessivage (calcium lavé en
# climat humide). Au tronçon ① le champ est POSÉ mais lu par PERSONNE → golden
# NEUTRE. Valeurs PLACEHOLDER (calibrage post-test), cf. docs/champs/sol/conception_sol_ph.md §3.
PH_MIN, PH_MAX = 4.0, 8.5
PH_PAR_SOL   = {"terre": 6.8, "argile": 7.0, "sable": 5.8, "roche": 7.6}  # héritage roche-mère
PH_INERTIA   = 0.02          # dérive décennale (avant amortissement CEC, volet NPK)
ACIDIF_OM    = 0.30          # acidification par matière organique fraîche (litière)
ACIDIF_LEACH = 0.20          # acidification par lessivage (climat humide → calcium lavé)
# Amendement pH (tronçon ⑥) : rondelle `chaux` (signe +, remonte le pH) ou `soufre`
# (signe −, acidifie) posée sur la tuile pousse la CIBLE de dérive de ±AMEND_PUSH
# tant qu'elle est présente. Sur la CIBLE, pas sur `ph` directement → progressif sur
# plusieurs saisons (forte inertie PH_INERTIA), réversible (retrait → cible repart
# vers l'héritage), event-driven → golden NEUTRE (aucune rondelle dans le smoke).
AMEND_PUSH   = 0.15          # poussée pH/saison d'un amendement présent (signe selon chaux/soufre)

# --- Lockout : disponibilité en cloche (tronçon ④) ------------------------
# Le pH DONNE ENFIN du sens à `ph` (inerte au ①) : il module la DISPONIBILITÉ
# des nutriments présents (un nutriment en stock n'est pas forcément assimilable).
# Facteur gaussien `dispo_i(ph) = exp(−((ph − PH_OPT_i)/PH_WIDTH_i)²)` ∈ ]0,1],
# appliqué multiplicativement à l'uptake N/P/K (par BESOIN) ET à l'activité
# microbienne de la décompo (ph → microbiome → minéralisation, sans champ neuf).
# Pas un gate de croissance (philo #2 : on module un FLUX, jamais la plante).
#   - P centré 6.5, ÉTROIT (1.0) : bloqué en acide (fer/alu) ET alcalin (Ca) — le
#     cas pédagogique roi (« pourquoi mon phosphore ne passe pas »).
#   - N centré 6.8, LARGE (2.2) : peu sensible.
#   - K centré 6.5, intermédiaire (1.8).
#   - micro centré 6.8 (1.6) : activité bactérienne, pilote la vitesse de décompo.
# Sur les sols du smoke (terre 6.8, argile 7.0) dispo ≈ 0.9+ (proche des optima)
# → dérive golden faible & localisée. PLACEHOLDERS, calibrage post-test
# (docs/champs/sol/conception_sol_ph.md §3). La CHLOROSE alcaline (CHLOROSE_PH) est reportée au
# tronçon ⑤ : elle a besoin de la notion « acidophile » par espèce (ph_opt/ph_tol)
# qui n'existe pas encore — pas de proxy jetable ici (décision Nico, 2026-06-20).
PH_OPT   = {"N": 6.8, "P": 6.5, "K": 6.5, "micro": 6.8}
PH_WIDTH = {"N": 2.2, "P": 1.0, "K": 1.8, "micro": 1.6}

# --- Fenêtre pH par espèce + chlorose alcaline (tronçon ⑤) -----------------
# Le pH cessait de ne moduler QUE les nutriments (④) : chaque espèce reçoit
# maintenant une FENÊTRE d'acidité (`ph_opt`/`ph_tol`, attributs de classe posés
# côté `plants/base/familles.py`) lue en cloche `bell(ph, ph_opt, ph_tol)` à deux
# endroits — germination/succession (porte : on ne s'installe pas hors fenêtre)
# et croissance/vigueur (on dépérit doucement en bord de fenêtre, façade
# `vigueur_plante`). Le DÉFAUT d'espèce est NEUTRE (`ph_tol` LARGE, cf.
# PH_TOL_DEFAUT, défini comme littéral dans `familles.py` car la couche `plants`
# n'importe jamais `fields` — règle de couches) → `bell ≈ 1.0` sur toute la plage,
# une espèce non spécifiée est insensible au pH (golden ~neutre).
#
# CHLOROSE alcaline (reportée du ④) : une espèce ACIDOPHILE (`ph_opt` bas, sous
# SEUIL_ACIDOPHILE) sur sol ALCALIN (`ph > CHLOROSE_PH`) subit le lockout du fer
# → malus de vigueur (CHLOROSE_MALUS). Pas un gate de mort (philo #2) : un facteur
# qui fait DÉPÉRIR, pas disparaître. L'indice visuel jaunissement = tronçon ⑨ (vue).
# PLACEHOLDERS, calibrage post-test (docs/champs/sol/conception_sol_ph.md §2.2/§2.3/§3).
CHLOROSE_PH      = 7.6     # au-dessus, chlorose ferrique des acidophiles
SEUIL_ACIDOPHILE = 5.5     # ph_opt en deçà duquel l'espèce est dite « acidophile »
CHLOROSE_MALUS   = 0.5     # facteur de vigueur min à chlorose pleine

# --- Nutriments N/P/K (sprint physico-chimie, tronçon ②) ------------------
# Le proxy unique `fertilite` sera ÉCLATÉ en trois nutriments distincts —
# azote (n), phosphore (p), potasse (k) — pour porter la loi du minimum de
# Liebig (la croissance est plafonnée par le nutriment le plus rare, pas par
# leur somme). Au tronçon ② les trois champs sont POSÉS mais lus/écrits par
# PERSONNE (uptake, minéralisation, soil_memory, signatures tournent encore sur
# `fertilite` intact) → golden NEUTRE, exactement comme le pH au ①. Ils sont
# INITIALISÉS PAR HÉRITAGE du `soil_type` (roche-mère). Plage [0, 3] (max_val du
# GridField, comme l'ancien `fertilite`). Valeurs PLACEHOLDER (calibrage post-
# test), cf. docs/champs/sol/conception_sol_nutriments_npk.md §3. Le retrait de `fertilite`, le
# split de la minéralisation, Liebig, le lessivage différencié, la CEC et la
# signature explicite arrivent au tronçon ③ (LE gros re-figé).
NUTRIENT_INIT_PAR_SOL = {  # (N, P, K) hérités de la roche-mère
    "terre": (1.0, 0.8, 0.9), "argile": (0.9, 0.9, 1.1),
    "sable": (0.5, 0.4, 0.4), "roche": (0.4, 0.6, 0.5)}

# --- Bascule Liebig (tronçon ③, LE re-figé large) -------------------------
# La minéralisation de la litière ne nourrit plus un proxy unique `fertilite`
# mais se RÉPARTIT en N/P/K selon le TISSU décomposé (feuille riche en azote,
# bois pauvre et lent, fruit riche en potasse…). Ratios de partage de la part
# MINÉRALISÉE (le `miner` de TISSU, déjà ôté de l'humifié/respiré) : somme ≤ 1
# (le complément à 1 = minéral non capté, perte). `humus` sert aux compartiments
# om_active/om_stable, mélangés (sans tissu). PLACEHOLDERS, calibrage post-test.
NPK_RELEASE = {
    # tissu      N      P      K      (somme)
    "diffus":  {"N": 0.40, "P": 0.25, "K": 0.35},   # 1.00 — exsudats équilibrés
    "feuille": {"N": 0.55, "P": 0.20, "K": 0.25},   # 1.00 — feuillage azoté
    "fleur":   {"N": 0.45, "P": 0.25, "K": 0.30},   # 1.00
    "herbace": {"N": 0.45, "P": 0.25, "K": 0.30},   # 1.00 — tiges molles
    "fruit":   {"N": 0.30, "P": 0.25, "K": 0.45},   # 1.00 — potasse de fructification
    "bois":    {"N": 0.15, "P": 0.25, "K": 0.20},   # 0.60 — ligneux : capte peu (immobilisation)
    "substrat":{"N": 0.20, "P": 0.25, "K": 0.25},   # 0.70 — substrat usé : pauvre, capte peu (faim d'azote)
    "humus":   {"N": 0.40, "P": 0.30, "K": 0.30},   # 1.00 — om_active/stable mélangés
}

# Besoin d'uptake par stade ET par nutriment (REMPLACE UPTAKE["fertilite"]).
# Profils CONTRASTÉS (c'est là que naît la loi du minimum) : N porte le
# végétatif (pic adulte), P le jeune âge/racines, K la fructification (pic
# adulte/sénescent). Le prélèvement réel est borné par le stock du plot.
# PLACEHOLDERS, calibrage post-test.
BESOIN = {
    "N": {0: 0.01, 1: 0.04, 2: 0.06, 3: 0.03},
    "P": {0: 0.02, 1: 0.03, 2: 0.02, 3: 0.02},
    "K": {0: 0.01, 1: 0.02, 2: 0.05, 3: 0.05},
}

# Lessivage DIFFÉRENCIÉ par nutriment (fraction lavée/semaine AVANT modulation
# CEC) : N très mobile (lessive vite), P quasi immobile, K intermédiaire. Le
# facteur appliqué = 1 − LEACHING[i]·(1 − cec_norm) : un sol à forte CEC
# (argile/humus) RETIENT, un sable laisse tout filer. Remplace le LEACHING_LOSS
# unique (0.999). PLACEHOLDERS, calibrage post-test.
LEACHING = {"N": 0.12, "P": 0.005, "K": 0.05}

# Capacité d'échange cationique (CEC) — facteur DÉRIVÉ (jamais un champ) texture
# + humus, modulant le lessivage (ici) et plus tard le tampon pH (volet A) :
#     cec = CEC_PAR_SOL[soil_type] + CEC_OM_COEF · om_stable_norm   (borné [0,1])
# Argile/humus → CEC élevée (retient) ; sable → CEC basse (tout lessive).
CEC_PAR_SOL = {"terre": 0.5, "argile": 0.8, "sable": 0.2, "roche": 0.4}
CEC_OM_COEF = 0.5

# Faim d'azote (tronçon ⑦, §2.7) — une litière C-riche fraîche (bois/BRF + le
# substrat usé de culture de champignons, crochet vers le futur acteur champignon)
# pousse les microbes décomposeurs à IMMOBILISER temporairement l'azote du sol
# pour digérer ce carbone : `immobilise = FAIM_N_COEF · masse_C_fraiche`. C'est un
# prélèvement RÉVERSIBLE recalculé chaque tick depuis la masse de bois présente
# (pas de stock d'azote emprunté : tant que le bois est là, N reste bridé ; quand
# il a mûri, le bridage disparaît tout seul). `FAIM_N_TISSUS` = les tissus qui
# immobilisent ; `substrat` est INERTE (jamais produit tant que l'acteur champignon
# n'existe pas — pur crochet, zéro effet sur le smoke). PLACEHOLDER, calibrage post-test.
FAIM_N_COEF  = 0.20
FAIM_N_TISSUS = frozenset(("bois", "substrat"))
# NB : la FIXATION d'azote des Fabaceae (§2.6) n'a PAS besoin de constante dédiée
# ici — elle EST l'effet famille `inject_field` (familles.py) redirigé vers `n`
# au tronçon ③ : flux explicite, lisible, déjà dans la boucle d'effets.

# --- Structure / compaction du sol (sprint physico-chimie ⑧, dette D30) -----
# Champ `structure_sol ∈ [0,1]` (1 = grumeleux/aéré, 0 = compacté/battant), HÉRITÉ
# du `soil_type` (STRUCTURE_INIT_PAR_SOL) et dérivant LENTEMENT (STRUCT_INERTIA,
# frère du pH/soil_memory_deep) sous forces ± : bioturbation des vers (+) et racines
# pivots décompactantes (+) construisent les grumeaux ; la pluie battante sur sol nu
# (−) les détruit. Le calcul vit dans `structure.py` (helper PUR, container déjà
# dense). Trois LECTEURS (CONCEPTION_SOL_STRUCTURE §2.3) : l'infiltration de la pluie
# de fond (∝ structure, le reste ruisselle), l'aggravation de l'asphyxie (sol tassé +
# saturé → anoxie pire) et la pénétration racinaire (uptake ↓ en sol tassé). Le champ
# hérité ≠ 1.0 sur les tuiles du smoke → golden RE-FIGÉ MAÎTRISÉ (§4). PLACEHOLDERS,
# calibrage post-test (docs/champs/sol/conception_sol_structure.md §3).
STRUCTURE_INIT_PAR_SOL = {"terre": 0.7, "argile": 0.45, "sable": 0.6, "roche": 0.4}
STRUCT_INERTIA    = 0.05     # dérive lente (saisons) des forces biotiques/abiotiques
BIOTURB           = 0.30     # construction par les vers (× densité lombric [0,1])
RACINE_PIVOT      = 0.10     # décompactage par une racine pivot présente sur le plot
GRELINETTE_GAIN   = 0.15     # gain durable d'un passage de grelinette (geste, plein effet)
BECHAGE_MALUS     = 0.20     # tassement net d'un bêchage (geste, version sobre §2.2)
BATTANCE          = 0.15     # dégradation max par pluie battante sur sol totalement nu
STRUCT_UPTAKE_MIN = 0.5      # uptake racinaire résiduel en sol totalement compacté
# Pluie BATTANTE par événement météo (§2.1, terme −BATTANCE·pluie_norm·(1−couvert)) —
# fraction ∈[0,1] de la violence d'impact des gouttes sur le sol nu. Table indexée par
# `event.kind` (donnée PURE, pas d'import inverse vers `sim`), miroir de NEBULOSITE.
# Seules les pluies frappantes comptent ; la neige couvre sans taper (0). Défaut 0
# (Beau temps, Sécheresse, Canicule, Gelée tardive, Redoux, Tempête, Neige) →
# aucune battance ces semaines-là.
PRECIP_NORM = {"Pluie prolongée": 1.0, "Orage": 0.9, "Grêle": 0.7}

# Apport d'eau météo par événement (sprint météo→champs ①, §2.2) — donnée PURE,
# pas d'import inverse vers `sim`, miroir de PRECIP_NORM/NEBULOSITE. Remplace les
# deltas plats humidité de WEATHER_ALEA (Canicule/Sécheresse/Pluie/Orage) par un
# flux : l'apport est ajouté à BASE_RAIN puis INFILTRÉ ∝ structure du sol dans
# `tick_hydrology` (un sol grumeleux boit la pluie, un sol battu la laisse filer).
# Positif = pluie qui tombe ; négatif (Sécheresse) = pluie de FOND TARIE (on réduit
# l'apport, on ne retire JAMAIS d'eau arbitrairement — l'évaporation∝T_sol fait le
# reste). Borné côté hydrologie pour que BASE_RAIN + apport ≥ 0. Canicule absente
# (apport 0) : son assèchement ÉMERGE de l'évaporation montée par la T_sol chaude.
# Événements non listés (Beau temps, Gelée, Redoux, Tempête, Grêle, Neige) → 0 :
# aucun apport d'eau ces semaines-là. PLACEHOLDERS, calibrage F5 / bancs d'essai.
PLUIE_APPORT = {
    "Pluie prolongée": +0.012,
    "Orage":           +0.010,
    "Tempête":         +0.004,
    "Grêle":           +0.003,
    "Sécheresse":      -0.012,   # < −BASE_RAIN (0.015) en valeur absolue → apport net
                                 # encore positif, jamais d'eau soustraite (cf. borne)
}

# --- Mycélium — réseau fongique (sprint mycélium & interconnexions, tronçon ①) --
# Acteur NEUF (CONCEPTION_MYCELIUM_INTERCONNEXIONS §1). Un champ scalaire `mycelium`
# ∈ [0,1] (`GridField max_val=1.0`, granularité plot, zéro RNG) qui CROÎT sur le bois
# humide non travaillé et DÉCLINE au sec / quand le substrat s'épuise. Dynamique pure
# par tick (helper `mycelium.tick_mycelium`) :
#     croissance = MYCEL_K_G · substrat · humidite_norm · fenetre_temp
#     declin     = MYCEL_K_D · mycelium · (secheresse + epuisement_substrat)
#     mycelium  += croissance − declin                  (clampé [0,1] par le GridField)
# Au tronçon ① les TROIS rôles §2 (saprophyte/mycorhize/faune) sont DÉBRANCHÉS : le
# champ existe et tique, mais personne ne le LIT → aucun effet écologique en retour.
# Comme `mycelium = 0` partout au repos et que le smoke ne pose pas de bois colonisable
# notable, le golden vise BIT-IDENTIQUE (§1.3, garde-fou ①). PLACEHOLDERS, calibrage
# post-test (cf. CONCEPTION §1.2 + annexe knobs).
#   - `substrat` = carbone pondéré BOIS : litière C-riche (`bois_fresh_at`) + `om_active`,
#     normalisé par MYCEL_SUBSTRAT_REF ; `epuisement = 1 − min(1, substrat/REF)`.
#   - `humidite_norm` = humidité /3 (échelle [0,3]) ; `secheresse = 1 − humidite_norm`.
#   - `fenetre_temp` = cloche douce `bell(T_sol, OPT, TOL)` : le réseau ralentit au gel
#     et à la canicule, large (TOL grand → ≈1 sur la plage tempérée du smoke).
MYCEL_K_G          = 0.10   # gain de croissance hebdomadaire à conditions pleines
MYCEL_K_D          = 0.08   # taux de déclin hebdomadaire (sec + substrat épuisé)
MYCEL_SUBSTRAT_REF = 2.0    # masse C (bois+om_active) au-dessus de laquelle le substrat sature
MYCEL_OM_POIDS     = 0.5    # poids de `om_active` dans le substrat (le bois compte 1.0, sa spécialité)
MYCEL_TEMP_OPT     = 18.0   # °C — optimum thermique du réseau fongique
MYCEL_TEMP_TOL     = 12.0   # °C — largeur de la cloche (large → tempéré ≈ plein régime)

# --- Rôle SAPROPHYTE + LIANT (tronçon ②, §2/§2.1) -------------------------
# Premier rôle BRANCHÉ du mycélium : le champignon lignivore DIGÈRE le bois et
# LIE le sol. Effets émergents, jamais directs (philo #2), zéro RNG (philo #3).
#   - ALPHA_SAPRO : terme fongique sur la décompo du SEUL tissu `bois`
#     (`d *= 1 + ALPHA_SAPRO·mycelium`) — là où le réseau est installé, le bois
#     se minéralise/humifie plus vite ; sans réseau, décompo `bois` INCHANGÉE
#     (mycelium=0 ⇒ facteur 1.0 ⇒ bit-identique à AVANT). AUCUN autre tissu touché
#     (le champignon est spécialiste du ligneux). Re-figeage golden MAÎTRISÉ attendu.
#   - LIANT_K : glomaline / liant du sol — un petit ajout LENT à `om_stable`
#     ∝ mycelium, agrégé dans `tick_mycelium` (c'est le réseau qui structure
#     l'humus). TRÈS petit pour ne pas dériver la mémoire du sol au-delà du bois
#     (om_stable se décompose à 0.0006/sem : un apport trop fort exploserait l'humus).
# PLACEHOLDERS, calibrage post-test (CONCEPTION §2/§2.1).
ALPHA_SAPRO        = 1.5    # accélération max de la décompo `bois` à réseau saturé (×2.5)
LIANT_K            = 0.0005 # apport glomaline à `om_stable`/sem à mycelium=1 (très lent)

# --- Rôle MYCORHIZE (tronçon ③, §2/§2.2) ----------------------------------
# Second rôle BRANCHÉ : le réseau relie ses hyphes aux racines vivantes (wood-wide-
# web) et leur FAIT PASSER le phosphore — le nutriment le plus immobile du sol, que
# les racines nues atteignent mal. Là où `mycelium` est présent sous l'empreinte
# racinaire, le FLUX prélevable de `p` (P SEULEMENT, jamais N/K — décision figée ii)
# est multiplié par `(1 + MYCO_P_BONUS·mycelium)` dans `plant_uptake`.
# Philo #2 : on amplifie ce que le SOL REND DISPONIBLE (un flux), JAMAIS la plante.
# Le `min(besoin, dispo_stock)` qui suit garde le bornage par le stock (Liebig) → un
# sol pauvre en P ne fait pas de miracle. La fenêtre pH `dispo(ph,"P")` reste un
# facteur SÉPARÉ et limitant (le réseau aide à puiser, il ne déverrouille pas un pH
# défavorable). mycelium=0 ⇒ facteur 1.0 ⇒ uptake bit-identique à AVANT.
# Patron `UPTAKE_MICRO_BONUS=0.40`. PLACEHOLDER, calibrage post-test (CONCEPTION §2.2).
MYCO_P_BONUS       = 0.40   # bonus max de prélèvement de P à réseau fongique saturé

# --- Herbivorie RACINAIRE du campagnol → perte d'UPTAKE (sprint santé & résilience ③, §3) ---
# Le campagnol ronge racines/bulbes/collet → moins de chevelu racinaire fonctionnel →
# la plante prélève MOINS d'eau et de N/P/K (philo #2 : le campagnol n'inflige AUCUN
# malus direct de santé — hors annélation mécanique ; il AFFAME la plante par un FLUX
# d'uptake réduit, la souffrance émerge des voies eau/azote EXISTANTES). Trois leviers :
#   • `root_herbivory_memory` (état d'instance, lerp lent ∝ densité campagnol) intègre
#     l'exposition ; ROOT_HERBIVORY_MEMORY_LERP = miroir des autres mémoires (0.05).
#   • perte d'uptake ∝ mémoire, capée à ROOT_HERBIVORY_UPTAKE_MALUS (−50 % max), jamais
#     sous ROOT_UPTAKE_FLOOR (une plante rongée boit encore un minimum : racines
#     réduites, pas anéanties).
#   • la niche d'espèce `root_loss_tolerance_base` (racines profondes/mycorhizo-
#     dépendantes tolèrent mieux) DIVISE la perte, et la MYCORHIZE la compense
#     (MYCO_ROOT_COMPENS : le réseau touchant la racine relaie l'eau/les nutriments
#     que les racines rongées n'atteignent plus — même champ `mycelium` déjà lu pour P).
# À densité `herbivore_vertebre` nulle → mémoire 0 → root_factor = 1.0 → uptake
# bit-identique. PLACEHOLDERS, calibrage post-test (CONCEPTION §3).
ROOT_HERBIVORY_MEMORY_LERP  = 0.05   # intégration lente de la pression campagnol (miroir des autres mémoires)
ROOT_HERBIVORY_UPTAKE_MALUS = 0.5    # mémoire saturée → −50 % d'uptake max (avant tolérance/mycorhize)
ROOT_UPTAKE_FLOOR           = 0.3    # plancher du facteur d'uptake racinaire (jamais 0 : racines rongées, pas mortes)
MYCO_ROOT_COMPENS           = 0.5    # réseau mycorhizien saturé → compense la moitié de la perte racinaire

# --- COLONISATION FONGIQUE DU TAS + bêchage (tronçon ⑤, §3.3/§1.2) ----------
# Le bac/pile est un habitat fongique de choix (humide, riche en bois) → il se fait
# COLONISER par le réseau : `Structure.colonisation ∈ [0,1]` croît au tick tant qu'il
# reste du contenu à digérer, puis MODULE la maturation (le compost colonisé mûrit
# plus vite — voie fongique du §3.3) et ENSEMENCE `eco.mycelium` au plot d'ancrage
# (le tas vivant rayonne du réseau → la faune fongivore ④ et les carpophores s'y
# installent : c'est ainsi que la faune arrive sur le bac, §3.4, par le MÊME patron
# qu'④, sans terme neuf). PLACEHOLDERS, calibrage post-test.
#   - COLONISATION_K  : vitesse de colonisation du tas (par sem, tend vers 1).
#   - COLONISATION_MATUR : poids de la colonisation dans le boost de maturation
#     (`mult ×= 1 + COLONISATION_MATUR·colonisation`) — colonisé ⇒ mûrit plus vite.
#   - COLONISATION_SEED : fraction de la colonisation reversée au champ `mycelium`
#     au plot d'ancrage chaque tick (le tas ensemence le sol autour).
# Ces termes ne touchent QUE des structures posées : `eco.structures == []` au smoke
# golden/population ⇒ tick_structures no-op ⇒ golden NEUTRE (event-driven du joueur).
COLONISATION_K       = 0.10   # croissance hebdo de la colonisation fongique du tas
COLONISATION_MATUR   = 1.0    # un tas pleinement colonisé mûrit ×2 (voie fongique §3.3)
COLONISATION_SEED    = 0.05   # part de colonisation ensemencée dans `mycelium`/sem

# Quantum de `mycelium` retiré par un coup de BÊCHE (tronçon ⑤, §1.2, event-driven).
# MIROIR du malus microbiome/lombric/structure_sol de `becher` (gestes.py) : bêcher
# casse aussi le réseau fongique (double peine pédagogique), là où `grelinette`
# PRÉSERVE (ne touche pas `mycelium`). Add d'un négatif clampé à 0 par le GridField →
# no-op si le réseau est déjà nul. PLACEHOLDER, calibrage post-test (§1.2).
BECHAGE_MYCELIUM_MALUS = 0.5

# --- Conditions initiales riches & hétérogènes (D56, sprint bugs d'émergence ①) ---
# Aujourd'hui le sol part de zéro absolu pour l'humus (`om_stable=0`) et d'un plancher
# nul/uniforme pour les champs vivants — monde « fade » au F5 (S4). D56 enrichit les
# valeurs de DÉPART et leur donne une HÉTÉROGÉNÉITÉ SPATIALE déterministe par plot :
# certains secteurs partent avec un peu plus d'humus/nutriments → ils amorcent la
# succession des tardifs plus tôt (fondation du déverrouillage S3, tronçon ②) → deux
# jardins jamais identiques (philo #7). ZÉRO RNG : l'hétérogénéité dérive du `seed`
# GLOBAL + du hash du `tile_id` via `fields.noise._hash_noise(seed_tuile, 0, r, c)`
# (philo #3, terrain reproductible à seed fixe). PLACEHOLDERS, calibrage F5 / bancs.
#
# - OM_STABLE_INIT : humus de fond hérité (le sol vivant n'est jamais parti de zéro
#   absolu ; une friche porte déjà un peu de matière organique stabilisée). Petit
#   devant la cascade OM (om_stable se décompose à 0.0006/sem → apport durable, lent).
# - INIT_AMPLITUDE : amplitude de la modulation spatiale ∈ [0,1[. Chaque champ initial
#   est multiplié par `1 + INIT_AMPLITUDE·(2·bruit − 1)` (∈ [1−A, 1+A]), borné ≥ 0
#   par le GridField. À 0.30, un plot va de −30 % à +30 % de sa valeur de plancher.
OM_STABLE_INIT = 0.15   # humus de fond hérité (matière organique stabilisée de départ)
INIT_AMPLITUDE = 0.30   # amplitude de l'hétérogénéité spatiale des champs initiaux

# --- Épaisseur de sol visible (D57, sprint épaisseur de sol ①a) -------------
# Champ `epaisseur_sol` par plot (cm de sol foisonnant au-dessus de la roche-mère).
# La MO qui tombe ÉPAISSIT le sol (litière fraîche foisonnante), le tassement + la
# décompo la rognent, l'humus stable persiste et l'exhausse sur les ans → le sol
# MONTE/DESCEND visiblement (②, rendu). Modèle à RELAXATION vers une cible bulk-
# density dérivée des `om_*`, PAS un accumulateur (l'inertie asymétrique EST le seul
# état stocké → satisfait la règle « pas d'état superflu », philo #4) :
#   foisonnement_fresh = Σ_parcelles( masse · foisonnement(age_sem) )
#   cible = E_FRESH·foisonnement_fresh + E_ACTIVE·om_active + E_STABLE·om_stable
#   epaisseur += (cible − epaisseur)·taux_asym  − EPAISSEUR_EROSION   (borné ≥ 0)
# La litière JEUNE foisonne (matelas aéré) ; en vieillissant elle se PLAQUE
# (tassement, décompo) → `foisonnement(age) = 1/(1 + K_TASSE·age_sem)` décroît. La
# consommation (faune/mycélium/minéralisation) fait baisser `om_*` → la cible baisse
# → l'épaisseur SUIT (elle ne consomme RIEN : anti-double-comptage). Asymétrie :
# monte VITE (apport foisonnant), descend LENT (tassement/érosion progressifs).
# AUCUN effet en retour ce tronçon (eau + accès NPK = ①b) : le champ est POSÉ et
# tické, lu par PERSONNE → golden NEUTRE. PLACEHOLDERS, calibrage F5 / bancs d'essai.
#   - E_FRESH > E_ACTIVE > E_STABLE : la litière fraîche foisonne le plus (volume par
#     unité de masse), l'humus stable le moins (dense, tassé) mais PERSISTE.
#   - K_TASSE : vitesse de plaquage de la litière avec l'âge (grand → se plaque vite).
#   - TAUX_MONTEE > TAUX_DESCENTE (∈ ]0,1[) : inertie asymétrique (monte vite,
#     descend lentement — un sol se construit plus vite qu'il ne s'érode sous couvert).
#   - EPAISSEUR_EROSION : rognage naturel/semaine (pluie, minéralisation, tassement de
#     fond) — petit, ramène vers le plancher minéral en l'absence d'apport.
# EPAISSEUR_MAX : plafond physique du champ (borne du GridField) — un sol ne monte pas
# indéfiniment ; ①b vérifiera l'anti-emballement sur 500 ans.
E_FRESH           = 8.0    # cm d'épaisseur par unité de litière fraîche PLEINEMENT foisonnante
E_ACTIVE          = 4.0    # cm par unité de MO active (partiellement digérée, mi-tassée)
E_STABLE          = 2.0    # cm par unité d'humus stable (dense mais durable — le socle)
K_TASSE           = 0.08   # plaquage de la litière avec l'âge (foisonnement = 1/(1+K·age_sem))
TAUX_MONTEE       = 0.30   # part de l'écart à la cible comblée/sem quand le sol MONTE
TAUX_DESCENTE     = 0.05   # part comblée/sem quand il DESCEND (bien plus lent — asymétrie)
EPAISSEUR_EROSION = 0.02   # cm rognés/sem (voies naturelles : pluie, tassement de fond)
EPAISSEUR_MAX     = 60.0   # cm — plafond physique du champ (borne GridField, anti-emballement)

# --- Effets écologiques en retour de l'épaisseur (D57, sprint épaisseur ①b) ---
# L'épaisseur AGIT sur l'écologie via DEUX flux du sol (jamais un bonus direct sur
# la plante — philo #2 : la plante répond émergemment à un sol plus/moins profond).
# Les deux lisent l'épaisseur du tick PRÉCÉDENT (hydro/uptake tournent AVANT
# `tick_epaisseur`, 13b-bis) → décalage 1 tick UNIFORME, déterministe (voulu, ①a).
#  - EPAISSEUR_NORM_REF : borne haute PLAUSIBLE (cm) qui normalise le champ vers
#    [0,1] pour les deux effets (`ep_n = min(1, epaisseur / réf)`). ≪ EPAISSEUR_MAX
#    (60, plafond physique) : un sol de jardin foisonnant tourne autour de quelques cm
#    à ~20 cm, pas 60 → la réf est le point où l'effet SATURE, pas la borne dure.
#  - EPAISSEUR_RETENTION : rétention d'eau supplémentaire max (à ep_n=1) ajoutée dans
#    `tick_hydrology`, MODULÉE par la composition via `cec_norm_at` (patron nutriments) :
#    effet PLUS FORT sur sable pauvre/drainant que sur argile déjà rétentrice. MODÉRÉ :
#    un sol épais TAMPONNE la sécheresse, il ne la rend pas impossible. Le revers
#    asphyxie (D39, sol gorgé) n'est PAS bridé — conséquence émergente assumée.
#  - EPAISSEUR_NPK_BONUS : amplificateur MAX (à ep_n=1) de la FRACTION du stock N/P/K
#    mise à l'uptake dans `plant_uptake` (`dispo_stock ×= 1 + bonus·ep_n`, patron
#    MYCO_P_BONUS). Un sol épais met une plus grande part du stock à disposition.
#    ⚠️ CROISE D41 (famine édaphique VOULUE) : à ep_n=0 le facteur vaut EXACTEMENT 1.0
#    → jamais PIRE que le baseline D41, l'effet ne fait qu'ATTÉNUER la carence sur sol
#    épais/humifère, il ne la SUPPRIME jamais (l'amplification est petite et bornée, et
#    le `min(besoin, dispo_stock)` de Liebig plafonne toujours par le stock réel : un sol
#    pauvre en N ne fait pas de miracle même épais). PLACEHOLDERS, calibrage F5 / bancs.
EPAISSEUR_NORM_REF   = 20.0   # cm — épaisseur où les effets SATURENT (ep_n = 1)
EPAISSEUR_RETENTION  = 0.006  # rétention d'eau max/sem d'un sol pleinement épais (× compo)
EPAISSEUR_NPK_BONUS  = 0.30   # amplification max de la fraction de stock N/P/K à l'uptake

# --- Altitude — micro-relief topographique (sprint hydrologie & marécages ①) ---
# Champ `altitude` par plot (cm de micro-relief du TERRAIN au-dessus d'une référence
# arbitraire). C'est la TOPOGRAPHIE du sol — à NE PAS confondre avec `epaisseur_sol`
# (D57), qui mesure l'HUMUS foisonnant : un sol épais est riche en matière organique,
# pas forcément « haut » au sens hydraulique. L'altitude, elle, est un socle
# géométrique FIXE (aucun tick ne l'écrit ; seuls les gestes `creuser`/`drainer` de
# ⑦ la modifieront, event-driven). Elle est initialisée HÉTÉROGÈNE par un bruit
# spatial déterministe (`init_eco`, canal de hash DÉCORRÉLÉ de l'humus → relief et
# fertilité ne coïncident pas) → deux terrains n'ont jamais le même micro-relief
# (philo #3/#7). Au tronçon ① elle est POSÉE mais lue par PERSONNE (aucun tick, aucun
# effet) → golden NEUTRE. C'est le support de l'ÉCOULEMENT (②, l'eau ruisselle du haut
# vers le bas) et de la surface hydraulique visible au relief (⑦/⑧). PLACEHOLDERS,
# calibrage F5 (dénivelé de jardin plausible ~0–40 cm, à l'œil sur le relief extrudé).
#   - ALT_BASE : altitude de référence (cm) — plancher autour duquel oscille le relief.
#   - ALT_AMPLITUDE : amplitude ± du micro-relief (cm) ; le facteur de bruit ∈ [−1,1]
#     module ALT_BASE de ±ALT_AMPLITUDE → dénivelé total ≈ 2·ALT_AMPLITUDE. Borné ≥ 0
#     par le GridField (un facteur extrême ne descend jamais sous le niveau zéro).
ALT_BASE      = 20.0   # cm — altitude de référence (mi-hauteur du micro-relief)
ALT_AMPLITUDE = 20.0   # cm — amplitude ± du micro-relief (dénivelé jardin ~0–40 cm)

# --- Catena topographique des champs édaphiques (sprint DIVERSITÉ FONDATRICE ②) ---
# Sous le flag `heterogene` (sites monde-réel : golden, main, pont, bancs), les champs
# de SOL STATIQUE non nuls (ph, n, p, k, structure_sol, microbiome) démarrent
# HÉTÉROGÈNES, structurés par la TOPOGRAPHIE déjà posée (`altitude`) : une CATENA. Le
# fond (altitude basse) concentre l'eau, la matière et les nutriments lessivés du haut
# → riche ; le versant (altitude haute) draine, se lessive, s'appauvrit mais se
# structure mieux (moins de battance). Le paysage devient LISIBLE (philo #5/#6) et
# jamais identique (philo #7). Zéro RNG (philo #3) : la part topo LIT l'altitude, la
# part bruit propre dérive d'un canal de hash DÉCORRÉLÉ par champ (`tile_id + suffixe`).
#   facteur = 1 + amplitude·(poids_topo·topo + (1−poids_topo)·bruit)
#   topo    = sens_topo · recentre(altitude ∈ [ALT_BASE±ALT_AMPLITUDE] → [−1,1])
#   bruit   = 2·_hash_noise(canal_champ, 0, r, c) − 1   ∈ [−1,1]
# `GridField.set` BORNE déjà chaque champ (min/max, portes pH/NPK) → les facteurs
# extrêmes sont écrêtés, jamais de plot hors-fenêtre catastrophique. `humidite` est
# EXCLUE (le ruissellement la creuse déjà depuis l'altitude → redondant) ; `om_stable`
# et `altitude` NON retouchés (déjà hétérogènes, D56 calibré).
#  - amplitude PROPRE par champ : pH PETITE (portes `bell` dures, faim d'azote,
#    mort carence D41 → hors-fenêtre si trop fort) ; NPK/microbiome plus larges ;
#    structure intermédiaire.
#  - poids_topo : part du facteur pilotée par le relief (le reste = bruit décorrélé).
#    Grand → gradient de catena bien lisible ; petit → surtout mosaïque de bruit.
#  - sens_topo : −1 = riche EN BAS (altitude basse ; NPK/microbiome, eau/matière
#    concentrées au fond) ; +1 = plus fort EN HAUT (structure : versant mieux drainé,
#    moins battu). Le pH varie surtout par roche-mère → poids_topo BAS.
# PLACEHOLDERS, calibrage F5 / bancs d'essai. Ne PAS relever « pour voir » (portes dures).
PH_INIT_AMPLITUDE        = 0.03   # PETITE — le pH ne doit pas sortir des fenêtres d'espèce
NPK_INIT_AMPLITUDE       = 0.20   # N/P/K : mosaïque édaphique bien marquée (faune variée)
STRUCTURE_INIT_AMPLITUDE = 0.10   # structure du sol : gradient modéré
MICROBIOME_INIT_AMPLITUDE = 0.20  # microbiome : suit la richesse du fond
CATENA_POIDS_TOPO = {  # part du facteur pilotée par l'altitude (le reste = bruit propre)
    "ph": 0.2, "n": 0.6, "p": 0.6, "k": 0.6, "structure_sol": 0.4, "microbiome": 0.6}
CATENA_SENS_TOPO = {   # signe du gradient topo : −1 = riche en bas, +1 = plus fort en haut
    "ph": -1.0, "n": -1.0, "p": -1.0, "k": -1.0, "structure_sol": 1.0, "microbiome": -1.0}

# --- Eau de surface & ruissellement (sprint hydrologie & marécages ②) --------
# Une LAME D'EAU de surface `eau_surface` (NEUF), DISTINCTE de `humidite` (eau des
# PORES, ce que boivent les racines). C'est elle qui RUISSELLE (du haut vers le bas
# sur la surface hydraulique `altitude + epaisseur_sol`) et fait la FLAQUE. Découplage
# physiquement juste : les pores saturent (≤ HUM_CAP), le surplus reste EN SURFACE.
#  - HUM_CAP : capacité des pores = plafond de `humidite` (3.0, borne actuelle du
#    GridField). Au-delà, `tick_hydrology` CAPTURE l'excédent `h − HUM_CAP` dans
#    `eau_surface` au lieu de le laisser écrêter silencieusement par le GridField
#    (= l'eau qu'on jetait jusqu'ici). Aligné sur la borne réelle du champ humidité.
#  - RUISSELLEMENT_FRACTION : part de la lame d'un plot qui S'ÉCOULE vers ses voisins
#    DESCENDANTS par tick (répartie ∝ la pente, multiple-flow-direction). < 1 : l'eau
#    met plusieurs ticks à dévaler une longue pente (inertie du ruissellement lent).
#  - INFILTRATION_SURFACE : eau de la lame qui REDESCEND dans `humidite` par tick, si
#    le sol peut encore boire (`humidite < HUM_CAP`) — MODULÉE par la structure du sol
#    (un sol grumeleux réabsorbe la flaque, un sol battu/argileux la garde en surface).
#    Borne par tick (une flaque profonde ne s'infiltre pas d'un coup).
#  - EVAP_SURFACE : fraction de la lame ÉVAPORÉE par tick (lame libre → évapore plus
#    vite que l'eau des pores ; couplage simple, pas de nouvelle traversée météo).
#  - SEUIL_FLAQUE : lame au-dessus de laquelle le plot AFFICHE une flaque (vue §7 / ⑧)
#    et, au ③, alimente `marais_memory`. Ici PUR seuil de perception (pas d'effet moteur).
# Aux BORDS du monde, l'eau qui ruisselle au-delà du dernier plot est PERDUE (exutoire
# implicite — pas de tuile voisine simulée). Conservation de masse À L'INTÉRIEUR : ce
# qui sort d'un plot entre chez ses voisins (double buffer → indépendant de l'ordre de
# balayage, déterminisme philo #3, zéro RNG). PLACEHOLDERS, calibrage F5 / banc ③.
HUM_CAP               = 3.0    # capacité des pores (= plafond humidité) ; surplus → eau_surface
RUISSELLEMENT_FRACTION = 0.5   # part de la lame écoulée/tick vers les voisins plus bas
INFILTRATION_SURFACE  = 0.15   # eau de surface réabsorbée/tick par le sol (× structure)
EVAP_SURFACE          = 0.20   # fraction de la lame évaporée/tick (lame libre)
SEUIL_FLAQUE          = 0.10   # lame au-dessus de laquelle on perçoit une flaque (vue)

# --- Marécage : mémoire + hystérèse (sprint hydrologie & marécages ③) ---------
# Une FLAQUE qui DURE fait basculer le plot en MARÉCAGE — un état PERSISTANT du
# milieu (philo #4), pas un type de sol scripté (philo #2/#6). On INTÈGRE une
# mémoire lente `marais_memory` ∈ [0,1] vers 1 tant que le plot porte une flaque
# (`eau_surface > SEUIL_FLAQUE`), vers 0 sinon ; puis une HYSTÉRÈSE (entrée haute
# `MARAIS_ON`, sortie basse `MARAIS_OFF`) décide de l'état `est_marais` — sans quoi
# un plot au seuil clignoterait à chaque oscillation de la lame (marais/pas-marais).
#   cible          = 1.0 if eau_surface > SEUIL_FLAQUE else 0.0
#   marais_memory += (cible − marais_memory) · MARAIS_LERP        (LENT, semaines)
#   est_marais     = mémoire franchit MARAIS_ON (entrée) puis reste jusqu'à MARAIS_OFF
# EFFETS du marécage (émergents, jamais scriptés) :
#  - DÉCOMPO ANAÉROBIE : la vitesse de décomposition est rabotée
#    `× (1 − MARAIS_DECOMP_MALUS · marais_memory)` → la litière s'accumule sans se
#    minéraliser → l'épaisseur monte = TOURBE (aucun code neuf : l'épaisseur SUIT
#    déjà la MO via `tick_epaisseur`). Couple D40.
#  - ACIDIFICATION : la cible de dérive du pH est poussée vers `PH_TOURBE` ∝
#    `marais_memory` (terme additif borné, dans `tick_ph`) → tourbière acide.
# MARAIS_LERP est LENT (bascule en ~une saison de flaque continue) : un marais ne
# naît pas d'une averse. L'écart ON/OFF garantit qu'un assèchement passager ne le
# fait pas ressortir aussitôt (persistance). `marais_memory` NULLE au repos (aucune
# flaque durable) → tous les termes neutres (×1.0, +0.0) → golden NEUTRE hors banc.
# PLACEHOLDERS, calibrage F5 / banc `tourbiere`.
MARAIS_LERP         = 0.05   # intégration lente de la mémoire de marais (semaines → bascule ~saison)
MARAIS_ON           = 0.60   # seuil HAUT d'entrée en marais (hystérèse)
MARAIS_OFF          = 0.30   # seuil BAS de sortie de marais (hystérèse, < MARAIS_ON)
MARAIS_DECOMP_MALUS = 0.6    # part max de vitesse de décompo rabotée à marais plein (anaérobie)
PH_TOURBE           = 4.5    # pH cible d'une tourbière acide (marais plein pousse la cible du pH ici)
PH_MARAIS_LERP      = 1.0    # poids du terme marais dans la cible de dérive du pH (∝ marais_memory)

# --- Paillage — champ `paillage` par plot (sprint équilibre invasion ③, D69) ---
# Le LEVIER PERMACOLE central contre l'invasion d'adventices : un champ scalaire
# `paillage` ∈ [0,1] (profondeur/densité du mulch) posé par le geste `pailler`, qui
# 1) FREINE la germination férale (succession), 2) ÉPUISE la banque de graines
# enfouies (vieillissement accéléré, seedbank), 3) RÉDUIT l'évapotranspiration
# (hydrologie, rétention d'humidité), 4) SE DÉCOMPOSE en humus (`om_stable`). NUL
# partout au repos → tous les lecteurs neutres → golden INTACT (le smoke ne paille
# jamais). C'est un FLUX (philo #2) : le mulch change le MILIEU, la réponse
# biologique (moins de levée, sol plus frais) ÉMERGE ; jamais un bonus direct sur
# une plante. Déterministe, zéro RNG (philo #3). PLACEHOLDERS, calibrage F5 / bancs.
#  - PAILLAGE_DECAY : décroissance hebdomadaire du champ (le mulch se décompose /
#    s'incorpore). ~0.03/sem → un mulch plein s'efface en ~1 saison (demi-vie ~23 sem)
#    → il faut RE-pailler pour tenir l'effet (usure de la solution, philo #1).
#  - PAILLAGE_OM_W : part de la profondeur décomposée reversée à `om_stable` (le mulch
#    qui disparaît nourrit l'humus). PETIT (om_stable se décompose à 0.0006/sem : un
#    apport trop fort exploserait la mémoire du sol).
#  - PAILLAGE_GERM_SEUIL : profondeur de mulch au-delà de laquelle la levée férale est
#    TOTALEMENT étouffée (cutoff dur, patron COUVERTURE_ADVENTICE_SEUIL) ; en dessous,
#    la fenêtre de germination est atténuée graduellement par (1 − paillage).
#  - PAILLAGE_AGING_BOOST : accélérateur du vieillissement des graines sous mulch
#    (`SEED_VIABILITY_LOSS ** (1 + boost·paillage)`). paillage=0 → exposant 1 →
#    vieillissement inchangé ; mulch plein → banque enfouie épuisée plus vite.
PAILLAGE_DECAY        = 0.03    # décroissance hebdo du champ (mulch dure ~1 saison)
PAILLAGE_OM_W         = 0.10    # part de la profondeur décomposée reversée à om_stable
PAILLAGE_GERM_SEUIL   = 0.5     # profondeur au-delà de laquelle la germination férale est étouffée (cutoff dur)
PAILLAGE_AGING_BOOST  = 1.0     # accélération du vieillissement des graines enfouies à mulch plein
PAILLAGE_EVAP_FRAC    = 0.5     # part du chemin evap→1.0 (rétention) à mulch plein (barrière d'évaporation, patron COUVERTURE_EVAP_FRAC)
# Dose de mulch déposée par un geste `pailler` (échelle [0,1], CUMULATIVE, cap 1.0).
# Un geste = un bon paillage local ; ré-pailler par-dessus épaissit jusqu'au plafond.
PAILLAGE_DOSE         = 0.6

# --- Nature du mulch (sprint équilibre invasion ④, D9/§3.2) ----------------
# Le mulch n'est plus abstrait : il VIENT d'une source (broyage de bois → BRF,
# récolte de plantes à paille → paille/aiguilles) et sa NATURE lui donne des
# propriétés distinctes. `NATURES_MULCH` est un dict data-driven (une ligne par
# nature) de MULTIPLICATEURS/termes appliqués aux effets génériques du champ
# `paillage` (③), selon la nature DOMINANTE du plot (`eco.paillage_nature`).
# Chaque propriété se branche sur un couplage EXISTANT (aucune machinerie neuve),
# philo #2 (flux → contrainte, jamais un bonus direct plante) :
#  - `decay`     : ×PAILLAGE_DECAY (BRF/aiguilles = lents ; paille = moyen).
#  - `humidite_w`: ×PAILLAGE_EVAP_FRAC (rétention d'humidité — paille = forte).
#  - `allelo`    : frein GRADUÉ SUPPLÉMENTAIRE à la germination férale
#    (`niche *= 1 − allelo·paillage`), aiguilles seulement (allélopathie conifère).
#  - `ph_shift`  : poussée pH/sem tant que le mulch est là (aiguilles acidifient) —
#    écrit la CIBLE de pH comme un amendement (patron AMEND_PUSH), réversible.
#  - `vers_bois` : part de la décompo reversée en litière `bois` (au lieu d'`om_stable`)
#    → BRF C-riche. Route DEUX couplages existants d'un coup : la FAIM D'AZOTE
#    (`bois` ∈ FAIM_N_TISSUS → immobilise N en surface) ET le MYCÉLIUM (`bois_fresh_at`
#    nourrit les saprophytes) — l'interconnexion « ferme la boucle » sans code neuf.
#  - `fongique`  : marqueur (hook mycélium) — informatif, lu par la vue/le pont (⑧) ;
#    l'effet fongique RÉEL passe déjà par `vers_bois` (litière bois → substrat).
#  - `abri_w`    : qualité d'ABRI pour la faune ombrophile (sprint équilibre invasion
#    ⑥, D11) — un mulch VOLUMINEUX offre un meilleur refuge. Le BRF (copeaux, cavités)
#    abrite mieux que la paille (couche plane). Lu par la couche `fields/population`
#    via `eco.nature_at` (pas d'import inverse) pour gonfler l'habitat des guildes de
#    sol. Repos (nature "") → NATURE_NEUTRE.abri_w = 0 → habitat inchangé → golden INTACT.
# Valeurs PLACEHOLDER, calibrage F5 / bancs. NUL au repos (nature "" → tous les
# multiplicateurs valent 1.0, aucun terme extra) → golden INTACT.
NATURES_MULCH = {
    #             decay  humidite_w  allelo  ph_shift  vers_bois  fongique  abri_w
    "paille":    {"decay": 1.0, "humidite_w": 1.2, "allelo": 0.0,  "ph_shift":  0.0,  "vers_bois": 0.0,  "fongique": False, "abri_w": 0.7},
    "brf":       {"decay": 0.5, "humidite_w": 0.9, "allelo": 0.0,  "ph_shift":  0.0,  "vers_bois": 1.0,  "fongique": True,  "abri_w": 1.0},
    "aiguilles": {"decay": 0.5, "humidite_w": 0.9, "allelo": 0.3,  "ph_shift": -0.10, "vers_bois": 0.0,  "fongique": False, "abri_w": 0.6},
    # Feuilles GLANÉES (acquisition des moyens d'agir ③, canal 1 `glaner`) : la
    # litière de surface TENDRE (feuille/fleur/herbace/fruit) ramassée à même le sol
    # → le mulch BASE, celui que le débutant se procure sans outil ni culture (lève
    # l'impasse `RAVITAILLEMENT_MANQUANT`). Profil calqué sur `paille` (mulch tendre,
    # RAPIDE : `decay` 1.0), MAIS DISTINCT du bois : `vers_bois` = 0 (pas de faim
    # d'azote, pas d'habitat fongique — c'est de la feuille, pas du BRF), rétention
    # d'humidité un cran SOUS la paille (couche plus mince, se tasse vite → 1.0 vs
    # 1.2), abri MODESTE (feuillage plat). Aucune allélopathie/décalage pH.
    # PLACEHOLDER, calibrage F5 / bancs.
    "feuilles":  {"decay": 1.0, "humidite_w": 1.0, "allelo": 0.0,  "ph_shift":  0.0,  "vers_bois": 0.0,  "fongique": False, "abri_w": 0.5},
}
# Nature NEUTRE (plot non mulché) : tous les multiplicateurs à l'identité, aucun
# terme extra → lecteurs strictement inchangés (garde-fou golden au repos).
NATURE_NEUTRE = {"decay": 1.0, "humidite_w": 1.0, "allelo": 0.0,
                 "ph_shift": 0.0, "vers_bois": 0.0, "fongique": False, "abri_w": 0.0}

# Rendement de matière par SOURCE (sprint équilibre invasion ④, §3.1). Convertit une
# masse physique (bois broyé, biomasse récoltée) en unités de STOCK de mulch (mêmes
# unités que PAILLAGE_DOSE : un geste `pailler` consomme PAILLAGE_DOSE du stock).
#  - BROYAGE_RENDEMENT : unités de BRF par unité de `bois_restant` broyée.
#  - RECOLTE_MULCH_RENDEMENT : unités de mulch par unité de biomasse récoltée d'une
#    plante à paille (blé/chanvre → paille, sapin → aiguilles — attribut d'espèce ⑤).
BROYAGE_RENDEMENT        = 2.0
RECOLTE_MULCH_RENDEMENT  = 1.5

# --- Allélopathie racinaire (sprint ALLÉLOPATHIE ①, D4) --------------------
# Champ de sol UNIQUE `allelopathie` = concentration agrégée d'allélochimiques
# (exsudats/juglone/lactones…) par plot. ALIMENTÉ par les émetteurs via
# `inject_field variable="allelopathie" cible="local"` (déposé sur l'empreinte
# RACINAIRE, comme l'azote de l'ortie) — au tronçon ① aucune espèce n'émet
# encore (`allelopathie_emission=0` partout, tronçon ⑤). DÉCROÎT chaque tick,
# LABILE : perte spontanée + DÉTOX par le sol vivant (microbiome). RÉGIME
# labile pur ici (l'accumulation autotoxique = tronçon ④). PERSONNE ne le LIT
# ce tronçon (germination ②, croissance ③) → golden NEUTRE (champ nul au repos,
# aucun émetteur). C'est un FLUX (philo #2) : la molécule change le MILIEU, la
# réponse biologique (levée bridée, voisine qui plie) ÉMERGERA aux ②/③, jamais
# un malus direct sur la plante. Déterministe, zéro RNG (philo #3).
# PLACEHOLDERS — calibrage F5 / bancs.
#  - ALLELO_DECAY_BASE   : perte spontanée hebdo (hydrolyse/lessivage minimal).
#    ~0.08/sem → une charge unique s'estompe en ~1 saison sur sol pauvre.
#  - ALLELO_DECAY_MICROBE: détox SUPPLÉMENTAIRE ∝ microbiome (échelle [0,3]) — un
#    sol vivant dégrade plus vite les allélochimiques (interconnexion). À
#    microbiome plein (3), la détox ajoute ~0.15/sem au-dessus de la base.
#  - ALLELO_FLOOR        : plancher de snap-à-0 (évite une traîne asymptotique
#    infinitésimale qui pollue le déterminisme des lecteurs futurs).
ALLELO_MAX          = 3.0     # concentration max/plot (borne GridField, ≡ échelle n/p/k)
ALLELO_DECAY_BASE   = 0.08    # perte spontanée hebdo (hydrolyse/lessivage)
ALLELO_DECAY_MICROBE = 0.05   # détox hebdo ∝ microbiome normalisé [0,1] (sol vivant)
ALLELO_FLOOR        = 1e-4    # sous ce seuil, on snap à 0 (fin de traîne)
# Constante de demi-saturation de la RAMPE DOUCE d'inhibition de germination
# (sprint ALLÉLOPATHIE ②, D6). L'escompte de niche d'un candidat sensible est
# `f_allelo = 1 − SENS · rampe(allelopathie[plot])` avec `rampe(x) = x/(x+K)`
# (Monod : continue, saturante, PAS de seuil dur — cohérent avec `niche_index`
# continu). K = concentration à laquelle la rampe vaut 0.5 : plus K est GRAND,
# plus il faut d'allélochimiques pour brider une levée. K = 1.0 (≈ 1/3 de
# ALLELO_MAX) → une charge modérée mord déjà, une charge forte (proche de 3)
# referme presque la niche des espèces pleinement sensibles (rampe ≈ 0.75).
# INVARIANT GOLDEN : `allelopathie = 0` ⇒ `rampe(0) = 0` ⇒ `f_allelo = 1` ⇒
# germination STRICTEMENT inchangée (K>0 garantit le zéro exact, pas de /0).
# PLACEHOLDER — calibrage F5 / bancs.
ALLELO_GERM_K       = 1.0     # demi-saturation de la rampe Monod d'inhibition de levée
# Escompte MAXIMAL de croissance/vigueur sous allélopathie racinaire (sprint
# ALLÉLOPATHIE ③, D1/D6). Une plante DÉJÀ levée dont les racines explorent des
# plots chargés voit son GAIN de croissance escompté (jamais sa santé décrémentée
# directement — philo #2) :
#   f_croissance = 1 − ALLELO_GROWTH_ESC_MAX · SENS · rampe(allelo_racinaire)
# avec la MÊME rampe Monod `x/(x+ALLELO_GERM_K)` qu'à la germination (②, cohérence)
# et `allelo_racinaire` = concentration MOYENNE de `allelopathie` sur l'empreinte
# racinaire (même empreinte que l'uptake — RÉUTILISÉE, pas recalculée). Borné < 1
# pour ne JAMAIS annuler la croissance d'un coup (la voisine plie, elle ne meurt pas
# net : dépérissement ÉMERGENT via ombre/ravageurs/sécheresse). À 0.6, une plante
# pleinement sensible (SENS=1) sur sol saturé (rampe→0.75) retombe à ~0.55 de gain.
# INVARIANT GOLDEN : `allelo = 0` ⇒ `rampe(0) = 0` ⇒ `f_croissance = 1` ⇒ croissance
# STRICTEMENT inchangée. PLACEHOLDER — calibrage F5 / bancs.
ALLELO_GROWTH_ESC_MAX = 0.6   # escompte max du GAIN de croissance (borné < 1)

# --- Autotoxicité / fatigue du sol (sprint ALLÉLOPATHIE ④, D3) --------------
# La pépite pédagogique permaculture : une MONOCULTURE répétée s'empoisonne. Un
# accumulateur `autotox` par plot MONTE quand la MÊME espèce émettrice (celle qui
# a `allelopathie_emission > 0`) ré-occupe le plot saison après saison sans
# rotation — l'allélochimique s'accumule faute de diversité microbienne pour le
# dégrader. `autotox` s'AJOUTE à l'allélopathie EFFECTIVE vue par cette SEULE
# espèce (spécificité de la fatigue : la rotation ou le sol nu font retomber
# `autotox` → le sol « se repose »). `soil_memory` ne trace PAS l'espèce (mémoire
# de fertilité) → un TRACEUR d'identité séparé (`autotox_espece`, clé espèce par
# plot) porte la mémoire de la culture récurrente. Résorption ACCÉLÉRÉE par le
# microbiome (sol vivant détoxifie, cohérent §A.3 / la décroissance labile ①).
# INVARIANT GOLDEN : tant qu'AUCUNE espèce n'émet (`allelopathie_emission=0`
# partout avant le ⑤), le traceur ne s'arme jamais → `autotox=0` partout → la
# lecture EFFECTIVE `allelo_effectif == allelopathie` → germination ET croissance
# STRICTEMENT identiques au pré-④ (toute dérive serait attribuable au SEUL
# traceur, cf. kickoff §Golden). Cadence SAISONNIÈRE (montée par saison de
# ré-occupation) → le ressort est lent, lisible sur plusieurs années.
# PLACEHOLDERS — calibrage F5 / bancs.
#  - AUTOTOX_MONTEE  : incrément par SAISON de ré-occupation par la même espèce.
#  - AUTOTOX_REPOS   : redescente fractionnelle spontanée quand le plot est libéré
#    ou occupé par une AUTRE espèce (rotation = échappatoire).
#  - AUTOTOX_MICROBE : redescente SUPPLÉMENTAIRE ∝ microbiome (sol vivant détoxifie).
AUTOTOX_MAX     = 3.0    # borne du GridField autotox (≡ échelle allelopathie / n/p/k)
AUTOTOX_MONTEE  = 0.25   # accumulation par saison de monoculture de l'espèce émettrice
AUTOTOX_REPOS   = 0.15   # redescente fractionnelle spontanée à la rotation / sol nu
AUTOTOX_MICROBE = 0.10   # redescente fractionnelle supplémentaire ∝ microbiome normalisé [0,1]

# Signature sol par famille (laissée après chaque saison)
SOIL_SIGNATURE = {
    "Fabaceae":   {"microbiome": +0.15, "fertilite": +0.10},
    "Solanaceae": {"microbiome": -0.05},
    "Asteraceae": {"microbiome": +0.05, "fertilite": +0.05},
    "Lamiaceae":  {"microbiome": +0.08},
    # Grimpantes (sprint Grimpantes ⑤, placeholders) : litière persistante du
    # lierre qui abrite la microfaune ; apport modéré du jasmin.
    "Araliaceae": {"microbiome": +0.06},
    "Oleaceae":   {"microbiome": +0.04},
}
