# ① Causes de mort lues correctement (carnet, aide, chronique)

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, puis
`docs/perf/run_eternel/conception_chronique_especes.md` §1-§2.
**Golden : INTACT** (`a10b7225…`). Le texte du `log` moteur NE CHANGE PAS.

## Objectif
`sim/evenements.py::evenements(log)` doit rendre, pour toute mort, la **bonne
espèce** et une **cause canonique** (table §2 de la conception). Aujourd'hui une
ligne réelle `  ✗ Santé Pommier@(3, 4) -1 [herbivorie p=0.040] → meurt` donne
`Evenement('mort', 'T0', (3, 4), None, 'conflit')` (vérifié le 2026-11-06).

## À faire
1. `sim/evenements.py` :
   - branche `✗` : retirer le préfixe `Santé ` avant `_CLE_DE_NOM` ; lire le
     `[reason]` (cf. `tests/diag_morts_field.py::_classify`) et le traduire en
     cause canonique par une table de préfixes (constante nommée, commentée).
     Ne garder `✗` comme mort que si la ligne finit par `→ meurt` (une ligne
     `!` = dégât non mortel, déjà exclue par le marqueur).
   - Ne JAMAIS retomber sur `conflit` : raison inconnue → `autre`.
   - Lire `❄ <Nom>@pos meurt (annual)` et `✿ <Nom>@pos meurt (bisannuelle…)`
     → `mort` / `fin_de_cycle` (formats dans `sim/engine/mortalite.py` ~l.318-337).
   - Relever au code les `effect["description"]` des effets `reduce_health`
     d'espèce (`plants/`) pour les ranger en `maladie` s'il s'agit de maladies.
   - `_evenements` (API historique de `maitrise_detection`) : NE PAS toucher.
2. `sim/carnet.py` : concept par cause (`CONCEPT_DE`) et gabarits `_D`/`_I`
   pour chaque nouvelle cause (`herbivorie`, `maladie`, `grele`, `vent`,
   `secheresse`, `ombre`, `usure`, `fin_de_cycle`, `autre`). Vérifier au code
   que les concepts visés existent (`ravageurs`, `maladie`, `météo`, `eau`,
   `lumière`, `sénescence`) ; sinon prendre le plus proche existant et le dire.
   Voix : descriptif = ce qu'on voit ; interprétatif = la cause comprise, à la
   première personne, ton des gabarits voisins. Garder les entrées `conflit`.
3. `sim/aide.py::REMEDE` : un remède par cause-problème (pas pour
   `fin_de_cycle`/`sénescence`). Remèdes = gestes de MILIEU (philo #1).
4. `tests/test_evenements.py` : remplacer le cas `_l_mort_conflit` par des
   lignes au **format réel** du moteur (au moins herbivorie, maladie, vent,
   gel, raison inconnue → `autre`, `❄`, `✿`) ; ajouter un test qui produit une
   vraie ligne via `apply_mutations([ReduceHealth(...)])` et la relit, pour que
   le format ne puisse plus dériver sans casser un test.

## Vérifier
`python3 -m tests.test_golden` (inchangé), `python3 -m tests.test_evenements`,
`python3 -m tests.test_carnet`, `python3 -m tests.test_maitrise_detection`.
NE PAS lancer `test_epaisseur_500ans`.

## Ne pas faire
Modifier le texte du log moteur ; toucher `_evenements` ; inventer une cause
non présente dans le log ; supprimer les entrées `conflit`.
