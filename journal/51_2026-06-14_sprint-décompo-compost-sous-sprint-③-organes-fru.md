## 2026-06-14 — Sprint décompo & compost · sous-sprint ③ : organes-fruits traçables — golden NEUTRE — absorbe D19

**Intention** : un fruit cesse d'être un **proxy de rendu saisonnier**
(`REPRO_BY_SEASON`, côté `tools/render_structure`) pour devenir un **état moteur
réel** — il naît à la nouaison, mûrit semaine après semaine, se **mange un par
un** (déplétion = D19), et **tombe en litière `fruit`** s'il n'est pas cueilli
(branche enfin la cascade fertilité de ① sur le canal fruitier).

**Modèle** (carte blanche, conception §3 FIGÉE) :
- `Fruit{segment_id, maturite, masse}` (`plants/base.py`) porté par
  `PlantInstance.fruits`. Flag d'éligibilité `PlantBase.fruitier` (Tomato,
  AppleTree). Le moteur **ne lit jamais `segment_id`** (simple repère pour la
  VUE ⑥) → le déterminisme et le golden sont **indépendants de la structure** de
  segments : seules `masse` (litière) et `maturite` (gain/seuil) pèsent.
- `organ_sites(plant)` placé en **couche basse** (`plants/base.py`), pas dans
  `tools` : `sim` peut l'importer sans violer la frontière de couches
  (CLAUDE.md). Géométrie pure sur les apex (`terminal`=tous / `lateral`=sauf
  meneur), plafond `MAX_ORGANS`=10. Le `_organ_sites` du rendu reste le proxy
  VUE intact (réconciliation différée à ⑥). Duplication de constante assumée.
- `engine._tick_fruits` (étape **15c**, chaque semaine) : **nouaison annuelle**
  fixe à `FRUIT_NOUAISON_WEEK`=14 (rendez-vous unique → anti-sur-création,
  déterministe), gardée par `fruitier ET age_years ≥ maturity_years` ; cohorte
  précédente non récoltée chutée d'abord ; **maturation** `+FRUIT_DMAT`(0.08) ;
  **chute** des sur-mûrs (`> MATURITE_CHUTE`=1.3) → `deposer_litiere(.., "fruit",
  FRUIT_MASSE=0.15)`.
- `manger` **dual-mode** (`sim/actions.py`) : `fruit_index` valide → consomme CE
  fruit (gain `= HARVEST_GAIN_FULL × santé × **maturité_fruit** × Qi × gène`,
  l'organe **disparaît**) ; sans index / hors-borne → **chemin générique legacy**
  (façade plante entière) → les tests vigueur D1-D4 restent verts. Coût NUL
  inchangé.
- Pont `sim_server.py` **0.3.3 → 0.3.4** : snapshot expose `plant.fruits`
  (`[{segment, maturite, masse}]`) ; `manger` route `target.fruit` (validé
  int+bornes, comme `tailler.segment`).

**Décision — golden NEUTRE (non re-figé), vérifié empiriquement** : la seule
espèce `fruitier` du scénario golden est AppleTree, dont `maturity_years`=5
dépasse la fenêtre de 2 ans → la nouaison n'est **jamais** déclenchée (même
logique de neutralité que ②A par gate). Hashs **bit-identiques à ②** : smoke
`908f591b…`, population `435e6f72…`. La vraie dérive fruitière n'apparaîtra que
sur un horizon ≥ 5 ans (couverte hors golden).

**Tests** : nouveau `tests/test_fruits.py` (**21 checks**) — nouaison, gate
d'âge (→ neutralité golden), annualité + remplacement de cohorte, maturation,
chute→litière, déterminisme (h1==h2), `manger` ciblé (gain ∝ maturité, ratio 3×
exact, déplétion réelle), `manger` générique (fallback). Suites vertes : golden,
population, vigueur 135, croissance 67, competition 14, eau 20, génétique 20,
maîtrise 35, maîtrise_detection, auxiliaires, signes 8, ombre_maison 4,
phototropisme 11, planter 18, sim_server 113, senescence, **fruits 21** ;
`main.py 5` exit 0.

**Sous-sprint ③ CLOS** (D19 absorbée). **Suivant** : ④ attraction animale (fruit
frais→`auxiliaire` / pourri→`ravageur`, pile à bois→habitat), ⑤ structures
posables, ⑥ vue Godot (différé). Écrire `04_*.md` avant ④. Reprise :
`00_etat.md` §REPRISE.

---
