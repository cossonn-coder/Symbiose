# Sprint PERF — LOD des émetteurs d'ombre (D67) — état vivant

> Carnet de bord `/conception` (§0bis). Reconstructible à froid : lire `CLAUDE.md`
> + ce fichier. Mis à jour à CHAQUE décision arrêtée. PAS encore figé (phase A).

## Sujet
D67 : couper « combien d'obstacles EXISTENT » dans les 2 boucles de
`fields/light.py:compute` (lumière reçue + scatter lumière-sol) par un **LOD
asymétrique** — sous un seuil de *pouvoir ombrageant*, une plante REÇOIT
toujours la lumière mais n'ÉMET plus d'ombre. Complémentaire de D66② (spatial
hash, qui a coupé « combien j'en visite par échantillon », bit-identique).
D67 est une **approximation de modèle → PAS bit-identique → golden re-figé**.

## Phase courante
Phase B (figeage) — 3 arbitrages tranchés par Nico, je finis seul (conception
autonome + carte blanche). Reste : doc `CONCEPTION_PERF_LOD_OMBRE.md` + kickoffs.

## Constats de vérification (lecture code, 2026-07-08)
- **`infos` = récepteurs ET émetteurs** confondus dans `light.py:compute`
  (l.207-219). La boucle reçue itère `infos` comme récepteurs ; l'`ObstacleIndex`
  + le scatter itèrent `infos` comme émetteurs. → D67 doit **découpler** :
  `receivers` = toutes vivantes ; `emitters` = sous-ensemble ≥ seuil.
- **Émetteurs réels** = plantes vivantes + squelettes debout (`stade_mort=="seche"`,
  densité `SILHOUETTE_SECHE=0.30`). La **maison** est hors `infos` (chemin
  `_point_in_swept_rect` séparé) → déjà toujours émettrice, jamais LOD. Bacs/piles/
  abris n'ombrent pas. ⇒ « structures fixes toujours émettrices » = vrai gratuitement.
- **Lecteurs lumière REÇUE** (`light_received`) : croissance (`croissance.py` ×3,
  `phases.py:181`), convalescence (`mortalite.py:107`), **self-thinning vis B**
  (`shade_stress_damage`, `perturbations.py:253`).
- **Lecteurs lumière-SOL** (`lumiere.at_plot`) : germination (`succession.py:124,288`),
  clonal (`clonal.py:104`), mortalité (`mortalite.py:206`), uptake, thermique. →
  surface fidélité plus large.
- **DÉ-RISQUE MAJEUR** (`perturbations.py:246`) : les férales sont SCIAPHILES
  (base 1.25) → vis B mord PEU sur elles ; le plafonnement N vient surtout de la
  **vis A** (couverture→germination, `couverture.py`), **INDÉPENDANTE du LightField**.
  ⇒ risque de D67 sur le plateau N (récemment fixé ~613/an6 par D69) réellement FAIBLE,
  mais à MESURER (surtout côté lumière-sol → germination).
- **Bras PERF déjà livré** : `tools/profile_monde.py` (config=full, --week N,
  ms/tick absolu + table cProfile). Reste à concevoir le **bras FIDÉLITÉ**.

## Décisions arrêtées (Nico, 2026-07-08)
- **D1 — Métrique de pouvoir ombrageant** : `pouvoir = current_height ×
  canopy_radius_at × foliage_density_at` (les 3 grandeurs déjà dans `infos`, zéro
  état neuf, déterministe). Nulle pour un caduc défeuillé (densité 0 → non-émetteur,
  cohérent). Seuil global unique `SHADING_POWER_MIN` (constante `light.py`).
- **D2 — Découplage** : `compute` sépare `receivers` (toutes vivantes, réception
  inchangée) et `emitters` (pouvoir ≥ seuil). `ObstacleIndex` + scatter itèrent
  `emitters` ; la boucle reçue itère `receivers`. Squelettes debout suivent la
  même règle de seuil. Maison hors `infos` = toujours émettrice (inchangé).
- **D3 — Invariant seuil=0** : `SHADING_POWER_MIN = 0.0` ⇒ `emitters == receivers`
  dans l'ORDRE EXACT de `infos` ⇒ comportement bit-identique à l'actuel ⇒ **golden
  INTACT** (`33c0ea6f…`). Verrou = test dédié. C'est le mode « LOD dormant ».
- **D4 — Portée** : LOD sur les DEUX boucles (reçue + sol). Nico.
- **D5 — Tolérance N** : bande souple ~±15 % autour de ~613/an6 (D69). On MESURE,
  on consigne, on ne rouvre PAS le calibrage D69 sauf dépassement franc. Nico.
- **D6 — Bras fidélité (5 critères)** : `tools/diag_lod_ombre.py` compare LOD
  off (seuil 0) vs on (seuil calibré), même seed, config=full an 0→6 :
  (a) trajectoire N (onset+plateau) ; (b) dérive `light_received` moy/max par
  plante ; (c) morts vis B (`carence lumineuse`) ; (d) ms/tick an 6 ; (e) **coût
  perf de la germination surnuméraire** = ms/tick mesuré à chaque équilibre PROPRE
  (net, pas à N figé) + comptage germination/saison. Nico (5e critère ajouté).
- **D7 — Calibrage** : `SHADING_POWER_MIN` choisi dans la zone « ombre coupée
  individuellement négligeable » tenant N dans la bande D5. Golden RE-FIGÉ maîtrisé
  annoncé au tronçon ② (+ digest `population_hash`, même cause).

## Arbitrages (lot 1) — TRANCHÉS
1. Dérive N → **souple + mesuré** (bande ~±15 %) — cf. D5.
2. Portée LOD → **les deux boucles** — cf. D4.
3. Bras fidélité → **5 critères** dont coût perf germination surnuméraire — cf. D6.

## Découpage figé (3 tronçons, perf-first, vue en dernier)
- **① Bras fidélité + découplage dormant** : `tools/diag_lod_ombre.py` (5 critères)
  + refactor `compute` receivers/emitters gaté par `SHADING_POWER_MIN` (défaut
  **0.0** = dormant). Test invariant D3 (seuil 0 ⇒ golden bit-identique). Golden INTACT.
- **② Calibrage + activation** : lancer le banc, choisir `SHADING_POWER_MIN` tenant
  N dans la bande D5, le mettre par défaut. Golden RE-FIGÉ maîtrisé annoncé
  (+ `population_hash`). Consigner gain net + dérive.
- **③ Vue Godot** : overlay F4 perf reflète le gain + toggle debug « émetteurs
  vs récepteurs » (teinte des plantes sous-seuil), snapshot `emitteur` par plante,
  bump protocole mineur. Golden INTACT. Points F5 Nico.

## Donnée terrain (F5 Nico, 2026-07-08) → `_rapport_terrain_20260708.md`
Mesure in-game archivée avant lancement. 2 signaux :
- **Cible D67 confirmée** : ~480/522 plantes = semis sous-seuil (Clover×220,
  PoaAnnua×67, BursaPastoris×76…) ; grosses canopées concentrées tuiles S/NO.
- **Pic ≠ géométrie** : pires ticks fin an 1 (s48-s52, jusqu'à 6240 ms) à PEU de
  segments (1224) ; an 2 plus rapide (2540 ms) à 4× plus de segments (4974). ⇒
  pic saisonnier probable germination/repro fin d'été, pas ombre. **Au ②** :
  calibrer en visant AUSSI s48-s52 dans `diag_lod_ombre.py` (D6 critères c+e,
  risque : LOD ↑ lumière-sol ↑ germination). Conception INCHANGÉE (D5/D6 couvrent).

## Coût perf estimé
Gain attendu sur les 2 boucles géométriques (~½ du tick à l'an 6, cf. table
profile_monde). N dominé par des SEMIS (Clover×85, PoaAnnua×65…) = émetteurs
sous-seuil → couper leur ombre = couper le gros du volume d'obstacles. Gain net
à chiffrer par le bras perf avec/sans LOD.

## Avancement (exécution `/sprint-auto`)
- **① Bras fidélité + découplage dormant — FAIT (2026-07-08).** Golden **INTACT**
  `33c0ea6f…`. Livré :
  - `fields/light.py` : constante `SHADING_POWER_MIN = 0.0` (dormant) + découplage
    `receivers` (toutes vivantes, réception inchangée) / `emitters` (pouvoir
    `h×rayon×densité ≥ seuil`) dans `compute` — boucle reçue itère `receivers`,
    `order`/`ObstacleIndex` + scatter sol itèrent `emitters`, cache géom laissé sur
    `infos`. Invariant D3 respecté (seuil 0 ⇒ bit-identique).
  - `tools/diag_lod_ombre.py` : banc fidélité 5 critères (trajectoire N + bande D5,
    dérive `light_received` à monde figé, coups vis B carence lumineuse, gain ms/tick,
    nouvelles plantes/saison). Sanity `--seuil 0` : off≡on (dérive 0.000 %, N Δ=0).
  - `tests/test_lod_ombre.py` : invariant dormant (0.0 ≡ 1e-9 bit-à-bit) + mécanisme
    actif GLOBAL (seuil élevé ⇒ emitters<receivers ⇒ reçue↑ ET sol↑ sur la scène).
    Note : l'assertion « reçue↑ » est agrégée sur la scène (sur une tuile donnée,
    3 semis coupés peuvent n'ombrer que le sol).
  - Suites ombre/lumière vertes (ombre_maison, phototropisme, scatter).
- **② Calibrage + activation — FAIT (2026-07-08).** `SHADING_POWER_MIN = 37.5`
  activé dans `fields/light.py`. Golden **RE-FIGÉ maîtrisé** `24ec11e7…`
  (ex-`33c0ea6f…`, dérive localisée = ombres des semis sous-seuil retirées).
  - **Calibrage piloté par `diag_lod_ombre`** (script batch jetable /tmp, grandit OFF
    une fois + balaye 4 seuils an 6). Distribution du pouvoir à l'an 6 : falaise nette
    p80=37.4 (semis, ~80 % des plantes) → p90=262 (structurantes). 37.5 = plus grand
    seuil coupant TOUT le cluster de semis sans mordre sur les structurantes.
  - **Mesures @ S=37.5** : N plateau off 587 → **on 689** (bande D5 [521, 704] → DANS) ;
    gain **+17.9 % ms/tick** (567 → ~465 ms net à l'équilibre propre) ; dérive
    `light_received` **moy 0.68 %** (négligeable), max 131 % = 1 seule plante de
    sous-étage sensible (dérive localisée) ; vis B préservée (139 vs 112 off, non
    effondrée). S=299 écarté (+6 % de gain mais ×3 dérive + vis B ÷2 → mord les
    structurantes).
  - **`population_hash` INCHANGÉ** (`1aa4997d…`) : le scénario du test population
    n'exerce pas la dérive LOD → contrairement à l'anticipation du kickoff, RIEN à
    re-figer côté population. Golden = seul hash bougé.
  - Suites lumière vertes (golden, lod_ombre, ombre_maison, phototropisme, scatter).
- **③ Vue Godot — À FAIRE** (kickoff `03_*.md`).

## §REPRISE
Lire `CLAUDE.md` + ce fichier. Décisions D1-D7 arrêtées, découpage figé (3 tronçons).
Tronçons ① et ② CLOS. Golden actif = **`24ec11e7…`** (LOD `SHADING_POWER_MIN=37.5`),
population `1aa4997d…` inchangé. **Reprendre au tronçon ③** (vue Godot) : snapshot
`emitteur` par plante (`serialize.py`), bump `ENGINE_VERSION` 0.5.21, lecture C# +
toggle debug teinte des non-émettrices (`WorldView.Snapshot/Controls`, `PlantRenderer`),
golden INTACT, `dotnet build` vert. Puis clôture : DETTE D67 → implémenté + BACKLOG +
journal + refactor auto-léger.
