## 2026-10-23 — Sprint FLUIDITÉ AN 2 (D114 recadrée) — CLOS

`/sprint-auto sprint_fluidite_an2` (`sprints/perf/fluidite/sprint_fluidite_an2/`), 5 tronçons,
golden `fecccded8cd146368623372919f4bdc6c61fb8bb997c75fdc59806f08dc3898b` **jamais re-figé**,
pont 0.5.57. Doc : `docs/perf/fluidite/conception_fluidite_an2.md` (§6 bilan).

### Tronçons
- **① banc de cadence** (`ab7ec72`) — `tools/banc_cadence.py` headless + banc E automate
  ouvert/fermé ; graine `--capture-seed` lue en float (1521550718 → 1521550720) corrigée.
- **② moteur bit-identique** (`c243170`) — population, voisinage indexé O(N), sol/autotoxicité en
  une passe, géométrie O(n) : tick an 2 −22,6 % [n=3 runs, VM].
- **③ pont allégé** (`ce0f965`) — segments sans `auxin`/`has_bud`, flottants arrondis : réponse
  −37 % ; `_snapshot` +26 % (cible −40 % manquée, le reste est dans `sim/`).
- **④ vue** (`303276c`) — semaine suivante calculée pendant l'application, plantes lues sur le
  thread du pool, survols différés : banc E 7,5 → 2,7-3,0 s/sem [n=3 runs, VM]. Cuisson : les pics
  sont des créations de pages d'atlas 2048². GC .NET ~×2.
- **⑤ bilan** (non commité par le tronçon) — mesure seule.

### Bilan ⑤ (VM partagée avec une autre session, charge 2-15 : limite de tous les chiffres)
- Headless A/B entrelacé `5c69ac6` / `303276c` : tick an 2 1 350 → 1 056 ms **−21,8 %** [n=3+3
  runs] ; pire semaine 2 023 → 1 277 ms ; snapshot 239 → 302 ms ; réponse 5 072 → 3 193 Ko.
- Banc E 1 s/sem : OFF 7,5 → 3,33-3,75 s/sem [n=2 runs hors run sous charge 14] ; automate
  fermé 6,0-7,5 → 3,00 [n=3 runs] ; ouvert 7,5 → 3,00-3,75 [n=3 runs]. Images > 100 ms : 100 %
  (llvmpipe, non interprétable). Pages d'atlas : médiane 83 ms, max 697 ms [n=94 créations].
- **Cible PC (≤ 1,5 s/sem, aucune image > 100 ms) non tenue sur VM** ; estimée à la limite sur PC
  [conversion ÷ 1,3, pas une mesure] → 3 rapports PC demandés (protocole §F5 de `00_etat.md` :
  Main Run Args `--capture-banc=full --capture-seed=1521550718 --capture-etalonnage=30
  --capture-banc-semaine=90 --capture-banc-cadence=1`, ± `--capture-banc-automate=ferme|ouvert`).
- Cause « automate » du F5 jamais reproduite sur VM.

### Dette
- **D114 close** (archive lot H) → **D116 ouverte** : chaîne du step (tick + parse + lecture),
  pages d'atlas, GC .NET, automate PC, + oracles de tests rouges AVANT le sprint
  (`test_population` hash périmé `a60c4a31…`, `test_vent` 52/54, `test_peripherie_pont` attend 0.5.41).
- Suite de la file : **D112 sprint B vue**. Rappel : « Vigueur infinie (test) » ON → OFF avant packaging.
