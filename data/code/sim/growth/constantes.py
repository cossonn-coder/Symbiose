"""
SYMBIOSE — sim/growth/constantes.py
Leviers de module de la croissance procédurale (D29 réorienté). Couche basse du
paquet `sim.growth`, sans dépendance interne.

Tronçon 2 : les leviers PAR ESPÈCE (vitesse, dominance, angle, gabarit, longévité
du bois) ont été promus en attributs de classe sur PlantBase (§E.1). Les constantes
marquées « ↳ défaut PlantBase » ci-dessous ne sont plus lues par grow_plant : elles
restent comme valeurs de référence, mirroir des défauts de PlantBase. Les autres
(EMIT_LENGTH, THICK*, JITTER_RAD, MAX_SEGMENTS, AUXIN_DECAY/THRESHOLD/FLOOR/SCALE)
demeurent des leviers de module communs à toutes les espèces.
"""

from __future__ import annotations
import math

# --- Auxine (dynamique de la dominance apicale, §D.1) ----------------------
AUXIN_SOURCE          = 1.0     # ↳ défaut PlantBase.apical_dominance_base (production d'un apex au repos)
AUXIN_DECAY           = 0.88    # transport descendant : auxin ×= DECAY par segment
AUXIN_INHIB_THRESHOLD = 0.35    # sous ce niveau, un bourgeon peut débourrer
AUXIN_PROD_FLOOR      = 0.15    # plancher de production (vieux sujet s'étale)
AUXIN_RELEASE_SCALE   = 400.0   # semaines : échelle de relâchement avec l'âge

# --- Allongement & émission (§D.2) -----------------------------------------
GROWTH_SPEED   = 2.0     # ↳ défaut PlantBase.growth_speed (cm/tick d'allongement)
EMIT_LENGTH    = 8.0     # cm : au-delà, l'apex émet un segment axial
THICKNESS_INIT = 0.3     # épaisseur d'un segment neuf
THICKEN_RATE   = 0.03    # OBSOLÈTE depuis le sprint lisibilité ligneuse (2026-07-23) :
                         # l'accumulation uniforme non bornée (baobab + ronces d'égal
                         # diamètre) est remplacée par le pipe model `taper_thickness`
                         # (geometrie.py). Conservé pour mémoire (garde-fou « conserver
                         # le code ») — plus lu par grow_plant.

# --- Croissance secondaire du bois (sprint lisibilité ligneuse, pipe model) ---
# Remplace THICKEN_RATE. L'épaisseur d'un segment DÉRIVE de la topologie (pipe
# model : section ∝ nombre de terminaux portés en aval) et d'une croissance
# secondaire SATURANTE avec l'âge → tronc épais mais BORNÉ, brindilles fines.
# thickness = THICKNESS_INIT + girth_max_espèce · (1−exp(−âge/GIRTH_TAU)) · taper.
GIRTH_TAU  = 300.0   # semaines : échelle de saturation de la croissance secondaire (placeholder → F5)
TAPER_EXP  = 0.5     # exposant du pipe model (0.5 = section ∝ n_term ; →1 = hiérarchie visuelle plus marquée) (placeholder → F5)

# --- Débourrement (§D.3) ----------------------------------------------------
BRANCH_ANGLE = math.radians(50.0)  # ↳ défaut PlantBase.branch_angle (50°) — converti à la lecture
JITTER_RAD   = math.radians(20.0)  # amplitude du jitter déterministe d'azimut

# --- Phototropisme (§D.4 — biais directionnel vers la lumière) --------------
PHOTOTROPISM_STRENGTH = 0.30                # ↳ défaut PlantBase.phototropism_strength (MARQUÉ, Q3)
MAX_PHOTOTROPISM_TILT = math.radians(12.0)  # déviation max d'azimut par segment émis (borné)
MIN_APEX_Z            = 0.30                 # composante verticale plancher de l'apex (jamais à plat)

# --- Port grimpant (D49 volet A, CONCEPTION_GRIMPANTES §3 — affalement) ------
# Plancher de verticalité EFFONDRÉ d'une grimpante LIBRE (non accrochée) qui a
# dépassé sa `hauteur_autoportante` : son apex ne se tient plus, il retombe
# (biais gravitaire léger vers le bas). max_z plafonne ~hauteur_autoportante et
# les segments suivants s'étalent → port affalé ÉMERGENT (philo #2, aucune hauteur
# clampée). Placeholder de calibrage (maquette ⑥). Une non-grimpante garde MIN_APEX_Z.
DROOP_Z               = -0.10                # composante z visée quand l'apex retombe

# Plancher de verticalité RENFORCÉ d'une grimpante ACCROCHÉE (②) tant qu'elle n'a
# pas atteint le sommet de son appui : l'apex vise fort vers le haut (l'axe du
# support) → la structure MONTE le long du tuteur/treillis/mur. Plus haut que
# MIN_APEX_Z (montée franche, pas la simple verticalité « jamais à plat »). Une
# fois au sommet de l'appui, on repasse à MIN_APEX_Z (la plante tient, ne force
# plus la montée). Placeholder de calibrage (maquette ⑥).
GRIMPE_Z              = 0.85                  # composante z visée en montée accrochée

# Tige libre d'une liane (sprint HOUPPIER ②, `tige_libre.py`). Tous [choix], à juger au F5.
LIGNIF_TIGE_MIN       = 0.25   # part de L_crit acquise sans lignification (jeune tige)
PLIAGE_Z              = -0.70  # composante z visée par une tige pliée : elle pend
PLIAGE_GAIN           = 0.35   # courbure par segment émis : l'arc se fait en 3 à 4 segments
MARGE_EFFONDREMENT    = 1.5    # libre > L_crit × marge → la partie pliée tombe
RELAIS_BIAIS          = 0.5    # force du rapprochement horizontal vers un nouvel appui
RELAIS_CONTACT_CM     = 15.0   # en deçà, la tige est contre son appui : plus de biais

# --- Étiolement (compétition intra-plot, Q7 — « filer vers la lumière ») -----
# Un HÉLIOPHILE (tolérance à l'ombre effective < 1) ombragé (lumière effective
# sous le seuil) ALLONGE plus vite en axial (tige grêle, entre-nœuds longs) :
# combiné au phototropisme, il a une chance d'atteindre une trouée → SAUVÉ. Le
# coût (robustesse −10 %) est porté côté convalescence (engine._tick_senescence_health).
# Un sciaphile (tol ≥ 1) ne s'étiole jamais. light_field absent → pas d'étiolement.
ETIOLEMENT_LIGHT_SEUIL = 0.40   # lumière effective sous laquelle un héliophile file
ETIOLEMENT_GAIN        = 0.30   # +30 % de vitesse axiale quand étiolé

# --- Bornage (§D.6 — run éternel) ------------------------------------------
MAX_REACH_CM     = 200.0  # ↳ défaut PlantBase.max_height_cm/max_extent_cm (gabarit d'arbre)
WOOD_PERSISTENCE = 60     # ↳ défaut PlantBase.wood_persistence (longévité du bois sans apex)
MAX_SEGMENTS     = 40     # plafond dur de segments par plante (filet de sécurité)

# --- Seam de perturbation (§F) ---------------------------------------------
COUPE_NETTE = 0.8   # intensité-seuil : AU-DELÀ, la perturbation ÉCIME (retrait du
                    # segment ciblé + son sous-arbre) ; EN DEÇÀ, elle ne fait que
                    # baisser l'auxine locale (perturbation douce). Levier de calibrage.

# --- Calibrage de l'ÉCRASEMENT (volet 2, CONCEPTION_ECRASEMENT §5) ----------
# Ces leviers sont LUS par sim.actions.ecraser_plante (geste joueur event-driven),
# JAMAIS par grow_plant → le golden ne peut pas bouger. growth.py reste pur
# structurel : la mutation `health` (régime NET) est faite dans actions.py ; ici on
# ne fournit que les CONSTANTES + la fonction d'âge (pures, déterministes).
INTENSITE_PIED     = 1.0    # intensité nominale d'un pied au sol (espèce de résistance
                           # nulle → NET franc) ; modulée par resistance × âge en aval.
SEUIL_DEGAT        = 0.5    # seuil sur (1 − stimulation) : au-delà, un écrasement NET
                           # entame la santé. Sépare les épargnées (stim ≥ 0.5 : basilic,
                           # pâturin, trèfle…) des entamées (stim < 0.5 : tournesol…).
LIGNIFICATION_SCALE = 52.0  # semaines : échelle de lignification. f≈0 pour un semis
                           # (s'écrase), → 1 pour un sujet établi (résistance pleine).

# --- Mort des branches (D111 ②bis, cf. cladoptose.py) ------------------------
# Cladoptose : lumière à une pointe = lumière reçue par la plante × (1 − densité ×
# OPACITE)^n, n = autres pointes de la même couronne plus hautes de > DZ dans un
# rayon horizontal RAYON. Une branche dont TOUTES les pointes sont sous SEUIL / tol
# et dont la racine a ≥ AGE_MIN × tol semaines tombe. SEUIL balayé sur 4 arbres
# isolés en plein soleil, 520 sem. [n=1 arbre/espèce, croissance sans lumière] :
# 0,30 démantèle chêne/hêtre (32 → 12 segments, la structure ne réitère pas) ;
# 0,12 → ~0 chute ; 0,18 → 0-2 branches/an dès l'an 7, couronne préservée.
# ②ter : avec le rythme BORNÉ (CLADO_FENETRE) le seuil remonte sans raser : 0,25,
# balayé 0,18/0,25/0,30 sur 7 arbres pré-crûs 14 ans [n=1 arbre/espèce, plein
# soleil] → adultes (an 8-14) pommier 1-3/an, cerisier 2-4, chêne/hêtre 0-2,
# charme 1-3, bouleau ~0 (couronne claire) ; sous lumière 0,6 : bouleau 3-6/an,
# hêtre 0-3 (l'héliophile lâche, le sciaphile garde).
CLADO_OPACITE_GRAPPE = 0.35   # part de lumière qu'une grappe de feuillage intercepte (× densité d'espèce)
CLADO_DZ_CM          = 30.0   # une grappe ne fait de l'ombre qu'à ce qui est nettement plus bas
CLADO_RAYON_CM       = 80.0   # rayon horizontal de l'ombre portée d'une grappe (soleil haut)
CLADO_SEUIL          = 0.25   # lumière sous laquelle une branche n'est plus rentable (tol = 1)
CLADO_AGE_MIN        = 26     # semaines : âge minimal d'une branche condamnée (tol = 1)
# Bornage du RYTHME (D111 ②ter) : un arbre ne lâche au plus que CLADO_PAR_FENETRE
# branche(s) d'ombre par FENÊTRE de CLADO_FENETRE semaines (la plus sombre d'abord),
# fenêtre déphasée par arbre (hachage de sa position). Saison feuillée d'un caduc ≈
# 39 sem. → au plus ~6 branches/an : jamais une couronne rasée d'un coup.
CLADO_FENETRE        = 6      # semaines entre deux cladoptoses possibles d'un même arbre
CLADO_PAR_FENETRE    = 1      # branches d'ombre au plus par fenêtre
