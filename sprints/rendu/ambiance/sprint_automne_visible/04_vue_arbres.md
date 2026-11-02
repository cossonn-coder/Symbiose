# ④ Vue : des arbres ressemblants, qui prennent leurs couleurs — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, `docs/vegetal/croissance/fiches_arbres.md`,
`docs/rendu/pixelart/etude_brief_da_16bits.md`, conception §3.1 et §3.3.

## Objectif

On reconnaît chaque arbre et sa couleur d'automne, à ×1 comme à ×4. La couronne s'éclaircit.

## À faire

1. **Recettes** : traduire chaque fiche dans le rendu : palette (`PlantRenderer.Organs.cs`, `Palettes`),
   forme de couronne par paliers (`PlantRenderer.Paliers.cs`, `Port()` traite aujourd'hui tous les arbres
   pareil), forme de feuille.
2. **Couleur d'automne par espèce** : `AutumnLeaves` est une palette commune à tous. La remplacer par
   une couleur tirée de la fiche, y compris dans `TeinteSaison` (paliers) et la palette indexée (couleur
   visible avec F11 ON). L'aulne reste presque vert, le sapin inchangé.
3. **Couronne qui s'éclaircit** : lire `feuillage` (③, `core/PlantStructure.cs`) et sous-échantillonner
   les feuilles au hash, comme `FoliageDensity`. Absent du snapshot → 1.
4. **Vérifier la recuisson** : une plante ne se redessine qu'après `Invalidate` : confirmer qu'un
   changement de `automne` ou de `feuillage` déclenche une cuisson (sinon l'arbre garde son image verte).
5. **Mesure à l'écran** : `tools/capture_vm.sh` sur `full`, un arbre à ×1 et ×4 en s20, s33, s37, s42 ;
   ouvrir les PNG et vérifier couleur, éclaircissement, arbres nus en hiver. Vérifier avec `tools/perf_vm.sh`
   que FPS et draw calls restent stables `[n=…, VM]`.
6. `dotnet build Symbiose.csproj` vert.

## Golden

**INTACT** (vue pure).

## NE PAS

Traiter les 37 autres espèces (reste de D118). Lancer `tests/test_epaisseur_500ans.py`.

## F5

Reconnaître chaque arbre ; automne visible sur chaque caduc.
