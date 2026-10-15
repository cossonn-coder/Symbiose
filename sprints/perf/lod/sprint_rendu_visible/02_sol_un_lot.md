# T2 — Le sol en un lot

> Lire `CLAUDE.md`, `00_etat.md`, `docs/perf/lod/conception_rendu_visible.md` §2/§5.
> Vue C# pure. Golden intact.

## Objectif
Le sol (`Ground`) coûte ~105 ms/frame à ×0,5 sur la VM : ~2400 nœuds alternés
(`Sprite2D` dessus texturé + `Polygon2D` flanc de relief) qui cassent le lot GPU.
Le remplacer par **un maillage par tuile** (ou très peu de draws au total), avec une
**image identique au pixel**.

## Code concerné (lire avant)
- `world/WorldView.Monde.cs` `BuildGround` : un `Sprite2D` par plot, texture partagée
  par (sol, orientation) via `GroundTexture` → `SolTexture.BakeLozenge` ; damier
  `Modulate` (1 / 0,95) ; boussole (Labels) et ombre de maison (`WorldView.Maison.cs`)
  posées aussi dans `_ground`.
- `world/WorldView.Relief.cs` : `RegisterReliefPlot` crée le flanc `Polygon2D`
  (couleur sol assombrie 0,4) AJOUTÉ AVANT le dessus (ordre de peinture voulu) ;
  `UpdateRelief` remonte dessus + flanc selon l'épaisseur courante (appelé depuis
  l'application du sol, famille 0 de `WorldView.Etalement.cs`).
- Rotation D35 : `RebuildWorld` (`WorldView.Camera.cs`) reconstruit le sol.
- Des plantes se recalent sur le relief (`ReliefRisePx`) : l'API lue par les autres doit
  survivre (même données, autre stockage).

## Modèle (intention — placement à vérifier au code)
- Par tuile : un `ArrayMesh` (via `MeshInstance2D` ou `DrawMesh` dans un nœud dédié)
  dont les triangles sont émis **dans l'ordre de peinture actuel** (flanc puis dessus,
  plot par plot, dans l'ordre de `BuildGround`) — dans un maillage, l'ordre des triangles
  EST l'ordre de dessin. Damier → couleur de sommet. Flanc = couleur unie : prévoir une
  zone de texel blanc opaque (atlas lozenge + texel) ou un 2ᵉ maillage si l'ordre le
  permet — choisir après vérification visuelle.
- Le filtre `Nearest`, l'UV exact du losange et l'ancrage du `Sprite2D` (centré, décalage
  éventuel) doivent être reproduits → **comparer les captures**.
- Relief : sur changement d'épaisseur, reconstruire le(s) maillage(s) des tuiles touchées
  seulement (1188 quads = trivial, mais jamais par frame).
- Garder boussole, ombre de maison, `ReliefRisePx`, picking de plot (`FindPlot`) intacts.

## Vérification
- Captures avant/après (`tools/capture_vm.sh`, ×0,5, ×4 sur 300,1700, ×16) : pixels
  différents ≈ 0 hors couches animées (méthode : pixels statiques sur 3 frames, cf.
  sprint jardin vivant T2). Rotation (4 orientations) et relief qui monte inclus.
- `tools/perf_vm.sh` : draw calls et FPS ×0,5 et ×4 avant/après [n≥2]. Attendu ×0,5
  ~5 → ~11 FPS VM, draw calls divisés par ~100 (à constater, pas à forcer).

## Ne pas faire
Pas de changement de DA du sol (D34 reste ouverte), pas de cuisson du sol entier en une
texture géante (illisible à ×32). Pas de touche au moteur.

## Fin de tronçon
Maj `00_etat.md` (gain mesuré, technique retenue), commit. Point F5 : « le sol a-t-il
changé ? » (attendu : non) + F4 ×0,5.
