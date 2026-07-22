# Tronçon ② — LOD organes intermédiaire + culling préventif

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` +
> `docs/perf/lod/conception_perf_rendu_plantes.md`. **Dépend du tronçon ①**
> (constante `SegmentDetailMinZoom`, pompe `RedrawAllPlants` déjà en place).
> Rendu/vue **C# pur** : AUCUNE touche `data/code/`, **golden INTACT**. Filet :
> `dotnet build Symbiose.csproj`.

## Objectif

Deux leviers préventifs, écrits « d'emblée » (choix Nico), sans attendre le F5 :

1. **LOD organes intermédiaire** — les organes (feuilles par segment × 3-5
   lobes + nervures, fleurs, fruits) dominent le décompte de primitives. Entre
   ×4 et ×8, dessiner **les segments SANS les organes**. Le VRAI levier de ce
   tronçon.
2. **Culling explicite léger** — masquer (`Visible=false`) les plantes dont
   l'emprise projetée est entièrement hors viewport. **Ceinture** : Godot cull
   déjà les items hors-écran (cf. §3.4 du doc) → rester léger, ne pas sur-investir.

## À faire

### A. LOD organes intermédiaire — `visuals/PlantRenderer.cs`
- Ajouter `private const float OrganDetailMinZoom = 8f;` (commentaire : sous ×8,
  on garde la structure de bois mais on saute le feuillage — trop de primitives
  pour un gain visuel nul à cette distance).
- Dans `DrawSegments()` (PlantRenderer.cs), l'appel `DrawOrgans(collet);` doit
  être **conditionné** :
  `if (WorldView.CurrentZoom >= OrganDetailMinZoom) DrawOrgans(collet);`
  Laisser `DrawHighlight` et `DrawTendrils` INCHANGÉS (surbrillance de taille et
  vrille d'accroche restent utiles à tout zoom où les segments sont dessinés).
- La pompe `RedrawAllPlants` du tronçon ① (appelée à chaque `StepZoom`) couvre
  déjà le franchissement de ×8 → **rien à ajouter côté redraw**.

### B. Culling explicite — `world/WorldView`
Objectif : une plante entièrement hors du viewport ne doit rien coûter.
- Où : un balayage des `_plantNodes` réévalué **au move/zoom caméra** (pas chaque
  frame inutilement). Le plus simple et robuste : l'appeler depuis
  `UpdateCameraPan` (quand la caméra bouge) et `StepZoom`, plus une fois après
  `ApplySnapshot` (de nouvelles plantes peuvent naître hors champ).
- Test : projeter le **centre** de chaque plante (`node.Position`, déjà en canvas)
  et comparer au rectangle visible du viewport en canvas, élargi d'une **marge**
  couvrant la hauteur/étalement max d'une plante (réutiliser une marge généreuse,
  ex. `node`… pas de `PickExtentCm` ici car privé au renderer → utiliser une
  marge fixe en cm × `PxPerCmX`, ex. 400 cm, un grand arbre). Une plante dont le
  centre + marge est hors du rectangle → `node.Visible = false`, sinon `true`.
  ```csharp
  private void CullPlants()
  {
      if (_camera == null) return;
      Rect2 view = VisibleCanvasRect();          // à dériver du Camera2D
      float margin = 400f * PxPerCmX;            // grand arbre, en px canvas
      Rect2 grown = view.Grow(margin);
      foreach (var node in _plantNodes.Values)
          if (IsInstanceValid(node))
              node.Visible = grown.HasPoint(node.Position);
  }
  ```
  - `VisibleCanvasRect()` : centre = `_camera.Position`, demi-taille =
    `(_worldVp.Size / 2) / _camera.Zoom` (le viewport interne divisé par le zoom
    donne l'étendue canvas visible). Vérifier le nom exact du SubViewport
    (`_worldVp`) dans `WorldView.cs` et sa `Size`.
- ⚠️ **Ne pas** masquer via `QueueFree` (on ne détruit pas les nœuds, juste
  `Visible`). Un nœud invisible sort du dessin ET du YSort → coût nul.
- ⚠️ Le culling ne doit PAS casser le picking : `FindSegmentGlobal`/`FindPlant`
  itèrent `_plantNodes` indépendamment de `Visible` — une plante hors-écran n'est
  de toute façon pas sous le curseur, donc pas de régression. Ne rien changer au
  picking ici.

## Ce qu'il NE faut PAS faire

- Pas de `data/code/`, pas de pont, pas de Python, pas de test moteur.
- Pas de batching / MultiMesh (hors sujet, cf. doc §6).
- Ne pas re-toucher le seuil silhouette ×4 du tronçon ① ni la pompe de redraw.
- Ne pas transformer le culling en quadtree ou structure spatiale — ~500 nœuds,
  balayage linéaire au move/zoom, trivial (leçon perf : mesurer avant d'optimiser).
- Ne PAS lancer `test_epaisseur_500ans` (interdit).

## Vérification / definition of done

- `dotnet build Symbiose.csproj` compile.
- Relire : à ×4–×8 les segments sont dessinés sans organes ; à ×8+ les organes
  reviennent ; le culling met bien `Visible=false` sur une plante hors champ et
  `true` quand elle rentre (au pan/zoom).
- **Golden** : inchangé (rendu pur).
- **F5 Nico** : à ×4 l'inspection large doit rester fluide même sur un jardin
  dense ; au pan en zoom fort, pas de saccade ; les plantes hors-écran
  réapparaissent correctement en rentrant dans le cadre.

## Golden attendu

**INCHANGÉ.**
