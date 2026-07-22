# ② Cap de létalité chronique par tick — « usure, pas punition »

> Kickoff AUTOSUFFISANT. Lis `CLAUDE.md` + `00_etat.md` + ce fichier. Prérequis :
> tronçon ① fait (conflit non-létal, golden `a1c9c51f…`). Source de vérité =
> Python `data/code/`. Lancement depuis `data/code/`.

## Objectif
Garantir qu'une **plante saine ne meurt jamais en un seul tick** des voies de
mortalité **de fond** indépendantes. Aujourd'hui `apply_disturbances`
(`sim/effects/perturbations.py`) empile sans plafond plusieurs `ReduceHealth` dans
le même tick ; sur l'échelle santé **entière 0-3**, un cumul peut passer 3→0 d'un
coup (ex. théorique : herbivorie LÉTALE `−2` sur sol mort + mortalité de fond
`×0,7` le même tick). Philo #6 : la mort doit être une **usure multi-tick**, pas
une punition instantanée.

## Fichier à toucher
`data/code/sim/effects/perturbations.py` — fonction `apply_disturbances`, au point
d'assemblage `all_mutations` juste **avant** `log += apply_mutations(all_mutations,
game_state)` (≈ ligne 452). **Un seul fichier.**

## Modèle
Borner à **−1 santé / tick / plante** le cumul des `ReduceHealth` issus des voies
**CHRONIQUES** :

    CHRONIQUES = { herbivory_pressure, background_mortality,
                   drought_stress_damage, shade_stress_damage, fungal_disease }
    AIGUËS (exemptes) = { damping_off (fonte des semis) }
      # gel/grêle/vent ne passent pas par apply_disturbances (déjà _mediated_/_wind_damage)

Implémentation (déterministe, **zéro RNG**) :
1. Construire séparément deux listes plutôt qu'un seul `all_mutations` :
   - `acute_muts` = sortie de `damping_off` (fonte des semis) ;
   - `chronic_muts` = sorties de herbivorie + fongique + sécheresse + ombre +
     mortalité de fond.
   (Réordonner l'assemblage de la boucle `for plant in list(tile.plants)` en
   conséquence ; garder l'ordre d'appel actuel des fonctions pour ne pas décorréler
   les tirages `_hash_noise` — seule la VENTILATION dans deux listes change.)
2. Cap par plante sur les CHRONIQUES : pour chaque plante présente dans
   `chronic_muts`, si la somme de leurs `amount` > 1, **ne garder qu'un total de
   1** (p.ex. conserver le premier `ReduceHealth` chronique de la plante avec
   `amount=1`, écarter le reste). Conserver la `cause`/`reason` du coup retenu
   pour la sémiologie (privilégier une cause non vide si présente, pour que la
   marque foliaire subsiste).
3. `log += apply_mutations(acute_muts + chronic_clampé, game_state)` — l'aigu
   (fonte) passe INTACT (une fonte des semis peut toujours emporter un semis).

Garde-fous :
- Ne borne QUE les voies chroniques listées ; damping_off reste décisif.
- Le cumul chronique max devient `−1`/tick → une plante saine (health 3) tient au
  moins 3 ticks de fond avant de mourir → usure (philo #6).
- Perf : simple regroupement O(mutations) des mutations déjà produites, aucune
  passe spatiale neuve.

## Ce qu'il NE faut PAS faire
- Ne PAS toucher l'échelle santé (reste 0-3, décidé).
- Ne PAS capper les voies aiguës (fonte/gel/grêle/vent).
- Ne PAS toucher `_tick_senescence_health` / `_resoudre_conflits` (sénescence,
  asphyxie, conflit — hors `apply_disturbances`). Une plante VIEILLE ou ASPHYXIÉE
  peut légitimement cumuler ; le cap ne concerne QUE le fond chronique de
  `apply_disturbances`.
- Ne PAS introduire d'aléa.

## Golden attendu — re-figeage LOCALISÉ pré-autorisé
Attendu **NEUTRE** sur le smoke (sols drainants + espèces neutres : le cumul
chronique dépasse rarement −1). **Si** le cap mord malgré tout, la dérive est
**localisée et expliquée** (cumul chronique borné à −1) → re-figeage AUTORISÉ par
ce kickoff : `python3 -m tests.test_golden --capture`, consigner le nouveau hash
dans `00_etat.md`. Si neutre : hash inchangé `a1c9c51f…`, rien à capturer.

## Vérifications
- `python3 -m tests.test_golden` (PASS si neutre, sinon re-capture annoncée).
- Test ciblé de non-mort-éclair : construire une tuile, une plante saine
  (health 3) sur **sol mort** (microbiome < 0,2 → `micro_norm < 0,20`) + champ
  `ravageur` et `auxiliaire` forçant la bascule létale (`aux < 0,20`), faire
  tourner `apply_disturbances` un tick → la plante perd **au plus 1** santé (pas
  −2, pas la mort). Vérifier aussi qu'un semis en fonte des semis peut toujours
  mourir (aigu non capé).
- `python3 -m tests.test_competition`, `python3 -m tests.test_senescence`.

## Mise à jour de fin de tronçon
`00_etat.md` : ② fait, statut golden (neutre / nouveau hash). Commit (fichiers
nommés).
