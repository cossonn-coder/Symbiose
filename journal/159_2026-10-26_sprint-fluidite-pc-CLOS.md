## 2026-10-26 — Sprint FLUIDITÉ PC (D116 + lisière D112 c/j) — CLOS

`/sprint-auto sprint_fluidite_pc` (`sprints/perf/fluidite/sprint_fluidite_pc/`), 4 tronçons,
golden `fecccded8cd146368623372919f4bdc6c61fb8bb997c75fdc59806f08dc3898b` **jamais re-figé**,
pont 0.5.58. Doc : `docs/perf/fluidite/conception_fluidite_pc.md`. Détail par tronçon :
`00_etat.md` (bilans ①→④).

### Tronçons
- **① instruments** (`b5c9e89`) — banc E en 3 phases (C moteur en pause → A normal → B rendu
  suspendu), rendu CPU au bilan, `TimeProcess` retiré, PollenLot innocenté (constat 2 réfuté),
  oracles `test_population`/`test_vent`/`test_peripherie_pont` recalés → D116 (d) fermée.
- **② lisière : bug F10 + coutures** (`9c6cbc9`) — F10 ×2 non reproduit sur VM, trace console
  `[DecorLayer] profil …` ; coutures = arrondi des sommets au pixel → bandes jointives.
- **③ kit + forêt** (`410580e`) — atlas patchwork (une texture, 1 draw call), prairie/friche en
  touffes, forêt en rideau ; plus de redessin hebdomadaire du décor ; graine de lisière incluant le
  seed du terrain (philo #7).
- **④ eau, roche, bilan** — rivière (lit en grille, reflets, galets/roseaux, scintillement sur un
  nœud enfant à 0,27 ms/redessin [n=1 run, VM]) ; falaise (strates en blocs, 3 pentes par la
  géométrie, face claire/ombre selon le soleil du monde, éboulis pilotés par l'entaille) ; anciens
  tracés conservés dans `DecorLayer.Aplats.cs`.

### Bilan VM ④ (charge 8-14, llvmpipe : limite de tous les chiffres)
- Banc 3 phases : A 2,51 s/sem, B 1,67 s/sem, C moyenne 202-210 ms/image [n=2 runs, VM] — même
  ordre qu'au ① : la lisière ne coûte rien en régime.
- Redessin du décor au changement de palier : ×4 164-165 ms sur le terrain normal [n=2 runs, VM],
  ×2 66-106 ms avec rivière+falaise [n=1-3 runs, VM] → à verser dans la 2ᵉ conception.

### Dette et suite
- D112 (c)(j) fermées côté code, F5 Nico restant ; D116 = diagnostic instrumenté, **attend UN run
  PC** (protocole `00_etat.md` §F5) → 2ᵉ `/conception D116` (leviers + arbitrage cadence ↔ images).
