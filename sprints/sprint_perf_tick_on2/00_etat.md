# Sprint PERF « scatter lumière-reçue » — état

> Conception FIGÉE le 2026-07-09. Prêt pour `/sprint-auto sprint_perf_tick_on2`.
> Doc : `docs/conception/CONCEPTION_PERF_SCATTER_RECUE.md`.
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
- **01 — Scatter de la boucle reçue** : `light_index.py` (`ReceiverIndex`),
  `light.py` (récriture boucle reçue), `tests/test_scatter_lumiere_recue.py` (verrou).
  Golden INCHANGÉ. → `01_scatter_recue.md`.
- **02 — Validation perf + F5** : mesure `profile_monde.py --week 104`,
  non-régression, checklist F5 pour Nico. → `02_validation_f5.md`.

## Mesure (à remplir par les tronçons)
- Avant ② (audit) : bloc 4 ticks à 595 plantes = 20,5 s cProfile ; `covering` = 40 % du tick.
- Après ② : _(tronçon 02 à consigner)_

## §REPRISE
Lancer `/sprint-auto sprint_perf_tick_on2`. Commencer par `01_scatter_recue.md`.
Golden doit rester `24ec11e7…` à CHAQUE tronçon (bit-identité) — s'il bouge, le
scatter a un bug d'indexation, NE PAS re-figer.
