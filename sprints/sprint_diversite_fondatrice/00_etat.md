# Sprint DIVERSITÉ FONDATRICE — état vivant

> Carnet de bord `/conception` (§0bis). Reprise à froid = lire `CLAUDE.md` +
> ce fichier. **Phase : conception ARBITRÉE (revue A-E intégrée) — attente OK
> final pour figer (phase B).**

## Revue critique A-E (tranchée avec Nico, option la + alignée aux philos)
- **A — Ensemencer la banque-sol fondatrice (retenu).** Au lieu de tirer
  `founder_genes` à chaque naissance, on ENSEMENCE la banque-sol (`SeedBank.species`
  GeneStat) au démarrage des tuiles avec une distribution fondatrice (`mean=1.0`,
  `var=GENE_INIT_SIGMA²`, `weight=densité fondatrice > SPECIES_POOL_MIN_DENSITY`),
  pour les espèces d'adventices (WEED_CATALOGUE). Argument philo #4 : une vraie
  banque de graines du sol n'est JAMAIS génétiquement uniforme → le sol porte la
  diversité latente dès le départ ; `sample_genes` tire alors avec variance
  immédiate ; la sélection (`_germ_gene_mean`) a de quoi mordre sans attendre N
  générations. `founder_genes` ne sert PLUS que pour les SEMIS DIRECTS (hors banque :
  8 cultivées démo, graine `planter` sans lignée).
- **B — Correctif déterminisme (retenu).** Le hash de `founder_genes` doit
  discriminer les plantes partageant un plot (compétition intra-plot, positions
  continues) : canal = f(seed, hash_espèce, r, c, **week**, **x_cm/y_cm**, index
  gène) → pas de re-clonage (philo #3).
- **C — Catena topographique (option structurée retenue).** Les NOUVEAUX champs
  édaphiques (`n`, `p`, `k`, `ph`, `structure_sol`, `microbiome`) sont corrélés à
  l'`altitude` déjà posée : facteur = part corrélée-topo (± selon le champ : NPK
  riches en bas) + part bruit propre décorrélé, amplitude PROPRE par champ. Paysage
  LISIBLE (#5/#6, le joueur voit le gradient). **Surgical** : `om_stable`/`altitude`
  NON retouchés (D56 calibré — ré-harmoniser dans la catena = dette légère notée).
  **`humidite` EXCLUE de l'init** (le ruissellement la creuse déjà depuis l'altitude
  → hétérogénéité redondante). Réordonner `init_eco` : altitude AVANT les édaphiques.
- **D — Garde-fous calibrage (inscrits kickoffs).** Amplitudes pH/NPK PETITES
  (portes dures `bell`, faim d'azote, mort carence D41 → hors-fenêtre si trop fort).
  **Re-passer `diag_population`** au tronçon vue (le sprint invasion a calibré des
  plateaux → risque de re-déséquilibrage).
- **E — Division du travail (à écrire dans le doc).** Rythme VISIBLE ← surtout
  hétérogénéité des CHAMPS (plasticité au milieu) ; GÉNÉTIQUE = part HÉRITABLE /
  sélectionnable. Les deux se combinent → enrichit le substrat de TOUS les acteurs
  (floraison désynchro → pollinisateurs continus ; mosaïque édaphique → faune variée).
- **Flag unifié** : un seul flag (`heterogene`, défaut False) sur `init_eco` active
  À LA FOIS l'ensemencement génétique fondateur (A) ET l'hétérogénéité des champs (C).
  Posé `True` par les sites monde-réel (harnais golden, main.py, sim_server, bancs
  d'observation). Tests unitaires ciblés → défaut False → INTACTS.

## Sujet (demande Nico)
Régler les conditions de départ de la simu : (1) que chaque plante n'ait PAS
exactement le même patrimoine génétique et qu'il mute à chaque génération, pour
compléter la sélection naturelle (**comportement émergent visé : chaque plante a
son propre rythme**) ; (2) que **les CHAMPS écologiques soient initialisés
hétérogènes** dès le départ (terrain varié, philo #7), pas seulement l'humus.

## Diagnostic (code lu, source de vérité `data/code/`)
Le moteur génétique est déjà à ~90 % en place :
- Vecteur 10 gènes (`plants/genetics.py:GENE_NAMES`), dont `vigueur`,
  `germination_thermique`, `phenologie_florale` = le « rythme ».
- **Mutation par génération** : `sim/reproduction.py:child_genes` (gaussienne
  `MUTATION_SIGMA=0.05`, déterministe par hash). ✅
- Héritage biparental + autofécondation + introgression. ✅
- **Sélection darwinienne émergente déjà câblée** (germ. thermique, désynchro
  florale) : le pool-sol dérive sans code de sélection dédié. ✅

**Le manque, cœur de la demande** : la **variance FONDATRICE = 0**.
- `GENE_INIT_SIGMA = 0.10` défini (`genetics.py:72`) mais **JAMAIS utilisé**.
- Toute plante née **sans lignée** reçoit `genes = {}` → tous gènes 1.0 →
  **clones parfaits**. Concerne : semis directs `add_plant` (démo + golden), et
  germinations férales tant que la banque-sol est vide (`sample_genes` renvoie
  `{}`). La diversité n'apparaît qu'après plusieurs générations de mutation.
- → Il manque le **tirage fondateur** : à la naissance sans lignée, tirer chaque
  gène ~ N(1.0, GENE_INIT_SIGMA), **déterministe** (hash seed+espèce+position,
  philo #3). La mutation existante prend ensuite le relais.

## Décisions arrêtées (arbitrées avec Nico)
- **Portée = variance génétique fondatrice SEULE.** On ne touche NI la
  composition du peuplement NI le placement spatial (déjà hétérogènes, bruit,
  philo #7). Chaque plante fondatrice = un tirage propre.
- **Golden : re-figeage LARGE assumé, une seule fois, annoncé.** Introduire la
  variance change le golden partout (semis directs + germinations férales ne sont
  plus clonales). Conforme CLAUDE.md (re-figeage maîtrisé). Le comportement réel
  reste ainsi couvert par le smoke test.
- **σ fondateur = GENE_INIT_SIGMA = 0.10** (point de départ, calibrage F5 Nico).
- **Couche** : `founder_genes` doit vivre en couche `fields` (a besoin de
  `hash_gauss` de `fields/noise` + `GENE_*`/`clamp_gene` de `plants/genetics`) →
  rangée dans `fields/seedbank.py`, sœur de `sample_genes`. `genetics.py` reste
  fondation pure (ne peut pas importer `hash_gauss`).
- **Câblage** : `sample_genes` retombe sur `founder_genes` quand le pool est vide
  (couvre férale + spontanée). Semis directs (bancs `main.py`/`test_golden` +
  futur seeding réel) naturalisés via `founder_genes`. Graine joueur `planter`
  sans gènes hérités → founder au dépôt/levée. Les DEUX canaux golden dans le
  MÊME tronçon → un seul re-figeage.
- **Déterminisme** : canal de hash décorrélé par index de gène ET par espèce
  (hash du nom de classe) → 2 espèces au même plot diffèrent, 2 plots diffèrent.
- **Perf** : négligeable (tirage à la naissance, événement rare, pas de boucle
  par tick). Aucun O(N²).

## Décisions arrêtées — AXE CHAMPS (arbitrées avec Nico)
- **Périmètre = tout champ de SOL STATIQUE non nul** : `ph`, `n`, `p`, `k`,
  `structure_sol`, `microbiome`, `humidite`. (`om_stable`/`altitude` déjà
  hétérogènes ; `epaisseur_sol` dérivée.)
- **Exclusion justifiée** : `temperature`/`temperature_sol` (non nuls mais
  CLIMATIQUES, ré-écrits chaque tick par la météo → hétérogénéité fondatrice
  effacée au tick 0) ; champs à 0 au repos (dynamiques, construisent leur propre
  hétérogénéité) ; `lumiere` (recalculée).
- **Amplitude PROPRE par champ** (constantes dédiées dans `ecofields/constants.py` :
  `PH_INIT_AMPLITUDE`, `NPK_INIT_AMPLITUDE`, `STRUCTURE_INIT_AMPLITUDE`,
  `MICROBIOME_INIT_AMPLITUDE`, `HUMIDITE_INIT_AMPLITUDE`) — valeurs de départ
  modestes, calibrage F5. pH varie peu, NPK plus.
- **Canal de hash DÉCORRÉLÉ par champ** (`stable_str_hash(tile_id+"_ph")`, `+"_n"`…,
  comme `altitude` fait déjà `+"_alt"`) → pas de corrélation « plot riche partout »,
  déterministe (philo #3).
- **Flag `heterogene=False` par défaut** sur `init_eco` ; posé à `True` UNIQUEMENT
  par les sites monde-réel : harnais `test_golden`, `main.py`, `sim_server` (pont
  jeu réel), bancs d'observation. → les tests unitaires ciblés qui forcent un champ
  plot-à-plot (test_eau, mycelium, substrat, stress_chronique…) restent INTACTS
  sans être touchés ; seul le golden re-fige. Généraliser `_init_heterogene(grid,
  plancher, amplitude=INIT_AMPLITUDE, canal_suffixe="")` (rétro-compatible om_stable).
- **Golden re-figé** (ligne `ECO` dérive, déterministe) — tronçon dédié ②.

## Découpage proposé (3 tronçons — sprint PETIT/MOYEN, briques déjà là)
- **① Moteur — variance génétique fondatrice, tous canaux de naissance.**
  `founder_genes` (fields/seedbank) + fallback `sample_genes` (férale/spontanée) +
  naturalisation des semis directs (main.py, test_golden) + graine joueur `planter`
  sans lignée. **Golden re-figé LARGE (GENES, annoncé).** Màj tests ciblés supposant
  des gènes neutres. Tests neufs : déterminisme + diversité inter-position.
- **② Moteur — hétérogénéité fondatrice des champs de sol.** `_init_heterogene`
  généralisé + flag `heterogene` sur `init_eco` + amplitudes propres + canaux
  décorrélés, sur ph/n/p/k/structure_sol/microbiome/humidite. Sites monde-réel
  passent `heterogene=True`. **Golden re-figé (ECO, annoncé).** Tests ciblés
  uniformes INTACTS (défaut False). Tests neufs : hétérogénéité déterministe +
  décorrélation inter-champs + uniformité préservée quand `heterogene=False`.
- **③ Vue Godot — banc d'observation.** Banc F5 : lot de même espèce côte à côte →
  VOIR les rythmes propres (tailles/stades/floraison désynchronisés, déjà rendus
  par PlantRenderer) ; heatmaps `FieldOverlay` (F6) montrant l'hétérogénéité
  fondatrice des champs ; debug survol affichant les gènes de la plante pointée.
  Golden intact. Rattacher toute dette de vue pertinente.

## Questions ouvertes
- (aucune) — conception FIGÉE, kickoffs écrits.

## Carte des tronçons (sprint figé — prêt /sprint-auto)
- **① `01_genetique_fondatrice.md`** — `founder_genes` + `seed_founder_pool` (banque
  ensemencée) + naturalisation semis directs + graine `planter` sans lignée + flag
  `heterogene` introduit. **Golden re-figé LARGE (GENES, annoncé).** Tests neufs.
- **② `02_champs_catena.md`** — `init_eco` réordonné (altitude AVANT édaphiques) +
  primitive `_init_catena` + amplitudes propres + sens topo. **Golden re-figé (ECO,
  annoncé).** Tests ciblés uniformes INTACTS (défaut False). Tests neufs.
- **③ `03_vue_godot.md`** — banc F5 `diversite_fondatrice` (rythmes désynchronisés) +
  heatmaps catena `FieldOverlay` (F6) + survol gènes debug + re-passage
  `diag_population` (garde-fou). **Golden INTACT.** Dernier tronçon = clôture sprint.

## §REPRISE
Conception FIGÉE le 2026-07-10 (phase B). Livrables écrits :
`docs/conception/CONCEPTION_DIVERSITE_FONDATRICE.md` + `01/02/03_*.md`. Reste
(phase C, en cours) : màj DETTE.md/BACKLOG.md/journal.md + commit. **Ne RIEN
implémenter dans `data/code/`** (métier de /sprint-auto). Exécution à froid :
lire `CLAUDE.md` + ce fichier + le kickoff `0N` du tronçon, dans l'ordre ①→②→③,
`/clear` entre chaque. Message à Nico après commit : `/sprint-auto
sprint_diversite_fondatrice`.
