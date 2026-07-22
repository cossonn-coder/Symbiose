# CONCEPTION — Modèle spatial des plantes (placement sous-plot + identité clonale)

> Figé le 2026-07-14 après `/conception`. Sujet ouvert par Nico :
> « les plots sont trop restrictifs / plusieurs plantes au même endroit
> impossible / les clones ne ressemblent pas aux clonées ».
> Sprint : `sprints/rendu/spatial/sprint_modele_spatial/` (3 tronçons). Prêt pour `/sprint-auto`.

## 0. Diagnostic — ce que le moteur fait DÉJÀ (ne pas réinventer)

La plainte de Nico portait sur ce qu'il **observe**, alors que le moteur écolo
satisfait déjà l'essentiel. Vérifié dans `data/code` le 2026-07-14 :

- **Position continue** : `PlantInstance.x_cm/y_cm` (`plants/base/instance.py:44`)
  — la plante n'est PAS clouée au plot. Le plot 50 cm n'est qu'une **maille de
  chimie du sol**.
- **Empreinte variable par espèce** : `foliar_plots`/`root_plots`
  (`instance.py:292-309`) dérivent des rayons canopée/racine, tabulés par stade
  ou dérivés de la structure procédurale. Un arbre couvre plus de plots qu'une
  herbe.
- **Chimie VÉCUE déjà variable par espèce** : `vigueur_plante`/`plant_uptake`
  lisent la chimie sur **tout `root_plots`** (`vigueur_plante.py:71` :
  `plots = plant.root_plots or [plant.plot_foyer]`) — pas seulement le plot-foyer.
  → la demande « chimie 50 cm mais variable par espèce » est **déjà remplie**.
- **Cohabitation déjà permise** : verrou d'occupation LEVÉ
  (`sim/succession.py:132`), mort-par-conflit DÉSACTIVÉE (`sim/engine/mortalite.py:247`).
  Deux plantes lèvent au même plot ; la compétition émerge des champs réels
  (lumière, densité racinaire) via `niche_index`, escompté par la tolérance à
  l'ombre → une plante d'ombre lève **sous** une canopée.
- **Pont vers Godot déjà complet** : `tools/simserver/serialize.py:101-105`
  sérialise par plante `x_cm,y_cm` + `segments` (structure). Le rendu place par
  `WorldView.WorldToScreen`. → tout changement de position/silhouette remonte
  **automatiquement** en F5.

Restaient donc **deux vrais manques**, tous deux à coût perf négligeable.

## 1. Manque A — placement au centre du plot systématique

**Constat.** Toute plante GERMÉE (férale ou plantée) naît au **centre du plot** :
`succession.py:207` et `:425` appellent `tile.add_plant(cls, r, c)` sans position,
et `PlantInstance.__post_init__` (`instance.py:158-162`) centre `x_cm,y_cm` au
milieu du plot. Seuls les **clones** posent déjà une position continue
(`sim/clonal.py:151`). Conséquences perçues par Nico :
- toutes les plantes d'une tuile alignées sur une grille visible ;
- deux plantes au même plot = **même point exact** = superposition en F5.

**Décision (Nico 2026-07-14).** Distinguer deux cas :

- **Plantée par le joueur → PIXEL CLIQUÉ EXACT.** Le pont dispose déjà du pixel
  (`{x_cm,y_cm}`, `tools/simserver/actions_cibles.py:42`) mais le rabat en
  `(r,c)` via `_plot_at` **avant** d'appeler `planter(...,r,c)` → le pixel est
  **perdu**. On le fait voyager jusqu'à la levée : le grain porte `x_cm,y_cm`,
  la plante naît **pile là**. `plot_foyer` = plot du pixel (chimie cohérente).
- **Férale (succession spontanée)** → pas de clic, donc **offset déterministe**
  hashé dans le plot, borné pour que `plot_foyer` reste le plot cible.

**Modèle de l'offset féral** (philo #3, zéro RNG) :
```
u1 = _hash_noise(seed, week * 53, r, c)      # canaux dédiés, décorrélés du reste
u2 = _hash_noise(seed, week * 59, r, c)
x_cm = c * PLOT_CM + OFFSET_MIN + u1 * (PLOT_CM - 2*OFFSET_MIN)
y_cm = r * PLOT_CM + OFFSET_MIN + u2 * (PLOT_CM - 2*OFFSET_MIN)
# OFFSET_MIN = 10 cm  → offset ∈ [10, 40] cm dans un plot de 50 cm
```
La marge `OFFSET_MIN` garantit `floor(x_cm/50) == c` et `floor(y_cm/50) == r`
→ **plot-foyer inchangé** → la chimie du sol lue reste stable (seule change,
légèrement, la découpe des plots que la racine chevauche : c'est précisément
l'effet « position → chimie » voulu).

**Golden.** Le cas FÉRAL **re-fige** le golden (les positions férales du smoke
dérivent → lumière/empreintes → toute la trajectoire). Cause unique et localisée,
annoncée. Le cas PLANTÉ est event-driven (le smoke ne plante jamais) → **neutre**.

## 2. Manque D — les clones ne partagent pas la silhouette de la mère

**Constat.** Le clone COPIE le vecteur de gènes + l'expression plastique
(`clonal.py:148-149`). Mais la morphogénèse (débourrement des branches) est
amorcée par la **position du segment** : `sim/growth/phases.py:95` fait
`_hash_noise(seed, week, bx+i, by)` avec `bx,by = base du segment` (dérivée de
`x_cm,y_cm`). Deux clones à des positions différentes tirent donc des angles de
branches **décorrélés** → aucun air de famille. De plus le ramet naît **bébé**
(stade 0, un segment) à côté d'une mère mature.

**Décision (Nico 2026-07-14).** Introduire une **identité morphologique
héritable** `form_seed`, et **refuser le coup de pouce d'établissement** : le
ramet reste **juvénile** et **grandit dans** la silhouette de la mère (philo #2
pure — pas de bonus de naissance). La ressemblance vient du patron partagé, la
divergence fine vient de la lumière/phototropisme local vécu.

**Modèle.**
- Champ `form_seed: int` sur `PlantInstance` (défaut `0` = « non posé »).
- **Posé une fois à la naissance**, aux mêmes sites que les gènes (les deux
  levées de `succession.py` + `planter`) : `form_seed = _form_seed(seed, x_cm,
  y_cm, week)` (hash entier stable).
- **Le clone hérite** : `sim/clonal.py` fait `ramet.form_seed = mother.form_seed`
  (comme il copie déjà `genes`/`expression`).
- La morphogénèse lit l'identité au lieu de la position. Dans `_debourrement`
  (`phases.py`), remplacer les coordonnées de segment par le seed d'identité,
  en gardant l'indice de segment `i` pour la variation intra-plante :
  ```
  fs = plant.form_seed or _hash_int(plant.x_cm, plant.y_cm)   # repli robuste
  phi = _hash_noise(fs, week, i, 0) * 2π
  jit = (_hash_noise(fs, week, i, 1) - 0.5) * JITTER_RAD
  ```
  → deux clones (même `form_seed`) tirent la **même séquence** d'angles ; deux
  plantes non apparentées gardent des `form_seed` distincts → silhouettes
  distinctes (comportement de diversité préservé).

**Golden.** Change les entrées du hash de débourrement pour **toutes** les
plantes → silhouettes reseed → **re-fige** le golden. Cause unique, annoncée.

## 3. Découpage (3 tronçons, perf-first, se termine par la vue Godot)

1. **① Placement sous-plot** (§1) — golden **re-figé** (cas féral). Fonde
   l'unicité spatiale des positions (utile au form_seed du ②).
2. **② Identité morphologique `form_seed`** (§2) — golden **re-figé** (silhouettes).
3. **③ Banc d'observation + vue Godot** — le pont porte déjà tout ; tronçon =
   banc déterministe (une mère + ses ramets qui lui ressemblent + deux plantes
   qui se chevauchent sans se superposer) + checklist F5 pour Nico. Aucun
   changement moteur → golden **intact**.

## 4. Coût perf

Négligeable : deux appels `_hash_noise` de plus par **naissance** (événement
rare, pas par tick), et un swap d'entrées de hash dans `_debourrement` (déjà
appelé). Aucune boucle nouvelle, aucun champ nouveau. Budget très en deçà du
+10 %/tronçon.

## 5. Ce que ce sprint NE fait PAS

- Pas de stratification verticale explicite (rejeté par Nico ; couvert par
  `sprint_luxuriance_stratification` D65, complémentaire).
- Pas de sous-maillage de la chimie du sol (rejeté : déjà variable par espèce
  via `root_plots`).
- Pas de coup de pouce d'établissement clonal (ramet reste juvénile).
