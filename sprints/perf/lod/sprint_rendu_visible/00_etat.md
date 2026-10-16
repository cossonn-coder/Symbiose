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
| T4 | `04_marge_paresseuse.md` | marge proportionnelle + hystérésis, semaine paresseuse | intact | **fait** (non commité, F5 Nico à faire) |
| T5 | `05_paliers_bas.md` | ×0,5/×1/×2 + tapis par plot | intact | à faire |
| T6 | `06_paliers_hauts.md` | ×4/×8/×16/×32 + cellules d'atlas par pose | intact | à faire |
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
T1 (`a5fa36b`), T2 (`7868373`), T3 (`8d49ab9`) commités. **T4 fait** (golden PASS
`22768f33…`, build vert, pan = image identique au pixel), **non commité** (l'orchestrateur
commit). Points F5 Nico ouverts : (T1) F4 + Maj+F4 à ×0,5 et ×4 sur `full` ; (T2) « le sol
a-t-il changé ? » (attendu : non) + F4 ×0,5 (~1450 draw calls) ; (T3) survol, étiquettes,
losange, surbrillance de taille, gènes G, étiquette conteneur réactifs comme avant ; voile
météo au repos ; **(T4) à ×8 en Continu/Turbo, pan rapide d'un bord à l'autre : aucune
plante ne « saute » ni n'apparaît en retard, pas d'à-coup hebdomadaire ; paillis / litière /
flaques / couverture présents jusqu'au bord après un long pan (avant : trou possible) ;
clic F2 sur une plante qui vient d'entrer à l'écran → dossier à jour ; tailler une branche
juste après un pan.** Prochaine étape : T5 `05_paliers_bas.md`.
