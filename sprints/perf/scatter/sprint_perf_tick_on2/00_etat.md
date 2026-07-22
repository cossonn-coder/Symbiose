# Sprint PERF « scatter lumière-reçue » — état

> Conception FIGÉE le 2026-07-09. Prêt pour `/sprint-auto sprint_perf_tick_on2`.
> Doc : `docs/perf/scatter/conception_perf_scatter_recue.md`.
> **Optimisation PURE : golden INCHANGÉ (`24ec11e7…`), bit-identique.**

## Origine
Audit du coût du tick 2026-07-09 (profil `tools/profile_monde.py` / `build_world_full`
grandi → 595 plantes ≈ pic an 2). Décompo : mémoire `perf_profile_simulation`.

## Déjà livré (HORS ce sprint)
- **Quick-win fongique** (`_local_density`/`_spore_load`, BFS hissée en set) —
  commit **`7c5344e`**, golden `24ec11e7` intact, **−13,5 %** mesuré. CLOS.

## Décisions arrêtées (validées Nico)
1. **② = scatter de la boucle lumière-reçue** (miroir de ce que D32 a fait au sol),
   bit-identique en itérant les émetteurs par hauteur décroissante. Retenu vs
   strates de hauteur / cache par cellule (l'approche architecturale, pas paramétrique).
2. **③ cap démographique = SORTI du sprint**, versé en **dette design D71** : ②
   rend le tick ~linéaire → plus de motif perf ; un cap ne se justifierait que
   design/réalisme, à rouvrir seulement si le gameplay le demande.
3. **Tronçon de clôture = validation F5 perf** (mesure tick client, rendu inchangé),
   pas de rendu neuf (sprint 100 % perf, zéro delta visuel).

## Faits établis (vérifiés dans le code)
- Boucle lumière-SOL déjà scatter (D32) ; boucle lumière-REÇUE restée en gather →
  `covering` avec `reach` dimensionné par `max_height` GLOBAL de la tuile = 40 % du tick.
- Trèfle MATURE = émetteur d'ombre (pouvoir 150 > seuil LOD 37,5).
- `light.py` 225 LDC 🟢, `light_index.py` 31 LDC → place pour un `ReceiverIndex`.
- Verrou modèle : `tests/test_scatter_lumiere_sol.py` (équivalence gather==scatter bit-à-bit).

## Carte des tronçons
- **01 — Scatter de la boucle reçue** ✅ CLOS 2026-07-09 : `light_index.py`
  (`ReceiverIndex` + `in_bbox`), `light.py` (boucle reçue récrite en scatter
  émetteur→échantillons, `ObstacleIndex` retiré de la reçue),
  `tests/test_scatter_lumiere_recue.py` (verrou bit-à-bit calqué sur le sol).
  Golden INCHANGÉ `24ec11e7…`. Toutes suites lumière/ombre vertes.
  LDC : light.py 242🟢 / light_index.py 54🟢. → `01_scatter_recue.md`.
- **02 — Validation perf + F5** ✅ CLOS 2026-07-09 : mesure `profile_monde
  --week 104`, non-régression golden + suites lumière/ombre toutes vertes,
  checklist F5 posée. Aucun code moteur touché. → `02_validation_f5.md`.

## Mesure (formelle, tronçon 02 — `profile_monde --week 104 --top 40`)
Monde à la semaine 104 (an 2, hiver) : 8 tuiles, 491 plantes, 8441 segments.

| Repère | ms/tick absolu | `covering` (gather reçue) | boucle lumière |
|---|---|---|---|
| **Avant ②** (audit, 595 plantes) | bloc 4 ticks ≈ 20,5 s cProfile | **40 % du tick**, 1ᵉʳ hors `LightField.compute` | — |
| **Après ①+②** (491 plantes, week 104) | **554 ms/tick** (moyen sur 5 ticks) | **DISPARU du profil** (gather reçue supprimé) | `light.compute` = 0,175 s tottime (rang 4) |

Détail post-② :
- `covering` **absent du top 40** — remplacé par `light_index.py:in_bbox`
  = **0,045 s tottime** (4362 appels, rang ~20), coût marginal.
- `light.compute` (light.py:210) = 0,175 s tottime, redescendu au rang 4 —
  n'est plus le poste dominant. `_point_in_capsule` = 0,090 s.
- Le tick est désormais dominé par des postes diffus (`field.tick`,
  `grids.at_plot`, `sum`/`min`/`max` builtins, uptake) — plus de motif
  quadratique lumière-reçue. Objectif ② atteint : boucle reçue ~linéaire.

> Note : le chiffre absolu ms/tick n'est pas directement comparable à l'audit
> (population et machine distinctes) ; l'invariant mesuré ici est
> **structurel** — `covering` sorti du profil, plus de poste O(N²) reçu.

## Non-régression (tronçon 02)
- `test_golden` → **PASS**, hash **`24ec11e7983595e71c4587fce8f558a1bec9eb5ec8511bf69ad76e9fdc2b6e91`** (INCHANGÉ, bit-identité).
- `test_scatter_lumiere_recue` → PASS (identité bit-à-bit gather==scatter reçue).
- `test_scatter_lumiere_sol` → PASS (D32 soldée, bit-à-bit).
- `test_lod_ombre` → PASS (invariant dormant + LOD actif).
- `test_ombre_maison` → PASS (4 tests verts, déterminisme).

## Sanity build C#
`git diff --name-only` depuis le début du sprint = **100 % Python + dossier
sprint** (`fields/light.py`, `fields/light_index.py`,
`tests/test_scatter_lumiere_recue.py`, `sprints/perf/scatter/sprint_perf_tick_on2/00_etat.md`).
**Aucun `.cs` touché → PAS de `dotnet build` nécessaire.**

## F5 à faire (Nico, sur Windows)
Sprint 100 % perf, zéro delta visuel attendu (scatter bit-identique).
1. **Rendu INCHANGÉ** — F5 sur un monde grandi (an ~2, forte population) et
   confirmer que l'affichage est visuellement identique : ombres au sol,
   lumière reçue par les plantes → couleurs/stades identiques à avant. Toute
   différence visible = bug d'indexation à remonter (NE PAS re-figer le golden).
2. **Relevé perf** — noter au HUD (F4 / rapport terrain) à forte population :
   **FPS + tick client + tick serveur**, et comparer à la référence
   (an 2 : tick serveur **~8 s AVANT**). Consigner le nouveau chiffre serveur
   (gain attendu de la disparition de la boucle reçue O(N²)).

## §REPRISE
**SPRINT CLOS** — tronçons 01 (scatter reçue) et 02 (validation) tous CLOS
le 2026-07-09. Golden **`24ec11e7…` INCHANGÉ** (bit-identité), suites
lumière/ombre + scatter toutes vertes, diff 100 % Python (aucun rebuild C#).
Commits **NON POUSSÉS** — Nico commit/push. Reste **hors sprint** : F5 de
validation (checklist ci-dessus, Nico) ; dette design **D71** (cap
démographique, à rouvrir si le gameplay le demande).
