# ② Les 45 icônes

**Lire avant** : `CLAUDE.md`, `00_etat.md` (alphabet de couleurs du ①), doc de
conception §3.5 et §5, `docs/rendu/pixelart/etude_brief_da_16bits.md`.
**Nature** : C# (données). **Golden : INTACT**.

## Objectif
Dessiner une icône 16×16 pour chacun des 45 gestes de `COUTS`
(`data/code/sim/actions/couts.py`), lisible à ×2, dans la grammaire 16 bits.

## Règles de dessin
- Contour sombre d'un pixel, 2 à 3 tons par matière, lumière en haut à gauche.
- **L'objet, pas l'action** : l'outil ou la chose posée (arrosoir, sécateur, bêche,
  grelinette, bac, pot, tuteur, treillis, pergola, perchoir, voile, cloche,
  ombrière, ruche, hache, serpe, pioche…). Les gestes à mains nues montrent la main
  et sa prise (pincer : deux doigts ; arracher : poing ; glaner : main et feuilles ;
  manger : fruit croqué ; écraser : semelle ou pouce).
- **Distinguer les voisins** : couper / tailler / pincer ; bêcher / creuser /
  drainer ; poser_bac (compost) / poser_bac_culture ; poser_pile / empiler_bois ;
  recolter / recolter_miel ; abattre / receper / eteter. Deux icônes d'une même
  famille ne doivent pas se confondre à ×2 : le vérifier à la planche, côte à côte.
- La silhouette seule doit rester reconnaissable (elle sert aux pressentis).
- Point chaud : noter pour chaque icône le pixel « actif » (pointe de la lame, bec
  de l'arrosoir, tranchant de la bêche) — le tronçon ③ en a besoin.

## À faire
1. Remplir les fichiers de `visuals/icones/` famille par famille (8 familles,
   §3.5). Après chaque famille : planche capturée, regardée, corrigée.
2. Un test ou une assertion au démarrage en mode debug : tout verbe de `Gestes[]`
   a sa grille, chaque grille fait 16×16, n'utilise que l'alphabet.
3. Planche finale complète à ×2 et ×4 jointe aux constats de `00_etat.md` (chemin
   des PNG) pour le F5 de Nico.

## Vérification
`dotnet build` vert ; planche complète regardée ; plus aucun geste en repli sur
l'ancien dessin.

## À ne pas faire
- Aucune couleur hors alphabet. Pas de texte ni de chiffre dans une icône.
- Ne pas supprimer l'ancien `_Draw` de `GesteIcon` (laissé inactif).
