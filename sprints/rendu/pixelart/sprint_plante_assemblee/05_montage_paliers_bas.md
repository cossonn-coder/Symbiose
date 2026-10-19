# ⑤ Montage de la plante assemblée aux paliers bas — kickoff autosuffisant

## Lire d'abord
`CLAUDE.md` · `00_etat.md` · `docs/rendu/pixelart/conception_plante_assemblee.md` §2.1 + §4.3 ·
`docs/perf/lod/conception_rendu_visible.md` §4 (tableau D4 des paliers, tapis D5).

## Objectif
Remplacer les **ellipses** des paliers ×0,5 · ×1 · ×2 (`DrawPalierBas`, `DrawCouronne`) par la
**plante assemblée** : vraies tiges + touffes du kit (④) posées sur les vrais segments. Fin des
« blobs ». **×4 et au-delà strictement inchangés** (capture identique au pixel à ×4/×8).

## Fichiers
`visuals/PlantRenderer.Paliers.cs` (161 LDC), le kit de ④, `PlantRenderer.Bake.cs` (boîte de cuisson
`EtendrePalierBas`).

## Modèle
- **Tiges / fût** : chaque segment en ligne de 1 px interne (plus si l'épaisseur réelle le dépasse),
  couleur bois/tige existante — même projection que `DrawBoisNu`.
- **Feuillage** : aux segments feuillés (extrémités et segments fins, critère `LeafMaxThickCm` déjà
  utilisé), une touffe du kit de la `LeafShape` de l'espèce ; **taille ∝ palier** et taille de la
  plante ; **nombre ∝ `foliage_density`** ; variante au hash (position + indice de segment).
  Ordre de peinture : du fond vers l'avant (tri en profondeur iso), pour que le volume se lise.
- **Information conservée** (tableau D4 — on change la FORME, pas l'information) : teinte espèce +
  saison dès ×0,5 (`TeinteSaison`), santé dès ×2 (`SymptomTint`), givre (`Frosted`), calotte de neige,
  fleurs dès ×2 (fleurons du kit à la place des taches), bois nu l'hiver / squelette (inchangés).
- Ports sans segments feuillés exploitables (tapis, rosette très plate) : semis de touffes sur
  l'emprise réelle au sol.
- Inchangés : **tapis par plot** (`TapisSeuilPx`), `Couronne()` comme **contour** du picking et de
  la boîte de cuisson (à élargir si les touffes débordent), pré-cuisson (zéro coût par image),
  pages d'atlas (②).

## Vérifications
1. Captures VM s45 (`tools/capture_vm.sh -b full -w 44 -z Z -c 1650,950 -n 2`) à ×0,5 / ×1 / ×2,
   avant/après, consignées dans `00_etat.md` ; planche des paliers (`-l 3`) sur une tomate, un arbre,
   un ail. Je juge : plus d'ellipse, les espèces se distinguent par la forme à ×2.
2. ×4 et ×8 identiques au pixel avant/après.
3. `tools/perf_vm.sh -E 20 -z 2` et `-z 1` : médiane et temps de cuisson par plante [VM] — la cuisson
   ne doit pas créer d'à-coups (> 100 ms) au changement de palier.
4. `dotnet build` vert ; golden `22768f33…` ; LDC (`Paliers.cs` ≤ 300, sinon partial).

## NE PAS
Toucher ×4+ · changer ce que chaque palier informe · toucher au Python · lancer `test_epaisseur_500ans`.

## F5 (à ⑦)
« À ×2 / ×1 / ×0,5, est-ce encore horrible ? » — une seule question.

## Golden
Intact.
