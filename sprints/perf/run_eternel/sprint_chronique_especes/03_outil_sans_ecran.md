# ③ Outil sans écran + premier run de 200 ans (`verger_mur`)

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §4-§5.
**Prérequis** : ② fait. **Golden : INTACT.**

## Objectif
Pouvoir lancer sur la VM, sans Godot ni Nico, un run de N années sur n'importe
quel monde/banc et en lire la chronique. Puis le faire une fois pour de vrai.

## À faire
1. `tools/chronique_run.py` (`python3 -m tools.chronique_run --config verger_mur
   --annees 200 [--seed S] [--sortie DIR]`). Monte le monde par
   `SimServer.cmd_init` (patron `tools/diag_population.py::_build_engine`) et
   avance par le **même chemin post-tick** que le serveur, pour que la chronique
   soit identique au rapport C. Si le coût du snapshot de `cmd_step_week` pèse
   > 30 % sur 1 an mesuré, factoriser la séquence post-tick dans le serveur pour
   l'appeler sans snapshot — sans la dupliquer. Écrit `chronique.txt` (le
   `texte()` de ②) et `chronique.json` (le brut), plus une ligne de progression
   sur stderr tous les 10 ans (année, vivants, temps écoulé).
2. Lancer `verger_mur` 200 ans **en tâche de fond** (≈ 1,7 h estimé), sortie
   dans `sprints/perf/run_eternel/sprint_chronique_especes/mesures/`.
3. Lire le résultat et consigner les FAITS dans D127 (`DETTE.md`) : année et
   cause de disparition de chaque fruitier, recrutement observé (levées par
   espèce), noyers. Chaque chiffre porte sa limite (`[seed 42, n=1 run, VM]`).
   Trancher l'hypothèse §5 (vieillesse ?) ; si la cause n'est pas la vieillesse,
   ouvrir le point écologique dans D127 pour une conception à part — NE PAS
   corriger le moteur ici.

## Vérifier
`python3 -m tests.test_golden`. Un run court (`--annees 2 --config smoke`)
passe avant le long. NE PAS lancer `test_epaisseur_500ans`.

## Ne pas faire
Modifier le moteur ; conclure sur une cause sans la lire dans la chronique.
