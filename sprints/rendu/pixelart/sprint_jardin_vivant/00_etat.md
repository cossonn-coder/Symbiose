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
| T0 | `01_banc_capture.md` | Godot portable + Xvfb + Movie Maker → PNG | intact | **fait** (`e88da4b`) |
| T1 | `02_palette_curseur.md` | shader palette 32 + Bayer · curseur + losange de survol | intact | **fait** (`447da15`) |
| T2 | `03_precuisson.md` | cuisson par plante + cache + file étalée (image identique) | intact | **fait** (`0bb6cb6`) |
| T3 | `04_vent_onde.md` | pont `weather.wind` + 8 poses de flexion + onde | intact | **fait** (`14c0fc4`) |
| T4 | `05_canicule_pluie.md` | réponses par plante canicule + pluie/orage | intact | **fait** (`c0e9a34`) |
| T5 | `06_neige_gel_banc.md` | neige + grêle/gel + traces + banc F5 « jardin vivant » | intact | **fait** (non commité) |

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

## T3 — vent en onde (fait 2026-10-15, golden `22768f33…` PASS, build vert, test_sim_server 283/283)
- **Pont 0.5.44** (`tools/simserver/vent_pont.py`, branché dans `serialize.py`) : `weather.wind =
  {force, direction, gusts}` (`wind_at`/`gust_profile` de la semaine `last`, calme à l'init) + clé
  OPTIONNELLE `abri` par plante vivante = facteur géométrique lu dans `eco._abri_cache[1]` (omise
  tant que le cache est froid). Test section 22 `tests/simserver/vent.py` ; asserts de version
  0.5.43→0.5.44 dans `simserver/{voix,structures,conteneurs}.py` (convention).
- **Écart kickoff (prémisse réfutée)** : `eco.vent` n'est PAS `None` au repos — il est alloué à 0
  (`container.py:445`) et recalculé à CHAQUE tick par `tick_abri` (`boucle.py:235`). Le seul état
  paresseux est `eco._abri_cache` (None avant le 1er tick) → c'est lui qui conditionne la clé `abri`.
  Pré-existant hors périmètre : `tests/test_peripherie_pont.py:97` attend encore 0.5.41.
- **Vue** : `visuals/WindWave.cs` (Node, état global + onde par frame sur `BakeQueue.All` visibles,
  zéro allocation) ; `visuals/PlantRenderer.Wind.cs` (flexion dans `Iso` : apex tiré vers l'aval
  ∝ z²/H et abaissé, raideur = 1/(1+épaisseur max/3 cm) ∈ [0,12;1], retard 0,002 s/cm, phase propre
  = hash de la position) ; `PlantBaker` : atlas de **1 pose au calme (force < 0,05), jusqu'à 8 au vent**
  (pose max = ceil(7×raideur×1,5) → un arbre n'en cuit que 3) ; boîte = union droite/plus couchée ;
  `MaxAtlasPx` 4096. Re-cuisson de tout (via la file) seulement à la bascule calme↔vent ou dérive
  de direction > 15°. `WeatherLayer` : inclinaison/dérive pluie-grêle-neige et stries de tempête
  suivent la direction ÉCRAN réelle × force (ex-`_slantPx` fixe par type).
- **Banc** : `capture_vm.sh -v FORCE[,DIR_RAD]` (`--capture-vent`, inactif sans argument).
- **Mesures** (VM llvmpipe, Movie Maker 10 FPS) :
  - Onde : 0,129 ms/frame moy. (max 1,4) [69 plantes, ×2, n=1] ; 0,169 ms (max 2,0) [109 plantes, ×1, n=1].
  - Cache : 116,1 Mo / 51 images au vent vs 12,8 Mo au calme [×8 full 700,1620, n=1 chacun] (×9 =
    8 poses + boîte élargie) ; 10,2 Mo / 69 [×2, vent 0,7] ; 4,3 Mo / 109 [×1, vent 0,7].
  - Calme (`-v 0`, ×8) : pixels de la plante identiques frame à frame après la cuisson (0 px sur
    10 paires) ; d'autres zones bougent aussi au calme (vie macro), hors plantes.
  - Vent 1,2 (×8) : la plantule (`-c 700,1620`) change de pose 3 fois en 4 s (4068 px par bascule) :
    tige penchée vers la gauche-bas écran (vent du N-NO → aval vers le sud), elle se couche
    davantage au passage du front puis revient. À ×1 (vent 0,7) : 100-500 px changent par frame,
    dispersés sur le massif (front + balancement propre mêlés) — **front peu lisible à ×1** sur des
    semis de 5 cm ; à juger au F5 sur un jardin adulte.
- **Points F5** : « le vent se voit-il, comme une main qui appuie ? » ; le balancement propre
  (SwayAmp 0,08) fait-il frétiller (trop) ? ; mémoire vidéo à ×8 (~2,3 Mo/plante) → si trop, baisser
  le nombre de poses ou ne cuire les 8 qu'en dessous de ×8 ; pluie qui s'incline dans le bon sens.

## T4 — canicule + pluie/orage (fait 2026-10-15, golden `22768f33…` PASS, build vert, pont NON touché)
- **Variante de dessin par plante** (`visuals/PlantRenderer.Meteo.cs`) : `_heat` = `secheresse` si
  `weather.kind == "Canicule"` (sinon 0) → feuilles abaissées de +6 cm × i et limbe refermé
  (largeur × (1 − 0,55 i)) ; `_wet` ∈ {0, ⅓, ⅔, 1} → extrémités qui retombent (4 cm × wet × raideur
  du port × z/H : l'herbacée ploie, l'arbre à peine) + reflets 1-2 px `MaitreBlanc` sur ~45 % × wet
  des feuilles (hash). Cuite dans l'atlas (× poses T3), copiée au pinceau ; `RefreshMeteo` ne salit
  QUE les plantes dont la variante change (sans `secheresse` → pas de recuisson à la canicule ; sans
  feuillage → pas de recuisson à la pluie). Hooks dans `.Organs.cs` : `LeafDropCm(p.Z)` remplace
  l'abaissement sécheresse (identique hors épisode), `LeafOpen`, `DrawWetGlint`.
- **État global** `visuals/MeteoPlantes.cs` (Node) : lit `weather.kind` ; pluie = « Pluie prolongée » ou
  « Orage » ; après l'épisode le feuillage se ressuie en 8 s de jeu par 3 paliers (= 3 vagues de
  recuisson via la file). `_Process` sort immédiatement sans épisode (animation = signal).
- **`WeatherLayer`** : éclaboussures au sol (carrés 2 px eau claire de `Palette16.Maitre`, point puis
  couronne, cycle 0,45 s, sites re-tirés au hash) ; éclair = flash 1 frame ~0,14 s à intervalles
  3-9 s (hash du rang), ex-2,4 s régulier. **Bug pré-existant corrigé** : le hash des précipitations
  (djb2 3 octets) avait des bits hauts quasi constants → toutes les gouttes à la même phase verticale
  = pluie en NAPPE horizontale (vu au banc) ; remplacé par le finaliseur murmur3 (pluie/neige/grêle
  désormais dispersées — touche aussi la neige T5).
- **Banc** : `capture_vm.sh -m KIND[,INT[,DUREE_S]]` (`--capture-meteo`, météo imposée puis retour au
  snapshot après DUREE_S → observe l'« après ») et `-w N` (`--capture-semaines`, warmup).
  Canicule : `-b secheresse_sable -w 3 -z 4 -c 125,222 -m Canicule`. Pluie : `-b full -z 8 -c 300,1700 -m "Pluie prolongée,0.8"`.
- **Mesures** (VM llvmpipe, Movie Maker) :
  - Canicule [secheresse_sable sem. 4, n=1] : 2 plantes examinées, seul le basilic (`secheresse`
    0,52) change (1128 px différents à ×4, 4244 à ×8) ; la bourse-à-pasteur voisine (sans symptôme)
    n'est pas recuite (0 px).
  - Pluie/orage [full ×4 300,1700, n=1] : 4 vagues (1 → ⅔ → ⅓ → 0) de 31 plantes cuites en 6 frames
    chacune (80 sales hors champ attendent) ; à 60 FPS ≈ 0,1 s par vague.
  - Mémoire : **0 Mo de plus** — la variante REMPLACE l'image (même atlas), pas d'image supplémentaire
    (17,4 Mo / 31 images avant et après chaque vague [full ×4, vent actif, n=1]).
  - Éclair : 1 frame éclaircie (+18 de luminance moyenne) en 4 s [smoke, 10 FPS, n=1].
- **Constat pour Nico** : sur `full` seed 42, AUCUNE plante ne porte `secheresse` en 34 semaines [scan
  Python, n=1 seed] (ni sur les autres bancs testés, sauf `secheresse_sable`) → en jeu la canicule ne
  se lira sur les plantes que dans un jardin réellement assoiffé (voulu : pas d'effet sans état).
  Le symptôme lui-même est rare — à juger si c'est un manque de calibrage moteur (dette éventuelle).
- **Points F5** : « on sent la chaleur / la pluie sur les plantes ? » ; reflets assez visibles
  (taille `r·0,1·zoom` px) ? ; séchage 8 s trop rapide/lent ? ; éclaboussures/éclair.

## T5 — neige, givre, grêle + banc F5 (fait 2026-10-15, golden `22768f33…` PASS, build vert, test_sim_server 283/283, pont NON touché)
- **Variantes froides cuites** (`visuals/PlantRenderer.Froid.cs`, partial NEUF 90 LDC) : **neige** = calotte
  blanche (`MaitreBlanc` sur ombre bleutée `a8cfe6`) sur le dessus des feuilles (part ∝ charge, plus en haut
  de la plante), trait blanc sur les branches peu inclinées (`DrawSnowOnBranch`, utile aux caducs nus de
  l'hiver), calotte sur la couronne au LOD ×0,5 ; la charge **raidit** (flexion × (1 − 0,6 neige), dans
  `PlantRenderer.Wind.UpdateWind`). **Givre** (« Gelée tardive ») = limbe tiré vers `a8c4d0` (45 % × givre) +
  liseré blanc 1 px pixel-art sur 40-100 % des feuilles. **Grêle** = 1-3 encoches triangulaires au bord du
  limbe ∝ `grele` (en plus du criblage existant). Hooks : `Organs` (couleur `Frosted`, `DrawColdLeaf`),
  `PlantRenderer.cs` (`DrawSnowOnBranch` dans la boucle des segments, `DrawSnowCrown` au LOD), `Bake`
  (copie `_snow/_frost` au pinceau), `Meteo.RefreshMeteo` (appelle `RefreshCold`).
- **État global** `MeteoPlantes` étendu : `SetWeather(kind, intensity)` ; charge = clamp(σ, 0,5, 2)/2 (même
  bornage que l'effet moteur) ; givre se dissipe en 5 s, neige fond en 6 s après l'épisode ; sous vent ≥ 0,5
  elle **tombe** en 5 s jusqu'à 30 % de la charge (il neige encore). La neige est quantifiée **par plante**
  avec un décalage de hash (±0,15) → les plantes perdent leurs plaques à des instants différents (jamais tout
  le jardin à la même frame) ; plantes ré-examinées toutes les 0,2 s pendant la fonte/chute seulement.
- **Traces** : rien d'inventé — encoches/criblage (`grele`) et bords noircis (`gel`) suivent `leaf_symptoms`
  (qui inclut `plant.symptom_marks`) ; elles restent tant que le snapshot les porte.
- **Abri** : `WorldView.Ciel.MarkCoveredPlants` marque les plantes dont le plot-foyer porte `couvert_pose`
  (voile/cloche) → ni neige ni givre ; grêle/gel déjà épargnés par le moteur. ⚠️ **Écart kickoff** : il citait
  `CouvertureLayer.cs` — c'est le tapis de couvre-sol (luxuriance) ; les voiles D104 sont `CoverLayer.cs`.
- **Banc F5 « jardin vivant » = touche F12** (`world/WorldView.Defile.cs`) : défilé sur le jardin courant,
  **7 situations × 10 s de jeu** en boucle (calme → vent 0,9 → canicule → pluie → neige, le vent forcit à
  mi-étape → grêle → gelée), encart ciel = « jardin vivant · Neige (5/7) » ; **re-F12 = arrêt** (météo, vent
  et ciel du snapshot). Impose seulement le `weather` reçu par la vue + l'onde (moteur intouché). Pour voir
  des **traces réelles** de grêle et la moitié voilée : banc `effondrement` **avec seed 12345** (cf. blocage).
- **Banc VM** : `capture_vm.sh -d` (défilé) et `-S N` (seed ; `--capture-seed`).
- **Mesures** (VM llvmpipe, Movie Maker) — PNG dans le scratchpad de session (non versionnés) :
  - 7 situations [défilé full ×4 300,1700, 2 FPS, 142 images, n=1] : calme/vent identiques à T3 ; canicule
    sans effet visible (aucune plante en `secheresse` sur full, cf. T4) ; pluie = voile gris + reflets ; neige =
    calottes blanches sur les 4 plantes du cadre puis plaques tombées après le coup de vent ; grêle = billes ;
    gelée = feuilles pâles bleutées cerclées de blanc ; l'encart nomme chaque situation.
  - Neige + vent 1,0 [full ×4, 60 images, n=1] : pixels blancs 5 680 → ~4 700 en 6 s (plaques tombées,
    flocons inclus dans le compte) ; vague de re-cuisson unique au début (111 plantes examinées).
  - Abri [effondrement ×4, seed 42, n=1] : moitié voilée **0 calotte**, moitié nue toutes enneigées.
  - Trace grêle [effondrement seed 12345, sem. 1312, ×16, n=1] : 18 plantes survivantes portent `grele` 0,117
    (toutes sous voile : grêle amortie) → 1 trou + 1 encoche par feuille, discret mais lisible à ×16.
  - Mémoire : 0 Mo de plus (variante = même atlas, remplace l'image, comme T4).
- **Blocage pré-existant (hors périmètre, NON corrigé)** : Godot envoie TOUJOURS `seed` (42, `WorldView.Seed`)
  à `init` → `BANC_SEED={"effondrement":12345}` n'est **jamais appliqué au F5** : le banc D104 tourne en seed
  42, sans la grêle du collapse (176 basilics vivants, ciel dégagé). Correctif possible : ne pas envoyer de
  seed pour un banc (`SimBridge.Init`), ou laisser le banc imposer le sien côté serveur — décision Nico.

## Ce qui reste
Sprint A **terminé**. F5 Nico : une seule question, « le jardin est-il beau et vivant ? » — F12 sur `full`
(défilé), puis sur `effondrement` (voile vs nu). Calibrages F5 : onde (`WindWave` λ/f/enveloppe,
`PlantRenderer.Wind` BendReach/raideur), séchage 8 s / fonte 6 s / givre 5 s, taille des calottes. Ensuite
sprint B (faune + champignons + fumée/eau) à concevoir.

## §REPRISE
Sprint clos (T0→T5 faits ; T5 **non commité** — orchestrateur). Prochaine étape : commit T5, puis F5 Nico.
Banc VM : `tools/capture_vm.sh -b full -z 4 -c 300,1700 -d -f 2 -n 142` (défilé complet, ~3 min) ;
neige `-m "Neige,1.5"`, gelée `-m "Gelée tardive,1.5"`, grêle `-m "Grêle,1.9"` ; traces réelles
`-b effondrement -S 12345 -w 3 -z 16 -c 225,175`.
