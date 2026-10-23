# 157 — 2026-10-23 — Conception FLUIDITÉ AN 2 (D114 recadrée) — FIGÉE

`/conception D114`. Doc : `docs/perf/fluidite/conception_fluidite_an2.md` ; sprint :
`sprints/perf/fluidite/sprint_fluidite_an2/` (5 tronçons, golden jamais re-figé `fecccded…`).

## Constats (HEAD `5c69ac6`, VM, graine 1521550718, `full`)
- Tick an 2 = 1 074 ms [n=1 run] à 654 plantes : le « +33 % » de D114 (1 884 ms) venait d'un
  run sous charge ; critère D114 déjà tenu.
- Automate innocent côté Python (24 ms/tick [n=1 run]) ; Nico : « c'est peut-être un autre
  ralentissement, il faut mesurer ».
- Goulot ressenti = la VUE : au banc E, 1 s/sem demandée → 2,73 s obtenues [n=1 run] ; semaine
  en application 13,9 s / 30 ; step bloqué tant que la semaine précédente s'applique
  (`WorldView.cs:627`) ; cuisson hors budget (pics 60-74 ms).
- Delta de snapshot par plante écarté : 589/590 plantes poussent > 1 cm/sem [n=1 semaine].

## Décisions (Nico)
- Cible : PC, an 2, 1 s/sem → ≤ 1,5 s/sem effectives, aucune image > 100 ms, automate ON ou OFF.
- Périmètre moteur + pont + vue. Interdits : brider la population, re-figer le golden.

## Tronçons
① banc de cadence (headless n≥3 + banc E automate) · ② moteur bit-identique (−20 %) ·
③ pont allégé (`auxin` hors snapshot, flottants arrondis) · ④ vue (chevauchement step /
application, lecture des plantes hors thread principal, cuisson sous budget) · ⑤ bilan.
