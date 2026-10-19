# ① Decor + couvre-sol en maillage — kickoff autosuffisant

## Lire d'abord
`CLAUDE.md` · `00_etat.md` (ce dossier) · `docs/rendu/pixelart/conception_plante_assemblee.md` §2.2 + §4.1.

## Objectif
Faire tomber les draw calls à ×4 de **~2 013 à ≲ 500 [VM]** en dessinant la ceinture (`Decor`) et les
couvre-sol en **lot** (un `ArrayMesh` + un `DrawMesh` par nœud), **image identique au pixel**.

Mesure de départ (banc E s45 ×4, VM, n=1) : total 2 013 ; masquer `Decor` −1 099 ; masquer
`Couverture,Allelopathie,Mulch,Puddle,Litter,LeafLitter` −449 ; `Objects` −380 ; masquer `Ground` 0.

## Fichiers
- `visuals/DecorLayer.cs` + `DecorLayer.Arbres.cs` (+ `.Pont.cs`/`.Banc.cs` si concernés) :
  `_Draw` émet des `DrawColoredPolygon`/`DrawCircle`/`DrawLine`/ellipses — chacune = un envoi GPU.
- `visuals/CouvertureLayer.cs`, `AllelopathieLayer.cs`, `MulchLayer.cs`, `PuddleLayer.cs`,
  `LitterLayer.cs`, `LeafLitterLayer.cs`.
- Recette de référence (à lire, à imiter) : `visuals/PlantShadow.cs` (ArrayMesh d'éventails, `DrawMesh`),
  `world/SolMaillage.cs`.

## Modèle
- Introduire un **accumulateur de triangles colorés** (sommets + couleurs par sommet, éventails pour
  polygones/cercles/ellipses, quads pour les lignes à largeur entière) qui produit un `ArrayMesh`.
  Un seul petit fichier helper réutilisé par toutes les couches (pas de copie par couche) — vérifier
  d'abord si `PlantShadow`/`SolMaillage` exposent déjà de quoi le factoriser.
- Chaque couche **reconstruit** son maillage seulement quand son contenu change (Decor : bascule de
  LOD `MaxZoom`/`DetailZoom`, rotation, profil ; couvre-sol : snapshot / changement de palier, comme
  aujourd'hui) puis `_Draw` = `DrawMesh` seul. Ne pas changer QUAND ces couches se redessinent, seulement
  COMMENT.
- Ordre de peinture conservé (Decor : passe assise puis passe motifs) → ordre des triangles = ordre
  des anciens appels. Antialiasing : les anciens appels sont `antialiased: false` ; vérifier.
- `Ground` masqué sans effet : comprendre pourquoi (nœuds de maillage du sol parentés ailleurs ?
  `WorldView.Couches.cs`) et le consigner ; corriger le masquage seulement si trivial.

## Vérifications
1. Captures VM AVANT/APRÈS identiques (`tools/capture_vm.sh -b full -w 44 -z Z -c 1650,950 -n 2`, Z ∈
   {0.5, 2, 4}) + une capture où la ceinture est visible (-c proche d'un bord, ex. 1950,1000) + une
   orientation tournée (`-r 1`). Comparaison pixel (python, PIL du venv `/tmp` cf. mémoire SVG, ou
   comparaison d'octets PNG décodés). Écart → expliquer ou corriger.
2. `tools/perf_vm.sh -E 20 -z 4` : draw calls avant/après, consignés dans `00_etat.md` [VM, n=…].
3. `dotnet build Symbiose.csproj` vert. Golden : `cd data/code && python3 -m tests.test_golden` → `22768f33…`.
4. `tools/compte_ldc.py` sur les fichiers touchés (DecorLayer.cs est à 295 LDC : ne pas dépasser 300 —
   le helper vit dans son propre fichier).

## NE PAS
Toucher au moteur Python · changer l'aspect · toucher aux plantes (②) · lancer `test_epaisseur_500ans`.

## Golden
Intact (pure vue).
