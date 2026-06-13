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
| ② | Dépôts vivant & mort (taille→bois, squelette persistant + fragmentation, abscission, écraser-squelette) | `02_depots_vivant_mort.md` | **Phase A FAITE (2026-06-13)** ; **B/C À FAIRE** (gros) |
| ③ | Organes-fruits traçables (maturité, `manger` ciblé, chute) — **absorbe D19** | `03_*.md` (à écrire) | en attente |
| ④ | Attraction animale (fruit→guildes, pile à bois→habitat) | `04_*.md` (à écrire) | en attente |
| ⑤ | Structures posables + gestes (composter/empiler/retourner/epandre, jauge, amendements) | `05_*.md` (à écrire) | en attente |
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

## REPRISE (démarrage à froid)
Lire ce fichier puis `02_depots_vivant_mort.md`. ① FAIT, ② **Phase A FAITE** →
reprendre **Phase B** (squelette persistant : mort ne retire plus la plante,
`tick_skeletons` sèche→couchée→fragmentation `bois`→retrait final ; **ombre =
silhouette nue, RISQUE #1** — trancher silhouette `SILHOUETTE_SECHE` vs ombre
nulle, §B.3) puis **Phase C** (abscission d'automne caducs→`feuille`,
`ecraser`-squelette→couchée). B/C re-figeront le golden (squelette + abscission
du pommier). Doc conception §2 tranche les « pourquoi ».
