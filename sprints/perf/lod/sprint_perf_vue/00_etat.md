# Sprint PERF VUE — état partagé

> Conception FIGÉE le 2026-10-19 (`/conception`, après le F5 raté de D106) →
> [`docs/perf/lod/conception_perf_vue.md`](../../../../docs/perf/lod/conception_perf_vue.md)
> (LIRE AVANT TOUT TRONÇON : mesures F5, diagnostic vérifié, décisions 1-8, table des tailles).
> **Golden jamais re-figé** : référence `22768f33…` (`cd data/code && python3 -m tests.test_golden`).
> Seul code Python touché : le peintre de vie macro (②, perception pure) + version du pont.
> Suite prévue : sprint « plante assemblée » (Nico, 2026-10-19).

## Décisions clés (Nico, 2026-10-19)
- **Critère nominal** (PC Nico : i5-4200H 2 cœurs, iGPU HD 4600, `gl_compatibility`) : à 60 s par
  semaine, **60 FPS à ×4** avec vent et animations à vitesse normale ; 30 FPS de ×0,5 à ×2.
- **Mode test accéléré** : au plus vite selon la machine, aucune image > 100 ms.
- **Étalonnage** : un run du banc sur le PC de Nico en fin de ① ; ensuite validation par mesure,
  F5 final = ressenti seul.
- **Vie macro** : 1 individu par espèce et par tuile + points chauds + grappes coloniales ;
  taille réelle, visible au palier où ≥ 1 px ; lombric jamais ; pixels fixes, animés sur signal ;
  un lot par tuile ; champ de population intact.
- **D109 (d)** au minimum ; **pleine résolution** mesurée seulement.

## Carte des tronçons
| # | Kickoff | Contenu | Golden | État |
|---|---|---|---|---|
| ① | `01_banc_etalonnage.md` | banc du jardin réel + instrument + étalonnage PC | intact | **fait** (attend le rapport PC de Nico) |
| ② | `02_vie_macro.md` | peintre D2 + points chauds + taille réelle, lot par tuile, fuite | intact (pont 0.5.45) | **fait** |
| ③ | `03_ombres_lot.md` | ombres en lot (un maillage) | intact | **fait** |
| ④ | `04_cadence_acoups.md` | cadence adaptative, priorité serveur, à-coups, D109 | intact | **fait** |
| ⑤ | `05_vue_bilan.md` | pleine résolution mesurée, bilan converti PC, F5 ressenti | intact | **fait** (bilan PC converti le 2026-10-19 : ×4 = 32,5 FPS, D1 raté) |

## Mesures
### Banc ① (2026-10-19) — touche **E** (F5) ≡ `tools/perf_vm.sh -E 20` (VM)
Scénario : monde full, seed 42, warmup 12, turbo jusqu'à la **semaine moteur 45** (hiver an 1),
puis ×4 sur (1650, 950) cm (tuile E, cellule la plus dense), 60 s/semaine, repos 8 s, mesure 20 s,
rapport au presse-papier. Constantes dans `world/WorldView.Etalonnage.cs`.
**Écart au kickoff** : le printemps an 2 (300-400 plantes) n'a pas de vie macro (0-4 bêtes servies,
semaines 48-61 [seed 42, scan Python]). s45 = 272 plantes + 3848 bêtes servies. Cas de stress : `-W 67`
(été an 2 : 562 plantes, 5000 bêtes).
Instrument : distribution (médiane/p95/p99/max, images > 33 / > 100 ms, horloge murale), postes CPU
(`visuals/PerfPostes.cs`), rendu CPU/GPU (`ViewportSetMeasureRenderTime`), bascules, machine/GPU.
Options VM : `-z`/`-c` (cadrage), `-x MacroLife`, `-O` (ombres OFF), `-W` (semaine).

**Fuite MacroLife reproduite** : au cadrage, 12 973 entrées client dont 7 988 mourantes [n=10 runs,
identique] ; masquée, elle reste à 13 305 dont 9 475 mourantes.

Référence VM (llvmpipe, FPS non comparables au PC ; draw calls, primitives et ms CPU par poste, si) :
| cas | n | moy. ms | p95 ms | > 100 ms /20 s | draw | prim | rendu CPU ms | macro _Draw ms |
|---|---|---|---|---|---|---|---|---|
| ×4 tout | 2 | 103,8 / 101,6 | 112 / 110 | 137 / 113 | 2730 | 110 k | 77-78 | 8,7 |
| ×4 macro masquée | 2 | 83,7 / 80,3 | 94 / 88 | 5 / 0 | 2070 | 69 k | 67-70 | 0 |
| ×4 ombres OFF | 2 | 102,5 / 100,2 | 112 / 112 | 122 / 79 | 2690 | 110 k | 75-77 | 8,7 |
| ×4 macro masquée + ombres OFF | 2 | 76,6 / 76,3 | 87 / 83 | 2 / 1 | 2027 | 68 k | 64 | 0 |
| ×0,5 tout | 2 | 85,6 / 88,9 | 93 / 102 | 0 / 17 | 1979 | 55 k | 72-75 | 0 (LOD) |
| ×1, ×2, ×8 tout | — | **manquant** (runs interrompus sur demande de l'orchestrateur) | | | | | | |

Lecture VM : la somme des postes CPU fait 0,2 à 9,5 ms par image ; le reste est du rendu (CPU de
rendu 64-78 ms). La vie macro coûte 8,7 ms de `_Draw` et environ 40 k primitives, 700 draw calls.
Les ombres coûtent peu sur la VM (0,1-0,3 ms, 48-128 redessins/s) : les ~300 ms vues sur le PC
viendraient du pilote/GPU → le rapport du PC tranchera.

### Tronçon ② (2026-10-19) — vie macro, VM llvmpipe
Peintre `peindre_presence` (`fields/population/perception.py`) : 1 représentant au plot le plus
dense (≥ 0,06) + ≤ 3 points chauds (≥ 0,18, écart ≥ 3 plots) par espèce et par tuile ; grappe
1 + quanta (≤ 6) pour puceron/moustique/cloporte ; **lombric ET pollinisateurs** jamais peints.
Bêtes servies, monde full seed 42 [scan Python] : s20 **300** · s45 **25** (avant 3 848) · s67 **77**
(avant ~5 000). Vue : un seul CanvasItem, `DrawRect` à taille réelle (px1 = 1/zoom), redessin
au snapshot / palier / marge / rotation / signal seulement ; sursaut 1,2 s sur geste (`Signal`).
| cas (banc E, ×4, 20 s) | n | moy. ms | p95 | > 100 ms | draw | prim | macro _Draw |
|---|---|---|---|---|---|---|---|
| s45 tout, après | 2 | 77,1 [p95 et moy. d'1 run] | 84,7 | 1 / 1 | 2063 / 2061 | 68 k | 0 appel/s |
| s67 tout, après | 1 | 113,1 | 128 | 177 | 2714 | 101 k | 0 appel/s |
| s67 macro masquée, après | 1 | 127,5 | 154 | 157 | 2712 | 101 k | 0 |
→ s45 « tout » rejoint « macro masquée » d'avant (2070 draw, 69 k prim) : la vie macro ne coûte
plus que ~0 entre deux snapshots. s67 : pas de mesure « avant » à cette semaine.
**Fuite corrigée** : masquée (s67, après turbo) 58 entrées au cadrage, 77 à la fin, **0 mourante**
(avant : 13 305 dont 9 475). Purge dans `_Process`, indépendante du dessin.
Paliers retenus (géométrie, ≥ 1 px interne) : puceron ×16 · moustique ×8 · coccinelle, doryphore ×4 ·
chrysope, cloporte, carabe ×2 · limace, merle, hérisson, campagnol, rapace, couleuvre, libellule ×0,5.
Capture ×4 (s20) : limaces = tirets bruns, merle = barre sombre ; ×16 : aucune bête dans le cadre
(1 à 4 points par espèce et par tuile → rare dans un cadre de 1,5 m) — à juger au F5 ⑤.
Écarts / reliquats : pollinisateurs exclus du bloc (la vue les sautait déjà) ; `FocusGuild` sans
effet (bêtes déjà fixes) ; texte HUD « LOD : zoomez ×4 » (`WorldView.Hud.cs:340`) périmé ;
`ForagerLayer` non touché (0 butineur à s45, 8 à s67).

### Tronçon ③ (2026-10-19) — ombres en lot, VM llvmpipe
`visuals/PlantShadow.cs` n'est plus un nœud par plante : c'est UN nœud « Ombres », enfant de
`Objects` en ZIndex relatif −1 (sous toutes les plantes, au-dessus de la maison, du sol et de la
vie macro, hors du tri en Y). Toutes les capsules forment **un ArrayMesh** (éventails), `DrawMesh`.
Modèle inchangé (`fields/light.py` §3), même alpha `SunStrength`. Drapeau `PlantShadow.Sale`,
consommé une fois par image : pas de soleil ≥ 2°, touche O, `PlantRenderer.Invalidate` (emprise,
tapis), entrée ou sortie de marge (`CullPlants`), retrait au snapshot. Seules les plantes dans la
marge (`Visible`) et hors tapis ont une ombre. L'ombre de la maison n'est pas touchée.
**Écart au kickoff** : un lot unique, pas un lot par tuile (la conception autorise « ou un lot ») ;
un pas de soleil redessine tout de toute façon.
**Piège mesuré** : la même géométrie passée par `CanvasItemAddTriangleArray` coûtait
**+55 ms** de rendu par image (131,7 ms contre 74,1 OFF [n=1]) → maillage retenu.
| cas (banc E, ×4, 20 s) | n | moy. ms | p95 | > 100 ms | draw | prim | ombres _Draw |
|---|---|---|---|---|---|---|---|
| s45 ON, avant | 1 | 76,8 | 83,4 | 0 | 2059 | 68,1 k | 51 appels/s |
| s45 OFF, avant | 1 | 73,7 | 79,9 | 0 | 2022 | 67,5 k | 0 |
| s45 ON, après (maillage) | 2 | 75,1 / 72,5 | 82,1 / 79,9 | 1 / 0 | 2023 / 2024 | 68,4 k | 1 appel/s, ~0,4 ms par recalcul |
| s45 OFF, après | 1 | 74,1 | 80,9 | 0 | 2024 | 67,6 k | 0 |
| s67 ON, après | 1 | 103,6 | 114,6 | 144 | 2603 | 102 k | 2 appels/s, ~2,3 ms par recalcul |
| s67 OFF, après | 1 | 101,1 | 109,3 | 86 | 2601 | 100 k | 0 |
→ ON − OFF tombe au bruit : 37 draw calls → 0, ~2-3 ms → ≤ 1 ms. Recalcul ≤ 2,3 ms [s67, VM], donc pas
d'image > 33 ms due aux ombres (sur la VM, toutes les images dépassent 33 ms de toute façon).
**Même image** (captures `full` ×4 et ×2, planification = midi) : les intérieurs sont identiques à
±1 niveau (arrondi du mélange). Le bord de chaque capsule est décalé d'**1 px écran** (rastérisation
par le chemin y-sort de l'ancien nœud enfant ; vérifié : `DrawSetTransform` donne le même résultat
que le lot, pas l'ancien). Changement d'ordre assumé : une ombre ne recouvre plus une plante voisine
ni la maison (« sous les plantes », kickoff). Les ombres n'ont plus de fondu : elles apparaissent
avec la plante et disparaissent au début de son fondu de sortie.

### Tronçon ④ (2026-10-19) — à-coups, cadence, D109, VM llvmpipe
**Instrument** (`world/WorldView.PerfAcoups.cs`, banc E) : 5 pires images avec leurs postes, rendu CPU
et pause GC ; coïncidences des images > 33 ms (étalement / step en vol / GC) ; pire passage et octets
par famille d'étalement ; collectes GC par génération + dernier GC (finaliseurs en attente) ; cuissons
et poses. Octets alloués par poste (`PerfPostes`). **Cadence pendant la mesure** : `perf_vm.sh -A s`
(0 = turbo, 1 = défaut de Nico, absent = 60 s) ; `-V f` impose le vent.
**À-coups expliqués** (suspects du kickoff départagés) : pas le parsing (déjà hors fil principal,
`SimBridge.Request` dans la Task) ; ce sont, par ordre de poids :
1. **GC .NET** : 9-11 collectes gen1 par 20 s, **35-45 ms chacune**, 26 000-64 000 objets à
   FINALISEUR en attente par collecte. Source mesurée (dotnet-trace, AllocationTick) : l'API Godot C#
   — `Variant` (Disposer finalisable), `StringName` (chaque `GetMeta("wx")`), wrappers `Array`/
   `Dictionary` + leurs `WeakReference`. 1er émetteur : `FindPlant` (survol, CHAQUE image pendant
   l'étalement, 2 StringName × 272 plantes). Corrigé : `core/LectureSnap.cs` (clés Variant et noms de
   méta en cache, valeurs/wrappers disposés) sur les chemins chauds (plantes, segments, symptômes,
   litières, couvertures, picking) + `SolMaillage` réutilisé. → 5-6 collectes, **10-20 ms**, 242 à
   6 600 finaliseurs.
2. **Cuisson** : 8,0 poses par plante cuites au vent alors que l'onde n'en atteint que 2-4 (D109 c) ;
   jusqu'à 30-47 ms de préparation dans une image. Corrigé : poses atteignables seules (2,9/cuisson)
   + budget de temps 4 ms par image dans `BakeQueue` (≥ 1 plante).
3. **Python sur 2 cœurs** : serveur lancé en priorité réduite (`SimBridge`, `BelowNormal` → nice 10
   vérifié sur la VM ; Windows = BELOW_NORMAL, non vérifiable ici). La VM (16 cœurs) ne montre pas
   l'effet.
Hypothèse sur le « 3 FPS à 57 ms » des rapports C : ils sont pris à `DebugSecondsPerWeek = 1` (défaut,
inchangé) → une semaine appliquée toutes les ~2,5-3 s en continu ; le compteur FPS et la ligne
« frame » ne couvrent pas la même seconde. Cohérent avec le banc [VM] ; non vérifié sur le PC.
| cas (banc E s45, ×4, 20 s) | n | moy. ms | p95 | p99 | max | GC total | s/semaine |
|---|---|---|---|---|---|---|---|
| nominal, avant | 1 | 77,3 | 85,7 | 100,2 | 107,2 | 0 | — |
| nominal, après | 1 | 72,1 | 78,9 | 84,1 | 87,7 | 0 | — |
| nominal + 1 semaine (`-E 75 -A 60`), après | 1 | 74,9 | 84,6 | 92,6 | 108,0 | 17,6 ms | — |
| 1 s/semaine, avant | 1 | 123,0 | 165,2 | 197,2 | 203,4 | 338 ms | 2,86 |
| 1 s/semaine, après | 1 | 95,6 | 113,6 | 127,7 | 131,1 | 74 ms | 2,50 |
| turbo, avant | 1 | 144,3 | 287,1 | 380,2 | 388,4 | 285 ms | 3,33 |
| turbo, après | 1 | 98,4 | 118,5 | 132,6 | 140,9 | 98 ms | 2,00 |
→ « aucune image > 100 ms » n'est **pas vérifiable sur la VM** : son rendu seul coûte 60-80 ms par
image. Ce qui reste au fil principal dans les pires images turbo : GC 10-20 ms + une famille
d'étalement (sol ≈ 8 ms dont maillage du relief 6 ms, couches ≈ 7 ms) + cuisson ≤ ~10 ms. Le PC tranchera.
Vent : vitesse et poses inchangées — même image au pixel (captures HEAD vs ④,
vent du snapshot et vent 0,9 : 0 px d'écart). **D109** : (a) fait (halo avant la couverture, ZIndex 1 ;
orientation 0 identique à HEAD, orientation 1 : halo visible) ; (b) vérifié ; (c) fait ; (d) reportée
(plantes + maison ≈ 400 draw calls sur 2 028 à ×4 ; masquer `Objects` ne baisse pas le rendu VM [n=1]).
Écarts au kickoff : « semaine suivante dès que la précédente est appliquée » existait déjà
(`_etale == null` dans `_Process`) : vérifié, inchangé. GC aussi testé par `DOTNET_GCgen0size`
(2 Mo : 18 pauses de ~36 ms ; 64 Mo : 2 pauses de ~215 ms) → rejeté, la cause est le nombre de
finaliseurs. Reste hors tronçon : `SimBridge.Request` (~0,9 Mo de chaîne par semaine, tas des gros
objets), `PlantShadow` (~6 Mo de tableaux / 25 s), conversions de chaînes Godot.

### Tronçon ⑤ (2026-10-19) — pleine résolution mesurée, bilan, VM llvmpipe
**Option de mesure** `--capture-pleine-res=1` (`tools/perf_vm.sh -R`, `world/WorldView.Capture.cs`) :
`stretch_shrink` 2 → 1 (SubViewport 1920×1080) et Zoom caméra = palier × 2 (`ZoomCamera`, 4 poses :
Camera, Capture, Planche) → même cadrage, mêmes tailles à l'écran ; palier logique (`CurrentZoom`,
LOD, 1/zoom de la vie macro) et `TileWPx` inchangés. Défaut intact. Vérifié : draw calls et
primitives identiques à ±10 entre les deux modes, à chaque palier → même scène, seul le remplissage change.
VM chargée : un process d'un AUTRE projet (`aria/bot.py`, 35-39 % CPU) tourne en continu ; charge 3,7-4,0
au départ de chaque run (sous le seuil 4 du script).
| banc E s45, 20 s | n | médiane ms ×1/2 → ×1 | rendu CPU ms | > 100 ms /20 s | draw | surcoût médiane |
|---|---|---|---|---|---|---|
| ×0,5 | 2 / 1 | 80,0 et 79,0 → 99,4 | 68-80 → 87 | 35 et 4 → 90 | 1830 | **+20 ms [VM, n=1 en ×1]** |
| ×1 | 1 / 1 | 80,8 → 106,8 | 69 → 95 | 2 → 183 | 2357 | **+26 ms [VM, n=1]** |
| ×2 | 1 / 1 | 77,1 → 103,8 | 66 → 92 | 2 → 187 | 2544 | **+27 ms [VM, n=1]** |
| ×4 | 1 / 2 | 75,8 → 107,2 et 106,5 | 64 → 93-95 | 0 → 185 et 184 | 2016 | **+31 ms [VM, n=1 en ×½]** |
→ **Donnée d'entrée du sprint « plante assemblée »** : sur la VM, la pleine résolution ajoute
**+20 à +31 ms par image [VM llvmpipe, n=1-2]** (+25 à +40 %), croissant avec le palier, tout en rendu.
llvmpipe remplit les pixels sur CPU (16 fils) : ce chiffre ne se transpose PAS à la HD 4600, dont le
remplissage est le point faible attendu (4× les pixels, conception décision 8). Seul un banc E sur le PC
(`-R` n'existe qu'en capture VM ; pas d'option F5) tranchera — à prévoir dans le sprint plante assemblée.
(La 1re mesure ×0,5 ×½ : p95 199,7, 35 images > 100 ms, pire image = cuisson 7 ms + rendu non mesuré :
bruit de démarrage [n=1], non reproduit au 2e run.)

**Bilan contre les critères — rapport d'étalonnage du PC de Nico ABSENT** (banc E pas encore lancé
sur le PC). Aucune conversion VM → PC n'est faite (rien pour la caler). Chiffres VM bruts, s45, ×½ (défaut) :
| critère (PC) | chiffre VM brut | tenu ? |
|---|---|---|
| 60 FPS à ×4, 60 s/semaine, vent | médiane 75,8 ms, p95 88,2 [VM, n=1] (≈ 13 FPS) | **inconnu** (VM : rendu logiciel 64 ms/image à lui seul) |
| 30 FPS de ×0,5 à ×2 | médianes 79-81 / 80,8 / 77,1 ms [VM, n=1-2] | **inconnu** |
| accéléré : aucune image > 100 ms | turbo max 140,9 ms, 1 s/semaine max 131,1 ms [VM, n=1, ④] | **inconnu** (non vérifiable sur la VM) |
Ce que la VM établit sans le PC (portable : draw calls, primitives, ms CPU par poste) : à ×4 s45, 2 016
draw calls [n=1] contre 2 730 [n=2] au départ de ① ; postes CPU ≤ 0,3 ms/image hors semaine ; vie macro
0 appel/s de `_Draw` entre deux snapshots ; ombres 1 appel/s ; GC 10-20 ms par collecte (④).
Fermeture du bilan dès que le rapport PC arrive : le recopier dans « Mesures », puis ratio PC/VM par
ligne (médiane, rendu CPU/GPU) et application aux 3 critères ; rejouer au besoin `-A 0` / `-A 1` /
`-E 75 -A 60` (④) pour l'accéléré.

**Vue** : légende F1 — touche E déjà présente ; I vie macro décrit le peintre (« 1 bête par espèce et
par tuile + pullulations, taille réelle : les petites aux forts zooms ») ; texte F4 périmé « LOD :
zoomez ×4 » remplacé par « taille réelle : palier par espèce » (`WorldView.Hud.cs`).
**Écarts** : ×8 non mesuré (hors critères) ; `WorldView.Hud.cs` à 294 LDC (sous 300, inchangé de bande) ;
`ForagerLayer` toujours non touché (reliquat ②).

### Étalonnage PC reçu (Nico, 2026-10-19) — banc E s45 ×4, F5 Windows
Machine : i5-4200H (4 fils), HD 4600 via ANGLE/Direct3D11 (`opengl3_angle`), monde 960×540 (×½).
Extraits du rapport (complet ci-dessous) :
| mesure (20 s, 60 s/semaine, vent actif 0,24) | PC [n=1] | VM même cas (⑤) [n=1] | ratio PC/VM |
|---|---|---|---|
| FPS | **32,5** | ≈ 13 | — |
| médiane / p95 / p99 / max ms | 28,9 / 41,6 / 47,0 / 51,3 | 75,8 / 88,2 / — / — | **0,38** (médiane) |
| images > 33 ms / > 100 ms | 123 / **0** | — / 0 | — |
| rendu CPU ms/image | **28,7** (GPU non mesuré par ANGLE) | 64 | **0,45** |
| postes CPU (somme) | **0,25 ms/image** | ≤ 0,3 | ~1 |
| draw calls / primitives | 2 044 / 70 k | 2 016 / 68 k | ~1 |
| GC | 3 collectes, 6,6 ms au total sur 20 s | 10-20 ms par collecte (④) | — |
| tick serveur | 1 146 ms (pire 1 495 ms en s39) | — | — |
Lecture : **il ne reste que le rendu**. Les postes de la vue (vie macro, ombres, vent, cuisson, semaine)
font 0,25 ms sur 30,8 ; le GC ne compte plus (1 image lente sur 123 avec un GC). Avant le sprint : 1-3 FPS
à ×4 (F5 du 2026-10-19 [n=1]) → **×10 à ×30**.

**Bilan contre les critères** (conversion = ratio de médiane ×4 appliqué aux autres paliers [n=1, même
scène supposée comparable — hypothèse]) :
| critère | chiffre PC | verdict |
|---|---|---|
| 60 FPS à ×4 (≤ 16,7 ms) | médiane 28,9 ms, 32,5 FPS [PC, n=1] | ❌ **RATÉ** — il manque ~12 ms par image, tout en rendu |
| 30 FPS de ×0,5 à ×2 (≤ 33,3 ms) | estimé 29-31 ms en médiane [VM 77-81 ms × 0,38, n=1] | 🟡 **probablement tenu, de justesse** — non mesuré au PC (le p95 ×4 vaut 41,6 ms) |
| accéléré : aucune image > 100 ms | estimé ~50-60 ms au pire [VM 131-141 ms × 0,38-0,45, n=1] | 🟡 **probable, non mesuré** — le ratio ne tient pas forcément quand le serveur Python dispute les 2 cœurs |

**Où chercher les 12 ms** (hypothèse à vérifier en mesure, pas un constat) : rendu CPU 28,7 ms pour 2 044
draw calls ≈ 14 µs par draw call [PC, n=1] → viser ≲ 1 000 draw calls à ×4 pour passer sous 16,7 ms.
Plantes + maison ≈ 400 draw calls sur 2 044 [VM ④, n=1] : D109 (d) seule ne suffit pas, il faut la
ventilation des ~1 600 autres (sol par tuile, couches, décor, HUD) — sur le PC, pas sur la VM (llvmpipe ne
réagit pas au nombre de draw calls de la même façon : masquer `Objects` n'y baissait rien). → **entrée du
sprint « plante assemblée »** (ou d'un tronçon perf dédié, à trancher en `/conception`).
Non couvert par ce rapport : pleine résolution (pas d'option F5), turbo et 1 s/semaine au PC.

<details><summary>Rapport brut du PC (collé par Nico)</summary>

```
=== Rapport perf Symbiose — hiver an 1 semaine 6/13 ===
[machine] Windows · Intel(R) Core(TM) i5-4200H CPU @ 2.80GHz (4 threads) · GPU ANGLE (Intel, Intel(R) HD Graphics 4600 (0x00000416) Direct3D11 vs_5_0 ps_5_0, D3D11-20.19.15.5171) · pilote opengl3_angle · F5
[banc E] semaine moteur 45 · zoom ×4 · centre 1650,950 cm · mesure 20 s · monde 960×540
  vie macro au cadrage (avant purge) : 63 entrées dont 0 mourantes
  cadence nominale 60 s/semaine : 0 semaines appliquées · dernier tick vu par la vue 1390 ms
  images 650 en 20.0 s · FPS 32.5 · moyenne 30.8 ms · médiane 28.9 · p95 41.6 · p99 47.0 · max 51.3 ms
  images > 33 ms : 123 · > 100 ms : 0 · draw calls 2044 · primitives 70035
  moniteur TimeProcess 44.59 ms/image · rendu CPU 28.71 · rendu GPU 0.00 ms/image (0 = non mesuré par ce pilote)
  postes CPU (somme 0.25 ms/image, non attribué 30.56) :
    vie macro _Process        0.00 ms/image ( 0.0 %) ·      32 appels/s ·       0 Ko alloués/s
    vie macro _Draw           0.00 ms/image ( 0.0 %) ·       0 appels/s ·       0 Ko alloués/s
    ombres _Draw              0.03 ms/image ( 0.1 %) ·       1 appels/s ·      24 Ko alloués/s
    soleil (UpdateSun)        0.01 ms/image ( 0.0 %) ·      32 appels/s ·       0 Ko alloués/s
    vent (poses)              0.20 ms/image ( 0.6 %) ·      32 appels/s ·       1 Ko alloués/s
    cuisson (file)            0.01 ms/image ( 0.0 %) ·      32 appels/s ·       0 Ko alloués/s
    plantes _Draw             0.01 ms/image ( 0.0 %) ·      14 appels/s ·       0 Ko alloués/s
    semaine (étalement)       0.00 ms/image ( 0.0 %) ·      32 appels/s ·       0 Ko alloués/s
    attente (marge)           0.00 ms/image ( 0.0 %) ·      32 appels/s ·       0 Ko alloués/s
    tapis/sol                 0.00 ms/image ( 0.0 %) ·      32 appels/s ·       0 Ko alloués/s
  à-coups : 123 images > 33 ms, dont 0 pendant l'application d'une semaine, 0 avec un step en vol, 1 avec un GC · pause GC totale 6.6 ms (0.01 ms/image)
    étalement, pire passage par famille : sol 0.0 plantes 0.0 vie macro 0.0 couches sol 0.0 structures 0.0 météo 0.0 ménage 0.0 ms
    étalement, alloué par famille : sol 0.0 plantes 0.0 vie macro 0.0 couches sol 0.0 structures 0.0 météo 0.0 ménage 0.0 Mo
    collectes GC gen0/1/2 : 2 / 1 / 0 · mode Interactive · serveur GC False · alloué 3 Mo (tous threads)
    cuissons 0 · poses cuites 0 (0.0 par cuisson) · vent force 0.24 (actif)
    dernier GC : gen0 · pause 2.3 ms · tas 17 Mo · promus 0.0 Mo · épinglés 0 · finaliseurs en attente 54 · compacté True · concurrent False
    pire 51.3 ms : rendu CPU 32.4 ms · postes — · GC 0.0 ms
    pire 48.8 ms : rendu CPU 26.7 ms · postes — · GC 0.0 ms
    pire 47.4 ms : rendu CPU 27.1 ms · postes — · GC 0.0 ms
    pire 47.1 ms : rendu CPU 27.5 ms · postes — · GC 0.0 ms
    pire 47.1 ms : rendu CPU 28.4 ms · postes — · GC 0.0 ms
[client] FPS 29 · tick 1390 ms · cadence 2,9 s/sem (2,4 j/s)
  plantes 272 (+0 pousses) · segments 1243 · vie macro 25 entrées dont 0 mourantes, AFFICHÉE · butineurs 0 · ombres ON · zoom ×4
  cadence : phase Saison · mode Saison · 60 s/semaine · monde « full » seed 42 · semaine moteur 45
[serveur] tick moteur 1146,2 ms · N plantes 272 · RSS —
[rendu — frame 35,0 ms (moy. ~1 s) · draw calls 2044 · objets 3178 · primitives 70034 · couches : tout]

--- pires ticks (serveur) ---
  s39 (an 1) : 1494,6 ms · 224 pl · 1136 seg · RSS —
  s43 (an 1) : 1487,2 ms · 255 pl · 1212 seg · RSS —
  s33 (an 1) : 1401,4 ms · 172 pl · 865 seg · RSS —
  s15 (an 1) : 1357,5 ms · 115 pl · 361 seg · RSS —
  s36 (an 1) : 1245,9 ms · 186 pl · 997 seg · RSS —
--- état courant ---
  s44 (an 1) : 1146,2 ms · 272 pl · 1243 seg · RSS —
```
</details>

### F5 ressenti — PROCÉDURE COURTE POUR NICO (après le banc E ci-dessous)
`git pull`, F5, **full** → Lancer. Espace (saison, 60 s/semaine). Molette jusqu'à ×4 sur la tuile E
(est de la maison). Répondre par oui/non + un mot :
1. À ×4, c'est fluide (pas de saccade au vent, pas d'à-coup à chaque nouvelle semaine) ?
2. La vie macro est-elle lisible et à la bonne taille (limace, merle dès ×0,5 ; coccinelle ×4 ; puceron ×16) ?
3. Les pullulations se voient-elles (grappes de pucerons / moustiques / cloportes aux points chauds) ?
4. Le mode accéléré (M) est-il agréable (pas d'image figée) ?
5. F1 : la légende de I (vie macro) est-elle claire ?

### F5 ressenti — réponses de Nico (2026-10-19)
1. **Fluidité** : « beaucoup plus fluide, mais ça chute à moins de 10 FPS parfois ». Second rapport F4
   (automne s35, ×8, **Continu 3 s/semaine**) : **FPS 5, frame 199 ms, 936 draw calls**, tick serveur
   2 354 ms (s34) contre ≤ 1 495 ms au banc nominal du même jardin [PC, n=1 chacun] ; vie macro 311 entrées,
   70 butineurs. → **critère accéléré « aucune image > 100 ms » RATÉ** [PC, n=1]. Pas les draw calls ;
   hypothèse contention CPU Python ↔ Godot (priorité réduite non vérifiée sous Windows), suspects
   `ForagerLayer` (jamais optimisé) et arrivée des semaines. À mesurer (le rapport F4 n'a pas les postes).
2. **Vie macro** : pas visible, ne le dérange pas ; ce qu'il voit, il ne sait pas l'identifier.
3. **Pullulations** : non vues, ne sait pas où regarder.
4. **Accéléré** : « ça va mieux ».
5. **F1** : la ligne sous « I vie macro… » est coupée en bas de l'écran (bug).
Hors questions : détails des feuilles beaucoup plus visibles, mais **demande une légende** (liseré
brun, taches noires) ; **×4 = le zoom où l'on a envie de rester**, ×2/×1/×0,5 « horribles » (blobs).
Décision de Nico : carnet = observé, encyclopédie = confirmé/appris, + légende technique au survol
(plantes et animaux). Tout est versé dans `docs/rendu/pixelart/entree_plante_assemblee.md`.

### Étalonnage PC — DEMANDE À NICO (seul point F5 de mesure du sprint)
« `git pull`, F5, choisis **full** → Lancer, puis **tout de suite** touche **E** (sans geste ni
autre touche). Attends ~2-4 min (le jardin avance tout seul jusqu'en hiver an 1, zoome ×4, mesure
20 s) jusqu'au message « banc E terminé — rapport copié », puis colle le rapport ici. »
(Re-E pendant le banc = abandon. Si le jardin a déjà dépassé la semaine 45 : relancer F5.)

## §REPRISE
Sprint **CLOS**, golden jamais re-figé (`22768f33…`). Étalonnage PC reçu et converti (section
« Étalonnage PC reçu ») : **×4 = 32,5 FPS** [PC, n=1] (avant 1-3), critère 60 FPS **raté**, ~12 ms à
trouver, tout en rendu CPU (~14 µs par draw call, 2 044 draw calls). ×0,5-×2 à 30 FPS et accéléré
< 100 ms : probables, non mesurés au PC. F5 ressenti reçu : accéléré **raté** (5 FPS à ×8,
Continu 3 s/semaine [PC, n=1]). **Suite** : `/conception` du sprint « plante assemblée » à partir de
`docs/rendu/pixelart/entree_plante_assemblee.md` (silhouettes, perf ×4 + accéléré, légende des signes).
Mesurer par `tools/perf_vm.sh -E 20 [-z Z] [-x MacroLife] [-O] [-R]`.
