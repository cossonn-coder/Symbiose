# Sprint décomposition & compost — état partagé

> **Conception FIGÉE** → source de vérité = `data/code/CONCEPTION_DECOMPOSITION_COMPOST.md`
> (la lire d'abord). Ce fichier = état léger + carte des sous-sprints. Mis à jour
> en fin de **chaque** sous-sprint. Boucle projet : `0N` → coder → vérifier/re-figer
> golden → MAJ ce fichier → commit → `/clear` → `0N+1`.

## En une phrase
La litière devient un modèle de **parcelles `{tissu, masse, age}` par plot** qui
remplacent le champ scalaire `om_fresh` ; mort → **squelette persistant** qui se
fragmente ; **organes-fruits traçables** (mangeables, qui déplètent) ; **bac à
compost** + **pile à bois** posables. Absorbe **D19** + une part de **D33**.

## Décisions structurantes (détail dans le doc de conception)
- Parcelles **remplacent** `om_fresh` (survit en lecture dérivée = Σ masses).
  6 tissus : `diffus` (exsudats, parcelle permanente) / `feuille` / `fleur` /
  `herbacé` / `fruit` / `bois`. `bois` humifie fort (humus, très lent), tendres
  minéralisent fort. Cascade `om_active`/`om_stable` **conservée**. Fusion par
  tissu = bornage. Granularité = plot ; jitter = cosmétique (vue).
- Mort → squelette persistant (`sèche` debout → `couchée` → fragmentation `bois`),
  n'occupe pas le plot, ombre = silhouette nue. `tailler` dépose du `bois`.
- Abscission d'automne (caducs → `feuille`). Fruits/fleurs sur-mûrs non cueillis
  → tombent. `manger` cible UN fruit (gain ∝ sa maturité, le fruit disparaît).
- Attraction : fruit frais → `auxiliaire` ; pourri → `ravageur` + frac.
  `auxiliaire` (décomposeurs ; pas de 5ᵉ guilde). Pile à bois → habitat `auxiliaire`.
- 2 structures **posables** (poser = planification). Bac : maturation hybride
  (passive + `retourner` accélère), jauge `compost_mur`. `epandre` borné → trio
  humus (+`om_stable`, ensemence `microbiome`, +`fertilite`). Pile à bois : idem,
  biais structure, plus lent.
- **Golden re-figé LARGE** annoncé (écolo + population). On **raccourcit** le
  smoke test (`N_YEARS 4 → 2`) en sous-sprint ①.

## Carte des sous-sprints (6, indépendants)
| # | Sujet | Kickoff | État |
|---|---|---|---|
| ① | Parcelles + cascade + `om_fresh` dérivé + recâblage + **raccourci golden** | `01_parcelles_cascade.md` | **FAIT (2026-06-13)** |
| ② | Dépôts vivant & mort (taille→bois, squelette persistant + fragmentation, abscission, écraser-squelette) | `02_depots_vivant_mort.md` | **FAIT (2026-06-14)** — A (2026-06-13) + B/C (2026-06-14) |
| ③ | Organes-fruits traçables (maturité, `manger` ciblé, chute) — **absorbe D19** | `03_organes_fruits.md` | **FAIT (2026-06-14)** — golden NEUTRE |
| ④ | Attraction animale (fruit→guildes ; pile→habitat reporté ⑤) | `04_attraction_animale.md` | **FAIT (2026-06-14)** — golden NEUTRE |
| ⑤ | Structures posables + gestes (composter/empiler/retourner/epandre, jauge, amendements) | `05_structures_posables.md` | **Phase A FAITE (2026-06-15)** — golden NEUTRE. Reste B (maturation+jauge+retourner) & C (epandre+pile+habitat) |
| ⑥ | Vue (post-mortem visible, litière, maturité-fruit) — **quand Godot reprend** | `06_*.md` (à écrire) | différé |

## Conventions
- Source de vérité = Python `data/code/`. Lancement depuis `data/code/`
  (`python3 main.py`, `python3 -m tests.test_golden`).
- Re-figeage golden **maîtrisé et annoncé** à chaque sous-sprint qui touche le
  tick : noter l'ancien → nouveau hash dans ce fichier + le commit.
- Déterminisme : ordre d'itération des parcelles STABLE (tri par tissu), zéro
  `Random`. Fusion par tissu déterministe (masse +, age moyenné par la masse).
- Tout garder (scripts de mesure inclus). Un fichier à la fois sauf synchro
  cohérente avant commit.

## Acquis sous-sprint ① (2026-06-13)
- `om_fresh` (GridField) **supprimé**. Couche fraîche = `EcoFields.litiere`
  (grille de listes de `Parcelle{tissu, masse, age_sem}`), parcelle `diffus`
  permanente/plot. API : `om_fresh_at` / `om_fresh_average` / `deposer_litiere`
  (point d'entrée unique, fusion par tissu). Table `TISSU` + `TISSU_ORDER`.
- **Choix d'équivalence** : `diffus` reprend la cinétique exacte de l'ancien
  `om_fresh` (`OM_FRESH_DECAY/HUMIF/MINER`) → le tick reste **bit-identique sur
  le flux exsudats** ; `tick_decomposition` lit active/stable AVANT l'humif du
  frais (ordre historique). La **dérive golden vient des SEULS** tissus
  episodiques (nécromasse + inject paillage routés en `herbace`, cinétique §1.2)
  **et du retrait du cap** `max_val=10`. Les autres tissus = placeholders §1.2,
  encore **jamais alimentés** en ① (sauf `herbace`).
- Recâblage : exsudats (`engine.py`)→`diffus` ; `add_necromass`→`herbace` ;
  `inject_field om_fresh` (`effects.apply_mutations`, intercepté avant `get_field`)
  →`herbace` ; lecteurs `soil_memory`/vers/summary→`om_fresh_at`/`_average`.
  `om_fresh` **disparaît de l'overlay F6** (`cmd_fields` introspecte les GridField)
  — acceptable (annoncé). Outil `tools/diag_fields_span.py` liste encore
  `"om_fresh"` (renverra None via get_field) — **non corrigé** (outil hors golden).
- **Golden re-figés (maîtrisés, déterministes h1==h2)** :
  - smoke test `tests/test_golden.py` : `N_YEARS 4 → 2` ;
    `6bf71ee5… → f75d1c219eafd00032b32fc66971b4b0927c99b40dbee47e906f793ffbd582c7`
  - champ population `tests/test_population.py` :
    `f1fe093c… → 9f3513030a4fff030886d5ec6c8e090217879d880c63b75d63cd615b665eb355`
- Suites vertes : golden, population, vigueur (135), croissance (67),
  competition (14), eau (20), sim_server (113), senescence, génétique (20),
  maîtrise (35). `main.py 30` exit 0.

## Acquis sous-sprint ② — Phase A (2026-06-13) : dépôts immédiats
- **Seam tranché = option (a)** : `atteindre_segment` (`sim/growth.py`) **retourne
  la liste des segments retirés** (`[]` en DOUX/collet). Sûr : les 2 appelants
  (`tailler`, `ecraser_plante`) + les 4 appels de `test_croissance` ignorent le
  retour.
- **`tailler`→`bois`** (intention Nico) : dépose `Σ length_cm × BOIS_PAR_CM`
  (knob, `ecofields.py`, =0.03 comme `NECROMASS_PER_CM`) du sous-arbre RÉELLEMENT
  coupé, en litière `bois` au plot. Rien coupé → rien déposé. Gain Vigueur
  inchangé. **`ecraser_plante` dépose AUSSI** sur écimage NET (même seam, voulu).
- **Mort → tissus mous typés** : `add_necromass(...,  tissu="herbace")` (défaut
  compat ①). Helper `sim/effects.tissu_mort(plant)` = `feuille` (caducs) /
  `herbace` (autres). Câblé aux **6 sites de mort** (`engine.py` : alea-santé,
  sénescence, conflit, bisannuelle, annuelle-die, `_mediated_damage`) + `deraciner`
  (`actions.py`). Récolte/résidus restent `herbace` (défaut). **Pas encore de
  bois à la mort** (le squelette qui fragmente = phase B).
- **Golden NEUTRE (non re-figé)** : hashs **bit-identiques à ①** — golden
  `f75d1c21…`, population `9f351303…`. Cause : le seul caduc du scénario
  (`AppleTree`) est **pérenne** (ne meurt pas en 2 ans) → toutes les morts sont
  des annuelles non caduques → `herbace`, comme ①. `tailler`/`ecraser`/`deraciner`
  ne sont pas exercés par le golden (succession pure). La vraie dérive caduque
  viendra de l'**abscission (phase C)** : le pommier larguera du `feuille` chaque
  automne.
- Suites vertes : croissance 67, competition 14, eau 20, sim_server 113,
  senescence, génétique 20, vigueur 135, maîtrise 35. `main.py 30` exit 0.

## Acquis sous-sprint ② — Phases B & C (2026-06-14) : squelette + abscission
- **État post-mortem** sur `PlantInstance` (`plants/base.py`) : `morte`,
  `stade_mort` (`""`/`seche`/`couchee`), `bois_restant`, `semaines_mort` — inertes
  tant que la plante vit. `is_alive ≡ health > 0` inchangé.
- **`deposer_mort(plant, eco)`** (`sim/effects.py`, idempotent sur `morte`) :
  dépose la **fraction molle** `biomass × (1 − frac_bois)` en `tissu_mort`,
  marque `morte`, met `bois_restant = biomass × frac_bois`. `frac_bois_mort` =
  `FRAC_BOIS_MORT` (0.45) **seulement** pour les ligneuses (`age_curve`), 0 sinon.
- **Squelette persistant** : la mort ne retire **plus** la plante. `_tick_skeletons`
  (`engine.py`, étape 16b, APRÈS tous les sites de mort) : `seche`→`couchee` après
  `T_SECHE`=6 sem, fragmente `bois_restant × FRAG_RATE(0.04) × decomp_speed(r,c)`
  en litière `bois`/sem, **seul point de retrait** (filtre `is_alive or (morte and
  bois_restant>1e-9)` → herbacées retirées le tick même, ligneuses après épuisement).
- **Ombre silhouette (RISQUE #1 tranché = `SILHOUETTE_SECHE`=0.30)** : squelette
  `seche` debout projette un tronc nu dégressif (`light.py`) ; `couchee`/herbacées
  retirées → rien. Jamais déclenchée par le golden (aucune ligneuse n'y meurt).
- **Abscission d'automne (C.1)** : `_abscission` (étape 15b, semaines `ABSCISSION_WEEKS`
  =(38,39)) — caducs **vivants** larguent `current_height × NECROMASS_PER_CM ×
  ABSCISSION_FRAC(0.15)` en `feuille`. **`ecraser`-squelette (C.2)** : sur un mort,
  `seche`→`couchee` + largue `bois_restant × ECRASER_FRAG_BOOST(0.50)` d'un coup.
- **Golden RE-FIGÉ LARGE (maîtrisé, déterministe h1==h2)** :
  - smoke `tests/test_golden.py` :
    `f75d1c21… → 908f591bee5b45736bc3e542253c3807a81e5551fcb0e50ab8703446df5d11b6`
  - champ population `tests/test_population.py` :
    `9f351303… → 435e6f72c220a2d19daed00712d09dc6c2d5d6f129066bd7ea3f37b99f557a61`
  - **Cause de la dérive (analysée par diff complet old↔new)** :
    1. **PRINCIPALE** — toute mort dépose désormais sa nécromasse via `deposer_mort`.
       L'ancien `_resoudre_conflits` (étape 12, AVANT `apply_disturbances`) avait un
       filtre **inconditionnel** `tile.plants=[… if is_alive]` qui balayait
       *silencieusement* (sans dépôt) les morts survenues entre sénescence et
       conflits — typiquement la **Tomate tuée par le mildiou familial dès la
       semaine 3** de chaque printemps. Ce filtre retiré (B), la morte persiste
       jusqu'à `apply_disturbances` qui la dépose → +nécromasse `herbace` aux plots
       Tomate (2,2) sur T0+T1 chaque printemps → cascade fertilité/succession sur
       2 ans (≈ toute la dérive de trajectoire). **Correction conforme au design**
       (« toute mort dépose ses tissus mous », ① / phase A), pas un bug introduit.
    2. **SECONDAIRE** — abscission du pommier (`feuille` aux sem. 38/39 et 90/91).
    3. **Fragmentation `bois`** : 0 occurrence (aucune ligneuse ne meurt en 2 ans).
    4. **Silhouette** : jamais déclenchée (aucun squelette ne persiste d'un tick
       à l'autre dans le golden).
- Suites vertes : golden, population, vigueur 135, croissance 67, competition 14,
  eau 20, génétique 20, maîtrise 35, maîtrise_detection 20, auxiliaires,
  signes 8, ombre_maison 4, phototropisme 11, planter 18, sim_server 113,
  **sénescence** (pommier mort de sénescence à 59.8 ans → exerce la fragmentation
  ligneuse + silhouette SANS casse). `main.py 5` exit 0.

## Acquis sous-sprint ③ (2026-06-14) : organes-fruits traçables (absorbe D19)
- **`Fruit{segment_id, maturite, masse}`** (`plants/base.py`) : un fruit cesse
  d'être un proxy de rendu saisonnier (`REPRO_BY_SEASON`) → **état moteur** porté
  par `PlantInstance.fruits` (liste, vide tant que pas de nouaison). Flag
  d'éligibilité `PlantBase.fruitier` (Tomato, AppleTree). Le moteur ne lit JAMAIS
  `segment_id` (repère VUE ⑥) → déterminisme/golden indépendants de la structure.
- **`organ_sites(plant)`** (`plants/base.py`, couche basse) : sites reproducteurs
  = (index segment, position 3D), pure géométrie sur `plant.segments`
  (`terminal`=tous apex / `lateral`=apex sauf meneur), plafond `MAX_ORGANS`=10.
  Source UNIQUE partagée par le moteur ; miroir du proxy VUE `_organ_sites`
  (`tools/render_structure`) laissé intact (frontière de couches : `sim` n'importe
  pas `tools`). Duplication mineure `MAX_ORGANS`/`MAX_FRUITS` assumée/documentée.
- **`engine._tick_fruits` (étape 15c, chaque semaine)** : (1) **nouaison annuelle**
  à `FRUIT_NOUAISON_WEEK`=14 (début d'été) pour `fruitier` **ET** `age_years ≥
  maturity_years` — pose un fruit vert/site, l'ancienne cohorte non récoltée chute
  d'abord en `fruit` ; (2) **maturation** `maturite += FRUIT_DMAT`(0.08) ; (3)
  **chute** des sur-mûrs (`maturite > MATURITE_CHUTE`=1.3) → litière `fruit`
  (`FRUIT_MASSE`=0.15). Gate fixe + tri stable + zéro RNG.
- **`manger` dual-mode** (`sim/actions.py`) : `fruit_index` valide → consomme CE
  fruit, gain `= HARVEST_GAIN_FULL × santé × **maturité_fruit** × Qi × gène`,
  l'organe **disparaît** (déplétion réelle D19). Sans index (ou hors-borne) →
  chemin **générique legacy** (façade `vigueur_plante` plante entière) → tests
  vigueur D1-D4 préservés. Coût NUL inchangé.
- **Pont `sim_server.py` 0.3.3 → 0.3.4** : snapshot expose `plant.fruits`
  (`[{segment, maturite, masse}]`) ; `manger` route `target.fruit` (validé int +
  bornes, comme `tailler.segment`) → `fruit_index`.
- **Golden NEUTRE (non re-figé)** : smoke `908f591b…`, population `435e6f72…`
  **bit-identiques à ②**. Cause : seule espèce `fruitier` du scénario = AppleTree,
  `maturity_years`=5 > fenêtre 2 ans → nouaison jamais déclenchée (gate d'âge,
  comme la neutralité ②A). Vérifié empiriquement.
- Nouveau test **`tests/test_fruits.py`** (21 checks) : nouaison, gate d'âge,
  annualité+remplacement de cohorte, maturation, chute→litière, déterminisme
  (h1==h2), `manger` ciblé (gain ∝ maturité, ratio 3× exact, déplétion),
  `manger` générique (fallback). Suites vertes : golden, population, vigueur 135,
  croissance 67, competition 14, eau 20, génétique 20, maîtrise 35,
  maîtrise_detection, auxiliaires, signes 8, ombre_maison 4, phototropisme 11,
  planter 18, sim_server 113, senescence, **fruits 21**. `main.py 5` exit 0.

## Acquis sous-sprint ④ (2026-06-14) : attraction animale (fruit→guildes)
- **Tout dans `fields/population.py`** (couche `fields` intacte, aucun import
  `sim`/`tools`). Le fruit tombé appelle la faune selon `age_sem` : **frais →
  `auxiliaire`** (frugivores), **pourri → `ravageur` DOMINANT + frac.
  `auxiliaire`** (décomposeurs). **Aucune 5ᵉ guilde** ; le fruit ne touche jamais
  la plante (philo #2).
- **Mécanisme** : 3ᵉ terme additif **optionnel `signal_fn`** sur `TrophicSpec`
  (défaut `None` → terme 0 → capacité inchangée → pollinisateur/vers
  **bit-identiques**). Branché dans `tick` : `capacite = clamp(resource_w·res +
  habitat_w·hab + signal)`. Helpers purs `_fruit_litter` (parcelle `fruit`
  unique/plot par fusion ① → déterministe), `_fruit_weights(age)`,
  `_aux_fruit_signal` = `FRUIT_AUX_GAIN·sig·(frais+FRAC_AUX_POURRI·pourri)`,
  `_rav_fruit_signal` = `FRUIT_RAV_GAIN·sig·pourri`, `sig=min(1,masse/
  FRUIT_SIGNAL_REF)`. Knobs conservatifs : FRAIS_SEM=3, POURRI_SEM=6, REF=0.45,
  AUX_GAIN=0.50, RAV_GAIN=0.60, FRAC_AUX_POURRI=0.25.
- **Décision #0** : **pile à bois → habitat (§4.1) reportée à ⑤** (la structure
  n'existe pas avant ⑤ ; réutilisera le patron rondelle/`_stability_grid`).
- **Golden NEUTRE (non re-figé), vérifié** : smoke `908f591b…`, population
  `435e6f72…` **bit-identiques à ③**. Cause : le golden ne crée aucune litière
  `fruit` (AppleTree `maturity_years`=5 > 2 ans → pas de nouaison → pas de chute)
  → `signal`=0 partout → capacité inchangée. (La §7 prévoyait « re-figé
  population » avant le constat empirique de ③ ; ④ confirme la neutralité.)
- Nouveau **`tests/test_attraction.py`** (17 checks, 2 niveaux : modèle pur exact
  + intégré après 15 ticks, plot-fruit vs témoin). Suites vertes : golden,
  population, fruits 21, vigueur 135, croissance 67, competition 14, eau 20,
  génétique 20, maîtrise 35, maîtrise_detection, auxiliaires, signes 8,
  ombre_maison 4, phototropisme 11, planter 18, sim_server 113, senescence,
  **attraction 17**. `main.py 5` exit 0.

## Acquis sous-sprint ⑤ — Phase A (2026-06-15) : modèle + poser + composter/empiler
- **Décisions ⑤ figées** : **#1** structures portées par `eco`
  (`EcoFields.structures: list[Structure]`, init `[]`) — couche `fields`, à côté
  de `litiere`. **#2** contenu = réutilisation de `Parcelle` ;
  `Structure{kind, plot, contenu, compost_mur}` (`ecofields.py`). **Décision ⑤A
  (dévie de la lettre du §5)** : le **bac REFUSE `diffus`** — les exsudats sont
  DANS le sol (parcelle permanente du plot, non ramassable). `STRUCTURE_ACCEPTE =
  {bac: {feuille,fleur,herbace,fruit}, pile: {bois}}`. *(tranché avec Nico.)*
- **`fields/ecofields.py`** : helper module `_fusion_parcelle(parcelles, tissu,
  masse)` extrait (fusion par tissu PARTAGÉE litière ↔ structures) → `deposer_litiere`
  refactorisé pour l'appeler (**bit-identique**, golden neutre). Nouveau
  `Structure.accepte(tissu)` + `EcoFields.deposer_dans_structure(struct, tissu, masse)`
  (miroir de `deposer_litiere`, garde-fou d'acceptation). Exports `Structure` /
  `STRUCTURE_ACCEPTE` ajoutés à `fields/__init__.py`.
- **`sim/actions.py`** : `poser_bac`/`poser_pile` (→ `Structure | None`, coût
  `MODÉRÉ`, binaire), `composter`/`empiler_bois` (coût `FAIBLE`, binaire) via le
  helper `_ramasser_vers_structure(eco, r, c, struct)` (déplace les parcelles
  acceptées plot→structure, **masse conservée**, `diffus`/`bois` restent au sol
  pour le bac). Entrées `COUTS` + `OBJETS_TOUCHES` (concept maîtrise `"compostage"`,
  sans état moteur → atténuation neutre 1.0). Aucun champ écolo touché (philo #2).
- **Golden NEUTRE (non re-figé), PROUVÉ** : smoke `908f591bee…`, population
  `435e6f72…` **bit-identiques à ④**. Cause : le golden ne pose aucune structure
  (succession pure) ET le refactor `_fusion_parcelle` est bit-identique → tick
  inchangé. **Aucune modif de `engine.py`/`tick_decomposition` en phase A.**
- Nouveau **`tests/test_structures.py` (34 checks)** : poser (binaire), acceptation
  §5, composter (tendre→bac, diffus/bois restent, masse conservée), empiler,
  fusion contenu (age pondéré), déterminisme, neutralité refactor. Suites vertes :
  golden, population, structures 34, fruits, attraction, vigueur 135, croissance 67,
  competition, eau, génétique 20, maîtrise 35, maîtrise_detection 20, signes 8,
  ombre_maison, phototropisme 11, planter, sénescence, sim_server 113 ;
  auxiliaires (AUX < TÉMOIN, régulation OK). `main.py 5` exit 0.
- **Reste ⑤** : **phase B** (`tick_structures` maturation hybride ∝ constitution +
  jauge `compost_mur` + `retourner`, appel après `tick_decomposition` dans
  `engine.py`) puis **phase C** (`epandre` trio humus borné + amendement pile +
  pile→habitat `auxiliaire` via rondelle + pont 0.3.5). Golden attendu NEUTRE.

## REPRISE (démarrage à froid)
Lire ce fichier puis le kickoff `05_structures_posables.md`. ①+②+③+④ **FAITS** ;
⑤ **phase A FAITE** (cf. §Acquis ⑤ Phase A). **PROCHAINE ÉTAPE = ⑤ phase B**
(`tick_structures` maturation hybride ∝ constitution + jauge `compost_mur` +
geste `retourner`, appelé après `tick_decomposition` dans `engine.py` ; golden
attendu NEUTRE — structures vides ⇒ no-op strict). Puis **phase C** (`epandre`
trio humus borné + amendement pile + pile→habitat `auxiliaire` via rondelle +
pont 0.3.4→0.3.5). Le kickoff §«Plan d'implémentation»/§«Décisions #3» détaille
les knobs de B/C. Ensuite **⑥ vue Godot** (différé : post-mortem visible, litière,
maturité-fruit). Hooks posés pour ⑥ : `plant.fruits` au snapshot, `manger` routé
sur `target.fruit`. Patron habitat pour ⑤C : rondelle `auxiliaire` lue par
`_stability_grid` (cf. `favoriser_auxiliaire`).
