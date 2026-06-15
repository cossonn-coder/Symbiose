## 2026-06-13 — Sprint conception : compétition intra-plot (cohabitation, stratification, éclaircissage) — CONCEPTION SEULE

Suite directe du sprint planter/arroser : **réaliser Q4** (« EMPILEMENT
AUTORISÉ », renvoyée ici). **Aucun code moteur** — livrable = conception figée
`docs/conception/CONCEPTION_COMPETITION_INTRAPLOT.md` + kickoff d'impl
`sprints/sprint_competition_intraplot.md`. Golden inchangé (`7ee907d3…`).

**Posture cadrée d'emblée** : la compétition est **déjà émergente** dans le
moteur (lumière asymétrique `light_received` filtre par voisins plus hauts +
uptake partagé sur `root_plots` chevauchants) — le risque était de la
**ré-empiler**. Le verrou réel est **uniquement** dans la germination
(`succession.py` : 3 portes sautent les plots occupés). L'empilement est déjà
permis au niveau bas (`tile.add_plant` ne vérifie pas l'occupation).

**Décisions figées (Nico, Q1–Q11) :**
- **Q1 — lever le verrou SANS malus artificiel.** Supprimer les 2 gardes
  (`occupied_roots` + position exacte) des 3 portes. Pas de terme « occupation » :
  la niche est freinée par les **champs réels** (lumière-sol ombragée par la
  canopée + sol établi). Nico recadre : **pas de plot binairement « occupé »** —
  hautes/grimpantes/couvre-sol **cohabitent par stratification** si les
  conditions le permettent.
- **Q2 — pas de cap dur** ; l'écologie borne seule (vigilance perf D32).
- **Q3 — lever et MESURER** ; la mort du perdant émerge de
  `_tick_senescence_health` → nécromasse. Pas de mortalité « verdict ».
- **Q4 — éclaircissage par convergence de stress existants** : fonte des semis
  (inclure les **co-occupants du centre** dans `_local_density`, aujourd'hui
  exclus par `plots_within_radius` qui `discard` le centre) + place racinaire /
  uptake + asphyxie + nutriments.
- **Q5 — le plus haut gagne** ; le plus bas n'ombrage pas au-dessus (déjà codé +
  gain perf).
- **Q6 — NOUVEAU GÈNE `tolerance_ombre`** (>1 = sciaphile) dans `GENE_NAMES`,
  hérité via `child_genes`, défaut par strate ; entre en **germination** (lumière
  effective `light × tolerance_ombre`) ET en **croissance** (`growth_factor`).
- **Q7 — AJOUTER L'ÉTIOLEMENT** : héliophile ombragé élonge plus (tige grêle) au
  prix de la robustesse → sauvé s'il atteint la lumière (phototropisme existant),
  sinon dépérit.
- **planter** : graine plantée sur plot occupé **lève** (réalise enfin Q4 du
  sprint planter). **espèces** : aucune restriction (guilde émergente).

**Trouvaille pédagogique clé** : le moteur a la **géométrie** des strates (champ
`strate`, `STRATE_PROFILES`) mais **pas l'écologie** — l'ombre pénalisait tout le
monde pareil, `niche_index` ignorait toute préférence d'ombre. Sans le gène
`tolerance_ombre`, « couvre-sol sous une haute » **ne survivait pas**. C'est le
maillon que le sprint d'impl ajoute.

**Re-figeage golden attendu à TROIS causes isolées** (d'où l'ordre des tronçons
d'impl : empilement seul **d'abord**, puis gène, puis étiolement) : (1) plus de
germinations sur plots auparavant exclus ; (2) vecteur de gènes +1 → canaux de
hash `child_genes` décalés ; (3) morphogénèse de l'étiolement. Chaque dérive
comptée et expliquée.

**Suivant** : implémentation (kickoff prêt, ampleur **moyen**, 4 tronçons +
tests) OU autre item backlog au choix de Nico.
