# T5 — Décor : forêt + rivière/falaise détaillés (VUE C#, golden inchangé)

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` + ce fichier.
> Conception : `docs/conception/CONCEPTION_RENDU_AMBIANCE.md` §5.2 & §5.3.
> **Dépend de T1** (noms d'essences) et **T4** (zones/`SurroundingsProfile`).

## Objectif
Remplir les zones posées en T4 par les **motifs détaillés** : **forêt d'arbres
adultes** (silhouettes procédurales, gradient de lisière), **rivière** (eau +
reflets) et **falaise** (paroi étagée) couplées, **prairie fleurie**. Tout
**statique, déterministe, cullable** — **jamais** de re-`_Draw` par frame (le vent
est exclu, dette D72).

## Fichiers à toucher
- `visuals/DecorLayer.cs` (+ éventuel partial `DecorLayer.Arbres.cs` pour la taille).
- `visuals/Palette16.cs` : feuillages par essence (bouleau clair, hêtre vert
  profond, chêne vert moyen, sapin vert-bleu), écorces (bouleau clair, brun), eau
  (2 teintes pour dithering), roche (2-3 valeurs).

## Arbres adultes du décor — rendu procédural (cœur du tronçon)
**Backdrop cosmétique** → PAS la structure de segments de `PlantRenderer` (perf).
Silhouette **adulte peinte directement** (« déjà haut et mûr » par construction) :
- **Un arbre = tronc + houppier**, quelques primitives, **dessiné une fois**, cullé.
- **Houppier = amas d'ellipses volumées** (2-3 valeurs + hue-shift sud) formant un
  « nuage » — pas de branches individuelles. Nombre/placement des blobs =
  **hash(seed, index arbre)**.
- **Table C# `TreeSilhouette`** (comme `LeafProfile`), clé = **nom d'espèce**
  (contrat partagé avec T1 : Hêtre/Bouleau/Charme + chêne/sapin/noyer existants) :
  - `Etale` (chêne) — dôme large bas, tronc court épais.
  - `Ovoide` (hêtre) — houppier en œuf dense haut, tronc droit.
  - `Elance` (bouleau) — houppier léger ouvert, **tronc clair** à chevrons.
  - `Sinueux` (charme) — tronc cannelé, houppier moyen irrégulier.
  - `Conique` (sapin) — étages triangulaires.
  - **Rayon de houppier = taille ADULTE** (table par essence).
- **Tronc** : 1-2 formes fuselées (rampe bois brune, cf. `PlantRenderer.Palette`)
  + signature d'écorce (bouleau clair à lenticelles, charme cannelé).
- **Couleur feuillage par essence** + **modulation automnale** optionnelle
  (réutiliser `LeafColor`/la saison du snapshot si dispo — la forêt rougeoie).
- **Gradient de lisière** : densité d'arbres **croissante** en s'enfonçant depuis
  le bord du jardin (scatter déterministe par hash, façon `MacroLife`/litière) ;
  bord = **bouleaux clairsemés**, profond = **chêne/hêtre denses**.
- **Profondeur** : tri par **Y de base** (proches masquent lointains), tout
  **derrière** le jardin.

## Rivière + falaise (couplées)
- **Rivière** : bande d'eau au tracé sinueux (du profil T4), **reflets** par
  **dithering ordonné** (2 teintes de palette), berges herbeuses.
- **Falaise** : paroi **étagée** (redans 2-3 valeurs), **pente** issue du profil
  (douce/verticale/déversante), sommet végétalisé. Adjacente à la rivière
  (l'érosion l'a creusée).
- **Prairie fleurie** : tapis vert + **semis déterministe** de petites fleurs
  (échantillonnage stable, pas de `Random`).

## Perf (ne PAS régresser le sprint perf du 2026-07-09)
- Tout **statique** (build + rebuild rotation), **cullable** hors écran, aucun
  re-`_Draw` par frame. Quelques milliers de primitives dessinées une fois = OK.
- **Repli** si trop lourd au F5 : cuire la zone forêt en **une texture unique**
  (comme `SolTexture`) et la blitter. Mentionner à Nico si activé.

## Golden / build
- Vue pure → **golden inchangé**. `dotnet build` vert.

## Ne PAS faire
- Pas de segments `PlantRenderer` pour les arbres du décor. Pas de croissance
  (arbres adultes d'emblée). Pas de vent/animation (D72). Pas de `Random`. Pas
  d'interaction (D73).

## F5 Nico
Forêt d'arbres adultes variés avec lisière→profondeur ; rivière qui reflète ;
falaise étagée à pente crédible ; prairie fleurie. Fluidité préservée à ×1.
