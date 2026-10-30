# ⑤ Vue Godot : la mare lisible en SNES + vérification des voix

**C# (vue) + pont si besoin. Golden INCHANGÉ.** Dernier tronçon (règle permanente).
Conception : `docs/champs/sol/conception_sol_nourricier.md` §3.5.

## Faits vérifiés au code (2026-10-30)
- L'eau de surface est déjà rendue par `visuals/PuddleLayer.cs` (flaques) ; le relief
  par `world/WorldView.Relief.cs` ; le pont sérialise `eau_surface` / marais
  (`tools/simserver/serialize.py`). Grammaire DA du sprint CASSÉ À L'ÉCRAN : palette
  indexée (`visuals/PaletteIndexee.cs`, `palette_indexee.gdshader`), brief
  `docs/rendu/pixelart/etude_brief_da_16bits.md`, recettes `visuals/RampesDa.cs`.
- Outils VM : `tools/capture_vm.sh` (captures PNG sous Xvfb), `tools/mesure_da.py`
  (banc de mesure DA), `tools/perf_vm.sh`.

## Objectif
1. La mare du ④ se lit comme une **mare** (eau sombre en SNES, reflets, berge humide)
   et non comme une grosse flaque ; si `PuddleLayer` suffit avec un traitement « eau
   permanente » (marais installé), préférer l'étendre plutôt que créer une couche.
2. Aulne, sphaigne, rossolis visibles ; moustique/libellule visibles (icônes ⑤ du
   sprint précédent).
3. Vérifier en capture, sous vision (psilocybe, touche U), que les voix des plantes
   ne réclament plus toutes un nutriment et que les bêtes ne sont plus toutes
   affamées (relever 10 phrases dans `00_etat.md`).

## Critères
`dotnet build Symbiose.csproj` vert ; captures ×1, ×2, ×4 de la mare, consignées ;
0 % de quasi-noir sur la mare (`mesure_da.py`) ; draw calls avant/après (≤ +2).
Ne laisser AUCUN processus Xvfb/Godot en fond.

## F5 Nico (ressenti seul)
La mare au nord-est se reconnaît comme une mare ; on y voit libellules et moustiques
en été ; sous vision, les plantes ne crient plus toutes famine ; un coin de sol
exploité qui réclame encore, et qui pousse moins.

## Ne PAS faire
Toucher le moteur (sauf sérialisation manquante, en lecture) ; la rivière Est (D118).
