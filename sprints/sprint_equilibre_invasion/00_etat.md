# Sprint « équilibre de l'invasion d'adventices » — état vivant (carnet de bord)

> Carnet de conception (`/conception`, dette **D69**). Reprise à froid = lire
> `CLAUDE.md` + ce fichier + `docs/faune/trophique/conception_equilibre_invasion.md`.
> **CONCEPTION FIGÉE (2026-07-06)** — design ARBITRÉ D1-D12, découpage ①-⑧ validé,
> doc + kickoffs 01-08 écrits. **PRÊT pour `/sprint-auto sprint_equilibre_invasion`.**

## Carte des tronçons (un seul sprint, perf-first, vue en dernier)
- **01** banc `config="propre"` + `tools/diag_population.py` [golden INTACT] ✅ FAIT 2026-07-06
- **02** recalibrage freins férals — onset ~2-3 saisons, N~650/8 tuiles [golden RE-FIGÉ, seul] ✅ FAIT 2026-07-08 (N an6=613, knob `GERM_PRESSION_FERALE=0.30`)
- **03** paillage moteur — champ + geste `pailler` + germ↓/ET↓/graines↑/→OM [golden INTACT] ✅ FAIT 2026-07-08 (champ `paillage`, geste `pailler`, 4 effets, golden `33c0ea6f…` inchangé)
- **04** matériau — `broyer`→BRF + récolte paille → stock + 3 natures [INTACT] ✅ FAIT 2026-07-08 (golden `33c0ea6f…` inchangé)
- **05** catalogue blé/chanvre/sapin + 5 voix [INTACT] ✅ FAIT 2026-07-08 (golden `33c0ea6f…` inchangé)
- **06** paillage ↔ vie macro (abri) [golden INTACT] ✅ FAIT 2026-07-08 (golden `33c0ea6f…` + population_hash `1aa4997d…` INCHANGÉS)
- **07** planter+pailler par maîtrise (auto-paillage) [INTACT] ✅ FAIT 2026-07-08 (golden `33c0ea6f…` + population_hash `1aa4997d…` INCHANGÉS)
- **08** vue Godot (pailler/broyer + rendu mulch + abri) + démo sud [golden INTACT] ✅ FAIT 2026-07-08 (golden `33c0ea6f…` + population_hash `1aa4997d…` INCHANGÉS, pont 0.5.20, build C# vert)

## Sujet
Rendre l'invasion d'adventices **infléchissable par le joueur via le milieu**
(philo #1), recalibrer les freins férals pour le monde réel **8 tuiles**, et
fournir un **banc de test « monde propre »** (observer les cultivées seules +
isoler la perf à N maîtrisé).

## Diagnostic (lecture seule, FAIT le 2026-07-06)
- Monde `config="full"` : 53 cultivées plantées → **balayées en < 1 saison**
  (dès s26 il ne reste que 8 haricots, tout le reste = pionnières de la seedbank).
- Trajectoire N (an0→5, seed serveur) : 53 → 336 → 603(an1 été) → 807(an3) →
  1043(an5), **oscillation saisonnière ~2×** (807 s156 → 386 s182), **enveloppe
  d'été qui grimpe encore** → N non borné proprement à 8 tuiles.
- Cause calibrage : vis A `COUVERTURE_GERM_EXP=4.0` + `COUVERTURE_ADVENTICE_SEUIL`
  (cutoff dur) dans `sim/succession.py`, calibrés **2 tuiles** au sprint D66③
  (« ~190 pour 2 tuiles »). Backstop `sim/capacite.py` cap 800/tuile ne fire
  jamais (max ~178/tuile).

## Mécanismes réels repérés (source de vérité)
- **Levée férale** (`succession.py:222+`) : par plot libre, `niche` = f(lumière,
  densité racinaire voisine, perturbation, mémoire sol, fertilité), puis
  × `(1-couverture)^4`, cutoff dur si `couverture ≥ seuil`, × cloches pH & T_sol.
  Grains PLANTÉS levés en priorité (`_lever_grains_en_attente`).
- **Banque férale** (`fields/seedbank.py`) auto-alimentée : `tick_disturbance_
  enrichment` (perturbation→pioneer), `tick_late_succession_enrichment`
  (OM→fixatrice/graminée/competitor), `tick_plant_production` (plantes mûres→
  graines locales). Vieillissement lent `SEED_VIABILITY_LOSS=0.998/sem`.
- **Paillage** (`paillage` rondelle) : ne protège QUE du vent
  (`mortalite.py`/`aleas.py`, `PAILLAGE_PROTECT=0.25`). **N'agit PAS sur la
  germination** → levier permacole anti-adventice ABSENT (trou majeur).
- **Gestes milieu existants** : `becher`(+perturbation), `grelinette`(préserve),
  `deraciner`/`ecraser`(directs, coûteux #1), couvre-sol→`couverture_sol`(gate).

## Décisions arrêtées (Nico, 2026-07-06)
- **D1 — Levier principal = PAILLAGE + épuisement de banque.** Le mulch supprime/
  atténue la levée férale sous la parcelle ET **accélère le vieillissement des
  graines enfouies** → effet durable (mulcher longtemps épuise la banque locale).
  Philo #1 (agir sur le milieu) / #2 (flux mulch → contrainte → moins de levée).
- **D2 — Garder l'invasion RÉELLE, donner le TEMPS.** Un jardin non tendu retourne
  à la friche (philo #6) ; on **ralentit l'onset** (friche en ~2-3 saisons, pas
  < 1) pour laisser au joueur le temps d'agir par le milieu, et on **borne N plus
  bas à 8 tuiles** (perf). PAS de nerf qui rende les cultivées invincibles (#2
  interdit le bonus direct). **Re-fige le golden** (localisé, annoncé).
- **D3 — Banc « monde propre » = preset `config="propre"`** dans `cmd_init`
  (mêmes tuiles + maison, seedbank férale vidée + succession férale coupée),
  réutilisable au F5 (observation cultivées), en tests et par le profileur.
- **Cadre philo acté** : objectif = AJOUTER des leviers milieu + donner du temps,
  PAS neutraliser l'invasion. Nuance diagnostic : la mort précoce des annuelles
  fragiles (tomate/basilic : froid<5°C + maladie) N'EST PAS que de la compétition
  férale — on ne buffe pas les cultivées (#2), on agit sur le milieu.

## Décisions arrêtées — round 2 (Nico, 2026-07-06)
- **D4 — Mulch = CHAMP par plot `paillage`** (∈[0,1] profondeur), pas la rondelle
  par tuile. Lu par la germination (succession) et le vieillissement des graines
  (seedbank). Tick : décroissance → `om_stable` + rétention d'humidité. Coût
  ~gratuit (scalaire/plot, patron `couverture_sol`).
- **D5 — Geste `pailler`** (zone, coût Vigueur modéré, planification). Source de
  matière **abstraite en v1** (mais le mulch se décompose en OM → déjà connecté
  sol/germination/humidité/banque) ; hook pour sourcer du compost/litière plus tard.
- **D6 — Cible de recalibrage** : friche en **~2-3 saisons** (pas <1), plateau N
  **~600-700 à 8 tuiles** (vs 1043+). Knobs : `COUVERTURE_GERM_EXP`, enrichissement
  seedbank, base de la vague de printemps — PAS le cutoff dur. Mesuré par le diag
  trajectoire avant/après. Re-fige golden (localisé, annoncé).

## Décisions arrêtées — round 3 (Nico, 2026-07-06) — ÉLARGISSEMENT
- **D5 SUPERSÉDÉE par D9** (matériau plus abstrait).
- **D7 — Démo monde 8 tuiles** : ajouter une **zone paillée plein sud** avec
  **tomate/basilic/poivron/tournesol** (démonstrateur du levier — ce sont
  justement les cultures qui mouraient). Modifie `build_world_full` (hors golden
  smoke 2 tuiles → golden INTACT).
- **D8 — Paillage ↔ ÉVAPOTRANSPIRATION** : le mulch **réduit l'évaporation**
  (rétention d'humidité), patron `couverture_sol`→évaporation déjà en place
  (sprint LUXURIANCE / VENT). Le mulch tempère aussi le sol (moins d'ET).
- **D9 — Matériau du paillage SOURCÉ** (révise D5) : deux voies —
  **(a) BRF par BROYAGE de bois** (geste `broyer` sur `bois_restant`/pile de bois),
  **(b) RÉCOLTE de plantes à paille**. La **nature du mulch dépend de la source**
  (BRF ligneux / paille / aiguilles) → propriétés distinctes (décompo, C:N,
  humidité, faune, acidité). Hook mycélium (BRF nourrit les saprophytes,
  cf. [[design_mycelium_interconnexions]] — non implémenté, simple hook).
- **D10 — Catalogue élargi** : **blé, chanvre, sapin** (+ **5 voix chacun**, règle
  catalogue « l'espèce sert l'idée » + « toutes ses voix »). Sources paille/BRF.
- **D11 — Paillage = ABRI pour la faune** : les champs de population lisent
  `paillage` comme **habitat/abri** (les ombrophiles n'aiment pas le plein soleil
  sans abri → s'abritent sous le mulch). Pont avec la vie macro (`PopulationField`).
- **D12 — Couplage planter + pailler par MAÎTRISE** : au-dessus d'un palier de
  maîtrise, **planter auto-paille** ; la **nature du paillage dépend de la plante
  ET de la maîtrise** de cette plante (on paille systématiquement quand on plante,
  une fois qu'on maîtrise). Lie [[design_voix_narratives]]/paliers (D12 maîtrise).
- **NOTE PERF** : ce sprint est un **détour justifié par la perf** (invasion →
  N non borné → tick ∝ N, philo #4). **REVENIR à la perf pure APRÈS** : D67 (LOD
  émetteurs d'ombre) + LightField, redevenu poste #1 depuis la mémoïsation 761bbe9.

## Découpage ÉLARGI proposé (perf-first, vue Godot en dernier) — à valider
- **① Banc « monde propre » + diag outillé** : preset `config="propre"` (seedbank
  férale vide + succession off) + `tools/diag_population.py` promu (mesure onset+
  plateau, réutilisé partout). Fondation de mesure. [golden INTACT]
- **② Recalibrage des freins férals** (D6) : onset ~2-3 saisons, N ~650/8 tuiles,
  via couverture/enrichissement seedbank. Mesuré ① avant/après. [golden RE-FIGÉ
  localisé annoncé — SEUL re-figeage du sprint]
- **③ Paillage moteur** : champ `paillage` par plot + geste `pailler` + effets
  écolo — germination férale↓, vieillissement graines↑, **évapotranspiration↓/
  humidité↑** (D8), décompo→`om_stable`. [golden INTACT — paillage=0 au repos]
- **④ Matériau du paillage** (D9) : geste `broyer` (bois→**BRF**), récolte de
  plantes à paille → **stock de mulch**, `pailler` le consomme ; **nature** du
  mulch (BRF/paille/aiguilles) = propriétés distinctes. Hook mycélium. [INTACT]
- **⑤ Catalogue paille/BRF** (D10) : **blé, chanvre, sapin** + **5 voix** chacun. [INTACT]
- **⑥ Paillage ↔ vie macro (abri)** (D11) : `PopulationField` lit `paillage` comme
  habitat/abri (ombrophiles au plein soleil). [golden INTACT — paillage=0 au repos]
- **⑦ Couplage planter+pailler par maîtrise** (D12) : auto-paillage à la plantation
  au-dessus du palier, nature selon plante+maîtrise. [golden INTACT]
- **⑧ Vue Godot + démo** (D7) : `pailler`/`broyer` cliquables, rendu mulch+BRF au
  sol, abri faune visuel, **zone paillée sud (tomate/basilic/poivron/tournesol)**
  dans `build_world_full`, pont (bump protocole), banc F5. [golden INTACT]

## §REPRISE
Design arbitré D1-D12 (D5 supersédée). Reste : valider le découpage ÉLARGI ①-⑧ +
le modèle de « nature du mulch » avec Nico → sur accord, PHASE B (doc
`docs/faune/trophique/conception_equilibre_invasion.md` + kickoffs 01-08, un fichier à la fois). Puis
commit + maj dette D69 (conçu) + message /clear pour `/sprint-auto`. NE PAS OUBLIER :
revenir à la perf pure (D67/LightField) après ce sprint.

## Coût perf estimé
- Paillage→germination : lecture d'une rondelle déjà comptée par plot → ~gratuit.
- Recalibrage : change des constantes → neutre en coût, mais **re-fige golden**.
- Banc : hors tick (config d'init) → neutre.

## §REPRISE — EXÉCUTION
**Tronçon ① FAIT (2026-07-06)** — golden INTACT (`84d35983…`), test_population
INTACT (`c2b4a01d…`). Livré :
- `tools/simserver/commands.py` : preset `config="propre"` dans `cmd_init` (monte
  `build_world_full`, vide la seedbank férale via helper `_vider_seedbank_ferale`,
  pose `game_state["feral_off"]=True`).
- `sim/succession.py` : `if game_state.get("feral_off"): return log` APRÈS la levée
  des grains plantés (germination férale spontanée coupée, grains plantés préservés).
- `tools/diag_population.py` créé (trajectoire N, top-6 espèces, tuile_max, tous les
  26 ticks ; `--config full|propre`).

Vérif : `--config full` s26 → N=336 avec les 4 adventices (invasion réelle) ;
`--config propre` s26 → N=127 SANS aucune adventice férale (Poa/Bursa/Medicago/
Taraxacum absentes). NOTE : en `propre`, N monte quand même (~421 à l'an 3) via
la **propagation stolonifère du Clover** (`_reproduction`, cultivée plantée par
`build_world_full`) — ce n'est PAS de l'invasion férale, et le kickoff demande de
ne garder QUE les cultivées de `build_world_full` (Clover en est une). Coupure
férale conforme au spec ; si Nico veut un banc « N strictement plat » il faudra
aussi geler la repro végétative (hors scope ①).

**Tronçon ② FAIT (2026-07-08)** — golden RE-FIGÉ (annoncé, seul re-figeage du
sprint), test_population RE-FIGÉ (même cause : moins de vie férale). Livré :
- `sim/succession.py` : nouveau scalaire GLOBAL `GERM_PRESSION_FERALE = 0.30`
  appliqué à la levée férale (`niche *= GERM_PRESSION_FERALE` après la vis A
  couverture). C'est le VRAI knob de plateau : la banque férale SATURE sur sol
  mûr → la germination est bornée par la NICHE, pas par les `SEED_*_GAIN` (d'où
  leur insensibilité) ni par la vis A seule (qui ne mord que sur les plots
  moyennement couverts). Baisser ce scalaire réduit UNIFORMÉMENT la pression
  férale. `COUVERTURE_ADVENTICE_SEUIL` (cutoff dur) et `capacite.py` intacts.
- `tests/golden_hash.txt` : `84d35983…` → `33c0ea6f…` (re-figé).
- `tests/population_hash.txt` : `c2b4a01d…` → `1aa4997d…` (re-figé même cause).

Trajectoire mesurée (`diag_population --config full`, seed serveur) — cible
atteinte (N plateau ∈ [600,700] à l'an6, onset ~2 saisons, pas < 1) :

| semaine        | AVANT (baseline) | APRÈS (0.30) |
|----------------|------------------|--------------|
| s26  (an1 été) | 336              | 225          |
| s78  (an2 été) | 603              | 565          |
| s130 (an3 été) | 807              | 424          |
| s234 (an5 été) | ~                | 485          |
| s260 (an5 hiv) | 1043             | 596          |
| s262 (an6 pri) | (non borné, ↗)   | **613**      |

Cultivées de `build_world_full` persistent nettement plus longtemps (Bean→s104,
Sunflower→s262) → onset ralenti conforme (philo #6 : la friche revient, mais on
laisse le temps d'agir). Enveloppe hiver monte encore doucement (417→613 sur 5
ans) mais PLAFONNE ~600 au lieu de diverger. Aucun buff des cultivées (#2).
Suite verte hors `test_epaisseur_500ans` (INTERDIT).

**Tronçon ③ FAIT (2026-07-08)** — golden INTACT (`33c0ea6f…`, hash post-②
inchangé : le champ naît à 0, le smoke n'appelle jamais `pailler` → tous les
facteurs ×1). test_population INTACT. Livré :
- `fields/ecofields/paillage.py` (créé) — `PaillageMixin` : champ `paillage`
  ∈[0,1] par plot + `tick_paillage()` (décroissance `PAILLAGE_DECAY` → reversée à
  `om_stable` via `PAILLAGE_OM_W`). Nul au repos → no-op strict.
- `fields/ecofields/container.py` — mixin branché, champ déclaré+init dans
  `__post_init__`, exposé au registre `get_field` (overlay F6/pont).
- `fields/ecofields/constants.py` — `PAILLAGE_DECAY/OM_W/GERM_SEUIL/AGING_BOOST/
  EVAP_FRAC/DOSE` (placeholders, calibrage F5).
- `sim/succession.py` — germination férale : cutoff dur si `paillage ≥
  PAILLAGE_GERM_SEUIL`, sinon `niche *= (1 − paillage)` (frein gradué). Paillage=0
  → ×1.0.
- `fields/ecofields/hydrologie.py` — évaporation : terme `+(1−evap)·
  PAILLAGE_EVAP_FRAC·paillage` (barrière, patron couverture). Paillage=0 → neutre.
- `fields/seedbank.py` — `tick_aging(paillage_field=None)` : sous mulch,
  `SEED_VIABILITY_LOSS ** (1 + SEED_AGING_BOOST·paillage)` (banque épuisée plus
  vite). Champ absent/nul → exposant 1 → inchangé. Câblé depuis `sol.py`.
- `sim/actions/gestes.py` + `couts.py` + `__init__.py` — geste `pailler(...,
  nature="paille", stock=None)` binaire (patron `arroser`), coût MODÉRÉ. `nature`/
  `stock` POSÉS mais INERTES (④ = matériau).
- `sim/engine/boucle.py` — `eco.tick_paillage()` en 15e (après les lecteurs).
- `sim/geste_corpus.py` + `outil_corpus.py` — fiches encyclopédie `pailler`
  (geste) + `paillage` (outil), 3 niveaux (garde-fou voix : toute clé classée a une
  fiche — sinon `test_encyclopedie` rouge).
- `tests/test_paillage.py` (créé) — 17 checks verts (geste, germ étouffée, décompo→
  om, ET freinée, aging accéléré, invariant repos).
- `tests/simserver/morts.py` — FIX d'un test FLAKY PRÉEXISTANT (indépendant de ③,
  vérifié sur checkout propre : 3/8 succès) : la compa déterminisme post-déracinage
  lisait le snapshot BRUT incluant `rss_mo` (RSS OS du sous-process, non
  déterministe) ; on neutralise `_PERF_VOLATILE` avant la compa (même filtre que le
  harness). ③ a juste nudgé la mémoire → révélé le flake.

NON concerné : C# (③ moteur Python pur, aucun build). F5 : rien à valider ce
tronçon (vue = ⑧). Reste ④ (matériau : `broyer`→BRF, récolte paille → stock, natures).

**Tronçon ④ FAIT (2026-07-08)** — golden INTACT (`33c0ea6f…`, hash post-② inchangé :
tout est event-driven, nature "" au repos → NATURE_NEUTRE → lecteurs bit-identiques).
Suite ENTIÈRE verte hors `test_epaisseur_500ans` (INTERDIT). Livré :
- `fields/ecofields/constants.py` — `NATURES_MULCH` (paille/brf/aiguilles data-driven :
  decay/humidite_w/allelo/ph_shift/vers_bois/fongique), `NATURE_NEUTRE`,
  `BROYAGE_RENDEMENT`, `RECOLTE_MULCH_RENDEMENT`.
- `fields/ecofields/paillage.py` — `nature_at` (bounds-safe, repos → NEUTRE),
  `poser_mulch` (dose + nature du plot), `tick_paillage` nature-aware : décompo ∝ decay ;
  reversement SELON nature — BRF → litière `bois` (route la FAIM D'AZOTE `FAIM_N_TISSUS`
  + le MYCÉLIUM `bois_fresh_at`, zéro code neuf), paille/aiguilles → `om_stable` ;
  aiguilles → poussée pH↓ (patron amendement) ; mulch effacé → nature oubliée.
- `fields/ecofields/container.py` — grille `paillage_nature` (chaînes, "" au repos).
- `fields/ecofields/hydrologie.py` — rétention d'évaporation × `humidite_w`.
- `sim/succession.py` — frein allélopathique extra `niche *= 1 − allelo·paillage` (aiguilles).
- `sim/actions/paillage.py` (créé) — `mulch_stock` (jauge par nature dans `game_state`),
  `stock_disponible`/`prelever_stock`, `broyer` (bois_restant squelette → stock brf,
  gradué), `recolter_paille` (espèce `mulch_source` → stock paille/aiguilles ; None → 0).
- `sim/actions/gestes.py` — `pailler` CONSOMME le stock de la nature (refus amont si vide,
  débité APRÈS paiement complet) + `poser_mulch`. Import de `.paillage`.
- `sim/actions/{couts,__init__}.py` — geste `broyer` (MODÉRÉ, objets broyage/broyeur) +
  ré-exports (mulch_stock/stock_disponible/prelever_stock/broyer/recolter_paille).
- `plants/base/familles.py` — attribut de classe `mulch_source` (défaut None ; blé/chanvre/
  sapin le posent au ⑤). LU seulement par recolter_paille (event-driven) → golden neutre.
- Voix encyclopédie (garde-fou `test_encyclopedie` 68/68) : geste `broyer`
  (`geste_corpus`), technique `broyage` (`technique_corpus` + set TECHNIQUES), outil
  `broyeur` (`outil_corpus`).
- `tests/test_paillage.py` — section [1] adaptée (stock requis) + section [7] matériau
  (broyer/recolter_paille/BRF→bois/aiguilles→pH/paille→humus/oubli nature) → 27/27 OK.
- FIX collatéral : `test_eau` cassait (IndexError) car `nature_at` indexait la grille
  brute alors que la succession itère les plots de la TUILE (≥ eco) ; `nature_at` est
  maintenant bounds-safe comme `GridField.at_plot` (hors grille → NEUTRE).

NON concerné : C# (④ moteur Python pur, pont/vue = ⑧). F5 : rien à valider ce tronçon.
Décision de design imprévue : au lieu d'un couplage neuf « BRF → retire du N »,
la décompo du BRF DÉPOSE de la litière `bois`, ce qui active AUTOMATIQUEMENT la faim
d'azote (`FAIM_N_TISSUS`) ET nourrit le mycélium (`bois_fresh_at`) — interconnexion via
les lecteurs existants, aucun code de couplage neuf. `NATURES_MULCH["brf"].fongique`
reste un simple marqueur informatif (l'effet fongique réel passe par `vers_bois`).

**Tronçon ⑤ FAIT (2026-07-08)** — golden INTACT (`33c0ea6f…`, hash post-② inchangé :
les 3 espèces sont HORS smoke 2 tuiles → jamais instanciées au golden). Suite ENTIÈRE
verte hors `test_epaisseur_500ans` (INTERDIT), dont `test_sim_server` 245/245 (le pont
voit les 3 espèces). Livré — 3 espèces, chacune COMPLÈTE (« l'espèce sert l'idée » +
« toutes ses voix ») :
- `plants/species/mulch_sources.py` (créé, 105 LDC) — **Blé** (`Wheat`, Poaceae,
  annuelle, `mulch_source="paille"`) + **Chanvre** (`Hemp`, Cannabaceae NEUVE déclarée à
  l'espèce, annuelle haute étouffe-adventice, `mulch_source="paille"`). Anémophiles
  (pas de retombée butineurs), stades semis→…→mature, HORS golden → NEUTRE.
- `plants/perennials.py` — **Sapin** (`FirTree`, Pinaceae NEUVE, conifère PERSISTANT
  `deciduous=False`/`evergreen`, `ph_opt=5.5` acidophile, `mulch_source="aiguilles"`,
  `age_curve` conifère lent 250 ans). Ombre projetée toute l'année (levier nord).
  Ligneux → sa mort réserve `bois_restant` → `broyer` → BRF (interconnexion ④, zéro
  code neuf).
- `plants/species/__init__.py` + `plants/__init__.py` + `plants/catalogue.py` —
  ré-exports + clés `ble`/`chanvre` (PLANT) et `sapin` (PERENNIAL).
- **5 voix** : (1) **encyclopédie** — 3 fiches 3-niveaux `sim/encyclopedie_corpus.py`
  (`test_encyclopedie` 68/68, `len(FICHES)` 35→**38**) ; (2) **carnet** — événements de
  cycle (germination/floraison/récolte/mort) mappés génériquement par `CONCEPT_DE`
  (aucun code par espèce, patron de TOUTES les espèces) ; (3) **pages secrètes** —
  P30 (chanvre plante-service, concept `paillage`) + P31 (sapin & sol acide, concept
  `sol`) dans `sim/pages_corpus.py` (`test_pages` 58/58, corpus 29→**31**, P01..P31) ;
  (4) **magazine** — offre famille DÉRIVÉE du catalogue (aucune entrée par espèce ;
  `test_magazine` 23/23) ; (5) **événements** — marqueurs de ledger génériques
  (`test_evenements` 20/20) via les stades semis/floraison/récolte.
- `tests/test_catalogue_mulch.py` (créé, 20/20) — présence catalogue + germination,
  nature de mulch, récolte→stock paille/aiguilles, sapin mort→BRF par broyage, voix
  encyclopédie. `tests/test_encyclopedie.py` (35→38) + `tests/test_pages.py` (29→31,
  range de sur-tirage 30→40) recalibrés.

Décision imprévue : la nature du mulch du modèle ④ n'a que 3 valeurs (paille/brf/
aiguilles). Le chanvre donne une paille de FIBRE plus durable que la céréale — nuance
rangée sous "paille" (pas de 4ᵉ nature dédiée), la durabilité reste DIÉGÉTIQUE
(encyclopédie N3), pas mécanique. Signalé.

NON concerné : C# (⑤ moteur Python pur ; le pont sérialise le catalogue → vu par
`test_sim_server`, mais aucun build C# nécessaire ; rendu = ⑧). F5 : rien à valider ce
tronçon (assets/rendu des 3 espèces = ⑧).

**Tronçon ⑥ FAIT (2026-07-08)** — golden INTACT (`33c0ea6f…`, hash post-② inchangé)
ET **population_hash INTACT** (`1aa4997d…`) : le couplage naît neutre (paillage=0 au
repos → terme d'abri nul → habitat bit-identique). Suite ENTIÈRE verte hors
`test_epaisseur_500ans` (INTERDIT). Le mulch devient un ABRI (D11) : les guildes
OMBROPHILES du sol colonisent les zones paillées. Livré :
- `fields/ecofields/constants.py` — nouvelle colonne `abri_w` dans `NATURES_MULCH`
  (BRF 1.0 > paille 0.7 > aiguilles 0.6 : un mulch volumineux abrite mieux) +
  `NATURE_NEUTRE.abri_w=0.0` (garde-fou golden au repos).
- `fields/population/resources.py` — constante `PAILLAGE_ABRI_W=0.5` + décorateur
  `_avec_abri_paillage(base_fn)` : `habitat += PAILLAGE_ABRI_W·abri_w(nature)·paillage`,
  borné [0,1]. Lit `eco.paillage`/`eco.nature_at` À TRAVERS `eco` (aucun import inverse
  `fields.population → ecofields` — pas de cycle de couche). Robuste pré-③ (`getattr`).
- `fields/population/registry.py` — 5 guildes ombrophiles décorées : `limace`,
  `lombric`, `cloporte`, `carabe`, `herisson` (habitat_fn wrappée). Import du décorateur.
- `tests/test_paillage.py` — section [8] (abri : habitat ombrophile ↑ sous mulch,
  BRF>paille, plot non paillé inchangé, invariant repos bit-identique) → 39/39 OK.
- DÉCALAGE : la population ticke AVANT `tick_paillage` (boucle L398 vs L487) → elle lit
  le paillage de la SEMAINE PRÉCÉDENTE (décalage uniforme, déterministe, pas de RNG).
- Tailles LDC pur : resources 270, registry 233 (bande verte ≤300).

NON concerné : C# (⑥ moteur Python pur ; rendu abri = ⑧). F5 : rien à valider ce
tronçon (visuel faune sous mulch = ⑧). Décision de design : liste ombrophile =
faune de SOL (carabe/lombric/cloporte/hérisson/limace) ; les pollinisateurs/oiseaux
volants NON décorés (pas de refuge de sol). Le décorateur est LOCAL au plot mulché
(les plots nus restent bit-identiques).

**Tronçon ⑦ FAIT (2026-07-08)** — golden INTACT (`33c0ea6f…`, hash post-② inchangé :
le smoke n'a aucune maîtrise → palier 0 < seuil → `auto_pailler` no-op strict) ET
population_hash INTACT (`1aa4997d…`, aucun chemin nouveau au tick). Suite verte hors
`test_epaisseur_500ans` (INTERDIT) : test_paillage 54/54, test_planter PASS,
test_maitrise 35/35, test_maitrise_detection 20/20, test_vigueur 136/136,
test_population PASS, test_sim_server 245/245. Le geste `planter`, une fois l'espèce
MAÎTRISÉE, paille le plot d'instinct (D12). Livré :
- `sim/actions/autopaillage.py` (créé, 25 LDC pur) — `SEUIL_AUTOPAILLAGE=3`
  (= palier « maîtrise » découverte1→invest2→**maîtrise3**→expert4→transcend5),
  `nature_autopaillage(species)` (mapping DÉRIVÉ du catalogue : `mulch_source`
  déclarée honorée → sinon arbre de `PERENNIAL_CATALOGUE` → "brf" → sinon "paille"),
  `auto_pailler(...)` (no-op si palier < seuil OU stock vide ; sinon consomme le
  stock + `poser_mulch`).
- `sim/actions/gestes.py::planter` — appelle `auto_pailler(...)` APRÈS le dépôt réussi
  du grain (+ docstring). Import de `.autopaillage`.
- `sim/actions/__init__.py` — ré-exports `SEUIL_AUTOPAILLAGE`/`nature_autopaillage`/
  `auto_pailler` (+ `__all__`).
- `tests/test_paillage.py` — section [9] (mapping nature, palier 0 → nue, maîtrisé+
  stock → paillé bonne nature+stock débité, maîtrisé sans stock → nue sans friction,
  arbre → BRF du bon stock) → 54/54.

Décision de tarif TRANCHÉE (kickoff ⑦ le laissait ouvert) : l'auto-paillage CONSOMME
le stock (respect ④, pas de mulch magique) mais NE facture AUCUNE Vigueur en plus —
c'est un RÉFLEXE fondu dans le geste de plantation du jardinier qui maîtrise, pas un
second geste à payer. Sans stock : plantation nue, aucune friction. Documenté dans
l'en-tête `autopaillage.py` et la docstring de `planter`.

NON concerné : C# (⑦ moteur Python pur, pont/vue = ⑧). F5 : rien à valider ce tronçon
(le visuel « mulch qui apparaît en plantant » = ⑧).

**Tronçon ⑧ FAIT (2026-07-08)** — golden INTACT (`33c0ea6f…`, hash post-② inchangé :
serialize/commands = pont hors tick, `build_world_full` hors golden smoke) ET
population_hash INTACT (`1aa4997d…`). Suite ENTIÈRE verte hors `test_epaisseur_500ans`
(INTERDIT), dont `test_sim_server` 245/245. Build C# `dotnet build Symbiose.csproj`
VERT (0 warning, 0 erreur). La vue Godot rend le paillage JOUABLE + OBSERVABLE. Livré :
- **Python** — `tools/simserver/serialize.py` : nouveau bloc `paillage` par tuile =
  liste CREUSE `[[r, c, profondeur, nature], …]` des plots mulchés (profondeur > 0),
  lu de `eco.paillage`/`eco.paillage_nature` (getattr garde-fous). `tools/simserver/
  actions.py` : DEUX verbes neufs au routeur — `pailler` (target plot {tile,r,c},
  `params.nature` ∈ paille/brf/aiguilles, relaie le refus « stock vide » de la façade)
  + `broyer` (target par POSITION {tile,x_cm,y_cm} sur un SQUELETTE via nouveau résolveur
  `_skeleton_at`, mort porteur de `bois_restant`). `version.py` : bump `ENGINE_VERSION`
  0.5.19 → **0.5.20** (+ entrée doc). `main.py::build_world_full` : DÉMO « planche
  paillée plein sud » (D7) — tuile S, cols 9..12 × lignes 2..8 = 28 plots de tomate/
  basilic/poivron/tournesol PRÉ-MULCHÉS paille (`poser_mulch`, init hors tick).
- **C#** — `visuals/MulchLayer.cs` (NEUF, patron `LitterLayer`) : tapis de mulch batché,
  teinte par nature (paille doré / BRF brun / aiguilles brun-vert), brins ∝ profondeur,
  jitter déterministe (zéro Random). `world/WorldView.Paillage.cs` (NEUF, partial) :
  `_mulchLayer` + `ApplyPaillage`. `WorldView.cs` : instanciation ZIndex 1.
  `WorldView.Snapshot.cs` : `ApplyPaillage(snap["paillage"])` (lecture tolérante).
  `WorldView.Actions.cs` : gestes `pailler` (kind 'U', cycle nature) + `broyer` (kind 'D',
  squelette) + cycle `CycleNature`. `WorldView.Controls.cs` : touche **N** = nature.
  `WorldView.Hud.cs` : nature courante au HUD + légende. `WorldView.Selecteur.cs` :
  option **`propre`** ajoutée (banc « monde propre » sélectionnable au F5).
- **Tests** — `tests/simserver/base.py` (53→81 plantes, cause démo sud), `conteneurs.py`/
  `voix.py`/`structures.py` (bump 0.5.19→0.5.20), `test_sim_server.py` (docstring).

**ABRI faune (item 3 du kickoff)** : DÉJÀ rendu sans code neuf — le moteur (⑥) fait
émerger plus de faune ombrophile sur les plots mulchés (le champ population lit
`paillage`), densité qui arrive au bloc `sprites` déjà dessiné par `MacroLife`. Le
MulchLayer (dessous) + MacroLife (dessus) racontent l'abri ensemble (documenté dans
`WorldView.Paillage.cs`).

**F5 Nico (à valider)** : (1) `config="full"` → planche sud paillée visible (tapis doré
sur la tuile S) ; (2) geste `pailler` (touche pour le sélectionner + N pour la nature)
au clic dépose du mulch — MAIS le stock démarre VIDE, il faut d'abord `broyer` un
squelette OU récolter blé/chanvre/sapin (message serveur « stock vide » sinon) ;
(3) `broyer` sur un squelette ligneux crédite du BRF ; (4) comparer une planche paillée
à une nue (adventices étouffées sous le mulch) ; (5) `config="propre"` (nouveau au
sélecteur) pour observer les cultivées seules ; (6) calibrage visuel du MulchLayer
(couleurs/densité/LOD MinZoom, placeholders).

**Décision de design imprévue** : le stock de mulch de la démo démarre VIDE (le geste
`pailler` consomme un stock, ④). La planche sud est PRÉ-mulchée à l'init (`poser_mulch`
direct, pas via le stock) pour le démonstrateur, mais pour pailler DE NOUVEAU au F5 il
faut approvisionner (broyer/récolter). C'est fidèle à ④ (pas de mulch magique) ; à
surveiller au F5 si Nico veut un stock de départ pour tester `pailler` sans détour.

**SPRINT ÉQUILIBRE INVASION CLOS** (①→⑧ tous FAITS). Reste hors sprint : maj `DETTE.md`
(D69 → implémenté) + `journal.md`. NE PAS OUBLIER : revenir à la perf pure (D67/
LightField) après ce sprint.
