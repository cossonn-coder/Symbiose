"""
SYMBIOSE — fields/ecofields/container.py
Conteneur EcoFields : tous les champs écologiques continus d'une tuile
(hydrologie, OM tri-compartiment, microbiome, soil memory, lumière, perturbation,
banque de graines, populations).

Le cœur du moteur écologique. Ce module porte l'ÉTAT (déclarations de champs +
`__post_init__`) et les accès transverses (`get_field`, `fertilite_index`,
`apply_weather`, `summary`/`__repr__`) ; le COMPORTEMENT (ticks) est éclaté en
mixins par responsabilité (scission refactor 2026-06-30, container devenu trop
dense) :
  - `matiere_organique.py` — litière, décomposition, structures, nécromasse
  - `hydrologie.py`        — cycle de l'eau (tick_hydrology)
  - `uptake.py`            — prélèvement racinaire (plant_uptake)
  - `vie_macro.py`         — populations, ponts de cycle de vie, pollinisateurs
  - `sol.py`               — banque de graines, mémoire du sol, vitalité, maladie
  - `ticks.py`             — ticks délégués (thermique/pH/structure/mycélium/rosée/
                             neige/transport) + diffusion/lumière/abri/perturbation
`EcoFields` ASSEMBLE ces mixins par héritage → l'API publique et le comportement
sont strictement inchangés (bit-identique à l'ancien `container.py` monolithe).
Les constantes de calibration vivent dans `constants.py`, les types de
litière/structures dans `litiere.py`.
"""

from __future__ import annotations
from dataclasses import dataclass, field

from fields.grids import GridField, DisturbanceField
from fields.noise import _hash_noise, stable_str_hash
from fields.light import LightField
from fields.seedbank import SeedBank, FOUNDER_POOL_DENSITY
from plants.genetics import GENE_INIT_SIGMA
from fields.population import (PopulationField, build_population_specs,
                               build_pollinator_specs, build_lifecycle_bridges)
from fields.lifecycle import larval_field_names
from .constants import *          # constantes de calibration écologique
from .litiere import Parcelle     # parcelle de litière (couche fraîche, __post_init__)

from .inoculum import InoculumField   # mémoire d'inoculum du sol (sprint mémoire d'inoculum ①)

from .matiere_organique import MatiereOrganiqueMixin
from .hydrologie import HydrologieMixin
from .ruissellement import RuissellementMixin
from .marais import MaraisMixin
from .uptake import UptakeMixin
from .vie_macro import VieMacroMixin
from .sol import SolMixin
from .ticks import TicksMixin
from .couverture import CouvertureMixin
from .paillage import PaillageMixin
from .couvertures_posees import CouverturePoseeMixin   # voile/cloche/ombrière posées (effondrement météo ③)
from .bordure import BordureMixin   # conditions aux limites de la ceinture (périphérie ③)


# Noms acceptés par `EcoFields.get_field` (chaque nom = un attribut GridField).
_CHAMPS_NOMMES = frozenset((
    "humidite", "microbiome", "lumiere", "soil_memory", "disturbance", "om_active",
    "om_stable", "soil_memory_fast", "soil_memory_deep", "temperature",
    "temperature_sol", "ph", "n", "p", "k", "structure_sol", "mycelium",
    "epaisseur_sol", "altitude", "eau_surface", "marais_memory", "couverture_sol",
    "paillage", "couvert_pose", "ombre_pose", "allelopathie", "autotox",
))


@dataclass
class EcoFields(MatiereOrganiqueMixin, HydrologieMixin, RuissellementMixin,
                MaraisMixin, UptakeMixin, VieMacroMixin, SolMixin, TicksMixin,
                CouvertureMixin, PaillageMixin, CouverturePoseeMixin, BordureMixin):
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
    # Givre déposé par la gelée blanche (sprint météo→champs ②, §3.4) — carte PAR
    # PLOT ∈ [0,1] (≠ scalaire `snow` : le givre suit le thermomètre nocturne LOCAL,
    # un coin nu/clair givre quand un coin paillé reste au-dessus de 0). Accumule la
    # condensation gelée des nuits ≤ 0 °C (`rosee.tick_rosee`) et la RESTITUE à
    # `humidite` quand T repasse > 0 (FONTE DIFFÉRÉE, couplage hydrique sûr). À 0 au
    # repos (golden NEUTRE tant qu'aucune nuit givrante ; le smoke en a en hiver → ②
    # re-fige MAÎTRISÉ). Hors `summary()` (état transient, ne change pas le digest).
    givre:            GridField = field(default=None)
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
    # Structure / compaction du sol (sprint physico-chimie ⑧, dette D30) ∈ [0,1] :
    # 1 = grumeleux/aéré, 0 = compacté/battant. INITIALISÉ PAR HÉRITAGE du `soil_type`
    # (STRUCTURE_INIT_PAR_SOL) puis dérive LENTE (`tick_structure`, helper pur) sous
    # bioturbation (+vers), racines pivots (+) et battance de pluie sur sol nu (−). Trois
    # LECTEURS : l'infiltration de la pluie de fond (`tick_hydrology`, le reste ruisselle),
    # l'aggravation de l'asphyxie et la pénétration racinaire (`plant_uptake`).
    structure_sol:    GridField = field(default=None)
    # Réseau fongique (sprint mycélium & interconnexions ①) ∈ [0,1] : 1 = sol
    # densément colonisé, 0 = sans réseau. Acteur NEUF (CONCEPTION_MYCELIUM §1) à
    # côté de `microbiome` (il est SESSILE, lié au substrat → PAS une 5ᵉ guilde de
    # PopulationField). Croît sur le bois humide non travaillé, décline au sec /
    # substrat épuisé (`tick_mycelium`, helper pur). NUL partout au repos. Au tronçon
    # ① POSÉ + dynamique propre mais lu par PERSONNE → golden NEUTRE (effets §2 —
    # saprophyte/mycorhize/faune — branchés aux tronçons ②③④). Exposé AUTO à la vue
    # F6/au pont par le registre `get_field` (palette overlay côté Godot = ⑥).
    mycelium:         GridField = field(default=None)
    # Perte de drainage du DERNIER tick d'hydrologie (sprint météo→champs ③, §4) :
    # `tick_hydrology` écrit ici l'eau qui s'est écoulée au fond par plot (= la perte
    # qu'il retournait déjà, jusqu'ici jetée par la tuile). `tick_decomposition` la LIT
    # pour AMPLIFIER le lessivage NPK ∝ l'eau qui draine (la pluie qui s'écoule emporte
    # les ions mobiles, N≫K>P). État TRANSIENT par tick, à 0 au repos → golden NEUTRE
    # tant que `LESSIVAGE_PLUIE_K=0` ou aucune eau ne draine. Hors `summary()` (transient).
    drainage_last:    GridField = field(default=None)
    # Eau liquide de rosée déposée au DERNIER tick nocturne (sprint météo→champs ⑤, §6) :
    # `tick_rosee` y écrit la condensation LIQUIDE par plot (régime > 0 °C — pas le givre,
    # qui va dans `eco.givre`). Carte transiente lue par les INTERCONNEXIONS vivantes du
    # matin : (A) habitat des détritivores de surface (limace/cloporte abreuvés) et (B)
    # captation foliaire (le feuillage hydraté allège le stress hydrique de la plante).
    # NULLE au repos / nuit douce-couverte → golden NEUTRE pour ces termes ; la rosée du
    # smoke en pose → golden léger ANNONCÉ. Hors `summary()` (transient, comme drainage_last).
    rosee_last:       GridField = field(default=None)
    # Aspersion foliaire du DERNIER geste (sprint HUMECTATION FOLIAIRE ③, §2.5) —
    # carte TRANSIENTE par plot (patron `rosee_last`) posée par le geste `arroser`
    # en mode FEUILLAGE (`aspersion_last.set(r, c, DOSE_ARROSAGE)`, event-driven, hors
    # tick). Lue par la SEULE humectation foliaire (`_update_physiology`, terme
    # ASPERSION_WET_GAIN) puis REMISE À PLAT chaque tick par `tick_semaine` (APRÈS
    # `_update_physiology` — cf. le commentaire au point de reset : le geste s'applique
    # ENTRE deux ticks, un reset AVANT la lecture effacerait l'apport). NULLE au repos
    # (aucun `arroser(feuillage=True)`) → terme nul → construction directe / smoke
    # bit-identiques, golden INTACT. Hors `summary()` (transiente comme `rosee_last`).
    aspersion_last:   GridField = field(default=None)
    # Champ de VENT spatialisé (sprint VENT & ÉVAPOTRANSPIRATION ③, §2.4/§4) — force
    # LOCALE du vent par plot ∈ [0,1+] : la masse d'air uniforme (`wind_at` ①) MODULÉE
    # par la géométrie d'abri (sillage sous le vent des obstacles, venturi des goulets).
    # Recalculé chaque tick par `tick_abri` (helper PUR `fields.abri`) AVEC CACHE sur
    # (obstacles, direction) — coût ≈ 0 en régime permanent (§7B). Lu par l'évaporation
    # (③ remplace la masse d'air uniforme du ②) et le wind chill (`t_min_nuit_at`, §5.5).
    # À 0 au repos (aucun vent/obstacle) → golden NEUTRE tant que `tick_abri` n'écrit pas.
    vent:             GridField = field(default=None)
    # Multiplicateur de RAFALE locale (sprint PÉRIPHÉRIE ②, D73, conception §3.2) —
    # ≥ 1 par plot : la TURBULENCE DE DÉCOLLEMENT derrière une lisière PEU POREUSE.
    # Le vent moyen (`vent`) et la rafale ne réagissent pas pareil à la porosité :
    # réduction linéaire en densité, turbulence QUADRATIQUE → une lisière trop dense
    # abrite du vent constant mais fait tomber des rafales (leçon émergente #6).
    # LAZY et **None au repos** (aucun obstacle poreux → aucune allocation) ; écrit
    # par `tick_abri` quand la ceinture porte un secteur boisé/rocheux. Son SEUL
    # lecteur est `_wind_damage` (casse mécanique), qui lit 1.0 quand le champ est
    # None → golden INTACT tant qu'aucune ceinture n'est posée. Hors `summary()`
    # (grandeur géométrique transiente, comme `vent`).
    turbulence:       GridField = field(default=None)
    # Champ de LISIÈRE (sprint PÉRIPHÉRIE ③, D73, conception §4.2) — ∈ [0,1] par plot :
    # l'intensité d'effet de lisière apportée par la ceinture, gradient décroissant
    # depuis chaque bord et pondéré par le TYPE de secteur (forêt/friche fort, berge
    # moyen, prairie/falaise faible). C'est un champ DU MILIEU, pas un bonus : chaque
    # guilde y répond via son poids déclaré `TrophicSpec.lisiere_w` (défaut 0.0 — le
    # carabe et le hérisson y répondent, le puceron non), ce qui interdit le « +0.2
    # d'habitat si forêt » que la philo #2 proscrit. Écrit par `maj_lisiere`, MÉMOÏSÉ
    # sur les types de secteurs (quasi statiques → calculé une fois). LAZY et **None
    # au repos** : son unique lecteur (`PopulationField.tick`) saute alors le terme →
    # capacité de charge bit-identique → golden INTACT sans ceinture. Hors `summary()`
    # (grandeur géométrique du milieu, comme `vent`/`turbulence`).
    lisiere:          GridField = field(default=None)
    # Épaisseur de sol visible (D57, sprint épaisseur de sol ①a) — cm de sol
    # foisonnant au-dessus de la roche-mère, PAR PLOT. Champ STOCKÉ (persisté) qui
    # RELAXE vers une cible bulk-density dérivée des `om_*` (litière fraîche
    # foisonnante + active + humus stable), avec inertie asymétrique (monte vite,
    # descend lent) et érosion (`tick_epaisseur`). C'est l'expression PHYSIQUE du
    # cycle de la MO : la matière qui tombe épaissit le sol, le tassement/la décompo
    # la rognent, l'humus persiste et l'exhausse sur les ans. INITIALISÉ AU REPOS
    # (`init_eco` : cible calculée sur l'`om_stable` de fond hérité D56) pour partir
    # déjà au niveau d'équilibre, sans transitoire de montée au tick 0. Au tronçon ①a
    # POSÉ + tické mais lu par PERSONNE → golden NEUTRE ; les effets écolo (rétention
    # d'eau + accès NPK) arrivent au ①b, le relief extrudé au ② (rendu). Exposé AUTO
    # au registre `get_field` (overlay debug F6 / pont ②).
    epaisseur_sol:    GridField = field(default=None)
    # Micro-relief topographique (sprint hydrologie & marécages ①) — cm d'altitude
    # du terrain PAR PLOT, au-dessus d'une référence arbitraire. Socle géométrique
    # FIXE (aucun tick ne l'écrit) qui portera l'ÉCOULEMENT de l'eau (②, du haut vers
    # le bas). À NE PAS confondre avec `epaisseur_sol` (humus foisonnant ≠ topographie).
    # Créé PLAT (0) ici — construction DIRECTE `EcoFields()`, ex. mini-sol de conteneur,
    # qui n'a pas de topographie et ne ruisselle pas → reste 0, inoffensif. Le chemin
    # monde `init_eco` le POSE hétérogène sur un canal de hash DÉCORRÉLÉ de l'humus
    # (relief et fertilité ne coïncident pas, philo #7). Au tronçon ① lu par PERSONNE
    # (aucun tick, aucun effet) → golden NEUTRE. Exposé AUTO au registre `get_field`
    # (overlay debug F6 / pont ①).
    altitude:         GridField = field(default=None)
    # Lame d'eau de SURFACE (sprint hydrologie & marécages ②) — cm d'eau STAGNANTE
    # au-dessus du plot, DISTINCTE de `humidite` (eau des pores). Reçoit le surplus
    # de saturation capturé par `tick_hydrology` (au lieu de l'écrêter), RUISSELLE
    # vers les plots plus bas (`tick_ruissellement`, double buffer, lit `altitude`+
    # `epaisseur_sol`), s'infiltre si le sol peut boire, s'évapore. `eau_surface >
    # SEUIL_FLAQUE` = FLAQUE (perçue à la vue ⑧, alimentera `marais_memory` au ③).
    # NULLE au repos (aucune saturation dépassée) → golden NEUTRE tant qu'aucun plot
    # ne déborde ; les plots gorgés du smoke en produisent → re-figeage LARGE ANNONCÉ
    # (l'eau circule enfin, le bilan hydrique par plot change). Exposée AUTO au
    # registre `get_field` (overlay debug F6) + au snapshot (bloc `eau_surface` ②).
    eau_surface:      GridField = field(default=None)
    # Mémoire de MARÉCAGE (sprint hydrologie & marécages ③) — état PERSISTANT ∈ [0,1]
    # par plot, INTÉGRÉ lentement (`tick_marais`) vers 1 tant qu'une flaque dure
    # (`eau_surface > SEUIL_FLAQUE`), vers 0 sinon. Une flaque qui DURE fait « noircir »
    # le plot en marais : décompo anaérobie ralentie (litière qui s'accumule = tourbe
    # émergente, lue par `tick_decomposition`) + pH poussé vers l'acide (`tick_ph`) +
    # niche humide/acide ouverte aux espèces marécageuses (⑤⑥). N'est PAS un type de
    # sol scripté : état ÉMU (mémoire + seuil, philo #2/#6). NULLE au repos (aucune
    # flaque durable) → décompo/pH neutres → construction directe (mini-sol de conteneur
    # qui ne ruisselle pas) bit-identique, golden NEUTRE hors banc. Exposée AUTO au
    # registre `get_field` (overlay debug F6 / pont) + au snapshot (bloc `marais` ③).
    marais_memory:    GridField = field(default=None)
    # État binaire de marais par plot (grille de bool) — dérivé de `marais_memory` par
    # HYSTÉRÈSE (entrée MARAIS_ON, sortie MARAIS_OFF ; anti-clignotement au seuil),
    # entretenu par `tick_marais`, lu par `est_marais`. Sépare l'ÉTAT (niche, vue) du
    # DOSAGE des flux (décompo/pH lisent la mémoire continue). False partout au repos.
    marais_etat:      list = field(default=None)
    # Couverture du sol (sprint LUXURIANCE ①, D65 §2.1) — fraction ∈ [0,1] du plot
    # couverte par le feuillage des strates BASSES (sol+basse), RECALCULÉE chaque tick
    # par SCATTER (`tick_couverture`, mixin `CouvertureMixin`). NULLE au repos (aucune
    # plante basse) → lecteurs (évaporation, germination) neutres → construction directe
    # (mini-sol de conteneur qui ne ticke pas la couverture) bit-identique. Bornée
    # [0,1] par le GridField. Exposée AUTO au registre `get_field` (overlay debug F6).
    couverture_sol:   GridField = field(default=None)
    # Paillage du sol (sprint équilibre invasion ③, D69) — profondeur/densité du mulch
    # ∈ [0,1] par plot, POSÉE par le geste `pailler` (event-driven), DÉCROISSANTE au
    # tick (`tick_paillage` → reverse à om_stable). Lue par la germination férale
    # (succession, étouffe la levée), le vieillissement des graines (seedbank, épuise
    # la banque) et l'évaporation (hydrologie, retient l'humidité). NULLE au repos
    # (aucun geste `pailler`) → tous les lecteurs neutres → construction directe
    # (mini-sol de conteneur qui ne paille pas) bit-identique, golden INTACT. Exposée
    # AUTO au registre `get_field` (overlay debug F6 / pont).
    paillage:         GridField = field(default=None)
    # Nature du mulch par plot (sprint équilibre invasion ④, D9) — grille de chaînes
    # ("" = plot non paillé, sinon "paille"/"brf"/"aiguilles"). PAS un GridField (donnée
    # catégorielle, pas scalaire ; patron `litiere`). Fixée par `poser_mulch` (geste
    # `pailler`), réinitialisée à "" quand le mulch se décompose (`tick_paillage`). Lue
    # via `nature_at` par la germination/l'évaporation/la décompo → propriétés distinctes
    # par nature (`NATURES_MULCH`). "" partout au repos → NATURE_NEUTRE → golden INTACT.
    paillage_nature:  list = field(default=None)
    # Couvertures POSÉES par le joueur (sprint effondrement météo ③) — écran physique
    # `couvert_pose` (voile/cloche) et occultation `ombre_pose` (ombrière), ∈ [0,1] par
    # plot. Alloués PARESSEUSEMENT (None au repos → zéro RAM) par les gestes
    # `poser_voile`/`poser_cloche`/`poser_ombriere` (event-driven, hors tick). Le
    # `couvert_pose` s'ajoute au couvert de gel (`t_min_nuit_at`) et protège de la grêle
    # (`_mediated_damage`) ; l'`ombre_pose` atténue la lumière-sol (`appliquer_ombrieres`)
    # → sol plus frais → moins d'évaporation (canicule/sécheresse). PERSISTANTS (structure
    # durable, aucun tick propre). NULS au repos (le smoke ne pose rien) → lecteurs neutres
    # → golden NEUTRE. Exposés AUTO au registre `get_field` (overlay debug F6 / pont ④).
    couvert_pose:     GridField = field(default=None)
    ombre_pose:       GridField = field(default=None)
    # Allélopathie racinaire (sprint ALLÉLOPATHIE ①, D4) — concentration agrégée
    # d'allélochimiques par plot, bornée [0, ALLELO_MAX]. Champ de sol UNIQUE (D4 :
    # pas un dict par molécule). ALIMENTÉ par les émetteurs via `inject_field
    # variable="allelopathie" cible="local"` (route générique `get_field`, dépôt sur
    # l'empreinte RACINAIRE — même chemin que l'azote de l'ortie) ; DÉCLINÉ chaque
    # tick (`tick_allelopathie`, helper pur : perte spontanée + détox ∝ microbiome).
    # NUL partout au repos (aucune espèce n'a `allelopathie_emission > 0` avant le ⑤)
    # → lu par PERSONNE ce tronçon (germination ②, croissance ③ branchées plus tard)
    # → construction directe (mini-sol de conteneur) bit-identique, golden NEUTRE.
    # Exposé AUTO au registre `get_field` (overlay debug F6 / pont ⑥).
    allelopathie:     GridField = field(default=None)
    # Autotoxicité / fatigue du sol (sprint ALLÉLOPATHIE ④, D3) — accumulateur
    # d'allélochimiques de la MÊME espèce émettrice qui ré-occupe un plot sans
    # rotation, borné [0, AUTOTOX_MAX]. Monte par SAISON de monoculture, redescend
    # à la rotation / sol nu (détox ∝ microbiome) : la monoculture s'empoisonne, la
    # diversité soigne (pépite pédagogique permaculture). LU par la SEULE espèce
    # traceée via `allelo_effectif` (allelopathie + autotox si la plante EST
    # l'émetteur récurrent du plot) → spécificité de la fatigue. `soil_memory` ne
    # trace PAS l'espèce → le traceur d'identité `autotox_espece` (ci-dessous) porte
    # la mémoire de la culture récurrente. NUL au repos + aucun émetteur avant le ⑤
    # → `allelo_effectif == allelopathie` → germination ② / croissance ③ inchangées
    # → golden NEUTRE. Exposé AUTO au registre `get_field` (overlay debug F6 / pont).
    autotox:          GridField = field(default=None)
    # Traceur d'identité d'espèce ÉMETTRICE récurrente par plot (sprint ALLÉLOPATHIE
    # ④) — grille de `plant_class` (le type, clé stable/hashable) ou None. Léger : une
    # référence par plot (garde-fou RAM du kickoff : PAS de structure lourde). Fixé en
    # fin de saison par `tick_autotoxicite` : si l'occupant émetteur du plot est le
    # MÊME qu'à la saison précédente, `autotox` monte ; sinon il redescend. None
    # partout au repos (aucun émetteur avant le ⑤) → aucune montée → golden NEUTRE.
    # Hors `summary()` (état d'identité, ne change pas le digest écologique).
    autotox_espece:   list = field(default=None)
    # Mémoire d'inoculum du sol (sprint mémoire d'inoculum ①) — champ SPARSE indexé
    # par FAMILLE botanique (dict, PAS un GridField) : la charge pathogène PERSISTANTE
    # qui SURVIT à la mort de la plante, là où `infection_memory` (par plante) s'éteint
    # avec l'hôte. Alimenté par deux canaux CONSÉQUENCE (dépôt continu de la plante
    # infectée vivante + pulse de résidu à la mort, cf. perturbations.py) et rabattu par
    # `tick_decay` (décroissance passive − microbiome suppressif). Au tronçon ① ALIMENTÉ
    # et DÉCROISSANT mais lu par PERSONNE dans la math du tick (DORMANT) → golden INTACT ;
    # le couplage à `disease_probability(family)` est le ②, la niche molène le ③. Hors
    # `summary()` (structure sparse, pas une grandeur du digest écologique).
    inoculum:         InoculumField = field(default=None)

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
        # Structure héritée du `soil_type` (⑧) : init uniforme, bornée [0,1]. La dérive
        # per-plot (`tick_structure`) creuse ensuite des écarts via vers/pivots/battance.
        if self.structure_sol is None:
            self.structure_sol = GridField(
                self.rows, self.cols,
                initial=STRUCTURE_INIT_PAR_SOL.get(self.soil_type,
                                                   STRUCTURE_INIT_PAR_SOL["terre"]),
                max_val=1.0, min_val=0.0)
        # Réseau fongique (①) — NUL partout au départ (initial=0.0 par défaut),
        # borné [0,1]. Le repos NEUTRE garantit l'invariant golden (§1.3).
        if self.mycelium is None:
            self.mycelium = GridField(self.rows, self.cols, max_val=1.0)
        # Givre (②) — NUL partout au départ, borné [0,1]. Repos NEUTRE → golden
        # inchangé tant qu'aucune nuit givrante (smoke : hiver en pose, ② re-fige).
        if self.givre is None:
            self.givre = GridField(self.rows, self.cols, max_val=1.0)
        # Perte de drainage du dernier tick (③) — NULLE au repos, écrite chaque tick
        # par `tick_hydrology`, lue par `tick_decomposition`. Pas de max_val borné
        # (perte d'humidité brute, petite pour un sol terre).
        if self.drainage_last is None:
            self.drainage_last = GridField(self.rows, self.cols)
        # Rosée liquide du dernier tick (⑤) — NULLE au repos, écrite par `tick_rosee`,
        # lue par les interconnexions vivantes du matin (faune abreuvée + captation foliaire).
        if self.rosee_last is None:
            self.rosee_last = GridField(self.rows, self.cols)
        # Aspersion foliaire du dernier geste (③) — NULLE au repos, posée par
        # `arroser(feuillage=True)`, lue par l'humectation puis remise à plat par le tick.
        if self.aspersion_last is None:
            self.aspersion_last = GridField(self.rows, self.cols)
        # Vent spatialisé (③) — NUL au repos (aucun tick d'abri encore appelé), écrit
        # par `tick_abri`. `_abri_cache` mémorise (signature, facteur, turbulence) pour
        # ne recalculer la géométrie que sur Δdirection/obstacle (§7B levier 2). None =
        # froid. `turbulence` reste None (② : allouée à la 1ʳᵉ lisière rencontrée).
        if self.vent is None:
            self.vent = GridField(self.rows, self.cols)
        # Épaisseur de sol (①a) — bornée [0, EPAISSEUR_MAX]. Créée à 0 ici (repos
        # NEUTRE d'une construction DIRECTE `EcoFields()`, ex. mini-sol de conteneur
        # qui ne ticke PAS l'épaisseur → reste 0, inoffensif). Le chemin monde
        # `init_eco` la POSE au niveau de REPOS (cible sur l'om_stable de fond D56)
        # APRÈS l'hétérogénéité → pas de transitoire de montée au tick 0.
        if self.epaisseur_sol is None:
            self.epaisseur_sol = GridField(self.rows, self.cols, max_val=EPAISSEUR_MAX)
        # Altitude (①) — bornée [0, ALT_MAX]. Créée PLATE (0) ici (construction directe
        # `EcoFields()` = mini-sol de conteneur, sans topographie → reste 0, inoffensif).
        # Le chemin monde `init_eco` la POSE hétérogène (canal de hash décorrélé de
        # l'humus). Repos NEUTRE d'une construction directe → déterminisme préservé.
        if self.altitude is None:
            self.altitude = GridField(self.rows, self.cols,
                                      max_val=ALT_BASE + 2.0 * ALT_AMPLITUDE)
        # Eau de surface (②) — NULLE au repos, bornée [0, HUM_CAP] (une lame ne dépasse
        # pas la profondeur d'un plot saturé). Écrite par `tick_hydrology` (capture du
        # surplus) puis rebrassée par `tick_ruissellement`. Repos NEUTRE (aucune
        # saturation) → déterminisme préservé pour une construction directe (conteneur).
        if self.eau_surface is None:
            self.eau_surface = GridField(self.rows, self.cols, max_val=HUM_CAP)
        # Mémoire de marais (③) — NULLE au repos, bornée [0,1], intégrée par
        # `tick_marais`. Repos NEUTRE (aucune flaque durable) → lecteurs décompo/pH
        # neutres → déterminisme préservé pour une construction directe (conteneur).
        if self.marais_memory is None:
            self.marais_memory = GridField(self.rows, self.cols, max_val=1.0)
        # État de marais (③) — False partout au repos (mémoire nulle < MARAIS_OFF).
        if self.marais_etat is None:
            self.marais_etat = [[False] * self.cols for _ in range(self.rows)]
        # Couverture du sol (sprint LUXURIANCE ①) — NULLE au repos, bornée [0,1],
        # écrite chaque tick par `tick_couverture` (scatter des empreintes basses).
        if self.couverture_sol is None:
            self.couverture_sol = GridField(self.rows, self.cols, max_val=1.0)
        # Paillage (sprint équilibre invasion ③) — NUL partout au départ, borné [0,1],
        # posé par le geste `pailler`, décru chaque tick par `tick_paillage`. Repos
        # NEUTRE (aucun geste) → lecteurs neutres → golden INTACT.
        if self.paillage is None:
            self.paillage = GridField(self.rows, self.cols, max_val=1.0)
        # Nature du mulch (④) — "" partout au repos (aucun plot paillé) → NATURE_NEUTRE
        # → lecteurs bit-identiques → golden INTACT. Une grille de chaînes propre.
        if self.paillage_nature is None:
            self.paillage_nature = [["" for _ in range(self.cols)]
                                    for _ in range(self.rows)]
        # Allélopathie (sprint ALLÉLOPATHIE ①) — NULLE au repos, bornée [0, ALLELO_MAX],
        # alimentée par `inject_field` (route générique) et déclinée par `tick_allelopathie`.
        # Repos NEUTRE (aucun émetteur, personne ne lit) → déterminisme préservé.
        if self.allelopathie is None:
            self.allelopathie = GridField(self.rows, self.cols, max_val=ALLELO_MAX)
        # Autotoxicité (sprint ALLÉLOPATHIE ④) — NULLE au repos, bornée [0, AUTOTOX_MAX],
        # montée/redescente saisonnière par `tick_autotoxicite`. Traceur d'identité à
        # None partout (aucune espèce émettrice au repos) → aucune montée → lecteurs
        # ②/③ voient `allelo_effectif == allelopathie` → déterminisme préservé.
        if self.autotox is None:
            self.autotox = GridField(self.rows, self.cols, max_val=AUTOTOX_MAX)
        if self.autotox_espece is None:
            self.autotox_espece = [[None] * self.cols for _ in range(self.rows)]
        # Mémoire d'inoculum (sprint mémoire d'inoculum ①) — VIDE au repos (aucun plot
        # infecté) → `at`/`total` renvoient 0 partout, `tick_decay` no-op → lu par
        # personne ce tronçon → déterminisme préservé, golden INTACT.
        if self.inoculum is None:
            self.inoculum = InoculumField()
        self._abri_cache = None
        # Signature du champ de lisière (③) — `None` = jamais calculé. `maj_lisiere`
        # ne reconstruit `eco.lisiere` que si les types de secteurs (ou l'offset de la
        # tuile) ont changé : la ceinture est quasi statique, donc coût ≈ 0 par tick.
        self._lisiere_sig = None

    def _init_heterogene(self, grid: GridField, plancher: float) -> None:
        """Pose `plancher` sur `grid` avec une HÉTÉROGÉNÉITÉ spatiale déterministe
        par plot (D56, ①). Facteur ∈ [1−INIT_AMPLITUDE, 1+INIT_AMPLITUDE] tiré du
        bruit `_hash_noise(seed_tuile, 0, r, c)` où `seed_tuile = stable_str_hash
        (tile_id)` → motif propre à chaque tuile, REPRODUCTIBLE (zéro RNG, philo #3).
        La borne ≥ 0 du GridField écrête les rares facteurs négatifs. Un plancher 0
        reste 0 (multiplication) → no-op sûr."""
        seed_tuile = stable_str_hash(self.tile_id)
        for r in range(self.rows):
            for c in range(self.cols):
                bruit = _hash_noise(seed_tuile, 0, r, c)       # [0,1]
                facteur = 1.0 + INIT_AMPLITUDE * (2.0 * bruit - 1.0)
                grid.set(r, c, plancher * facteur)

    def _init_catena(self, grid: GridField, base: float, amplitude: float,
                     canal_suffixe: str, poids_topo: float, sens_topo: float) -> None:
        """Hétérogénéise `grid` autour de `base` par une CATENA topographique
        déterministe (sprint DIVERSITÉ FONDATRICE ②). Chaque plot est multiplié par
        `1 + amplitude·(poids_topo·topo + (1−poids_topo)·bruit)` où :
          - `topo` LIT l'altitude déjà posée (`self.altitude`), recentrée depuis
            [ALT_BASE−ALT_AMPLITUDE, ALT_BASE+ALT_AMPLITUDE] vers [−1,1] et signée par
            `sens_topo` (−1 = riche en bas, +1 = plus fort en haut) → gradient LISIBLE ;
          - `bruit` dérive d'un canal de hash DÉCORRÉLÉ (`tile_id + canal_suffixe`) →
            pas de corrélation « plot riche partout », deux champs diffèrent plot-à-plot.
        Zéro RNG (philo #3). `GridField.set` borne déjà (portes pH/NPK) → facteurs
        extrêmes écrêtés. REQUIERT une altitude déjà posée (appelé APRÈS dans init_eco).
        Un `base` de 0 reste 0 (multiplication) → no-op sûr."""
        seed_c = stable_str_hash(self.tile_id + canal_suffixe)
        for r in range(self.rows):
            for c in range(self.cols):
                # Recentre l'altitude sur [−1,1] autour d'ALT_BASE (2·ALT_AMPLITUDE = pleine échelle).
                alt = self.altitude.at_plot(r, c)
                topo = sens_topo * ((alt - ALT_BASE) / ALT_AMPLITUDE)   # ≈ [−1,1]
                bruit = 2.0 * _hash_noise(seed_c, 0, r, c) - 1.0        # [−1,1] décorrélé
                facteur = 1.0 + amplitude * (poids_topo * topo + (1.0 - poids_topo) * bruit)
                grid.set(r, c, base * facteur)

    def get_field(self, name: str) -> GridField | None:
        """Champ nommé (clé = nom d'attribut) ou None. Avant : un dictionnaire de
        25 entrées reconstruit à CHAQUE appel (~4 000 appels/tick via l'uptake) ;
        désormais un test d'appartenance à `_CHAMPS_NOMMES` + `getattr` (FLUIDITÉ
        AN 2 ②) — même table de noms, même résultat."""
        return getattr(self, name) if name in _CHAMPS_NOMMES else None

    def allelo_effectif(self, r: int, c: int, plant_class) -> float:
        """Allélopathie EFFECTIVE ressentie par `plant_class` au plot `(r, c)`
        (sprint ALLÉLOPATHIE ④) = allélopathie AMBIANTE (champ `allelopathie`, tous
        émetteurs confondus, tronçons ②/③) PLUS l'autotoxicité `autotox` du plot SI
        cette espèce EST l'émetteur récurrent traceé ici (`autotox_espece`). La
        fatigue du sol ne frappe donc QUE l'espèce fatigante — une AUTRE espèce (ou
        la même sur un plot reposé) ne lit que l'ambiant, la rotation reste
        l'échappatoire lisible (D3). Lu par la germination (② succession) et la
        croissance (③ engine) à la place du raw `allelopathie.at_plot`.

        INVARIANT GOLDEN : `autotox` NUL partout (aucun émetteur avant le ⑤, le
        traceur ne s'arme jamais) ⇒ renvoie EXACTEMENT `allelopathie.at_plot(r, c)`
        ⇒ ②/③ bit-identiques au pré-④. Court-circuit rapide quand le plot n'est pas
        fatigué (cas du repos). Pure lecture, zéro RNG."""
        ambiant = self.allelopathie.at_plot(r, c)
        auto = self.autotox.at_plot(r, c)
        if auto > 0.0 and self.autotox_espece[r][c] is plant_class:
            return ambiant + auto
        return ambiant

    def fertilite_index(self, r: int, c: int) -> float:
        """Index nutritif LISSE dérivé (③) = moyenne des trois champs N/P/K, sur la
        même échelle [0,3] que l'ancien `fertilite`. Distinct du `min` de Liebig
        (que ressent la croissance/Vigueur) : c'est une grandeur stable pour les
        lecteurs qui veulent une fertilité agrégée (soil_memory, vitalité,
        succession) → seuils/normalisations historiques intacts en FORME."""
        return (self.n.at_plot(r, c)
                + self.p.at_plot(r, c)
                + self.k.at_plot(r, c)) / 3.0

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
             microbiome: float = 0.0, soil_type: str = "terre",
             heterogene: bool = False) -> EcoFields:
    """`fertilite` est un PARAM DE COMPAT (③ : le champ unique a disparu). Si fourni,
    il initialise les trois nutriments à la MÊME valeur uniforme (n=p=k=fertilite) ;
    si None (défaut), n/p/k gardent leur héritage `soil_type` (NUTRIENT_INIT_PAR_SOL).

    D56 (①) : `init_eco` est le chemin de construction des TUILES du monde (le golden
    et `main.py` passent par ici ; les mini-sols de conteneur, eux, appellent
    `EcoFields(...)` directement + une recette → PAS touchés, ce qui préserve leur
    déterminisme). C'est donc ici — et NON dans `__post_init__` — qu'on pose l'humus de
    fond `om_stable` HÉTÉROGÈNE (`_init_heterogene`, plancher OM_STABLE_INIT modulé par
    plot). Le sol vivant ne part jamais de zéro absolu ; certains secteurs partent plus
    humifères → ils amorcent plus tôt la facilitation des tardifs (`om_index` lu au
    tronçon ②) → succession hétérogène (philo #7), deux jardins jamais identiques.
    Les champs explicitement fournis (humidité/microbiome/NPK) restent UNIFORMES à la
    valeur demandée — l'hétérogénéité passe par le SEUL `om_stable`, ce qui garde le
    contrôle du re-figeage (kickoff §Modèle) et n'invalide aucun test unitaire qui
    contrôle un champ forcé plot à plot (test_eau/lessivage/substrat/mycelium).

    `heterogene` (sprint DIVERSITÉ FONDATRICE ①, défaut False) : quand True, ENSEMENCE
    en plus la banque-sol génétique FONDATRICE (`seed_founder_pool` par plot × espèce
    d'adventice) → la germination férale part avec une variance immédiate (fin des
    clones neutres). Posé True par les seuls sites monde-réel (golden, main, pont,
    bancs) ; les tests unitaires ciblés gardent le défaut False → INTACTS. Le flag
    portera AUSSI l'hétérogénéité des champs de sol au tronçon ②."""
    eco = EcoFields(tile_id=tile_id, rows=rows, cols=cols, soil_type=soil_type)
    eco._init_heterogene(eco.om_stable, OM_STABLE_INIT)
    for r in range(rows):
        for c in range(cols):
            eco.humidite.set(r, c, humidite)
            eco.microbiome.set(r, c, microbiome)
            if fertilite is not None:
                eco.n.set(r, c, fertilite)
                eco.p.set(r, c, fertilite)
                eco.k.set(r, c, fertilite)
    # Épaisseur de sol AU REPOS (D57 ①a) : APRÈS l'humus de fond hétérogène (l'om_stable
    # ci-dessus est posé) → cible calculée sur cet état de départ (litière vide + active
    # 0 + stable hérité). Le sol part donc déjà au niveau d'équilibre correspondant à
    # son humus de fond, sans transitoire de montée au tick 0. Suit ensuite la MO
    # (`tick_epaisseur`). Lu par PERSONNE ce tronçon → golden inchangé.
    for r in range(rows):
        for c in range(cols):
            eco.epaisseur_sol.set(r, c, eco._cible_epaisseur(r, c))
    # Altitude — micro-relief topographique FIXE (sprint hydrologie & marécages ①).
    # Posée sur un canal de hash DÉCORRÉLÉ de l'humus (`_init_heterogene` sème sur
    # `stable_str_hash(tile_id)` ; ici on sème sur `tile_id + "_alt"` → motif de relief
    # INDÉPENDANT de la fertilité, deux terrains jamais identiques, philo #3/#7). Le
    # facteur de bruit ∈ [0,1] est recentré en [−1,1] → `ALT_BASE ± ALT_AMPLITUDE`,
    # borné ≥ 0 par le GridField. Aucun tick ne l'écrit (seuls les gestes ⑦ le
    # modifieront) → lu par PERSONNE ce tronçon → golden inchangé.
    seed_alt = stable_str_hash(tile_id + "_alt")
    for r in range(rows):
        for c in range(cols):
            bruit = _hash_noise(seed_alt, 0, r, c)              # [0,1]
            eco.altitude.set(r, c, ALT_BASE + ALT_AMPLITUDE * (2.0 * bruit - 1.0))
    # Catena topographique des champs édaphiques (sprint DIVERSITÉ FONDATRICE ②) —
    # SOUS le flag `heterogene`, et APRÈS l'altitude (la catena la LIT). Les champs de
    # sol STATIQUE non nuls (ph/n/p/k/structure_sol/microbiome) partent HÉTÉROGÈNES,
    # structurés par le relief : fond riche, versant pauvre mais mieux structuré (philo
    # #5/#6/#7). `base` = valeur uniforme héritée du plot (avant catena) — on la lit sur
    # le plot [0][0] (uniforme à ce stade : héritage roche-mère + éventuel `fertilite`/
    # `microbiome` forcés ci-dessus). `humidite` EXCLUE (le ruissellement la creuse déjà
    # depuis l'altitude → hétérogénéité redondante) ; `om_stable`/`altitude` non retouchés.
    # Amplitudes PETITES pour pH (portes `bell`, faim d'azote, mort carence D41) → jamais
    # de plot hors-fenêtre catastrophique (le GridField borne en plus).
    if heterogene:
        eco._init_catena(eco.ph, eco.ph.at_plot(0, 0), PH_INIT_AMPLITUDE,
                         "_ph", CATENA_POIDS_TOPO["ph"], CATENA_SENS_TOPO["ph"])
        eco._init_catena(eco.n, eco.n.at_plot(0, 0), NPK_INIT_AMPLITUDE,
                         "_n", CATENA_POIDS_TOPO["n"], CATENA_SENS_TOPO["n"])
        eco._init_catena(eco.p, eco.p.at_plot(0, 0), NPK_INIT_AMPLITUDE,
                         "_p", CATENA_POIDS_TOPO["p"], CATENA_SENS_TOPO["p"])
        eco._init_catena(eco.k, eco.k.at_plot(0, 0), NPK_INIT_AMPLITUDE,
                         "_k", CATENA_POIDS_TOPO["k"], CATENA_SENS_TOPO["k"])
        eco._init_catena(eco.structure_sol, eco.structure_sol.at_plot(0, 0),
                         STRUCTURE_INIT_AMPLITUDE, "_struct",
                         CATENA_POIDS_TOPO["structure_sol"],
                         CATENA_SENS_TOPO["structure_sol"])
        eco._init_catena(eco.microbiome, eco.microbiome.at_plot(0, 0),
                         MICROBIOME_INIT_AMPLITUDE, "_micro",
                         CATENA_POIDS_TOPO["microbiome"],
                         CATENA_SENS_TOPO["microbiome"])
    # Banque-sol FONDATRICE (sprint DIVERSITÉ FONDATRICE ①, option A) — SOUS le flag
    # `heterogene` (posé par les sites monde-réel : golden, main, pont, bancs). Pour
    # chaque plot × chaque adventice de WEED_CATALOGUE, on ENSEMENCE le pool
    # génétique (`seed_founder_pool` : mean=1.0, var=GENE_INIT_SIGMA², densité
    # FOUNDER_POOL_DENSITY). Une vraie banque de graines du sol n'est JAMAIS
    # génétiquement uniforme (philo #4) → dès le tick 0, `sample_genes` tire la
    # germination férale avec une variance immédiate, et la sélection darwinienne a
    # de quoi mordre sans attendre N générations. Import LOCAL de WEED_CATALOGUE
    # (couche : `fields` ne dépend pas de `plants.catalogue` en tête de module ;
    # exécuté uniquement sur le chemin monde, jamais pour un mini-sol de conteneur).
    if heterogene:
        from plants import WEED_CATALOGUE
        for r in range(rows):
            for c in range(cols):
                for cls in WEED_CATALOGUE.values():
                    eco.seed_bank.seed_founder_pool(
                        r, c, cls, GENE_INIT_SIGMA, FOUNDER_POOL_DENSITY)
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
