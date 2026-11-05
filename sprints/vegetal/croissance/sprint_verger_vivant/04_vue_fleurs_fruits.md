# ④ Vue : fleurs nombreuses et belles, fruits nombreux, banc F5 — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §7, `visuals/PlantRenderer.Houppier.cs` (`SitesFleursHouppier`, `DrawFleuronsHouppier`, `DrawFruitsHouppier`, `PartFleurs`, `FleursArbreMax`), `visuals/PlantRenderer.Organs.cs` (`FloraisonSeuil`, palettes), `visuals/PlantRenderer.Gerbes.cs`, `core/PlantStructure.cs` (lecture des fruits), `sprints/rendu/pixelart/sprint_houppier/00_etat.md` (cuisson, clé stable, bancs de capture), mémoire DA : SNES mignon, palette 16 bits.

## Objectif

Un cerisier en fleur est beau, et il y a des fleurs partout. Un arbre en fruits montre beaucoup de fruits. Les deux se voient au F5.

## À faire

1. **Fleurs continues** : densité ∝ `floraison` (seuil d'apparition bas, ~0,15 `[choix]`, à caler), du bouton au plein, puis à la chute. Plus de tout ou rien à 0,5 pour les arbres.
2. **Nombreuses** : des bouquets de plusieurs fleurs par brindille au pic. Au pic, le houppier du cerisier paraît blanc, et la fleur se voit avant ou avec la feuille selon l'espèce (②). `FleursArbreMax` relevé, avec un budget de cuisson mesuré par coup de pinceau ×2/×4/×8 avant/après.
3. **Belles** : la pièce de fleur montre ses pétales et son cœur aux paliers proches ; le pommier passe du bouton rose au blanc rosé ; le cerisier est blanc pur. Palette SNES, `KitFleuron` à enrichir plutôt qu'à remplacer.
4. **Pétales qui tombent** au déclin de `floraison` : quelques pétales au sol sous la couronne, en vue seule, qui disparaissent en quelques semaines.
5. **Fruits** : dessiner le `nombre` de chaque cohorte (pont de ③), réparti sur les brindilles du site, avec un plafond de dessin par arbre pour la perf (mesuré). Grappes de cerises par 2 ou 3.
6. **Banc F5** : le `verger_mur` espacé (①), cadré, avec des captures VM (banc de capture Xvfb du projet) au pic de fleurs du cerisier, au pic du pommier et en pleins fruits. `dotnet build Symbiose.csproj` doit passer.
7. Bilan dans `00_etat.md` : captures, coût de cuisson, FPS banc ; consignes F5 pour Nico (quoi regarder, à quelle semaine) ; commit.

## Golden

**INTACT** (vue seule). Le pont ne change pas ici (sinon, c'était au ③).

## NE PAS

Toucher au moteur. Ouvrir une dette sans en fermer une (cf. mémoire surcharge F5). Lancer `tests/test_epaisseur_500ans.py`.
