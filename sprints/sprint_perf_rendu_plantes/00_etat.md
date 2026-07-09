# Sprint PERF — rendu des plantes (LOD silhouette) — carnet de bord

> Carnet VIVANT (skill /conception §0bis). Reprise à froid = lire `CLAUDE.md`
> + ce fichier. Phase A (challenge) en cours — RIEN n'est figé tant que Nico
> n'a pas dit « OK ».

## Sujet

Chantier 2/2 du diagnostic perf 2026-07-09 (cf. mémoire `perf_profile_simulation`) :
le **5 FPS à ×1 en vue d'ensemble** vient du RENDU des PLANTES (C#/Godot), plus
du moteur Python (tick 861 ms depuis D70). À l'an 3 du F5 : **9668 segments** +
des **organes** (feuilles/fleurs/fruits) par plante, ~500 plantes, **un `_Draw`
par plante**. La vie macro (14229) est déjà LOD-off à ×1 (`MinZoom=4`).

## Diagnostic technique (fait, lecture code)

- **`PlantRenderer._Draw`** ne tourne QUE sur `QueueRedraw` (à chaque snapshot /
  survol), pas par frame → Godot **retient** les primitives et les **rejoue au
  GPU chaque frame**. Le coût par frame = **rejeu de ~9668 lignes larges +
  milliers de polygones d'organes** par le rendering server. C'est ça le 5 FPS.
- **Ampleur des organes** : `DrawOrgans` dessine des feuilles **par segment ×
  n lobes/folioles + nervures** (PlantRenderer.Leaf.cs), + fleurs (5 pétales) +
  fruits. Les organes **dominent largement** le décompte de primitives, loin
  devant les 9668 segments.
- **LOD silhouette DÉJÀ CODÉ mais MORT** : `DrawCanopySilhouette()`
  (PlantRenderer.cs:468) = **2 `DrawColoredPolygon`** (base ombrée + calotte
  éclairée) et **saute tout** (segments ET organes, `return` avant `DrawOrgans`).
  Déclenché par `if (ZoomPalier <= 4)` (:363) — mais `ZoomPalier` est un
  `[Export] = 16` (:40) **jamais mis à jour depuis le zoom réel** (« TODO
  brancher sur le vrai zoom caméra »). → la silhouette ne s'affiche JAMAIS.
- **Preuve que le pattern marche** : 8 couches (MacroLife, MulchLayer,
  LitterLayer, LeafLitterLayer, CouvertureLayer, CarpophoreLayer, ForagerLayer,
  et même `PlantRenderer.Organs.cs:439` pour la forme des feuilles) LODent déjà
  sur `WorldView.CurrentZoom` (`MinZoom = 4f`). Le renderer plante est le SEUL
  à ne pas le faire au niveau silhouette.
- **Culling** : `_objects` (parent des plantes) est un Node2D YSort. Godot 4
  cull déjà les canvas items hors viewport (zoom fort). Pas de culling explicite
  sur les plantes (contrairement à MacroLife, un seul node qui, lui, DOIT culler
  à la main). → culling explicite probablement INUTILE, à confirmer au F5.

## Recadrage (≠ énoncé initial)

L'énoncé listait « batching / culling / LOD ». Le diagnostic montre que **le LOD
silhouette (déjà écrit) est LA réponse** : à ×0.5/×1/×2 (vue d'ensemble, macro
déjà off), chaque plante passe de ~50 lignes + N organes à **2 polygones**.
- **Batching** : écarté (casserait le YSort iso par-plante ; inutile si le LOD
  suffit).
- **Culling explicite** : écarté par défaut (Godot cull déjà les items hors
  écran au zoom fort) ; à rouvrir SEULEMENT si le F5 le réclame.

## Décisions arrêtées (Nico, phase A)

- **Seuil LOD silhouette = `CurrentZoom < 4`** : silhouette à ×0.5/×1/×2,
  segments à partir de ×4 (aligné sur le `MinZoom=4` des autres couches ; à ×4 la
  vie macro s'allume = mode inspection). Constante nommée `SegmentDetailMinZoom`.
- **Squelettes morts en silhouette grise** sous le seuil (DrawSkeleton LODé aussi).
- **2 tronçons perf d'emblée** (pas d'attente F5) : LOD silhouette + LOD
  intermédiaire/culling préventif.
- **AJOUT fonctionnel** : priorité de clic **plante > maison** — cliquer sur une
  plante ne doit jamais ouvrir le hub-maison, que la maison soit devant ou
  derrière la plante. → 3ᵉ tronçon (picking).

## Plan de tronçons (proposé, à figer)

- **① LOD silhouette (perf, headline)** — `PlantRenderer` lit
  `WorldView.CurrentZoom` (retirer le stub `[Export] ZoomPalier`), silhouette si
  `< SegmentDetailMinZoom` (=4), appliquée AUSSI à `DrawSkeleton` (silhouette
  grise). `WorldView` pompe un `QueueRedraw` sur tous les `_plantNodes` au
  franchissement du seuil (miroir du `_lastZoomOk` de MacroLife). Golden intact.
- **② LOD intermédiaire + culling préventif (perf)** — palier ×4–×8 = segments
  SANS organes (skip `DrawOrgans`, les organes sont le gros du décompte) ; ×8+ =
  détail complet. + culling explicite léger : `Visible=false` sur les plantes
  dont l'emprise projetée est hors viewport (évalué au move/zoom caméra). Golden
  intact. NB honnête : Godot 4 cull déjà les items hors-écran → le culling
  explicite est surtout une ceinture ; le VRAI levier de ② est le LOD organes.
- **③ Priorité de clic plante > maison (vue/picking)** — dans le routage du clic
  gauche (`WorldView.Controls.cs`), résoudre la plante AVANT `ClicSurMaison` :
  n'ouvrir le hub que si AUCUNE plante sous le curseur. Prédicat `PointeUnePlante`
  = curseur dans l'emprise projetée d'une plante (réutilise `PickExtentCm` +
  containment silhouette/segment). Golden intact.

Tous les tronçons sont RENDU/VUE C# pur → **golden INTACT par construction**,
philo #1-#7 non concernée. La règle « vue Godot en dernier tronçon » est
satisfaite d'office (tout le sprint est de la vue).

## Coût perf estimé

Vue d'ensemble ×1 : ~500 plantes × (~50 lignes + N organes) → ~500 × 2 polygones.
Réduction d'ordre ~25× des primitives rejouées/frame. Cible : 5 FPS → 30+ FPS.
Golden : **INTACT par construction** (rendu C# pur, zéro touche à `data/code/`).

## Carte des tronçons (FIGÉE 2026-07-09, prête /sprint-auto)

- **①** `01_lod_silhouette.md` — câblage LOD silhouette (`CurrentZoom < 4`),
  squelette en silhouette grise, pompe `RedrawAllPlants` au `StepZoom`. Le fix
  décisif du 5 FPS. Golden INCHANGÉ.
- **②** `02_lod_organes_culling.md` — palier ×4–×8 = segments sans organes
  (`OrganDetailMinZoom=8`), + culling explicite léger (`Visible` hors viewport).
  Dépend de ①. Golden INCHANGÉ.
- **③** `03_clic_plante_prioritaire.md` — priorité de clic plante > maison :
  `PointeUnePlante` (ellipse de couronne, `ContientCurseur`) testé AVANT
  `ClicSurMaison`. Golden INCHANGÉ.

Doc de conception : `docs/conception/CONCEPTION_PERF_RENDU_PLANTES.md`.

## Avancement

- **① LOD silhouette — FAIT (2026-07-09, non commité)**. `PlantRenderer.cs` :
  stub `[Export] ZoomPalier` SUPPRIMÉ, constante `SegmentDetailMinZoom = 4f`,
  `_Draw` bascule silhouette ⟷ segments sur `WorldView.CurrentZoom < 4`
  (vivant ET squelette). Surcharge `DrawCanopySilhouette(Color baseC)` :
  vivant = `SymptomTint(CrownColor)`, squelette = `DeadWoodColor` (jamais
  teinté par un symptôme vivant). Pompe `RedrawAllPlants()` posée dans
  `WorldView.Snapshot.cs`, appelée par `StepZoom` (WorldView.Camera.cs) au
  franchissement de palier. `grep ZoomPalier` = vide.
  Golden **INCHANGÉ** (`24ec11e7…`, rendu C# pur). `dotnet build` **VERT**.
  Reste : **F5 Nico** (fluidité ×1, lisibilité silhouettes, retour détail ×8).
- ② LOD organes + culling — À FAIRE (`02_lod_organes_culling.md`).
- ③ Clic plante > maison — À FAIRE (`03_clic_plante_prioritaire.md`).

## §REPRISE

Tronçon ① CLOS côté VM (build vert + golden intact `24ec11e7…`), **non commité**
(Nico commit). Tous les tronçons sont **rendu/vue C# pur** → golden INTACT par
construction, aucun test moteur, aucune touche `data/code/`. Filet compil VM :
`dotnet build Symbiose.csproj`. Validation finale = **F5 de Nico** (Godot pas
sur la VM).

Prochaine étape : ② puis ③ (`/sprint-auto sprint_perf_rendu_plantes` reprend au
tronçon restant), ou commit + push de ① pour un F5 intermédiaire de Nico.
Après le sprint : push GitHub (canal `infra_canal_git`) pour que Nico pull + F5.
Fichiers cœur : `visuals/PlantRenderer.cs`, `world/WorldView.Camera.cs`,
`world/WorldView.Snapshot.cs`, `world/WorldView.Actions.cs`,
`world/WorldView.Controls.cs`.
