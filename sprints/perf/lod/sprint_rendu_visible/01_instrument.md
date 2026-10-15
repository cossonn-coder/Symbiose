# T1 — Instrument de mesure du rendu

> Lire d'abord `CLAUDE.md`, `00_etat.md` (même dossier) et
> `docs/perf/lod/conception_rendu_visible.md` §2. Vue C# + un script bash. Golden intact.

## Objectif
Donner à Nico ET aux tronçons suivants une mesure **comparable** du coût de frame :
1. **F4 enrichi** (`world/WorldView.Hud.cs` `UpdatePerf`, ou un partial neuf si le Hud
   dépasse la bande) : ajouter par frame les moniteurs Godot
   `Performance.Monitor.RenderTotalDrawCallsInFrame`, `RenderTotalObjectsInFrame`,
   `RenderTotalPrimitivesInFrame`, et le temps de frame (ms, moyenne glissante ~1 s).
   Ajouter les mêmes chiffres au rapport presse-papier (touche C, `WorldView.PerfReport.cs`).
2. **Bascule de couches debug** : une touche (choisir une touche LIBRE après lecture de
   `WorldView.Controls.cs` — Shift+F4 suggéré) qui fait défiler « tout · sans Sol · sans
   Décor · sans Objets (plantes+maison) · sans vie macro · sans couches au sol · sans
   ciel/météo/vignette · rien du monde ». Le nom du cas s'affiche dans F4. Masquage par
   `CanvasItem.Visible` des nœuds nommés (`Ground`, `Decor`, `Objects`, `MacroLife`,
   `Mulch`, `Puddle`, `Couverture`, `Allelopathie`, `Carpophores`, `ForagerLayer`,
   `LeafLitter`, `Litter`, `Covers`, `Snow`, `Weather`, `Sky`, `Vignette` — noms à
   revérifier au `grep 'Name = "'`). ⚠️ Des nœuds sont RECRÉÉS (rotation `RebuildWorld`,
   snapshot) : ré-appliquer le masquage après reconstruction, pas une seule fois.
   Retour au cas « tout » = état initial exact.
3. **Banc VM temps réel** `tools/perf_vm.sh` : même amorçage Xvfb/Godot que
   `tools/capture_vm.sh` (le réutiliser/factoriser, pas le dupliquer mollement) mais
   SANS Movie Maker, avec `--print-fps`, durée bornée ; options banc/zoom/centre +
   `--capture-cacher=Nom1,Nom2` (nouvel argument de `world/WorldView.Capture.cs`, même
   mécanique de masquage que 2.). Sortie : FPS moyen sur les N derniers relevés + draw
   calls moyens (à imprimer par le jeu en mode capture, ex. une ligne `[perf]` par s).
   Le script affiche `uptime` (charge VM) en tête : au-dessus de ~4, avertir.

## Vérification
- Reproduire le tableau de `00_etat.md` (×0,5 tout / sans Ground ; ×4 tout) [n≥2 runs
  chacun] et consigner les **draw calls** de chaque cas (chiffre neuf, la référence de T2).
- F4 sans la bascule = comportement inchangé hormis les lignes ajoutées.

## Ne pas faire
Ne rien optimiser ici. Pas de toucher au moteur Python ni au pont.

## Fin de tronçon
Maj `00_etat.md` (mesures de référence draw calls, touche choisie, usage de `perf_vm.sh`),
commit. **Point F5 Nico** : F4 + bascule de couches à ×0,5 et ×4 sur `full` — noter FPS et
draw calls de chaque cas (c'est la référence sur SON PC pour D1).
