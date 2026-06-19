# 2026-06-19 — Sprint CATALOGUE ENRICHI · tronçon ④b : scinder `ravageur` → puceron / limace / doryphore — golden re-figé MAÎTRISÉ #1 — ④b CLOS

## Contexte

Première **scission** du modèle B, posée sur le filet de ④a. La catégorie
`ravageur` (un champ unique) devient **3 champs NOMMÉS** partageant
`category="ravageur"`, chacun avec SA triade propre (nourriture / prédateur /
habitat). La pression herbivore subie par les plantes (C1) et la ressource de
l'auxiliaire (C11) lisent désormais `category_density("ravageur")` = somme des 3.
C'est le **premier re-figeage attribuable** du sprint (le filet ④a garantissait
qu'il serait localisé et lisible). Conception figée : `CONCEPTION_FAUNE_DEDIEE.md`.

## Ce qui est fait (`fields/population.py`)

- **puceron** — reprend l'**ex-triade ravageur intégrale** (feuillage + chaleur),
  fenêtre estivale `daylen 10/13` ; prédateurs nommés `(coccinelle, chrysope,
  syrphe_larve)`.
- **limace** — **détritivore préférentielle** : `_limace_food_grid` =
  litière DOMINANTE (`LIMACE_LITTER_W=1.0`, via `_litter_grid` hors fruit) +
  feuillage tendre secondaire (`LIMACE_FOLIAGE_W=0.3`) ; habitat humide/frais
  (`_humide_litiere_grid`) ; fenêtre **précoce/large `9/12`** (humide-frais) ;
  signal fruit-pourri (`signal_fn=_rav_fruit_signal`) ; prédateurs `(carabe,
  herisson)`.
- **doryphore** — **spécialiste Solanaceae** : ressource (`_foliage_solanaceae_grid`)
  et habitat (`_solanaceae_grid`) **NULS sans Solanaceae**, habitat **réduit par
  l'ail** (`DORY_AIL_REPULSE`, Amaryllidaceae répulsif §4.4) ; fenêtre estivale
  `10/13` ; prédateur `(carabe,)`.
- `_ravageur_grid` (ressource auxiliaire C11) renvoie désormais
  `category_density("ravageur")` — la guilde est une **VUE**, plus un champ.

## Régression transitoire ASSUMÉE (④b → ④c) — décision Nico

Les prédateurs nommés ci-dessus **n'existent pas encore** (ils naissent à la
scission ④c de l'auxiliaire). `_predator_field` rend donc `None` →
terme de prédation 0 → **ravageurs non régulés** → pression herbivore accrue sur
les plantes. Nico a tranché « **noms dès ④b** » (vs garder `auxiliaire`/
`syrphe_larve` comme prédateurs provisoires) : on accepte cette régression
temporaire de l'écosystème, **cause majeure du re-figeage**, attendue et résorbée
en ④c. C'est un choix de lisibilité (la triade finale est posée d'emblée).

## Golden — re-figeage MAÎTRISÉ #1

| hash | avant (④a) | après (④b) |
|------|-----------|-----------|
| smoke `golden_hash` | `5fddfe54…` | **`63d50eeb22…`** |
| `population_hash` | `5e6e688f…` | **`1f7dcda831…`** |
| `vigueur_hash` | `e63b9d7f…` | **`e63b9d7f…` INCHANGÉ** |

La trajectoire de Vigueur joueur **ne bouge pas** : elle ne dépend ni de la
régulation des ravageurs ni de la santé fine des plantes sur l'horizon du smoke.
Les deux autres hash bougent par (1) l'apport limace/doryphore à l'agrégat et
(2) la perte de prédation. **Attribuable**, donc maîtrisé.

## Recâblages hors moteur

- `tools/simserver/actions.py:ecraser` — défaut du sprite cliqué `ravageur` →
  `puceron` (le champ `ravageur` n'existe plus ; réacheminement par `target.espece`
  reste **dette ⑥**, C9/C10).
- ~10 suites de tests adaptées : clé `populations["ravageur"]` → `"puceron"` (qui
  alimente l'agrégat) ou lecture directe `category_density("ravageur")` quand le
  test vérifie la guilde-vue (`test_population`, `test_attraction`, `test_lifecycle`,
  `test_alarme`, `vigueur/*`, `simserver/*`).

## Validation

- **Test neuf** `tests/test_faune_dediee.py` — 6 fonctions, **23 checks** : 3 espèces
  distinctes même catégorie + triades propres ; `category_density == somme` ;
  fenêtres par espèce ; doryphore nul sans Solanaceae / réduit par l'ail ; limace
  litière-dominante.
- `test_golden` PASS contre les **nouvelles références** ; `test_population`
  (TOUS), `test_fruits` (24/24), `test_ruche` (20/20), `test_vigueur` (135/135),
  balayage `test_*` vert **sauf les deux échecs pré-existants** ci-dessous.
- Filet C# `dotnet build Symbiose.csproj` : **exit 0**.

## Signalements (carte blanche)

1. **`fields/population.py` = 449 LDC pur** (873 total dont 310 commentaires) >
   garde-fou ~350 — déjà ~369 avant ④b, +80 par les 3 triades. À **éclater en
   paquet `fields/population/`** dans un sprint refactor dédié (pas dans un tronçon
   catalogue). À arbitrer avec Nico.
2. **Deux échecs PRÉ-EXISTANTS, hors périmètre** (prouvés sur HEAD propre via
   `git stash` — PAS des régressions ④b) : `test_senescence` (plante « meurt
   asphyxié, excès d'eau soutenu » à ~2.7 ans sur terre/hum1.5 — modèle eau) ;
   `test_sim_server` pommier nouaison (0 fruit @ S52). La chaîne pollinisation reste
   gardée au niveau unitaire (test_fruits/test_ruche verts) → l'échec intégration
   n'ouvre pas de trou de couverture. À traiter dans un correctif dédié.

## Reste / prochain (choix Nico, pas d'enchaînement auto)

④c (scinder `auxiliaire` → coccinelle/chrysope/carabe/merle/hérisson — **résorbe la
régression de prédation**, re-figé #2) ou ⑤ (pollinisateurs B, indépendant).
`/clear` entre tronçons.
