# ④ Kit d'éléments de pixel-art — kickoff autosuffisant

## Lire d'abord
`CLAUDE.md` · `00_etat.md` · `docs/rendu/pixelart/conception_plante_assemblee.md` §3 (décisions 2-3)
+ §4.3 · `docs/rendu/pixelart/conception_jardin_vivant.md` (palette SNES, précuisson).

## Objectif
Générer **une fois au démarrage** un **atlas de kit** : les petites pièces de pixel-art dont ⑤
assemblera les plantes aux paliers bas. Livrable visible : une **planche du kit** (capture VM).

## Matière existante (vérifiée)
- `visuals/PlantRenderer.Leaf.cs` : `enum LeafShape` (Composee, Elliptique, Cordee, Lobee, Lanceolee,
  Aciculaire) + table par espèce `(Shape, Aspect, Count, VeinLighter)`.
- `visuals/PlantRenderer.Palette.cs` (palettes par espèce : `Leaf`, `Flower`…), `visuals/PaletteSnes.cs`
  / `Palette16.cs` (palette maître), `Organs.cs` (`HueShift`, `OrganShade`/`OrganLit`).

## Modèle
- Pour chaque `LeafShape` : **touffes** à plusieurs tailles internes (3, 5, 7, 9 px — à régler) ×
  2-3 **variantes** choisies au hash (zéro `Random`). Une touffe = quelques feuilles de la forme
  (folioles découpées pour Composee, aiguilles pour Aciculaire, ruban pour Lanceolee…) en **3 valeurs**
  (ombre / base / lumière, lumière côté sud comme le reste du rendu), contour sombre 1 px si lisible.
- Les touffes sont peintes en **niveaux** (indices de rampe), pas en couleur finale : ⑤ les teinte avec
  la couleur d'espèce/saison/santé au moment de la cuisson (même langage que les paliers actuels).
- **Fleurons** 1-2 px (forme ponctuelle / étoile 3×3), teintés au `Flower` de l'espèce.
- Un seul fichier (ou deux si > 300 LDC) dans `visuals/` ; pas de PNG dessinés à la main (procédural,
  déterministe).
- Banc d'observation : une option de capture qui affiche la planche du kit (toutes formes × tailles ×
  variantes, en 2-3 teintes) — à la manière de la planche des paliers (`WorldView.Planche.cs`).

## Vérifications
- Capture VM de la planche ; je (l'agent) juge la lisibilité : à 3 px une touffe composée et une
  lancéolée doivent déjà différer ; à 9 px la forme de feuille de l'espèce se reconnaît.
- `dotnet build` vert ; golden `22768f33…` ; LDC.

## NE PAS
Brancher le kit sur les plantes (⑤) · toucher ×4 et au-delà · toucher au Python · lancer
`test_epaisseur_500ans`.

## Golden
Intact.
