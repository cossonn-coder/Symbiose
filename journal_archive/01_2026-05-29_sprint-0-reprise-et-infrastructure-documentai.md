<!-- Archivé depuis journal.md le 2026-06-03 (Sprint refactor structurel) -->

## 2026-05-29 — Sprint 0 : reprise et infrastructure documentaire

### Contexte

Reprise du projet après une pause de plusieurs semaines. Travail en SSH
depuis téléphone sur VM Debian. Objectif de la session : faire l'état
des lieux complet, poser le `CLAUDE.md`, le `journal.md`, l'index mémoire,
et sécuriser le tout dans un dépôt git initial.

### État des lieux à l'ouverture

**Moteur Python** (`data/code/`) — solide, ~2500 lignes, 500+ ans simulés
sans crash. C'est la source de vérité écologique.

| Fichier | Rôle |
|---|---|
| `models.py` | Hiérarchie classes, instances, tuiles, rondelles, registre d'effets |
| `fields.py` | GridField, LightField, DisturbanceField, SeedBank, EcoFields |
| `effects.py` | Système d'effets hybride probabiliste |
| `engine.py` | Boucle 52 semaines, succession, transitions saisonnières |
| `main.py` | Scénario test (5 plantes, 1 tuile, durée paramétrable) |

**Portage Godot/C#** — fondations posées dans `core/`, orchestration vide.

Fonctionnels (~1700 lignes) : `PlantData.cs`, `GridField.cs`, `TileData.cs`,
`PlantCatalogue.cs` (14 espèces dont indicatrices), `SpriteLoader.cs`.

Le `GridField.cs` C# est **plus avancé** que la version Python :
- OM tri-compartiment (fresh / active / stable) au lieu d'un seul champ
- Pression pathogène scalaire par tuile
- Rain feedback couplé à la densité végétale

Stubs vides (12 fichiers) : `GameManager`, `EcologySystem`, `TurnSystem`,
`SeedBankSystem`, tout `plants/`, `ui/`, `visuals/`, `world/SoilField.cs`,
`Main.cs` (classe nommée `Node2d`, hors namespace).

Non portés : `effects.py`, `engine.py` (toute la logique de simulation
hebdomadaire et la succession écologique).

**Configuration Godot** :
- Godot 4.6 .NET, C# .NET 8 ✓
- 1920×1080, filtre Nearest ✓
- Seul `SpriteLoader` en autoload
- `run/main_scene` pointe vers `TileGrid.tscn` (et non `Main.tscn` qui est
  un brouillon obsolète avec des Node vides en français)

**Sprites** :
- `tile_terre.png` mesure **78×57** sur disque alors que `TileGrid.cs`
  code une grille en 96×48 → décalages garantis
- Plusieurs PNG de plantes sont des sprite sheets 1408×768 non parsés
- Le basilic a 4 stades en PNG individuels mais en RGB **sans canal alpha**
- Catalogue C# cherche `tomato_*`, `basil_*`, `bean_*` — sur disque les
  fichiers sont nommés en français (`basilic_*`, `tomates`, `haricot`)
- **Pas de sprite maison** — pourtant pièce centrale du design 3×3

### Incident Nextcloud

Pendant la session, le dossier projet a temporairement perdu plusieurs
sous-dossiers (`plants/`, `ui/`, `visuals/`, `world/`, `data/code/`, ainsi
que `Main.cs`, `project.godot`, `Symbiose.csproj`, etc.) suite à une
synchronisation Nextcloud. La synchronisation s'est terminée et tout est
revenu. Conséquence durable : **toujours travailler avec un dépôt git
sain** pour éviter une perte définitive lors d'un prochain incident sync.

### Décisions du Sprint 0

- **Décision** : adopter le `CLAUDE.md` global de Karpathy (déjà installé
  dans `~/.claude/CLAUDE.md`) et lui adjoindre un `CLAUDE.md` projet
  spécifique à Symbiose contenant identité, source de vérité, stack,
  philosophie, archi courante, garde-fous, backlog.
- **Décision** : tenir un `journal.md` à la racine du projet versionné
  avec le code. C'est la mémoire partagée Nico ↔ Claude des décisions.
- **Décision** : initialiser un dépôt git local pour geler l'état après
  l'incident Nextcloud, sans pousser vers un remote pour l'instant.
- **Décision** : reporter la création des skills et agents au Sprint 2,
  quand le besoin se manifestera concrètement. Ne pas sur-outiller.
- **Décision** : ajouter `.claude/settings.local.json` au `.gitignore`
  (permissions par machine, non partageables).
- **Décision** : prioriser l'alignement Python ← C# (faire évoluer Python
  vers OM tri-compartiment et pathogen_pressure) plutôt que de régresser
  le C#, pour conserver Python comme référence à jour.

### Ce qui a été produit dans le Sprint 0

- `.gitignore` étendu (Claude settings, `__pycache__`)
- `CLAUDE.md` projet (≈110 lignes)
- `journal.md` (ce fichier)
- Système mémoire initialisé (index + 3 fichiers essentiels)
- Premier commit git de l'état complet

---
