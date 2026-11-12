# ① Moteur d'icônes et planche de contrôle

**Lire avant** : `CLAUDE.md`, `00_etat.md`, doc de conception §5.
**Nature** : C#. **Golden : INTACT**.

## Objectif
Poser l'outillage : un format d'icône, sa cuisson, et une planche qui montre toutes
les icônes d'un coup pour que l'agent les regarde sur la VM.

## État du code (vérifié le 2026-11-12)
- `world/WorldView.Curseur.cs` : `MainRepos`/`MainTap` = `string[]` de 16 lignes de
  16 caractères ; `CuireMain` les peint dans une `Image` Rgba8 avec
  `Palette16.MaitreSombre/Blanc/Granite/Jaune`, `Resize` en `Nearest` ×2, puis
  `ImageTexture`. Les textures sont libérées dans `LibererCurseur` (sinon fuite à
  la sortie, constaté au banc VM).
- `visuals/Palette16.cs` (+ `PaletteSnes.cs`, `PaletteIndexee.cs`) : palette maître.
- `world/GesteIcon.cs` (269 LDC) : `Button` de 44 px, pictogramme dessiné dans
  `_Draw` avec des couleurs brutes, par famille (`_kind`).
- Planche existante comme modèle : `world/WorldView.Planche.cs`, `PlancheKit.cs`
  (touche L) ; capture VM : `tools/capture_vm.sh` (PNG lus avec l'outil Read).

## À faire
1. **`visuals/IconeGeste.cs`** (classe statique) : `Cuire(string[] grille, int
   echelle)` → `ImageTexture`, avec un **alphabet de couleurs unique** (une lettre =
   une couleur de `Palette16` ; viser 12 à 16 lettres : contour, 2 métaux, 2 bois,
   2 verts, terre, eau, rouge, jaune, blanc, ombre…) documenté en tête de fichier.
   `CuireSilhouette(grille, echelle)` → même forme, une seule teinte sombre.
   Cache par (verbe, échelle, variante) ; libération explicite à la sortie.
   Factoriser `CuireMain` dessus si c'est simple, sans changer le rendu de la main.
2. **Registre** `visuals/icones/` : un fichier de données par famille
   (`IconesMain.cs`, `IconesSol.cs`…), chacun un dictionnaire verbe → grille
   (et plus tard verbe → images d'animation). Au ① : **3 icônes témoins**
   seulement (arroser, couper, poser_bac), pour valider le format.
3. **`GesteIcon`** : si une grille existe pour le verbe, afficher la texture cuite
   (échelle entière choisie pour tenir dans 44 px : ×2 = 32 px, centrée) ; sinon
   l'ancien dessin (repli). Cadre « actif » et état pressenti conservés.
4. **Planche des icônes** : un mode de capture qui affiche sur fond de jeu toutes
   les icônes enregistrées, à ×2 et ×4, avec leur silhouette, rangées par famille
   (nouvelle option de `tools/capture_vm.sh` ou banc dédié, au plus simple vu
   `WorldView.Capture.cs`). C'est l'outil de contrôle des tronçons ② à ④.

## Vérification
`dotnet build` vert ; planche capturée et regardée ; palette en jeu inchangée hors
des 3 témoins.

## À ne pas faire
- Ne pas dessiner les 45 icônes ici.
- Pas d'asset PNG : tout est dans le code.
