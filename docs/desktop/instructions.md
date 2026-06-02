# Instructions projet — Symbiose (app desktop Claude)

À coller dans le champ **Instructions** d'un projet Claude desktop. Les fichiers de contexte (`vision.md`, `architecture.md`, `historique_decisions.md`) sont à uploader comme knowledge.

---

## Qui je suis

Nico, ingénieur électronique embarqué à Grenoble, ~10 ans de C/Python. Frontend (Godot 4 / C#) = **débutant**, c'est mon premier projet de jeu vidéo. Tu m'expliques la pile graphique comme à quelqu'un qui sait coder mais découvre l'écosystème.

Public visé du jeu : amis et famille. Pas de jeu commercial.

## Source de vérité

Le moteur Python dans `data/code/` (`models.py`, `fields.py`, `effects.py`, `engine.py`, `main.py`) est la **source de vérité écologique**. `main.py` tourne — il a simulé 500+ ans sans crash.

- Toute mécanique Godot/C# doit avoir un équivalent Python ou être propagée vers Python avant intégration.
- Quand Python et C# divergent, prioriser l'alignement **vers Python** sauf décision explicite contraire.
- Pas de gameplay décidé en C# qui ne soit pas dans Python d'abord.

## Stack & contraintes techniques

- **Godot 4.6 .NET, C# .NET 8.0**. **GDScript interdit**. Namespace `Symbiose` sur tout le gameplay.
- Pixel art, filtre `Nearest` partout. Résolution 1920×1080. Zoom par paliers entiers ×4 / ×8 / ×16 / ×32 — **jamais de fraction**.
- **Boucle hybride** : phase planification en temps figé ↔ phase saison de 15 minutes en temps réel (1 semaine = 60 secondes).
- Tuile de sprite réelle = **78×57** sur disque (pas 96×48 codé dans `TileGrid.cs` — c'est la dette D2).
- Échelle : **1 plot = 50×50 cm**, monde 3×3 tuiles × (6×8) = **432 plots ≈ 108 m²**. Position des plantes **continue** (pixel-sol). Lumière au pixel à 2 cm/px. Chimie du sol au plot.

## Philosophie de design — NE JAMAIS DÉRIVER

1. Le joueur agit **principalement** sur le MILIEU. Action directe sur les êtres vivants possible mais **coûteuse en Vigueur et perturbatrice** — la permaculture s'enseigne par l'usure de la solution facile.
2. Jamais bonus/malus direct **sur les plantes** — toujours flux → contrainte écologique → réponse biologique émergente.
3. Simulation **déterministe** (seed global, hash de bruit spatial).
4. **Run éternel** — un jardin unique et persistant. Le sol porte la mémoire et grandit avec le joueur. Pas de roguelike, pas de game over, pas de bouton « recommencer ».
5. Indices biologiques **visuels** + encyclopédie et carnet auto. Pas de chiffres ni de barres en HUD primaire (sauf mode debug).
6. La sagesse écologique prime — pas de tutoriel imposé. Apprentissage diffus : action → conséquence → consultation → hypothèse.
7. Hétérogénéité persistante — deux joueurs n'ont jamais le même terrain.

## Comment travailler avec moi

- **Français systématique** dans les réponses. Identifiants code en anglais ou français selon le fichier existant.
- **Pédagogie explicite** à chaque proposition d'architecture — je découvre Godot/C#.
- **Pas de fichier créé sans demande explicite** — concevoir en conversation d'abord, puis ne créer que sur « OK », « vas-y », « lets go ».
- **Un fichier modifié à la fois** sauf si je demande une synchro multi-fichiers (typiquement avant un commit).
- **Avant tout sprint code**, vérifier que git est à jour. Nextcloud a déjà perdu des fichiers en synchro.
- **Max 3 questions à la fois.**
- **Tenir `journal.md` à jour à la fin de chaque sprint** — c'est notre mémoire partagée des décisions et de l'avancement.
- Pour les sujets bio/éco hors de mon expertise (rhizosphère, succession, génétique des populations…) : **produire un dossier d'étude** à lire tranquillement, pas une rafale de questions à trancher.

## Domaine non-trivial

- L'écologie du sol (rhizosphère, microbiome, exsudats, OM en cascade fresh/active/stable, mycorhizes) est **modélisée** dans le moteur. Tu peux raisonner sur la biologie au niveau d'un étudiant en agro ou d'un praticien de permaculture.
- L'astronomie solaire (azimut/élévation par latitude ~49°N, 4 tranches horaires + intégrale journalière) sert au calcul des ombres au pixel.
- La génétique : héritage biparental par moyenne + mutation gaussienne, hybridation inter-espèces par introgression sur espèce fixe (pas de génération de nouvelles `PlantData`).

## Backlog sprints (référence)

Chaque sprint a un kickoff autosuffisant dans `sprints/`. À l'ouverture d'une session : « lis `sprints/sprint_X.md` » suffit à reprendre.

- `sprint_succession.md` — mini-sprint D25 (pionnier → prairie)
- `sprint_1_recalibrage_visuel.md` — grille 3×3 + maison + alignement sprites
- `sprint_2_orchestration.md` — Main, GameManager, TurnSystem
- `sprint_eclairement.md` — D20-D21 : ombres pixel + pérennes
- `sprint_genetique.md` — D17+D22 : banques + héritage biparental
- `sprint_3_portage_simulation.md` — effects.py + engine.py → C#
- `sprint_4_mecaniques_conception.md` — Vigueur, paliers, encyclopédie, carnet, magazine, foyer

Pour comprendre **où on en est** : `journal.md` (entrées datées) + le `vision.md` / `architecture.md` / `historique_decisions.md` chargés en knowledge.
