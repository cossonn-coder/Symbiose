# 2026-06-19 — Sprint CATALOGUE ENRICHI · tronçon ④c : scinder `auxiliaire` → coccinelle / chrysope / carabe / merle / hérisson — golden re-figé MAÎTRISÉ #2 — ④c CLOS

## Contexte

Deuxième **scission** du modèle B. La catégorie `auxiliaire` (un champ unique)
devient **5 champs NOMMÉS** partageant `category="auxiliaire"`, chacun avec SA
triade propre. C'est le tronçon qui **referme les boucles** : les prédateurs
nommés posés en ④b (coccinelle/chrysope sur le puceron, carabe/hérisson sur la
limace) **existent enfin comme champs** → la prédation s'applique → la régression
transitoire ④b est **résorbée**. Conception figée : `CONCEPTION_FAUNE_DEDIEE.md`.

## Ce qui est fait (`fields/population.py`)

Fabrique `_espece_grid(name)` : une ressource = la densité de la proie nommée,
fraîchement mise à jour (les auxiliaires tickent après les ravageurs).

- **coccinelle** — **héritière** du champ `auxiliaire` (salt identique →
  continuité des sprites) ; proie `puceron`, habitat `_stability_grid`, fenêtre
  estivale `10/13`.
- **chrysope** — proie `puceron`, habitat `_auxiliaire_habitat_grid` (rondelle
  attire-auxiliaire), fenêtre `10/13`.
- **carabe** — proie `limace`, habitat `_undisturbed_structure_grid` (sol non
  perturbé **+ bump des structures `pile`/bois mort**), fenêtre précoce `9/12`.
- **merle** — **omnivore** : nourriture `_merle_food_grid` = fruit FRAIS
  (`_aux_fruit_signal` **repromu** de signal additif en RESSOURCE) + agrégat
  `category_density("detritivore")` (vers) ; habitat plancher **uniforme**
  `MERLE_BASE_HABITAT=0.20` (oiseau ubiquiste — c'est sa nourriture qui le
  concentre, pas l'habitat) ; fenêtre large `8.5/10`.
- **hérisson** — proie `limace`, habitat `_pile_grid` (**NUL sans pile posée** →
  dépend ENTIÈREMENT d'un aménagement joueur), fenêtre `9/12`.

`signal_fn=_aux_fruit_signal` est **retiré** de l'auxiliaire (devient la ressource
du merle) ; `_rav_fruit_signal` reste utilisé par la limace.

## Boucles proie↔prédateur ACTIVES (résorption de la régression ④b)

`_predator_field` résout maintenant coccinelle/chrysope/carabe/hérisson (champs
réels) → terme de prédation > 0 → ravageurs **régulés** (avec un lag d'une
semaine, les auxiliaires tickent après leurs proies). L'écosystème se referme.

## Habitats sur STRUCTURES — golden NEUTRE par construction

Carabe et hérisson lisent `eco.structures` en **duck-typing** (comme
`_abeille_habitat_grid` lit les ruches — aucun import de l'apiculture/compost,
pas de cycle de couche) : un bump `PILE_HABITAT_W=0.40` au plot de chaque `pile`.
Le smoke golden **n'instancie aucune structure** → ces termes-sources sont nuls →
cette part du modèle est **golden NEUTRE** (le re-figeage vient des boucles, pas
des habitats structures).

## Réconciliation kickoff ↔ doc figé

Le kickoff `04c` annonçait `_ravageur_grid` → SUPPRIMÉ, mais le doc figé §4 liste
le **pont syrphe inchangé** (il lit `_ravageur_grid`). Le **doc est source de
vérité** : `_ravageur_grid` est **conservé** pour le seul pont syrphe, et retiré
uniquement comme ressource des auxiliaires (désormais `_espece_grid`).

## Golden — re-figeage MAÎTRISÉ #2

| hash | avant (④b) | après (④c) |
|------|-----------|-----------|
| smoke `golden_hash` | `63d50eeb…` | **`533276328199…`** |
| `population_hash` | `1f7dcda831…` | **`e707002f435b…`** |
| `vigueur_hash` | `e63b9d7f…` | **`e63b9d7f…` INCHANGÉ** |

La trajectoire de Vigueur joueur **ne bouge pas** (indépendante de la régulation
des ravageurs). Les deux autres hash bougent par le retour de prédation (boucles
refermées) + l'émergence du merle (qui lit fruit frais + agrégat détritivore).
**Attribuable**, donc maîtrisé.

## Recâblages hors moteur

~7 suites adaptées : clé `populations["auxiliaire"]` → `"coccinelle"` (héritière) ou
lecture `category_density("auxiliaire")` (guilde-vue) ; listes d'espèces 8 → 12
(`test_population`, `test_attraction`, `vigueur/gestes`, `vigueur/macro`,
`simserver/actions`, `simserver/macro`, `simserver/fields`).

## Validation

- **Test enrichi** `tests/test_faune_dediee.py` — +4 fonctions (→ 10 au total) :
  5 auxiliaires même catégorie + triades distinctes ; proies propres (coccinelle/
  chrysope nulles sans puceron, carabe/hérisson nuls sans limace) ; habitats
  `pile` (hérisson NUL sans pile / bump au plot, carabe bumpe) ; merle omnivore.
- `test_golden` PASS contre les **nouvelles références** ; `test_population` (TOUS),
  `test_attraction` (TOUS), `test_vigueur` (135/135), `test_ruche` (20/20),
  `test_fruits`, balayage `test_*` vert **sauf les deux échecs pré-existants**.
- Filet C# `dotnet build Symbiose.csproj` : **exit 0** (④c est Python pur).

## Signalements (carte blanche)

1. **`fields/population.py` toujours > garde-fou ~350 LDC** (encore alourdi par les
   5 triades) → à **éclater en paquet `fields/population/`** dans un sprint refactor
   dédié (pas dans un tronçon catalogue). À arbitrer avec Nico.
2. **Mêmes deux échecs PRÉ-EXISTANTS, hors périmètre** (re-prouvés sur HEAD ④b via
   `git stash` — PAS des régressions ④c) : `test_senescence` (~2.7 ans) ;
   `test_sim_server` pommier nouaison (0 fruit @ S52, suite 183/184). À traiter dans
   un correctif dédié.
3. **Observation** : `test_auxiliaires.py` (diagnostic NON-assertif) montre désormais
   **0 dégât herbivorie sur les DEUX tuiles** (AUX et TÉMOIN) sur 30 ans — conséquence
   attendue des boucles refermées (la coccinelle régule le puceron même sans
   rondelle). Le scénario ne distingue plus AUX/TÉMOIN ; à revisiter si on veut
   re-mesurer l'effet attire-auxiliaire (le levier est désormais l'HABITAT, pas la
   simple présence). Pas un blocage : aucune assertion, script de mesure.

## Reste / prochain (choix Nico, pas d'enchaînement auto)

④d (scinder `detritivore` → lombric/cloporte ; `_merle_food_grid` basculera de
`category_density("detritivore")` vers `_espece_grid("lombric")` — note posée dans
le code ; re-figé #3) ou ⑤ (pollinisateurs B, indépendant). `/clear` entre tronçons.
