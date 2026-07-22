# Backlog — scatter

> Fragment de [`BACKLOG.md`](../../../BACKLOG.md) — les entrées de sprint qui
> concernent ce thème, reprises **verbatim**. L'index global des thèmes et
> les kickoffs de dette dormante restent à la racine.

| Sprint | Fichier kickoff |
|---|---|
| **Sprint PERF — Scatter de la boucle lumière-REÇUE (D70)** — ✅ **TERMINÉ 2026-07-09** (`/sprint-auto sprint_perf_tick_on2`, ①→②, commits `68020b2`/`1c1ea19`/`35aab7a`). Résidu perf après D66②/D67 : au régime lourd, **LightField = 62 % du tick, dont `ObstacleIndex.covering` = 40 %** (boucle lumière-**reçue** restée en **gather**, `reach` dimensionné par `max_height` GLOBAL). ① boucle reçue **renversée en scatter émetteur→échantillons** (nouvelle classe `ReceiverIndex`+`in_bbox` dans `light_index.py`, récriture `light.compute`, verrou `test_scatter_lumiere_recue` == strict) — **golden `24ec11e7` INCHANGÉ (bit-identique, jamais re-figé)** ; ② validation perf : **`covering` DISPARU du top-40**, remplacé par `in_bbox` (0,045 s, marginal), plus de poste O(N²) reçu. Les 2 boucles lumière (sol D32 + reçue) sont désormais scatter+LOD. Diff 100 % Python (aucun rebuild C#). Refactor auto-léger no-op (light.py 242 / light_index.py 54 🟢). ③ cap démographique clonal SORTI → **dette design D71** (dormante, à rouvrir si le gameplay le demande). Quick-win fongique connexe livré avant (`7c5344e`, −13,5 %). **Reste F5 Nico** (rendu inchangé + relevé tick serveur vs ~8 s an 2). | `docs/conception/CONCEPTION_PERF_SCATTER_RECUE.md` + `sprints/sprint_perf_tick_on2/` (00_etat + 01→02) |
