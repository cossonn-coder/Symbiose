# Tronçon ④c — SCINDER la catégorie `auxiliaire` (coccinelle / chrysope / carabe / merle / hérisson)

> Sprint CATALOGUE ENRICHI. État partagé : `00_etat.md` (lire d'abord).
> Doc FIGÉ : `docs/conception/CONCEPTION_FAUNE_DEDIEE.md` (§2 auxiliaire, §3 graphe, §4).
> **Pré-requis : ④b CLOS** (ravageur scindé en puceron/limace/doryphore).
> Kickoff autosuffisant. Python depuis `data/code/`. Filet `dotnet build`.

## Objectif

Remplacer le champ unique `auxiliaire` par **5 champs d'espèce** (catégorie
`"auxiliaire"`), chacun mangeant une **proie nommée précise** → les boucles
proie↔prédateur deviennent réelles (puceron↔coccinelle/chrysope ; limace↔carabe/
hérisson). C'est ici que les `predators` posés en ④b **s'activent**.

| Espèce | Nourriture (resource_fn) | Habitat (habitat_fn) | Fenêtre |
|---|---|---|---|
| **coccinelle** | `_espece_grid("puceron")` *(scindé de `_ravageur_grid`)* | `_stability_grid` *(existe, nectar+stabilité)* | estivale |
| **chrysope** | `_espece_grid("puceron")` | `_auxiliaire_habitat_grid` *(existe, rondelle)* | estivale |
| **carabe** | `_espece_grid("limace")` (+ larves sol) | `_undisturbed_structure_grid` *(neuf : sol non perturbé + piles ⑤)* | nocturne→large |
| **merle** | **fruit frais** (`_aux_fruit_signal` repromu en resource) + `_espece_grid("lombric")`* | `_base_habitat_grid` *(neuf : plancher + structures hautes)* | toute saison |
| **hérisson** | `_espece_grid("limace")` | `_pile_grid` *(neuf : structures pile ⑤)* | nocturne→large |

> *Le merle mange aussi le lombric, **scindé seulement en ④d**. En ④c, `lombric`
> n'existe pas encore → `_espece_grid("lombric")` renvoie 0 (ou lire la catégorie
> `detritivore` encore mono-champ `vers_de_terre`). Défaut : lire
> `category_density("detritivore")` pour le merle/hérisson tant que ④d n'a pas
> scindé → bascule vers `lombric` en ④d. Le noter.

## Périmètre EXACT

**Helper neuf** `_espece_grid(name)` (`population.py`) : grille = lecture du champ
`eco.populations[name]` (généralise `_ravageur_grid`). Si `name` absent → grille 0
(robuste aux ordres de scission).

**Specs** : retirer `auxiliaire`, ajouter les 5 (`category="auxiliaire"`), salts
dédiés neufs. **Activer les prédateurs nommés** posés en ④b : puceron mangé par
coccinelle/chrysope ; limace par carabe/hérisson. (Le résolveur `_predator_field`
les trouve maintenant qu'ils existent.)

**Habitats neufs** (`population.py`) :
- `_undisturbed_structure_grid` : `_undisturbed_grid` + bump des structures `pile`
  (lecture `eco.structures`, duck-typé comme `_abeille_habitat_grid` lit les ruches).
- `_pile_grid` : terme-source d'habitat = présence de structures `kind=="pile"`.
- `_base_habitat_grid` : plancher constant léger + structures hautes (placeholder).

**Recâblage** :
- C11 `_ravageur_grid` (ancien, agrégé) → SUPPRIMÉ ; remplacé par `_espece_grid`
  ciblé par prédateur. Vérifier qu'aucun appelant résiduel ne le référence.
- C13 signal fruit **frais** `_aux_fruit_signal` → porté par **merle** (resource ou
  signal_fn). Le fruit **pourri** reste à reposer en ④d (cloporte).

## Validation

1. `python3 -m tests.test_golden` → re-figé MAÎTRISÉ #2. Nouveau hash → `00_etat.md`
   + journal, dérive expliquée (régulation par espèce : la coccinelle ne suit QUE le
   puceron, etc. → boucles décalées distinctes).
2. `tests/test_faune_dediee.py` enrichi : 5 auxiliaires, proies correctes
   (coccinelle nulle sans puceron ; hérisson nul sans limace), habitats structures
   (pile → carabe/hérisson montent).
3. `test_population`/`test_attraction`/`tests/vigueur/*` adaptés (plus de champ
   `auxiliaire` ; utiliser `category_density("auxiliaire")`).
4. Filet `dotnet build`.

## À faire en fin de tronçon

- `00_etat.md` (④c ✅ : auxiliaire scindé en 5, **nouveau hash**, boucles
  proie↔prédateur actives, merle/hérisson lisent encore `detritivore` agrégé).
- Entrée `journal/` + index.
- Commit : `feat(catalogue) : faune ④c — auxiliaire scindé (coccinelle/chrysope/carabe/merle/hérisson), boucles proie↔prédateur, golden re-figé`.
- Proposer ④d (scinder détritivore) — pas d'auto-enchaînement.
