# Sprint JARDIN VIVANT (A) — état partagé

> Conception FIGÉE le 2026-10-15 (`/conception`) →
> [`docs/rendu/pixelart/conception_jardin_vivant.md`](../../../../docs/rendu/pixelart/conception_jardin_vivant.md)
> (LIRE AVANT TOUT TRONÇON). Pure vue + un export de pont : **golden jamais
> re-figé** (référence courante `22768f33…` — à vérifier en tête de T1).

## Décisions clés (Nico)
- Mignon SNES ; **animation = signal d'état** (calme + beau = quasi immobile).
- Sprites procéduraux **par instance** (segments réels, étiolement, symptômes,
  `automne` par plante, fleur par famille/espèce).
- 8 poses = **8 degrés de flexion**, choisis par une **onde de vent cohérente
  qui appuie** ; balancement propre décalé par plante (hash id).
- **Re-cuisson jamais simultanée** : file à budget par frame, **seulement écran visible + marge** (rien hors champ).
- Hors sprint : détails par palier de zoom + culling généralisé = **D106** ; D72 absorbée (à fermer en T5).
- Palette ~32 couleurs + tramage Bayer (shader sur le SubViewport).
- 2 sprints : A (ici) puis B = faune + champignons + fumée/eau (réutilise T2).

## Carte des tronçons
| # | Kickoff | Contenu | Golden | État |
|---|---|---|---|---|
| T0 | `01_banc_capture.md` | Godot portable + Xvfb + Movie Maker → PNG | intact | **fait** (non commité) |
| T1 | `02_palette_curseur.md` | shader palette 32 + Bayer · curseur + losange de survol | intact | **fait** (`447da15`) |
| T2 | `03_precuisson.md` | cuisson par plante + cache + file étalée (image identique) | intact | **fait** (non commité) |
| T3 | `04_vent_onde.md` | pont `weather.wind` + 8 poses de flexion + onde | intact | à faire |
| T4 | `05_canicule_pluie.md` | réponses par plante canicule + pluie/orage | intact | à faire |
| T5 | `06_neige_gel_banc.md` | neige + grêle/gel + traces + banc F5 « jardin vivant » | intact | à faire |

## Faits vérifiés au code (2026-10-15)
- `data/code/sim/wind.py` : `wind_at(seed, week) -> WindState(force ∈ [0,1+], direction ∈ [0,2π) = D'OÙ vient le vent)`, pur ; `gust_profile(seed, week)` (4 sous-ticks). `fields/abri.py` → `eco.vent` (force locale, **LAZY**, `None` au repos, D99).
- Snapshot : `weather` sans vent ; plante : `wind_memory`, `leaf_symptoms`, `floraison`, `automne` (`data/code/tools/simserver/serialize.py:191-246`). `ENGINE_VERSION = "0.5.43"` (`tools/simserver/version.py:669`).
- `tests/test_golden.py` hache log moteur + attributs d'instance, **pas le snapshot** → export de pont golden-neutre.
- `PlantRenderer` (Node2D, `_Draw` vectoriel + `QueueRedraw` sur changement) : `PlantRenderer.cs` 279 LDC, `.Organs.cs` **317 (🟡)**, `.Leaf.cs` 217, `.Flower.cs` 135. Instancié dans `world/WorldView.Snapshot.cs:216` et `WorldView.Conteneurs.cs:180`. Zoom réel : `WorldView.CurrentZoom` (static), pompe de redraw au palier dans `WorldView.Camera.StepZoom`.
- Projet `gl_compatibility` (`project.godot:48`) ; VM : réseau OK (github), **pas de Xvfb installé**, pas de sudo (`apt-get download` + `dpkg-deb -x`).
- Aucun curseur/survol de plot existant (seul `world/SolTexture.cs` cuit un losange de sol).
- Météo C# : `visuals/WeatherLayer.cs` (197 LDC, stries de vent tempête), `SnowLayer.cs`, `PuddleLayer.cs`.

## Banc de capture VM (T0, vérifié 2026-10-15)
- **Commande** : `tools/capture_vm.sh -o <dossier> -b <monde|banc> -z <palier> -c <x_cm>,<y_cm> -n <N>`
  (ex. `tools/capture_vm.sh -o /tmp/cap -b full -z 2 -c 300,1700 -n 3`) → `frame0000000k.png`
  1920×1080 (HUD compris) + `godot.log`. `--no-build` saute le `dotnet build`.
- **Durée** : ~11 s pour 3 images [smoke et full, warmup 12 sem. inclus, n=4 runs] ; rendu llvmpipe
  ~12 % du temps réel [n=1]. FPS **fixes** (Movie Maker, défaut 10) → temps de jeu = N/FPS, déterministe.
- **Mode capture C#** : `world/WorldView.Capture.cs` (args `--capture-banc/zoom/centre` après `--`) saute
  le sélecteur et cadre la caméra ; **inactif sans argument** (F5 Nico inchangé). 2 lignes d'accroche
  dans `WorldView.cs` (`_Ready`, après `FrameCamera`).
- **Hors dépôt** : Godot 4.6-stable mono dans `~/opt/godot/` ; Xvfb + deps (`xvfb`, `xserver-common`,
  `x11-xkb-utils`, `libunwind8`, `libxfont2` 2.0.6-1+deb13u1, `libfontenc1`, `libxkbfile1`) téléchargés
  depuis `deb.debian.org/debian/pool/` (l'index apt local est périmé : `apt-get download` → 404) et
  extraits `dpkg-deb -x` dans `~/opt/xvfb/root/`. **Patch** : Xvfb appelle `xkbcomp` via un chemin
  compilé `/usr/bin` → copie `Xvfb-patched` où cette chaîne (unique) devient `/tmp/xk` ; le script
  recrée le lien `/tmp/xk/xkbcomp` à chaque lancement.
- **Import** : `.godot/` présent ; un `Godot --headless --path . --import` (~50 s) a suffi, aucun
  fichier suivi modifié.
- **Limites** : la phase démarre en Planification (temps figé) → images identiques tant que rien
  n'anime ; pas de souris (étiquette de survol arbitraire possible) ; avertissement V-Sync bénin.

## T1 — palette SNES + curseur (fait 2026-10-15, golden `22768f33…` PASS, build vert)
- **Palette maître** `Palette16.Maitre` = **34 couleurs** (8 verts, 5 terres, 4 argiles, 3 sables,
  6 pierres, 1 blanc, 3 eaux, 4 accents fleurs) ; calée par k-means sur les captures T0 puis
  simulation Python du shader. 4 entrées nommées (`MaitreSombre/Granite/Blanc/Jaune`).
- **Shader** `visuals/palette_snes.gdshader` sur le `SubViewportContainer` (`PaletteSnes.cs`) :
  plus proche en **OKLab** + Bayer 4×4 sur la grille interne 960×540, `tramage` 0.5 ; **accents
  (fleurs) jamais partenaires de tramage** (sinon argile mouchetée de rouge, constaté). **F11** =
  avant/après. HUD/étiquettes non quantifiés.
- **Curseur** main gantée 16×16 ×2 cuite (`WorldView.Curseur.cs`), tap 150 ms au clic gauche.
  **Losange de survol** `visuals/PlotHover.cs` (blanc + ombre 1 px, suit relief et rotation),
  respire (période 1,4 s) **seulement** geste armé.
- **Banc** : `capture_vm.sh` gagne `-s X,Y` (souris, WarpMouse sous Xvfb OK) et `-g N` (geste armé).
- **Avant/après** (full vue d'ensemble + zoom 4 sur le sable 300,1700) : nuances conservées ; erreur
  moyenne OKLab ~0,02 [simulation Python, 2 images] ; 28 couleurs distinctes à l'écran [vue
  d'ensemble, n=1]. Flancs de sable = aplat gris-beige (avant : trame grise) ; dessus de sable et
  terres = grain tramé fin ; ardoise/granite gardent leurs 2-3 valeurs. Moucheture rouge résiduelle
  sur l'argile : ~118 px [simulation, vue d'ensemble], uniquement là où la source est déjà rouge.
- **Coût shader** : non mesurable sur la VM (Movie Maker 9-14 s/image dominé par sim + encodage
  [n=2 avant, n=2 après]) ; 1 passe 518 400 px × 2 boucles ≤ 34 → à confirmer F4 par Nico.
- **Points F5** : plus SNES / plus beau ? `tramage` (0,5) ; grain vert sur le sable ; losange
  lisible sur sable clair ? curseur main (taille ×2) ; respiration trop/pas assez visible.

## T2 — pré-cuisson par instance (fait 2026-10-15, golden `22768f33…` PASS, build vert)
- **Technique** : un `SubViewport` PAR PLANTE (enfant du `PlantRenderer`), contenant un **pinceau**
  = un `PlantRenderer` `IsBrush` qui reçoit une copie de l'état dessiné et rejoue `DrawVector()`
  (l'ex-`_Draw`, inchangé). Rendu `UpdateMode.Once` → sa texture EST l'image ; aucune lecture GPU→CPU.
  Atlas prévu : `PlantBaker.PoseCount` (=1 ; T3 → 8) cellules côte à côte, `DrawImage(pose)`.
- **Fichiers** : `visuals/PlantRenderer.Bake.cs` (partial : `Invalidate`, `_Draw` dispatch, copie
  d'état, boîte englobante), `visuals/PlantBaker.cs` (cuiseur), `visuals/BakeQueue.cs` (file) ;
  `PlantRenderer.cs` : setters `QueueRedraw`→`Invalidate`, `_Draw`→`DrawVector`, pinceau sans ombre ;
  `.Organs.cs` (`SetSupport`) ; `WorldView.Snapshot.RedrawAllPlants` invalide ; `WorldView.cs` ajoute la file.
- **Règles** : setter → plante « sale » ; avec image elle la GARDE jusqu'à re-cuisson, sans image
  elle se dessine en direct (naissance, hors champ libérée, trop grande). Cuisson visible
  uniquement (`IsVisibleInTree` = marge de `CullPlants`), écran d'abord ; affichage à frame+1
  (jamais une texture non peinte) ; nouvelle géométrie = nouveau SubViewport, l'ancien libéré au
  commit. Hors marge → image libérée (balayage /15 frames). Côté > `MaxSidePx` 2048 → direct
  (grand arbre à ≥×8). Surbrillance de taille dessinée EN DIRECT par-dessus l'image.
- **Alpha** : l'image sur fond transparent sort **prémultipliée** (feuilles a=0,92) → matériau
  partagé `BakeQueue.Unpremultiply` (shader 3 lignes) remet l'alpha droit ; neutre sur le direct.
- **Écarts imprévus (kickoff)** : `LeafLitterLayer` HÉRITE de `PlantRenderer` (stylo) → exclu de la
  cuisson (`Bakeable`). Reporter la phase sous-pixel du collet dans le pinceau a été essayé
  (3 variantes) et fait PIRE → abandonné. Les captures VM ne sont PAS déterministes d'un run à
  l'autre (couches animées) → comparaison sur pixels statiques (identiques sur 3 frames des 2 runs).
- **Mesures** (VM llvmpipe, Movie Maker) :
  - Identité avant/après, pixels statiques différents : 0 [×0,5 full, ×4 effondrement, ×16 lux] ;
    24-1753 px [×1-×8, n=1 chacun] = trame Bayer qui bascule d'1 px (arrondi 8 bits de
    l'alpha prémultiplié) ; 4022 px = 0,19 % [×2 foret_ports, le figuier 67 segments] = arêtes
    de branches décalées d'1 px interne. À l'œil : identique.
  - Cache : 0,2 Mo / 143 images [×0,5 effondrement] ; 0,7 Mo [×1, idem] ; 2,3 Mo / 35 [×4, idem] ;
    4,6 Mo / 14 [×2 forêt] ; 11,4-11,5 Mo / 7-12 [×4 forêt avec arbres, ×8-×16 lux].
  - Pinceau (CPU, enregistrement du dessin) : 0,07-0,18 ms/plante moy. [herbacées ≤ 3 segments,
    4 runs] ; 3,9-4,9 ms [arbre 67 segments, 3 runs] ≈ 0,06 ms/segment.
  - **Budget retenu** : 6 plantes ET 80 segments par frame (≥ 1 plante). Vidage : 143 plantes en
    24 frames ≈ 0,4 s à 60 FPS [effondrement, n=1] ; 111 en 19 frames [full, n=1].
  - FPS : non mesurable sur la VM (Movie Maker ~450 ms/frame dominé par sim + encodage PNG :
    446 avant / 456 après [×1], 434 / 425 [×4], n=1) → **F4 Nico**.
- **Points F5** : « rien n'a changé et ça reste fluide ? » ; F4 au passage de semaine (pas de pic)
  et en zoomant ; pan rapide à ×4-×8 (plantes jamais invisibles, éventuel flou d'1-2 frames au
  changement de palier = ancienne image étirée, voulu) ; taille au survol (surbrillance réactive).

## Ce qui reste
T3→T5. T3 : porter `PlantBaker.PoseCount` à 8 (poses = cellules de l'atlas, `brush.Position`
décalée par cellule ; ajouter la pose à l'état du pinceau) ; mémoire ×8 → revoir `MaxSidePx`.

## §REPRISE
`/sprint-auto sprint_jardin_vivant` : lire CLAUDE.md + ce fichier + le doc de conception, puis le premier kickoff « à faire » (**T3** `04_vent_onde.md`). T2 fait mais **non commité** (orchestrateur). Bascule F11 = palette ON/OFF pour comparer. Vérifier chaque rendu avec `tools/capture_vm.sh` puis Read des PNG ; comparer avant/après sur les pixels STATIQUES (couches animées non déterministes).
