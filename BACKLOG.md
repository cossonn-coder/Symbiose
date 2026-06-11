# Backlog — SYMBIOSE

> **Source unique.** Ce fichier est la référence du backlog des sprints.
> `journal.md` et `CLAUDE.md` y renvoient au lieu de le dupliquer (décidé au
> Sprint refactor structurel, 2026-06-03).
>
> Chaque sprint à venir possède un **kickoff autosuffisant** dans le dossier
> `sprints/`. À l'ouverture d'une nouvelle session, donner à Claude
> l'instruction « lis `sprints/sprint_X.md` » suffit à reprendre sans le
> contexte de la session précédente.

| Sprint | Fichier kickoff |
|---|---|
| Sprint 1 (recalibrage visuel) | `sprints/sprint_1_recalibrage_visuel.md` |
| Sprint 2 (orchestration C#) | `sprints/sprint_2_orchestration.md` |
| Sprint éclairement (Z7, D20-D21 : ombres pixel + pérennes + réalignement OM) — ✅ **TERMINÉ 2026-06-02 (Python)** | `sprints/sprint_eclairement.md` |
| Sprint génétique/reproduction (Z7, D17+D22 : banques + héritage biparental) — ✅ **TERMINÉ 2026-06-03 (Python)** | `sprints/sprint_genetique.md` |
| Sprint refactor structurel (réorg `data/code/` en paquets + archive journal + dette/backlog source unique + golden output) — ✅ **TERMINÉ 2026-06-03** | `sprints/sprint_refactor_structurel.md` |
| Sprint conception météo (conception seule : météo/climat + signes diégétiques, D16+Z2) — ✅ **TERMINÉ 2026-06-03** → spec `data/code/CONCEPTION_METEO.md` | `sprints/sprint_conception_meteo.md` |
| Sprint conception Vigueur (conception seule : Vigueur universelle + coûts d'action, D11) — ✅ **TERMINÉ 2026-06-04** → spec `data/code/CONCEPTION_VIGUEUR.md` | — |
| Sprint implémentation météo (porter `CONCEPTION_METEO.md` en Python : `weather_at`/forecast, `temperature`, gène rusticité, signes) — ✅ **TERMINÉ 2026-06-04** (4 sous-sprints, golden `63bfdac4…`) | `sprints/sprint_meteo_impl/00_etat.md` |
| Sprint implémentation Vigueur (porter `CONCEPTION_VIGUEUR.md` en Python : couche joueur + coûts d'action + façade plante + manger, D11) — ✅ **TERMINÉ 2026-06-04** (4 sous-sprints, golden joueur 59/59, golden écolo `ee79dd66…` jamais re-figé) | `sprints/sprint_vigueur/00_etat.md` |
| Sprint conception paliers de maîtrise (conception seule, D12) — ✅ **TERMINÉ 2026-06-04** → spec `data/code/CONCEPTION_MAITRISE.md` (squelette : objet de maîtrise générique, 2 mesures globales, `palier_bonus` intact + coût d'action seam séparé). Sous-sprints D12.1–D12.5 ci-dessous | — |
| D12.1 — Succès par axe — ✅ **TERMINÉ 2026-06-04** → `CONCEPTION_MAITRISE.md` **§9**. Pivot : succès = action joueur qui améliore au-delà du cours spontané, observée ; nature de preuve croissante ; palier 5 = conjonction action experte **+** naturalisation férale. Reste : Nᵢ (répétitions/palier) → calibrage D12.4 | — |
| D12.2 — Table palier → déblocage (conception seule : quel palier ouvre magazine D13 / bascule carnet D14 / fait apparaître tuile D15 / enrichit l'encyclopédie ; `CONCEPTION_MAITRISE.md` §8.2). **BLOQUÉ** : D13/D14/D15 doivent être conçus d'abord (la table mappe vers eux). En conversation, pas de kickoff | — |
| D12.3 — Taxonomie des objets de maîtrise — ✅ **TERMINÉ 2026-06-04** → `CONCEPTION_MAITRISE.md` **§10** (passage unique, pas de découpage : conception = 1 fichier). Catalogues **reflétés** (17 espèces / 11 familles ; spillover data-driven actif sur Solanaceae/Fabaceae/Asteraceae/Rosaceae ≥2 esp.) ; concepts → terme global de `cout_action` ; outil/structure/technique **déclarés** non câblés (D29/D30/D31). Livrable central : **table objets-touchés par action** (§10.4) ; décision **outil ≠ technique** (raffine l'exemple §4.2), concepts hors terme 2. Reste : Nᵢ + atténuations → D12.4 | — |
| D12.4 — Calibrage maîtrise (post-test, pas un sprint : `K`, `BASE`, `R`, atténuations de coût, gains ponctuels ; `CONCEPTION_MAITRISE.md` §8.4). Se fait jeu en main | — |
| D12.5 — Portage C# de la maîtrise (D24) — s'absorbe dans le Sprint 3 portage. Non prioritaire (attend conception jugée satisfaisante) | `sprints/sprint_3_portage_simulation.md` |
| **Sprint impl. paliers de maîtrise (D12, Python)** — porter `CONCEPTION_MAITRISE.md` en Python (remplir `palier_bonus` stubbé + seam `cout_action`). Sprint **GROS découpé en 4 tronçons** : **i1** cœur (objet de maîtrise + progression intra-objet, golden intact) — ✅ **FAIT 2026-06-04** (`sim/maitrise.py` + `tests/test_maitrise.py` 18/18, golden écolo inchangés) ; **i2** agrégats (complétude/accumulation/spillover) + ponts Vigueur (`palier_bonus` délégué, gains ponctuels) — ✅ **FAIT 2026-06-04** (maitrise 35/35, vigueur 96/96, golden écolo inchangés ; point ouvert tranché → `palier_bonus(game_state,player)`, gains §4.3 dans `actions.py`, sens Vigueur→Maîtrise) ; **i3** seam `cout_action` + table objets-touchés (§10.4) — ✅ **FAIT 2026-06-04** (`actions.py` : `cout_action`=base×f_globale×f_objets, tables `COUTS`/`OBJETS_TOUCHES`, helpers reverse classe→clé + cible→spillover, 6 gestes branchés, urgence séparée, outils/structures neutres 1.0 ; vigueur 103/103 + section G, maitrise 35/35, golden écolo inchangés) ; **i4** détection de succès branchée (§9) — ✅ **FAIT 2026-06-04 → impl. D12 COMPLÈTE** (nouveau `sim/maitrise_detection.py` : logement (a) appelé par le driver après chaque tick, lit le `log`+état post-tick, `engine` ne l'importe jamais ; fenêtre d'imputation `noter_geste`, tag provenance féral/`marquer_replante`, gate d'observation palier ≥ 1, nature croissante §9.2, concept par cause, pollinisation biparentale, naturalisation férale §9.4(b) ; détection pure maîtrise, `actions.py` inchangé ; `tests/test_maitrise_detection.py` 20/20, maitrise 35/35, vigueur 103/103, golden écolo inchangés ; placeholders fenêtre/seuils → D12.4). Couche joueur **au-dessus du tick** → **golden écolo jamais re-figé** (`c950f06c…`/`b005d9ba…`), comme la Vigueur. Calibrage `K`/`BASE`/`R`/`SPILLOVER_RATE`/atténuations coût/fenêtre/seuils → D12.4 post-test | `sprints/sprint_D12_impl/00_etat.md` + `01_coeur_progression.md` + `03_cout_action.md` (kickoff i3) + `04_detection_succes.md` (kickoff i4) |
| Sprint conception vie macroscopique observable (conception seule, D31) — ✅ **TERMINÉ 2026-06-04** → spec `data/code/CONCEPTION_VIE_MACRO.md`. Modèle hybride : **`PopulationField` générique** × 4 guildes (ravageur/auxiliaire/pollinisateur/vers), dynamique **DANS le tick** (golden re-figé à l'impl. D31.2), sprites échantillonnés déterministes (golden-neutres), façades `vigueur_*` trophiques. Découpe impl. **D31.1** champs+perception (golden intact) → **D31.2** câblage écolo (re-fige) → **D31.3** façades+gestes. Gain signé « manger un individu » → dette D19 | — |
| Sprint impl. vie macroscopique **D31.1** (champs de population + perception, golden intact) — ✅ **TERMINÉ 2026-06-04** → `fields/population.py` (`PopulationField` générique + `TrophicSpec` + 4 instances + `sample_sprites`), `EcoFields.tick_populations` (étape 13b engine), `tests/test_population.py` (golden champ `population_hash.txt`, bornes, cap, positions). Modèle tick **multiplicatif** (capacité × survie). **Golden engine inchangé** `ee79dd66…`. Reste **D31.2** (câblage écolo, re-fige) + **D31.3** (façades+gestes) | — |
| Sprint impl. vie macroscopique **D31.2** (câblage écologique, re-figeage golden assumé) — ✅ **TERMINÉ 2026-06-04** : herbivorie←`ravageur` (`HERBIVORY_GAIN`), terme `predator` supprimé du calcul (commenté ; auxiliaire lu directement seulement pour la bascule létale → anti-double-comptage), `pollinator_reach`←champ `pollinisateur` (interface `eco` threadée), vers de terre câblé en **option sobre** (bioturbation→léger bonus décomposition ; D30 complet différé). **Golden re-figé** `ee79dd66…`→`c950f06c…`, golden de champ `2e6c3075…`→`b005d9ba…`. `test_auxiliaires` contraste préservé, `test_genetique` 20/20, `main.py` OK. Reste **D31.3** (façades+gestes) | `sprints/sprint_D31_2/01_cablage.md` |
| Sprint impl. vie macroscopique **D31.3** (façades `vigueur_*` read-only + gestes joueur) — ✅ **TERMINÉ 2026-06-04** : `sim/vigueur_macro.py` (4 façades pures `densité × qi_local trophique` + `decrire_vigueur_pop`) ; `sim/actions.py` — `favoriser_auxiliaire` (rondelle habitat persistant), `ecraser` **RÉEL** (retire un quantum de `ravageur`, nouvelle signature `+eco,r,c`), `becher` (↓vers + ↓microbiome), `grelinette` **livrée** (jumeau qui préserve, aération→D30). **Golden écolo INTACT** `c950f06c…`/`b005d9ba…` (vérifiés inchangés — event-driven hors tick). Golden joueur `test_vigueur` **59→87/87** (E6 « la pression revient » prouvée). `main.py` OK. **Clôt D31 côté Python** (reste portage C# D24). Gain signé « manger un individu »→D19 ; habitat local + aération grelinette→D30 | `sprints/sprint_D31_3/01_facades_gestes.md` |
| Sprint conception Hormones de croissance (conception seule, D29 : auxine / dominance apicale / réponse à la taille) — ✅ **TERMINÉ 2026-06-04** → spec `data/code/CONCEPTION_HORMONES.md` (volets A–I). Topologie **tranchée scalaire** (le rendu ne peut suivre, pas de moteur végétal procédural) ; **2 scalaires** `dominance_apicale=1.0`/`ramification=0.0` repos NEUTRE → golden intact ; mapping coupe→émergence sur variables existantes ; action `tailler` (apex/branche) dans `actions.py` ; trait `reponse_taille` (défaut `insensible`), démonstrateur **tomate + pommier** ; succès maîtrise = technique §9.5 (futur marqueur `🌿`). Placeholders → calibrage post-test | `sprints/sprint_hormones.md` |
| ~~**Sprint impl. Hormones (D29, Python)** — 2 scalaires + cinétique + `tailler` + démonstrateur, golden préservé~~ ⚠️ **SUPERSEDED 2026-06-05** : modèle scalaire abandonné, découpage `sprints/sprint_D29_impl/` archivé. Absorbé dans le **Sprint impl. Croissance procédurale** (tronçon 3) ci-dessous | `sprints/sprint_D29_impl/00_etat.md` (archivé) |
| Sprint conception Croissance procédurale (conception seule, D29 réorienté : auxine structurelle + rendu pixel procédural + morphogénèse) — ✅ **TERMINÉ 2026-06-05** → spec `data/code/CONCEPTION_CROISSANCE.md` (A–M). Pivot : **structure de segments** en Python (remplace les 2 scalaires), **moteur permanent**, **auxine le long de la structure**, **phototropisme** (`LightField`), **empreinte dérivée** (contrat `height_at`… inchangé → golden re-figé localisé), **organes tout procéduraux**, racines rayon dérivé. **Profil de croissance PAR ESPÈCE** (vitesse + `port_archetype`) à décrire pour les 14 espèces, calibré sur `growth_stages`/`age_curve`. Absorbe `CONCEPTION_HORMONES.md` | `sprints/sprint_hormones.md` + audit session 2026-06-05 |
| **Sprint impl. Croissance procédurale (D29, Python)** — ✅ **CLOS côté Python 2026-06-07** (tronçons 1-6). **1** structure+croissance Python ✅ ; **2** profil par espèce + empreinte dérivée (tomate) ✅ ; **3** seam `atteindre_segment`+`tailler` (pommier ; absorbe D29 hormones) ✅ ; **3bis** migration pommier ✅ ; **4** rendu = pont JSON Godot `export_structure.py` + stub C# `PlantRenderer.cs` ✅ ; **5** organes procéduraux (feuilles/fleurs/fruits) = **prototype Python SVG** `render_structure.py:_draw_organs` ✅ (affinage esthétique pressenti Godot, cf. D33) ; **6** sérialisation round-trip de la structure §J ✅. `test_croissance` 67/67, golden intact (`16a1b937…`). **Reste hors sprint** : save GLOBAL transversal, rendu pixel Godot des organes, portage C# (D24), profil du reste du catalogue, déclencheurs naturels du seam, marqueur `🌿` | `sprints/sprint_croissance/00_etat.md` |
| Sprint conception Maison & ombre déterministe (conception seule) — ✅ **TERMINÉ 2026-06-07** → spec `data/code/CONCEPTION_MAISON_OMBRE.md`. Maison centrale **8×8×6 m** (calcaire Montmartin, albédo espalier borné, **paramétrable**) projette une **ombre déterministe** dans le `LightField` ; monde agrandi **20×20 m = 1600 plots** ; **chemins en pierre** entre tuiles (option B : champs lumière par tuile conservés, pas d'ombrage inter-tuiles → coût ×30 évité) ; **phototropisme** branché (apex se penche) ; **golden réduit en smoke test**. 6 décisions tranchées (Q1-Q6) | `sprints/sprint_maison/00_etat.md` |
| **Sprint impl. Maison & ombre (Python)** — ✅ **CLOS côté Python 2026-06-07** (tronçons 1-4). **1** monde 20×20 m + maison inerte + golden smoke test (`world/building.py`) ✅ ; **2** ombre maison (rectangle balayé) + albédo espalier dans `LightField` ✅ ; **3** phototropisme branché dans `growth.py` (`phototropism_strength` défaut **marqué 0.30**, borné) ✅ ; **4** maquette saisonnière 3 secteurs × 4 saisons (`render_maquette`, 2 fichiers subtil/marqué) ✅. Golden smoke test `16a1b937…`. Verdict phototropisme provisoire = **marqué**, à reconfirmer avec organes/Godot. **Plus tard** (tronçon 5, hors sprint) : rendu Godot maison + ombre, portage C# (D24) | `sprints/sprint_maison/00_etat.md` |
| **Sprint Intégration Godot ↔ Python (PROCHAIN)** — 🟢 **kickoff prêt 2026-06-07**. Architecture **ACTÉE = Option B** (Python moteur / Godot vue, pont sous-process JSON ; moteur pur-stdlib → binaire gelé ; source de vérité unique). Découpé en ~6 tranches verticales (pont minimal → monde statique rendu + fix D2/D3/D8 → saison animée → actions joueur → organes/overlays/vie macro → packaging PyInstaller). Lève D24 (« portage » → « pont ») + D2/D3/D4/D8. ⚠️ Pas de `dotnet` ici → Nico build/lance dans Godot, Claude code | `sprints/sprint_integration_godot/00_etat.md` |
| **Sprint gestes `planter` + `arroser` (Python)** — gravé 2026-06-11 (t4 intégration) : ces deux gestes n'existent pas côté moteur → exclus du pont tant que Python ne les a pas (règle projet). `planter` = pont `PlayerSeedBank` → tuile ; `arroser` = geste sur le champ humidité. Moteur d'abord, pont ensuite | — (kickoff à écrire) |
| **Sprint compétition intra-plot (Python)** — gravé 2026-06-11 (retour F5 t4 Nico) : aujourd'hui `sim/succession.py` refuse toute germination sur un plot occupé (« Plot déjà occupé → pas de germination ») → une seule plante tente sa chance par case. But : plusieurs plantes peuvent ESSAYER de pousser par plot, la compétition (lumière/eau/nutriments) fait l'éclaircissage naturel. Touche le cœur écolo → re-figeage golden maîtrisé à prévoir | — (kickoff à écrire) |
| **Sprint décomposition & compost (Python + vue)** — gravé 2026-06-11 (retour F5 t4 Nico) : une plante morte disparaît instantanément (OM rendue au sol d'un coup). But : états post-mortem visibles (plante sèche → couchée → litière), restitution OM étalée dans le temps, compost comme pratique. Moteur (états + cinétique OM) puis vue (rendu des stades). Cohérent philo #1 (le sol porte la mémoire) | — (kickoff à écrire) |
| Sprint diversification écologique (D26 : étendre le catalogue d'espèces ; décision class-based vs data-driven) | `sprints/dette_kickoffs/D26_diversification_ecologique.md` |
| Sprint 3 (portage simulation — peut absorber le sprint éclairement) | `sprints/sprint_3_portage_simulation.md` |
| Sprint 4 (mécaniques conception) | `sprints/sprint_4_mecaniques_conception.md` |

### Kickoffs de dette dormante — `sprints/dette_kickoffs/`
> Écrits le 2026-06-06 : **un kickoff autosuffisant par dette sans sprint** (les
> dettes C# ont déjà les leurs : sprint_1/2/3/4). Carte + ordre recommandé + choix
> de design à trancher dans **`sprints/dette_kickoffs/00_index.md`**.

| Dette | Kickoff |
|---|---|
| D13 — Magazine de botanique | `sprints/dette_kickoffs/D13_magazine_botanique.md` |
| D14 — Carnet auto | `sprints/dette_kickoffs/D14_carnet_auto.md` |
| D15 — Extension du terrain par maîtrise | `sprints/dette_kickoffs/D15_extension_terrain.md` |
| D12.2 — Table palier→déblocage (après D13/D14/D15) | `sprints/dette_kickoffs/D12_2_table_deblocage.md` |
| D18 — Pages secrètes | `sprints/dette_kickoffs/D18_pages_secretes.md` |
| D19 — Organes comestibles (manger) | `sprints/dette_kickoffs/D19_organes_comestibles.md` |
| D23 — Catalogue d'arbres pérennes étendu | `sprints/dette_kickoffs/D23_catalogue_arbres.md` |
| D26 — Diversification écologique | `sprints/dette_kickoffs/D26_diversification_ecologique.md` |
| D30 — Champ structure/compaction du sol | `sprints/dette_kickoffs/D30_structure_compaction_sol.md` |
| D32 — Optimisation du LightField (perf) | `sprints/dette_kickoffs/D32_optim_lightfield.md` |

### Sprint 0 — gel et infrastructure documentaire — TERMINÉ ✅
- [x] État des lieux complet
- [x] `CLAUDE.md` projet
- [x] `journal.md` initial
- [x] `.gitignore` étendu
- [x] Système mémoire initial
- [x] Premier commit git

### Sprint conception — redéfinition de la vision du jeu — TERMINÉ ✅
- [x] 12 décisions structurantes actées
- [x] `journal.md` enrichi
- [x] `CLAUDE.md` réécrit (vision actualisée)
- [x] Fichiers mémoire rafraîchis
- [x] Commit dédié

### Sprint conception bis — zones blanches restantes — TERMINÉ ✅
- [x] Cycle de sauvegarde (run éternel) — JSON, auto-save par saison, seed persistée
- [x] Mécanique de gestion des aléas météo — signes diégétiques + prépa/réaction
- [x] Multiples jardins / multijoueur — avatar transportable, terrain intrinsèque
- [x] Lore / narration — jardinier silencieux + 3 voix (encyclopédie / carnet / pages secrètes)
- [x] Conditions de panne sèche — succession spontanée + manger + régen croissante
- [x] Difficulty / accessibilité — Options modulaires + debug libre + pictogrammes

### Zone Z7 — éclairement spatial — CONCEPTION CLOSE ✅
- [x] Décisions actées (pixel exact, 4 tranches + intégrale, hauteurs cm,
      genetic_factor × growth_factor)
- [x] Audit botanique des 14 espèces actuelles
- [x] 5 arbres pérennes premiers calibrés
- [x] Kickoff sprint éclairement rédigé (`sprints/sprint_eclairement.md`)
- [x] **Recadrage conception (2026-05-29)** : Option A (lumière+plantes au
      pixel, sol au plot), échelle 50 cm / 2 cm/px, soleil astronomique,
      empreintes par stade, pérennes polymorphes, génétique biparentale par
      introgression. Voir entrée *Sprint conception éclairement & reproduction*.
- [x] **Implémentation scindée en deux sprints** : éclairement (D20-D21)
      puis génétique/reproduction (D17+D22)
- [x] Implémentation : les deux sprints dédiés sont terminés (Python)

### Sprint refactor structurel — TERMINÉ ✅ (2026-06-03)
- [x] Golden output déterministe (`tests/test_golden.py`, 3 tuiles / 100 ans)
- [x] `data/code/` réorganisé en paquets `plants/ world/ fields/ sim/` + `constants.py`
- [x] Succession extraite d'`engine` vers `sim/succession.py`
- [x] Tests déplacés dans `tests/`, shims supprimés, golden identique avant/après
- [x] `journal_archive/`, `DETTE.md`, `BACKLOG.md` ; déduplication `CLAUDE.md`

### Sprint 1 — recalibrage visuel
- [ ] Mesurer dimensions exactes de tous les sprites attendus
- [ ] Décider format final tuile (78×57 conservé, ou re-générer en 96×48)
- [ ] Générer sprite maison (calcaire gris, toit ardoise, volets bois)
- [ ] Réécrire `world/TileGrid.cs` pour grille 3×3 tuiles + maison centrale
- [ ] Aligner nomenclature sprites ↔ catalogue (`SpriteName` dans
      `PlantCatalogue.cs` ou renommage des fichiers)
- [ ] Vérifier en éditeur Godot que la grille s'affiche correctement

### Sprint 2 — fondations orchestration
- [ ] `Main.cs` propre, dans namespace `Symbiose`, classe `Main : Node2D`
- [ ] `core/GameManager.cs` — singleton état global, GameState analogue
      au `game_state` dict de Python
- [ ] `core/TurnSystem.cs` — phases (planification / saison)
- [ ] Nouvelle `Main.tscn` qui remplace le brouillon obsolète

### Sprint 3 — portage simulation
- [ ] Porter `sim/effects.py` → `core/EffectSystem.cs` (mutations + résolveur)
- [ ] Porter `sim/engine.py` + `sim/succession.py` → `core/EcologySystem.cs`
      (tick hebdo, succession, aléas, transitions saisonnières)
- [ ] Tests de cohérence : lancer 1 an de simulation côté Python ET C#
      avec mêmes seeds, comparer états finaux
- [ ] Porter la logique sol vivant (D24) : uptake spatial, exsudats,
      bonus microbiome→uptake, `vitalite()` dérivée
- [ ] Réconcilier le reste de D10 (`PathogenPressure` C# → Python)

> Extension future (palier de maîtrise avancé) : **chantier C — réseau
> mycorhizien** (`etude_sol_vivant.md` Partie 3), différé hors Sprint 3.

### Sprint 4 — affichage écologique
- [ ] `PlantNode.cs` — Sprite2D plante, ancrage bas-centre, ZIndex
- [ ] `CameraSystem.cs` — zoom par paliers ×4/×8/×16/×32 snap pixel-perfect
- [ ] `LightOverlay.cs` — ombre dynamique maison (Light2D + LightOccluder2D)
- [ ] Premier test bout-en-bout : 1 tuile + 5 plantes + 1 an simulé visible

### Backlog lointain
- Shop roguelike (inter-run et intra-run)
- Bilan écologique fin de run (narratif)
- Journal Connaissance (dans la maison)
- Vue loupe Z3 (gestes fins)
- Catalogue étendu 80–120 espèces
- Cartes événements (météo + narratifs)
- Sprint version physique (STL plantes, cartes MTG)
