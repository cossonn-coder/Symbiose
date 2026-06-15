## 2026-06-13 — Sprint compétition intra-plot · IMPLÉMENTATION CLOSE — golden RE-FIGÉ maîtrisé (3 causes)

Implémentation de la conception figée ci-dessus. **5 tronçons**, golden re-figé
de façon maîtrisée et annoncée, suite complète verte, `main.py` 30 ans propre.

**Fait, par tronçon :**
- **T1 — verrou levé (`sim/succession.py`)** : suppression des gardes
  d'occupation des 3 portes (`succession`, `spring_flush`, `_lever_grains_en_attente`).
  Plus de plot binairement « occupé » ; la cohabitation est arbitrée par les
  champs réels. `tile.add_plant` permettait déjà la co-localisation.
- **T2 — gène `tolerance_ombre`** : ajouté EN FIN de `GENE_NAMES` (canaux de hash
  `child_genes` préservés pour les 5 gènes existants). Défaut par strate
  (`STRATE_SHADE_TOLERANCE` : sol/basse 1.25 sciaphile, moyenne 1.0, haute 0.90
  héliophile), override explicite possible (`PlantBase.shade_tolerance`). Entre en
  **germination** (escompte `light_eff = min(1, light × tol)` dans
  `germination_candidates` + à la levée des grains plantés) ET en **croissance**
  (`growth_factor` de `_update_physiology`).
- **T3 — étiolement (`sim/growth.py`)** : `est_etiole` (héliophile, tol<1, sous
  lumière effective < 0.40) → vitesse axiale ×1.30 dans `grow_plant` + léger frein
  de guérison dans `_tick_senescence_health`.
- **T4 — densité intra-plot : SAUTÉ (décision).** Q4 figée prévoyait d'inclure les
  co-occupants du centre dans `_local_density` (fonte des semis intra-plot). La
  **mesure** (`tests/_mesure_competition.py`) a montré que l'éclaircissage émerge
  DÉJÀ via les stress existants (eau/uptake/asphyxie) : pic ~73 plantes → final ~12
  ≈ baseline, pas d'embouteillage de « zombies ». Le kickoff conditionnait ce
  tronçon à « si justifié » → jugé non justifié. **Écart à valider par Nico** : la
  fonte des semis intra-plot stricto-sensu (co-occupants dans la densité) n'est PAS
  câblée ; la compétition passe par les autres canaux. Réactivable si besoin.
- **T5 — tests** : `test_competition.py` (NOUVEAU, 14 checks : règle de tolérance
  par strate + override, `est_etiole`, étiolement observable, escompte de niche
  sous canopée, co-occupation spontanée) ; `test_planter` test 4 **réécrit**
  (l'ancienne assertion Q4 « plot occupé → graine PATIENTE » est inversée vers
  §2.4 « lève en co-occupation ») ; `test_senescence` **isolé** de la succession
  (double de test `germination_candidates → []` : sinon ~27 adventices vivaces
  tuent le pommier solitaire par compétition hydrique vers ~7 ans — émergence
  légitime mais qui défait l'isolation voulue du test de sénescence).

**Re-figeage golden (chaîne, maîtrisé) :**
`7ee907d3…` (départ, post planter/arroser) → `37da42e7…` (T1) → `2157f38e…` (T2)
→ **`6bf71ee5…`** (T3, FINAL). Population golden (vie macro, scénario distinct) :
`b005d9ba…` → **`f1fe093c…`** (mêmes 3 causes : germination plus dense → réponse
des champs de population différente ; déterminisme `h1==h2` intact). Les 3 causes
attendues sont les seules observées.

**Paradoxe pionnier (à trancher, post-test §4).** La règle de strate rend les
**4 adventices sciaphiles** (toutes strate sol/basse → tol 1.25), alors que ce
sont des ruderales **héliophiles**. Conséquences : (1) écologiquement à l'envers ;
(2) **aucune adventice héliophile n'existe** → le critère de succès « héliophile
ne lève pas sous canopée » n'est pas démontrable avec les espèces réelles (testé
sur le **mécanisme** dans `test_competition`, pas sur une adventice). Correctif
trivial (override `shade_tolerance` héliophile sur les 4 espèces, autorisé par §4
« valeurs affinées post-test ») — MAIS ce serait une **4ᵉ cause de dérive du
golden**, donc laissé à la décision de Nico plutôt qu'appliqué unilatéralement.

**Vérifs** : `test_golden` `6bf71ee5…`, `test_competition` 14/14, `test_planter`
18/18, `test_senescence` 59,8 ans (sénescence), `test_population` re-figé,
`test_sim_server`/`genetique`/`croissance`/`vigueur`/`eau`/`phototropisme`/
`maitrise` PASS, `main.py 30` propre (exit 0, ~32-36 vivantes/tuile).

**Suivant** : scénario potager annuel dans `main.py` (semis dense
tomate/basilic/poivron/tournesol chaque printemps via le geste `planter` fidèle,
une tuile dédiée) — petit travail, hors moteur. Puis paradoxe pionnier + T4 si
Nico veut les reprendre.

---
