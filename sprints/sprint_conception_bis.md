# Sprint conception bis — fermer les zones blanches de la vision

**Statut** : à faire
**Prérequis** : Sprint conception (commit `509ff4c`) terminé
**Estimation** : 1 session de conversation dense (sans code écrit)
**Objectif** : compléter les 6 dernières zones blanches de la vision du
jeu pour clore définitivement la phase conception et permettre aux
sprints code de démarrer sur une cible stable.

---

## Avant de commencer

Tu démarres dans une session vide. Pour comprendre où on en est :

1. **`CLAUDE.md`** est déjà chargé automatiquement. Lis-le complètement.
2. **`journal.md`** — lis surtout les deux entrées du 2026-05-29 :
   - Sprint 0 (gel infrastructure)
   - Sprint conception (12 décisions structurantes)
3. **Memory** — les fichiers `project_game_vision.md`, `project_status.md`,
   `feedback_design.md` sont déjà chargés via `MEMORY.md`.

Inutile de lire le code Python ou C# pour ce sprint — c'est de la
conception pure.

---

## Mission

Le Sprint conception du 2026-05-29 a laissé **6 zones blanches** que
Nico veut traiter dans cette session via le même format de challenge
constructif (Claude pose 3 questions à la fois maximum, Nico tranche,
on note les décisions).

Pour chaque zone, démarre par **2 ou 3 tensions concrètes** issues du
moteur Python actuel ou de la vision déjà actée, puis **2-3 questions
ciblées**. Ne demande pas tout à la fois.

### Z1. Cycle de sauvegarde
- **Critique** : run éternel = persistance fiable obligatoire
- À cadrer : auto-save à chaque passage de saison ? Sauvegarde manuelle
  possible ? Format binaire ou texte (debug-friendly) ?
  Multiple slots ou un seul ? Versionnage du save quand la simulation
  évolue (ex : passage Python v5 → v6) ?

### Z2. Gestion des aléas météo
- Aujourd'hui dans `engine.py`, les aléas (canicule, gelée, pluies, vent,
  brouillard, ravageurs) sont **subis** : random.choice au début de saison
  applique l'effet, le joueur ne réagit pas.
- Or Nico a listé « gérer les événements météo » dans les 10 actions
  joueur. Donc à concevoir : **comment** le joueur agit-il sur la météo ?
  Préparation (paillage avant canicule, voiles avant gelée), réaction
  pendant l'événement (arrosage d'urgence), ou les deux ?
- Question annexe : la météo est-elle prévisible (icône qui s'affiche
  une semaine avant), ou subie sans préavis ?

### Z3. Multiples jardins / multijoueur
- Run éternel + démarrage au choix (3 écoles) = un joueur pourrait
  vouloir tenter plusieurs jardins ?
- Profils multiples sur la même installation ? Save séparée ?
- Multijoueur local ou en ligne envisagé ? Sinon, le confirmer pour
  pouvoir fermer le sujet.

### Z4. Lore / narration
- Qui est le joueur ? Personnage incarné, présence diffuse, jardinier
  anonyme ?
- La maison normande (Montmartin-sur-Mer) a une histoire ? Le jardin
  a-t-il un passé évoqué ?
- Narration via la voix de l'encyclopédie (style « naturaliste qui
  observe ») ? Voix narrative externe ? Aucune narration explicite ?
- Pas un lore lourd type RPG — un cadre poétique permaculturel.

### Z5. Conditions de panne sèche
- Run éternel = pas de game over. Mais que se passe-t-il si **tout
  meurt** ? Tous les plots vides, pas de graines viables, plus de
  Vigueur joueur ?
- Trois options à débattre :
  - (a) Le sol reste fertile, la succession spontanée fait repartir
    quelque chose (run vraiment éternel)
  - (b) Un événement narratif spécial se déclenche (« le silence du
    jardin »), le joueur reçoit un don rituel pour repartir
  - (c) Le jeu propose explicitement un redémarrage (mais sans perdre
    les paliers de maîtrise déjà acquis)

### Z6. Difficulty / accessibilité
- Public = amis et famille, niveaux de jeu hétérogènes
- Pas de mode difficulté classique (le jeu n'est pas un jeu de score)
- Mais des **réglages d'aide** ? Vitesse de simulation ajustable ?
  Notifications plus ou moins verbeuses ? Encyclopédie plus ou moins
  préremplie au démarrage ?
- Mode « expert » avec affichage debug des champs écologiques ?

---

## Format de session attendu

Reprends le format du Sprint conception qui a bien marché :
- Pour chaque zone, démarre par **synthèse de la tension** (3-5 lignes)
- Pose ensuite **3 questions max** à la fois
- Quand Nico tranche, **acte par écrit** ce qui est décidé
- Évite de passer à la zone suivante tant que la précédente n'est pas close
- Mon vote (Claude) est utile pour aider Nico à trancher — il a apprécié
  ce format au Sprint conception. Donne ton avis franc.

---

## À produire à la fin de la session

- [ ] **`journal.md`** : nouvelle entrée datée `## YYYY-MM-DD — Sprint
      conception bis : zones blanches` listant les ~12-18 décisions prises
- [ ] **`CLAUDE.md`** : ajouter dans la section « Mécaniques centrales »
      ce qui mérite d'y être (sauvegarde, météo, narration probablement)
- [ ] **Memory** : enrichir `project_game_vision.md` avec les nouvelles
      décisions, mettre à jour `project_status.md` si nouvelles dettes
- [ ] **Commit** avec message HEREDOC détaillé, ex :
      `Sprint conception bis : zones blanches refermées`
- [ ] **Proposer Sprint 1** à Nico (recalibrage visuel) comme suite

---

## Critère de fin

Aucune des 6 zones blanches n'est plus marquée « à cadrer » dans la
vision. La conception est figée pour permettre le code.
