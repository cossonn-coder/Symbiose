# ① Kit de lisière en splats + rameau aplati du sapin — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/rendu/splatting/conception_lisiere_chargement.md`
(L4, L7, §3.1), `tools/splat/README.md`, `visuals/PlantRenderer.KitSplats.cs` (le patron à copier).
Golden attendu : **`bce813af…` INTACT** (`data/code/` jamais modifié). Build vert
(`dotnet build Symbiose.csproj`), 0 avertissement.

## Objectif
Les 10 formes du kit de la lisière (`DecorLayer.Kit.cs` : Herbe, HerbeHaute, Fleur, Roncier,
SousBois, Feuillu, Conifere, Galet, Bloc, Roseau — toutes leurs tailles × 3 variantes) viennent de
pièces précuites en splats, au lieu du générateur à la règle. Plus la recette **rameau aplati** du
sapin (aiguilles), qui sert le bouquet Conifere ici et le sapin du jardin au ②.

## À faire
1. **Recettes** (`tools/splat/recettes/`) : réutiliser les mots existants quand ils conviennent
   (`limbe_graminee`/`feuille_ruban`/`touffe*` pour les herbes, `fleuron` pour la fleurette,
   `feuille_composee` pour la ronce, masses feuillues de S2 ④ pour le bouquet Feuillu — vérifier au
   `ls` ce qui existe) ; neuves : `rameau_aplati` (sapin : aiguilles sur deux rangs, face claire
   dessus, stomates argentés dessous), galet, bloc anguleux, roseau. Cuisson par palier à la taille
   en px que le kit utilise (`Tailles`, `TailleZoom`) ; format = celui de `KitCodes` (codes de
   palette : ton + orientation), à confronter AVANT de cuire en masse sur une pièce témoin.
2. **Adaptateur** : partial neuf `visuals/DecorLayer.KitSplats.cs` qui remet les planches au format
   exact attendu par `AssurerKitDecor` / `CoderPiece` (mêmes clés forme × taille × variante, même
   ancrage). Recette ou planche absente → avertissement + pièce générée, entière.
3. **Interrupteur** : Maj+F11 / `SYMBIOSE_SPLATS=0` bascule aussi la lisière (vider le kit et
   reconstruire les mailles, comme `OublierKit` côté plantes ; vérifier au code comment le décor
   reconstruit ses mailles).

## Mesures
- `tools/capture_vm.sh` monde `full` (les 4 motifs : prairie, forêt, rivière, falaise ; banc F10 du
  décor si utile) ×0,5/×1/×2/×4, avant (`SYMBIOSE_SPLATS=0`) / après, été + hiver (`-w`). Montages
  dans `mesures/01_*`. Lire les PNG.
- Temps de construction d'une maille par palier (log `[DecorLayer] maille … prête`), poids de
  `assets/splats/` (alerte 200 Mo).

## Ne PAS faire
- Changer les règles de semis, de saison, de vent (`DecorLayer.Patchwork/Saison/Vent`).
- Arbres de lisière (②), paliers > ×4 (③).
- `data/code/`, `test_epaisseur_500ans`, DeepSeek, `tools/splat/vendor/`.

## Fin
Compte rendu dans `00_etat.md` (recettes neuves/réutilisées, mesures avec leurs limites entre
crochets), commit `feat(lisiere①) : …`.
