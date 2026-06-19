# 2026-06-19 — Sprint CATALOGUE ENRICHI · tronçon ④a : scaffolding « catégorie » (filet du modèle B) — golden NEUTRE — ④a CLOS

## Contexte

Tournant du tronçon ④. Le modèle **A « parfum »** (animaux = variantes de sprite
d'une guilde, triade mutualisée) a été **abandonné** : Nico a tranché le **modèle
B** (chaque animal a SA triade nourriture/prédateur/habitat ; les guildes
deviennent des **catégories**, les espèces remplacent les champs). Conception
figée : `docs/conception/CONCEPTION_FAUNE_DEDIEE.md`. Le sprint ④ a été re-découpé
en **④a→④e** (kickoffs `sprints/sprint_catalogue_enrichi/04a_*…04e_*`).

④a est le **filet** : on introduit la notion de catégorie et l'agrégation, et on
recâble les consommateurs dessus **sans scinder aucun champ encore**. Tant qu'une
catégorie n'a qu'un membre, l'agrégat == le champ unique → **golden NEUTRE**.
C'est l'invariant de contrôle qui rendra les scissions ④b/c/d sûres et lisibles.

## Pourquoi ce filet d'abord (le risque qu'il neutralise)

Audit préalable : **6 consommateurs lisaient `populations["ravageur" |
"auxiliaire" | "vers_de_terre"]` en dur**, dont la **santé des plantes**. Scinder
les champs sans filet aurait tout cassé d'un coup et fait sauter le golden de façon
opaque. Le filet permet de migrer **une catégorie à la fois** ensuite.

## Ce qui est fait

- **`TrophicSpec.category: str`** (champ requis, `fields/population.py`). Tag des 3
  specs trophiques : `ravageur`→`"ravageur"`, `auxiliaire`→`"auxiliaire"`,
  `vers_de_terre`→`"detritivore"` (le **`name`** du champ reste `vers_de_terre`
  jusqu'à la scission ④d ; seule la **catégorie** est déjà renommée). Les
  pollinisateurs (construits aussi en `TrophicSpec` via `build_pollinator_specs`)
  reçoivent `category="pollinisateur"` — catégorie **isolée**, lue par aucun
  agrégat trophique.
- **`EcoFields.category_fields(category)`** (liste des champs membres) +
  **`category_density(category, r, c)`** (somme des densités), dans
  `fields/ecofields/container.py`. La guilde devient une **VUE** calculée, plus un
  champ stocké. Les pollinisateurs (catégorie distincte) en sont naturellement
  exclus des agrégats `ravageur`/`auxiliaire`/`detritivore`.
- **6 consommateurs recâblés** :
  - C1 `sim/effects/perturbations.py` pression herbivore (SANTÉ) `ravageur` →
    `category_density("ravageur")`.
  - C2 `perturbations.py` bascule létale `auxiliaire` → `category_density("auxiliaire")`.
  - C3/C4/C5 `sim/vigueur_macro.py` : nouvel helper **`_vigueur_categorie`** qui
    **itère `category_fields` et somme `_vigueur_pop` (densité × Qi trophique)**,
    borné [0,1]. ⚠️ Subtilité : un simple `category_density` (somme de densités)
    aurait **perdu** le facteur `activite()` (Qi trophique) → PAS neutre. D'où
    l'itération sur les champs plutôt qu'un scalaire de densité.
  - C6 `decomp_speed` (`container.py`) et C8 `gestes.py:420` **inchangés** : le
    champ s'appelle encore `vers_de_terre` (deviendra `lombric` en ④d).

## Golden

**NEUTRE** — `5fddfe54…` inchangé (smoke), pop-golden `5e6e688f…` inchangé,
vigueur-trajectoire `e63b9d7f…` inchangé. Preuve : à un seul membre par catégorie,
`category_density(cat) == populations[cat]` et `_vigueur_categorie(cat) ==
_vigueur_pop(champ)` plot par plot. Si le hash avait bougé en ④a, c'eût été un
**bug d'agrégation**, pas un re-figeage.

## Validation

- `tests/test_golden` PASS (hash inchangé) ; `test_population`, `test_attraction`,
  `test_auxiliaires`, `test_vigueur` (135/135), `test_lifecycle`, `test_structures`
  (65/65), `test_alarme` (16/16) PASS ; balayage `test_*` vert **sauf
  `test_senescence` et `test_sim_server`** (voir signalement) ; le reste de
  `test_sim_server` est vert (183/184).
- Filet C# `dotnet build Symbiose.csproj` : **0 avertissement, 0 erreur**.

## Signalement (carte blanche)

**`test_senescence` ET `test_sim_server` ÉCHOUENT — mais PRÉ-EXISTANTS, pas des
régressions de ④a, et de MÊME cause racine.**
- `test_senescence` : « mort inattendue : autre (âge 2.7 ans) ».
- `test_sim_server` : 1 check sur 184 rouge — « le pommier pré-âgé a noué des
  fruits réels (fin de floraison) — 0 fruits @ S52 ».

Cause racine commune : le **pommier pré-âgé meurt (âge 2.7 ans) avant de
fructifier** → la suite sénescence voit une mort inattendue, et la suite pont ne
voit aucun fruit à S52. Vérifié par `git stash` : **les deux échouent à
l'identique sur la base commitée `315e058`** (avant ④a). Le golden, le pop-golden
et la vigueur-trajectoire sont inchangés → ④a est bien neutre. Défaillance
antérieure (probablement une dérive de longévité d'une espèce d'un sprint plantes
②/③) → à investiguer dans un correctif dédié, hors périmètre du scaffolding faune.

## Reste / prochain (choix Nico, pas d'enchaînement auto)

④b (scinder `ravageur` → puceron/limace/doryphore, **re-figé maîtrisé #1** ;
`_litter_grid` + `_limace_food_grid` litière-dominante car limace = détritivore
préférentielle) ou ⑤ (pollinisateurs B, indépendant).
