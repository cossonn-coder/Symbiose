# CONCEPTION — Perf du rendu des plantes (LOD silhouette + picking)

> Figé le 2026-07-09 (skill `/conception`). Chantier 2/2 du diagnostic perf
> 2026-07-09 (mémoire `perf_profile_simulation`). **Rendu / vue C# pur** : aucune
> touche à `data/code/`, **golden INTACT par construction**, philo #1-#7 non
> concernée (on ne change AUCUN comportement écologique, seulement le nombre de
> pixels dessinés et l'ordre de résolution d'un clic).

## 1. Problème

À l'an 3 du F5 (i5-4200H 2C/2014, iGPU HD 4600), la vue d'ensemble à ×1 tombe à
**5 FPS**. Le moteur Python n'est plus en cause (tick 861 ms depuis D70) : le
goulot est le **rendu des plantes** dans Godot.

- **~500 plantes**, **9668 segments** de bois, **+ des milliers de polygones
  d'organes** (feuilles dessinées *par segment × 3-5 lobes/folioles + nervures*,
  fleurs 5 pétales, fruits). Les organes **dominent** le décompte de primitives.
- **Un `PlantRenderer` (Node2D) par plante**. `_Draw` ne tourne que sur
  `QueueRedraw` (snapshot, survol) → Godot **retient** les primitives et les
  **rejoue au GPU chaque frame**. Le coût par frame = rejeu de tout ce corpus de
  primitives par le rendering server. C'est ça, le 5 FPS.
- La **vie macro** (14229 entités) est déjà LOD-off à ×1 (`MinZoom=4`,
  MacroLife.cs). En vue d'ensemble, **les plantes sont donc le seul coupable**.

## 2. Constat clé — le remède est déjà écrit mais débranché

`PlantRenderer.DrawCanopySilhouette()` remplace toute la plante par **2
`DrawColoredPolygon`** (base ombrée + calotte éclairée) et **saute tout** (return
avant `DrawOrgans`). Il est piloté par `if (ZoomPalier <= 4)` — mais `ZoomPalier`
est un `[Export] = 16` **jamais mis à jour depuis le zoom réel** (« TODO brancher
sur le vrai zoom caméra »). → la silhouette ne s'affiche **jamais**.

Les **8 autres couches** (MacroLife, Mulch, Litter, LeafLitter, Couverture,
Carpophore, Forager, et déjà `PlantRenderer.Organs.cs` pour la forme des
feuilles) LODent correctement sur `WorldView.CurrentZoom` (`MinZoom = 4f`). Le
renderer plante est **le seul oublié au niveau silhouette**.

→ Le chantier n'est PAS « inventer du batching » : c'est **câbler le LOD
existant** et ajouter un palier intermédiaire.

## 3. Décisions de conception

### 3.1 Seuil de LOD (arbitré Nico)
- `CurrentZoom < 4` → **silhouette** (2 polygones), organes et segments sautés.
- `4 ≤ CurrentZoom < 8` → **segments SANS organes** (palier intermédiaire).
- `CurrentZoom ≥ 8` → **détail complet** (segments + organes), inchangé.

Aligné sur le `MinZoom=4` du reste : à ×4 la vie macro s'allume, on entre en
« mode inspection ». Constantes nommées `SegmentDetailMinZoom = 4f` et
`OrganDetailMinZoom = 8f` (ajustables au F5).

### 3.2 Squelettes morts (arbitré Nico)
`DrawSkeleton` suit la **même** règle : sous `SegmentDetailMinZoom`, silhouette
grise (bois mort) au lieu de tous les segments. Cohérence + les arbres morts
peuvent être nombreux.

### 3.3 Redraw au franchissement de seuil
La représentation d'une plante change quand le zoom **franchit** ×4 ou ×8. Comme
`_Draw` ne tourne que sur `QueueRedraw`, `WorldView` doit **pomper** un
`QueueRedraw` sur tous les `_plantNodes` au franchissement (miroir du
`_lastZoomOk` de MacroLife). Coût ponctuel au palier, nul entre-temps.

### 3.4 Culling explicite (préventif, léger)
Bonus de ② : `Visible=false` sur les plantes dont l'emprise projetée est
entièrement hors viewport, réévalué au move/zoom caméra.
> **Avis honnête consigné** : Godot 4 cull déjà les canvas items hors-écran, et
> au zoom fort peu de plantes sont visibles → ce culling est surtout une
> **ceinture**. Le VRAI levier de ② est le **LOD organes** (§3.1). On garde le
> culling léger (choix « d'emblée » de Nico), sans en faire un gros morceau.

### 3.5 Priorité de clic plante > maison (ajout Nico)
Aujourd'hui le clic gauche teste `ClicSurMaison` **avant** toute plante :
```
if (ClicSurMaison(canvas)) OuvrirHubMaison(); else TryAction(canvas, …);
```
La maison a une **silhouette écran généreuse** (murs + toit + avant-toits) →
une plante plantée devant/derrière la maison voit son clic « volé » par le hub.

**Règle** : résoudre la plante **d'abord**. Le hub ne s'ouvre que si **aucune
plante** n'est sous le curseur :
```
if (PointeUnePlante(canvas))      TryAction(canvas, …);   // la plante gagne
else if (ClicSurMaison(canvas))   OuvrirHubMaison();
else                              TryAction(canvas, …);   // sol / rien
```
`PointeUnePlante(canvasMouse)` = le curseur touche le **corps visible** d'une
plante : silhouette de couronne projetée **OU** une branche dans la tolérance de
picking. Réutilise `PickExtentCm` (pré-filtre monde) + le hit-test existant
(`FindSegmentNear`) et un containment de la silhouette de couronne. Aucune
nouvelle géométrie inventée : mêmes primitives que ce qu'on dessine.

## 4. Coût perf

| Zoom | Avant | Après |
|------|-------|-------|
| ×0.5–×2 (vue d'ensemble) | ~500 × (~19 lignes + N organes) | ~500 × 2 polygones |
| ×4–×8 (inspection large) | segments + organes | segments seuls |
| ×8+ (loupe) | inchangé | inchangé |

Réduction d'ordre **~25×** des primitives rejouées par frame en vue d'ensemble.
Cible : **5 FPS → 30+ FPS** à ×1 (à valider au F5 de Nico). Le picking (§3.5) est
un simple ré-ordonnancement de tests déjà présents → coût neutre.

## 5. Découpage (3 tronçons, tous golden intact)

1. **① LOD silhouette** — câblage `CurrentZoom`, seuil ×4, silhouette +
   squelette, pompe de redraw. Le fix décisif du 5 FPS.
2. **② LOD organes intermédiaire + culling** — palier ×4–×8 sans organes ;
   culling explicite léger hors viewport.
3. **③ Priorité de clic plante > maison** — ré-ordonnancement du routage clic,
   prédicat `PointeUnePlante`.

Tous en **rendu/vue C# pur** → golden intact, pas de pont, pas de Python. La
règle « vue Godot en dernier tronçon » est satisfaite d'office (tout le sprint
est de la vue). **Validation finale = F5 de Nico** (la VM n'a pas Godot).

## 6. Ce qu'on ne fait PAS

- **Pas de batching / MultiMesh** : casserait le tri iso par-plante (YSort) pour
  un gain que le LOD obtient sans risque.
- **Pas de cache de sprite** (blit d'une texture pré-rendue, BACKLOG) : hors
  sujet ici, le LOD suffit.
- **Aucune modif moteur** : on ne change pas ce que la plante EST, seulement
  combien de pixels on en dessine selon le zoom.
