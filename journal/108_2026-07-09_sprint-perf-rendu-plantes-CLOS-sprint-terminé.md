# 2026-07-09 — Sprint PERF : rendu des plantes (LOD silhouette) — CLOS

**Chantier 2/2 du diagnostic perf 2026-07-09.** Après avoir soldé le tick
moteur Python (D70, −91 %), le **5 FPS à ×1 en vue d'ensemble** venait du
**RENDU des PLANTES** côté C#/Godot : à l'an 3 du F5, ~9668 segments + des
milliers d'organes (feuilles/fleurs/fruits) par plante × ~500 plantes, chaque
`PlantRenderer._Draw` retenu par Godot et **rejoué au GPU chaque frame**. Le LOD
silhouette était **déjà codé mais mort** (`ZoomPalier` un `[Export]=16` jamais
mis à jour depuis le zoom réel). Sprint entièrement **rendu/vue C# pur** →
**golden INTACT par construction** (`24ec11e7…`, aucune touche `data/code/`),
`dotnet build` vert à chaque tronçon.

## Tronçons (①→③, exécutés par `/sprint-auto`)

- **① LOD silhouette câblé sur le zoom réel** (`58990ed`) — `PlantRenderer` lit
  `WorldView.CurrentZoom`, stub `[Export] ZoomPalier` supprimé, constante
  `SegmentDetailMinZoom = 4f`. Sous ×4 (vue d'ensemble, macro déjà off à
  `MinZoom=4`) chaque plante passe de ~50 lignes + N organes à **2 polygones de
  couronne** (surcharge `DrawCanopySilhouette(baseC)` : vivant teinté par
  symptôme, squelette en silhouette grise non teintée). Pompe `RedrawAllPlants()`
  (`WorldView.Snapshot.cs`) appelée par `StepZoom` (`WorldView.Camera.cs`) au
  franchissement de palier — miroir du `_lastZoomOk` de MacroLife. Le fix décisif
  du 5 FPS. Golden INCHANGÉ, build vert.

- **② LOD organes ×4–×8 + culling préventif** (`4106088`) — palier ×4–×8 = **bois
  seul** (`DrawOrgans` conditionné à `CurrentZoom >= OrganDetailMinZoom = 8f`) :
  le feuillage, gros du décompte de primitives, est sauté en vue rapprochée
  intermédiaire ; détail complet à ×8+. Culling explicite léger `CullPlants()` +
  `VisibleCanvasRect()` (`WorldView.Camera.cs`) : `node.Visible` selon l'emprise
  projetée dans le viewport (marge 400 cm), évalué au pan/zoom et en fin de
  snapshot. Ceinture au culling natif Godot (le VRAI levier de ② est le LOD
  organes). Golden INCHANGÉ, build vert.

- **③ Priorité de clic plante > maison** (`e771f69`) — AJOUT fonctionnel : le clic
  gauche résout la plante AVANT le hub-maison. `PointeUnePlante` (balayage des
  `_plantNodes` **visibles** → respecte le culling ②) testé avant `ClicSurMaison`
  dans `WorldView.Controls.cs` ; le hub ne s'ouvre que si aucune plante sous le
  curseur. `ContientCurseur` (`PlantRenderer`) teste l'appartenance à l'ellipse de
  couronne (même géométrie que `DrawCanopySilhouette`). Cliquer une plante contre
  la maison — devant ou derrière — n'ouvre plus jamais le hub. Golden INCHANGÉ,
  build vert.

## Bilan

- **Golden final `24ec11e7…`** — INCHANGÉ à chaque tronçon (rendu/picking C# pur,
  zéro touche `data/code/`). `dotnet build Symbiose.csproj` vert partout.
- **Refactor auto-léger : no-op** — fichiers touchés tous en zone verte
  (`PlantRenderer.cs` 266 LDC pur, `WorldView.Snapshot.cs` 224,
  `WorldView.Controls.cs` 160, `WorldView.Camera.cs` 102, tous 🟢).
- **Coût perf visé** : ~500 plantes × (~50 lignes + N organes) → ~500 × 2
  polygones en vue d'ensemble. Réduction d'ordre ~25× des primitives
  rejouées/frame. Cible : 5 FPS → 30+ FPS.
- Doc de conception : `docs/conception/CONCEPTION_PERF_RENDU_PLANTES.md`.

## Reste F5 = Nico (Godot pas sur la VM)

1. Fluidité en vue d'ensemble ×1 (cible 30+ FPS vs 5), lisibilité des silhouettes
   de couronne, bascule au (dé)zoom via la pompe.
2. À ×4 sur jardin dense = bois sans feuillage ; retour feuillage à ×8 ; pan en
   zoom fort sans saccade ; plantes hors-écran réapparaissant en rentrant dans le
   cadre (culling).
3. Cliquer une plante contre la maison (devant ET derrière) exécute le geste,
   jamais le hub ; clic maison hors de toute plante ouvre bien le hub (pas de
   régression). Jeunes semis à couronne minuscule = cliquables seulement de près.

Après le sprint : **push GitHub** (canal `infra_canal_git`) pour que Nico pull +
F5.
