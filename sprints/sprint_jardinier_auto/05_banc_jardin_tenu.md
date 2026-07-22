# ⑤ Banc « jardin tenu » + rapport d'impasses agrégé

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` +
> `docs/joueur/automate/conception_jardinier_automate.md` (§11, §7). Prérequis : ①→④ faits.

## Objectif
Le **livrable de mesure** du sprint : un banc qui fait tourner le MÊME monde en deux
régimes — **jardin TENU** (avec l'automate) vs **jardin ABANDONNÉ** (sans) — et
compare démographie, couverture du sol, et surtout **coût perf `LightField`**
(l'hypothèse Q9 : un jardin tenu porte plus de biomasse → plus d'ombre → LightField
plus cher). Plus un **rapport d'impasses agrégé** (les « trous de gameplay »).

## Fichiers à CRÉER
- `tools/bancs/jardin_tenu.py` — monte deux copies déterministes du même monde (même
  seed, même carte), en joue une avec `JardinierAutomate` et l'autre sans, sur N
  années, et imprime un tableau comparatif. Réutiliser le patron des bancs existants
  (`tools/bancs/`, ex. `diag_population.py` / `profile_monde.py` — s'en inspirer pour
  la mise en place du monde et l'instrumentation perf).
- `tools/jardinier_auto/rapport.py` (CRÉER) — `rapport_impasses(gs) -> str` :
  agrège `automate_journal` (entrées `impasse`) par type/facteur et produit un
  résumé lisible (« excès d'eau : 12 impasses geste_inexistant sur T3 »).

## Métriques à comparer (tenu vs abandonné)
- **Démographie** : N plantes vivantes, N cultivées vs férales, par tuile, dans le
  temps. (Contre-test D69 : le paillage de l'automate infléchit-il l'invasion ?)
- **Couverture du sol** : moyenne du champ `paillage`/couverture.
- **Perf `LightField`** : temps passé dans `tick_light` (ou ms/tick global +
  décomposition). Réutiliser l'instrumentation perf des bancs existants si présente ;
  sinon `time.perf_counter` autour de `tick_semaine`. **C'est la mesure clé (Q9)** :
  le régime tenu coûte-t-il plus cher ? De combien ?

## Sortie attendue (rapport)
Un tableau texte clair : pour chaque métrique, valeur tenu vs abandonné + écart. Un
verdict sur Q9 (perf). Le **rapport d'impasses** listant les trous de gameplay
rencontrés. Ce banc est un OUTIL, pas un test golden.

## Golden attendu
**INCHANGÉ.** Le banc est un nouvel appelant ; il n'entre pas dans `test_golden`.

## Ce qu'il NE faut PAS faire
- NE PAS toucher le moteur pour « aider » la mesure. NE PAS re-calibrer D67/D71 ici
  — si la perf du régime tenu explose, **le CONSIGNER** (rapport + `00_etat.md` +
  note pour DETTE), c'est un résultat, pas un chantier de ce tronçon.
- NE PAS lancer `test_epaisseur_500ans`. Choisir un N d'années raisonnable (perf).
- NE PAS dépasser 300 LDC/fichier.

## Vérif de sortie
`python3 -m bancs.jardin_tenu` tourne et imprime le comparatif + le rapport
d'impasses. Golden intact. Consigner dans `00_etat.md` le verdict perf Q9 (tenu
plus cher ? de combien ?) — c'est peut-être le résultat le plus important du sprint.
