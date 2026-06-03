# Dette technique consolidée — SYMBIOSE

> **Source unique.** Ce fichier est la référence de la dette technique du projet.
> `journal.md` et `CLAUDE.md` y renvoient au lieu de la dupliquer (fin de la
> triple maintenance, décidé au Sprint refactor structurel, 2026-06-03).

| Code | Description | Priorité |
|---|---|---|
| D1 | Fichiers transitoirement perdus le 2026-05-29 (Nextcloud). Mitigé par init git. | 🔴 → ✅ mitigé |
| D2 | Mismatch dimensions tuiles : 78×57 réel vs 96×48 codé dans `TileGrid.cs` | 🔴 |
| D3 | Mismatch noms sprites : catalogue C# attend `basil_*`, fichiers nommés `basilic_*` | 🔴 |
| D4 | Sprite maison absent — pièce centrale du design 3×3 sans visuel | 🔴 |
| D5 | `effects.py` jamais porté en C# | 🟡 |
| D6 | `engine.py` jamais porté en C# (boucle 52 semaines, succession, aléas) | 🟡 |
| D7 | Stubs vides hors namespace `Symbiose` (Main, EcologySystem, etc.) | 🟡 |
| D8 | `Main.tscn` obsolète (Node vides en français), à supprimer/refaire | 🟡 |
| D9 | Conflit de nom `PlantInstance` (`core/PlantData.cs` data vs `plants/PlantInstance.cs` Node Godot) | 🟡 |
| D10 | Divergence Python ↔ C# : OM tri-compartiment. **OM v4 porté en Python le 2026-06-02 (Sprint sol vivant)** — `om_fresh/active/stable` + cascade. Reste `PathogenPressure` (C# seul) à réconcilier. | 🟢 → ✅ (OM) / 🟡 (pathogène) |
| D11 | Moteur Python à étendre : **Vigueur universelle** (joueur + plantes + auxiliaires + nuisibles), couche transversale à concevoir | 🟡 |
| D12 | Moteur Python à étendre : **paliers de maîtrise** (méta-état du joueur, conditions de passage par famille et concept) | 🟡 |
| D13 | Système **Magazine de botanique** à concevoir (coût Vigueur + maîtrise, déblocage espèces) | 🟡 |
| D14 | Système **Carnet auto** à concevoir (enregistrement événements, indexation, bascule descriptif → interprétatif) | 🟡 |
| D15 | Mécanique d'**extension du terrain par maîtrise** (tuile thématique apparaît au palier maîtrise d'une famille) | 🟢 |
| D16 | Décaler le tirage météo en `forecast` 1-2 semaines en avance dans `engine.py`, pour alimenter les signes diégétiques (Z2). **Conçu le 2026-06-03 (Sprint conception météo)** — `data/code/CONCEPTION_METEO.md`. Pivot : `random.choice` → fonction pure `weather_at(seed, week)` (`_hash_noise`) ⇒ forecast = évaluation en avance, sans tirage décalé à stocker. Champ `temperature` ambiant + gène rusticité induits. **Reste : implémentation** (sprint découpé, re-figer le golden) | 🟢 ✅ (conçu) / 🟡 (impl.) |
| D17 | Séparer `SeedBank-joueur` (lots par espèce, transportable, suit l'avatar) de `SeedBank-sol` (génétique vectorielle par espèce, intrinsèque au terrain), Python puis C# (Z3). **Couplé à D22** dans le Sprint génétique/reproduction. **Traité le 2026-06-03 (Sprint génétique, Python)** — `seeds.py` (`PlayerSeedBank` lots + JSON, ponts récolte→joueur), couche `species` dans `fields.SeedBank` (`add_species`/`sample_genes`/`GeneStat`). Portage C# → D24 | 🟢 ✅ (Python) / 🟡 (C#) |
| D18 | Système de **pages secrètes** à concevoir — sources, lieu de consultation, volume cible v1.0, génération de contenu (Z4) | 🟢 |
| D19 | Action gameplay **« manger »** à concevoir (organes consommables → Vigueur joueur) (Z5) | 🟡 |
| D20 | **Éclairement spatial (Option A)** : ombres-capsules astronomiques ~49°N, 4 saisons × 3 tranches + intégrale, `foliage_density` par espèce, cumul multiplicatif, plancher 15 %, auto-ombrage exclu. **Traité le 2026-06-02 (Sprint éclairement, Python)** — `LightField` v2 **analytique** (sans grille pixel ; la grille 2 cm/px reste pour le rendu Godot). Position continue côté lumière. Portage C# → D24 | 🟢 ✅ (Python) |
| D21 | **Pérennes ligneuses** : base polymorphe commune aux annuelles, `age_years`, courbe d'âge interpolée, `foliage_density` saisonnière (caduc nu l'hiver). **Traité le 2026-06-02 (Sprint éclairement, Python)** — `perennials.py`, 5 arbres (figuier/pommier jardin, cerisier intermédiaire, noyer/chêne lisière). Portage C# → D24 | 🟢 ✅ (Python) |
| D22 | **Héritage génétique de la graine** : vecteur de gènes extensible, héritage biparental (pollinisation par espèce, modulée par auxiliaires), hybridation par introgression sur espèce fixe. **Sprint génétique/reproduction**, couplé à D17 (Z7). **Traité le 2026-06-03 (Sprint génétique, Python)** — `reproduction.py` (appariement biparental déterministe, moyenne+mutation, autoféc., introgression intra-famille), `GENE_NAMES`/`clamp_gene` dans `plants/genetics.py`, `genetic_factor` réel branché dans `height_at`. Portage C# → D24 | 🟢 ✅ (Python) / 🟡 (C#) |
| D23 | **Catalogue arbres pérennes étendu** : poirier, prunier, châtaignier, frêne, tilleul, bouleau, saule, aulne, peuplier, érable… — différé post-validation squelette (Z7) | 🟢 |
| D24 | **Portage C# de la logique sol vivant** : uptake spatial sur `root_plots`, exsudats (`_apply_exudates`), bonus microbiome→uptake, `vitalite()` dérivée — codés en Python le 2026-06-02, pas encore en C#. **+ gradient de succession** (`choisir_archetype`, `tick_late_succession_enrichment`, 2026-06-02). **+ système d'éclairement** (`LightField` v2 analytique, interface lumière polymorphe, `perennials.py`, hauteurs/rayons/`foliage_density` sur `PlantData`, 2026-06-02). **+ génétique/reproduction** (`seeds.py`, `reproduction.py`, couche `species`+`GeneStat` de `SeedBank`, `genes`/`gene()` sur l'instance, pollinisation, 2026-06-03). À absorber dans le **Sprint 3 (portage)** | 🟡 |
| D25 | **Succession écologique pionnier → prairie** : choix d'archétype ∝ maturité (`soil_memory_deep`) + amorçage de la banque en propagules vivaces. **Traité le 2026-06-02 (mini-sprint succession)** — couvert installé bascule pionnier → prairie vivace (~80 %) sur ~30 ans, stable 500 ans. Portage C# reporté (→ D24) | 🟢 ✅ |
| D26 | **Sprint diversification écologique** : catalogue de test très incomplet (5 familles, 4 archétypes). Étendre les espèces. À séquencer **après** Sprint éclairement (D21 = strates/ligneux, nouveaux archétypes) et une décision *class-based vs data-driven*, en coordination avec la génétique (D22). Étendre `SOIL_SIGNATURE` pour les nouvelles familles | 🟢 |
| D27 | **Mortalité réaliste (sénescence)** : santé dynamique (chute + récupération, plancher `background_mortality` levé), sénescence par âge (`longevity_years`, onset 70 %), fonte des semis, maladies fongiques (susceptibilité familiale), ravageurs **régulés par prédateurs émergents** (biodiversité + fleurs + stabilité), renouvellement, nécromasse ∝ hauteur, résistance des sujets établis. **Implémenté en Python le 2026-06-02** (passe 1 M1–M3 + passe 2 M4–M7) — 500 ans stables, santé dynamique, arbres meurent de sénescence. Renouvellement **provisoire** (`_renewal`/M7) **remplacé le 2026-06-03 par `_reproduction`** (Sprint génétique, D17+D22) ; champ auxiliaire dédié = sprint futur. **Reste : portage C#** (→ D24) | 🟢 ✅ (Python) / 🟡 (C#) |
| D28 | **Refactor structurel** : `data/code/` réorganisé en paquets (`plants/ world/ fields/ sim/` + `constants.py`), succession extraite vers `sim/succession.py`, golden output déterministe (`tests/test_golden.py`). **Fait le 2026-06-03** — comportement strictement inchangé (golden identique). N'affecte pas le portage C# (D24). | ✅ |
