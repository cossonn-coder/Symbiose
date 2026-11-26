# ③ Lisière en pixel natif ×8-×32 (atlas par palier) — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md` (①②), `docs/rendu/splatting/conception_lisiere_chargement.md`
(L2, §3.3), `visuals/DecorLayer.Mailles.cs`, `visuals/BudgetCuisson.cs`.
Golden attendu : **`bce813af…` INTACT**. Build vert, 0 avertissement.

## Objectif
Au-delà de ×4, la maille ×4 sert telle quelle (sa géométrie est en px canvas), mais l'**atlas des
pièces** est remplacé par un atlas cuit 2× (×8), 4× (×16), 8× (×32) plus fin, **mêmes UV
normalisées** → chaque pièce s'affiche au pixel natif du palier.

## À faire
1. Cuire les pièces du kit (et les bandes d'écorce recopiées au ②, et les texels-codes des aplats)
   aux résolutions ×8/×16/×32. Vérifier au code ce qui fixe la taille en px d'une pièce
   (`TailleZoom`, `ZoomConstr`, `MaxZoom`) pour que la pièce ×8 couvre exactement la même surface
   canvas que la pièce ×4.
2. Permuter la texture du matériau du décor au changement de palier (pas la maille). Atlas des
   paliers non affichés : libérables ; compter les octets dans `BudgetCuisson` (budget 1 Go, E6).
3. Grains procéduraux du shader `decor_indexe.gdshader` (roche, eau, neige, givre — `ip`, uniform
   `zoom`) : constater en capture ×8/×16/×32, puis les caler sur la même règle (pixel natif au palier
   réel) si la capture montre des pavés grossis. Vérifier ce que vaut `zoom` au-delà de ×4.
4. `EauScintillement` (nœud enfant) : même constat.

## Mesures
- Capture du bord du jardin (`-c` près d'une lisière forêt, puis rivière, puis falaise) ×8/×16/×32
  avant/après. `mesures/03_*`.
- Octets de chaque atlas (mesurés, pas estimés), temps de cuisson, ms par image au changement de
  palier (pas d'à-coup nouveau).

## Ne PAS faire
- Construire des mailles ×8+ (la géométrie ne change pas). `data/code/`, `test_epaisseur_500ans`,
  DeepSeek, `tools/splat/vendor/`.

## Fin
`00_etat.md`, commit `feat(lisiere③) : …`.
