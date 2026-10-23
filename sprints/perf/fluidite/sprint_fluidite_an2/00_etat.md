# Sprint FLUIDITÉ AN 2 (D114 recadrée) — état partagé

> Conception FIGÉE le 2026-10-23 (`/conception D114`) →
> [`docs/perf/fluidite/conception_fluidite_an2.md`](../../../../docs/perf/fluidite/conception_fluidite_an2.md)
> (LIRE AVANT TOUT TRONÇON : mesures HEAD, ce qui est exclu, cible, décisions).
> **Golden jamais re-figé** : `fecccded8cd146368623372919f4bdc6c61fb8bb997c75fdc59806f08dc3898b`
> (`cd data/code && python3 -m tests.test_golden`). NE JAMAIS lancer `test_epaisseur_500ans`.

## Décisions clés (Nico, 2026-10-23)
- D114 recadrée : le tick n'est plus le goulot (an 2 ≈ 1,07 s VM [n=1 run], critère D114 déjà
  tenu) ; le goulot ressenti = **la vue** (semaine en application 13,9 s / 30 s au banc E VM).
- **Cible** : PC Nico, an 2, cadence test 1 s/sem → **≤ 1,5 s/sem effectives, aucune image
  > 100 ms**, automate branché ou non. Validation par mesure, F5 = ressenti.
- **Périmètre** : moteur + pont + vue. Interdits : brider la population, re-figer le golden.
- Automate : innocent côté Python (24 ms/tick) ; « peut-être un autre ralentissement » (Nico)
  → **mesurer au ①**, ne pas supposer.

## Carte des tronçons
| # | Kickoff | Contenu | Golden | État |
|---|---|---|---|---|
| ① | `01_banc_cadence.md` | banc headless n≥3 + banc E automate ON/OFF/onglet → baseline + cause « automate » | intact | à faire |
| ② | `02_moteur_bit_identique.md` | postes plats du tick an 2, −20 % visé | INCHANGÉ (bit-identique) | à faire |
| ③ | `03_pont_allege.md` | `auxin` hors snapshot, flottants arrondis, `_snapshot` −40 % | intact (pont +1) | à faire |
| ④ | `04_vue_application.md` | lecture des plantes hors thread principal, cuisson sous budget, cause ① | intact | à faire |
| ⑤ | `05_bilan.md` | banc final VM, protocole PC, clôture D114 | intact | à faire |

## Mesures de référence (HEAD `5c69ac6`, VM, graine 1521550718, `full`)
Headless [n=1 run] : tick an 0/1/2 591/921/1074 ms, snapshot an 2 183 ms, 654 pl. ; automate ON
564/853/1022 ms, automate 24 ms, 613 pl. Banc E `-E 30 -A 1 -W 90` [n=1 run] : 2,73 s/sem
obtenues, pipe 1 139 ms, parse 150-297 ms, réponse 1,5 Mo, cuisson pics 60-74 ms/image.
(Le banc E a affiché « seed 1521550720 » pour `-S 1521550718` — à éclaircir au ①.)

## Ce qui reste
Tout (①→⑤).

## §REPRISE
Lire `CLAUDE.md`, ce fichier, le doc de conception, puis le kickoff du premier tronçon
« à faire ». Lancement : `/sprint-auto sprint_fluidite_an2`.
