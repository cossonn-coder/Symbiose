# ③ Palette indexée + éclat côté soleil — paliers bas ×0,5 / ×1 / ×2

Lire d'abord : `CLAUDE.md`, `00_etat.md` (§Notes ① : table des rampes, banc de mesure,
mesures de base), `docs/rendu/pixelart/etude_brief_da_16bits.md`,
`docs/rendu/pixelart/conception_casse_ecran.md` §2 (points 2, 3, 4) et §4.
**Golden intact.** Filet : `dotnet build Symbiose.csproj`. Pas d'appel DeepSeek.
Ne JAMAIS lancer `test_epaisseur_500ans`. Tronçon **structurant** : il pose le pipeline
que ④⑤⑥ réutilisent.

## Objectif
Les plantes des paliers bas passent en **palette indexée** (analogue CGRAM SNES) :
1. La **précuisson** (`visuals/PlantRenderer.Kit.cs`, `PlantRenderer.Bake.cs`,
   `PlantBaker.cs`, `AtlasPages.cs`) n'écrit plus une couleur finale mais, par pixel :
   un **indice de ton** dans la rampe (creux / moyen / clair / éclat…), un **code
   d'orientation de la face** (normale 2D quantifiée, ex. 8 directions + « plat »), et
   la **matière** (ligne de LUT). Encodage dans les canaux de l'atlas au choix (documenté).
2. Un **shader de lecture** unique (un seul `ShaderMaterial` partagé par toutes les plantes
   → le regroupement des draw calls est préservé) lit l'indice, l'orientation, et une
   **texture LUT globale** (une ligne par matière, issue de la table des rampes ①), plus un
   uniform global = direction du soleil à l'écran (`WorldView.SunShadowDir`,
   `world/WorldView.Soleil.cs:24`, opposée à l'ombre ; `SunStrength` pour l'intensité).
   Face tournée vers le soleil → ton monté d'un cran (jusqu'à l'éclat), face opposée →
   descendu d'un cran. Résultat : **éclat du côté du soleil réel**, qui suit la journée et
   la rotation D35, **sans aucune recuisson**.
3. **Contour** : supprimé sur les masses (touffes, feuillage : `KitContour`,
   `MaitreSombre 2e3038`, `KitContourMin`) ; gardé sur les petits objets (fleurs —
   `PlantRenderer.Flower.cs`) mais en **teinte la plus sombre de la rampe de l'objet**.
   Les interstices entre feuilles = ton « creux » teinté de la rampe, jamais un fond uni.
4. `Eclairement()` (`Kit.cs:286`) cesse d'éclairer le bas de la touffe : il produit
   l'orientation de face (et un grain au hash) ; la lumière vient du shader.
5. **Ombres portées teintées** : `PlantShadow.cs:38` (noir alpha 0,18) → vert-noir
   (`#071010` ou le creux de la rampe du sol) à alpha équivalent en contraste. Idem ombre de
   la maison si elle est noire.
6. **F11 retiré** : la quantification plein écran (`visuals/PaletteSnes.cs` +
   `palette_snes.gdshader`) est **débranchée** du chemin de rendu ; les fichiers sont GARDÉS
   (règle Nico : ne jamais supprimer de code), avec une ligne d'en-tête « débranché au
   sprint CASSÉ À L'ÉCRAN ③ ». La touche F11 est libérée (ou montre l'avant/après LUT). ⚠️ `PaletteSnes.cs` porte AUSSI le shader de **vision**
   (`vision.gdshader`, `_matVision`) du psilocybe : il doit continuer à marcher. F11 est
   OFF par défaut aujourd'hui → la vue par défaut (dont le « dégradé des plots » que Nico
   aime) ne doit pas changer pour le sol.
7. **Ce qui doit survivre** : météo par plante (`PlantRenderer.Meteo.cs`, `Froid.cs`,
   `MeteoPlantes.cs` — trempé, givre, canicule), symptômes, fondus d'apparition, poses au
   vent (`PlantRenderer.Wind.cs`, 8 poses), santé à ×2, signes (couleur physiologique).
   Choisir pour chacun : variante de LUT, modulate, ou indice — documenter.

## Validation (banc ①)
Planche ×0,5/×1/×2 + monde `full` : ≤ 5 tons par matière, 0 pixel `#000`/quasi-noir
neutre sur masse, dérive de teinte dans le bon sens, éclat du côté du soleil à 3 heures
(matin, midi, soir via `-m`/heure de capture ou un argument à ajouter) × 2 rotations,
voisins non identiques. Comparer aux mesures de base ①. Perf : `tools/perf_vm.sh` avant /
après (draw calls inchangés ou mieux ; frame ≤ +10 %).

## Ne PAS faire
Toucher aux paliers ≥ ×4 (④) sauf si une interface commune l'exige (alors sans changer
leur rendu) ; changer le sol ; introduire du `Random` ; toucher `data/code/`.

## Fin de tronçon
Captures lues avec Read, rapport du banc avant/après, perf avant/après dans `00_etat.md`
§Notes ③ (+ l'encodage choisi, pour ④⑤⑥) ; commit. F5 Nico : ×1/×2 au lever, midi,
coucher ; tourner la caméra.
