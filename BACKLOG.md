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
| Sprint conception météo (conception seule : météo/climat + signes diégétiques, D16+Z2) — ✅ **TERMINÉ 2026-06-03** → spec `docs/conception/CONCEPTION_METEO.md` | `sprints/sprint_conception_meteo.md` |
| Sprint conception Vigueur (conception seule : Vigueur universelle + coûts d'action, D11) — ✅ **TERMINÉ 2026-06-04** → spec `docs/conception/CONCEPTION_VIGUEUR.md` | — |
| Sprint implémentation météo (porter `CONCEPTION_METEO.md` en Python : `weather_at`/forecast, `temperature`, gène rusticité, signes) — ✅ **TERMINÉ 2026-06-04** (4 sous-sprints, golden `63bfdac4…`) | `sprints/sprint_meteo_impl/00_etat.md` |
| Sprint implémentation Vigueur (porter `CONCEPTION_VIGUEUR.md` en Python : couche joueur + coûts d'action + façade plante + manger, D11) — ✅ **TERMINÉ 2026-06-04** (4 sous-sprints, golden joueur 59/59, golden écolo `ee79dd66…` jamais re-figé) | `sprints/sprint_vigueur/00_etat.md` |
| Sprint VENT & ÉVAPOTRANSPIRATION (D37 complet : vent micro-climatique + évapotranspiration enrichie) — ✅ **TERMINÉ 2026-06-30** (⓪→⑦, perf-first) : masse d'air `sim/wind.py`, évapotranspiration rayonnement+vent (re-résout D39), abri spatial `fields/abri.py` (cache → perf +0 %), thigmomorphogénèse (`port_trapu`), pollinisation/dispersion anémophiles, vent×maladies fongiques, transport éolien de la litière `fields/ecofields/transport.py` + voix `transport_litiere`. Solde **D37**+**D32**+**D39**. Golden re-figé maîtrisé `0d3ca606…`, `test_vent` 54/54, `test_sim_server` 207/207, `test_senescence` PASS. « Arbres en drapeau » → dette future | `sprints/sprint_vent_evapotranspiration/00_etat.md` |
| Sprint conception paliers de maîtrise (conception seule, D12) — ✅ **TERMINÉ 2026-06-04** → spec `docs/conception/CONCEPTION_MAITRISE.md` (squelette : objet de maîtrise générique, 2 mesures globales, `palier_bonus` intact + coût d'action seam séparé). Sous-sprints D12.1–D12.5 ci-dessous | — |
| D12.1 — Succès par axe — ✅ **TERMINÉ 2026-06-04** → `CONCEPTION_MAITRISE.md` **§9**. Pivot : succès = action joueur qui améliore au-delà du cours spontané, observée ; nature de preuve croissante ; palier 5 = conjonction action experte **+** naturalisation férale. Reste : Nᵢ (répétitions/palier) → calibrage D12.4 | — |
| D12.2 — Table palier → déblocage (conception seule : quel palier ouvre magazine D13 / bascule carnet D14 / fait apparaître tuile D15 / enrichit l'encyclopédie ; `CONCEPTION_MAITRISE.md` §8.2). **BLOQUÉ** : D13/D14/D15 doivent être conçus d'abord (la table mappe vers eux). En conversation, pas de kickoff | — |
| D12.3 — Taxonomie des objets de maîtrise — ✅ **TERMINÉ 2026-06-04** → `CONCEPTION_MAITRISE.md` **§10** (passage unique, pas de découpage : conception = 1 fichier). Catalogues **reflétés** (17 espèces / 11 familles ; spillover data-driven actif sur Solanaceae/Fabaceae/Asteraceae/Rosaceae ≥2 esp.) ; concepts → terme global de `cout_action` ; outil/structure/technique **déclarés** non câblés (D29/D30/D31). Livrable central : **table objets-touchés par action** (§10.4) ; décision **outil ≠ technique** (raffine l'exemple §4.2), concepts hors terme 2. Reste : Nᵢ + atténuations → D12.4 | — |
| D12.4 — Calibrage maîtrise (post-test, pas un sprint : `K`, `BASE`, `R`, atténuations de coût, gains ponctuels ; `CONCEPTION_MAITRISE.md` §8.4). Se fait jeu en main | — |
| D12.5 — Portage C# de la maîtrise (D24) — s'absorbe dans le Sprint 3 portage. Non prioritaire (attend conception jugée satisfaisante) | `sprints/sprint_3_portage_simulation.md` |
| **Sprint impl. paliers de maîtrise (D12, Python)** — porter `CONCEPTION_MAITRISE.md` en Python (remplir `palier_bonus` stubbé + seam `cout_action`). Sprint **GROS découpé en 4 tronçons** : **i1** cœur (objet de maîtrise + progression intra-objet, golden intact) — ✅ **FAIT 2026-06-04** (`sim/maitrise.py` + `tests/test_maitrise.py` 18/18, golden écolo inchangés) ; **i2** agrégats (complétude/accumulation/spillover) + ponts Vigueur (`palier_bonus` délégué, gains ponctuels) — ✅ **FAIT 2026-06-04** (maitrise 35/35, vigueur 96/96, golden écolo inchangés ; point ouvert tranché → `palier_bonus(game_state,player)`, gains §4.3 dans `actions.py`, sens Vigueur→Maîtrise) ; **i3** seam `cout_action` + table objets-touchés (§10.4) — ✅ **FAIT 2026-06-04** (`actions.py` : `cout_action`=base×f_globale×f_objets, tables `COUTS`/`OBJETS_TOUCHES`, helpers reverse classe→clé + cible→spillover, 6 gestes branchés, urgence séparée, outils/structures neutres 1.0 ; vigueur 103/103 + section G, maitrise 35/35, golden écolo inchangés) ; **i4** détection de succès branchée (§9) — ✅ **FAIT 2026-06-04 → impl. D12 COMPLÈTE** (nouveau `sim/maitrise_detection.py` : logement (a) appelé par le driver après chaque tick, lit le `log`+état post-tick, `engine` ne l'importe jamais ; fenêtre d'imputation `noter_geste`, tag provenance féral/`marquer_replante`, gate d'observation palier ≥ 1, nature croissante §9.2, concept par cause, pollinisation biparentale, naturalisation férale §9.4(b) ; détection pure maîtrise, `actions.py` inchangé ; `tests/test_maitrise_detection.py` 20/20, maitrise 35/35, vigueur 103/103, golden écolo inchangés ; placeholders fenêtre/seuils → D12.4). Couche joueur **au-dessus du tick** → **golden écolo jamais re-figé** (`c950f06c…`/`b005d9ba…`), comme la Vigueur. Calibrage `K`/`BASE`/`R`/`SPILLOVER_RATE`/atténuations coût/fenêtre/seuils → D12.4 post-test | `sprints/sprint_D12_impl/00_etat.md` + `01_coeur_progression.md` + `03_cout_action.md` (kickoff i3) + `04_detection_succes.md` (kickoff i4) |
| Sprint conception vie macroscopique observable (conception seule, D31) — ✅ **TERMINÉ 2026-06-04** → spec `docs/conception/CONCEPTION_VIE_MACRO.md`. Modèle hybride : **`PopulationField` générique** × 4 guildes (ravageur/auxiliaire/pollinisateur/vers), dynamique **DANS le tick** (golden re-figé à l'impl. D31.2), sprites échantillonnés déterministes (golden-neutres), façades `vigueur_*` trophiques. Découpe impl. **D31.1** champs+perception (golden intact) → **D31.2** câblage écolo (re-fige) → **D31.3** façades+gestes. Gain signé « manger un individu » → dette D19 | — |
| Sprint impl. vie macroscopique **D31.1** (champs de population + perception, golden intact) — ✅ **TERMINÉ 2026-06-04** → `fields/population.py` (`PopulationField` générique + `TrophicSpec` + 4 instances + `sample_sprites`), `EcoFields.tick_populations` (étape 13b engine), `tests/test_population.py` (golden champ `population_hash.txt`, bornes, cap, positions). Modèle tick **multiplicatif** (capacité × survie). **Golden engine inchangé** `ee79dd66…`. Reste **D31.2** (câblage écolo, re-fige) + **D31.3** (façades+gestes) | — |
| Sprint impl. vie macroscopique **D31.2** (câblage écologique, re-figeage golden assumé) — ✅ **TERMINÉ 2026-06-04** : herbivorie←`ravageur` (`HERBIVORY_GAIN`), terme `predator` supprimé du calcul (commenté ; auxiliaire lu directement seulement pour la bascule létale → anti-double-comptage), `pollinator_reach`←champ `pollinisateur` (interface `eco` threadée), vers de terre câblé en **option sobre** (bioturbation→léger bonus décomposition ; D30 complet différé). **Golden re-figé** `ee79dd66…`→`c950f06c…`, golden de champ `2e6c3075…`→`b005d9ba…`. `test_auxiliaires` contraste préservé, `test_genetique` 20/20, `main.py` OK. Reste **D31.3** (façades+gestes) | `sprints/sprint_D31_2/01_cablage.md` |
| Sprint impl. vie macroscopique **D31.3** (façades `vigueur_*` read-only + gestes joueur) — ✅ **TERMINÉ 2026-06-04** : `sim/vigueur_macro.py` (4 façades pures `densité × qi_local trophique` + `decrire_vigueur_pop`) ; `sim/actions.py` — `favoriser_auxiliaire` (rondelle habitat persistant), `ecraser` **RÉEL** (retire un quantum de `ravageur`, nouvelle signature `+eco,r,c`), `becher` (↓vers + ↓microbiome), `grelinette` **livrée** (jumeau qui préserve, aération→D30). **Golden écolo INTACT** `c950f06c…`/`b005d9ba…` (vérifiés inchangés — event-driven hors tick). Golden joueur `test_vigueur` **59→87/87** (E6 « la pression revient » prouvée). `main.py` OK. **Clôt D31 côté Python** (reste portage C# D24). Gain signé « manger un individu »→D19 ; habitat local + aération grelinette→D30 | `sprints/sprint_D31_3/01_facades_gestes.md` |
| Sprint conception Hormones de croissance (conception seule, D29 : auxine / dominance apicale / réponse à la taille) — ✅ **TERMINÉ 2026-06-04** → spec `docs/conception/CONCEPTION_HORMONES.md` (volets A–I). Topologie **tranchée scalaire** (le rendu ne peut suivre, pas de moteur végétal procédural) ; **2 scalaires** `dominance_apicale=1.0`/`ramification=0.0` repos NEUTRE → golden intact ; mapping coupe→émergence sur variables existantes ; action `tailler` (apex/branche) dans `actions.py` ; trait `reponse_taille` (défaut `insensible`), démonstrateur **tomate + pommier** ; succès maîtrise = technique §9.5 (futur marqueur `🌿`). Placeholders → calibrage post-test | `sprints/sprint_hormones.md` |
| ~~**Sprint impl. Hormones (D29, Python)** — 2 scalaires + cinétique + `tailler` + démonstrateur, golden préservé~~ ⚠️ **SUPERSEDED 2026-06-05** : modèle scalaire abandonné, découpage `sprints/sprint_D29_impl/` archivé. Absorbé dans le **Sprint impl. Croissance procédurale** (tronçon 3) ci-dessous | `sprints/sprint_D29_impl/00_etat.md` (archivé) |
| Sprint conception Croissance procédurale (conception seule, D29 réorienté : auxine structurelle + rendu pixel procédural + morphogénèse) — ✅ **TERMINÉ 2026-06-05** → spec `docs/conception/CONCEPTION_CROISSANCE.md` (A–M). Pivot : **structure de segments** en Python (remplace les 2 scalaires), **moteur permanent**, **auxine le long de la structure**, **phototropisme** (`LightField`), **empreinte dérivée** (contrat `height_at`… inchangé → golden re-figé localisé), **organes tout procéduraux**, racines rayon dérivé. **Profil de croissance PAR ESPÈCE** (vitesse + `port_archetype`) à décrire pour les 14 espèces, calibré sur `growth_stages`/`age_curve`. Absorbe `CONCEPTION_HORMONES.md` | `sprints/sprint_hormones.md` + audit session 2026-06-05 |
| **Sprint impl. Croissance procédurale (D29, Python)** — ✅ **CLOS côté Python 2026-06-07** (tronçons 1-6). **1** structure+croissance Python ✅ ; **2** profil par espèce + empreinte dérivée (tomate) ✅ ; **3** seam `atteindre_segment`+`tailler` (pommier ; absorbe D29 hormones) ✅ ; **3bis** migration pommier ✅ ; **4** rendu = pont JSON Godot `export_structure.py` + stub C# `PlantRenderer.cs` ✅ ; **5** organes procéduraux (feuilles/fleurs/fruits) = **prototype Python SVG** `render_structure.py:_draw_organs` ✅ (affinage esthétique pressenti Godot, cf. D33) ; **6** sérialisation round-trip de la structure §J ✅. `test_croissance` 67/67, golden intact (`16a1b937…`). **Reste hors sprint** : save GLOBAL transversal, rendu pixel Godot des organes, portage C# (D24), profil du reste du catalogue, déclencheurs naturels du seam, marqueur `🌿` | `sprints/sprint_croissance/00_etat.md` |
| Sprint conception Maison & ombre déterministe (conception seule) — ✅ **TERMINÉ 2026-06-07** → spec `docs/conception/CONCEPTION_MAISON_OMBRE.md`. Maison centrale **8×8×6 m** (calcaire Montmartin, albédo espalier borné, **paramétrable**) projette une **ombre déterministe** dans le `LightField` ; monde agrandi **20×20 m = 1600 plots** ; **chemins en pierre** entre tuiles (option B : champs lumière par tuile conservés, pas d'ombrage inter-tuiles → coût ×30 évité) ; **phototropisme** branché (apex se penche) ; **golden réduit en smoke test**. 6 décisions tranchées (Q1-Q6) | `sprints/sprint_maison/00_etat.md` |
| **Sprint impl. Maison & ombre (Python)** — ✅ **CLOS côté Python 2026-06-07** (tronçons 1-4). **1** monde 20×20 m + maison inerte + golden smoke test (`world/building.py`) ✅ ; **2** ombre maison (rectangle balayé) + albédo espalier dans `LightField` ✅ ; **3** phototropisme branché dans `growth.py` (`phototropism_strength` défaut **marqué 0.30**, borné) ✅ ; **4** maquette saisonnière 3 secteurs × 4 saisons (`render_maquette`, 2 fichiers subtil/marqué) ✅. Golden smoke test `16a1b937…`. Verdict phototropisme provisoire = **marqué**, à reconfirmer avec organes/Godot. **Plus tard** (tronçon 5, hors sprint) : rendu Godot maison + ombre, portage C# (D24) | `sprints/sprint_maison/00_etat.md` |
| **Sprint Intégration Godot ↔ Python (PROCHAIN)** — 🟢 **kickoff prêt 2026-06-07**. Architecture **ACTÉE = Option B** (Python moteur / Godot vue, pont sous-process JSON ; moteur pur-stdlib → binaire gelé ; source de vérité unique). Découpé en ~6 tranches verticales (pont minimal → monde statique rendu + fix D2/D3/D8 → saison animée → actions joueur → organes/overlays/vie macro → packaging PyInstaller). Lève D24 (« portage » → « pont ») + D2/D3/D4/D8. ⚠️ Pas de `dotnet` ici → Nico build/lance dans Godot, Claude code | `sprints/sprint_integration_godot/00_etat.md` |
| ~~**Sprint gestes `planter` + `arroser` (Python)**~~ — ✅ **CLOS 2026-06-13** (3 sessions). `planter` dépose un `GrainEnAttente` (gènes propres, `cultive`) que la succession lève au bon moment ; `arroser` mouille le champ humidité (cap 3, cumulatif). **Modèle « eau »** : drainage par sol (`DRAINAGE_PAR_SOL`) + asphyxie 2 paliers (uptake réversible / `asphyxie_memory` → santé), stagnation « noyé ». **Golden RE-FIGÉ maîtrisé T0+T1** (`16a1b937…`→`7ee907d3…`, asphyxie globale, option A Nico). Pont 0.3.3 (route les 2 gestes, banque-joueur au snapshot). Reste connexe hors sprint : semis intérieur (Q6), bouture/division (Q7), gène `tolerance_exces_eau` si calibrage le réclame | `sprints/sprint_planter_arroser.md` + `docs/conception/CONCEPTION_PLANTER_ARROSER.md` |
| ~~**Sprint compétition intra-plot (Python)**~~ — ✅ **CLOS 2026-06-13** (conception figée Q1–Q11 + impl). Verrou de germination levé (`sim/succession.py`, 3 portes) sans malus artificiel + **gène `tolerance_ombre`** (défaut par strate + escompte de niche/croissance) + **étiolement** (`growth.py`, héliophile ombragé ×1.30 axial). Éclaircissage **émergent** confirmé par mesure (pic ~73 → final ~12). **Golden RE-FIGÉ maîtrisé à 3 causes** : `7ee907d3…`→`6bf71ee5…` ; population golden `b005d9ba…`→`f1fe093c…`. `test_competition.py` créé (14/14), `test_planter`/`test_senescence` adaptés, suite verte, `main.py 30` propre. **2 points laissés à Nico** : (a) **tronçon 4 SAUTÉ** — fonte des semis intra-plot (co-occupants dans `_local_density`, Q4) non câblée car jugée non justifiée ; (b) **paradoxe pionnier** — les 4 adventices sont sciaphiles (strate sol/basse → 1.25) alors qu'elles sont héliophiles ; correctif = override `shade_tolerance` (4ᵉ cause de dérive golden, non appliqué unilatéralement) | `sprints/sprint_competition_intraplot.md` (impl) + `docs/conception/CONCEPTION_COMPETITION_INTRAPLOT.md` (conception figée) |
| **Sprint décomposition & compost (Python + vue)** — ✅ **CONCEPTION FIGÉE 2026-06-13** → spec `docs/conception/CONCEPTION_DECOMPOSITION_COMPOST.md` (4 rounds, Nico tranche). **Parcelles de litière `{tissu,masse,age}`/plot remplacent `om_fresh`** (dérivé = Σ) ; 6 tissus (`diffus`/`feuille`/`fleur`/`herbacé`/`fruit`/`bois`) à vitesses propres ; **mort → squelette persistant** (sèche→couchée→fragmentation) ; `tailler` dépose du `bois` ; **abscission d'automne** ; **organes-fruits traçables** (maturité visible, `manger` ciblé qui déplète → **absorbe D19**) ; **attraction animale** sur le fruit (frais→auxiliaire, pourri→ravageur+déco) ; **bac à compost** (tendre, maturation hybride) + **pile à bois** (BRF, habitat) posables, **épandre** borné par jauge → trio humus. **Re-figeage golden LARGE annoncé** (écolo + population) + **raccourci du smoke test**. Impl = **6 sous-sprints indépendants** (① parcelles+cascade → ② dépôts → ③ organes-fruits → ④ attraction → ⑤ structures+gestes → ⑥ vue). Lève une part de **D33** (état d'organe réel). **Reste : implémentation** (kickoffs `sprints/sprint_decomposition_compost/0N_*.md` à écrire au démarrage) | `docs/conception/CONCEPTION_DECOMPOSITION_COMPOST.md` (conception) + kickoffs impl à écrire |
| ~~**Sprint saisonnalité vie macro (Python, calibrage)**~~ — ✅ **CLOS 2026-06-16** (conception figée + impl). Diagnostic confirmé (warmth printemps ~0.42, inertie 0.85^13≈0.12 = ~13 sem). Solution : **horloge photopériode** `daylength(wiy)` (sinusoïde 8↔16 h, pic solstice wiy25, pure) + **porte phénologique** `phenology=smoothstep(daylength, daylen_min, daylen_full)` **par guilde** (ravageur/aux 10/13 h, pollinisateur 12/14.5 h, vers 8.5/10 h) + **inertie asymétrique** (chute 0.55 rapide / montée 0.85 lente). Mesuré (110 sem) : ravageur/aux/pollinisateur hiver ~0.001-0.007 vs pic 0.15-0.25 ; vers hiver 0.07 = 45 % du pic (fenêtre par guilde prouvée). **Golden RE-FIGÉ maîtrisé** (chemin herbivorie D31.2 seul) : golden `af3bfa8f…`, population `6dc7004d…`. `test_population.py` +3 preuves (dormance/réveil, vers insensibles, photopériode verrouille un redoux). `daylength` posée comme **fondation de la phénologie florale** (arc pollinisation) | `docs/conception/CONCEPTION_SAISONNALITE_VIE_MACRO.md` + journal 55 |
| ~~**Sprint plasticité & expression de gènes adaptogènes (Python)**~~ — ✅ **CLOS 2026-06-22** (①→⑤, conception figée `CONCEPTION_PLASTICITE_EXPRESSION.md`). Le stress VÉCU module l'EXPRESSION effective des gènes adaptogènes (`expressed_gene = clamp_gene(genes × expression)`), distincte du génotype darwinien figé. **5 gènes** (sécheresse/ombre/froid/pathogène/asphyxie), dynamique lerp à **hystérèse** (`TAU_UP≠TAU_DOWN`) ; **coût croissance/défense** (`cout_defense`, anti-sélection) ; **priming transgénérationnel** (`child_expression`, mère seule, oubli ÉMERGENT) qui **voyage avec la graine par tous les canaux** (④bis) ; **signe diégétique** d'acclimatation (cause `acclimatation`, feuillage glauque/coriace, ⑤). Golden RE-FIGÉ maîtrisé ①→④ (`3f86bf53…`→`2ab026ad…`), NEUTRE en ④bis et ⑤ ; pont **0.5.3** ; `dotnet build` vert. **Dette D43** (Maîtrise → carnet interprétatif, P4). Reste F5 visuel = Nico + mapping C# `ombre` du sprint précédent (hors périmètre) | `sprints/sprint_plasticite/00_etat.md` + `docs/conception/CONCEPTION_PLASTICITE_EXPRESSION.md` + journal 74 |
| ~~**Sprint bancs d'essai / environnements de test dédiés**~~ — ✅ **TERMINÉ 2026-06-23** (①→⑤ tous clos). Paquet `data/code/bancs/` (9 fabriques de mondes paramétrés + helpers `base.py` `force_memoire`/`force_faune`/`vieillir`), branché `cmd_init` (`config in BANCS`, hors `smoke`/`full` → **golden NEUTRE** `2ab026ad…` à TOUS les tronçons). Oracles `data/code/tests/bancs/` (1 test/banc, source `sim/semiologie.py` = ce que la vue lit). ⑤ : commande pont **`list_bancs`** (0.5.4, registre Python source unique) + **sélecteur Godot** (`WorldView.Selecteur.cs`, `OptionButton` peuplé du serveur, `dotnet build` vert). **Bilan D47** consolidé (cf. DETTE.md) : C4/C5/C6 = artefacts de carte/design tranchés MOTEUR ; C2/C3/`ombre` = suspects RENDU C# à confirmer au F5 du ⑤ (`ombre` = dette 0.5.2). Reste **F5 visuel = Nico** (exhiber chaque banc, verser les bugs rendu confirmés en dette ciblée). — gravé 2026-06-22 (F5 post-plasticité, conclusion Nico : « il faudra créer des environnements de test dédiés, la carte actuelle ne permet pas d'observer tous les 18 phénomènes »). **CADRÉ 2026-06-22** (5 tronçons). But : des **mondes paramétrés** (paquet `data/code/bancs/`, registre branché dans `cmd_init` hors `smoke`/`full`) qui FORCENT chaque condition observable, **chacun avec un oracle** (mini-test Python qui asserte le signe) — sert aussi d'outil de tri pour **D47** (oracle vert + écran muet ⇒ bug rendu C#). Granularité MIXTE (thématiques + isolés). Bancs : `chlorose_acidophile`, `asphyxie_argile`, `carence_npk` (édaphique) ; `secheresse_sable`, `acclimatation`, `ombre_dense` (climatique, ⚠️ rendu `ombre` C# manquant dette 0.5.2) ; `infestation_ravageur`, `verger_floraison`, `semis_tempere` (biotique). **AUCUNE mécanique nouvelle** (composition de conditions) → golden NEUTRE à chaque tronçon. Sélecteur Godot (menu C#) au ⑤ + bilan D47. Recoupe D33 (sémiologie), plasticité, D41 (sol affamé), D31 (vie macro). | `sprints/sprint_bancs_essai/00_etat.md` (+ `01`→`05`) |
| ~~**Sprint physico-chimie du sol : température du sol + pH (Python)**~~ — ✅ **CLOS** : champ `temperature_sol` livré (sprints `thermique_microclimat` + vent) et champ `ph` livré (sprint physico-chimie NPK `b7ee4be`, 2026-06-20). **Reste de la phrase d'origine — « la germination devrait lire le sol, pas l'air » — désormais CONÇU 2026-06-30** dans `sprint_germination_thermique` (porte `bell(T_sol,…)` sur la niche, gène `germination_thermique`, suppression du flush calendaire, correctif pluie→T_air) | `sprints/sprint_germination_thermique/00_etat.md` + `docs/conception/CONCEPTION_GERMINATION_THERMIQUE.md` |
| **Arc pollinisation & cycle de vie (MOTEUR → re-fige golden)** — ✅ **CONCEPTION FIGÉE 2026-06-16** → spec `docs/conception/CONCEPTION_POLLINISATION_CYCLE_VIE.md` (§A–§F, Nico tranche A–E). **Audit clé : le brassage génétique pollinisé existe déjà** (`reproduction.py` `find_father`/`child_genes` + `pollinator_reach` modulé par le champ, D31.2) → l'arc ne le reconstruit pas (E non retenu). Décisions : **A** floraison = scalaire `floraison∈[0,1]` sur `PlantInstance`, **double porte GDD (`gdd_accum`, `T_BASE_FLORAISON≈6`) + photopériode** (`bloom_daylen_min/max`, s'appuie sur `daylength`), fenêtre par espèce estivale ; **B** nouaison **continue** ∝ `pollen_recu` (dose intégrée pendant la floraison), déclenchée **en fin de floraison PAR PLANTE** (remplace `FRUIT_NOUAISON_WEEK`), self/wind pleins, entomophiles **sans plancher** ; **C** ressource pollinisateur = `Σ(floraison × attractivite_pollinisateur)` (nouveau trait mellifère) remplace `_flower_grid`, **pas de Vigueur joueur** ; **D** cycle bouclé chenille→papillon via 2 champs légers `chenille`+`chenille_nourrie` (PAS une 5ᵉ guilde) — ponte des papillons, herbivorie lit `ravageur+chenille`, maturation par la nourriture, famine→mortalité, métamorphose→pollinisateur. Découpe impl : **① floraison+phénologie (golden NEUTRE visé) → ② nouaison pollinisée (golden ~neutre) → ③ reconnexion ressource (golden RE-FIGÉ maîtrisé) → ④ cycle chenille (golden RE-FIGÉ maîtrisé)**. **Reste : implémentation** (kickoffs `01_*.md`…`04_*.md` à écrire au démarrage). Mémoire : `design_pollinisation_cycle_vie.md` | `docs/conception/CONCEPTION_POLLINISATION_CYCLE_VIE.md` + `sprints/sprint_pollinisation_cycle_vie/00_conception_kickoff.md` + journal 56 |
| **Raffinement compost & interconnexions du jardin (conception d'abord, MOTEUR + vue)** — gravé 2026-06-16 (retour F5 vue·rattrapage 03, Nico). Revoir le modèle ⑤ : **(a) bac/pile = stock au niveau TUILE, pas posé à un plot** — `composter` sur N'IMPORTE quel plot verse dans le bac de la tuile, `empiler_bois` idem vers la pile (aujourd'hui structure liée à un plot, ramasse le plot porteur seulement). **(b) `epandre` en 2 clics** : clic sur le bac → clic sur le plot ciblé → restitue au plot et réduit `compost_mur` d'autant ; jauge insuffisante ⇒ épand tout le dispo (le moteur fait DÉJÀ q=None⇒tout + bornage ; neuf = l'UX 2 temps + structure-tuile). **(c) cycle de MATURATION du compost explicite** (vérifier l'existant `retourner`/`tick_structures` ⑤B et le rendre lisible/présent). **(d) faune attirée par le compost ET la pile** (abris + nourriture) — la pile est déjà un habitat `auxiliaire` ⑤, étendre au bac/compost via attraction ④. **(e) NOUVEL acteur : champignons / mycélium** dans la décomposition (le cycle décompo·compost ne les modélise pas) + leur attrait nourricier pour certains animaux. **(f) RÈGLE TRANSVERSE** : tisser des liens explicites entre chaque acteur (plantes, faune, champignons, sol, structures) — tout coexiste, cf. mémoire `regle_interconnexion_acteurs.md`. ✅ **CONCEPTION FIGÉE 2026-06-25** → spec `docs/conception/CONCEPTION_MYCELIUM_INTERCONNEXIONS.md`. Acteur NEUF **mycélium** = champ déterministe `EcoFields` + carpophores échantillonnés (visible) ; **3 rôles** saprophyte (terme fongique sur décompo `bois`) / liant (`om_stable`) / **mycorhizien wood-wide-web** (boost borné du `p` dans `plant_uptake` + miroir `qi_local`) + faune fongivore (`auxiliaire`) ; bêchage casse le réseau (`disturbance` déjà écrit → `becher` vs `grelinette` différenciés) ; structures bac/pile passées **niveau tuile** + `epandre` 2 clics + maturation lisible/colonisation fongique du tas + faune sur le bac. Re-figeage golden LARGE annoncé (décompo+uptake+structure+population). **6 sous-sprints** ①champ→②saprophyte+liant→③mycorhize→④faune+carpophores→⑤structures tuile→⑥vue. ✅ **TERMINÉ 2026-06-25** (exécution autonome `/sprint-auto`, ①→⑥ tous clos, commits `4fc9fd4`→`d6f3528`) : golden final smoke `db5e7c66…` / pop `9ba39ab7…` (re-figés MAÎTRISÉS au ②③④, isolations prouvées) ; pont 0.5.9 ; `dotnet build` vert. **Reste F5 visuel = Nico** (carpophores, voile fongique, `epandre` 2 temps, overlay `mycelium` F6) + calibrage des knobs placeholders | `docs/conception/CONCEPTION_MYCELIUM_INTERCONNEXIONS.md` + `sprints/sprint_mycelium_interconnexions/` + journal 81 |
| **Bloc voix narratives (D13 magazine + D14 carnet + D18 pages secrètes + D43 acclimatation + encyclopédie + D12.2)** — ✅ **CONCEPTION FIGÉE 2026-06-29** → spec unifiée `docs/conception/CONCEPTION_VOIX_NARRATIVES.md` (§0→§8). Décisions Nico : **substrat = ledger partagé** (`sim/journal.py`, extrait de `_evenements()` → `sim/evenements.py`, consigné par le DRIVER hors tick → golden INTACT) ; **4 voix lecteurs read-only** (carnet « je » par événement, encyclopédie « naturaliste » par espèce, pages secrètes lore pur, magazine 4ᵉ canal) ; **encyclopédie 3 niveaux** sur paliers 1/2/3 (A) ; **carnet bascule interprétatif au palier 3** du concept (B, D43 = cas `adaptation`) ; **magazine sœurs au palier 3** famille (C) ; **table D12.2** remplie (§3, seuils → D12.4). **Corpus complet** : carnet (gabarits 2 registres §5), **encyclopédie 28 fiches × 3 niveaux** (§6), **pages secrètes 20 entrées 5 voix** (§7). Roadmap impl. **6 tronçons** (①evenements→②journal→③carnet→④encyclopédie→⑤pages→⑥magazine, tous golden-neutres, §8). **CONCEPTION SEULE — pas d'impl. tant que Nico ne lance pas** (portage non prioritaire). Mémoire `design_voix_narratives.md`. Reste : impl. Python (6 tronçons) + UI Godot (D24) + marqueurs bouture/oiseau/vent + calibrage D12.4 | `docs/conception/CONCEPTION_VOIX_NARRATIVES.md` + journal |
| **Sprint HYDROLOGIE DE RELIEF & MARÉCAGES (MOTEUR + vue)** — ✅ **CONCEPTION FIGÉE 2026-07-03** (`/conception`, s'appuie sur D57 relief) → spec `docs/conception/CONCEPTION_HYDROLOGIE_MARECAGE.md`. Ajoute la dimension hydraulique LATÉRALE : champ `altitude` micro-relief déterministe NEUF (≠ épaisseur d'humus D57) ; `eau_surface` (lame de surface) + `tick_ruissellement` (double-buffer déterministe, l'eau va des plots hauts aux bas) → **FLAQUE** ; flaque durable → **MARÉCAGE** (`marais_memory` + hystérèse → décompo anaérobie=tourbe, pH acide, niche). Guilde interconnectée : **sphaigne** (ingénieur : acidifie+retient+tourbe), **aulne** (Betulaceae NEUVE, fixe l'azote arboré), **plante carnivore** (Drosera = 1er végétal-PRÉDATEUR, puits sur la **faune de mare** moustique/libellule NEUVE → échappe à la faim d'azote D41) — chacune ses 5 voix. Gestes joueur **`creuser`** (cuvette) / **`drainer`**. **8 tronçons** (①altitude→②eau_surface+ruissellement [golden RE-FIGÉ LARGE annoncé]→③marécage→④faune de mare→⑤aulne+sphaigne→⑥carnivore+puits→⑦gestes→⑧vue). Croise D57/D40/D39/D31/D41/D55. **Prêt pour `/sprint-auto`** | `docs/conception/CONCEPTION_HYDROLOGIE_MARECAGE.md` + `sprints/sprint_hydrologie_marecage/` (00_etat + 01→08) |
| **Sprint LUXURIANCE PAR STRATIFICATION (densification — MOTEUR + vue, D65, absorbe D62)** — 🟢 **CONÇU 2026-07-04, PRÊT `/sprint-auto`** (`/conception`). Le jardin se remplit et se superpose : ① champ de couverture au sol (1 scalaire, scatter) → évaporation réduite + anti-adventice + gate clonal [golden RE-FIGÉ] ; ② **mécanique clonale** 1 chemin paramétré `clonal_mode` stolon/rhizome/drageon, déterministe, coût Vigueur, envahissement émergent [golden RE-FIGÉ] ; ③ silhouette rendu + override empreinte ciblé (courge) ; ④ fraisier+menthe ; ⑤ framboisier+bambou traçant+violette (+ famille Violaceae) — 5 voix chacune ; ⑥ vue Godot (empilement multi-strates visible + couverture rendue + silhouettes + banc F5 `luxuriance` + pont 0.5.19). **Absorbe D62** (rampantes/clonales — à fermer à la clôture). | `docs/conception/CONCEPTION_LUXURIANCE_STRATIFICATION.md` + `sprints/sprint_luxuriance_stratification/` (00_etat + 01→06) |
| **Sprint GRIMPANTES (mécanique de grimpe — MOTEUR + vue, D49)** — ✅ **TERMINÉ 2026-07-04** (①→⑥, carte blanche façon `/sprint-auto`). Volet A seul (grimpe ; rampantes/traçantes = D62). Livré : modèle **GÉOMÉTRIQUE** (hauteur = `max(z)` des segments, affalement/grimpe par plancher d'apex modulé, JAMAIS de clamp), trait **`mode_grimpe`** (crampon/vrille_volubile/sarmenteux), supports NEUFS (tuteur/treillis/pergola posables + mur maison + **plante-hôte vivante** avec étranglement émergent par l'ombre), gestes `poser_*`/`palisser` + maîtrise + exemption verse, catalogue **lierre**+**jasmin**+5 voix, pont **0.5.18** (bloc `supports` + état `support` par plante), vue C# (`SupportRenderer` pieu/grille/portique + vrilles `DrawTendrils`), banc `grimpantes`. **Golden JAMAIS re-figé** (`a6c2f651…` du 1er au dernier tronçon), `test_sim_server` 245/245, `test_grimpe` 10/10, `dotnet build` vert. Absorbe le rendu de vrille (`CONCEPTION_RENDU_FEUILLAGE §7/E6`). Reste = **F5 Nico** (calibrage à l'œil). | `docs/conception/CONCEPTION_GRIMPANTES.md` + `sprints/sprint_grimpantes/` (00_etat + 01→06) |
| **Sprint USURE, PAS PUNITION (létalité & compétition — MOTEUR, D64 reframé)** — ✅ **TERMINÉ 2026-07-04** (①→③, `/sprint-auto`). Le conflit spatial cesse de tuer d'un verdict ; la mort du dominé ÉMERGE du stress continu (aligne le code sur `CONCEPTION_COMPETITION_INTRAPLOT` Q3). ① `_resoudre_conflits` NON-LÉTAL (conflit = notification + élagage `_conflit_perime`, `regress()` conservé inutilisé) ; ② cap létalité chronique −1 santé/tick (`_cap_chronique`, flux AIGU/CHRONIQUE dans `apply_disturbances`) ; ③ vue = vérif pure (rendu `ombre` déjà mappé). **Golden final `15073be1…`** (① re-figé `007be139…` — log fantôme prouvé, PAS le `a1c9c51f…` pré-mesuré ; ② re-figé localisé). `test_competition` 14/14, `test_senescence` PASS. Reste **F5 Nico**. Suite = **D65 luxuriance/stratification** (`/conception` séparée). | `docs/conception/CONCEPTION_USURE_LETALITE.md` + `sprints/sprint_usure_letalite/` (00_etat + 01→03) |
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

### Pistes génération / renouvellement de terrain — analyses PDF (2026-06-23)
> Lecture de deux papiers d'algorithmic botany : ① modélisation procédurale d'arbres
> 3D (hors-scope à 90 %), ② Lane & Prusinkiewicz 2002, « Generating Spatial
> Distributions for Multilevel Models of Plant Communities » (2D, sur grille de
> probabilité). Bilan : les mécaniques niche/lumière/succession/compagnonnage sont
> **déjà dans le moteur, souvent en mieux** (`niche_index` n-dim, `bell(pH)`,
> `shade_tolerance_base` + gène `tolerance_ombre`, `shade_stress_damage`, sénescence
> `_tick_senescence_health`, registre d'effets typés `basil_companion_check` /
> family_effects). Les papiers **valident** l'archi (et le multi-niveaux = Option B).
> Restent ces angles morts réels (génération INITIALE des champs + renouvellement
> temporel), à creuser un jour — aucun n'est urgent.
- [ ] **Prototypes de taches de sol** (self-similarité) — initialiser l'hétérogénéité
  du microbiome/fertilité par instanciation + perturbation locale d'un petit
  catalogue de motifs. Sert les 3 écoles de départ et l'hétérogénéité persistante.
- [ ] **Sénescence de cohorte → gaps** — champ « âge de cohorte » ouvrant des trouées
  quand une classe d'âge meurt ensemble. Renouvellement spontané du jardin éternel.
  (La sénescence INDIVIDUELLE existe déjà : `mortalite.py:_tick_senescence_health`.)
- [ ] **Gradient directionnel sur un champ** — primitive simple de transition douce
  orientée (ex. humidité plus haute d'un côté du terrain).
- [ ] **Noyau de dispersion contrôlable des semis** — état réel du moteur (corrige une
  note antérieure imprécise) : les **archétypes** déposent au plot-foyer du parent
  (`mortalite.py:_reproduction` → banque-sol, germination par niche) ; les
  **vivaces/arbres** recrutent DÉJÀ dans un rayon (`RESEED_RADIUS_CM = 150 cm`) mais
  par sélection du plot le plus **lumineux**, pas par noyau probabiliste. Piste :
  noyau gaussien à rayon paramétrable → levier « petit rayon → agrégats / grand →
  homogène » (Fiche dispersion P②).
- [ ] **Indice de Hopkins comme outil de validation** (P②) — métrique scalaire
  clusterisé/aléatoire/dispersé. À utiliser en test pytest pour valider que les futurs
  générateurs des 3 écoles produisent bien la texture spatiale visée. Outil, pas
  mécanique de jeu.
- [ ] **Deformation-kernel pour le placement initial** (P②) — placement global-to-local
  par noyau d'inhibition/promotion sur un champ de proba 2D (`f` initialisé depuis
  fertilité × humidité). Séquentiel donc PAS hash-spatial-pur → réservé à
  l'**initialisation** du monde (calcul unique, résultat persisté via seed), jamais
  par-tick. Donne un levier de forme de clustering par espèce.

### Pistes RENDU PIXEL-ART 16-bits (Chrono Trigger) — recherche web (2026-06-23)
> Axe DISTINCT des précédents : ici la source de vérité est la couche **Godot/C#**
> (`world/WorldView*`, `visuals/PlantRenderer*`, overlays), pas `data/code/`. État
> actuel : sol = losanges placeholder en **aplats unis** (`WorldView.Monde.cs`,
> `SoilColor`), aucune transition / ramp / dithering ; `default_texture_filter=0`
> (Nearest) ✓. Aucune de ces techniques n'existe encore côté rendu de sol.
- [ ] **Dual-grid autotiling** — transitions terre↔argile↔sable avec **5 tuiles**
  (grille graphique décalée d'½ plot lisant 4 voisins logiques) au lieu des 47 du
  blob. Se branche sur le `t["soil"]` du snapshot. Déterministe, pur voisinage.
  Réf. Excalibur / redblobgames / BorisTheBrave.
- [ ] **Dithering ordonné (matrice de Bayer)** — déterministe par pixel. Double
  emploi : casser le banding des rampes ET **afficher les champs scalaires** (humidité,
  fertilité) en texture de sol lisible **sans HUD chiffré** (philo #5) — alternative
  diégétique aux heatmaps debug `FieldOverlay`. (Floyd-Steinberg = séquentiel →
  réserver à la génération d'asset hors-ligne.)
- [ ] **Palette : ramps + hue-shifting** — remplacer les aplats unis (1 couleur/sol,
  1 couleur/organe) par des rampes 3-5 valeurs, ombre décalée vers le froid plutôt
  que vers le noir. Fondation des deux pistes ci-dessus.
- [ ] **⚠️ Alerte archi : iso losange vs grille carrée SNES** — tout le corpus
  pixel-art suppose une grille carrée top-down ; Symbiose rend en **iso 2:1**
  (78×39 px/plot). Chrono Trigger est top-down 3/4 carré, pas iso pur. À TRANCHER
  avant tout dev pixel-art : assumer l'iso (tuiles diamant) ou se rapprocher du carré.
- [ ] **Cache de sprite `PlantRenderer`** (perf) — « rendre une fois sur une
  surface/texture puis blitter » si le rendu procédural redessine trop souvent.
- Shop roguelike (inter-run et intra-run)
- Bilan écologique fin de run (narratif)
- Journal Connaissance (dans la maison)
- Vue loupe Z3 (gestes fins)
- Catalogue étendu 80–120 espèces
- Cartes événements (météo + narratifs)
- Sprint version physique (STL plantes, cartes MTG)
