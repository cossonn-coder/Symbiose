# T1 — Palette SNES (32 couleurs + Bayer) et curseur vivant

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, `docs/rendu/pixelart/conception_jardin_vivant.md` §2.4,
`docs/rendu/pixelart/conception_rendu_pixelart.md` (SS① SubViewport 960×540, SS② palette).

## Objectif
1. Tout ce qui est dessiné DANS le SubViewport pixel-art passe par une
   **palette maître d'~32 couleurs** avec **tramage ordonné Bayer** léger
   (technique SNES : faire des dégradés et du relief avec peu de couleurs).
2. Un **curseur** mignon + un **losange de survol** du plot visé (aujourd'hui
   inexistants) — animés **seulement en réponse à un geste** (clic = petit
   « tap »), immobiles sinon (animation = signal).

## Contexte vérifié
- `visuals/Palette16.cs` (~27 couleurs + matériaux maison, 81 LDC) ; ~199
  littéraux couleur épars hors palette (ne PAS tous les migrer : le shader
  rend l'écran conforme, c'est son intérêt).
- SubViewport créé dans `world/WorldView.tscn` (`_worldVp`, cf.
  `WorldView.Camera.cs:33`) ; étiquettes nettes HORS SubViewport
  (`WorldView.Etiquettes.cs`) → non quantifiées, c'est voulu.
- Aucun curseur/survol existant ; `world/SolTexture.cs` cuit le losange de sol
  (mêmes cotes iso que `MakeLozenge`) ; projection `WorldView.WorldToScreen`
  (78×39 px/plot).

## À faire (intention)
- Shader `canvas_item` (fichier `.gdshader` — c'est du shader, pas du GDScript,
  autorisé) appliqué au rendu du SubViewport (ex. sur le `TextureRect`/
  `SubViewportContainer` qui l'affiche) : couleur → plus proche couleur de la
  palette (distance perceptuelle simple), avec seuil Bayer 4×4 entre les deux
  plus proches. Palette passée en uniform depuis C# (`Palette16` = source
  unique ; l'étendre à ~32 entrées : rampes partagées feuillage/sol/ciel/
  pierre/eau/fleurs). Toggle debug (touche libre, cf. `WorldView.Controls.cs`)
  pour comparer avant/après.
- Curseur : `Input.SetCustomMouseCursor` avec image cuite procéduralement
  (style main/flèche SNES, 2 frames : repos / tap). Losange de survol :
  contour pixel 1 px sur le plot sous la souris (picking existant
  `WorldView.ActionPicking.cs`), qui « respire » UNIQUEMENT quand un geste est
  armé, statique sinon.
- Captures avant/après via le banc T0 (`tools/capture_vm.sh`) : regarder les
  PNG, vérifier que ciel, feuillage, sol gardent leurs nuances (pas d'aplats
  écrasés) ; ajuster la palette.

## Critère de réussite
`dotnet build Symbiose.csproj` vert ; PNG avant/après comparés et décrits dans
`00_etat.md` ; coût du shader négligeable (une passe plein écran 960×540).
Question F5 pour Nico : « l'image est-elle plus SNES / plus belle ? ».

## NE PAS
- GDScript (interdit) ; toucher au moteur Python ; re-figer le golden.
- Quantifier les étiquettes/HUD hors SubViewport.
- Animer le curseur en permanence.
- Dépasser 400 LDC par fichier (`tools/compte_ldc.py`).
