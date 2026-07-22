# Backlog — run éternel

> Fragment de [`BACKLOG.md`](../../../BACKLOG.md) — les entrées de sprint qui
> concernent ce thème, reprises **verbatim**. L'index global des thèmes et
> les kickoffs de dette dormante restent à la racine.

| Sprint | Fichier kickoff |
|---|---|
| **Sprint STABILISATION PERF EN RUN ÉTERNEL (perf + vue, D66)** — ✅ **TERMINÉ 2026-07-05** (`/sprint-auto`, ①→④). Le monde complet 8 tuiles ralentissait puis PLANTAIT au fil des années (philo #4). Diagnostic 3 moteurs traité : **① profileur** `tools/profile_memoire.py` PROUVE **aucune fuite indépendante de N** (RSS suit N, seedbank déjà purgée → M3=M1, pas de colmatage) [golden INTACT `061934db…`] ; **② spatial LOD LightField** = `fields/light_index.py` (`ObstacleIndex`) + cache géométrique, bit-identique, **LightField −57 %** (solde la boucle reçue O(N²) restante de D32) [golden INTACT] ; **③ capacité de charge émergente** = germination férale graduée par la couverture `(1-couv)^4` (3 canaux) + self-thinning avancé → **N plafonne** (~197 stable dès l'an 6, plateaux par tuile #7) + backstop pur-perf `sim/capacite.py` cap 800/tuile jamais firé [golden RE-FIGÉ MAÎTRISÉ `061934db…`→`84d35983…`, `population_hash` re-figé même cause `5a1873db…`→`c2b4a01d…`] ; **④ banc d'observation perf** = snapshot `perf:{ms_tick,n_plants,rss_mo}` (`tools/simserver/perf.py`) + overlay debug Godot F4 [golden INTACT, build C# vert]. Réécriture C/C++/C# REJETÉE (problème algorithmique). Réserve numpy/Cython non activée. **Reste F5 Nico** (turbo ~10-15 ans : N plafonne + ms/tick stable + aucun `⚠ cap perf tuile`). | `docs/perf/run_eternel/conception_perf_run_eternel.md` + `sprints/sprint_perf_run_eternel/` (00_etat + 01→04) |
