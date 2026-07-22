# CONCEPTION — DIVERSITÉ FONDATRICE

> Régler les **conditions de départ** de la simu sur deux axes couplés : la
> **génétique des plantes** (chaque plante un patrimoine propre, mutant à chaque
> génération) et l'**hétérogénéité des champs** de sol. But émergent : **chaque
> plante a son propre rythme**, et deux terrains ne sont jamais identiques.
>
> Figé le 2026-07-10 (`/conception`). Prêt pour `/sprint-auto`.

## 1. Constat — ce qui existe déjà (source de vérité `data/code/`)

Le moteur génétique est à ~90 % en place :
- Vecteur de 10 gènes (`plants/genetics.py:GENE_NAMES`), dont `vigueur`,
  `germination_thermique`, `phenologie_florale` = le **rythme**.
- **Mutation par génération** : `sim/reproduction.py:child_genes` (gaussienne
  `MUTATION_SIGMA=0.05`, déterministe par hash). ✅
- Héritage biparental + autofécondation + introgression. ✅
- **Sélection darwinienne émergente déjà câblée** : `_germ_gene_mean` relit
  `GeneStat.mean` du pool-sol → l'optimum de germination/floraison dérive là où
  le milieu sélectionne, sans code de sélection dédié. ✅
- Banque-sol `fields/seedbank.py` : distribution **moyenne+variance par plot ×
  espèce** (`GeneStat`), échantillonnée par `sample_genes`. ✅

**Le manque** — la **variance FONDATRICE = 0** :
- `GENE_INIT_SIGMA = 0.10` défini (`genetics.py:72`) mais **jamais utilisé**.
- Toute plante née **sans lignée** reçoit `genes = {}` → tous gènes 1.0 →
  **clones parfaits**. La diversité n'apparaît qu'après N générations de mutation.
- Côté sol : sur le chemin monde `init_eco`, **seuls `om_stable` et `altitude`**
  sont hétérogènes ; `ph`, `n/p/k`, `structure_sol`, `microbiome`, `humidite`
  démarrent **uniformes** (choix historique délibéré, pour contrôler le re-figeage).

## 2. Principe retenu

### 2.1 Axe génétique — banque-sol fondatrice + semis directs
Une **banque de graines du sol n'est jamais génétiquement uniforme** (philo #4 :
le sol porte la mémoire, ici la diversité latente). Donc :
- **Ensemencer** la couche `SeedBank.species` (GeneStat) au démarrage des tuiles
  monde, pour les espèces d'adventices (WEED_CATALOGUE), avec une distribution
  fondatrice : `mean=1.0`, `var=GENE_INIT_SIGMA²`, `weight=densité fondatrice`
  (> `SPECIES_POOL_MIN_DENSITY` pour que `sample_genes` l'utilise). → les semis
  féraux tirent avec **variance dès le départ** ; la sélection a de quoi mordre
  immédiatement.
- Pour les naissances **hors banque** (8 cultivées de la démo, graine `planter`
  sans lignée héritée), une fonction `founder_genes(...)` tire un vecteur gaussien
  `N(1.0, GENE_INIT_SIGMA)` par gène, **déterministe** (voir 2.3).
- La **mutation par génération** (déjà là) prend ensuite le relais.

### 2.2 Axe champs — catena topographique
Hétérogénéiser les champs édaphiques **structurés par l'altitude** déjà posée
(paysage lisible, philo #5/#6 : le joueur voit le gradient versant/fond) :
- Champs concernés : `n`, `p`, `k`, `ph`, `structure_sol`, `microbiome`.
- Chaque champ = base × facteur, `facteur = 1 + A_champ·[ w·topo(r,c) + (1−w)·bruit_propre(r,c) ]`
  où `topo` dérive de l'`altitude` (NPK/humus riches en bas → corrélation négative
  à l'altitude), `bruit_propre` = canal de hash décorrélé, `A_champ` = **amplitude
  propre** (pH/structure faibles ; NPK plus fortes), `w` = poids topographique par
  champ. **Amplitudes pH/NPK PETITES** (portes dures `bell`, faim d'azote D41).
- **`om_stable`/`altitude` NON retouchés** (D56 calibré — surgical ; les
  ré-harmoniser dans la catena = dette légère future).
- **`humidite` EXCLUE** de l'init : le ruissellement la creuse déjà depuis
  l'altitude → hétérogénéité redondante.
- **`temperature`/`temperature_sol` EXCLUES** : climatiques, ré-écrites chaque
  tick par la météo → une init hétérogène serait effacée au tick 0.

### 2.3 Déterminisme (philo #3)
- `founder_genes` : canal de hash = `f(seed, stable_str_hash(species), r, c, week,
  x_cm, y_cm, index_gène)`. Le discriminant `week` + position **continue** évite le
  re-clonage de deux plantes de même espèce nées au même plot (compétition
  intra-plot). Zéro RNG live.
- Champs : chaque champ son canal décorrélé (`stable_str_hash(tile_id+"_ph")`, etc.,
  comme `altitude` fait `+"_alt"`).

### 2.4 Flag unifié `heterogene`
Un seul flag (`heterogene`, défaut **False**) sur `init_eco` active **à la fois**
l'ensemencement génétique fondateur (2.1) ET l'hétérogénéité des champs (2.2). Posé
`True` par les sites **monde-réel** : harnais `test_golden`, `main.py`,
`sim_server` (pont), bancs d'observation. Les **tests unitaires ciblés** qui forcent
un champ plot-à-plot (test_eau, mycelium, substrat, stress_chronique…) gardent le
défaut False → **INTACTS sans être touchés**. Seul le golden re-fige.

## 3. Division du travail « rythme » (cadrage E)
Le rythme **visible** vient surtout de l'**hétérogénéité des CHAMPS** (plasticité
au milieu : un plot chaud lève avant un plot froid). La **génétique** apporte la
part **héritable / sélectionnable**. Les deux se combinent — et ce sprint n'ajoute
pas un acteur isolé : il enrichit le **substrat de tous les acteurs** (floraison
désynchronisée → pollinisateurs nourris en continu ; mosaïque édaphique → faune et
succession variées). Interconnexion maximale.

## 4. Coût perf
Négligeable : tirages à l'**init** (une passe rows×cols par champ) et à la
**naissance** (événement rare). Aucune boucle par tick, aucun O(N²).

## 5. Découpage (3 tronçons, golden re-figé 2× maîtrisé)
- **① Génétique fondatrice** — banque ensemencée + `founder_genes` + semis directs
  + graine `planter`. Golden re-figé **GENES** (annoncé).
- **② Champs — catena topographique** — `init_eco` réordonné + primitive
  généralisée + flag `heterogene`. Golden re-figé **ECO** (annoncé).
- **③ Vue Godot** — banc F5 (rythmes désynchronisés + heatmaps catena + survol
  gènes) + re-passage `diag_population`. Golden intact.

## 6. Garde-fous (D)
- Amplitudes pH/NPK **petites** (calibrage F5) — sinon plots hors-fenêtre (mortalité,
  dérive qualitative).
- **Re-passer `diag_population`** au ③ : le sprint « équilibre invasion » a calibré
  des plateaux ; la variance génétique + édaphique peut re-déséquilibrer.
