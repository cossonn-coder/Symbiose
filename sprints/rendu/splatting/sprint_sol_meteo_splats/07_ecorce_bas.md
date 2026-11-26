# ⑦ Écorce sous ×4 (bandes ×0,5/×1/×2) — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md`, conception E3, `tools/splat/cuire_ecorces.js`,
`visuals/Ecorces.cs`, `visuals/BandesCuites.cs`, `visuals/PlantRenderer.Ecorce.cs` (`EcorceMinPx`),
`visuals/DecorLayer.Charpente.cs` (`EcorceReductionMax`, `RangerEcorces`),
`sprints/rendu/splatting/sprint_lisiere_chargement/00_etat.md` (compte rendu ②, « bouleau gris tacheté »).
Golden attendu : **`bce813af…` INTACT**. Build vert, 0 avertissement.

## Objectif
Retour F5 de Nico (2026-11-26) : « l'écorce n'apparaît qu'à partir de ×4 ». Cuire les bandes d'écorce aux
paliers ×0,5/×1/×2 au pixel natif (pas de réduction de la bande ×4, E7), et les poser au jardin et en lisière.

## À faire
1. `cuire_ecorces.js` aux paliers bas (vérifier la largeur minimale lisible : une bande de 1-2 px n'a pas
   de sens ; le seuil se fixe à la mesure, et en dessous le ruban lissé + stries reste).
2. Jardin : la bande du palier courant au lieu du repli. Lisière : `RangerEcorces` recopie la bande du
   palier ; la règle `EcorceReductionMax` ne sert plus que de garde-fou.
3. Le bouleau doit garder ses lenticelles lisibles à ×1 (pas de sel).

## Mesures
Captures ×0,5/×1/×2 avant/après (bouleau, chêne, sapin ; jardin et forêt de lisière) ; `mesures/07_*` ;
Mo git ; poids de l'atlas du décor.

## Ne PAS faire
`data/code/`, `test_epaisseur_500ans`, DeepSeek, `vendor/`.

## Fin
`00_etat.md`, commit `feat(tapis⑦) : …`.
