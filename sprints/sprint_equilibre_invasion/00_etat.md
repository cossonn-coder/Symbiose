# Sprint « équilibre de l'invasion d'adventices » — état vivant (carnet de bord)

> Carnet de conception (`/conception`, dette **D69**). Reprise à froid = lire
> `CLAUDE.md` + ce fichier + `docs/conception/CONCEPTION_EQUILIBRE_INVASION.md`.
> **CONCEPTION FIGÉE (2026-07-06)** — design ARBITRÉ D1-D12, découpage ①-⑧ validé,
> doc + kickoffs 01-08 écrits. **PRÊT pour `/sprint-auto sprint_equilibre_invasion`.**

## Carte des tronçons (un seul sprint, perf-first, vue en dernier)
- **01** banc `config="propre"` + `tools/diag_population.py` [golden INTACT]
- **02** recalibrage freins férals — onset ~2-3 saisons, N~650/8 tuiles [golden RE-FIGÉ, seul]
- **03** paillage moteur — champ + geste `pailler` + germ↓/ET↓/graines↑/→OM [INTACT]
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

## §REPRISE
Prochaine étape : remonter à Nico la critique Phase A + les 3 arbitrages
ci-dessus (via AskUserQuestion). Puis itérer, consigner chaque arbitrage ici,
et ne figer (phase B : doc `CONCEPTION_*` + kickoffs) qu'après accord global.
Le découpage se terminera par un **tronçon vue Godot** (règle projet).
