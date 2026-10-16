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
| T2 | `02_sol_un_lot.md` | sol = 1 maillage/tuile, image identique | intact | **fait** (non commité, F5 Nico à faire) |
| T3 | `03_plancher_fixe.md` | souris 1×/frame, survol paresseux, plein écran à la demande | intact | à faire |
| T4 | `04_marge_paresseuse.md` | marge proportionnelle + hystérésis, semaine paresseuse | intact | à faire |
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
T1 commité (`a5fa36b`). **T2 fait** (golden PASS `22768f33…`, build vert, 0 pixel
différent), **non commité** (l'orchestrateur commit). Points F5 Nico ouverts : (T1) F4 +
Maj+F4 à ×0,5 et ×4 sur `full` ; (T2) « le sol a-t-il changé ? » (attendu : non, y compris
rotation et relief qui monte) + F4 ×0,5 (draw calls attendus ~1450 sur `full`). Prochaine
étape : T3 `03_plancher_fixe.md` (plancher fixe ~36 ms à 36 draw calls = coût CPU).
