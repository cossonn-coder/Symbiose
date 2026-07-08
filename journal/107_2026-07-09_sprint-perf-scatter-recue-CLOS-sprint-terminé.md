# 2026-07-09 — Sprint PERF : scatter de la boucle lumière-reçue (①→②) — SPRINT TERMINÉ

> `/sprint-auto sprint_perf_tick_on2`. Perf pure, dans la foulée de D67 (LOD ombre).
> **Golden INCHANGÉ `24ec11e7…` (bit-identique) à chaque tronçon** — optimisation
> algorithmique, zéro delta observable (philo #3).

## Objectif

L'audit du tick (2026-07-09, `tools/profile_monde`) montrait que la boucle
**lumière-REÇUE** de `LightField.compute` pesait **~40 % du tick** : restée en
**gather** (chaque échantillon de récepteur interroge `ObstacleIndex.covering`
avec un `reach` dimensionné par l'ombre la plus longue de la tuile), alors que la
boucle lumière-SOL était déjà passée en **scatter** (D32). Ce sprint renverse la
boucle reçue en scatter émetteur→échantillons — chaque émetteur ne visite plus que
la bbox de sa propre capsule. Approximation ZÉRO : l'ordre d'atténuation (émetteurs
par hauteur décroissante) est préservé → **bit-identique**, golden intouché.

## Tronçons

- **① Scatter de la boucle reçue — golden INCHANGÉ `24ec11e7…`.** Commit `68020b2`.
  Nouvelle classe `ReceiverIndex` (+ `in_bbox`) dans `fields/light_index.py`
  (miroir de `ObstacleIndex` : buckets d'**échantillons** par cellule de plot,
  chaque échantillon = `(ph, ref, sx, sy)`). Récriture de la boucle reçue dans
  `fields/light.py:compute` : par tranche solaire, on indexe les échantillons
  ACTIFS (non masqués par la maison), puis chaque émetteur — itéré dans `order`
  (hauteur décroissante, garanti par `sorted(...reverse=True)`) — atténue
  `att[(ref,k)] *= (1-qd)` des seuls échantillons couverts par sa capsule. Les
  facteurs s'accumulent dans le MÊME ordre que le gather → produit identique
  bit-à-bit. `light_slice = max(LIGHT_FLOOR, att_sum/5)` (division par 5 = les
  échantillons masqués comptent comme 0, réplique exacte du `continue` du gather).
  `ObstacleIndex` retiré de la reçue (conservé pour le sol). Verrou neuf
  `tests/test_scatter_lumiere_recue.py` (équivalence gather==scatter en `==`
  strict, calqué ligne à ligne sur `test_scatter_lumiere_sol.py` : monde smoke
  grandi, 4 saisons, avec ET sans maison).

- **② Validation perf + checklist F5 — golden INCHANGÉ, aucun code moteur touché.**
  Commit `1c1ea19`. Mesure `profile_monde --week 104 --top 40` (491 plantes, an 2
  hiver) : **`covering` (gather reçue) a DISPARU du top 40**, remplacé par
  `light_index.in_bbox` = 0,045 s tottime (rang ~20, marginal) ; `light.compute`
  redescendu au rang 4 (0,175 s). Plus de poste O(N²) sur la lumière reçue : le
  tick est désormais dominé par des postes diffus (`field.tick`, `grids.at_plot`,
  uptake). Note : le ms/tick absolu (554 ms/tick ici) n'est pas comparable à
  l'audit (population/machine distinctes) — l'invariant mesuré est **structurel**
  (le poste quadratique reçu est éliminé). Diff **100 % Python** → aucun rebuild C#.

## Vérifications finales

- Golden final **`24ec11e7…`** (INCHANGÉ / bit-identité, jamais re-figé).
- Suites vertes : `test_golden`, `test_scatter_lumiere_recue` (neuf),
  `test_scatter_lumiere_sol`, `test_lod_ombre`, `test_ombre_maison`.
- Refactor auto-léger **no-op** : `light.py` 242 LDC 🟢, `light_index.py` 54 🟢,
  `test_scatter_lumiere_recue.py` 109 🟢 — rien au-dessus de la bande.
- Aucun `.cs` touché → pas de `dotnet build` (noté au kickoff ②).

## Reste F5 = Nico

Sprint 100 % perf, **zéro delta visuel attendu** (scatter bit-identique).
1. **Rendu INCHANGÉ** — F5 sur monde grandi (an ~2, forte pop), confirmer que
   ombres au sol + lumière reçue (couleurs/stades) sont identiques à avant. Toute
   différence visible = bug d'indexation à remonter, NE PAS re-figer.
2. **Relevé perf** — au HUD (F4) à forte population : FPS + tick client + tick
   serveur, comparer à la référence (an 2 : tick serveur ~8 s AVANT).

**Sprint CLOS.** LightField : après D67 (LOD émetteurs, −18 %) et ce sprint
(boucle reçue scatter), les deux boucles lumière sont désormais scatter + LOD.
Hors sprint : dette design **D71** (cap démographique, à rouvrir si le gameplay
le demande — le scatter rend le tick ~linéaire, plus de motif perf).
