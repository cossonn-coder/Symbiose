# ④ Écran de chargement en mycélium — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/rendu/splatting/conception_lisiere_chargement.md`
(L3, L5, L6, §3.4), `world/WorldView.Chargement.cs`, `core/SimBridge.cs` (verrou `_ioLock`,
en-tête), `tools/splat/README.md`, `tools/splat/cuire_portraits.js` (rendu palette pleine).
Golden attendu : **`bce813af…` INTACT**. Build vert, 0 avertissement.

## Objectif
Remplacer la touffe ×8 par un **filament de mycélium qui s'arborise et sert de barre de
progression** (barre permise à l'écran de chargement, E2 : philo #5 vaut pendant le jeu). Récit :
une spore germe → les hyphes s'arborisent → rejoignent la racine d'une plantule (manteau
mycorhizien) → un petit carpophore sort à 100 %. Garder « Le jardin se prépare ».

## À faire
1. **Maquette = porte de décision.** Recette `tools/splat/recettes/mycelium.js` (ou dossier dédié) :
   chaque splat porte un âge ∈ [0, 1] (arborisation déterministe au hash : colonisation d'espace
   ou ramification, zéro `Math.random`). Deux rendus : couleur (palette pleine, lumière cuite,
   comme les portraits) et carte des âges (définir l'âge d'un pixel couvert par plusieurs splats :
   p. ex. âge du splat dominant en alpha). Résolution : 480×270 (affichée ×4) ou 960×540 (×2),
   choisie à l'œil. Simuler la révélation à p = 0,1 / 0,4 / 0,7 / 1 en PNG et les lire :
   si halos ou pointillés, **repli** = ~32 images cuites choisies par p. Consigner le choix.
2. **Shader de l'écran** : pixel visible si âge ≤ p ; front lumineux si p − ε < âge ≤ p ; le
   carpophore occupe les âges les plus hauts (~0,9-1).
3. **Chargement non bloquant** (L5) : `_bridge.Init` en `Task.Run` (le verrou d'I/O existe ;
   vérifier qu'aucun autre appel du pont ne part avant la fin) ; `AssurerGerbes` : son travail est
   de l'`Image`/octets puis `ImageTexture.CreateFromImage` (vérifier au code) → calcul hors fil
   principal, création des textures sur le fil principal ; sinon tranches entre images. Le montage
   (`StartSimulation`, arbre de scène) reste sur le fil principal : mesurer son gel.
4. **Progression** (L6) : monotone (`max`), poids par phase fixés par les durées mesurées (log
   `[Chargement]` enrichi par phase) ; avance asymptotique pendant une phase de durée inconnue ;
   cuisson du cadre = 1 − file restante / file initiale (`BakeQueue`). Filet de 30 s conservé.
5. Le chemin réel du clic « Lancer » du sélecteur (`WorldView.Selecteur.cs:177`) et le mode capture
   (`chargement=1`) passent tous deux par cet écran.

## Mesures
- `tools/capture_vm.sh` en mode chargement (cf. `ArgCapture("chargement")`, `WorldView.cs:259`) :
  suite d'images de l'écran, durées par phase, gel du montage (ms, n et charge VM entre crochets).
- Poids des deux textures.

## Ne PAS faire
- Chiffres ou pourcentage à l'écran. Animation sans lien avec la progression réelle.
- `data/code/` (le pont Python ne change pas), `test_epaisseur_500ans`, DeepSeek, `tools/splat/vendor/`.

## Fin
`00_etat.md`, commit `feat(chargement④) : …`.
