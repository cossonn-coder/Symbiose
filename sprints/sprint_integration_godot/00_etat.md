# Sprint Intégration Godot ↔ Python — kickoff & état partagé

> **Kickoff autosuffisant** (démarrage à froid). Ce fichier porte aussi la
> **conception actée** (Option B, validée par Nico le 2026-06-07 : « tes
> recommandations sont bonnes, on suivra ce chemin »). Source de vérité du
> moteur = **Python `data/code/`** ; ce sprint construit la **VUE Godot**, pas un
> second moteur. **GDScript INTERDIT, tout en C#, namespace `Symbiose`.**

## Ce qu'on construit, en une phrase
Faire **jouer/voir** le jardin dans Godot **sans réécrire le moteur** : Python
(moteur, source de vérité) tourne comme **sous-process**, émet l'**état du monde
en JSON**, Godot le **rend** et lui **renvoie les actions joueur**. On généralise
le pont déjà en place (`tools/export_structure.py` → `structure.json` →
`visuals/PlantRenderer.cs`).

## Décision d'architecture ACTÉE — Option B (Python moteur / Godot vue)
**Pourquoi B et pas « porter en C# » (A) :**
- Le moteur est **~7 500 lignes 100 % stdlib** (aucune dépendance tierce —
  vérifié) → se **gèle en un exécutable autonome** (PyInstaller/Nuitka), zéro
  Python à installer chez les joueurs. Le seul reproche fait à B s'effondre.
- **Source de vérité unique** (règle projet : « Godot une vue, aligner vers
  Python »). A dédoublerait le moteur → **divergence permanente** à re-porter à
  chaque évolution Python (7 500 lignes mûres, golden-protégées).
- **Budget temps réel énorme** : 1 semaine = 60 s réel, tick ≈ 177 ms Python
  (×339 de marge) → la sérialisation JSON + IPC est **négligeable**.
- **Déterminisme + debug** : le flux JSON est inspectable (≈ philo du save JSON
  lisible). Même seed → même run ; Godot peut enregistrer/rejouer.
- A ne se justifierait que pour shipper **un seul binaire natif** — le binaire
  gelé règle déjà ça. **Hybride** (porter plus tard un point chaud en C# si la
  perf serre) reste une porte de sortie, pas un prérequis.

## Protocole d'échange (direction actée, détails à figer en tranche 1)
- **Transport** : **sous-process + stdin/stdout, JSON ligne-délimité** (simple,
  debuggable, pas de port à gérer). Godot **pilote la boucle** (envoie des
  commandes, Python répond).
- **Charge utile** : **snapshot complet du monde** au départ (diffs = optimisation
  ultérieure si la taille gêne ; à mesurer). Schéma **versionné** (`engine_version`,
  comme le save). JSON **lisible**.
- **Python possède les RÈGLES** (validité d'une action, coût Vigueur, etc.) ;
  **Godot est « bête »** : il rend et transmet l'intention du joueur.

## Mapping de la boucle hybride (cf. CLAUDE.md « Boucle hybride »)
- **Phase planification (temps figé)** : Python au repos, Godot fait l'UI/
  l'interaction ; les actions « préparation » sont envoyées et validées.
- **Phase saison (15 min réel, 1 sem = 60 s)** : Godot demande « avance d'une
  semaine », Python ticke et renvoie le snapshot ; Godot **anime/interpole** le
  visuel entre deux snapshots hebdomadaires (tweens), la sim reste hebdo.
- **Save** : Python possède le save JSON (au passage de saison) → **converge avec
  le futur « sprint save global »** (naturellement Python). Godot le déclenche.

## Rendu — ce que Godot dessine du snapshot
Tuiles iso (monde) · plantes **procédurales** (porter `_iso` + structure ; les
**organes** `_draw_organs` du prototype Python SVG → C#) · **ombre de la maison**
· overlays de champs en **mode debug** (heatmaps) · **vie macro** (sprites
échantillonnés) · HUD/**notifications hiérarchisées** · plus tard encyclopédie/
carnet. Indices **visuels** d'abord (philo #5 : pas de chiffres en HUD primaire).

## État de départ Godot (ce qui existe déjà)
- **Fonctionnel** : `core/PlantData.cs`, `TileData.cs`, `GridField.cs`,
  `PlantCatalogue.cs` (14 esp.), `SpriteLoader.cs` ; `core/PlantStructure.cs` +
  `visuals/PlantRenderer.cs` (lisent `structure.json`, projection `Iso()` = portage
  de `_iso`) ; `world/TileGrid.cs` (affiche **1** tuile iso 6×8 + 4 plantes démo).
- **Stubs vides (15 lignes)** : `Main.cs` (classe `Node2d`, hors namespace !),
  `GameManager`, `TurnSystem`, `EcologySystem`, `SeedBankSystem`, `SoilField`,
  tout `plants/*`, `ui/*`, `LightOverlay`/`PlantAnimator`/`WindAnimator`.

## Découpage proposé en sous-sprints (vertical slices — révisable)
1. **Pont vivant minimal** : `tools/sim_server.py` (boucle stdin/stdout JSON :
   commandes `init(seed,config)` / `step_week` / `snapshot`) côté Python ; côté C#
   un `core/SimBridge.cs` qui lance le sous-process, parse le snapshot. **But :
   prouver le tube** (un snapshot s'affiche, une semaine avance). Réutilise le
   schéma `structure.json`. Golden Python **intact** (on lit le moteur, on n'y
   touche pas). → **Kickoff prêt (2026-06-10) : `01_pont_minimal.md`**
2. **Monde statique rendu** : Godot dessine le **monde complet** du snapshot
   (tuiles hétérogènes + maison + plantes procédurales + ombre) — **corrige
   D2/D3/D8** au passage (tuiles **78×57**, noms de sprites, scène principale
   propre). Reprend `TileGrid`/`PlantRenderer`.
3. **Saison animée** : bouton « avancer », `step_week` ×N, **interpolation**
   visuelle entre snapshots ; cycle de saison + auto-save déclenché.
4. **Actions joueur** : clic → commande Python (planter, arroser, tailler,
   manger…) ; Python valide + applique (coût Vigueur), renvoie le snapshot.
5. **Organes + overlays + vie macro** : porter `_draw_organs` en C#, heatmaps
   debug, sprites auxiliaires/nuisibles échantillonnés.
6. **Packaging** : gel PyInstaller du moteur en binaire, Godot le spawne ;
   build exportable pour amis/famille.
*(HUD riche, encyclopédie, carnet, pages secrètes = au-delà, sprints dédiés.)*

## Contraintes & pièges
- **Pas de `dotnet` CLI ici** → **Nico build/lance dans Godot sur son poste**,
  Claude code et Nico fait les retours (boucle plus lente, prévoir des tranches
  vérifiables).
- **GDScript interdit, namespace `Symbiose`, déterminisme** (seed global).
- `Main.cs` = `Node2d` hors namespace (D8) ; tuiles **78×57** ≠ 96×48 codé dans
  `TileGrid.cs` (D2) ; noms sprites attendus ≠ disque (D3) ; `Main.tscn` obsolète.
- Le moteur Python **ne doit pas être modifié pour Godot** : si Godot a besoin
  d'une donnée, on l'**expose en lecture** (nouveau champ du snapshot), on ne
  change pas la logique → golden intact.

## Questions ouvertes (à trancher au fil, défaut sobre + signaler)
- **Granularité du snapshot** : complet vs diffs (mesurer la taille/latence à la
  tranche 1 avant d'optimiser).
- **Format des commandes joueur** (verbe + cible + params) : à figer en tranche 4.
- **Cycle de vie du sous-process** : un process persistant (état en mémoire) vs
  relancé (rejoue depuis le save) — défaut **persistant**, à confirmer.
- **Où vit le save** : ici (Python) ou attendre le « sprint save global » — défaut
  **Python ici**, convergent.

## Lien dette
Lève progressivement **D24** (le « portage C# » devient « pont », plus un portage
intégral) + **D2/D3/D4/D8** (rendu/scène). À refléter dans `DETTE.md`/`BACKLOG.md`
quand le sprint démarre.
