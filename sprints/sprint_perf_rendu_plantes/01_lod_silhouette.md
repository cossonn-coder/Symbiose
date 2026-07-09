# Tronçon ① — LOD silhouette des plantes (le fix décisif du 5 FPS)

> Kickoff autosuffisant. Lire d'abord `CLAUDE.md` (racine) + `00_etat.md` +
> `docs/conception/CONCEPTION_PERF_RENDU_PLANTES.md`. Rendu/vue **C# pur** :
> **AUCUNE** touche à `data/code/`, **golden INTACT** (rien à re-figer, aucun
> test moteur à relancer). Filet de compil : `dotnet build Symbiose.csproj` sur
> la VM (le F5 visuel reste à Nico).

## Objectif

Brancher le LOD silhouette **déjà écrit** mais mort : à zoom faible, chaque
plante se dessine en **2 polygones** (`DrawCanopySilhouette`) au lieu de tous ses
segments + organes. C'est ce qui fait passer la vue d'ensemble de 5 FPS à ~30+.

## Contexte technique (déjà vérifié)

- `visuals/PlantRenderer.cs` a un `[Export] public int ZoomPalier = 16;`
  **jamais mis à jour** depuis le zoom réel (commentaire « TODO brancher »). Son
  `_Draw` fait `if (ZoomPalier <= 4) { DrawCanopySilhouette(); return; }` — donc
  la silhouette ne s'affiche JAMAIS.
- Le vrai zoom vit dans `WorldView.CurrentZoom` (`static`, float : 0.5→32).
  `PlantRenderer.Organs.cs:439` le lit DÉJÀ pour la forme des feuilles → le
  pattern « lire `WorldView.CurrentZoom` dans `_Draw` » est validé et utilisé.
- `MacroLife.cs` montre le pattern de **pompe de redraw au franchissement de
  seuil** : un champ `_lastZoomOk`, comparé chaque frame à
  `WorldView.CurrentZoom >= MinZoom`, qui déclenche UN redraw au basculement.
- `_Draw` d'une plante ne tourne QUE sur `QueueRedraw` (pas par frame) : sans
  pompe, une plante déjà dessinée en segments RESTERAIT en segments après un
  dézoom. La pompe est donc indispensable.

## À faire

### A. `visuals/PlantRenderer.cs`
1. **Supprimer** le `[Export] public int ZoomPalier = 16;` (stub mort, référencé
   nulle part ailleurs — vérifier par `grep -rn ZoomPalier --include=*.cs`, il ne
   reste que la déclaration et le test dans `_Draw`).
2. Ajouter une constante `private const float SegmentDetailMinZoom = 4f;`
   (commentaire pédagogique : sous ×4 on est en vue d'ensemble, la vie macro est
   elle aussi off — on ne rastérise pas chaque brindille).
3. Dans `_Draw`, remplacer `if (ZoomPalier <= 4)` par
   `if (WorldView.CurrentZoom < SegmentDetailMinZoom)`.
4. **Squelette** : dans `_Draw`, le court-circuit `if (!string.IsNullOrEmpty(
   _deadStade)) { DrawSkeleton(); return; }` s'exécute AVANT le test LOD. Le
   modifier pour que, sous le seuil, le squelette passe aussi en silhouette
   grise. Le plus simple : ajouter dans `DrawSkeleton` (ou juste avant son appel)
   un branchement `if (WorldView.CurrentZoom < SegmentDetailMinZoom) {
   DrawCanopySilhouette en gris ; return; }`.
   - Réutiliser `DrawCanopySilhouette` mais en **bois mort** : le plus propre =
     paramétrer la couleur de base de la silhouette. Introduire une surcharge
     privée `DrawCanopySilhouette(Color baseColor)` et faire l'actuelle
     `DrawCanopySilhouette()` appeler `DrawCanopySilhouette(SymptomTint(CrownColor))`.
     Le squelette appelle `DrawCanopySilhouette(DeadWoodColor)`. Ne PAS teinter
     le bois mort par les symptômes (une plante morte n'a plus de symptôme vivant).

### B. `world/WorldView` — pompe de redraw au franchissement de seuil
Le LOD des plantes a DEUX seuils qui les concernent : `SegmentDetailMinZoom` (×4,
ce tronçon) et `OrganDetailMinZoom` (×8, tronçon ②). Pour ne pas y revenir,
poser une pompe qui redessine toutes les plantes dès que le zoom **franchit un
palier** (le plus simple et robuste : redessiner à CHAQUE changement de palier de
zoom, il n'y en a que 7 et le redraw d'un dézoom est justement ce qu'on veut).

- Le seul endroit qui change le zoom est `StepZoom(int dir)` dans
  `world/WorldView.Camera.cs` (et `FrameCamera` à l'init). Après la mise à jour de
  `CurrentZoom` dans `StepZoom`, ajouter un appel `RedrawAllPlants();`.
- Implémenter `RedrawAllPlants()` (partial le plus naturel : `WorldView.Snapshot.cs`
  qui détient déjà `_plantNodes`, ou un petit ajout dans `WorldView.Camera.cs` —
  au choix, garder le fichier sous la bande de taille) :
  ```csharp
  private void RedrawAllPlants()
  {
      foreach (var node in _plantNodes.Values)
          if (IsInstanceValid(node)) node.QueueRedraw();
  }
  ```
  Commentaire pédagogique : le LOD change la représentation d'une plante ; comme
  `_Draw` ne tourne que sur `QueueRedraw`, on force un redraw de toutes les
  plantes au changement de palier (~500 `QueueRedraw`, ponctuel, invisible).

## Ce qu'il NE faut PAS faire

- Ne PAS toucher `data/code/`, le pont, le protocole, un test moteur. Zéro Python.
- Ne PAS changer la géométrie de `DrawCanopySilhouette` (formes par silhouette
  d'espèce) ni celle de `DrawSegments` : on ne fait que **choisir** l'un ou
  l'autre selon le zoom.
- Ne PAS introduire le palier organes ×8 ici (c'est le tronçon ②).
- Ne PAS relancer `test_epaisseur_500ans` (interdit, cf. `CLAUDE.md` mémoire).

## Vérification / definition of done

- `dotnet build Symbiose.csproj` **compile sans erreur** (filet VM).
- `grep -rn ZoomPalier --include=*.cs` ne renvoie **plus rien**.
- Relire : sous ×4 le chemin silhouette est pris (vivant ET squelette), à ×4+ les
  segments. La pompe part bien depuis `StepZoom`.
- **Golden** : inchangé par construction (aucune modif moteur). Le lancer une
  fois pour l'attester est superflu — aucun fichier `data/code/` n'a bougé.
- **F5 Nico** (hors VM) : à ×1, la vue d'ensemble doit être fluide (cible 30+
  FPS) et les plantes lisibles en silhouettes ; à ×8 le détail revient.

## Golden attendu

**INCHANGÉ.** Aucune raison de re-figer (rendu pur, zéro moteur).
