# ② Plantes en pages d'atlas communes (D109 d) — kickoff autosuffisant

## Lire d'abord
`CLAUDE.md` · `00_etat.md` · `docs/rendu/pixelart/conception_plante_assemblee.md` §2.2 + §4.1 ·
`DETTE.md` D109 (d).

## Objectif
Les plantes cuites partagent des **pages d'atlas** pour que Godot regroupe en un envoi les plantes
consécutives de même texture. Cible : `Objects` (plantes + maison, 380 draw calls à ×4 s45 [VM, n=1])
divisé par ≥ 3. **Image identique au pixel.** Puis **bilan ×4 VM** de l'axe perf (① + ②).

## Fichiers
- `visuals/PlantBaker.cs` (aujourd'hui : une texture par plante, rangée de cellules par pose de vent,
  `MaxAtlasPx = 4096`), `visuals/PlantRenderer.Bake.cs`, `visuals/BakeQueue.cs`.
- Lire comment la plante affiche sa cellule (région de texture) et comment le vent change de pose.

## Modèle (intention — le placement est à toi, vérifié au code)
- Un **gestionnaire de pages** partagé : alloue un rectangle par (plante, poses) dans une page commune
  (empaquetage simple par étagères ; nouvelle page quand pleine) ; libère à la mort / recuisson ;
  défragmente ou recrée une page quand la fragmentation dépasse un seuil (à choisir, mesuré).
- La plante dessine sa région de la page (`DrawTextureRectRegion` ou équivalent) — même position
  pixel, même filtre `Nearest`.
- **Vérifier dans Godot 4.6 / `gl_compatibility`** que des CanvasItems distincts, triés en Y, de même
  texture, sont bien regroupés : mesurer, ne pas supposer. Si le tri Y intercale la maison ou des
  structures, mesurer ce qu'il reste.
- La cuisson reste à la file (`BakeQueue`), sans coût par image ajouté.

## Vérifications
1. Captures VM avant/après identiques (×4, ×8, ×2 ; vent actif `-v 0.6` pour les poses).
2. `tools/perf_vm.sh -E 20 -z 4` et `-z 8` : draw calls, primitives, médiane [VM].
3. **Bilan perf ×4 VM** consigné dans `00_etat.md` : draw calls départ 2 013 → après ① → après ②.
4. `dotnet build` vert, golden `22768f33…`, LDC des fichiers touchés.

## NE PAS
Changer le contenu des cuissons (c'est ④/⑤) · toucher au Python · lancer `test_epaisseur_500ans`.

## Golden
Intact.
