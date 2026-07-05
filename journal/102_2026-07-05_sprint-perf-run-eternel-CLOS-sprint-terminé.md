# 2026-07-05 — Sprint STABILISATION PERF EN RUN ÉTERNEL (D66) — CLOS / sprint terminé

**`/sprint-auto sprint_perf_run_eternel`, tronçons ①→④.** Le monde complet
8 tuiles + maison + vie macro ralentissait puis **plantait** au fil des années.
Objectif : borner le coût CPU+mémoire à horizon infini (philo #4) sans trahir
l'émergence (#1/#2/#7). Réécriture C/C++/C# **rejetée** (problème algorithmique,
pas de langage : seul l'asymptote compte en run éternel).

## Tronçons

- **① Profileur mémoire par catégorie** — `tools/profile_memoire.py` (RSS via
  `resource.getrusage`, comptages d'objets par catégorie). VERDICT mesuré
  (8 tuiles × 4 ans) : **aucune fuite indépendante de N** — RSS suit N en
  lockstep, le suspect `SeedBank.species` est déjà purgé par
  `tick_species_aging`. Donc M3 (mémoire) = M1 (population), pas de colmatage.
  Golden INTACT `061934db…`.
- **② Spatial LOD LightField** — `fields/light_index.py` (`ObstacleIndex`,
  buckets par plot, re-tri = ordre exact de `order`) + cache géométrique dans
  `light.py`. Coupe la boucle « lumière reçue » O(N²)→O(N·k), **bit-identique**
  (n'élague que des facteurs 1.0 neutres). **LightField −57 %** (~19→8 ms/tick,
  2 tuiles). Golden INTACT. Solde la boucle reçue O(N²) restante de D32.
- **③ Capacité de charge émergente + backstop** — germination férale GRADUÉE par
  la couverture `(1-couv)^4` (3 canaux : succession/reproduction/ramets, seuil
  adventice 0.6→0.5) + self-thinning avancé (`shade_stress` seuil 0.6→0.55).
  **N plafonne** (~197 stable dès l'an 6, plateaux différents par tuile → #7).
  Backstop pur-perf `sim/capacite.py` cap 800/tuile (jamais firé). Golden
  **RE-FIGÉ MAÎTRISÉ ANNONCÉ** `061934db…`→`84d35983…` (dérive localisée 44→42
  plantes au smoke, déterminisme intact) ; digest satellite `population_hash`
  re-figé pour la MÊME cause `5a1873db…`→`c2b4a01d…` (6 invariants structurels
  de `test_population` intacts). Suite complète (46 suites hors 500 ans) VERTE.
- **④ Vue Godot — banc d'observation perf** — champ snapshot lecture seule
  `perf:{ms_tick,n_plants,rss_mo}` (`tools/simserver/perf.py`, chronométré
  AUTOUR de `tick_semaine()`, jamais dedans) + overlay debug Godot F4 (3e ligne,
  étiquette `[debug]`, philo #5). Golden INTACT, build C# vert.

## Décisions de design

- **Le digest satellite `test_population` se re-fige pour la même cause que le
  golden principal.** ③ change la végétation → les densités de vie macro
  changent ; ce n'est pas un second golden caché mais une autre fenêtre sur le
  même comportement délibérément modifié. Re-figeage étendu et documenté, après
  vérification que les 6 invariants structurels tiennent.
- **Réserve numpy/Cython NON activée** : les mesures actuelles (−57 % lumière +
  N borné) suffisent, on ne paie pas la complexité tant que la perf ne serre pas.

## État

Golden final `84d35983…`. Tous fichiers du sprint en zone verte (≤300 LDC pur,
max `serialize.py` 248) → refactor auto-léger sans objet. **Reste F5 Nico** :
config full → F4 → turbo ~10-15 ans, vérifier que N plafonne, que ms/tick cesse
de doubler, et qu'aucun `⚠ cap perf tuile` n'apparaît en jeu normal. D66 → 🟢 ✅
(Python complet) dans DETTE.md ; BACKLOG.md à jour.
