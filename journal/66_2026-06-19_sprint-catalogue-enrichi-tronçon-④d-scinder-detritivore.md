# 2026-06-19 — Sprint CATALOGUE ENRICHI · tronçon ④d : scinder `detritivore` → lombric / cloporte — golden re-figé MAÎTRISÉ #3 — ④d CLOS

## Contexte

Troisième et dernière **scission** du modèle B. La catégorie `detritivore` (un
champ unique `vers_de_terre`) devient **2 champs NOMMÉS** partageant
`category="detritivore"`, chacun avec SA triade propre. Ce tronçon **referme les
dernières boucles** : le lombric devient une vraie proie (merle/hérisson), le
cloporte naît avec ses prédateurs (carabe/hérisson) et hérite du signal
fruit-pourri. Conception figée : `CONCEPTION_FAUNE_DEDIEE.md`.

## Ce qui est fait (`fields/population.py`)

Bloc détritivore placé en **position PROIE** (après les ravageurs, avant les
auxiliaires) → les prédateurs nommés le lisent **frais** (cohérence de la chaîne
ravageur→auxiliaire ; convention « toutes les proies avant tous les prédateurs »).

- **lombric** — **héritier** du champ `vers_de_terre` (salt identique →
  continuité des sprites) : brasse l'**humus du sol** (ressource `_soil_food_grid`,
  habitat `_undisturbed_grid` sol non perturbé), proie de `(merle, herisson)`,
  fenêtre LARGE `8.5/10` (actif quasi toute l'année). **Pilote `decomp_speed`.**
- **cloporte** — détritivore de **litière + fruit pourri** : ressource
  `_litter_grid`, habitat `_humide_litiere_grid` (humide/frais), proie de
  `(carabe, herisson)`, `signal_fn=_rav_fruit_signal` (le fruit pourri le fait
  monter), fenêtre `9/12`.

`signal_fn=_rav_fruit_signal` est **retiré de la limace** : le fruit pourri passe
désormais au cloporte (défaut « cloporte seul » du kickoff §C13), la limace n'en
garde aucune part.

## Recâblages moteur — le ver nommé remplace l'agrégat

- `_merle_food_grid` : bascule de `category_density("detritivore")` vers
  `_espece_grid("lombric")` (nouveau module-level `_lombric_grid`). **Le merle
  mange le ver, pas le cloporte** (note posée en ④c honorée).
- `ecofields/container.py` : `decomp_speed` (C6) **et** `tick_decomposition`
  lisent `populations["lombric"]` (était `["vers_de_terre"]`). Le cloporte traite
  la litière, pas l'humus du sol → **dette si on veut le rendre littéral** (doc §5.3).
- `sim/actions/gestes.py` : `becher` (C8) retire de la densité `populations["lombric"]`.
- `ecofields/constants.py` : commentaire D31.2 `vers_de_terre`→`lombric`.
- `sim/vigueur_macro.py` (C5) **inchangé** : déjà `_vigueur_categorie("detritivore")`
  (somme lombric + cloporte automatiquement) depuis ④a.

## Golden — re-figeage MAÎTRISÉ #3

| hash | avant (④c) | après (④d) |
|------|-----------|-----------|
| smoke `golden_hash` | `533276328199…` | **`9be1c05a7282…`** |
| `population_hash` | `e707002f435b…` | **`58ecf6d89e21…`** |
| `vigueur_hash` | `e63b9d7f…` | **`e63b9d7f…` INCHANGÉ** |

Causes du re-figeage, **toutes intentionnelles ④d** : ordre de tick (détritivores
en position proie) ; prédation du lombric désormais ACTIVE (merle/hérisson, était
0 sous l'agrégat) ; cloporte neuf ; limace perd le signal pourri ; `decomp_speed`
sur le lombric seul. La trajectoire de Vigueur joueur **ne bouge pas**
(indépendante de la régulation faune). **Attribuable**, donc maîtrisé.

## Recâblages hors moteur

Clé `populations["vers_de_terre"]` → `["lombric"]` / `["cloporte"]` ; listes
d'espèces 12 → 13 (`test_population`, `simserver/fields`, `simserver/macro`,
`vigueur/macro`). Deux tests intégrés de `test_attraction` renommés
ravageur→**détritivore** (le fruit pourri monte le cloporte, plus la limace).

## Validation

- **Test enrichi** `tests/test_faune_dediee.py` — merle vise le lombric (pas le
  cloporte) ; +2 fonctions : `test_deux_detritivores_nommes` (existence, catégorie,
  prédateurs, ressource litière du cloporte, signal déplacé) +
  `test_decomp_speed_suit_le_lombric` (cloporte insensible, lombric accélère).
- `test_golden` PASS contre les **nouvelles références** ; `test_population` (TOUS),
  `test_attraction` (TOUS), `test_faune_dediee` (TOUS), `test_structures` (65/65),
  `test_fruits` (24/24), `test_ruche` (20/20), `test_vigueur` (135/135).
- Filet C# `dotnet build Symbiose.csproj` : **exit 0** (④d est Python pur).

## Signalements (carte blanche)

1. **`fields/population.py` toujours > garde-fou ~350 LDC** → à **éclater en paquet
   `fields/population/`** dans un sprint refactor dédié (hors tronçon catalogue).
   À arbitrer avec Nico.
2. **Mêmes deux échecs PRÉ-EXISTANTS, hors périmètre** (re-prouvés sur HEAD ④c via
   `git stash` — PAS des régressions ④d) : `test_senescence` (~2.7 ans) ;
   `test_sim_server` pommier nouaison (0 fruit @ S52, suite 183/184).
3. **Dette détritivore littérale** : `decomp_speed` ne lit que le lombric (humus) ;
   le cloporte (litière) ne contribue pas encore à la décomposition. Choix assumé
   du kickoff §5.3 — à rendre littéral plus tard si on veut coupler les deux.

## Reste / prochain (choix Nico, pas d'enchaînement auto)

④e = encyclopédie (blurb/interconnexions) + tests + stub pont (golden NEUTRE),
ou ⑤ (pollinisateurs B, indépendant). `/clear` entre tronçons.
