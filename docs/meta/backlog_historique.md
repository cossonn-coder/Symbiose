# Backlog — archives

> Sections **historiques** de [`BACKLOG.md`](../../BACKLOG.md), reprises
> **verbatim**. Elles racontent une chronologie (sprints 0 à 4, zones de
> conception closes), pas un thème — d'où leur regroupement ici plutôt que
> leur dispersion par thème.

### Sprint 0 — gel et infrastructure documentaire — TERMINÉ ✅
- [x] État des lieux complet
- [x] `CLAUDE.md` projet
- [x] `journal.md` initial
- [x] `.gitignore` étendu
- [x] Système mémoire initial
- [x] Premier commit git

### Sprint conception — redéfinition de la vision du jeu — TERMINÉ ✅
- [x] 12 décisions structurantes actées
- [x] `journal.md` enrichi
- [x] `CLAUDE.md` réécrit (vision actualisée)
- [x] Fichiers mémoire rafraîchis
- [x] Commit dédié

### Sprint conception bis — zones blanches restantes — TERMINÉ ✅
- [x] Cycle de sauvegarde (run éternel) — JSON, auto-save par saison, seed persistée
- [x] Mécanique de gestion des aléas météo — signes diégétiques + prépa/réaction
- [x] Multiples jardins / multijoueur — avatar transportable, terrain intrinsèque
- [x] Lore / narration — jardinier silencieux + 3 voix (encyclopédie / carnet / pages secrètes)
- [x] Conditions de panne sèche — succession spontanée + manger + régen croissante
- [x] Difficulty / accessibilité — Options modulaires + debug libre + pictogrammes

### Zone Z7 — éclairement spatial — CONCEPTION CLOSE ✅
- [x] Décisions actées (pixel exact, 4 tranches + intégrale, hauteurs cm,
      genetic_factor × growth_factor)
- [x] Audit botanique des 14 espèces actuelles
- [x] 5 arbres pérennes premiers calibrés
- [x] Kickoff sprint éclairement rédigé (`sprints/sprint_eclairement.md`)
- [x] **Recadrage conception (2026-05-29)** : Option A (lumière+plantes au
      pixel, sol au plot), échelle 50 cm / 2 cm/px, soleil astronomique,
      empreintes par stade, pérennes polymorphes, génétique biparentale par
      introgression. Voir entrée *Sprint conception éclairement & reproduction*.
- [x] **Implémentation scindée en deux sprints** : éclairement (D20-D21)
      puis génétique/reproduction (D17+D22)
- [x] Implémentation : les deux sprints dédiés sont terminés (Python)

### Sprint refactor structurel — TERMINÉ ✅ (2026-06-03)
- [x] Golden output déterministe (`tests/test_golden.py`, 3 tuiles / 100 ans)
- [x] `data/code/` réorganisé en paquets `plants/ world/ fields/ sim/` + `constants.py`
- [x] Succession extraite d'`engine` vers `sim/succession.py`
- [x] Tests déplacés dans `tests/`, shims supprimés, golden identique avant/après
- [x] `journal_archive/`, `DETTE.md`, `BACKLOG.md` ; déduplication `CLAUDE.md`

### Sprint 1 — recalibrage visuel
- [ ] Mesurer dimensions exactes de tous les sprites attendus
- [ ] Décider format final tuile (78×57 conservé, ou re-générer en 96×48)
- [ ] Générer sprite maison (calcaire gris, toit ardoise, volets bois)
- [ ] Réécrire `world/TileGrid.cs` pour grille 3×3 tuiles + maison centrale
- [ ] Aligner nomenclature sprites ↔ catalogue (`SpriteName` dans
      `PlantCatalogue.cs` ou renommage des fichiers)
- [ ] Vérifier en éditeur Godot que la grille s'affiche correctement

### Sprint 2 — fondations orchestration
- [ ] `Main.cs` propre, dans namespace `Symbiose`, classe `Main : Node2D`
- [ ] `core/GameManager.cs` — singleton état global, GameState analogue
      au `game_state` dict de Python
- [ ] `core/TurnSystem.cs` — phases (planification / saison)
- [ ] Nouvelle `Main.tscn` qui remplace le brouillon obsolète

### Sprint 3 — portage simulation
- [ ] Porter `sim/effects.py` → `core/EffectSystem.cs` (mutations + résolveur)
- [ ] Porter `sim/engine.py` + `sim/succession.py` → `core/EcologySystem.cs`
      (tick hebdo, succession, aléas, transitions saisonnières)
- [ ] Tests de cohérence : lancer 1 an de simulation côté Python ET C#
      avec mêmes seeds, comparer états finaux
- [ ] Porter la logique sol vivant (D24) : uptake spatial, exsudats,
      bonus microbiome→uptake, `vitalite()` dérivée
- [ ] Réconcilier le reste de D10 (`PathogenPressure` C# → Python)

> Extension future (palier de maîtrise avancé) : **chantier C — réseau
> mycorhizien** (`etude_sol_vivant.md` Partie 3), différé hors Sprint 3.

### Sprint 4 — affichage écologique
- [ ] `PlantNode.cs` — Sprite2D plante, ancrage bas-centre, ZIndex
- [ ] `CameraSystem.cs` — zoom par paliers ×4/×8/×16/×32 snap pixel-perfect
- [ ] `LightOverlay.cs` — ombre dynamique maison (Light2D + LightOccluder2D)
- [ ] Premier test bout-en-bout : 1 tuile + 5 plantes + 1 an simulé visible

### Idées longue traîne — non rattachées à un thème
> Liste héritée, laissée telle quelle faute de rattachement clair.

- Shop roguelike (inter-run et intra-run)
- Bilan écologique fin de run (narratif)
- Journal Connaissance (dans la maison)
- Vue loupe Z3 (gestes fins)
- Catalogue étendu 80–120 espèces
- Cartes événements (météo + narratifs)
- Sprint version physique (STL plantes, cartes MTG)
