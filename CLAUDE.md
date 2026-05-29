# SYMBIOSE

Jeu roguelike écologique en permaculture. Version vidéo (Godot 4 / C#) et
version physique (tuiles 3D imprimées + cartes MTG) développées en parallèle.
Public : amis et famille de Nico, ingénieur électronique embarqué à Grenoble.

## Source de vérité

Le moteur Python dans `data/code/` (`models.py`, `fields.py`, `effects.py`,
`engine.py`, `main.py`) est la **source de vérité écologique** du jeu.

- Toute mécanique Godot doit avoir un équivalent Python ou être propagée
  vers Python avant intégration.
- Quand Python et C# divergent (cf entrée D10 du `journal.md`), prioriser
  l'alignement vers Python sauf décision explicite contraire de Nico.
- `main.py` tourne — il a simulé 500+ ans sans crash. C'est la référence
  comportementale.

## Stack technique

- Godot 4.6 .NET, C# .NET 8.0
- Namespace `Symbiose` sur tous les fichiers de gameplay
- **GDScript INTERDIT** — tout en C#
- Pixel art : filtre `Nearest` partout (réglé dans `project.godot`)
- Résolution 1920×1080
- Zoom par paliers entiers ×4 / ×8 / ×16 / ×32 — jamais de fraction
- Tour par tour saisonnier — pas de temps réel sauf pendant la phase saison

## Philosophie de design — NE JAMAIS DÉRIVER

1. Le joueur agit sur le MILIEU, jamais directement sur les plantes
2. Jamais bonus/malus direct — toujours flux → contrainte écologique →
   réponse biologique émergente
3. Simulation déterministe (seed global, hash de bruit spatial)
4. Indices biologiques visuels uniquement — pas de chiffres ni de barres
   (sauf mode debug)
5. Roguelike Run C — même terrain entre runs, le sol porte la mémoire
6. La sagesse écologique prime — pas de tutoriel explicite
7. Hétérogénéité persistante — deux joueurs n'ont jamais le même terrain

Pour le détail, voir `data/code/models.py` et `data/code/fields.py`.

## Architecture courante (mise à jour : 2026-05-29)

### Fonctionnels (~1700 lignes C#)
- `core/PlantData.cs` — GrowthStage, PlantData, PlantInstance
- `core/GridField.cs` — GridField, LightField, EcoFields complet
- `core/TileData.cs` — Tile, StakeSlot, ConflictNotification
- `core/PlantCatalogue.cs` — 14 espèces dont indicatrices avec UnlockCondition
- `core/SpriteLoader.cs` — autoload, chargement récursif

### Stubs vides (à écrire)
- `core/GameManager.cs`, `EcologySystem.cs`, `TurnSystem.cs`, `SeedBankSystem.cs`
- `plants/*`, `ui/*`, `visuals/*`, `world/SoilField.cs`
- `Main.cs` (la classe s'appelle encore `Node2d`, hors namespace)

### Non-portés
- `effects.py` → pas encore en C#
- `engine.py` → pas encore en C# (boucle 52 semaines + succession)

### Données calibrage
- Sprites tuiles **78×57** sur disque (et non 96×48 codé dans `TileGrid.cs`)
- Sprites plantes : sheets 1408×768 + PNG individuels en RGB sans alpha
- Pas de sprite maison à ce jour

Voir `journal.md` pour le détail de l'avancement et les décisions.

## Garde-fous spécifiques

- **Français systématique** dans les réponses utilisateur. Conserver les
  identifiants code en anglais ou français selon le fichier existant.
- **Pédagogie explicite** à chaque proposition d'architecture — Nico
  apprend Godot/C# en frontend, vient du C/Python embarqué.
- **Pas de fichier créé sans demande explicite** — concevoir en
  conversation d'abord, puis ne créer que sur "OK", "vas-y", "lets go".
- **Un fichier modifié à la fois** sauf demande contraire.
- **Avant tout sprint**, vérifier que git est à jour. Nextcloud a déjà
  perdu transitoirement des fichiers le 2026-05-29.
- **Max 3 questions à la fois.**
- **Mettre à jour `journal.md` à la fin de chaque sprint** — c'est notre
  mémoire partagée des décisions et de l'avancement.

## Backlog actif

Sprint en cours : **Sprint 0 — gel de l'état et infrastructure documentaire.**

Prochaine priorité après Sprint 0 :
- Sprint 1 : recalibrer dimensions sprites, refaire `world/TileGrid.cs`
  avec grille 3×3 tuiles et maison centrale.

Pour le détail complet du backlog, voir la section dédiée du `journal.md`.
