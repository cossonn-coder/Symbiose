# T3 — Le plancher fixe de la frame

> Lire `CLAUDE.md`, `00_etat.md`, `docs/perf/lod/conception_rendu_visible.md` §2/§5.
> Vue C# pure. Golden intact.

## Objectif
Même avec tout le monde masqué, une frame coûte ~40 ms sur la VM. Couper le travail
qui tourne à chaque frame sans raison.

## Constat (profil `dotnet-trace`, ×0,5)
`WorldView._Process` (`world/WorldView.cs` ~l.410-445) appelle chaque frame
`UpdatePlantLabels`, `ObserveHoveredPlant`, `ObserveHoveredMacroLife`,
`UpdateContainerLabel`, `UpdateTailleHighlight`, `UpdateCurseur`, `UpdateSun`,
`UpdateGenesHover`… dont beaucoup rappellent `WorldMouseCanvas()` (≈10 sites :
`grep -n "WorldMouseCanvas()" world/*.cs`) → `Viewport.GetMousePosition` (coûteux sous
X11/VM, à ne pas sur-interpréter), puis `FindPlot` / `FindPlant`.
Couches plein écran : `world/SkyPanel.cs` (+ `Vignette`), `visuals/WeatherLayer.cs`
(enfant `WeatherSky`) — vérifier quand elles `QueueRedraw`.

## Modèle (intention)
1. **Souris lue une fois par frame** : position canvas et monde mises en cache en tête
   de `_Process`, consommées par tous les sites (les appels hors `_Process` — clic,
   zoom centré — peuvent garder un appel direct).
2. **Survol paresseux** : recalculer survol / étiquettes / losange / gènes seulement si
   la souris (px) ou la caméra (position, zoom, orientation) a changé, ou si un
   snapshot vient d'être appliqué. Sinon réutiliser le résultat précédent. Attention aux
   animations voulues (losange qui « respire » quand un geste est armé : il garde son
   rythme propre).
3. **Plein écran à la demande** : ciel, vignette, météo ne se redessinent que si leur
   état change ou s'ils animent réellement (pluie, neige, éclair, battement) ; au repos,
   zéro `QueueRedraw` par frame.
4. Profiler à nouveau (`dotnet-trace collect -p <pid> --profile dotnet-sampled-thread-time`,
   outil installé en local utilisateur `~/.dotnet/tools`) et traiter le prochain poste
   s'il reste évident ; s'arrêter quand le C# par frame n'est plus dominant.

## Vérification
`tools/perf_vm.sh` « rien du monde » ×0,5 et ×4 avant/après [n≥2] ; comportement de
survol inchangé (captures avec `-s X,Y` et `-g N`).

## Ne pas faire
Pas de nouveau comportement de survol ; pas de toucher au picking (`FindSegmentGlobal`).

## Fin de tronçon
Maj `00_etat.md`, commit. Point F5 : survol, étiquettes, curseur réactifs comme avant.
