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
| ① | `01_banc_cadence.md` | banc headless n≥3 + banc E automate ON/OFF/onglet → baseline + cause « automate » | intact | **FAIT** (non commité) |
| ② | `02_moteur_bit_identique.md` | postes plats du tick an 2, −20 % visé | INCHANGÉ (bit-identique) | à faire |
| ③ | `03_pont_allege.md` | `auxin` hors snapshot, flottants arrondis, `_snapshot` −40 % | intact (pont +1) | à faire |
| ④ | `04_vue_application.md` | lecture des plantes hors thread principal, cuisson sous budget, cause ① | intact | à faire |
| ⑤ | `05_bilan.md` | banc final VM, protocole PC, clôture D114 | intact | à faire |

## Mesures de référence (HEAD `5c69ac6`, VM, graine 1521550718, `full`)
Headless [n=1 run] : tick an 0/1/2 591/921/1074 ms, snapshot an 2 183 ms, 654 pl. ; automate ON
564/853/1022 ms, automate 24 ms, 613 pl. Banc E `-E 30 -A 1 -W 90` [n=1 run] : 2,73 s/sem
obtenues, pipe 1 139 ms, parse 150-297 ms, réponse 1,5 Mo, cuisson pics 60-74 ms/image.
(Le banc E a affiché « seed 1521550720 » pour `-S 1521550718` — à éclaircir au ①.)

## ① Banc de cadence — FAIT (2026-10-23)
Outils : `data/code/tools/banc_cadence.py` (headless, `--runs/--seed/--semaines/--automate`,
sondes posées sur l'INSTANCE du serveur, golden intact) ; `tools/perf_vm.sh -a ouvert|ferme`
(→ `--capture-banc-automate`, mêmes gestes que la touche A ± fermeture du panneau) ; le
rapport E/C dit maintenant « automate BRANCHÉ/débranché · onglet Automate VISIBLE/fermé ».
**Graine** : `--capture-seed` était lu en `float` (24 bits de mantisse) → 1521550718 devenait
1521550720. Lu en entier désormais. ⚠️ Les mesures E de la conception (2,73 s/sem, 1,5 Mo)
portaient donc sur UN AUTRE JARDIN : ne plus les comparer aux chiffres ci-dessous.

### Mesures (HEAD `b198967` + ①, VM, graine 1521550718, `full`)
Headless 156 sem. (an 2 = semaines 105-156 ; tick / snapshot / réponse / plantes, moyenne an) :
| cas | tick an 0/1/2 | automate an 2 | snapshot an 2 | réponse an 2 | plantes an 2 |
|---|---|---|---|---|---|
| OFF | 539 / 866 / 1 011 ms [n=3 runs, charge < 2,3] | — | 183 ms (max 342) [n=3 runs] | 5 072 Ko (max 5 771) [n=3 runs] | 654 |
| automate ON | 521 / 830 / 968 ms [n=3 runs, charge < 2,3] | 23,5 ms (max 29) [n=3 runs] | 169 ms (max 312) [n=3 runs] | 4 503 Ko [n=3 runs] | 613 |
Populations identiques entre runs (déterminisme OK). Réponse an 1 (≈ semaine 90 du banc E) :
2,2-2,4 Mo moy., 3,1-3,5 Mo max [n=3 runs].

Banc E `-E 30 -A 1 -W 90 -S 1521550718` (semaine moteur 94-95, ~640 plantes, réponse 3,0-3,3 Mo) :
| cas | s/sem obtenues | FPS | p99 image | rendu CPU | cuisson pire image | semaine en application / 30 s | parse | draw calls |
|---|---|---|---|---|---|---|---|---|
| OFF | 7,50 ×3 [n=3 runs, résolution 1 sem./30 s, charge départ 1,1-3,9] | 4,5-4,8 | 288-361 ms | 122-153 ms | 74-159 ms | 11,6-12,0 s | 264-285 ms | 651-685 |
| automate, onglet fermé | 6,00 / 6,00 / 7,50 [n=3 runs, idem] | 5,0-5,2 | 264-298 ms | 104-145 ms | 74-96 ms | 11,5-12,1 s | 230-249 ms | 631-640 |
| automate, onglet ouvert | 7,50 ×3 [n=3 runs, idem] | 4,7-5,0 | 300-310 ms | 103-141 ms | 71-123 ms | 11,6-12,0 s | 249-302 ms | 753-759 |
Toutes les images > 100 ms dans les 9 runs : la VM (llvmpipe) est dominée par le rendu
logiciel (~100-150 ms CPU/image) → à 5 FPS l'étalement (tranche 6 ms/image) met ~12 s à
appliquer une semaine. Proxy VM pertinent pour les POSTES, pas pour la cadence absolue.

### Diagnostic « automate » [n=3 runs par cas, VM]
**Cause NON reproduite au banc VM.** Automate branché onglet fermé : aucun poste ne bouge
(tick −3 %, il désherbe → −40 plantes, réponse −10 %). Onglet ouvert : seuls écarts mesurés =
**+~100 draw calls/image** (panneau + RichTextLabel, ~+15 %) et la famille « ménage » de
l'étalement (`ApplyAutomate` → `AutomateContent.Rendre` réécrit tout le BBCode à chaque
semaine) : 0,4 ms/image en moyenne vs 0,1, pire passage 30 ms une fois sur 3 runs (vs ≤ 8,7).
Rien de trivial à corriger ici. Pistes pour le ④ (non prouvées) : coût GPU réel du panneau sur
la HD 4600 (invisible sous llvmpipe), relayout du RichTextLabel. → **faire mesurer au PC** :
touche E onglet Automate ouvert vs fermé (le rapport le dit désormais).

### Pour le ② / ③ / ④ (constats mesurés)
- Réponse an 2 ≈ 5 Mo [n=3 runs] (pas 1,5) : l'enjeu du ③ est plus gros que prévu.
- Cuisson : pires images 50-160 ms dans 9/9 runs → le budget de cuisson (④ b) reste n°1 côté vue.

## Ce qui reste
②→⑤.

## §REPRISE
Lire `CLAUDE.md`, ce fichier, le doc de conception, puis le kickoff du premier tronçon
« à faire » (② `02_moteur_bit_identique.md`). Référence headless à re-mesurer avec
`cd data/code && python3 -m tools.banc_cadence [--automate]` (≈ 3 min/run). Lancement : `/sprint-auto sprint_fluidite_an2`.
