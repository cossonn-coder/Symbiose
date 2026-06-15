## 2026-06-06 — Sprint Croissance·4 : premier rendu pixel des branches (Godot/C#)

Premier tronçon **frontend** du sprint Croissance : on **voit** enfin les branches.
La sim de croissance vit **uniquement en Python** (source de vérité, dette de portage
D24 hors sujet) — pour afficher les **vraies** plantes du moteur dans Godot sans le
porter, on construit un **pont JSON read-only**.

**Décision : pont JSON, C# consommateur passif.** `data/code/tools/export_structure.py`
rejoue le moteur déterministe (mêmes spécimens/SEED que la maquette
`render_structure.py`) et **dump** la géométrie en `tools/structure.json` (Tomate
40 seg ; Pommier an 3/7/10 — an 10 h≈351/cr≈197). L'exporteur ne **lit** que
`grow_plant`/l'empreinte → **golden INTACT** (`5a5f1cee…`, + population/vigueur/
croissance 57/57 inchangés). Ce pont **préfigure** le save §J (tronçon 6) sans le
verrouiller (pas d'`engine_version`, pas de contrat).

**Décision : projection iso partagée avec la maquette, ancrage par le collet.**
`visuals/PlantRenderer.cs` (`Node2D._Draw`) porte **exactement** `_iso`
(cos30/sin30/`PxPerCm`=0.42 `[Export]`), rastérise chaque segment en
`DrawLine(antialiased:false)` trié par épaisseur décroissante (bois épais dessous),
**apex vert / bois brun**, largeur arrondie au pixel (cohérence pixel art, filtre
Nearest). Le collet se pose à `HexToScreen(row,col)+GridOffset` de la grille
existante ; les segments projettent **relativement** au collet. **Obstacle assumé** :
la grille (quinconce `HexToScreen`) et la plante (iso vrai `_iso`) ne sont **pas le
même modèle de projection** — on ne partage que l'**ancrage**, pas l'échelle. L'échelle
« vraie » jeu (PLOT_CM=50 ↔ TileW) reste un **point ouvert** → défaut 0.42 (validé à
l'œil sur la maquette SVG), `[Export]` pour réglage en direct.

**Décision : miroir minimal de `Segment` en C#, sans toucher l'ancien modèle.**
`core/PlantStructure.cs` = `record struct Segment` (Base/Dir/Length/Thickness/IsApex,
les seuls champs utiles au rendu) + DTO `PlantStructure` (empreinte pour la
silhouette LOD) + chargeur **`Json.ParseString`** natif Godot (vs `System.Text.Json` :
idiomatique moteur, zéro dépendance .NET, au prix d'un typage manuel — négligeable
ici). Lit `res://data/code/tools/structure.json` **directement** (source unique, pas
de copie). `core/PlantData.cs` (ancien modèle à offsets de plots) **non touché**, il
survit pour le reste du C# non porté.

**LOD §H.3** : `ZoomPalier≤4` → silhouette de couronne (ellipse dérivée de l'empreinte
§G) au lieu des brindilles ; `≥8` → détail segment. Palier **stubé** `[Export]`=16 (la
caméra/zoom n'est pas câblée — `// TODO zoom réel`). **Pas d'organes** (feuilles/fleurs/
fruits = tronçon 5, le risque n°1).

**Intégration** : `TileGrid` (scène principale `TileGrid.tscn`) spawne 4 `PlantRenderer`
de démo (`[Export] ShowPlantDemo`), un par spécimen, sur des plots espacés.

**Limite honnête** : pas de `dotnet` CLI dans l'environnement → **compilation C# non
vérifiée** et **rendu non lancé**. À confirmer par Nico dans Godot : ouvrir
`TileGrid.tscn` (scène principale, F5) → 4 plantes au-dessus de la grille, le pommier
qui s'étale an 3→10. Si les traits « bavent » aux paliers entiers, c'est l'obstacle
esthétique anticipé (rastérisation manuelle en repli).

**Statut.** Tronçon 4 ✅. Prochain = **tronçon 5 — organes procéduraux** (risque n°1,
itératif/esthétique) : **à cadrer avec Nico avant** de lancer.

---
