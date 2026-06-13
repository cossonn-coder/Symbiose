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
| ① | Parcelles + cascade + `om_fresh` dérivé + recâblage + **raccourci golden** | `01_parcelles_cascade.md` | **À FAIRE** |
| ② | Dépôts vivant & mort (taille→bois, squelette persistant + fragmentation, abscission, écraser-squelette) | `02_*.md` (à écrire) | en attente |
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

## REPRISE (démarrage à froid)
Lire ce fichier puis `01_parcelles_cascade.md`. Le doc de conception
(`data/code/CONCEPTION_DECOMPOSITION_COMPOST.md`) tranche tous les « pourquoi ».
