## 2026-06-10 — Sprint Intégration·3 : saison animée (boucle hybride côté vue)

### Contexte

Tranche 3 du sprint Intégration (kickoff `03_saison_animee.md`) : le monde
statique de t2 se met à **vivre** — boucle hybride **Planification (temps
figé) ↔ Saison (temps réel, 1 semaine = 60 s)** implémentée côté vue. Comme
prévu au kickoff : **un seul fichier modifié** (`world/WorldView.cs`), **zéro
Python** (le protocole v0 `step_week` suffit). Golden intact (`16a1b937…`).

### Fait — C# (`WorldView.cs`)

- **Machine à états** `Planification` (défaut) ↔ `Saison` ↔ `Pause`, bascule
  **Espace** (`_UnhandledInput`) — les boutons UI viendront au sprint UI.
- **Temps continu sur sim discrète** : accumulateur dans `_Process` ;
  `[Export] SecondsPerWeek=60` (plage design 30-180 s) +
  `[Export] DebugSecondsPerWeek=3` (prioritaire si >0, pour valider sans
  attendre 13 min/saison — à remettre à 0 hors debug).
- **Step hors thread d'affichage** : `Task.Run(StepWeek)` pollée par
  `IsCompleted` dans `_Process` — l'arbre de scène n'est JAMAIS touché depuis
  la Task, une seule requête en vol (pont maître/esclave 1↔1), échec → retour
  Planification + erreur console. `_ExitTree` attend la Task en vol (2 s)
  avant `quit` : jamais deux écritures concurrentes sur le pipe.
- **`ApplySnapshot` en diff** par clé stable `tile|species|x_cm|y_cm` (pas
  d'id moteur ; les plantes ne bougent jamais) : connue → `SetStructure`
  (swap sec, la plante a poussé) ; nouvelle → **fondu d'apparition** 0,6 s ;
  disparue → **fondu de sortie** 0,9 s puis `QueueFree`. Sol/maison intacts.
  Step **consommé même en pause** (la semaine était engagée côté moteur).
- **Fin de saison** : `season` du snapshot change → retour **automatique** en
  Planification + hook `OnSeasonEnd()` vide (TODO auto-save → sprint save
  global ; pas de commande `save` inventée dans le protocole v0).
- **HUD provisoire** (`CanvasLayer`+`Label` 28 px, contour noir) : « été ·
  an 1 — semaine 5/13 [====------] état » — la jauge intra-semaine s'anime
  chaque frame et **fige en pause**. Sautera au sprint UI (philo #5).

**Décision :** sémantique d'horloge assumée — `week` du snapshot = prochaine
semaine à simuler (décision t1), donc la planification s'affiche « semaine
1/13 » de la saison **à venir** (rien d'elle n'est simulé) : on prépare PUIS
on vit la saison, exactement la boucle hybride voulue.

### Péripétie de validation

Premier F5 : « Espace ne fait rien, pas d'horloge » → le label v1 (petit,
blanc sur fond clair) était illisible et le code pas encore synchronisé/
rebuildé côté poste (circuit VM → Nextcloud → build Godot). Réglé par : label
28 px à contour noir, jauge animée, prints console à chaque appui d'Espace,
texte témoin de build au chargement.

**Statut.** Tranche 3 **CLOSE** — confirmée par Nico dans Godot le jour même,
**tous critères validés** : lancement figé en planification ; Espace → les
semaines défilent, fondus visibles (naissances/morts) ; pause/reprise OK ;
**aucun gel perceptible** aux ticks ; été complet déroulé (13 semaines) +
retours automatiques en planification aux passages de saison. NB : la 1ʳᵉ
saison post-warmup ne dure qu'1 semaine (warmup 12 sem. → départ sem. 13/13
du printemps), assumé au kickoff. **Prochaine : tranche 4 (actions joueur),
kickoff `04_*.md` à écrire** (figer le format des commandes verbe+cible+
params ; la machine à états t3 porte déjà la distinction préparation/réaction).
