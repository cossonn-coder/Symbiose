# Conception — Chronique des espèces (outiller les runs longs, D127)

**Figée le 2026-11-06** (`/conception`, accord Nico). Sprint :
`sprints/perf/run_eternel/sprint_chronique_especes/`. Golden **intact** sur
tout le sprint (`a10b7225…`).

## 1. Le problème

Après un run de 192 ans en turbo sur `verger_mur` (rapport C du 2026-11-06),
Nico : « il faut s'outiller pour ». Le rapport ne montre ni **quand** une espèce
disparaît, ni **de quoi**. Trois causes vérifiées au code :

1. **Fenêtre tronquée** : `tools/simserver/perf_annees.py`, `MAX_ANNEES = 60`.
   Sur 192 ans on ne voit que les 60 dernières années ; « plus que des noyers
   dès l'an 132 » est très probablement le bord de la fenêtre.
2. **Top 3 seulement** : une espèce minoritaire s'éteint sans trace.
3. **Causes de mort mal lues** (bug qui touche aussi le joueur) : la mort ne se
   journalise que dans le `log` texte du tick. `sim/evenements.py` range toute
   ligne `✗` en `cause="conflit"`, alors que la mort par conflit n'existe plus
   (`regress()` retiré, `sim/engine/mortalite.py:254`). Chaque `✗` est un
   `ReduceHealth` résolu (`sim/effects/resolution.py`), au format
   `  ✗ Santé <Nom>@(r, c) -<n> [<reason>] → meurt`. Le préfixe « Santé » n'est
   pas retiré → `espece=None`. Le carnet écrit donc « a cédé la place à plus
   vigoureux » sans nom d'espèce pour une plante mangée. `tests/test_evenements.py`
   teste un format `✗ Tournesol@(8, 8) meurt (conflit)` que le moteur n'émet plus.

## 2. Causes canoniques

Lues dans le `[reason]` déjà présent dans la ligne `✗` (aucun changement du
texte du log : le golden hache le log). Précédent : `tests/diag_morts_field.py`
(`_classify`).

| `reason` (préfixe, insensible à la casse) | cause | concept carnet (à vérifier au code) |
|---|---|---|
| `herbivorie`, `Limaces`, `Chenilles` | `herbivorie` | ravageurs |
| `maladie fongique`, `oïdium`, description d'effet d'espèce (mildiou…) | `maladie` | maladie |
| `fonte des semis` | `maladie` | maladie |
| `gel`, `Gelée tardive` | `gel` | météo |
| `grêle` | `grele` | météo |
| `vent` | `vent` | météo |
| `stress hydrique` | `secheresse` | eau |
| `carence lumineuse` | `ombre` | lumière |
| `mortalité de fond` | `usure` | (aucun concept : pas d'entrée carnet interprétative dédiée, texte descriptif seul) |
| autre | `autre` (raison brute conservée pour la chronique) | aucun |

S'ajoutent les marqueurs déjà lus (`🪦` → `sénescence` / `asphyxie`) et deux
non lus jusqu'ici : `❄ … meurt (annual)` et `✿ … meurt (bisannuelle, an 2)` →
`fin_de_cycle` (concept : le même que la sénescence).
La table des raisons des effets d'espèce (`effect["description"]`) se relève au
code ; toute raison non classée tombe en `autre`, jamais en `conflit`.

Les entrées `("mort", "conflit")` du carnet et de l'aide **restent** (règle :
on ne jette pas de code), mais plus rien ne les produit.

## 3. La chronique

Un instrument **hors tick**, côté serveur (`tools/simserver/`), alimenté après
`tick_semaine()` par le même `log` que le carnet (`evenements(log)`) et par
l'état des tuiles. Golden neutre par construction (le golden tourne hors
serveur).

- **Bilan annuel** (clôture à `semaine % 52 == 0`, comme `perf_annees`) :
  effectifs vivants de **toutes** les espèces végétales, morts de l'année par
  espèce × cause, levées de l'année par espèce (germinations + émissions
  clonales + reproduction lues au flux).
- **Registre des disparitions et retours, non borné** : quand le dernier
  individu vivant d'une espèce meurt → semaine, espèce, cause de cette dernière
  mort, âge, tuile ; quand une espèce disparue réapparaît → semaine.
  Comptage des vivants par espèce à chaque tick : O(N), ≤ ~1 ms [estimation,
  non mesurée] face à un tick de 520-710 ms [verger_mur, PC].
- Les morts **hors tick** (gestes du joueur ou de l'automate) n'apparaissent pas
  dans le `log` du tick : elles sont comptées à part (`hors_tick`), par écart
  entre vivants attendus et vivants constatés — placement laissé à l'exécution.
- **Mémoire** : pas de borne à 60 ans (≈ 40 espèces × 200 ans, petit).
- **Un seul texte** : Python compose la section lisible (tableau tous les
  10 ans + toute année avec une disparition ou un retour, puis le registre en
  entier) ; le rapport C (C#) et l'outil sans écran l'affichent tels quels.

## 4. Outil sans écran (VM)

`tools/` : monte un monde ou un banc par `SimServer.cmd_init` (même fabrique que
le F5), avance N années par le même chemin post-tick que le serveur, écrit la
section et un JSON brut. Lancé en tâche de fond par Claude : 200 ans de
`verger_mur` ≈ 1,7 h [estimation sur le tick médian PC, VM chargée].

## 5. Hypothèse à trancher par le premier run (non mesurée)

`verger_mur` coupe les levées et l'herbivorie ; les fruitiers y sont plantés à
15-16 ans (longévités cerisier 60, pommier 70, figuier 80, noyer 200, déclin dès
0,7 de la longévité) → morts de vieillesse vers l'an 30-65 du run ? Mais les
noyers passent de 2 à 5 : une voie de recrutement existe (dépôt génétique de
`_reproduction`). Le run dira quand et de quoi. **Corriger l'écologie est hors
de ce sprint** (conception à part si la cause n'est pas la vieillesse).

## 6. Hors périmètre

Faune (D119) ; correction écologique des disparitions ; réécriture du texte du
log moteur (re-figerait le golden).
