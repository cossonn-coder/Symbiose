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
| ② | `02_vie_macro.md` | peintre D2 + points chauds + taille réelle, lot par tuile, fuite | intact (pont 0.5.45) | **fait** (non commité) |
| ③ | `03_ombres_lot.md` | ombres en lot (un maillage) | intact | **fait** (non commité) |
| ④ | `04_cadence_acoups.md` | cadence adaptative, priorité serveur, à-coups, D109 | intact | à faire |
| ⑤ | `05_vue_bilan.md` | pleine résolution mesurée, bilan converti PC, F5 ressenti | intact | à faire |

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

### Étalonnage PC — DEMANDE À NICO (seul point F5 de mesure du sprint)
« `git pull`, F5, choisis **full** → Lancer, puis **tout de suite** touche **E** (sans geste ni
autre touche). Attends ~2-4 min (le jardin avance tout seul jusqu'en hiver an 1, zoome ×4, mesure
20 s) jusqu'au message « banc E terminé — rapport copié », puis colle le rapport ici. »
(Re-E pendant le banc = abandon. Si le jardin a déjà dépassé la semaine 45 : relancer F5.)

## §REPRISE
Lire `CLAUDE.md` + ce fichier + la conception, puis le prochain kickoff « à faire » (④).
① fait : banc E + instrument. ② fait (pont 0.5.45, golden intact `22768f33…`, suites pont 285/285). ③ fait (ombres = 1 maillage, vue C# pure, golden intact, build vert) → prochain : ④. Mesurer chaque tronçon par `tools/perf_vm.sh -E 20 [-z Z] [-x MacroLife] [-O]`.
Rapport PC de Nico attendu → à recopier dans « Mesures » (conversion en ⑤). ×1/×2/×8 VM manquants.
Lancement : `/sprint-auto sprint_perf_vue`.
