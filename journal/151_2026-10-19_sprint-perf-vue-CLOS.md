# 2026-10-19 — Sprint PERF VUE — CLOS (moteur de mesure + allègements, verdict PC en attente)

`/sprint-auto`, ①→⑤. **Golden `22768f33…` jamais re-figé**, `dotnet build` vert à
chaque tronçon. Doc : `docs/perf/lod/conception_perf_vue.md` ; mesures et bilan :
`sprints/perf/lod/sprint_perf_vue/00_etat.md`. Critère : 60 FPS à ×4 sur le PC de
Nico (i5-4200H + HD 4600), 30 FPS de ×0,5 à ×2, accéléré sans image > 100 ms.

- **① banc E** (`9bd6e81`) : touche **E** (F5) ≡ `tools/perf_vm.sh -E` — turbo jusqu'à
  la semaine 45 (full, seed 42), ×4 sur la zone dense, 20 s mesurées, rapport au
  presse-papier (distribution, postes CPU `visuals/PerfPostes.cs`, rendu CPU/GPU).
  Écart : le printemps an 2 n'a pas de vie macro → semaine 45 (272 plantes, 3 848
  bêtes) ; `-W 67` = cas de stress. Fuite `MacroLife` reproduite (7 988 mourantes).
- **② vie macro** (`0dd6bb8`) : peintre `peindre_presence` (1/espèce/tuile + ≤ 3 points
  chauds + grappes), lombric et pollinisateurs hors bloc ; s45 3 848 → 25 bêtes ;
  `MacroLife` taille réelle, pixels fixes, redessin sur événement, fuite corrigée.
  Pont **0.5.45**. ×4 : 2 730 → 2 063 draw calls [VM, n=2].
- **③ ombres** (`01f4bd4`) : un seul `ArrayMesh` sous les plantes, redessin sur
  événement ; écart ON/OFF au bruit [VM, n=2]. `CanvasItemAddTriangleArray` = +55 ms
  [n=1], écarté.
- **④ à-coups** (`6ad47c1`) : `core/LectureSnap.cs` (lectures de snapshot en cache, fin
  des allocations par image → GC 35-45 ms ×~10 → 10-20 ms ×5-6 /20 s) ; cuisson des
  seules poses atteignables (8,0 → 2,9 [n=1]) ; serveur en priorité réduite. Turbo
  p99 380 → 133 ms [VM, n=1]. D109 (a)(c) faits, **(d) reportée au sprint plante
  assemblée** (masquer `Objects` ne baisse pas le rendu VM [n=1]).
- **⑤ bilan** (`313e922`) : `perf_vm.sh -R` pleine résolution, +20 à +31 ms/image
  [VM llvmpipe, n=1-2] ; HUD F1/F4 corrigés. **Critères PC : inconnus** — rapport du
  banc E de Nico absent, aucune conversion VM → PC inventée.

**Verdict PC (banc E, F5 Windows, le soir même)** : ×4 = **32,5 FPS**, médiane 28,9 ms, 0 image
> 100 ms [PC, n=1] — avant 1-3 FPS. Critère 60 FPS **raté** (~12 ms à trouver), mais il ne reste
que le rendu CPU (28,7 ms, ~14 µs par draw call ×2 044) : postes de la vue 0,25 ms, GC négligeable.
×0,5-×2 à 30 FPS et accéléré < 100 ms : probables par ratio PC/VM 0,38-0,45, non mesurés au PC.

Reste : ventilation des draw calls au PC (entrée du sprint suivant), puis F5 ressenti
(fluidité ×4, lisibilité et taille de la vie macro, pullulations, accéléré, ombres
sans fondu ni recouvrement des voisines). Mesures VM ×1, ×2, ×8 manquantes.
Ensuite : sprint « plante assemblée » (absorbe D109 d).
