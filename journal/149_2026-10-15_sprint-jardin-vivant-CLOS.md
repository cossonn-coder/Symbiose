# 2026-10-15 — Sprint JARDIN VIVANT (sprint A rendu) — CLOS

`/sprint-auto`, T0→T5. Pure vue + un export de pont (0.5.44, `weather.wind`).
**Golden `22768f33…` jamais re-figé**, `dotnet build` vert, `test_sim_server`
283/283. Doc : `docs/rendu/pixelart/conception_jardin_vivant.md` ; état et
mesures : `sprints/rendu/pixelart/sprint_jardin_vivant/00_etat.md`.

- **T0 banc de capture VM** (`e88da4b`) : Godot portable + Xvfb (sans sudo) +
  Movie Maker → PNG que l'agent regarde ; `tools/capture_vm.sh`.
- **T1 palette + curseur** (`447da15`) : palette maître 34 couleurs + Bayer 4×4
  (shader OKLab sur le SubViewport, F11 avant/après), main gantée, losange de survol.
- **T2 pré-cuisson** (`0bb6cb6`) : un SubViewport par plante, file à budget
  (6 plantes / 80 segments par frame), écran d'abord, image identique.
- **T3 vent en onde** (`14c0fc4`) : pont 0.5.44, atlas de 8 poses de flexion,
  onde cohérente + balancement propre ; calme = image fixe.
- **T4 canicule + pluie/orage** (`c0e9a34`) : variantes cuites par plante
  (feuilles qui pendent si `secheresse`, feuillage trempé qui se ressuie).
- **T5 neige, givre, grêle + banc F5** : calottes de neige qui raidissent la
  plante et tombent par plaques sous le vent (plante par plante), givre bleuté
  liseré, feuilles déchiquetées ∝ `grele` (trace lue au snapshot), aucune charge
  sous voile/cloche ; **défilé F12** des 7 situations (10 s chacune, encart ciel
  nommé). Écart kickoff : `CouvertureLayer` ≠ voiles (c'est `CoverLayer`).
- **Découverte** (non corrigée, décision Nico) : Godot envoie toujours seed 42 →
  `BANC_SEED` d'`effondrement` (12345) jamais appliqué au F5.

Dette : **D72 → CLOSE** (archivée, lot E) ; D34/D44 annotées (couvert / non
couvert). Reste **F5 Nico** : « le jardin est-il beau et vivant ? ». Ensuite
sprint B (faune + champignons + fumée/eau) à concevoir.
