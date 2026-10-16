# Sprint RENDU VISIBLE (D106) — état partagé

> Conception FIGÉE le 2026-10-16 (`/conception D106`) →
> [`docs/perf/lod/conception_rendu_visible.md`](../../../../docs/perf/lod/conception_rendu_visible.md)
> (LIRE AVANT TOUT TRONÇON : diagnostic chiffré + décisions D1-D6 + échelle des paliers).
> **Vue C# pure** : `data/code/` intouché, **golden jamais re-figé** (référence
> `22768f33…`, à vérifier en tête de T1 : `cd data/code && python3 -m tests.test_golden`).

## Décisions clés (Nico)
- **D1 critère de fin** (PC Nico, HD 4600, `full`) : 60 FPS à ≥ ×4, 30 FPS à ×0,5-×2.
- **D2** semaine appliquée paresseusement hors marge (à l'entrée ou à la consultation).
- **D4** échelle cumulative : ×0,5 présence+saison · ×1 port · ×2 santé · ×4 architecture ·
  ×8 organes · ×16 symptômes fins · ×32 intime. Art NEUF, plantes toujours visibles.
- **D5** plante trop petite au palier → **tapis de son plot** ; un seul tapis (fusion
  `CouvertureLayer`).
- **D6** marge + travail hors champ pour toutes les couches ; paliers faune → sprint B.

## Carte des tronçons
| # | Kickoff | Contenu | Golden | État |
|---|---|---|---|---|
| T1 | `01_instrument.md` | F4 draw calls + bascule couches + `tools/perf_vm.sh` | intact | **fait** (`a5fa36b`, F5 Nico à faire) |
| T2 | `02_sol_un_lot.md` | sol = 1 maillage/tuile, image identique | intact | **fait** (`7868373`, F5 Nico à faire) |
| T3 | `03_plancher_fixe.md` | souris 1×/frame, survol paresseux, plein écran à la demande | intact | **fait** (`8d49ab9`, F5 Nico à faire) |
| T4 | `04_marge_paresseuse.md` | marge proportionnelle + hystérésis, semaine paresseuse | intact | **fait** (`4b6e402`, F5 Nico à faire) |
| T5 | `05_paliers_bas.md` | ×0,5/×1/×2 + tapis par plot | intact | **fait** (`7912b1a`, F5 Nico à faire) |
| T6 | `06_paliers_hauts.md` | ×4/×8/×16/×32 + cellules d'atlas par pose | intact | **fait** (non commité, F5 Nico à faire) |
| T7 | `07_banc_bilan.md` | planche des paliers F5 + bilan contre D1 | intact | à faire |

## Mesures de référence (VM llvmpipe, 2026-10-16)
×0,5 : 5,2-5,5 FPS [3 runs] ; sans sol 11,7-12,0 [3 runs] ; ×4 : 12-13 FPS [4 runs] ;
tout masqué 20-26 FPS [n=3, bruités]. ⚠️ Vérifier `uptime` avant de mesurer (load 17 vu
une fois → runs aberrants). Métrique portable = draw calls/frame (T1).

**Référence T1** (`tools/perf_vm.sh`, `full` seed 42, 2026-10-16, charge < 4, moyenne de
6 relevés de 1 s après 4 ignorés ; draw calls stables ±0,3 % d'un run à l'autre) :

| Cas | FPS VM | draw calls | objets | primitives |
|---|---|---|---|---|
| ×0,5 tout | 5,1-5,4 [2 runs] | **3825** | 4223 | 26 200 |
| ×0,5 sans `Ground` | 11,9-12,4 [2 runs] | **1439** | 1837 | 19 020 |
| ×0,5 sans `Decor` | 5,4 [n=1] | 2992 | 3390 | 11 113 |
| ×0,5 sans `Objects` | 4,1 [n=1, plus lent que « tout » : bruit ?] | 3257 | 3647 | 23 476 |
| ×4 tout | 13,0-13,2 [2 runs] | **1522** | 2304 | 35 621 |
| rien du monde (×0,5 et ×4) | 26,4-27,6 [n=1 chacun] | 36 | 416 | 1215 |

→ le sol coûte ~2390 draw calls [×0,5, 2 runs] = la cible de T2 ; plancher fixe ~36 ms
[n=2] à 36 draw calls (coût CPU, pas GPU → T3).

**Mesures T2** (`tools/perf_vm.sh`, `full` seed 42, 2026-10-16, charge < 4) :

| Cas | FPS VM avant → après | draw calls avant → après |
|---|---|---|
| ×0,5 tout | 5,1-5,4 → **12,2** [2 runs chacun] | 3825 → **1456** |
| ×0,5 sans `Ground` | 11,9-12,4 [2 runs] → 13,2 [n=1] | 1439 → 1439 |
| ×4 tout | 13,0-13,2 → 15,0 [2 runs chacun] | 1522 → 1520 |

→ le sol passe de ~2390 à **17 draw calls** [×0,5] (8 tuiles + boussole/ombre) ; il
coûte encore ~7 ms [×0,5, n=1 sans `Ground`]. Primitives ×4 : 35 621 → 39 825 (une tuile
partiellement visible envoie tous ses triangles, coût GPU négligeable).
**Image : identique au pixel** (0 pixel différent, sol seul) sur 10 captures avant/après :
×0,5 aux 4 orientations, ×4 et ×16 sur 300,1700, ×4 orientation 1, ×1 après 40 semaines
de warmup (relief monté) ; scène complète ×0,5 : 0 ; ×4 : seuls les sprites animés de la
vie macro diffèrent (phase d'animation).

**Technique retenue T2** (pédagogie dans les en-têtes) :
- `world/SolMaillage.cs` : builder d'`ArrayMesh` par tuile, triangles émis dans l'ordre
  d'avant (flanc puis dessus, plot par plot). Dessus = les 6 sommets du rectangle Sprite2D
  de Godot (mêmes triangles, UV 0/1 exacts : à ×0,5 chaque pixel tombe pile sur une
  frontière de texel → le choix du texel dépend de l'interpolation). **Arrondi Sprite2D
  rejoué CPU** : le SubViewport snappe (`snap_2d_transforms_to_pixel`), Godot arrondissait
  l'origine LOCALE de chaque sprite `floor(pos+0,5)` puis le décalage `floor(−taille/2+0,5)`
  = (−19,−10) ; sans ça ~300 000 pixels différaient. Flanc = `Geometry2D.TriangulatePolygon`
  (la fonction de Polygon2D).
- `world/SolMateriau.cs` : `ShaderMaterial` partagé, **fragment seul** : flanc (UV = −1)
  → couleur de sommet ; dessus → texture × damier, damier en DRAPEAU (blanc/noir) et 0,95
  en constante flottante (une couleur de sommet est sur 8 bits → ±1 sur ~80 000 px sinon).
- `WorldView.Relief.cs` : `SolTuile` (un `MeshInstance2D` par tuile + relief mémorisé) ;
  `UpdateRelief` ne ré-émet que les tuiles dont un plot a bougé. API `ReliefRisePx` /
  `ReliefRiseAtPlot` intactes. `WorldView.Monde.cs` `BuildGround` : 1 nœud/tuile.
- Outils : `capture_vm.sh -r ORIENT -x COUCHES` (+ `--capture-orient=` dans
  `WorldView.Capture.cs`) pour comparer le sol seul aux 4 orientations.
- Leçon (shaders Godot 4.6 GLES3, lue dans le binaire `strings`) : `MODEL_MATRIX` exclut la
  caméra (`CANVAS_MATRIX`), l'arrondi des transforms se fait en espace local du canvas.

**Mesures T3** (`tools/perf_vm.sh`, `full` seed 42, 2026-10-16, charge < 3 attendue avant
chaque run — un autre projet chargeait la VM par moments, runs sous charge écartés) :

| Cas | frame VM avant → après | FPS avant → après |
|---|---|---|
| ×0,5 rien du monde | 32,5-32,6 ms → **29,4-31,2 ms** | 30,7-30,8 [2 runs] → 32,0-34,0 [3 runs] |
| ×4 rien du monde | 32,0-33,0 ms → **29,1-29,9 ms** | 30,3-31,2 [2 runs] → 33,5-34,3 [3 runs] |
| ×0,5 tout | 81-82 ms → 78,5-79,2 ms | 12,2-12,3 → 12,6-12,7 [2 runs chacun] |
| ×4 tout | 66,7-66,8 ms → 64,5 ms | 15,0 → 15,5 [2 runs chacun] |

Draw calls inchangés (36 / 1456 / 1520). **Gain ~2-3 ms/frame [VM, 2-3 runs]** : le
plancher restant (~29 ms à 36 draw calls) n'est **plus du C#**. Profil `dotnet-trace`
avant : 75 % des échantillons C# dans le SEUL `Viewport.GetMousePosition()` (aller-retour
X11 `XQueryPointer` à chaque appel, ~8 appels/frame) ; après : la souris n'y figure plus,
le 1er poste C# restant est `BakeQueue.PickInto` (cf. ci-dessous), puis `UpdateCameraPan`
(4 `IsKeyPressed`) et la sonde F4 elle-même. Retirer 75 % des échantillons C# n'a rendu
que ~2-3 ms → le C# par frame pèse quelques ms sur ~30 : il n'est plus dominant (critère
d'arrêt du kickoff). Hypothèse (non mesurée) pour le reste : composition llvmpipe plein
écran (upscale SubViewport 480×270 → 1920×1080 + HUD), coût GPU-logiciel propre à la VM.
**Comportement inchangé** : captures avant/après (`-z 2 -c 300,1700 -s 960,560 -g 1` et
`-z 4 … -s 900,500`) — losange + étiquette « Pepper · mature » au même endroit ; seuls
diffèrent la respiration du losange (horloge murale) et la vie macro animée, qui
diffèrent AUTANT entre deux runs « après » (bruit de run, vérifié).

**Technique retenue T3** (pédagogie dans les en-têtes) :
- `world/WorldView.Survol.cs` (neuf) : souris mémorisée depuis `_Input` (tous les
  `InputEventMouse`, jamais consommés) → zéro `GetMousePosition` par frame ; lecture directe
  seulement au démarrage et après `WarpMouse` (`ResemerSouris`, banc capture). **Clé de
  survol** = px souris + transform caméra + orientation + `_survolVersion` + modes
  (étiquettes, gènes, geste armé) ; `_survolVersion++` dans `Etalement.Avancer` (point de
  passage UNIQUE de toute application de snapshot, étalée ou synchrone, rotation comprise).
- Sites lazy (`if (!_survolSale) return;`) : étiquettes, observation plante + vie macro
  (ancres = position snapshot), étiquette conteneur, surbrillance taille, losange
  (position), gènes. La respiration du losange (`AlphaLosange`) et la fin du « tap »
  restent par frame (animations voulues). `TickPiqure` lit la souris de la frame.
  Clic et zoom centré gardent `WorldMouseCanvas()` direct ; conversion px → canvas
  factorisée (`SourisVersCanvas`, une seule formule).
- `visuals/WeatherLayer.cs` : ne `QueueRedraw` plus le voile AU REPOS (redessinait le
  plein écran chaque frame dès `_nebCur > 0,01`) : seulement précipitations, voile qui
  glisse, éclair (+ la frame qui l'efface). `SkyPanel` était déjà paresseux (battement du
  composé = animation voulue).
- **Reporté à T4** (marge paresseuse, même famille « hors champ ») : `BakeQueue.PickInto`
  rebalaye chaque frame TOUT `_dirty` (2 passes × `IsVisibleInTree`) même quand aucune
  plante sale n'est visible (cas normal : les sales hors marge) — à n'évaluer qu'au
  changement de caméra/culling/masque. 1er poste C# restant, ~quelques % du temps C#.

**Mesures T4** (`tools/perf_vm.sh -T 30 -n 40`, `full` seed 42, 30 semaines TURBO pendant
la mesure, charge < 3 au départ ; « avant » = même outillage sans la logique T4) :

| Cas | famille plantes / semaine (médiane) | FPS VM | draw calls | gels > 250 ms |
|---|---|---|---|---|
| ×8 sur 300,1700, avant | 54,1 ms [n=14 semaines, 1 run] | 9,7 | 741 | 6 [1 run] |
| ×8 sur 300,1700, après | **12,7-15,5 ms** [n=17 semaines × 2 runs] | 10,8 [2 runs] | 663-671 | 1-2 [2 runs] |
| ×8 centre (maison, 0 plante à l'écran) avant → après | 55,7 → 10,8 ms [n=16 / 19, 1 run chacun] | 12,1 → 13,2 | 724 → 647 | 0 → 0 |
| ×0,5, avant → après | 54,4 → 53,0 ms [n=14 / 12, 1 run chacun] | 8,6 → 8,1 [bruit] | 1577 → 1577 | 0 → 0 |

→ à ×8, ~120 des ~130 plantes restent en attente chaque semaine ; la famille plantes est
divisée par ~4 [×8, 2 runs]. À ×0,5 tout est dans la marge : gain ≈ 0, c'est normal.
Pire frame ×8 : 297 → 255-270 ms [1 run vs 2]. Le reste du gel n'est plus dans les plantes :
vie macro 28 ms/semaine en médiane [×8, n=18, 2 runs], étalée en tranches de 6 ms → **non
rendue paresseuse** (cf. kickoff : « mesurer d'abord ») ; ces 28 ms sont déjà étalées.
**Vérif « rien de périmé »** : `capture_vm.sh -b full -z 8 -T 4 -p 300,1700 -v 0
-x MacroLife,ForagerLayer,Weather -n 200`, départ à 1700,300 (saut caméra 3 s après la
4e semaine, 8 plantes en attente entrent dans la marge → file) contre départ direct sur
300,1700 : **0 pixel différent** sur les images 120, 150 et 199 ; image non vide.

**Technique retenue T4** (pédagogie dans les en-têtes) :
- `world/MargeVue.cs` (neuf, statique) : la marge commune. Visible +25 %/côté pour
  ENTRER, +50 % pour SORTIR (`Garde(dedans, emprise)`, test sur l'emprise). `Cadre` =
  rectangle stable des couches inertes, ré-ancré (`Version++`) seulement quand la zone
  d'entrée en déborde ou quand le zoom change sa taille. `Mettre` appelé par `CullPlants`
  (pan/zoom/rotation/snapshot + désormais `FrameCamera`).
- `CullPlants` : emprise mémoïsée par plante (`PlantRenderer.EmpriseCanvas`, recalculée
  après `Invalidate` seulement) au lieu du centre + 400 cm fixes ; notifie la file de
  cuisson et la file d'entrée au seul changement d'état.
- `BakeQueue` : ensemble `_eligibles` (sales ET dans la marge) tenu par événements
  (`MarkDirty`, `VisibiliteChangee`) → plus de rebalayage de tous les sales chaque frame
  (le poste C# reporté depuis T3) ; saute les plantes `EnAttente`.
- `WorldView.Attente.cs` (neuf) : semaine paresseuse D2. Famille 1 : plante connue hors
  marge → payload stocké (la dernière écrase la précédente), index dossier/butineurs/clés
  à jour. Entrée dans la marge → file à budget `BudgetPlantesUs`, du centre vers
  l'extérieur, hors étalement en cours. Consultation (clic du dossier F2, segment visé
  par la taille) → application synchrone. Naissances toujours appliquées tout de suite ;
  mortes hors marge retirées sans fondu.
- `Snapshot.cs` : `AppliquerPlante` scindé (index → `MajPlante` / naissance,
  `PositionPlante`) ; le test « sans segments » lit la taille du tableau sans le parser.
- 7 couches inertes (Mulch, Litter, LeafLitter, Couverture, Puddle, Allelopathie, Cover)
  dessinent dans `MargeVue.CadreCouche(CullMarginPx)` et se redessinent au ré-ancrage.
  **Effet de bord voulu** : avant, elles ne se redessinaient jamais au pan → au-delà de
  leur cadre de départ (+48-64 px), rien n'était dessiné jusqu'au snapshot suivant (trou
  au bord en pannant à fort zoom). MacroLife/ForagerLayer (animées, redessinées à chaque
  tick d'animation) gardent volontairement leur rectangle visible serré.
- Outils : `--capture-turbo=n` / `--capture-pan=x,y` (`WorldView.Capture.cs`),
  `perf_vm.sh -T`, `capture_vm.sh -T -p` ; la ligne `[perf]` ajoute `max=` (pire frame) et
  `gels=` (> 250 ms) ; le journal hebdo donne « dont N en attente » + ms de la famille
  plantes ; `[Etalement] vie macro X ms` (capture seulement).

**Mesures T5** (`tools/perf_vm.sh -z 0.5 -w 30`, `full` seed 42, 2026-10-16, charge < 2 ;
« avant » = T4 seul, mêmes options) :

| Cas | FPS VM | draw calls | images cuites (cache) | cuisson initiale ×0,5 |
|---|---|---|---|---|
| ×0,5 avant | 12,6-13,9 [2 runs] | 1534 | 150 (2,6 Mo) | 150 plantes / 25 frames, 2,8-2,9 s [2 runs] |
| ×0,5 après | 9,9-12,8 [2 runs, bruit VM] | **1580** | **132** (2,6 Mo) | 132 plantes / 22 frames, 2,7 s [2 runs] |

→ coût d'affichage inchangé (+46 draw calls [×0,5, 2 runs] : les plantes AVANT étaient
cuites… vides, cf. trou ci-dessous) ; 18 plantes [×0,5, w30, n=1 monde] passent au tapis
au lieu d'être cuites. Pinceau ≤ 0,24 ms/plante. Cuisson d'un palier complet mesurée au
démarrage à ×0,5 (pas de dézoom ×1→×0,5 scripté : la ligne `[Cuisson] file vidée` du
F4/journal le donne au F5).
**Trou trouvé** : le snapshot ne porte pas `CanopyRadiusCm` (0, `PlantStructure.FromSnapshot`)
→ l'ancienne silhouette ×0,5 était une ellipse VIDE : **aucune plante n'était visible à
×0,5** (capture avant/après), et `ContientCurseur` rendait toujours faux. Corrigé côté vue
(rayon = étalement réel des segments), pont intouché.

**Technique retenue T5** (pédagogie dans les en-têtes) :
- `visuals/PlantRenderer.Paliers.cs` (neuf) : `DrawPalierBas` sous `PaliersHautsMinZoom`
  (= 4, le détail segments+organes reste à ≥ ×4 pour T6). Cumulatif : ×0,5 tache
  (teinte d'ESPÈCE `Palettes[].Leaf` → automne (teinte chaude au hash de position) → bois
  ∝ 1−`foliage_density`) ; ×1 + port (`Couronne()` par port + fût/tige) ; ×2 + santé
  (`SymptomTint` = vitalité + colorant dominant) + taches de fleurs (`floraison` ≥ seuil).
  Caduc défeuillé / squelette = vrais segments en bois nu (≥ 1 px interne). Port =
  grimpante (strate) · arbre (strate haute ET bois > `LeafMaxThickCm`) · sinon silhouette
  moteur (tapis/rosette/étalée→couchée/dressée/buisson/touffe). Géométrie = SEGMENTS
  (pas `height_cm`, qui peut valoir 4× le bois dessiné : la plante rétrécirait en zoomant).
  Couronne lisse (10-48 sommets selon la taille).
- **Tapis D5** : `TapisSeuilPx = 3` px INTERNES (max largeur/hauteur projetée × zoom).
  Décidé à chaque `Invalidate` (croissance, pompe de palier) : plante au tapis → image
  libérée, `BakeQueue.Retirer`, ombre masquée, `_Draw` vide. `world/WorldView.Tapis.cs`
  (neuf) agrège par plot (espèce dominante par aire, teinte moyenne, fraction d'aire),
  drapeau `_tapisSale` (MajPlante, retrait, pompe de palier), recalcul hors étalement.
  `CouvertureLayer` = LE tapis : fusion par clé tuile|ligne|colonne avec `couverture_sol`
  (jamais deux voiles) ; plot à petites plantes visible à tout palier (alpha ≥ 0,55,
  taches ≤ 2,6 px internes), plot de couverture seule = LOD d'avant (≥ ×1).
- Picking inchangé (FindPlant itère tous les nœuds, dessinés ou non) ; `ContientCurseur`
  lit la même `Couronne()` que le dessin.
- **Bug corrigé en passant** : `CouvertureLayer` ZIndex 0 → 1 — à ZIndex égal,
  `RebuildWorld` (rotation) recrée le sol en dernier enfant et le dessinait PAR-DESSUS le
  tapis. ⚠️ Même défaut non corrigé (hors périmètre) : `AllelopathieLayer` (ZIndex 0).
- Orphelin : `Palette16.Couronne` n'est plus lu (laissé, palette centrale).
- Taille : `WorldView.Snapshot.cs` 302 LDC 🟡 (+4, une responsabilité) ; autres ≤ 300.

**Mesures T6** (`full` seed 42 sauf mention, 2026-10-16, charge < 3 ; « avant » = T5, même
outillage, build HEAD via `git stash -u`) :

| Cas | avant → après |
|---|---|
| cache au vent ×4 (`capture_vm -w 30 -v 0.9 -c 600,1400`, 43 plantes) | 37,3 → **33,4 Mo** [n=1 chacun] |
| cache au vent ×8 (même cadrage, 13 plantes ; au calme 4,5 Mo) | 45,5 → **40,5 Mo** [n=1 chacun] |
| pinceau ×4, calme (`-w 24 -c 648,1474`, 49 plantes) | 0,77 → **0,13 ms/plante** (max 2,74 → 0,21) [n=1] |
| pinceau ×8 `vieux_pommier` (arbre 70 segments) | max 5,67 → **3,47 ms** [n=1] (0,05 ms/segment) |
| pinceau ×16 / ×32, calme (tournesol 6 segments) | max 3,44 → 3,99 ms / 2,43 → 2,74 ms [n=1 chacun] |
| FPS VM ×4 / ×16 (`perf_vm -c 600,1400 -w 30`) | 12,0 → 12,0 / 16,5 → 17,1 [n=1 chacun], draw calls identiques |

→ **Prémisse du kickoff réfutée** (cellules serrées) : le gain mémoire au vent n'est que
de ~11 % [×4 et ×8, n=1 chacun]. Ce n'est pas l'union des boîtes qui coûte, c'est le
NOMBRE de poses (jusqu'à 8 cellules, la pose couchée étant aussi la plus large) : au vent
le cache reste ~9× celui du calme [×8, n=1]. Levier réel (non fait, hors kickoff) : ne
cuire que les poses que la force du vent courante peut atteindre. Le ×4 cuit ~6× plus
vite [n=1] (masses au lieu de chaque feuille) ; ×16/×32 +15 % [n=1], pas d'explosion de
file. Un grand arbre à ×16+ dépasse `MaxSidePx` → dessin direct, inchangé.
**Images** (montages vus) : poivron ×4 masses où seront les feuilles → ×8 feuilles d'espèce
+ pétiole, morsures disparues → ×16 contour + nervures + morsures → ×32 nervilles ;
basilic grêlé (`effondrement` seed 12345) : encoche + trou + nervures dès ×16 seulement ;
tournesol : point jaune ×4 → capitule ×8 → nervures + morsures ×16 → poils + fleurons
en spirale ×32. Vent ×8 (`-v 1.2`, 40 images) : le collet reste au même pixel d'une pose
à l'autre (pas de saut). Bancs `verger_floraison`/`floraison_saisons` : arbres « vieillis »
SANS structure (1 segment, invisibles) — artefact de banc pré-existant (vu sur HEAD).

**Technique retenue T6** (pédagogie dans les en-têtes) :
- `visuals/PlantRenderer.PaliersHauts.cs` (neuf) : seuils `PalierOrganesZoom` 8,
  `PalierSymptomesZoom` 16, `PalierIntimeZoom` 32 + `AuPalier(z)`. ×4 `DrawMassesFeuillage` :
  les feuilles RÉELLES (même hash de présence, même position que ×8) groupées par 3 voisines
  → une ellipse volumée par paquet ; neige par masse. `DrawFleurs`/`DrawFruits` (déplacés
  d'Organs) : point ×4, organe ×8, pruine ×32. `DrawDetailsFeuille` : ×16 `DrawLeafDamage`
  (déplacé, + nécrose MARGINALE de `secheresse`), ×32 surface par espèce (table `Surfaces` :
  poils / pruine / glandes — drosera). `DrawNervuresSecondaires`, `DrawEtamines` (Simple :
  filets + anthères ; Capitule : fleurons en spirale d'or ; Clochette : style).
- `Organs.cs` 319 → 273 LDC : `PlaceFeuille`/`NbFeuilles`/`PerpFeuilles` (géométrie de
  feuille partagée masses ↔ feuilles, comportement identique). `Froid.cs` : encoches de
  grêle + liseré de givre ≥ ×16 (teinte givrée et neige dès ×4). `Leaf.cs` : nervures ≥ ×16
  pour une plante vivante (la litière garde son LOD, hors périmètre), nervilles ×32.
- **Seuils supprimés car remplacés** : `OrganDetailMinZoom` (PlantRenderer.cs),
  `FlowerShapeMinZoom` (Flower.cs), `LeafOutlineMinZoom` (→ `PalierSymptomesZoom`).
  `LeafShapeMinZoom` garde le repli de la litière.
- **Défauts d'unité corrigés** (révélés par les paliers) : nervures et pétiole tracés en
  1-2 px CANVAS = 16-32 px INTERNES à ×16 (aussi larges que la tige ; de même couleur après
  la quantification SNES, ils faisaient des « taches » sur le limbe) → `NervureLargeurPx`
  0,125 px canvas (2 px internes à ×16) + `NervureShift` 0,45 (≠ 0,22, fondu par la palette
  34 couleurs). Nervures du contour fidèle recalées sur ses demi-axes (elles filaient en
  travers du limbe et en débordaient).
- `PlantBaker.cs` : `Cell` = `Rect2I[] Cells` + `Vector2I[] Origins` par pose, atlas en
  rangée de largeurs variables (hauteur = max) ; chaque pinceau porte son ancrage
  (`Position`), `CanvasTransform` = échelle seule ; `DrawImage` pose la cellule depuis SON
  ancrage. `Wind.cs` : `PoseBounds(k)` remplace `BoundsAllPoses` (+ `LocalBounds` retiré).
  `MaxSidePx` par pose, `MaxAtlasPx` sur la somme, repli dessin direct inchangés.
- Taille : `PaliersHauts.cs` 207 LDC ; tous les fichiers touchés ≤ 300.

## Règles communes à tous les tronçons
- `dotnet build Symbiose.csproj` vert ; golden PASS ; **jamais** `test_epaisseur_500ans`.
- Taille : `python3 tools/compte_ldc.py <fichiers>` ≤ 300 (🟡 ≤ 400 signalé).
- Captures VM : `tools/capture_vm.sh` (cf. sprint jardin vivant `00_etat.md` §T0) ; FPS
  temps réel : `tools/perf_vm.sh` (créé en T1).
- Pas d'appel DeepSeek en routine (CLAUDE.md).

## Outils livrés en T1
- **F4** : 4e ligne « rendu — frame X ms (moy. ~1 s) · draw calls · objets · primitives ·
  couches : <cas> » ; même ligne dans le rapport presse-papier (C). Mesure murale
  (`Time.GetTicksUsec`, pas le `delta` de _Process qui sous-estimait : 7,5 vs 5-6 FPS).
  `world/WorldView.PerfMesure.cs`.
- **Maj+F4** (touche libre, motif Maj+F6) : cycle tout · sans Sol · sans Décor · sans
  Objets · sans vie macro · sans couches au sol · sans ciel/météo/vignette · rien du
  monde. Masquage par nom (`FindChild`), visibilité d'avant restaurée, ré-appliqué en fin
  de `RebuildWorld`. `world/WorldView.Couches.cs`.
- **`tools/perf_vm.sh`** `[-b full] [-z 0.5] [-c X,Y] [-x Nom1,Nom2] [-k 4] [-n 8]` :
  Xvfb + Godot temps réel `--print-fps`, lit les lignes `[perf]` (culture invariante)
  du jeu en mode capture, imprime FPS + draw calls moyens. Attend que la charge
  retombe < 4 (≤ 120 s ; un run llvmpipe pousse lui-même la charge), avertit sinon.
  Amorçage Xvfb/build factorisé dans `tools/lib_vm_godot.sh` (sourcé aussi par
  `capture_vm.sh`, revérifié : 1 image smoke OK). Argument jeu neuf
  `--capture-cacher=` (`WorldView.Capture.cs`).
- Liste « rien du monde » pour `-x` : `Ground,Decor,Objects,MacroLife,ForagerLayer,`
  `Carpophores,Couverture,Allelopathie,Mulch,Puddle,Litter,LeafLitter,Snow,Covers,`
  `Weather,Sky,Vignette`.

## §REPRISE
T1 (`a5fa36b`), T2 (`7868373`), T3 (`8d49ab9`), T4 (`4b6e402`), T5 (`7912b1a`) commités.
**T6 fait** (golden PASS `22768f33…`, build vert), **non commité** (l'orchestrateur commit).
Points F5 Nico ouverts : (T1) F4 + Maj+F4 à ×0,5 et ×4 sur `full` ; (T2) « le sol a-t-il
changé ? » (attendu : non) ; (T3) survol, étiquettes, losange, surbrillance de taille, gènes G,
étiquette conteneur ; voile météo au repos ; (T4) pan rapide ×8 sans plante en retard,
couches au sol jusqu'au bord, clic F2 juste après un pan ; (T5) « au dézoom, je lis où ça
pousse (×0,5), quel port (×1), qui va bien (×2) ? » ; semis = taches du tapis, pas de double
voile ; cliquer dans un tapis sélectionne la plante la plus proche ; arbre caduc nu en hiver ;
seuil `TapisSeuilPx` et formes de port ; rotation (R) garde le tapis ; **(T6) « zoomer = voir
plus ? » à chaque cran ×4→×8→×16→×32 ; masses ×4 lisibles (taille, `MasseFeuilles` = 3) ;
contraste/largeur des nervures (`NervureShift` 0,45, `NervureLargeurPx`) ; poils/étamines
visibles à ×32 ; la grêle et les morsures ne se lisent plus qu'à ×16 (voulu D4) ; pas de
saut de pose au vent.** Prochaine étape : T7 `07_banc_bilan.md`.
