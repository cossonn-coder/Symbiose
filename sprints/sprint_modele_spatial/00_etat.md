# 00_etat — Sprint MODÈLE SPATIAL (nom provisoire) — carnet de bord vivant

> Statut : **SPRINT TERMINÉ** (①②③ CLOSE, 2026-07-14) — golden 4f6c4f31e0…,
> reste F5 côté Nico (checklist §REPRISE). Ce fichier est le handoff permanent
> (skill /conception §0bis). Reprise à froid = lire `CLAUDE.md` + ce fichier.

## Sujet (mots de Nico)
1. « les plots sont trop restrictifs, ils devraient avoir une taille variable
   propre aux plantes qui y poussent »
2. « plusieurs plantes devraient pouvoir pousser au même endroit et ce n'est pas
   le cas actuellement »
3. « les clones ne ressemblent pas aux plantes clonées »

## Diagnostic moteur (vérifié dans data/code, 2026-07-14)
Découverte cardinale : **le moteur fait déjà ~80 % de la demande**. L'écart perçu
par Nico vient probablement du **rendu Godot / banc de démo**, pas du moteur.

- **P1 (plots)** : le plot 50 cm n'est QU'une maille de chimie du sol. Position
  plante = CONTINUE (`x_cm,y_cm`, instance.py:44,158-162). Empreinte = déjà
  variable par plante (canopée + racines, rayons tabulés/procéduraux ;
  `foliar_plots`/`root_plots` instance.py:292-309). Restent en grille : (a) la
  CHIMIE du sol échantillonnée à 50 cm ; (b) le RENDU qui colle peut-être au
  centre de plot.
- **P2 (cohabitation)** : verrou d'occupation DÉJÀ LEVÉ (succession.py:132),
  mort-par-conflit DÉSACTIVÉE (mortalite.py:247). Deux graines lèvent sur le même
  plot, cohabitation arbitrée par niche_index (lumière + densité racinaire),
  escomptée par tolérance à l'ombre → strate d'ombre déjà possible. Frein réel :
  plot dense/ombragé → niche faible → 2e plante ne s'établit pas (correct éco).
  ET `planter` recentre au CENTRE du plot → 2 plantes/plot = même position exacte
  = superposition visuelle.
- **P3 (clones)** : clonal.py:148-149 copie gènes + expression. MAIS morphogénèse
  amorcée par POSITION (phases.py:95 `_hash_noise(seed,week,bx,by)`) → part
  stochastique du port décorrélée de la mère. + ramet naît bébé (stade 0).

## Vrais chantiers candidats (à trancher avec Nico)
- A. Rendu/placement Godot : jitter de position sous-plot pour éviter la
  superposition au centre (probable cœur de P1+P2 perçus).
- B. Résolution chimie du sol (rester 50 cm vs sub-plot) — coûteux, à challenger.
- C. Stratification verticale explicite (strates canopée/sous-bois/couvre-sol) —
  si Nico veut de la coexistence par étage, pas juste « ne pas se chasser ».
- D. Morphogénèse amorcée par IDENTITÉ héritable (graine de forme portée par la
  plante, copiée au clone) → air de famille clonal. + question maturité bébé.

## Arbitrages TRANCHÉS (Nico, 2026-07-14)
- Q1 (P1) → « pas systématiquement au centre du plot ; chimie reste 50 cm mais
  variable par espèce ». Découverte : la chimie *vécue* est DÉJÀ variable par
  espèce (`vigueur_plante.py:71` lit sur `root_plots`, footprint variable). Donc
  P1 = **placement sous-plot** (chantier A) ; le sub-plot raffine la chimie
  gratuitement (la position exacte décide quels plots la racine touche). B REJETÉ.
- Q2 (P2) → « juste ne plus superposer » = chantier A (placement sous-plot).
  Cohabitation déjà OK dans le moteur. C (stratification) REJETÉ.
- Q3 (P3) → « les deux », mais coup de pouce ramet REFUSÉ (« juvénile qui grandit
  dedans »). Donc chantier D = **form_seed héritable** seul ; le ramet reste
  juvénile et grandit dans la silhouette de la mère. Pas de head-start (philo #2).

## Conception FIGÉE (2 chantiers, 3 tronçons) — perf négligeable
- **① Placement sous-plot déterministe** — DEUX cas distincts :
  · **Plantée par le joueur** = position au **PIXEL CLIQUÉ EXACT** (Nico
    2026-07-14). Le pont a déjà `{x_cm,y_cm}` mais `actions_cibles._plot_at` le
    rabat en `(r,c)` avant `planter` → le pixel est PERDU. Fix : `planter` reçoit
    x_cm/y_cm, `GrainEnAttente` les porte, la levée place la plante PILE là.
    Event-driven (smoke ne plante pas) → **golden NEUTRE** pour ce cas.
  · **Férale** (succession spontanée + levée sans pixel) = offset hashé
    déterministe (seed,r,c,semaine) DANS le plot, borné [~10,40] cm → plot-foyer
    INCHANGÉ (chimie stable). Fini le centrage systématique.
  Dans les deux cas le plot-foyer = celui du pixel/plot cible (chimie stable).
  Clones déjà continus (clonal.py) → non touchés. Fichiers : fields/seedbank.py
  (GrainEnAttente + x_cm/y_cm), sim/actions/gestes.py (planter), simserver route
  (passer le pixel), sim/succession.py (2 sites de levée + helper offset féral).
  **Golden RE-FIGÉ** par le cas FÉRAL uniquement (positions férales dérivent →
  lumière/empreintes). Ordre 1er (fonde l'unicité spatiale des positions).
- **② Identité morphologique héritable (form_seed)** — champ `form_seed:int` sur
  PlantInstance, posé 1× à la naissance (hash position+semaine dans __post_init__),
  COPIÉ au clone (clonal.py, comme les gènes). `_debourrement` (phases.py:95) lit
  `plant.form_seed` au lieu de (bx,by) → clones = même patron de branches (air de
  famille), divergence fine par lumière/phototropisme. Fichiers : instance.py,
  phases.py, clonal.py (copie). **Golden RE-FIGÉ** (silhouettes reseed).
- **③ Banc d'observation + vue Godot** — le pont porte DÉJÀ x_cm/y_cm + segments
  (serialize.py:101-105) → les 2 chantiers remontent tout seuls. Tronçon = banc
  déterministe (mère + N ramets + 2 plantes qui se chevauchent) + checklist F5
  pour Nico. AUCUN changement moteur. **Golden INTACT**.

## Coût perf (pré-estimé, à affiner)
- A (jitter position) : négligeable (une passe au placement).
- B (chimie sub-plot) : ROUGE — multiplie la taille des GridField, gros risque
  LightField (dette D32). À éviter sauf besoin fort.
- C (stratification) : dépend du modèle ; possible sans nouveau champ si on
  s'appuie sur niche/lumière existants.
- D (identité morpho) : négligeable (remplace la clé de hash, pas un coût runtime).

## Statut : CONCEPTION FIGÉE (2026-07-14) — prêt pour /sprint-auto
Doc : `docs/conception/CONCEPTION_MODELE_SPATIAL.md`. Kickoffs autosuffisants :
- `01_placement_sousplot.md` — pixel cliqué (joueur) + offset féral. Golden RE-FIGÉ (féral).
- `02_form_seed.md` — identité morpho héritable, clone = air de famille. Golden RE-FIGÉ.
- `03_banc_vue.md` — banc d'observation + F5. Golden INTACT.

## Carte des tronçons
① re-fige le golden (positions férales) ; ② prévu re-figé mais s'est révélé
NEUTRE (le digest ne capture pas les angles de branche — silhouettes reseed mais
scalaires captés inchangés) ; ③ neutre. Ordre imposé : ① avant ② (positions
uniques avant dérivation du form_seed).

## §REPRISE (pour /sprint-auto)
- **① CLOSE** (2026-07-14) — placement sous-plot : pixel cliqué (joueur, golden
  NEUTRE event-driven) + offset féral déterministe borné [10, 40] cm (plot-foyer
  inchangé). Golden RE-FIGÉ par le cas féral (prévu). Empreinte : **4f6c4f31e0…**.
  Fichiers : fields/seedbank.py, sim/actions/gestes.py, sim/succession.py,
  tools/simserver/actions.py, tests/golden_hash.txt.
- **② CLOSE** (2026-07-14) — identité morphologique héritable `form_seed`. Champs
  `form_seed`/`branch_count` sur PlantInstance (hors `_PLANT_ATTRS`), fabrique
  `form_seed_at` dans fields/noise.py (exportée), posée aux 2 sites de levée
  (succession.py), COPIÉE au clone (clonal.py), `_debourrement` amorcé par
  `form_seed`+`branch_count` (ordinal stable) au lieu de position+semaine.
  **Golden INCHANGÉ : 4f6c4f31e0…** — contre l'attente du kickoff. Raison : le
  digest golden ne capture QUE les scalaires `_PLANT_ATTRS` + logs, PAS les
  segments/angles de branche. La reseed CHANGE bien les silhouettes (footprint
  hash b929…→67f1…, vérifié) mais l'écart ne franchit aucun seuil de quantif des
  scalaires captés sur la fenêtre 2 tuiles × 2 ans → aucun re-figeage nécessaire.
  Le changement est bien exercé (27/42 plantes branchent, form_seed posé sur les
  26 férales ; les fondatrices semées direct via `semer_fondateur` gardent
  form_seed=0 → repli robuste dans `_debourrement`). form_seed HÉRITÉ vérifié sur
  les ramets Minette (mère & clones même form_seed). Fichiers : plants/base/
  instance.py, fields/noise.py, fields/__init__.py, sim/succession.py,
  sim/clonal.py, sim/growth/phases.py.
  ⚠️ **test_population et test_sim_server ÉCHOUENT** — mais IDENTIQUEMENT à la
  baseline (avant ce tronçon) → **hérités du re-figeage ① non propagé** à ces 2
  suites, PAS causés ni affectés par ② (hashes identiques avec/sans ②). À traiter
  hors ② (concerne ①).
  📝 Aparté save (futur) : `branch_count` devra être sérialisé avec la structure
  (sinon plante rechargée re-tire ses branches sur compteur remis à 0). Save
  inexistant → aucune action.
- **③ CLOSE** (2026-07-14) — banc d'observation + vue Godot. AUCUN changement
  moteur. **Golden INTACT : 4f6c4f31e0…** (confirmé). Nouveau banc
  `bancs/modele_spatial.py` (58 LDC pur) enregistré dans `bancs/__init__.py`
  (registre `BANCS["modele_spatial"]`). Le banc COMPOSE l'état existant : un
  framboisier mature pré-vieilli (drageon) qui essaime des ramets à l'air de
  famille (② `form_seed` copié) + un trio de trèfles au MÊME plot (2,2) posés à
  des positions sous-plot distinctes (① placement sous-plot). Runner de vérif
  `python3 -m bancs.modele_spatial` : ASSERTE positions du trio distinctes + une
  lignée clonale de framboisiers partageant un `form_seed` (mère + ramets). PASS.
  Fichiers : bancs/modele_spatial.py (neuf), bancs/__init__.py.
  **SPRINT TERMINÉ** — reste F5 côté Nico (checklist ci-dessous).

## Checklist F5 (Nico — vue Godot)
Lancer le banc côté Godot (F5) : `init config="modele_spatial"` (via `SimBridge` /
`cmd_init` du serveur — même canal que les autres bancs, cf. `BANCS`). Observer,
laisser tourner quelques saisons (le clonal émet au fil des ticks) :
- les plantes ne sont **plus alignées au centre** de la grille (positions
  sous-plot variées) ;
- le **trio de trèfles** au même plot **ne se superpose plus** (3 pieds décalés
  de quelques cm, lisibles séparément) ;
- le **framboisier** essaime des **drageons qui RESSEMBLENT à la mère** (même
  port/patron de branches) mais **plus JEUNES** (juvéniles, pas de head-start) ;
- (option) `planter` à un pixel précis → la plante lève **pile à l'endroit
  cliqué** (cas joueur du tronçon ①).

Chaque tronçon lit `CLAUDE.md` + ce fichier + son `0N_*.md`. Après chaque
tronçon : golden vérifié/re-figé selon le kickoff, empreinte notée ICI, commit,
/clear, tronçon suivant. Golden de départ : 240f10219e… (désync phéno) → ① :
4f6c4f31e0…. NOTER ici l'empreinte après ②. Penser à MAJ DETTE.md + BACKLOG.md +
journal.md à la clôture.
