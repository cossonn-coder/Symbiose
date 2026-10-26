# ③ Lisière en DA SNES : atlas « patchwork » + prairie/friche + forêt

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, `docs/perf/fluidite/conception_fluidite_pc.md`
(§3, §4 principes de rendu). **Golden** : intact (vue C# seule).

## Objectif (consigne Nico, 2026-10-26)
La lisière doit avoir **le niveau de détail qu'on voit aux zooms ×1 / ×0,5**, faite
**d'assets en patchwork qui rendent bien** : un kit de petites pièces pixel-art précuites,
assemblées et variées au hash, à la place des aplats peints. DA : mignon SNES
(Chrono Trigger / FF VI), palette limitée, contours sombres, lumière cohérente avec le kit des
plantes. F5 : une seule question à Nico, « c'est mieux ? ».

## À faire
1. **Atlas du décor** (partial NEUF de `DecorLayer`, ex. `DecorLayer.Kit.cs` — `DecorLayer.cs`
   est plein) : pièces générées UNE fois, procédurales et déterministes (hash, zéro Random),
   peintes en NIVEAUX de rampe puis teintées — même langage que
   `visuals/PlantRenderer.Kit.cs` (0 vide · 1 contour · 2 ombre · 3 base · 4 lumière).
   Pièces minimales : touffes d'herbe (plusieurs tailles × variantes), fleurettes, ronciers /
   arbustes de friche, houppiers de lisière (plusieurs ports : feuillus ronds, conifères,
   bouleaux clairs), troncs, sous-bois sombre. Teinte par motif ; par saison si simple.
2. **Prairie et friche** : l'assise devient un patchwork tramé (aucune zone unie visible à ×0,5
   et ×1), un ourlet de touffes le long du jardin ; friche = touffes hautes + ronciers +
   jeunes ligneux épars. Les deux motifs les plus fréquents en jeu : soigner en premier.
3. **Forêt** : une vraie lisière sur toute la longueur du bord — rideau de houppiers
   superposés (arrière plus sombre, avant plus clair), bord clairsemé → cœur dense (gradient
   actuel de `DecorLayer.Arbres.cs`), sous-bois sombre visible entre les troncs. Densité et
   hauteur toujours pilotées par la ceinture du pont (`DecorLayer.Pont.cs` : clairière, coupe,
   recépage → repousses visibles).
4. **Coût** : décor toujours inerte (redessin au build / LOD / ceinture / rotation seulement) ;
   pièces d'un même atlas dessinées en lot. Mesurer les draw calls du décor et le temps du
   `_Draw` du décor au banc VM avant/après : **≤ aujourd'hui** en draw calls.
5. **Contrôle visuel** : captures VM ×0,5 / ×1 / ×2 des bords (graines 1521550718 et 42, plus
   le banc F10 4 motifs — ajouter un argument de capture qui l'active si besoin) ; les ouvrir et
   juger avant le commit. Noter les chemins dans `00_etat.md`.

## Ne PAS faire
- Rivière, falaise (④). Ombre de lisière sur le jardin (hors périmètre, décision Nico).
- Animer le décor (vent exclu, DA : animation = signal).
- Toucher `fields/peripherie.py`, le pont, le golden.

## Fin de tronçon
`dotnet build` vert ; captures jugées ; LDC ≤ 300 par fichier (partials neufs) ; commentaires
pédagogiques au cœur des fichiers ; golden intact ; `00_etat.md` (point F5 « c'est mieux ? ») ;
commit.
