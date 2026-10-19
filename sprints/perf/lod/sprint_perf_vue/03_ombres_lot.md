# ③ — Ombres des plantes en lot

> Lire d'abord `CLAUDE.md`, `00_etat.md`, `docs/perf/lod/conception_perf_vue.md` §2-3.
> Vue C# pure. Golden intact.

## Objectif
Les ombres ON ne doivent plus coûter qu'au moment où le soleil bouge vraiment, et en un lot.

- Aujourd'hui : un nœud `PlantShadow` (`visuals/PlantShadow.cs`) par plante, polygone capsule
  (modèle exact de `fields/light.py` §3) ; à chaque pas de soleil ≥ 2°
  (`world/WorldView.Soleil.cs`), `QueueRedraw` de tous ces nœuds. Lire d'abord les mesures du
  banc ① : coût CPU de redessin, ou casse du regroupement des plantes (ombres et plantes
  alternées dans le tri en Y) ?
- Cible : **un lot par tuile** (un maillage/polygone combiné, ou une texture d'ombres par tuile)
  hors du tri en Y des plantes, sous les plantes. Recalcul seulement quand le soleil a bougé
  d'un pas, quand une plante change d'emprise (snapshot) ou à la rotation de vue. Respecter
  `MargeVue`.
- **Même image** : forme, direction, longueur, alpha selon `SunStrength` — vérifier sur captures
  VM avant/après (`tools/capture_vm.sh`), pixel à pixel si possible comme au sol (D106 T2).
- L'ombre de la maison (`_houseShadow`) : la laisser telle quelle sauf si le banc la désigne.
- Touche O inchangée (ON/OFF).
- `dotnet build Symbiose.csproj` vert.

## Mesure (banc ①)
Cas « ombres ON » vs « OFF » à ×4 : l'écart doit tomber au bruit entre deux pas de soleil ;
ms du recalcul au pas de soleil, sans image > 33 ms.

## Ne pas faire
Ne pas changer le modèle d'ombre (c'est la vérité Python reproduite). Ne pas toucher le moteur.
Pas de `test_epaisseur_500ans`.

## Fin de tronçon
`00_etat.md` (mesures avant/après), commit.
