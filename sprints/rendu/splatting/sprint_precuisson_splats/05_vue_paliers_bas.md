# ⑤ Vue Godot : le kit des paliers ×0,5 → ×2 vient des splats

Lire d'abord `docs/rendu/splatting/conception_precuisson_splats.md` (D4, §3) et
`00_etat.md` (verdict de lisibilité du ①, chargement des planches choisi au ④).

## Existant (vérifié 2026-11-20)
- Kit actuel GÉNÉRÉ en code : `visuals/PlantRenderer.Kit.cs` (touffes par
  `LeafShape`, 4 tailles internes 3/5/7/9 px × 3 variantes, fleurons point/bouton/
  étoile, niveaux en R, codes de palette indexée en G) + `PlantRenderer.KitCodes.cs`.
- Assemblage : `visuals/PlantRenderer.Assemblee.cs` (vrais segments en tiges 1 px,
  touffes aux rameaux feuillés, nombre ∝ `foliage_density`, ordre nord → sud,
  permutation ombre/lumière selon l'orientation D35).
- Planche du kit visible en jeu : `world/WorldView.PlancheKit.cs`.

## Objectif
1. Remplacer la **source** des pièces du kit : les touffes et fleurons viennent des
   planches splats (recette « touffe » du ②, fleurons du ③) aux tailles des paliers
   bas, au même format que le kit actuel. L'assemblage (`Assemblee.cs`) doit
   changer le moins possible : idéalement il ne voit pas la différence.
2. L'ancien générateur reste derrière un interrupteur (conserver le code).
3. La **planche du kit** en jeu montre les nouvelles pièces (contrôle visuel).
4. Captures VM (`tools/capture_vm.sh -b planche_especes -z 0.5|1|2`) avant/après,
   examinées, chemins dans `00_etat.md`.

## Golden
**INTACT**. `dotnet build` vert.

## Ne PAS faire
Changer la densité, l'ordre ou les tailles de l'assemblage (c'est la forme qui
change, pas l'information) ; toucher aux paliers hauts (④).

## F5
Banc `planche_especes` et monde `full` à ×0,5, ×1, ×2 : les espèces se reconnaissent
toujours de loin, le jardin garde sa lisibilité, la lumière suit le soleil.
