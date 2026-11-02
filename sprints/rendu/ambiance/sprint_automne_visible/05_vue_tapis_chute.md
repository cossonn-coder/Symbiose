# ⑤ Vue : tapis de feuilles et chute — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, `mesures/apres_feuilles.md`,
`visuals/LeafLitterLayer.cs` (en-tête), conception §3.2 et §3.4.

## Objectif

On voit les feuilles tomber, puis le tapis se former et se défaire avec la décomposition.

## À faire

1. **Tapis** (`visuals/LeafLitterLayer.cs`, `world/WorldView.Compost.cs`) :
   - lire le 9ᵉ élément de `litiere` (③) au lieu du seul tissu dominant, avec repli si absent ;
   - visible dès ×1 (`MinZoom` = 2 aujourd'hui), le zoom de jeu du joueur ;
   - densité recalibrée sur les masses réelles de `mesures/apres_feuilles.md` (`MasseRef`, `MaxLeaves` = 6
     est trop bas pour un tapis) ; à ×1, un simple pixel coloré peut suffire ;
   - couleurs chaudes fraîches, puis brunes avec `age_sem`, dans la palette indexée.
   Couleur par espèce impossible : le moteur ne trace pas l'espèce de la litière (D50) ; le signaler.
2. **Chute** : nouveau calque en lot (patron `visuals/ForagerLayer.cs` + `PollenLot.cs`), un seul CanvasItem,
   hash déterministe, feuilles de la couleur de l'arbre, qui descendent en oscillant et suivent le vent réel
   (`WindWave.cs`). Actif seulement pour les plantes dont `feuillage` baisse, à l'arrêt sinon. Respecter la
   pause et la rotation de vue (patron `WorldToScreen`).
3. **Mesure** : captures `full` en s33-37 à ×1 et ×4 (animation : plusieurs frames) ; `tools/perf_vm.sh` en
   pleine chute. Budget : pas plus de quelques draw calls supplémentaires `[n=…, VM]`.
4. `dotnet build Symbiose.csproj` vert.

## Golden

**INTACT** (vue pure).

## NE PAS

Modifier le moteur. Lancer `tests/test_epaisseur_500ans.py`.

## F5

Chute visible sans gêner ; tapis lisible à ×1 ; il disparaît au fil de l'hiver et du printemps.
