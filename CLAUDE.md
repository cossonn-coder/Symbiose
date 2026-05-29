# SYMBIOSE

**Sandbox écologique évolutif** en permaculture — jardin éternel à un seul
run. Version vidéo (Godot 4 / C#) et version physique (tuiles 3D imprimées
+ cartes MTG) développées en parallèle. Public : amis et famille de Nico,
ingénieur électronique embarqué à Grenoble.

> Avant : « roguelike écologique ». Redéfini le 2026-05-29 — voir
> Sprint conception dans `journal.md`. Ne plus utiliser le vocabulaire
> roguelike (run, shop inter-run, extinction terminale, héritage entre
> runs).

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
- **Boucle hybride** : phase planification en temps figé ↔ phase saison
  de 15 minutes en temps réel (1 semaine = 60 secondes)

## Philosophie de design — NE JAMAIS DÉRIVER

1. Le joueur agit **principalement** sur le MILIEU. L'action directe sur
   les êtres vivants reste possible (écraser un nuisible, déraciner une
   plante) mais coûteuse en Vigueur et perturbatrice — la permaculture
   s'enseigne par l'usure de la solution facile.
2. Jamais bonus/malus direct **sur les plantes** — toujours flux →
   contrainte écologique → réponse biologique émergente.
3. Simulation déterministe (seed global, hash de bruit spatial).
4. **Run éternel** — un jardin unique et persistant, le sol porte la
   mémoire et grandit avec le joueur.
5. Indices biologiques visuels + encyclopédie et carnet auto comme
   dispositifs informationnels. Pas de chiffres ni de barres en HUD
   primaire (sauf mode debug).
6. La sagesse écologique prime — pas de tutoriel imposé. L'apprentissage
   est diffus : action → conséquence → consultation → hypothèse.
7. Hétérogénéité persistante — deux joueurs n'ont jamais le même terrain.

Pour le détail historique, voir `data/code/models.py` et `data/code/fields.py`.

## Mécaniques centrales (depuis Sprint conception, 2026-05-29)

### Vigueur unifiée (Qi + Mana)
Chaque être vivant possède sa **Vigueur** (≡ Mana, énergie propre).
Les **champs écologiques existants** (`microbiome`, `soil_memory`, `om_*`,
`fertilite`) modélisent le **Qi territorial**. La Vigueur se puise dans
le territoire et y retourne à la mort.

**Modèle de Vigueur joueur** (base, à ajuster post-test) :
- Montant initial 100, +10/semaine simulée, full au passage de saison
- Sources extra : récolte plantes mûres, méditation au foyer
- **Vigueur max augmente avec les paliers de maîtrise**

### Maîtrise et paliers
5 paliers par famille botanique et par concept écologique transversal :
**découverte → investissement → maîtrise → expertise → transcendant**.
La maîtrise débloque : extension de terrain (tuile thématique), accès au
magazine, basculement du carnet en mode interprétatif, augmentation de
la Vigueur max joueur.

**Transcendant = non-action existentielle** : l'écosystème devient
auto-suffisant, le joueur n'a plus besoin d'agir. Les perturbations
entretiennent l'engagement à très long terme.

### Apprentissage par méthode scientifique
Observer → formuler → tester → conclure. Trial & error, prise de risque,
diversification d'idées sont récompensés. Aucune action n'est punitive en
soi — c'est l'écosystème qui répond.

### Encyclopédie & Carnet
- **Encyclopédie** : wiki ingame qui se complète aux découvertes (voir
  une espèce = entrée basique ; cycle complet = description bio ; cycles
  répétés avec succès = effets écosystémiques).
- **Carnet auto** : enregistrement automatique des événements,
  consultable, indexé. **Descriptif au début**, **interprétatif au seuil
  de maîtrise** sur le concept concerné. Préserve la méthode scientifique
  pendant l'apprentissage, révèle les causes une fois la compréhension
  intériorisée.

### Acquisition d'espèces (4 canaux)
1. Succession spontanée (`niche_index` dans le moteur Python)
2. Événements rares (bouture, oiseau, vent)
3. Exploration de friche périphérique (abstraite au début)
4. **Magazine de botanique** — déblocage par Vigueur joueur + maîtrise

### Auxiliaires
**Visibles dès le début, non identifiables sans maîtrise.** Modèle
technique : champ ambiant `GridField` pour la dynamique + sprites
apparents pour la perception. Tu vois l'insecte avant de connaître son
nom — posture du naturaliste débutant.

### Maison normande — hub vivant (5 fonctions)
Atelier · Semis intérieur · Magazine de botanique · Carnet · **Foyer**
(point de récupération de Vigueur).

### Démarrage du jardin (3 écoles au choix)
Friche pionnière · Sol modeste · Jardin abandonné.

### Extension du terrain
**Par maîtrise écologique** uniquement. Maîtriser une famille fait
apparaître une tuile thématique (verger, mare, prairie aromatique…).
Pas d'achat, pas de conquête : la connaissance ouvre l'espace.

### UX du volume cognitif
432 plots × 15 min temps réel = trois mitigations actives simultanément :
**pause libre + notifications hiérarchisées + zoom contextuel**.

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

### Systèmes à concevoir (issus du Sprint conception)
- **Vigueur universelle** (D11) — couche transversale (joueur + plantes +
  auxiliaires + nuisibles)
- **Paliers de maîtrise** (D12) — méta-état du joueur, conditions de
  passage par famille et concept
- **Magazine de botanique** (D13) — déblocage espèces, coût Vigueur +
  maîtrise
- **Carnet auto** (D14) — capture événements, indexation, bascule
  descriptif → interprétatif
- **Extension de terrain par maîtrise** (D15) — apparition tuile thématique

### Données calibrage
- Sprites tuiles **78×57** sur disque (et non 96×48 codé dans `TileGrid.cs`)
- Sprites plantes : sheets 1408×768 + PNG individuels en RGB sans alpha
- Pas de sprite maison à ce jour

Voir `journal.md` pour le détail de l'avancement et les décisions
historiques.

## Garde-fous spécifiques

- **Français systématique** dans les réponses utilisateur. Conserver les
  identifiants code en anglais ou français selon le fichier existant.
- **Pédagogie explicite** à chaque proposition d'architecture — Nico
  apprend Godot/C# en frontend, vient du C/Python embarqué.
- **Pas de fichier créé sans demande explicite** — concevoir en
  conversation d'abord, puis ne créer que sur « OK », « vas-y », « lets go ».
- **Un fichier modifié à la fois** sauf demande contraire (cette règle
  est suspendue quand une synchro cohérente multi-fichiers est explicitement
  demandée — typiquement avant un commit).
- **Avant tout sprint**, vérifier que git est à jour. Nextcloud a déjà
  perdu transitoirement des fichiers le 2026-05-29.
- **Max 3 questions à la fois.**
- **Mettre à jour `journal.md` à la fin de chaque sprint** — c'est notre
  mémoire partagée des décisions et de l'avancement.

## Backlog actif

Chaque sprint à venir possède un **kickoff autosuffisant** dans
`sprints/`. À l'ouverture d'une nouvelle session, Nico donne
l'instruction « lis `sprints/sprint_X.md` » et Claude reprend sans
contexte préalable.

| Sprint | Kickoff |
|---|---|
| Sprint conception bis (zones blanches : sauvegarde, météo, lore…) | `sprints/sprint_conception_bis.md` |
| Sprint 1 (recalibrage visuel + grille 3×3 + maison) | `sprints/sprint_1_recalibrage_visuel.md` |
| Sprint 2 (orchestration C# : Main, GameManager, TurnSystem) | `sprints/sprint_2_orchestration.md` |
| Sprint 3 (portage simulation Python → C# + parité) | `sprints/sprint_3_portage_simulation.md` |
| Sprint 4 (Vigueur, paliers, encyclopédie, carnet, magazine, foyer) | `sprints/sprint_4_mecaniques_conception.md` |

Pour l'historique des décisions, voir `journal.md`.
