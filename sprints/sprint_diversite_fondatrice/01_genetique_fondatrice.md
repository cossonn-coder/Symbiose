# Tronçon ① — Génétique fondatrice

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + ce fichier. Ne lis le
> reste que si besoin. Doc complet : `docs/conception/CONCEPTION_DIVERSITE_FONDATRICE.md`.

## Objectif
Que chaque plante née **sans lignée** ait un patrimoine génétique **propre**
(plus de clones neutres au démarrage), sur deux canaux :
1. **Banque-sol ensemencée** (féral spontané) — distribution fondatrice.
2. **`founder_genes`** — semis directs (démo, graine `planter` sans lignée).

La mutation par génération (`sim/reproduction.py:child_genes`) existe déjà et
prend le relais — NE PAS y toucher.

## Contexte moteur (déjà en place)
- `plants/genetics.py` : `GENE_NAMES` (10 gènes), `GENE_INIT_SIGMA=0.10` (défini,
  JAMAIS utilisé — c'est ce qu'on active), `clamp_gene`, bornes dures [0.4,1.6].
- `fields/seedbank.py` : `GeneStat(mean,var,weight)` (a `.add`, `.decay`, `.sample`),
  couche `SeedBank.species[r][c] = {classe: {"density", "genes":{g:GeneStat}, ...}}`,
  `sample_genes(r,c,cls,seed,week)` → `{}` si `density < SPECIES_POOL_MIN_DENSITY`
  (0.005), sinon tire `mean + gauss·sqrt(var)`. Importe déjà `hash_gauss` (via
  `fields.noise`) et `clamp_gene`.
- `fields/noise.py` : `hash_gauss(seed,week,r,c,k=0)`, `_hash_noise`, `stable_str_hash(text)`.
- `plants/base/instance.py` : `PlantInstance.genes` (dict, vide=neutre), `.x_cm/.y_cm`
  (position continue), `.position` (plot r,c).
- Semis directs : `world/tile.py:add_plant(cls,row,col)` crée l'instance (genes vide).
  Appelé par `main.py` et `tests/test_golden.py` (8 cultivées : Tomato, Basil, Bean,
  Sunflower, Pepper, Yarrow, Phacelia, Clover + AppleTree).
- Graine `planter` : `sim/seeds.py:Seed` (default `neutral_genes()`), levée par
  `sim/succession.py:_lever_grains_en_attente` (gènes propres du grain).
- Monde construit par `fields/ecofields/container.py:init_eco(tile_id, rows, cols,
  humidite, fertilite, microbiome, soil_type)`.
- WEED_CATALOGUE (adventices) : importé depuis `plants` (archétypes de succession).

## Modèle / implémentation

### a) `founder_genes` (nouveau, dans `fields/seedbank.py`)
Fonction pure (couche `fields` = a accès à `hash_gauss`, `GENE_NAMES`,
`GENE_INIT_SIGMA`, `clamp_gene` ; `genetics.py` est fondation pure et ne PEUT PAS
importer `hash_gauss`).
```
def founder_genes(plant_class, seed, week, r, c, x_cm, y_cm) -> dict:
    base = stable_str_hash(plant_class.__name__)
    genes = {}
    for i, g in enumerate(GENE_NAMES):
        # canal décorrélé par espèce + gène + position CONTINUE + semaine
        z = hash_gauss(seed, week*31 + i, r, c, k=base + i*7 + int(x_cm) + int(y_cm)*13)
        genes[g] = clamp_gene(1.0 + z * GENE_INIT_SIGMA)
    return genes
```
> Discriminant `x_cm/y_cm` + `week` = deux plantes de même espèce au même plot
> (compétition intra-plot) ne sont PLUS clones (correctif B). Vérifier la vraie
> signature de `hash_gauss` (arg `k`) et adapter si besoin — l'important : canal
> décorrélé par (espèce, gène, position continue, semaine), déterministe, zéro RNG.

### b) Ensemencement banque-sol fondateur (dans `init_eco`, sous flag `heterogene`)
Nouvelle méthode `SeedBank.seed_founder_pool(r, c, plant_class, sigma, density)` :
pose directement un `GeneStat(mean=1.0, var=sigma², weight=density)` pour CHAQUE
gène de `GENE_NAMES` dans `species[r][c][plant_class]["genes"]` (créer le `rec`
comme `add_species`). `density` un peu au-dessus de `SPECIES_POOL_MIN_DENSITY`
(ex. 0.02) pour que `sample_genes` l'utilise dès le départ.
Dans `init_eco`, SI `heterogene` : pour chaque plot × chaque espèce de
WEED_CATALOGUE, appeler `seed_founder_pool`. Résultat : `sample_genes` (succession
férale) tire avec variance immédiate ; `_germ_gene_mean` reste à 1.0 au départ
(mean=1.0) mais la variance permet à la sélection de dériver.

### c) `founder_genes` sur les semis directs
- `tests/test_golden.py` et `main.py` : après `add_plant`, si le harnais est en
  mode monde (voir flag §d), poser `p.genes = founder_genes(cls, seed, week=0,
  r, c, p.x_cm, p.y_cm)`. Le plus propre : un petit helper `semer_fondateur(tile,
  cls, r, c, seed)` (dans `sim/` ou utilitaire de test) = `add_plant` + founder.
- Graine `planter` : dans `_lever_grains_en_attente`, si `grain.genes` est VIDE
  (graine sans lignée), poser `founder_genes` à la levée (garder les gènes propres
  si présents). (Une Seed de départ magazine = vide → fondatrice ; une graine
  récoltée = gènes hérités → inchangée.)

### d) Flag `heterogene` (introduit ICI, réutilisé au ②)
Ajouter `heterogene: bool = False` à `init_eco`. Sous ce flag → ensemencement (b).
Sites monde-réel qui passent `True` : harnais `test_golden` (→ re-figeage), `main.py`,
`tools/simserver/*` (pont jeu réel — chercher l'appel `init_eco`), `bancs/base.py`.
Défaut False → tests unitaires ciblés INTACTS.

## Golden
**Re-figé LARGE (GENES)**, annoncé. Cause : les germinations férales ET les 8
semis directs de `test_golden` ne sont plus neutres → la ligne `GENES[...]` par
plante change, et les trajectoires (croissance/floraison) dérivent de façon
déterministe. Re-figer `tests/test_golden.py` (nouvelle empreinte) APRÈS avoir
vérifié que la dérive est cohérente (variance présente, pas d'explosion). Consigner
le nouveau hash dans `00_etat.md`.

## Tests
- **Neuf** `tests/test_diversite_fondatrice.py` : (1) déterminisme — même
  (seed, cls, r, c, x_cm, y_cm, week) → mêmes gènes ; (2) diversité — deux positions
  continues ≠ (même plot) → gènes ≠ (correctif B) ; (3) `sample_genes` renvoie non
  vide sur un pool ensemencé.
- **Mettre à jour** les tests ciblés qui supposent des gènes neutres si présents
  (chercher `neutral` / `genes == {}` / `GENES[]` dans `tests/`). NE PAS toucher les
  tests qui passent `heterogene=False` (défaut).

## NE PAS faire
- Ne pas toucher `child_genes` / la mutation (déjà correcte).
- Ne pas hétérogénéiser les champs ici (c'est le ②).
- Ne pas mettre `founder_genes` dans `genetics.py` (couche : pas d'accès `hash_gauss`).
- Ne pas relever `GENE_INIT_SIGMA` (0.10 = valeur retenue).

## Fin de tronçon
Golden re-figé + hash consigné, tests verts, `00_etat.md` mis à jour, commit.
