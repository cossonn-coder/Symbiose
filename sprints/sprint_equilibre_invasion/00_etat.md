# Sprint « équilibre de l'invasion d'adventices » — état vivant (carnet de bord)

> Carnet de conception (`/conception`, dette **D69**). Reprise à froid = lire
> `CLAUDE.md` + ce fichier + `docs/conception/CONCEPTION_EQUILIBRE_INVASION.md`.
> **CONCEPTION FIGÉE (2026-07-06)** — design ARBITRÉ D1-D12, découpage ①-⑧ validé,
> doc + kickoffs 01-08 écrits. **PRÊT pour `/sprint-auto sprint_equilibre_invasion`.**

## Carte des tronçons (un seul sprint, perf-first, vue en dernier)
- **01** banc `config="propre"` + `tools/diag_population.py` [golden INTACT] ✅ FAIT 2026-07-06
- **02** recalibrage freins férals — onset ~2-3 saisons, N~650/8 tuiles [golden RE-FIGÉ, seul] ✅ FAIT 2026-07-08 (N an6=613, knob `GERM_PRESSION_FERALE=0.30`)
- **03** paillage moteur — champ + geste `pailler` + germ↓/ET↓/graines↑/→OM [golden INTACT] ✅ FAIT 2026-07-08 (champ `paillage`, geste `pailler`, 4 effets, golden `33c0ea6f…` inchangé)
- **04** matériau — `broyer`→BRF + récolte paille → stock + 3 natures [INTACT]
- **05** catalogue blé/chanvre/sapin + 5 voix [INTACT]
- **06** paillage ↔ vie macro (abri) [INTACT]
- **07** planter+pailler par maîtrise (auto-paillage) [INTACT]
- **08** vue Godot (pailler/broyer + rendu mulch + abri) + démo sud [INTACT]

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
`CONCEPTION_EQUILIBRE_INVASION.md` + kickoffs 01-08, un fichier à la fois). Puis
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

**Prochain : tronçon ④.** Message /clear : « lis
`sprints/sprint_equilibre_invasion/00_etat.md` puis `04_*.md` ».
