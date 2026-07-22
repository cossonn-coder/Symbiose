# Architecture technique — Symbiose

Document de contexte (knowledge file). Décrit **où en est le code** au 2026-06-02. Vérifier contre `git log` et l'arborescence avant d'agir — ce snapshot vieillit.

---

## Moteur Python — source de vérité

Dossier `data/code/` (~2500 lignes). **`main.py` tourne** — il a simulé 500+ ans sans crash, c'est la référence comportementale.

| Fichier | Rôle |
|---|---|
| `models.py` | Hiérarchie classes, instances, tuiles, rondelles, `EFFECT_REGISTRY` |
| `fields.py` | `GridField`, `LightField`, `DisturbanceField`, `SeedBank`, `EcoFields` |
| `effects.py` | Système d'effets hybride probabiliste (mutations + résolveur) |
| `engine.py` | Boucle 52 semaines, succession, transitions saisonnières |
| `main.py` | Scénario test (5 plantes, 1 tuile, durée paramétrable) |

### Boucle `engine.py:tick_semaine` — 17+ étapes

1. Aléas début de saison
2. Spring flush (sem 1)
3. Lumière directionnelle
4. Hydrologie
5. Décomposition OM (cascade fresh → active → stable, modulée par microbiome)
6. Diffusion spatiale
7. Avancement stades
8. Effets weekly
9. Uptake racinaire (**spatial sur `root_plots` depuis le 2026-06-02**)
10. Mise à jour physiologie
11. Floraison (mi-saison)
12. Récolte (fin de saison active)
13. Conflits spatiaux
14. Perturbations écologiques
15. Banque de graines
16. Succession
17. Transition hivernale (sem 48-52)
18. Soil memory (fin de saison)

Plus, depuis le Sprint sol vivant : **dépôt d'exsudats** ∝ photosynthèse sur les `root_plots` à chaque tick (`_apply_exudates`).

---

## Architecture C# courante

Stack : **Godot 4.6 .NET, C# .NET 8.0**. Namespace `Symbiose` sur le gameplay. GDScript interdit.

### Fonctionnels (~1700 lignes)

| Fichier | Contenu |
|---|---|
| `core/PlantData.cs` | `GrowthStage`, `PlantData`, `PlantInstance` (data, pas Node Godot) |
| `core/GridField.cs` | `GridField`, `LightField`, `EcoFields` — **OM tri-compartiment, PathogenPressure, rain feedback** (plus avancé que Python à un moment, voir dette D10) |
| `core/TileData.cs` | `Tile`, `StakeSlot`, `ConflictNotification`, `HexToScreen` |
| `core/PlantCatalogue.cs` | 14 espèces dont indicatrices, avec `UnlockCondition` |
| `core/SpriteLoader.cs` | Autoload, chargement récursif `assets/sprites/` |

### Stubs vides (à écrire)

- `core/GameManager.cs`, `EcologySystem.cs`, `TurnSystem.cs`, `SeedBankSystem.cs`
- Tout `plants/`, `ui/`, `visuals/`, `world/SoilField.cs`
- `Main.cs` (la classe s'appelle encore `Node2d`, hors namespace)

### Non portés vers C#

- `effects.py` → dette D5
- `engine.py` (boucle 52 semaines + succession) → dette D6
- Logique sol vivant Python (uptake spatial, exsudats, microbiome→uptake bonus, `vitalite()`) → dette D24

---

## Échelle spatiale actée (Sprint conception éclairement, 2026-05-29)

- **1 plot = 50×50 cm**
- Monde 3×3 tuiles × (6×8 plots) = **432 plots = 12×9 m ≈ 108 m²**
- Le **plot** ne sert plus qu'à la **chimie du sol** (humidité, fertilité, microbiome, soil_memory…)
- La **position des plantes est continue** (pixel-sol `x_cm, y_cm`), plot-foyer = `floor(pos / 50 cm)`
- **Lumière** : grille pixel-sol **top-down cartésienne** à **2 cm/px** (~270 k px-sol monde, ~5,4 MB pour 5 floats/px)
- Empreintes plantes :
  - Canopée = disque rayon tabulé par stade (à calibrer en code)
  - Racines = rayon racinaire **continu** (cm → ensemble de plots exploités pour l'uptake). **Remplace** les `RootOffsets` discrets

---

## Données calibrage sprites

- Sprites tuiles **78×57** sur disque (et non 96×48 codé dans `TileGrid.cs` — dette D2)
- Sprites plantes : sheets 1408×768 (`tomates.png`, `haricot.png`, …) **non parsés** + PNG individuels parfois en RGB sans alpha (basilic — dette D3)
- Catalogue C# attend `tomato_*`, `basil_*`, `bean_*` — fichiers nommés en français (`basilic_*`, `tomates`, `haricot`) — dette D3
- **Pas de sprite maison à ce jour** — dette D4
- Sprite house attendu en style normand : calcaire gris, toit ardoise, volets bois, Montmartin-sur-Mer

---

## Sol vivant Python v4 (Sprint sol vivant, 2026-06-02)

**D10 levée côté Python.** Le sol est passé de **décor réactif** à **organisme**.

### OM tri-compartiment

`organic_matter` mono-compartiment → **`om_fresh` / `om_active` / `om_stable`** dans `EcoFields`, alignés sur `GridField.cs`. `tick_decomposition` en **cascade** :

- `OM_FRESH_DECAY = 0.08`
- `OM_ACTIVE_DECAY = 0.018`
- `OM_STABLE_DECAY = 0.0006`
- Modulé par le microbiome.
- Trois destinations sommant à 1.0 : **humification** (compartiment suivant), **minéralisation** (→ `fertilite`, principale sur `active`), **respiration** (perte nette).
- Nécromasse et résidus entrent par `om_fresh`. Aucune création de carbone.

### Racines spatiales

`_apply_uptake` boucle sur `plant.root_plots` (filtrés aux bornes), avec `share = 1/nb_plots` — on **répartit** la consommation, on ne la duplique pas. Idem pour les enrichissements `inject_field` « local » dans `effects.py`. La **compétition souterraine** devient émergente.

### Boucle rhizosphère

`_apply_exudates` (chaque tick) : chaque plante vivante dépose des **exsudats** ∝ photosynthèse (lumière reçue × surface foliaire × santé) sur ses `root_plots` — l'essentiel au `microbiome`, fraction `EXUDATE_OM_SHARE = 0.15` à `om_fresh`.

**Rétroaction** : le microbiome donne un **bonus d'uptake fertilité** (`UPTAKE_MICRO_BONUS = 0.40`, borné).

**Universalisation** : suppression du scripting `microbiome` par famille (Fabaceae, Medicago). Le microbiome émerge des exsudats de **toutes** les plantes. Les Fabaceae gardent uniquement leur fixation N₂ → `fertilite`.

**Bornage anti-emballement** : le dépôt microbiome décroît en ×(1 − micro_norm), la boucle converge au lieu d'exploser.

### Puits microbien (Consolidation 2026-06-02)

Mortalité microbienne modulée par la disponibilité de carbone frais : `famine = 1 − min(1, om_fresh/MICROBE_FOOD_REF)` (0 si rassasié, 1 si épuisé) ; `microbiome *= 1 − MICROBE_DECAY_MAX * famine`.

Constantes : `MICROBE_FOOD_REF = 1.0`, `MICROBE_DECAY_MAX = 0.006` (0.015 d'abord testé, trop violent).

Résultat : le microbiome devient un **solde** apports (exsudats/OM) − pertes. Monte sous couvert végétal, redescend sur sol nu.

### Vitalité dérivée

`EcoFields.vitalite(r, c)` — **grandeur dérivée, jamais stockée** (respecte la décision de design « pas de nouveau champ pour le Qi »). Combinaison bornée [0,1] de microbiome, `om_active`, `fertilite`, structure (`om_stable`), moins la perturbation. Intégrée aux logs de saison et au bilan final de `main.py`. Préfigure la **Vigueur (D11)**.

### Mycorhizes différées

Chantier C de l'étude sol vivant — réseau mycorhizien (graphe inter-plantes, partage eau/nutriments) — **différé** en extension future (palier de maîtrise avancé), hors Sprint 3.

---

## Backlog sprints

Chaque sprint a un **kickoff autosuffisant** dans `sprints/`. Format : « lis `sprints/sprint_X.md` » suffit à ouvrir une session.

| Sprint | Kickoff | État |
|---|---|---|
| Mini-sprint succession (D25 : pionnier → prairie) | `sprint_succession.md` | À démarrer |
| Sprint 1 — recalibrage visuel + grille 3×3 + maison | `sprint_1_recalibrage_visuel.md` | À démarrer |
| Sprint 2 — orchestration C# (Main, GameManager, TurnSystem) | `sprint_2_orchestration.md` | Bloqué par Sprint 1 |
| Sprint éclairement (Z7, D20-D21 : ombres pixel + pérennes) | `sprint_eclairement.md` | À démarrer (peut absorber Sprint 3) |
| Sprint génétique/reproduction (Z7, D17+D22) | `sprint_genetique.md` | À démarrer après éclairement |
| Sprint 3 — portage simulation Python → C# (D5/D6) | `sprint_3_portage_simulation.md` | Bloqué par Sprint 2 |
| Sprint 4 — Vigueur, paliers, encyclopédie, carnet, magazine, foyer | `sprint_4_mecaniques_conception.md` | Bloqué par Sprint 3 + conception bis |

### Sprints terminés

- ✅ **Sprint 0** (2026-05-29) — gel et infrastructure documentaire
- ✅ **Sprint conception** (2026-05-29) — 12 décisions structurantes (vision actée)
- ✅ **Sprint conception bis** (2026-05-29) — 6 zones blanches refermées
- ✅ **Zone Z7** (2026-05-29) — éclairement spatial pixel-exact, conception close
- ✅ **Sprint conception éclairement & reproduction** (2026-05-29) — recadrage Z7, Option A
- ✅ **Sprint sol vivant** (2026-06-02) — D10 levée côté Python (OM v4 + racines spatiales + rhizosphère + vitalité)
- ✅ **Consolidation sol vivant** (2026-06-02) — puits microbien modulé par la famine
- 🟡 **Kickoff mini-sprint succession** (2026-06-02) — diagnostic D25 posé

---

## Mots de passe rapides du projet

- **`game_state`** (Python `engine.py`) : dict global = état complet. À porter en C# comme singleton `GameManager`.
- **`EcoFields`** : conteneur de tous les champs sol (`humidite`, `fertilite`, `microbiome`, `om_*`, `soil_memory`, `disturbance`).
- **`SeedBank`** : à scinder en `SeedBank-sol` (intrinsèque terrain) + `SeedBank-joueur` (transportable) — dette D17.
- **`PlantInstance`** : conflit de nom — data dans `core/PlantData.cs`, stub Node Godot dans `plants/PlantInstance.cs`. Renommer le stub en `PlantNode` (dette D9).
- **`EFFECT_REGISTRY`** : registre Python décoré `@register_effect`. À porter en `EffectRegistry.cs`.
- **`LightField` v2** = grille pixel-sol top-down + ombres-capsules par stade + 4 tranches solaires + intégrale.

---

## Pièges connus / dettes critiques

- **D2 — Mismatch tuile 78×57 ↔ 96×48 codé** : décalages d'affichage garantis. À trancher au Sprint 1.
- **D3 — Mismatch noms sprites FR/EN** : catalogue C# ne trouve aucun fichier. Renommer fichiers OU catalogue. Conseil : modifier le catalogue (FR = langue projet).
- **D4 — Sprite maison absent** : pièce centrale du design 3×3. À générer (Aseprite ou IA).
- **D8 — `Main.tscn` obsolète** : Node vides en français, à supprimer/refaire au Sprint 2.
- **D9 — Conflit `PlantInstance`** : renommer le stub Godot en `PlantNode`.
- **D10 — Divergence Python/C#** : **levée côté OM** au Sprint sol vivant. Reste `PathogenPressure` (C# seul) à réconcilier au Sprint 3.

---

## Conventions

- **Pixel art** : filtre `Nearest` partout (réglé dans `project.godot`).
- **Résolution** 1920×1080.
- **Zoom** par paliers entiers ×4 / ×8 / ×16 / ×32 — jamais de fraction.
- **Boucle hybride** : phase planification en temps figé ↔ phase saison de 15 minutes en temps réel (1 semaine = 60 secondes).
- **Sauvegarde** : JSON lisible, un seul save par profil, auto au passage de saison.
- **Déterminisme** : seed global + `_hash_noise` pour les champs déterministes (disturbance, succession).
- **Git** : à jour avant tout sprint code (Nextcloud a déjà perdu des fichiers en synchro le 2026-05-29).
