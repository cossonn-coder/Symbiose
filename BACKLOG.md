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
| Sprint conception vie macroscopique observable (conception seule, D31) — ✅ **TERMINÉ 2026-06-04** → spec `data/code/CONCEPTION_VIE_MACRO.md`. Modèle hybride : **`PopulationField` générique** × 4 guildes (ravageur/auxiliaire/pollinisateur/vers), dynamique **DANS le tick** (golden re-figé à l'impl. D31.2), sprites échantillonnés déterministes (golden-neutres), façades `vigueur_*` trophiques. Découpe impl. **D31.1** champs+perception (golden intact) → **D31.2** câblage écolo (re-fige) → **D31.3** façades+gestes. Gain signé « manger un individu » → dette D19 | — |
| Sprint impl. vie macroscopique **D31.1** (champs de population + perception, golden intact) — ✅ **TERMINÉ 2026-06-04** → `fields/population.py` (`PopulationField` générique + `TrophicSpec` + 4 instances + `sample_sprites`), `EcoFields.tick_populations` (étape 13b engine), `tests/test_population.py` (golden champ `population_hash.txt`, bornes, cap, positions). Modèle tick **multiplicatif** (capacité × survie). **Golden engine inchangé** `ee79dd66…`. Reste **D31.2** (câblage écolo, re-fige) + **D31.3** (façades+gestes) | — |
| Sprint impl. vie macroscopique **D31.2** (câblage écologique, re-figeage golden assumé) — ✅ **TERMINÉ 2026-06-04** : herbivorie←`ravageur` (`HERBIVORY_GAIN`), terme `predator` supprimé du calcul (commenté ; auxiliaire lu directement seulement pour la bascule létale → anti-double-comptage), `pollinator_reach`←champ `pollinisateur` (interface `eco` threadée), vers de terre câblé en **option sobre** (bioturbation→léger bonus décomposition ; D30 complet différé). **Golden re-figé** `ee79dd66…`→`c950f06c…`, golden de champ `2e6c3075…`→`b005d9ba…`. `test_auxiliaires` contraste préservé, `test_genetique` 20/20, `main.py` OK. Reste **D31.3** (façades+gestes) | `sprints/sprint_D31_2/01_cablage.md` |
| Sprint impl. vie macroscopique **D31.3** (façades `vigueur_*` read-only + gestes joueur) — ✅ **TERMINÉ 2026-06-04** : `sim/vigueur_macro.py` (4 façades pures `densité × qi_local trophique` + `decrire_vigueur_pop`) ; `sim/actions.py` — `favoriser_auxiliaire` (rondelle habitat persistant), `ecraser` **RÉEL** (retire un quantum de `ravageur`, nouvelle signature `+eco,r,c`), `becher` (↓vers + ↓microbiome), `grelinette` **livrée** (jumeau qui préserve, aération→D30). **Golden écolo INTACT** `c950f06c…`/`b005d9ba…` (vérifiés inchangés — event-driven hors tick). Golden joueur `test_vigueur` **59→87/87** (E6 « la pression revient » prouvée). `main.py` OK. **Clôt D31 côté Python** (reste portage C# D24). Gain signé « manger un individu »→D19 ; habitat local + aération grelinette→D30 | `sprints/sprint_D31_3/01_facades_gestes.md` |
| Sprint diversification écologique (D26 : étendre le catalogue d'espèces). Pas encore de kickoff | — |
| Sprint 3 (portage simulation — peut absorber le sprint éclairement) | `sprints/sprint_3_portage_simulation.md` |
| Sprint 4 (mécaniques conception) | `sprints/sprint_4_mecaniques_conception.md` |

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
