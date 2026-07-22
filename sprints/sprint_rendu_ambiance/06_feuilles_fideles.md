# T6 — Feuilles fidèles au modèle réel (VUE C#, golden inchangé)

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` + ce fichier.
> Conception : `docs/rendu/ambiance/conception_rendu_ambiance.md` §3bis.
> **Indépendant** (organes végétaux) — peut être fait dès après T1/T2.

## Objectif
Nico : « enlever les rendus simplistes de feuille en ovale, que chaque feuille
soit **fidèle à son modèle réel** ». Aujourd'hui `visuals/PlantRenderer.Leaf.cs`
synthétise chaque feuille par **amas d'ellipses fusionnées** (un chêne « lobé » =
petites ellipses) → lecture en taches ovales. On ajoute, **au zoom rapproché**,
un **vrai contour de silhouette authoré par espèce**.

## Fichiers à toucher
- **Neuf** : `visuals/PlantRenderer.LeafOutline.cs` (partial) — la table de contours
  par espèce + le tracé polygone volumé. (`Leaf.cs` fait déjà 358 LDC : ne PAS y
  entasser les contours — garde-fou taille, un fichier = un concept.)
- `visuals/PlantRenderer.Leaf.cs` : brancher le **palier LOD** (dispatcher vers le
  contour authoré au zoom ≥ seuil, sinon garder l'archétype existant). Lire
  `DrawShapeBySpecies` (le point de dispatch actuel), `LeafFrame`, `DrawLeafVeins`,
  `LeafShapeMinZoom`.
- Lire `visuals/PlantRenderer.Palette.cs` (`DrawVolumeEllipse`, `HueShift`,
  `SouthDir`) pour reproduire le volume 2 valeurs sur un polygone.

## Modèle
### Contour par espèce
- `LeafOutline` = **liste de points normalisés** (repère feuille : axe = longueur,
  cross = largeur, ≈ [-1,1]), contour **fermé**, **façonné à la main par espèce**
  d'après sa feuille réelle. Le contour **encode la marge** : entière = bord lisse ;
  **dentée** = petites dents ; **lobée** = sinus profonds. **Composée** = cas à
  part : rachis + N **folioles** (chacune un petit contour denté), pas un limbe unique.
- Table `LeafOutlines[species]` en regard de `LeafProfiles`. **Mapper les ~27
  espèces du catalogue** (clé = nom de classe Python, `_structure.SpeciesName`).
  Espèce non mappée → repli archétype (l'existant). Fidélité visée (indicatif) :
  chêne (lobes arrondis+sinus), figuier/courgette/érable (palmatilobée),
  pommier/cerisier/bourrache (ovale **denté**), tomate/carotte/achillée/phacélie/
  frêne-noyer (**composée pennée** à folioles découpées), ail/lavande/consoude
  (linéaire-lancéolé), trèfle (3 folioles obcordées), haricot (foliole cordée).
- Dérogation D10 assumée (forme = fait de rendu, direct C#).

### Tracé (invariants pixel-art conservés)
1. Points normalisés → écran via `LeafFrame` (axe/cross) × (rx, ry).
2. **≥ 2 valeurs (E4, jamais d'aplat)** : remplir le polygone en teinte **ombrée**,
   puis re-remplir une **copie réduite (~0,8) décalée au SUD** en teinte **éclairée**
   (même logique que `DrawVolumeEllipse`). `DrawColoredPolygon`, filtre Nearest.
3. **Nervures** par-dessus (réutiliser `DrawLeafVeins` : penninerve / palmée /
   composée selon la marge du contour).
4. **Déterminisme** : contour statique ; léger jitter inclinaison/taille par **hash**
   (canaux déjà utilisés dans `Leaf.cs`). **Zéro `Random`.**

### LOD (3 paliers — attente honnête, cf. §3bis.1)
- `LeafOutlineMinZoom ≈ 16f` : contour fidèle + volume + nervures.
- `[LeafShapeMinZoom(4), LeafOutlineMinZoom(16)[` : **archétype ellipses actuel**
  (repli intermédiaire, inchangé).
- `< 4` : tache simple (existant).
Ne dessiner le contour QUE au palier haut (peu de plantes à l'écran, culling actif).

## Perf (ne PAS régresser le sprint perf du 2026-07-09)
- Contour = 1 polygone rempli (+ copie ombrée + nervures) par feuille, **seulement
  au ×16+**. En dessous : archétype/ellipse. **Repli** si lourd au F5 : cuire un
  **sprite de feuille par espèce** (taille fixe, `SolTexture`-like) et le blitter —
  signaler à Nico si activé.

## Golden / build
- Vue pure → **golden inchangé** (`python3 -m tests.test_golden` inchangé).
  `dotnet build Symbiose.csproj` vert.

## Ne PAS faire
- Pas de `Random`, pas d'aplat (toujours ≥ 2 valeurs). Ne pas dessiner le contour
  fidèle sous le palier haut (perf). Ne pas toucher la couleur (déjà par espèce).
  Ne pas supprimer l'archétype ellipses (il devient le repli intermédiaire).

## F5 Nico
Zoomer sur une plante (×16/×32) : la feuille doit être **reconnaissable comme celle
de l'espèce** (chêne lobé, figuier palmé, tomate composée…), pas un ovale. Vérifier
la bascule LOD au dézoom et la fluidité préservée.
