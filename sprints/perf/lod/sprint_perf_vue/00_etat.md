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
| ② | `02_vie_macro.md` | peintre D2 + points chauds + taille réelle, lot par tuile, fuite | intact (pont 0.5.45) | à faire |
| ③ | `03_ombres_lot.md` | ombres en lot par tuile | intact | à faire |
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

### Étalonnage PC — DEMANDE À NICO (seul point F5 de mesure du sprint)
« `git pull`, F5, choisis **full** → Lancer, puis **tout de suite** touche **E** (sans geste ni
autre touche). Attends ~2-4 min (le jardin avance tout seul jusqu'en hiver an 1, zoome ×4, mesure
20 s) jusqu'au message « banc E terminé — rapport copié », puis colle le rapport ici. »
(Re-E pendant le banc = abandon. Si le jardin a déjà dépassé la semaine 45 : relancer F5.)

## §REPRISE
Lire `CLAUDE.md` + ce fichier + la conception, puis le prochain kickoff « à faire » (②).
① fait : banc E + instrument. Mesurer chaque tronçon par `tools/perf_vm.sh -E 20 [-z Z] [-x MacroLife] [-O]`.
Rapport PC de Nico attendu → à recopier dans « Mesures » (conversion en ⑤). ×1/×2/×8 VM manquants.
Lancement : `/sprint-auto sprint_perf_vue`.
