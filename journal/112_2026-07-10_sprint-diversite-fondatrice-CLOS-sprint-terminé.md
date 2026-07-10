# 2026-07-10 — Sprint DIVERSITÉ FONDATRICE (D74, ①→③) — SPRINT TERMINÉ (`/sprint-auto`)

Régler les conditions de départ pour que **chaque plante ait son propre rythme**,
sur deux axes couplés : variance génétique fondatrice + hétérogénéité des champs
de sol. 3 tronçons enchaînés en autonome.

## ① Génétique fondatrice — plus de clones au démarrage (`ee10774`)
Active enfin `GENE_INIT_SIGMA` (défini mais JAMAIS utilisé) : `founder_genes()`
(`fields/seedbank.py`) tire chaque gène ~ N(1.0, σ²) de façon **déterministe**
(canal de hash décorrélé espèce+gène+position CONTINUE `x_cm/y_cm`+semaine →
correctif B, pas de re-clonage intra-plot #3). `seed_founder_pool()` ENSEMENCE la
banque-sol (`SeedBank.species` GeneStat) par plot×WEED_CATALOGUE sous le flag
`heterogene` (option A : le sol porte la diversité latente dès le départ #4).
Féral (`succession`) et levée `planter` sans lignée retombent sur `founder_genes`
si pool vide. `Seed.genes` défaut passé de `neutral_genes()` à `{}` pour
distinguer sachet magazine (→ fondateur) de graine héritée (décision imprévue
tranchée dans le périmètre GENES). Sites monde-réel à `True`+founder
(`test_golden`, `main.py`, `bancs/base.py`). Test neuf `test_diversite_fondatrice`.
**Golden RE-FIGÉ LARGE (GENES, prévu)** `24ec11e7…`→`a63e388c…` ; `population_hash`
re-figé (germination férale non-clonale) →`dd2c1457…` ; déterministes ×2. 52 suites
vertes.

## ② Hétérogénéité fondatrice des champs — catena topographique (`cfc1a60`)
`EcoFields._init_catena()` : chaque plot édaphique = `base·(1 + amplitude·
(poids_topo·topo + (1−poids_topo)·bruit))`, `topo` lu sur l'`altitude` déjà posée
(NPK riches en bas), `bruit` sur canal de hash décorrélé par champ (zéro RNG #3).
Appliqué sous flag `heterogene`, APRÈS l'altitude, sur ph/n/p/k/structure_sol/
microbiome (`humidite`/`om_stable`/`altitude`/`temperature*` exclus). Amplitudes
propres + tables poids/sens topo dans `ecofields/constants.py` (pH petite=0.03,
NPK/microbiome=0.20, structure=0.10). **Golden RE-FIGÉ (ECO, prévu)**
`a63e388c…`→`452b5256…`, déterministe ×2. 51 tests uniformes ciblés INTACTS
(défaut `heterogene=False`). 3 tests catena neufs.

## ③ Vue Godot — banc d'observation + heatmaps + survol gènes (`4721966`)
Banc `diversite_fondatrice` (`bancs/diversite.py`) : 64 tournesols même espèce à
patrimoine fondateur propre sur sol catena → rythmes désynchronisés observables
(`BANC_WEEK_DEPART=9`). Snapshot expose `genes` par plante (pont **0.5.22**).
`FieldOverlay.cs` : palette `altitude` (F6, catena lisible). `WorldView.Genes.cs`
(neuf) : survol gènes debug touche **G** (vigueur/germination_thermique/
phenologie_florale). **Golden INTACT** `452b5256…` (vue seulement). `dotnet build`
VERT. Garde-fou `diag_population` : N=641/an6 (cible invasion [600,700]) — aucun
re-déséquilibrage.

## Clôture
Refactor auto-léger **no-op** (tous fichiers touchés ≤290 LDC pur 🟢). **Golden
final `452b5256…`.** D74 ✅ FAIT. Reste **F5 Nico** : `init config=
"diversite_fondatrice"` → rythmes désynchronisés, heatmaps catena F6
(altitude/NPK), survol gènes touche G ; calibrage `GENE_INIT_SIGMA=0.10`,
`FOUNDER_POOL_DENSITY=0.02`, amplitudes catena (placeholders).
