# T3 — Maison normande : granite + ardoise (VUE C#, golden inchangé)

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` + ce fichier.
> Conception : `docs/rendu/ambiance/conception_rendu_ambiance.md` §4.

## Objectif
Remplacer le placeholder gris de la maison par une **maison normande de granite et
d'ardoise du Cotentin** (réf. Nico, Montmartin-sur-Mer). PAS de colombages/chaume :
c'est la maison de **pierre + ardoise**, pas la chaumière du pays d'Auge. Rendu
**procédural déterministe**, cohérent pixel-art, **D35-aware** (façades indexées
mur-monde comme aujourd'hui).

## Fichiers à toucher
- Lire `world/WorldView.Monde.cs` : la maison actuelle (`BuildHouse`, `RoofPane`,
  `FacadeColors`/`ToitColors`, 4 coins, 2 façades visibles + toit pyramidal,
  ancrage YSort, ombre portée). **Extraire** tout le rendu maison dans un partial
  neuf `world/WorldView.Maison.cs` (Monde.cs gonfle — garde-fou taille ; garder
  le sol dans Monde.cs). Conserver l'ombre portée animée telle quelle.
- `visuals/Palette16.cs` : ajouter les teintes (granite gris-bleu, granite roux,
  granite clair pour encadrements, ardoise, brique orangée, joint chaux). Étendre
  `Facades`/`Toits` ou ajouter des rampes nommées.

## Modèle (procédural, ≥ 2 valeurs partout, hue-shift sud)
1. **Murs = moellons de granite** : sur chaque façade visible, texture de pierre
   2-3 valeurs (grain déterministe par **hash**, esprit `SolTexture`), joints de
   chaux clairs. Éclairement **sud-monde** (façade sud claire, nord froide/sombre),
   indexé mur-monde (fait tourner la maison sous D35).
2. **Chaînages d'angle** : pierres harpées plus claires aux arêtes des façades.
3. **Encadrements de baies** en granite clair (jambages + linteau + appui débordant
   à larmier).
4. **Pignon exposé (ouest-monde)** : **essentage d'ardoise** (petit motif d'écailles
   2 valeurs) jusqu'à mi-hauteur, sur la façade choisie par orientation.
5. **Toit ardoise** : remplacer la pyramide plate par **2 pans pentus (> 45°) +
   croupe**, faîte marqué ; **rangs d'écailles** (pureau serré, 2 valeurs) ;
   **lucarne à bâtière** sur le versant sud (petit volume saillant + mini-toit).
6. **Ouvertures** : porte au sud + fenêtres à petits carreaux (croisillons 1 px,
   menuiserie sombre).
7. **Cheminée** : souche en brique orangée émergeant du faîtage (volume 2 valeurs).
   **PAS de fumée** (= animation, différée D72).

## Contraintes
- **D35** : tout suit le sud-monde (indexation mur-monde existante). Vérifier que
  la maison ne « saute » pas sous rotation (comme le fix du 1er F5 t4).
- **Statique** : dessinée une fois au build (et rebuild rotation), pas par frame.
- **Déterminisme** : grain/écailles/chaînages par hash, zéro `Random`.
- Garder l'**empreinte au sol** et l'**échelle** actuelles (lecture du bloc
  `house` du snapshot : `footprint_cm`, `height_cm`) + l'**ombre portée**.

## Golden / build
- Vue pure → **golden inchangé** (aucun moteur touché). `dotnet build` vert.

## Ne PAS faire
- Pas de colombages, pas de chaume. Pas de sprite bitmap (procédural only). Pas de
  fumée. Ne pas casser la rotation D35 ni l'ombre portée.

## F5 Nico
Silhouette de granite + toit d'ardoise pentu reconnaissable ; rotation propre aux
4 orientations ; lucarne sud ; cheminée brique.
