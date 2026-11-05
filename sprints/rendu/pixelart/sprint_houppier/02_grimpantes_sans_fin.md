# ② Grimpantes sans fin de pousse — golden INTACT attendu

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (bilan ①), conception §3, `sim/grimpe.py`, `sim/growth/geometrie.py` (`_apex_z_floor`), `sim/growth/phases.py` (`_elongate_emit`), `sim/growth/cladoptose.py` (`couper_branches`), `sim/engine/branches.py` (`mort_des_branches`, `deposer_bois_tombe`), `world/support.py`.

## Objectif

Une liane arrivée au sommet de son appui continue. Elle trouve un autre appui depuis son apex, ou elle plie, et sa partie effondrée meurt en litière `bois`, puis repart d'un bourgeon. Le dépassement du treillis (zmax 251 à 302 cm pour 180 [`accroches_adultes`, seed 42, n=1 run, VM]) disparaît au profit de ce comportement.

## Modèle (intention, placement à vérifier au code)

- **Levier** `rigidite_tige` sur `PlantBase`, `None` par défaut : tout est inerte. Renseigné sur `Ivy` et `Jasmine` seuls. `L_crit = rigidite_tige × f(lignification) × d^⅔`, d = épaisseur au départ de la partie libre. Repère 2 m à 1 cm pour une tige ligneuse [odg]. Le jasmin est plus souple que le lierre [choix].
- **Longueur libre** d'un apex : longueur le long de sa branche au-dessus de la hauteur d'appui.
- **Relais** : fonction neuve dans `sim/grimpe.py`, une fois toutes les 4 semaines [choix], seulement si un apex a dépassé l'appui. Scan depuis la pointe de l'apex le plus haut, rayon `RAYON_ACCROCHE_CM`. Candidats : `support_compatible`, plus hauts que l'apex, plante non grimpante (`mode_grimpe is None`) pour un hôte. `tile.plants` de la tuile seule. Départage sans RNG, sans `id()` si la clé doit survivre à un rejeu : vérifier ce point, `_hote_candidats` utilise `id(other)`.
- **Rapprochement** : `_apex_z_floor` ne fait que relever le z. Si un apex relayé monte en l'air à 60 cm de son nouvel appui, ajouter un biais horizontal vers l'appui, à la même condition d'espèce. Décider sur capture.
- **Pliage** : au-delà de `L_crit`, plancher `DROOP_Z` pour cet apex. `_apex_z_floor` raisonne aujourd'hui par plante : vérifier s'il faut descendre à l'apex, et que ce changement reste inerte sans `rigidite_tige`.
- **Effondrement** : au-delà de `L_crit` × marge [choix], coupe du sous-arbre, cause `effondrement` dans `mort_des_branches`, litière `bois`, bourgeon sur le porteur. Respecter l'axe porteur et le collet. Pas d'oscillation : mesurer sur 3 ans qu'une liane ne repousse pas et ne retombe pas à chaque tick.
- **Mise à jour** de la docstring `Jasmine` : le mur reste au `palisser`, le relais couvre plantes et structures.

## Banc et oracle

Banc `liane_relais` dans `data/code/bancs/` : treillis + arbre haut dans le rayon de relais ; treillis + mur ; treillis seul ; liane sans aucun appui. `tests/bancs/test_liane_relais.py` : appui changé, zmax ≤ appui + `L_crit` sur le treillis seul, litière `bois` déposée à l'effondrement, repousse. Enregistrer le banc au registre `bancs/__init__.py`, avec sa semaine de capture.

## Mesures

Haricot : digests identiques sur `accroches_adultes` avant/après, tous pieds de haricot. Lierre et jasmin : longueur et chutes comme au ①. Hôte : vitalité du pommier sous lierre sur 3 ans, pour constater l'étranglement émergent. Tick du banc : ≤ +10 %, avec `[n=…, VM, charge …]`.

## Golden

**INTACT**. S'il bouge : anomalie à diagnostiquer, pas de re-figeage.

## NE PAS

Donner `rigidite_tige` à une autre espèce. Ouvrir le relais à une autre tuile. Toucher à `hauteur_autoportante`. Modifier `_elaguer`. Lancer `tests/test_epaisseur_500ans.py`.
