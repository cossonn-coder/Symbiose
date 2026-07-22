# Backlog — pistes de génération / renouvellement de terrain

> Section de [`BACKLOG.md`](../../../BACKLOG.md) reprise **verbatim**.

### Pistes génération / renouvellement de terrain — analyses PDF (2026-06-23)
> Lecture de deux papiers d'algorithmic botany : ① modélisation procédurale d'arbres
> 3D (hors-scope à 90 %), ② Lane & Prusinkiewicz 2002, « Generating Spatial
> Distributions for Multilevel Models of Plant Communities » (2D, sur grille de
> probabilité). Bilan : les mécaniques niche/lumière/succession/compagnonnage sont
> **déjà dans le moteur, souvent en mieux** (`niche_index` n-dim, `bell(pH)`,
> `shade_tolerance_base` + gène `tolerance_ombre`, `shade_stress_damage`, sénescence
> `_tick_senescence_health`, registre d'effets typés `basil_companion_check` /
> family_effects). Les papiers **valident** l'archi (et le multi-niveaux = Option B).
> Restent ces angles morts réels (génération INITIALE des champs + renouvellement
> temporel), à creuser un jour — aucun n'est urgent.
- [ ] **Prototypes de taches de sol** (self-similarité) — initialiser l'hétérogénéité
  du microbiome/fertilité par instanciation + perturbation locale d'un petit
  catalogue de motifs. Sert les 3 écoles de départ et l'hétérogénéité persistante.
- [ ] **Sénescence de cohorte → gaps** — champ « âge de cohorte » ouvrant des trouées
  quand une classe d'âge meurt ensemble. Renouvellement spontané du jardin éternel.
  (La sénescence INDIVIDUELLE existe déjà : `mortalite.py:_tick_senescence_health`.)
- [ ] **Gradient directionnel sur un champ** — primitive simple de transition douce
  orientée (ex. humidité plus haute d'un côté du terrain).
- [ ] **Noyau de dispersion contrôlable des semis** — état réel du moteur (corrige une
  note antérieure imprécise) : les **archétypes** déposent au plot-foyer du parent
  (`mortalite.py:_reproduction` → banque-sol, germination par niche) ; les
  **vivaces/arbres** recrutent DÉJÀ dans un rayon (`RESEED_RADIUS_CM = 150 cm`) mais
  par sélection du plot le plus **lumineux**, pas par noyau probabiliste. Piste :
  noyau gaussien à rayon paramétrable → levier « petit rayon → agrégats / grand →
  homogène » (Fiche dispersion P②).
- [ ] **Indice de Hopkins comme outil de validation** (P②) — métrique scalaire
  clusterisé/aléatoire/dispersé. À utiliser en test pytest pour valider que les futurs
  générateurs des 3 écoles produisent bien la texture spatiale visée. Outil, pas
  mécanique de jeu.
- [ ] **Deformation-kernel pour le placement initial** (P②) — placement global-to-local
  par noyau d'inhibition/promotion sur un champ de proba 2D (`f` initialisé depuis
  fertilité × humidité). Séquentiel donc PAS hash-spatial-pur → réservé à
  l'**initialisation** du monde (calcul unique, résultat persisté via seed), jamais
  par-tick. Donne un levier de forme de clustering par espèce.
