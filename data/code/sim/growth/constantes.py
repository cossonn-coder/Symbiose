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
THICKEN_RATE   = 0.03    # cm/tick d'épaississement du bois porteur

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
