# ② Vue : fleurs en colonies, butineurs de bord, damier cassé — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (bilan ①), conception §3.1, §3.3, §3.6.

## Objectif

Plus aucun quadrillage : des taches de fleurs crédibles, des insectes dessus, une prairie sans rectangles.

## À faire

1. **Fleurs** : dans `visuals/DecorLayer.Patchwork.cs`, `ChoisirPiece` ne pose plus de fleur au tirage général. Une fleur n'apparaît
   que dans une colonie du pont, dense au centre, éparse au bord, de la couleur de la colonie, bords irréguliers. Vérifier que le
   bloc `ceinture` arrive avant la construction du décor et que les colonies entrent dans le déclencheur de reconstruction
   (`DecorLayer.Pont.cs`), sans reconstruire par semaine.
2. **Shader** (`visuals/decor_indexe.gdshader`, `lisiere`) : neutraliser la grille de printemps (`ip.x % 6`, `ip.y % 4`), en la laissant
   en commentaire (règle du projet : on ne jette pas). Les fleurs `ORIENT_FLEUR` suivent la floraison du pont par couleur, via uniforms
   (`visuals/DecorLayer.Saison.cs`), décalées au hash, et non plus la fenêtre `w` en dur.
3. **Butineurs de bord** : à partir du compte du pont, insectes qui volent au-dessus de leur colonie, patron `visuals/ForagerLayer.cs`
   (horloge + hash, aucun état, même lot, rotation D35, pause). Aucun sans floraison.
4. **Damier** (`DrawAssise`) : la parcelle `hp` (blocs `i / 3`, `(k + 1) / 2`) laisse place à un bruit basse fréquence au hash du secteur,
   mêmes sommets. Vérifier aussi la limite `seuil` (frange claire/fond).
5. **Mesure** : captures `smoke -B` et `full`, ×0,5 et ×1, s6, s12, s20, s30 ; lire les PNG. Chercher tout alignement restant.
   `tools/perf_vm.sh` avant/après : draw calls constants, nombre de sommets `[n=…, VM]`.
6. `dotnet build Symbiose.csproj` vert.

## Golden

**INTACT** (vue pure).

## NE PAS

Modifier le moteur. Toucher aux arbres (③). Lancer `tests/test_epaisseur_500ans.py`.

## F5

Taches de fleurs crédibles, plus de quadrillage ; insectes sur les fleurs ; prairie sans rectangles.
