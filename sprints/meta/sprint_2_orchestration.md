# Sprint 2 — Fondations d'orchestration C#

**Statut** : à faire
**Prérequis** : Sprint 1 terminé (grille 3×3 + maison fonctionnels)
**Estimation** : 2 à 4 sessions
**Objectif** : poser les bases C# de l'orchestration du jeu — point
d'entrée propre (`Main`), singleton d'état (`GameManager`), gestion des
phases (`TurnSystem`) — afin de pouvoir attacher la simulation au
Sprint 3.

---

## Avant de commencer

1. **`CLAUDE.md`** est chargé. Lis-le complètement, surtout la section
   « Mécaniques centrales » et la section « Architecture courante ».
2. **`journal.md`** — lis les dettes D7, D8, D9 (stubs hors namespace,
   `Main.tscn` obsolète, conflit nom `PlantInstance`).
3. **Memory** — `project_game_vision.md` (vision actée), `project_status.md`
   (avancement), `reference_godot.md` (conventions Godot).
4. **Code à lire** :
   - `Main.cs` (stub avec classe `Node2d`, hors namespace) — à refondre
   - `Main.tscn` — brouillon obsolète à supprimer/remplacer
   - `core/GameManager.cs`, `core/TurnSystem.cs`,
     `core/SeedBankSystem.cs`, `core/EcologySystem.cs` — stubs vides,
     hors namespace
   - `data/code/engine.py` — la classe `Engine` Python est le modèle
     mental cible (game_state dict, week, tick_semaine, run_year…)
   - `data/code/main.py` — voir comment Python instancie tout
5. **`project.godot`** — vérifier `run/main_scene` (actuellement
   pointé vers TileGrid.tscn — sera bientôt Main.tscn)

---

## Mission

Passer d'un état « la grille s'affiche en standalone » à « le jeu a un
point d'entrée propre qui orchestre la scène, possède un état global
sérialisable, gère les transitions planification ↔ saison ».

Pas de simulation écologique active à ce sprint — c'est le Sprint 3.
Juste les coquilles C# vivantes et reliées.

---

## Tâches dans l'ordre

### T1. Nettoyer `Main.cs` et `Main.tscn`
- **Renommer la classe `Node2d` en `Main`**, dans namespace `Symbiose`,
  attribut `[Tool]` non requis, `partial class Main : Node2D`
- **Supprimer l'ancien `Main.tscn`** (les 16 Node vides en français
  « humidité », « matière organique », etc. — vestige sans script)
- Créer une **nouvelle `Main.tscn`** propre avec attaché `Main.cs`
- Sous-nodes essentiels :
  - `GameManager` (autoload ou enfant ? voir T2)
  - `TurnSystem` (enfant)
  - `WorldRoot : Node2D` qui aura les tuiles, la maison, plantes
  - `UIRoot : CanvasLayer` pour l'HUD (vide pour l'instant)
- `Main` instancie `TileGrid` dans `WorldRoot` au `_Ready`
- Pointer `project.godot:run/main_scene` vers `Main.tscn`

### T2. `core/GameManager.cs`
Singleton autoload. Classe `GameManager : Node` dans namespace `Symbiose`.

Responsabilités :
- État global du jeu (équivalent du `game_state` dict de Python)
- Seed déterministe global
- Conteneur des tuiles, eco-fields, scores, joueur
- Sérialisation/désérialisation (préparer le hook pour Sprint conception
  bis qui aura décidé du format de save)
- Singleton pattern : `public static GameManager Instance { get; private set; }`

Référence Python : `engine.py:Engine.__post_init__` montre les clés
initiales du game_state (`week`, `scores`, `current_player`, `log`,
`eco`, `seed`).

### T3. `core/TurnSystem.cs`
Classe `TurnSystem : Node` dans namespace `Symbiose`.

Responsabilités :
- Gérer la phase courante : `Planification` (figée) ou `Saison`
  (15 min temps réel)
- Démarrer/terminer une saison (semaine 1 → 13, puis transition)
- Émettre des signaux Godot pour les transitions (`SeasonStarted`,
  `WeekTicked`, `SeasonEnded`, `PlanningPhaseStarted`)
- Pendant la phase saison : timer 60s = 1 semaine simulée
- Pendant la phase planification : temps figé, le joueur peut agir
- Pause libre (action joueur) suspend le timer

Référence Python : `engine.py:Engine.tick_semaine` et la boucle
`run_year` montrent la cadence à respecter.

### T4. `core/EcologySystem.cs` — squelette
Pas encore de tick écologique réel (c'est le Sprint 3).
Mais préparer la classe `EcologySystem : Node` dans namespace `Symbiose`
avec une méthode `TickWeek()` vide branchée sur le signal `WeekTicked`
de `TurnSystem`. Le portage de `engine.py` viendra remplir ça.

### T5. Résoudre dette D9 (conflit `PlantInstance`)
Deux classes portent ce nom :
- `core/PlantData.cs:PlantInstance` (data) — utilisée partout
- `plants/PlantInstance.cs` (stub Node Godot vide) — pas utilisée

Décision recommandée : **renommer le stub Godot en `PlantNode`**
(`plants/PlantNode.cs:partial class PlantNode : Node2D`). Plus
descriptif : c'est le node Godot qui représente visuellement une
`PlantInstance` data. Garder la convention dans tous les autres
fichiers `*Node` (cf. `TileNode`, `HouseNode` à venir).

### T6. Migration des stubs vides
Pour chaque stub C# en `plants/`, `ui/`, `visuals/`, `world/SoilField.cs`,
`SeedBankSystem.cs` :
- Soit le **migrer dans namespace `Symbiose`** et lui donner un
  squelette propre
- Soit le **supprimer** s'il n'est plus pertinent (`SoilField.cs` est
  douteux puisque les champs sol sont dans `EcoFields`)

À discuter avec Nico avant suppression.

### T7. Lancer le tout
- `dotnet build` côté C# (Godot 4.6 .NET appelle ça en interne)
- Lancer la scène `Main.tscn` dans Godot
- Critère : la console Godot affiche les signaux de phases qui
  s'enchaînent correctement (logs de debug à laisser dans `TurnSystem`
  pour ce sprint)

---

## Pièges connus

- **Godot 4.6 .NET autoload** : la déclaration se fait dans
  `project.godot` section `[autoload]`. Actuellement seul
  `SpriteLoader` y est. Si tu y ajoutes `GameManager`, le projet ne
  doit pas casser à l'ouverture.
- **Signals Godot en C#** : utiliser `[Signal]` delegate + EmitSignal.
- **Sérialisation** : préparer mais ne pas implémenter complètement —
  attendre la décision du Sprint conception bis sur le format de save.
- **Pas de gameplay actif** dans ce sprint — juste les phases qui
  s'enchaînent dans le vide. La simulation vient au Sprint 3.

---

## À produire à la fin

- [ ] `Main.cs` propre (namespace, classe `Main`)
- [ ] `Main.tscn` nouvelle
- [ ] `core/GameManager.cs` minimal mais utilisable (singleton, état)
- [ ] `core/TurnSystem.cs` minimal mais utilisable (phases + signaux)
- [ ] `core/EcologySystem.cs` squelette branché sur les signaux
- [ ] `plants/PlantNode.cs` (anciennement `PlantInstance.cs`)
- [ ] `project.godot` mis à jour (autoload + main_scene)
- [ ] `journal.md` : dettes D7, D8, D9 marquées ✅ levées (au moins
      partiellement), nouvelle entrée datée
- [ ] **Commit** dédié, ex :
      `Sprint 2 : fondations d'orchestration C#`
- [ ] Proposer Sprint 3 (portage simulation) à Nico

---

## Critère de fin

Au lancement de Godot :
1. `Main.tscn` se charge
2. Le jeu démarre en phase planification, attend une action
3. Une action de Nico (touche `Espace` par exemple) lance la phase
   saison : le timer démarre, 13 semaines simulées passent en 13 minutes
4. La console affiche un log clair des signaux
5. Pas d'exception C# au build ni au runtime
