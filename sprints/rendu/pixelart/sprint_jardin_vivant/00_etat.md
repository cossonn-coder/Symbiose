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
| T1 | `02_palette_curseur.md` | shader palette 32 + Bayer · curseur + losange de survol | intact | à faire |
| T2 | `03_precuisson.md` | cuisson par plante + cache + file étalée (image identique) | intact | à faire |
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

## Ce qui reste
T1→T5. Mesures à graver ici au fil des tronçons : Mo de cache, ms de cuisson/plante, budget/frame retenu.

## §REPRISE
`/sprint-auto sprint_jardin_vivant` : lire CLAUDE.md + ce fichier + le doc de conception, puis le premier kickoff « à faire » (T1). T0 fait mais **non commité** (orchestrateur). Vérifier chaque rendu avec `tools/capture_vm.sh` puis Read des PNG.
