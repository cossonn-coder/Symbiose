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
| ② | Dépôts vivant & mort (taille→bois, squelette persistant + fragmentation, abscission, écraser-squelette) | `02_depots_vivant_mort.md` | **À FAIRE** (gros — phases A/B/C, A\|B coupable) |
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

## REPRISE (démarrage à froid)
Lire ce fichier puis le prochain kickoff. ① est FAIT → écrire `02_*.md` (dépôts
vivant & mort : `tailler`→`bois`, squelette persistant + fragmentation,
abscission d'automne, `ecraser`-squelette). Le doc de conception
(`data/code/CONCEPTION_DECOMPOSITION_COMPOST.md`) tranche tous les « pourquoi ».
