# 2026-06-18 — Sprint CATALOGUE ENRICHI · tronçon ③ : plantes lot 2 (familles + cycles neufs) — gate `biennial` comblé, golden NEUTRE — ③ CLOS

## Contexte

Tronçon ③ du sprint catalogue enrichi (kickoff
`sprints/sprint_catalogue_enrichi/03_plantes_lot2.md`, doc figé
`docs/conception/CONCEPTION_CATALOGUE_ENRICHI.md`). Contrairement à ②, ce lot
introduit **5 familles botaniques NEUVES** (donc nouvelles entrées d'attractivité
`_ATTRACT_*`) et exerce pour la **première fois** le cycle `life_cycle="biennial"`
— qui révèle un **trou moteur** (aucun gate annuel de montaison) à combler.

## Ce qui est fait

**+5 plantes** (clés `PLANT_CATALOGUE`) :

| Espèce | Latin | Famille (NEUVE) | Cycle | Hiver | Niche |
|---|---|---|---|---|---|
| Carotte | *Daucus* | **Apiaceae** | **biennial** | dormant | ombelle mellifère syrphe n°1, racine comestible, hôte |
| Courgette | *Cucurbita* | **Cucurbitaceae** | annual | die | `fruitier`, couvre-sol étalé (compétition sol), mellifère |
| Mâche | *Valerianella* | **Caprifoliaceae** | annual | die | couvre-sol rustique d'hiver (`temp_min_growth=2`) |
| Ortie | *Urtica* | **Urticaceae** | perennial | dormant | spontanée non-archétype, +fertilité (biomasse azotée), anémophile |
| Ail | *Allium* | **Amaryllidaceae** | **biennial** | dormant | compagne répulsive (soufre), bulbe comestible |

- **Nouveaux fichiers** `plants/species/potageres.py` (carotte/courgette/mâche —
  `cultivees.py` déjà à ~308 LDC, le garde-fou ~350 interdisait l'ajout) et
  `plants/species/sauvages.py` (ortie). Ail ajouté à `compagnes.py`.
- **2 familles à effet familial → classes** dans `plants/base/familles.py` :
  `Urticaceae` (injection `fertilite` locale = biomasse azotée) et `Amaryllidaceae`
  (répulsif via `adjacency_bonus reduce_maladie_rondelle`). Les 3 autres (Apiaceae,
  Cucurbitaceae, Caprifoliaceae) n'ont **pas** d'effet familial → `family="…"` au
  niveau espèce (patron Phacelia/Borage).
- **Attractivité** : les 3 tables `_ATTRACT_*` (`population.py`) reçoivent les 5
  familles. Saillant : Apiaceae syrphe **1.0** (ombellifère, ressource n°1 du
  syrphe), Cucurbitaceae abeille 0.70, Urticaceae **0.0 partout** (anémophile).
- Câblage : `species/__init__.py`, `plants/base/__init__.py`, `plants/__init__.py`,
  `catalogue.py` (PLANT_CATALOGUE seul ; `WEED_`/`PERENNIAL_` intacts).

## Trou moteur comblé : gate annuel des bisannuelles

`life_cycle="biennial"` existait (longévité 2 + mort monocarpique à age≥2,
`mortalite.py`) mais **aucune espèce ne l'exerçait** et la progression de stade
n'avait **aucun gate annuel** — une bisannuelle aux stades courts montait à fleur
dès l'an 1. Ajout dans `sim/engine/croissance.py` :
- `_bolt_stage_index(cls)` : index du stade de MONTAISON = 1er stade portant un
  effet `floraison` (convention catalogue).
- `_bolt_bloque(plant)` : pour une bisannuelle d'`age_years < 1.0`, bloque le
  franchissement VERS ce stade (et au-delà) → **rosette l'an 1, montaison/floraison
  l'an 2**, puis mort. N'a d'effet QUE pour `biennial` ⇒ golden NEUTRE.

## Tests neufs

- **`tests/test_biennial.py`** (carotte + ail) : (a) an 1 jamais au-delà de la
  rosette, (b) an 2 atteint la montaison qui pose bien `pollinisateur`, (c) morte
  en fin d'an 2. Verrou du gate.
- **`tests/test_catalogue_lot2.py`** : sanity des 5 clés (germent, dépassent le
  semis) ; attractivité (carotte → syrphe > abeille/papillon ; ortie → nectar nul
  pour tous) ; courgette `fruitier` (pollinisée → ≥1 fruit ; sans pollen → 0,
  philo #2).

## Golden

**NEUTRE** — hash `5fddfe54…` inchangé. Le smoke (2 tuiles × 4 ans) n'instancie
aucune des 5 espèces ; le gate bisannuel ne touche aucune espèce du smoke
(non bisannuelle). evergreen non-régressé.

## Signalements (carte blanche)

1. **`fields/population.py` ≈ 369 LDC pur > garde-fou ~350** — déjà au-dessus
   AVANT ③ (363 → +5 clés familles). À éclater dans un sprint refactor, pas dans
   un tronçon catalogue.
2. **Amaryllidaceae répulsif = `adjacency_bonus`** (effet existant). Un vrai
   abaissement de pression `ravageur` serait une action moteur neuve → dette si
   on veut le rendre littéral.
3. **Mort de la bisannuelle ≈ âge 1.9** par la rampe de sénescence (longévité 2)
   AVANT le monocarpique à age≥2.0 ; les deux disent « meurt en fin d'an 2 », le
   test ne couple pas la mort à un chemin précis.

## Reste / prochain (choix Nico, pas d'enchaînement auto)

④ (faune nommée « parfums », golden-neutre) ou ⑤ (nouveaux pollinisateurs,
re-figé maîtrisé).
