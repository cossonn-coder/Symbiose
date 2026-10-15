# T2 — Pré-cuisson des plantes PAR INSTANCE + file de re-cuisson étalée

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, `docs/rendu/pixelart/conception_jardin_vivant.md` §3.

## Objectif
Remplacer « redessin vectoriel de la plante » par « affichage d'une image
cuite de CETTE plante ». **Aucun changement visible** attendu à ce tronçon
(même image qu'avant, à la palette T1 près) : on pose l'infrastructure que T3
(8 poses de flexion) et T4/T5 (variantes météo) rempliront.

## Contexte vérifié
- `visuals/PlantRenderer.cs` (Node2D, 279 LDC) + partials `.Organs` (317 🟡),
  `.Leaf`, `.LeafOutline`, `.Flower`, `.Palette` : `_Draw()` vectoriel,
  `QueueRedraw()` appelé par les setters (`SetStructure`, `SetSymptoms`,
  `SetVitality`, `SetSkeleton`, `SetSilhouette`…). Dessin en coordonnées écran
  via `WorldView.WorldToScreen` au zoom `WorldView.CurrentZoom` ; LOD ;
  pompe de redraw au palier de zoom dans `WorldView.Camera.StepZoom`.
- Instances : `world/WorldView.Snapshot.cs:216` (`_plantNodes`) et
  `WorldView.Conteneurs.cs:180` (plantes en pot).
- Le snapshot porte par plante `floraison`, `automne`, `leaf_symptoms`,
  `vitality`… → déjà consommés par les setters.

## Modèle (intention)
- **Le dessin existant EST le pinceau** : la cuisson rejoue le même code de
  dessin (mêmes primitives, mêmes palettes, même LOD) vers une image, au
  palier de zoom courant. Ne pas réécrire le dessin des feuilles/fleurs.
- Une plante = **un jeu de poses** (à ce tronçon : 1 pose, celle d'aujourd'hui ;
  l'API prévoit `poseCount` = 8 pour T3 et des variantes pour T4/T5).
- **Invalidation** : tout setter qui appelait `QueueRedraw` marque la plante
  « sale » au lieu de redessiner ; changement de palier de zoom = toutes
  sales (même file, pas de pic).
- **File de re-cuisson à BUDGET PAR FRAME — exigence Nico : JAMAIS toutes les
  plantes au même moment.** Budget en plantes ET/OU en ms par `_Process`,
  ordre = plantes visibles à l'écran d'abord (frustum caméra), puis le reste.
  Une plante sale garde son ancienne image jusqu'à sa cuisson (jamais de trou,
  jamais de plante invisible). Une semaine simulée (60 s) salit tout le
  jardin : la file doit se vider en ~1-2 s sans chute de FPS.
- **Technique de cuisson** : à choisir et MESURER par l'agent. Pistes Godot 4
  `gl_compatibility` : SubViewport(s) d'atlas en `UpdateMode.Once` avec
  `AtlasTexture` par pose ; ou rastérisation CPU dans une `Image`. Éviter
  les lectures GPU→CPU synchrones par plante (`GetImage()` bloquant) dans la
  boucle de jeu. Prévoir la libération (plante morte/retirée).
- Ancrage : l'image est positionnée au collet (même point qu'aujourd'hui) ;
  Y-sort, ombre (`PlantShadow.cs`), étiquettes, picking et teinte LOD debug
  (`ApplyLodTint`) inchangés.

## Mesures à graver dans `00_etat.md`
Mo de cache (jardin de démo + un banc dense), ms de cuisson par plante
(herbacée / arbre), budget/frame retenu, durée de vidage de la file après un
tick, FPS avant/après (le rapport perf existant `WorldView.PerfReport.cs` / F4
peut servir). Chiffres avec leur limite entre crochets (règle CLAUDE.md global).

## Critère de réussite
`dotnet build` vert ; captures T0 avant/après **visuellement identiques**
(regarder les PNG, comparer pixel si possible) à ×4, ×8, ×16 ; FPS ≥ avant ;
aucun pic à la semaine simulée. Question F5 Nico : « rien n'a changé et ça
reste fluide ? ».

## NE PAS
- Recuire toutes les plantes dans la même frame (ni au tick, ni au zoom).
- Réécrire le dessin des organes ; partager une image entre deux plantes
  (pré-cuisson PAR INSTANCE, même espèce ≠ même image).
- Toucher au moteur Python / golden ; GDScript ; `test_epaisseur_500ans`.
- Dépasser 400 LDC : la cuisson + la file vivent dans des fichiers dédiés
  (ex. `visuals/PlantBaker.cs`, `visuals/BakeQueue.cs`), `PlantRenderer.cs` ne
  grossit pas.
