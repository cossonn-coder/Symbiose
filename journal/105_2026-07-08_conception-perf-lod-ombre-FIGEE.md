# 2026-07-08 — CONCEPTION : LOD des émetteurs d'ombre (D67) — FIGÉE

Reprise de la **perf pure** annoncée à la clôture de D69. `/conception D67`.

## Contexte
Le `LightField.compute` (`fields/light.py`) pèse ~½ du tick à l'an 6 (table
`tools/profile_monde.py`, livré au bras PERF). D66② a coupé « combien
d'obstacles je VISITE par échantillon » (spatial hash, bit-identique). D67 coupe
« combien d'obstacles EXISTENT » — approximation de modèle, donc **pas
bit-identique** → golden re-figé maîtrisé.

## Vérification de vérité (lecture code)
- `infos` sert À LA FOIS de récepteurs et d'émetteurs dans `compute` → D67 les
  découple.
- Émetteurs réels = plantes vivantes + squelettes debout. **La maison est hors
  `infos`** (chemin `_point_in_swept_rect` séparé) → toujours émettrice, jamais
  LOD ; bacs/piles/abris n'ombrent pas. « Structures fixes toujours émettrices »
  est donc vrai gratuitement.
- **Dé-risque majeur** (`perturbations.py:246`) : les férales sont SCIAPHILES →
  la vis B (self-thinning, seule chose côté lumière REÇUE touchée) mord peu sur
  elles ; le plateau N vient surtout de la vis A (couverture→germination),
  INDÉPENDANTE du LightField. La lumière-SOL (germination, clonal) est la surface
  la plus exposée.

## Arbitrages Nico (D1-D7)
- Métrique `pouvoir = hauteur × canopy_radius × foliage_density` (géométrie déjà
  dans `infos`, zéro état neuf, déterministe) ; seuil global `SHADING_POWER_MIN`.
- Découplage receivers (toutes vivantes, réception inchangée) / emitters (≥ seuil).
- **Invariant seuil=0 ⇒ golden bit-identique** (mode dormant = filet).
- LOD sur **les DEUX boucles** (reçue + sol).
- Tolérance N **souple ±15 %** (~613/an6, D69 ; ne PAS rouvrir D69 sauf
  dépassement franc).
- Bras fidélité `tools/diag_lod_ombre.py`, **5 critères** : trajectoire N, dérive
  `light_received`, morts vis B, ms/tick net, **coût perf de la germination
  surnuméraire** (ms/tick net au nouvel équilibre — le 5e ajouté par Nico :
  éclaircir le sol → plus de germination → plus de N → une part du gain se mange).

## Découpage figé (3 tronçons, perf-first, vue en dernier)
① bras fidélité + découplage dormant [golden INTACT + test invariant] → ②
calibrage + activation [golden RE-FIGÉ maîtrisé annoncé + `population_hash`] → ③
vue Godot (overlay F4 perf + toggle debug émetteurs/récepteurs, protocole 0.5.21)
[INTACT].

Livrables : `docs/conception/CONCEPTION_PERF_LOD_OMBRE.md` +
`sprints/sprint_perf_lod_ombre/` (00_etat + kickoffs 01-03). Dette D67 → 🟠 conçu.
**PRÊT pour `/sprint-auto sprint_perf_lod_ombre`.**
