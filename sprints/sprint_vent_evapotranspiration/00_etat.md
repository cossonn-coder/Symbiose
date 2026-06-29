# Sprint VENT & ÉVAPOTRANSPIRATION (D37) — état partagé

> **État léger** (mis à jour en fin de chaque tronçon). Le **design figé** vit dans
> [`docs/conception/CONCEPTION_VENT_EVAPOTRANSPIRATION.md`](../../docs/conception/CONCEPTION_VENT_EVAPOTRANSPIRATION.md)
> — chaque kickoff `tN_*.md` y renvoie pour le détail. Repars à froid : lis ce
> fichier + le `tN_*.md` du tronçon courant + la/les §§ de conception citées.

## En une phrase
Introduire le **vent** comme facteur micro-climatique complet et **enrichir
l'évaporation** (rayonnement + vent) pour rééquilibrer la rosée → résout **D37**
(vent continu) et **D39** (`test_senescence` rouge : pommier asphyxié à 19,5 ans).
**Contrainte #1 = perf** (Nico : « peur que le moteur soit trop lent »).

## Décisions figées (Nico, 2026-06-29)
- Périmètre = **D37 complet** + tous les effets (thigmo, dégât étiolées, semis
  intérieur/extérieur, régimes nul/risées/venturi, vent↔nébulosité, pollinisation/
  dispersion, maladies fongiques, wind chill, transport litière/neige).
- Découpage **perf-first 8 tronçons** (⓪→⑦, §8 conception). ⓪→② débloquent D39 à
  coût ~nul ; ③ (abri spatial) = seul morceau cher, isolé/caché/mutualisé/reportable.
- **D32 intégré au tronçon ⓪** : optim scatter de la boucle lumière-sol, **mesurée
  ×6 plancher, golden-safe** (`tools/diag_light_coverage.py`). Verrou = test
  d'équivalence bit-à-bit.
- **Re-figeage golden LARGE assumé** dès ② (nébulosité dynamique + évaporation).
- « Arbres en drapeau » = hors périmètre (dette).

## Carte des tronçons
| # | Fichier | Coût | Golden | Statut |
|---|---------|------|--------|--------|
| ⓪ | [`t0_reference_perf_scatter.md`](t0_reference_perf_scatter.md) | mesure+gain | **INTACT** `11eceeb9…` | ✅ fait |
| ① | [`t1_vent_masse_air.md`](t1_vent_masse_air.md) | O(1) | **neutre** `11eceeb9…` | ✅ fait |
| ② | [`t2_evapotranspiration.md`](t2_evapotranspiration.md) | marginal | **re-figé LARGE** `4a3cfe03…` → D39 vert | ✅ fait |
| ③ | [`t3_abri_spatial.md`](t3_abri_spatial.md) | **+0 % (caché)** | **re-figé** `4ce4ae3c…` | ✅ fait |
| ④ | [`t4_thigmomorphogenese.md`](t4_thigmomorphogenese.md) | négligeable | **re-figé** `d948f648…` | ✅ fait |
| ⑤ | [`t5_pollinisation_dispersion.md`](t5_pollinisation_dispersion.md) | négligeable | **INTACT** `d948f648…` | ✅ fait |
| ⑥ | [`t6_maladies_fongiques.md`](t6_maladies_fongiques.md) | négligeable | **INTACT** `d948f648…` | ✅ fait |
| ⑦ | [`t7_transport_voix.md`](t7_transport_voix.md) | amorti | **re-figé MAÎTRISÉ** `0d3ca606…` | ✅ fait |

## Référence perf + scatter (tronçon ⓪, 2026-06-29 — D32 SOLDÉE)
- **Base mesurée** (`tools/profile_tick.py`, monde smoke 2 tuiles/96 plots/51
  plantes, 52 sem échauffement) AVANT : tick **59.2 ms**, `LightField.compute`
  **34.1 ms** (57.6 %). APRÈS scatter : tick **52.3 ms**, `compute` **25.8 ms**
  (49.4 %). Boucle lumière-sol seule : **×6.0 plancher** (`diag_light_coverage`,
  monde dense 79 % ombré = pire cas ; le monde réel 1600 plots est ~20× plus
  clairsemé → gain réel >> ×6).
- **Golden INTACT** `11eceeb9e80aec108dd46907c7e530e96d6040b486150944c4090c1c90b11ba0`
  (optim pure, bit-à-bit). Verrou : `tests/test_scatter_lumiere_sol.py` (PASS).
  Non-régression : `test_phototropisme`, `test_ombre_maison`, `test_sim_server`
  (207/207) verts.
- **Budget X fixé** : ce tronçon a **baissé** le tick (−12 %). Règle pour ①→⑦ :
  aucun tronçon n'ajoute plus de **~+10 %** au tick complet (≈ +5 ms sur la base
  52 ms) sans justification ; ③ (abri spatial) seul à risque → mesurer seul,
  réutiliser la même bbox/scatter que la lumière (levier 2, mutualisation).

## Masse d'air (tronçon ①, 2026-06-29 — golden NEUTRE)
- **Nouveau module `sim/wind.py`** (62 LDC pur), calqué sur `weather.py` : canaux
  décorrélés `K_WIND/K_DIR/K_GUST` en tranche 90_01x, zéro RNG vivant.
  - `wind_at(seed, week) → WindState(force, direction)` : force de fond (canal +
    saisonnalité hiver-venteux, opposée à `temp_norm`), écrasée haute par
    Tempête/Orage (continuise le dégât ponctuel) ; **direction O(1)** (somme de 3
    sinusoïdes basse fréquence — PAS de marche cumulée O(week), évite ~4 ms/tick
    en fin de partie).
  - `gust_profile` (§2.2 régimes intra-jour, enveloppe SUBTICKS=4 : risées + brise
    de fin de journée) ; `nebulosite_dynamique` (§2.3, le vent chasse la couverture
    figée) — **calculés, NON branchés** (le câblage aval = tronçon ②).
- **Golden INTACT** `11eceeb9e80aec108dd46907c7e530e96d6040b486150944c4090c1c90b11ba0`
  (module non lu par la boucle — vérifié par `test_vent.py::test_non_cable`).
  Non-régression : `test_sim_server` 207/207.
- **Test neuf** `tests/test_vent.py` (18/18) : déterminisme, bornes, saisonnalité
  hiver>été, réactivité Tempête, isolement golden-neutre.
- **Perf** : `wind_at` ~24 µs/call, **plat** quelle que soit la semaine (O(1)) →
  ~0.05 % d'un tick 52 ms même appelé chaque tick au ②. Budget +10 % très tenu.

## Évapotranspiration enrichie (tronçon ②, 2026-06-29 — golden RE-FIGÉ LARGE, D39 vert)
- **Deux pilotes neufs de l'évaporation** greffés dans `tick_hydrology`
  (`fields/ecofields/container.py`, **zéro nouvelle traversée**) : RAYONNEMENT
  `−EVAP_RAD_COEF·(1−nébulosité)` (ciel clair = contre-flux exact de la rosée) +
  VENT `−EVAP_WIND_COEF·vent_masse_air` (balayage de la couche limite). Coefs
  `EVAP_RAD_COEF=0.0042`, `EVAP_WIND_COEF=0.0035` (`constants.py`). Défauts
  rétro-compatibles `nebulosite=1.0`/`vent_masse_air=0.0` → conteneurs pots/bacs
  **bit-identiques**.
- **Nébulosité DYNAMIQUE** : `weather_state` (`sim/weather.py`) lit désormais
  `sim.wind.nebulosite_dynamique(seed, week)` (import local, évite le cycle
  weather↔wind) au lieu de la table figée `NEBULOSITE[kind]` → tout le bloc
  lumière/rosée/thermique bouge ensemble (cœur du re-figeage LARGE).
- **Câblage** : `boucle.py` calcule `vent_force = wind_at(seed, week).force` et le
  passe (+ `nebul`) à `tick_hydrology`.
- **Golden RE-FIGÉ** `4a3cfe030562680bf5af2cc88e01629bee22eba6129909524ae22a5a822729fb`
  (re-figeage LARGE **prévu** par le kickoff). **D39 VERT** : `test_senescence`
  PASS (pommier mort de **sénescence à 59.8 ans**, plus asphyxié à 19,5). Garde-fou
  anti-sécheresse OK : `test_rosee` 10/10, `test_eau` 20/20, `test_croissance`
  67/67, `test_stress_chronique` PASS, `test_sim_server` 207/207, `test_vent`
  19/19 (câblage vérifié).
- **Perf** : +2 lectures/plot dans une boucle existante (marginal). D39 re-rouvert
  puis re-résolu PAR LE FOND dans `DETTE.md`.

## Champ d'abri spatial (tronçon ③, 2026-06-29 — golden RE-FIGÉ MAÎTRISÉ, perf NEUTRE)
- **Nouveau module `fields/abri.py`** (94 LDC pur) : `compute_abri` spatialise la
  masse d'air en `eco.vent` (GridField par plot). Obstacles = MAISON + plantes
  hautes (≥ `ABRI_HAUTEUR_MIN_CM`=80 cm → haie = brise-vent émergent, philo #1).
  Chaque obstacle projette une **capsule SOUS LE VENT** (`_point_in_capsule` de
  `light.py` RÉUTILISÉE + scatter par bbox D32), réduction dégressive le long du
  sillage (`ABRI_REDUCTION_MAX`=0.6, portée 10× hauteur) ; **venturi** (+0.15) en
  frange (passe voisinage 4-conn). **CACHE** sur (obstacles, direction discrétisée
  ~15°) → en régime permanent on ne RE-CALCULE PAS la géométrie, juste la mise à
  l'échelle par `wind_force`.
- **Câblage** : `boucle.py` 2a appelle `eco.tick_abri(...)` (après lumière, avant
  thermique/hydro) ; `tick_hydrology` lit `vent_field=eco.vent[r,c]` (vent local au
  lieu de la masse d'air uniforme du ②) ; `t_min_nuit_at` ajoute le **wind chill**
  `−WINDCHILL_COEF·eco.vent` (un abri réchauffe la nuit, §5.5). Défauts rétro-compat
  → pots/bacs bit-identiques.
- **Golden RE-FIGÉ MAÎTRISÉ** `4ce4ae3cdf77bb79860dcebac5c7cfac9959511227f89eea770e59a2449bfd25`
  (évaporation par plot + wind chill bougent humidité/T_min — re-figeage **prévu** par
  le kickoff). **D39 toujours VERT** : `test_senescence` PASS (pommier 59.8 ans).
  Suites : `test_sim_server` 207/207, `test_eau` 20/20, `test_rosee` 10/10,
  `test_croissance` 67/67, `test_stress_chronique` PASS, `test_vent` **26/26**
  (+7 checks abri spatial : sillage, venturi, direction, cache, calme→nul).
- **PERF (point clé §7B)** : tick **51.3 ms AVANT → 50.9-54 ms APRÈS** = **≈ +0 %**
  (dans le bruit). Le **cache + scatter mutualisé** annulent le coût en régime
  permanent → **PAS d'off-ramp**, ③ implémenté en entier (pas reporté en dette).

## Thigmomorphogénèse (tronçon ④, 2026-06-29 — golden RE-FIGÉ, perf NEUTRE)
- **Gène neuf `port_trapu`** ajouté EN FIN de `GENE_NAMES`/`ADAPTOGENIC_GENES`
  (`plants/genetics.py`) → canal de hash en queue, **gènes existants intacts**.
  Attribut `wind_memory` (`plants/base/instance.py`) = mémoire d'exposition mécanique.
- **Paire plastique `"port_trapu": "wind_memory"`** dans `_EXPR_MEMOIRE`
  (`sim/engine/croissance.py`) : `_update_physiology` intègre `eco.vent.at_plot` en
  `wind_memory` (lerp `WIND_MEMORY_LERP`, ref `WIND_MEMORY_REF`) → `expressed_gene
  ("port_trapu")` glisse vers `1+EXPR_GAIN·wind_memory` (hystérèse TAU_UP/DOWN).
  Semis extérieur endurci, semis intérieur fragile à la transplantation ; priming
  transgénérationnel via `child_expression` existant.
- **Réponse trapu** : `phases.py` divise le gain d'étiolement par `port_trapu`
  (port trapu = entre-nœuds courts, s'étiole moins) → golden NEUTRE à 1.0.
- **Dégât MÉCANIQUE médié** (`_wind_damage`, `sim/engine/mortalite.py`, calqué sur
  `_mediated_damage`) : `sév(vent_local·risée − SEUIL) × (étiolement/port_trapu) ×
  (1−paillage)`. Constantes `WIND_DAMAGE_SEUIL=0.7`, `WIND_SEVERITY_REF=0.8`,
  `WIND_ETIOLE_SUSCEPT=1.5` (`aleas.py`). Câblé `boucle.py` 9b-bis avec
  `gust_peak=max(gust_profile(...))`. Seul le tissu « semis » est visé.
- **Transpiration foliaire (§3)** : dans `_update_physiology`, le vent local amplifie
  `drought_stress ∝ surface foliaire` (`WIND_TRANSPI_COEF=0.25`) → une grande feuille
  au vent souffre plus de la soif.
- **Golden RE-FIGÉ** `d948f648a94be4d5a8227cb28b530ae6be104cf4558bd721431b83f8c5a0440f`
  (re-figeage **prévu** : 2 rejetons portent `port_trapu` + transpiration/dégât/
  étiolement bougent santé & structure). Suites : `test_sim_server` 207/207,
  `test_senescence` PASS (pommier 59.8 ans, **D39 vert**), `test_croissance` 67/67,
  `test_plasticite` (+`test_thigmo_wind_memory`/`test_thigmo_degat_etiole`).
- **PERF** : tick **54.75 ms** (vs ③ ~51-54) = dans le bruit, effets par-plante
  négligeables. Budget +10 % tenu.

## Pollinisation & dispersion anémophiles (tronçon ⑤, 2026-06-29 — golden INTACT, perf neutre)
- **3 effets par-plante** branchés sur `eco.vent` (③) + `vent_dir` (①), philo #2
  (flux vent → contrainte → nouaison/dispersion émergente) :
  1. **Anémophilie** — nouveau module `sim/engine/anemophilie.py` (98 lignes,
     `AnemophilieMixin._tick_anemophilie`) : dépose `pollen_recu` sur les fleurs
     `pollination_mode=="wind"` ∝ vent_local × Σ floraison des congénères **EN AMONT**
     (projection > 0 sur le vecteur d'origine du vent) + auto-anémophilie
     (`ANEMO_AUTO_FRAC`). `_tick_fruits` (decompo.py) lit désormais `pollen_recu` en
     mode `wind` aussi (seul `self` court-circuite à frac=1). Câblé boucle.py 13c-bis.
  2. **Butineurs cloués** — `butineurs.py::_forager_wind_factor(vent_local)` ∈
     [`FORAGER_WIND_FLOOR`,1] atténue les dépôts entomophiles par grand vent local.
  3. **Anémochorie** — trait `seed_dispersal` (`barochore` défaut / `anemochore`) sur
     `PlantBase` ; posé sur Pissenlit/Pâturin/Ortie. `_reproduction` (mortalite.py)
     décale le dépôt génétique `add_species` **SOUS LE VENT** (`_plot_sous_le_vent`,
     ∝ `wind_force`, clampé à la tuile) pour les anémochores → la lignée féral migre.
- **Golden INTACT** `d948f648a94be4d5a8227cb28b530ae6be104cf4558bd721431b83f8c5a0440f`
  (re-figeage **prévu mais non survenu** : `pollen_recu` hors digest + aucun fruitier
  anémophile mûr dans le smoke ; les anémochores ne grènent pas dans la fenêtre
  2 tuiles × 4 ans, ou le dépôt décalé n'altère pas le digest). Mieux que prévu, sûr.
- **Tests** : `test_vent` **36/36** (+10 : anémophile noue sans butineur, calme→0 pollen,
  butineurs cloués décroissants, anémochorie sous le vent vs barochore au pied).
  Suites : `test_sim_server` 207/207, `test_senescence` PASS (pommier 59.8 ans, **D39
  vert**), `test_fruits` 24/24 (branche wind inchangée pour les modes existants),
  `test_biennial` PASS, `test_croissance` 67/67, `test_rosee` 10/10, `test_eau` PASS,
  `test_plasticite`/`test_stress_chronique` PASS.
- **Perf** : tick **53.5 ms** (vs ④ ~54.75) = dans le bruit. Effets O(fleurs²)/espèce
  anémophile en fleur — quelques unités par tuile, négligeable. Budget +10 % tenu.

## Vent × maladies fongiques (tronçon ⑥, 2026-06-30 — golden INTACT, perf neutre)
- **Double tranchant greffé sur `fungal_disease`** (`sim/effects/perturbations.py`),
  philo #2 (flux vent → contrainte → pression fongique émergente), sans bonus/malus
  direct sur la plante :
  1. **Assèchement protecteur** : `p *= max(0, 1 − FUNGAL_VENT_DRY·min(1,vent_local))`
     — un feuillage bien venté (`eco.vent[r,c]` du ③) sèche, le champignon manque
     d'eau → **la ventilation est un remède** (espacement/taille/brise-vent ajouré),
     pédagogie aération permaculture.
  2. **Dispersion des spores** : nouveau helper `_spore_load` somme l'`infection_memory`
     (foyer ≥ `FUNGAL_INOC_SEUIL`=0.4) des voisins placés **AU VENT** (projection > 0
     sur `wind_vec`, convention `_wind_from_vector`), dans le **voisinage 1-conn DÉJÀ
     calculé** (`plots_within_radius` réutilisé — zéro passe spatiale neuve, garde-fou
     perf). `p *= 1 + FUNGAL_SPORE_GAIN·spore` → l'inoculum voyage **sous le vent**.
  - Constantes `FUNGAL_VENT_DRY=0.7`, `FUNGAL_SPORE_GAIN=0.8`, `FUNGAL_INOC_SEUIL=0.4`
    (`constants.py`, ré-exportées `fields/__init__.py`). **Défauts neutres**
    (`vent_local=0`, `wind_vec=(0,0)`) → bit-identique à l'avant-⑥.
  - **Câblage** : `apply_disturbances(... vent_dir, vent_force)` calcule `wind_vec`
    une fois et lit `eco.vent.at_plot` par plante ; `boucle.py` passe `vent_dir`/
    `vent_force` (①) au site d'appel.
- **Golden INTACT** `d948f648a94be4d5a8227cb28b530ae6be104cf4558bd721431b83f8c5a0440f`
  (re-figeage **prévu mais non survenu**, comme au ⑤). Mécanisme bien EXERCÉ dans le
  smoke (`vent_local` atteint 1.24, `infection_memory` 0.44 > seuil, 6 plant-événements
  avec inoculum sous le vent) mais **aucun flip discret** du tirage `_hash_noise < p`
  → digest bit-identique. Neutre-mais-actif, sûr.
- **Tests** : `test_vent` **42/42** (+6 ⑥ : foyer au vent transmet l'inoculum,
  inversion du vent inverse la source, sous-seuil/calme → 0 ; **assèchement** : 38
  infections confiné → 13 venté = −66 %, ≈ `FUNGAL_VENT_DRY`). Suites :
  `test_sim_server` 207/207, `test_senescence` PASS (pommier 59.8 ans, **D39 vert**),
  `test_croissance` 67/67, `test_rosee` 10/10, `test_eau` 20/20,
  `test_stress_chronique` PASS.
- **Perf** : tick **51.55 ms** (vs ⑤ ~53.5) = dans le bruit. `_spore_load` ne scanne
  que le voisinage 1-conn existant et ne s'active qu'autour d'un foyer infecté →
  négligeable. Budget +10 % tenu.

## Transport éolien de la litière & voix (tronçon ⑦, 2026-06-30 — golden RE-FIGÉ MAÎTRISÉ, perf neutre)
- **Nouveau module pur `fields/ecofields/transport.py`** (≈55 LDC pur,
  `tick_transport`) : charrie la litière LÉGÈRE (`TRANSPORT_TISSUS=("feuille",
  "herbace")`) des plots EXPOSÉS vers leur voisin SOUS LE VENT **SI ce voisin est
  plus abrité** (`vent[d] > vent[a]`, §5.6) → la matière s'amasse derrière un
  brise-vent comme une congère (philo #2 : flux vent → contrainte → hétérogénéité
  du sol émergente). Bois/fruits/`diffus` (lourds) restent au sol.
  - **DÉTERMINISME (philo #3, zéro RNG)** : SNAPSHOT des masses donneuses AVANT
    mutation (double buffer comme `GridField.diffuse`) → ordre de parcours
    indifférent. Direction discrétisée en **un** voisin cartésien (`_aval`).
    **Conservation stricte** : on redépose exactement la masse retirée (`pris`).
  - **PASSE CONDITIONNELLE (perf, levier 5 §7B)** : no-op strict (liste vide) tant
    que `wind_force < TRANSPORT_SEUIL`=0.35 → **coût NUL les jours calmes**. Quand
    elle tourne = une seule passe O(plots), LIT `eco.vent` (③) sans capsule ni
    scatter cher. Émet le signe `🍃` si la masse nette charriée ≥ `TRANSPORT_LOG_SEUIL`=0.05.
  - Constantes `TRANSPORT_SEUIL/FRAC/TISSUS/LOG_SEUIL` (`constants.py`, ré-exportées
    via `import *`). Helpers conteneur : `retirer_litiere` (retrait par tissu,
    conservation) + `tick_transport` (délégation). Câblé `boucle.py` 15d (APRÈS tous
    les dépôts de litière du tick, avant transition hivernale).
- **Voix narratives** (read-only, HORS tick) : nouvel événement `transport_litiere`
  parsé du marqueur `🍃` (`sim/evenements.py`) → carnet (`sim/carnet.py`,
  `CONCEPT_DE`/gabarit : « les feuilles s'amassent le long de l'abri » descriptif →
  interprétatif « là où le vent ralentit, la matière s'amasse et nourrira ce coin »
  au seuil de maîtrise décompo). Le signe `🍃` est diégétique, pas de narrateur
  omniscient. Le sign « le vent tourne » (Tempête, `weather.py`) couvre déjà le
  préavis météo.
- **Golden RE-FIGÉ MAÎTRISÉ** `0d3ca606c815c9efb99e8e438a2e7c47bf7abd4d17dade8de0f51b892be1d6ad`
  (re-figeage **prévu** par le kickoff). Divergence **localisée et bénigne** : sur
  les 41 lignes de digest qui bougent, le SEUL champ modifié est `drought_memory`
  (4ᵉ–6ᵉ décimale) — la litière déplacée change la matière organique de surface par
  plot → micro-variation de la rétention d'humidité locale → dérive infime de la
  mémoire de soif. **Aucun** changement structurel (plante, stade, santé, position,
  gènes intacts). Transport fire 13× dans le smoke. Voix = read-only → n'ont pas
  touché le golden.
- **Tests** : `test_vent` **54/54** (+12 ⑦ : feuille charriée/bois immobile/masse
  conservée/marqueur émis/passe calme sautée/pas de remontée amont/déterminisme +
  voix parsée → carnet descriptif→interprétatif). Suites : `test_sim_server`
  207/207, `test_senescence` PASS (pommier 59.8 ans, **D39 vert**), `test_journal`
  15/15, `test_carnet` 19/19, `test_structures` 80/80.
- **Perf** : tick **54.1 ms AVEC transport vs 51.9 ms SANS** = **+2.2 ms (+4.2 %)**
  dans le pire cas (smoke riche en litière, vent fréquent) ; les jours calmes la
  passe est SAUTÉE (coût nul). Budget +10 % tenu.

## Boucle de travail (rappel CLAUDE.md)
Lancer `tN` → coder → **mesurer ms/tick avant/après** (budget §7B) → golden (intact
ou re-figeage annoncé) → MAJ ce fichier → commit → `/clear` → lancer `tN+1`.

## Clôture du sprint
- Rouvrir/MAJ **D39** dans `DETTE.md` (récidive via rosée, re-résolu par le fond).
- Solder **D37** + **D32** (scatter). MAJ `journal.md` (index) + entrée `journal/NN_…`.
- Supprimer `HANDOFF.md` (devenu obsolète).

## REPRISE (démarrage à froid)
« lis `sprints/sprint_vent_evapotranspiration/00_etat.md` puis
`t7_transport_voix.md` » → exécuter le tronçon ⑦ (transport de litière & neige sous
le vent §5.6 + voix narratives du vent ; lit `eco.vent[r,c]` posé au ③ + direction).
Tronçons ⓪ (réf perf + scatter D32, golden `11eceeb9…`), ① (masse d'air
`sim/wind.py`, golden neutre `11eceeb9…`), ② (évapotranspiration enrichie +
nébulosité dynamique, golden re-figé LARGE `4a3cfe03…`, D39 vert), ③ (abri spatial
`fields/abri.py` + wind chill, golden re-figé `4ce4ae3c…`, **perf +0 % grâce au
cache**, PAS d'off-ramp), ④ (thigmomorphogénèse : paire `port_trapu↔wind_memory`,
dégât mécanique médié `_wind_damage`, transpiration foliaire, golden re-figé
`d948f648…`, perf neutre), ⑤ (pollinisation & dispersion anémophiles :
`sim/engine/anemophilie.py`, butineurs cloués, trait `seed_dispersal`/anémochorie,
golden **INTACT** `d948f648…`, perf neutre) et ⑥ (vent × maladies fongiques :
`fungal_disease` enrichie — assèchement protecteur + dispersion des spores sous le
vent `_spore_load`, golden **INTACT** `d948f648…`, perf neutre) = ✅ faits.
