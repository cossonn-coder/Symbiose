# ② Butineurs + pollen dessinés en un lot

**Golden** : intact (vue C# seule). **Build** vert.

## Constat (run PC, phase C) [n=1 run, PC]
`butineurs _Draw` 29 ms/image, pics 108 ms ; rendu CPU 117 ms/image, 861 draw calls, avec
285 fleurs pollinisées et 53 butineurs. Au code : `visuals/PollenLot.cs` `Dessiner()` fait
un `DrawCircle` par grain (≤ `MaxParFleur = 8` par fleur, rayon 1,3 px) ; `ForagerLayer.cs`
`DessinerButineurs()` fait 1-2 `DrawCircle` par butineur. Un `DrawCircle` est un polygone :
~2 300 polygones dont les commandes repartent au rendu à chaque image.

## À faire
1. **Reproduire d'abord sur VM** la scène fleurie (s90 an 2, ×4, graine 1521550718 —
   p. ex. le banc 3 phases ou une capture) et mesurer `butineurs _Draw`, rendu CPU, draw
   calls, primitives : chiffres « avant ».
2. Dessiner le pollen ET les butineurs via **une géométrie en lot** — `visuals/LotTriangles.cs`
   (déjà utilisé par le décor, la litière, les carpophores) : points pixel-art (petit carré
   ou losange au pixel du SubViewport) au lieu de cercles polygonaux. Même couleurs, même
   positions, même LOD (`MinZoom`), même cadence (pollen ≤ 4 Hz sur signal, butineurs
   `AnimHz`), même culling.
3. Vérifier que les deux nœuds gardent leur ordre (pollen SOUS les butineurs,
   `ShowBehindParent`) et le ZIndex 11 des butineurs.
4. Mesurer « après » (même scène) + capture visuelle avant/après à ×4 et ×8 dans
   `sprints/perf/fluidite/sprint_fluidite_pc_leviers/captures_02/`. Un tronçon sans gain
   mesuré n'est pas un succès : si le gain est faible, chercher où part le temps (outil ①).

## Ne PAS faire
Changer la logique de vol / de dépôt de pollen (`AccumulatePollen`, hops) — c'est un
ressenti de vue figé. Toucher au moteur.

## F5 Nico
Les butineurs et le pollen se voient-ils comme avant (×4, ×8) ?
