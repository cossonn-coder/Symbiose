# Sprint Croissance·4 — **Rendu pixel de la structure** (Godot / C#)

> **Kickoff autosuffisant.** Démarrage à froid : tu reprends sans contexte
> préalable. Lis ce fichier en entier, puis les sources citées, puis exécute.
> Carte blanche (conception figée) : implémente sans re-valider chaque étape,
> rends compte après. Français + **pédagogie RENFORCÉE** : c'est un tronçon
> **frontend Godot/C#**, le terrain où Nico est **débutant** (il vient du
> C/Python embarqué, expert simulation). Explique les idiomes Godot que tu
> emploies (`_Draw`, `Node2D`, `DrawLine`, filtre Nearest, palier de zoom) —
> pas juste le code, le *pourquoi* de l'API.
>
> Tronçon **moyen-gros** : 1 outil Python **read-only** (export JSON) + 2-3
> fichiers C# (struct miroir `Segment`, chargeur JSON, renderer `Node2D`).
> Synchro cohérente multi-fichiers assumée (l'exception « un fichier à la fois »
> est levée pour ce tronçon). **GOLDEN INTACT** (≠ tronçon 3bis) : on n'ajoute
> **aucune lecture nouvelle** au moteur Python — juste un **exporteur qui lit**
> l'état déjà calculé. Zéro changement de dynamique → `golden_hash` inchangé.

## Ce que c'est, en une phrase

Le **premier rendu visible des branches** : on projette la structure de segments
(cm 3D sol, déjà poussée par le vrai moteur) en **isométrie d'affichage** et on
la **rastérise en pixels** côté Godot, aux paliers de zoom ×4…×32 avec **LOD**
(silhouette de couronne en vue large, détail segment en vue serrée, §H.1/§H.3).
La maquette SVG `tools/apercu_structure.svg` (tronçon 3bis) montre **exactement**
la cible visuelle — ici on refait la même projection, mais en pixels Godot et
fed par les **vraies données du moteur**.

## Le principe directeur (à NE PAS contourner)

**Python reste la source de vérité.** On ne **porte PAS** le moteur de croissance
(`sim/growth.py`) en C# — ce serait la dette D24, hors sujet et énorme. À la
place, **Python EXPORTE** la structure déjà calculée en **JSON déterministe**, et
**C# la LIT et la DESSINE**. Le C# de ce tronçon est un **consommateur passif** :
zéro logique écologique, zéro RNG, juste géométrie → pixels. Ce pont JSON
**préfigure** le save §J (tronçon 6) mais ne le verrouille pas (pas encore de
`engine_version`, pas de contrat de sérialisation — juste de quoi nourrir le
rendu).

> Pourquoi ce détour plutôt que « brancher Godot sur la sim » ? Parce que la sim
> n'existe **qu'en Python** (le C# est très en retard, dette D10/D24). Tant que
> le portage n'est pas fait, le seul moyen de voir les **vraies** plantes du
> moteur dans Godot, c'est de **transporter leur état** par fichier. C'est aussi
> ce que fera le save (§J) : on réutilise donc l'effort.

## Décisions déjà tranchées (avec Nico) — NE PAS re-débattre

1. **Périmètre = rendu PUR, alimenté par export JSON.** Pas de portage moteur,
   pas de croissance live dans Godot, pas de tick C#. On affiche des structures
   **figées** exportées depuis Python (les 4 spécimens de la maquette + de quoi
   choisir lesquels).
2. **Données = fichier JSON exporté par un outil Python read-only.** Golden
   intact (l'outil **lit** `grow_plant`, ne le modifie pas). Format minimal :
   par plante, la liste des segments (géométrie) + l'empreinte dérivée (pour la
   silhouette LOD).
3. **Pas d'organes** (feuilles/fleurs/fruits) = tronçon 5, le risque n°1 (§H.2/§K).
   Ici **uniquement le bois** (segments) + la **silhouette de couronne** (ellipse
   de l'empreinte §G). Apex en vert, bois en brun — comme la maquette SVG.
4. **Projection iso identique à la maquette** (`tools/render_structure.py:_iso`)
   pour cohérence visuelle : `(dx,dy,dz)cm → ((dx−dy)·cos30, (dx+dy)·sin30 − dz)·k`.
   Le collet de la plante se pose à la **position écran de son plot-foyer**
   (`TileGrid.HexToScreen`), les segments projettent **relativement au collet**.

## Les obstacles (le cœur du tronçon)

**Obstacle 1 — il n'y a AUCUN `Segment` en C#.** `core/PlantData.cs` modélise
encore la plante à l'**ancien modèle** (offsets de plots `FoliarOffsets`/
`RootOffsets`, hérité d'avant la croissance procédurale) — il **ignore** la
structure de segments. Il faut donc créer un **miroir C#** du `Segment` Python
(`plants/base.py:130-141` : `base` xyz, `dir` xyz unitaire, `length_cm`,
`thickness_cm`, `is_apex` — les seuls champs utiles au rendu ; `age_weeks`,
`auxin`, `has_bud` non rendus). Un `struct`/`record` C# léger + un chargeur JSON.
**Ne touche pas** `PlantData.cs` (l'ancien modèle survit pour le reste).

**Obstacle 2 — réconcilier DEUX projections iso.** La maquette projette en iso
**relatif au collet** (cm → px, formule `_iso`). `TileGrid.cs` projette les
**tuiles** au sol avec une **autre** formule (`HexToScreen`, `TileW=96/TileH=48`,
décalage hexagonal `col%2`). Les deux doivent s'emboîter : le **collet** d'une
plante = `HexToScreen(plot_row, plot_col) + GridOffset` (sa position au sol dans
la grille existante), **puis** chaque segment ajoute son offset iso `_iso(seg −
collet_cm, …)`. Attention à l'**échelle** : `TileGrid` est en pixels d'écran,
`_iso` a un facteur `PX_PER_CM=0.42` (maquette) — à recaler sur l'échelle réelle
du jeu (1 plot = 50 cm = `TileW` px au sol ? à mesurer/choisir, point ouvert).

**Obstacle 3 — pixel art, pas vecteur.** `DrawLine` de Godot **anti-aliase** par
défaut → des branches floues, incohérentes avec le pixel art (filtre **Nearest**
partout, CLAUDE.md). Deux options : (a) `DrawLine(..., antialiased: false)` +
épaisseur arrondie au pixel du **palier de zoom** ; (b) rastériser soi-même
(petits rects/quads alignés grille). Commence par (a) (simple), signale si le
rendu « bave » aux paliers entiers. C'est le **risque esthétique** du tronçon
(moindre que les organes du tronçon 5, mais réel).

**Obstacle 4 — d'où vient le palier de zoom ?** Le LOD (§H.3) est piloté par le
zoom ×4/×8/×16/×32. Si la caméra/zoom n'est **pas encore câblée** dans la scène
(probable — beaucoup de C# est stub), **stub un palier fixe** (p.ex. ×16, détail
segment) avec un commentaire `// TODO zoom réel` et expose une variable
`[Export] int ZoomPalier`. Ne construis pas un système de caméra ici (hors sujet).

## Lis d'abord, dans cet ordre

1. `data/code/CONCEPTION_CROISSANCE.md` — **§H** en entier (H.1 projection→pixels,
   H.2 organes = **ce qu'on NE fait PAS ici**, H.3 LOD), **§G** (empreinte dérivée
   = la silhouette LOD), **§J** (save — ce que le pont JSON préfigure sans le
   verrouiller), **§K** (perf rendu = distinct de la sim, maîtrisé par LOD).
2. `data/code/tools/render_structure.py` — **LA RÉFÉRENCE**. La fonction `_iso`
   (`:35-37`) est la projection à reproduire en C# ; `_panel` (`:51-91`) montre
   le tri par épaisseur (bois épais dessous), la couleur apex/bois, l'ellipse de
   couronne. Le SVG produit (`tools/apercu_structure.svg`) = la cible visuelle.
3. `sprints/sprint_croissance/00_etat.md` — état + tronçons 1/2/3/3bis faits ; la
   structure de segments y est décrite (source Python déterministe).
4. Code — **les ancrages** :
   - `data/code/plants/base.py:130-141` — `class Segment` (les champs à exporter/
     mirrorer) ; `:147-232` — `PlantInstance` + `update_footprint`/`footprint_value`
     (l'empreinte `height`/`canopy_radius` pour la silhouette LOD, pure géométrie).
   - `world/TileGrid.cs:78-83` — `HexToScreen(row,col)` (où poser le collet) ;
     `:12-13` `TileW/TileH` (l'échelle écran existante à réconcilier) ; `:9` la
     plante doit vivre comme `Node2D` enfant, comme les tuiles.
   - `core/PlantData.cs` — l'ancien modèle (offsets de plots) : **constate** qu'il
     n'a pas de segments, **ne le modifie pas**.
   - `visuals/PlantAnimator.cs` — le stub d'animation de plante existant (point
     d'accroche naturel, ou crée un `visuals/PlantRenderer.cs` à côté — au choix,
     signale lequel).

## Périmètre

### A. Python — exporteur JSON **read-only** (golden INTACT)
Crée `data/code/tools/export_structure.py` (calqué sur `render_structure.py` :
même `_grow`, mêmes spécimens, même déterminisme `SEED`). Au lieu d'émettre du
SVG, **dump un JSON** : `{ "specimens": [ { "title", "species", "footprint":
{"height_cm","canopy_radius_cm"}, "collet_cm":[x,y,z], "segments": [ {"base":
[x,y,z], "dir":[x,y,z], "length_cm", "thickness_cm", "is_apex"} … ] } … ] }`.
Usage `python3 -m tools.export_structure tools/structure.json`. **Ne lit que**
`grow_plant`/`footprint` (déjà calculés) → **zéro impact golden**. Écris le JSON
dans `data/code/tools/structure.json` (commité, pour que Godot le trouve sans
lancer Python).

### B. C# — miroir `Segment` + chargeur JSON
Un `record struct` (ou `class`) C# `Segment` (namespace `Symbiose`) avec
`Vector3 Base, Dir; float LengthCm, ThicknessCm; bool IsApex`, **et** un petit
DTO plante (`Title, SpeciesName, HeightCm, CanopyRadiusCm, ColletCm, Segments`).
Un chargeur JSON (Godot a `Json.ParseString` natif, OU `System.Text.Json` —
explique lequel et pourquoi). Lit `res://…/structure.json` (ou un chemin de
projet — signale où tu le ranges côté Godot). **Pas de logique**, juste du
parse → objets.

### C. C# — renderer `Node2D` (la projection + rastérisation)
Un `Node2D` (`visuals/PlantRenderer.cs` ou extension de `PlantAnimator`) qui, en
`_Draw()` (le rappel de **dessin immédiat** de Godot — explique-le) :
1. **Projette** chaque segment via un `Iso(dx,dy,dz)` C# = portage **exact** de
   `_iso` (cos30/sin30/`PX_PER_CM` ou l'échelle recalée, obstacle 2). Origine =
   le collet, posé à `HexToScreen(plotRow, plotCol) + GridOffset`.
2. **Rastérise** : `DrawLine(p1, p2, color, width, antialiased:false)` par
   segment, **trié par épaisseur décroissante** (bois épais dessous, fines
   brindilles au-dessus — comme `_panel`), couleur **apex vert / bois brun**,
   largeur ∝ `thickness_cm × échelle` arrondie au pixel du palier (obstacle 3).
3. **LOD (§H.3)** : si `ZoomPalier ≤ ×4` → ne dessine **PAS** les segments,
   dessine **une ellipse de silhouette** (`DrawCircle`/arc aplati) à partir de
   `CanopyRadiusCm` (empreinte §G). Si `≥ ×8` → détail segment. Palier stubbable
   (obstacle 4). **Pas d'organes** (tronçon 5).

### D. Intégration scène (minimale)
Instancie 1-N `PlantRenderer` dans la scène principale (`TileGrid.tscn` ou un
nœud parent), chacun pointant un spécimen du JSON, posé sur un plot. But = **voir
les branches à l'écran**, pas un système de spawn complet (ça viendra avec le vrai
gameplay). Hardcode/`[Export]` les positions de démo. Signale comment lancer la
scène (Nico ouvrira Godot ; toi tu ne peux pas — cf. Vérification).

## Hors périmètre (NE PAS faire ici)
**Organes** (feuilles/fleurs/fruits procéduraux, palette/saison) = **tronçon 5**
(le risque n°1, §H.2). **Save** sérialisation §J = **tronçon 6** (le JSON d'ici
le préfigure mais ne le verrouille pas : pas d'`engine_version`, pas de contrat).
**Portage du moteur** `sim/growth.py`/`engine.py` en C# (dette D24) — on consomme
l'export, on ne recalcule rien. **Système de caméra/zoom** complet (stub un
palier). **Croissance live** tick-par-tick dans Godot. **Phototropisme/lumière**
visuels. Ne **modifie pas** le moteur Python (golden doit rester intact).

## Vérification (success criteria)

⚠️ **Réalité GUI** : ce tronçon produit du **visuel Godot**, que **tu ne peux pas
lancer toi-même** (pas de Godot headless ici, pas de rastériseur). Sois **honnête**
là-dessus : ne déclare pas « ça marche » sur le rendu — déclare ce que tu **as**
validé et ce qui reste à l'œil de Nico.

Ce que tu PEUX et DOIS vérifier :
```
cd data/code
python3 -m tools.export_structure tools/structure.json   # produit le JSON
python3 -m tests.test_golden        # INTACT (5a5f1cee…) — l'exporteur ne touche rien
python3 -m tests.test_croissance    # 57/57 INCHANGÉ
python3 -m tests.test_population && python3 -m tests.test_vigueur   # INTACTS
# + JSON bien formé : python3 -c "import json; json.load(open('tools/structure.json'))"
```
Côté C# : **compile** (`dotnet build` si dispo, sinon vérifie la cohérence de
syntaxe/namespace `Symbiose`/usings à la relecture et signale que la compilation
reste à confirmer dans Godot). **Critère dur** : (1) l'export JSON existe, est
déterministe (2 runs = même fichier) et bien formé ; (2) golden + toute la suite
Python **intacts** (aucune fuite, c'est un ajout read-only) ; (3) le code C#
existe, projette via le portage exact de `_iso`, rastérise apex-vert/bois-brun
non-anti-aliasé trié par épaisseur, et dégrade en silhouette au zoom faible ;
(4) la doc dit **précisément** à Nico comment ouvrir la scène et **quoi regarder**
(les 4 spécimens, le pommier qui s'étale an 3→10). Mets à jour `00_etat.md`
(tronçon 4 ✅ : pont JSON read-only, miroir `Segment` C#, renderer iso+LOD, golden
intact), **mets à jour `journal.md`** (fin de sprint Croissance·4), commit,
`/clear`, lance `05_*.md` (organes — le risque n°1, **à confirmer** avec Nico
avant : c'est itératif et esthétique, il voudra cadrer).

## Points ouverts (défaut sobre + signaler)
- **Échelle px/cm dans Godot** : la maquette utilise `PX_PER_CM=0.42` (arbitraire,
  pour tenir dans un panneau SVG). Dans le jeu, l'échelle est fixée par `TileW`/
  `TileH` et `PLOT_CM=50`. **Choisis** une échelle cohérente (1 plot sol = combien
  de px ? → cm/px dérivé) et documente-la. Défaut sobre : recale `PX_PER_CM` pour
  qu'un arbre de 350 cm fasse une hauteur écran « raisonnable » vs une tuile.
- **`Json` Godot vs `System.Text.Json`** : `Json.ParseString` est natif (zéro
  dépendance, retourne des `Variant`/Dictionary) mais peu typé ; `System.Text.Json`
  est typé mais c'est du .NET pur. Défaut : **Godot `Json`** (idiomatique moteur),
  signale le compromis.
- **Où ranger `structure.json` côté Godot** : `res://data/structure.json` ?
  `res://assets/` ? À ranger là où SpriteLoader/les autres assets vivent — vérifie
  la convention du projet et signale le chemin retenu.
- **`PlantRenderer` neuf vs extension de `PlantAnimator`** : défaut = **fichier
  neuf** `visuals/PlantRenderer.cs` (le rendu de structure ≠ l'animation de
  sprite ; ne pas mélanger). Signale si tu préfères fusionner.
- **Palier de zoom** : stub `×16` fixe (`[Export]`) si la caméra n'est pas câblée.
  Le vrai branchement zoom→LOD viendra avec le système de caméra (hors sprint).
