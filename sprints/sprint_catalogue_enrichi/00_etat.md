# SPRINT CATALOGUE ENRICHI — état partagé

> Lancement Python depuis `data/code/`. Filet C# : `dotnet build Symbiose.csproj`.

## Objectif

**Étoffer le catalogue de plantes ET d'animaux pour souligner leur inclusion et
leur place dans les features déjà développées** (thermique/microclimat,
pollinisation & cycle de vie, décomposition/compost, vigueur/maîtrise, écrasement,
compétition intra-plot, succession). Le cast actuel exerce inégalement ces
mécaniques ; on l'enrichit pour les mettre en valeur — et côté FAUNE on passe de
guildes abstraites à des **espèces NOMMÉES** rattachées aux guildes.

## Décisions de cadrage (2026-06-18, avec Nico)

- **Doc-conception D'ABORD** (tronçon ①, golden intact) : un doc de référence à
  étudier (matrice espèce × feature + sélection raisonnée), PUIS implémentation
  en sous-sprints écrits une fois le doc figé.
- **Périmètre = plantes ET animaux** (gros sprint → découpé).
- **Animaux = espèces NOMMÉES rattachées aux guildes existantes** (coccinelle,
  carabe, merle, hérisson, ver…), sur le patron data-driven du registre des
  pollinisateurs (`PollinatorSpec` dans `fields/population.py`). PAS de refonte
  moteur, PAS de 5ᵉ guilde sauf décision contraire du doc.

## État de l'existant (audit de départ, à approfondir dans le doc)

- **Plantes — 17** (`plants/catalogue.py`) : 8 cultivées (tomate, poivron,
  haricot, trèfle, tournesol, basilic, achillée, phacélie) + 4 adventices/succession
  (bourse-à-pasteur, minette, pâturin, pissenlit) + 5 pérennes ligneuses (figuier,
  pommier, cerisier, noyer, chêne).
- **Animaux — guildes abstraites** (`fields/population.py`) : 4 guildes trophiques
  (ravageur, auxiliaire, pollinisateur, vers_de_terre) + 3 types pollinisateurs
  NOMMÉS data-driven (abeille, syrphe, papillon) + 2 ponts larvaires
  (chenille→papillon, syrphe_larve→syrphe).
- **Familles botaniques** : `plants/base/familles.py` (Solanaceae, Fabaceae,
  Asteraceae, Lamiaceae + ligneuses). Attractivité florale par famille :
  `_ATTRACT_*` dans `population.py`.

## Tronçons

| # | Tronçon | Golden | Statut |
|---|---------|--------|--------|
| ① | Doc-conception `CONCEPTION_CATALOGUE_ENRICHI.md` (audit + matrices + sélection + partage doc/code) | INTACT (0 code) | ✅ |
| ② | Plantes lot 1 — familles connues (thym, lavande, bourrache, consoude, moutarde) | NEUTRE (hash intact) | ✅ |
| ③ | Plantes lot 2 — familles + cycles neufs (carotte, ortie, courgette, mâche, ail) + `_ATTRACT_*` + **vérif `biennial`/`evergreen`** | NEUTRE (hash intact) | ✅ |
| ④ | Faune nommée — **modèle B, champ dédié par espèce** (RE-DÉCOUPÉ a→e, voir ci-dessous). ~~parfums (A)~~ CADUC | re-figé MAÎTRISÉ large | ⬜ |
| ④a | Scaffolding catégorie : `TrophicSpec.category` + `category_density` + 6 consommateurs recâblés | **NEUTRE** | ✅ |
| ④b | Scinder `ravageur` → puceron/limace/doryphore | re-figé #1 | ✅ |
| ④c | Scinder `auxiliaire` → coccinelle/chrysope/carabe/merle/hérisson | re-figé #2 | ⬜ |
| ④d | Scinder `detritivore` → lombric/cloporte (decomp→lombric, fruit pourri→cloporte) | re-figé #3 | ⬜ |
| ④e | Encyclopédie (blurb/interconnexions) + tests + stub pont | NEUTRE | ⬜ |
| ⑤ | Faune nommée — **nouveaux pollinisateurs** (bourdon, osmie) : registre data-driven | re-figé maîtrisé (pollen/nouaison) | ⬜ |
| ⑥ | Vue Godot / sprites / encyclopédie + protocole pont `target.espece` | NEUTRE | ⬜ |

## §REPRISE

**① CLOS** le 2026-06-18 — doc figé `docs/conception/CONCEPTION_CATALOGUE_ENRICHI.md`
(golden `5fddfe54…` intact, doc seul). Découpage ②→⑥ arrêté ci-dessus (détail
§7 du doc). **Alerte moteur** : `life_cycle="biennial"` et
`winter_strategy="evergreen"` sont codés mais **jamais exercés** → ③ devra les
vérifier (trou possible).

**② CLOS** le 2026-06-18 — +5 plantes : thym/lavande (`aromatiques.py`, nouveau
fichier, Lamiacées evergreen) + bourrache/consoude/moutarde (`compagnes.py`,
217 LDC). Câblées `species/__init__.py`, `plants/__init__.py`, `catalogue.py`
(PLANT_CATALOGUE seul ; WEED_/PERENNIAL_ intacts). Golden **NEUTRE** (hash
`5fddfe54…` inchangé — espèces non plantées par le smoke). Chemin
`winter_strategy="evergreen"` désormais EXERCÉ : nouveau `tests/test_evergreen.py`
(thym vivant + feuillé après hiver ; 5 espèces germent). `biennial` reste à
vérifier en ③ (carotte/ail).

**③ CLOS** le 2026-06-18 — +5 plantes, 5 familles botaniques NEUVES :
- `species/potageres.py` (nouveau fichier — cultivees.py déjà à ~308 LDC, le
  garde-fou interdisait l'ajout) : carotte (Apiaceae), courgette (Cucurbitaceae),
  mâche (Caprifoliaceae) ; `species/sauvages.py` (nouveau) : ortie (Urticaceae) ;
  ail (Amaryllidaceae) ajouté à `compagnes.py`.
- 2 familles neuves PORTANT un effet familial → classes dans `familles.py`
  (`Urticaceae` = injection fertilité/biomasse azotée ; `Amaryllidaceae` =
  répulsif via `adjacency_bonus reduce_maladie_rondelle`). Les 3 autres (Apiaceae,
  Cucurbitaceae, Caprifoliaceae) sans effet familial → `family="…"` au niveau
  espèce (patron Phacelia/Borage). `_ATTRACT_*` (×3) étendus aux 5 familles
  (Apiaceae syrphe=1.0 ; Urticaceae anémophile 0.0 partout).
- **GATE BISANNUEL comblé** (`sim/engine/croissance.py`, `_bolt_bloque`) : une
  bisannuelle ne franchit pas son stade de montaison (1er stade fleuri) tant que
  `age_years < 1.0` → rosette l'an 1, ombelle/hampe l'an 2, puis mort. AUCUNE
  espèce du smoke n'est bisannuelle → golden NEUTRE (si ce gate l'avait bougé,
  c'eût été une fuite, pas un re-figeage).
- Golden **NEUTRE** (hash `5fddfe54…` inchangé). Tests neufs :
  `tests/test_biennial.py` (carotte+ail : rosette an 1, montaison an 2, mort) +
  `tests/test_catalogue_lot2.py` (sanity 5 clés, attractivité syrphe/ortie,
  courgette fruitier pollinisée vs sans pollen). evergreen non-régressé.
- ⚠️ **Signalements** : (1) `fields/population.py` ≈ 369 LDC pur > garde-fou ~350
  — DÉJÀ au-dessus avant ③ (363 → +5 clés familles) ; à éclater dans un futur
  sprint refactor, pas dans un tronçon catalogue. (2) Amaryllidaceae répulsif =
  `adjacency_bonus` (effet existant) ; un vrai abaissement de pression `ravageur`
  serait une action moteur neuve → dette si on veut le rendre littéral. (3) Mort
  de la bisannuelle ≈ âge 1.9 par la RAMPE de sénescence (longévité 2) AVANT le
  déclencheur monocarpique à age≥2.0 ; les deux disent « meurt en fin d'an 2 »,
  le test ne couple pas la mort à un chemin précis.

**Tournant ④ — modèle A abandonné, modèle B tranché** (2026-06-19, Nico) : le
kickoff `04_faune_parfums.md` (modèle **A « parfum »** = sprite-variante, triade
mutualisée au niveau guilde) est **CADUC**. Nico a tranché le **modèle B** :
**chaque animal a SA triade propre** (nourriture/prédateur/habitat) et **les
guildes deviennent des catégories** (les espèces remplacent les champs). C'est une
**refonte de la vie macro** (3 champs → 10), pas un ajout cosmétique. Conception
FIGÉE : `docs/conception/CONCEPTION_FAUNE_DEDIEE.md` (amende §5.1 du catalogue).
Audit clé : **6 consommateurs lisent `populations[guilde]` en dur** dont la SANTÉ
des plantes (`perturbations.py`) → d'où le re-figeage golden large mais maîtrisé.

**Stratégie de migration** : ④ re-découpé en **a→e** pour des re-figeages
LOCALISÉS (une catégorie à la fois). ④a pose le filet (`category_density`) et reste
**golden NEUTRE** (invariant de contrôle) ; ④b/c/d scindent chacun une catégorie
(un nouveau hash attribuable chacun) ; ④e = encyclo+tests, neutre.

**④a CLOS** le 2026-06-19 — filet de catégorie posé, golden **NEUTRE** (hash
`5fddfe54…` inchangé) :
- `TrophicSpec` gagne `category: str` (champ requis) ; les 3 specs trophiques
  taguées (`ravageur`/`auxiliaire`/`detritivore` — le `name` du champ reste
  `vers_de_terre` jusqu'à ④d) + les pollinisateurs `category="pollinisateur"`
  (catégorie isolée, lue par aucun agrégat trophique).
- `EcoFields.category_fields(cat)` (liste des champs membres) + `category_density(
  cat, r, c)` (somme des densités) — la guilde devient une VUE.
- **6 consommateurs recâblés** : santé des plantes `perturbations.py` (C1 ravageur,
  C2 auxiliaire → `category_density`) ; vigueur macro `vigueur_macro.py` (C3/C4/C5 →
  `_vigueur_categorie` qui itère `category_fields` en sommant `densité×activité` —
  PAS un simple `category_density`, sinon on perdrait le facteur Qi trophique).
  `decomp_speed` (C6) et `gestes.py:420` (C8) **inchangés** (champ encore nommé
  `vers_de_terre`).
- À un membre par catégorie, agrégat == champ unique → **golden NEUTRE prouvé**
  (golden `5fddfe54…`, pop-golden `5e6e688f…`, vigueur-traj `e63b9d7f…` inchangés ;
  suites complètes vertes ; `dotnet build` OK).

**④b CLOS** le 2026-06-19 — `ravageur` scindé en 3 champs NOMMÉS (modèle B), golden
**re-figé MAÎTRISÉ #1** :
- `build_population_specs()` pose 3 specs `category="ravageur"`, triades PROPRES :
  - **puceron** = ex-triade ravageur intégrale (feuillage + chaleur), fenêtre estivale
    10/13 ; prédateurs nommés `(coccinelle, chrysope, syrphe_larve)`.
  - **limace** = DÉTRITIVORE préférentielle : `_limace_food_grid` = litière dominante
    (`LIMACE_LITTER_W=1.0`) + feuillage tendre secondaire (`LIMACE_FOLIAGE_W=0.3`) ;
    habitat humide/frais (`_humide_litiere_grid`), fenêtre précoce/large 9/12 ;
    signal fruit-pourri (`signal_fn=_rav_fruit_signal`) ; prédateurs `(carabe, herisson)`.
  - **doryphore** = SPÉCIALISTE Solanaceae : ressource/habitat NULS sans Solanaceae
    (`_foliage_solanaceae_grid` / `_solanaceae_grid`), habitat RÉDUIT par l'ail
    (`DORY_AIL_REPULSE`, Amaryllidaceae §4.4) ; fenêtre estivale 10/13 ; prédateur `(carabe,)`.
- La guilde `ravageur` devient une **VUE** : `_ravageur_grid` (ressource auxiliaire C11)
  et l'herbivorie C1 lisent `category_density("ravageur")` = somme des 3 densités.
- **Régression transitoire ASSUMÉE (④b→④c)** — décision Nico « noms dès ④b » : les
  prédateurs nommés n'existent pas encore (④c) → `_predator_field` rend None → prédation
  0 → ravageurs non régulés → pression herbivore accrue. C'est une cause MAJEURE du
  re-figeage, attendue, résorbée en ④c.
- **Re-figeage attribuable** : golden `5fddfe54…` → **`63d50eeb22…`** ;
  pop-golden `5e6e688f…` → **`1f7dcda831…`** ; vigueur-traj **`e63b9d7f…` INCHANGÉ**
  (la trajectoire Vigueur joueur ne dépend pas de la régulation des ravageurs).
- Recâblages : `simserver/actions.py:ecraser` (défaut sprite `ravageur`→`puceron`,
  le champ `ravageur` n'existe plus — réacheminement `target.espece` = dette ⑥) ;
  ~10 suites de tests adaptées (clé `ravageur`→`puceron` ou `category_density`).
- Test neuf : `tests/test_faune_dediee.py` (6 fonctions, 23 checks — existence/triades,
  agrégat=somme, fenêtres, doryphore Solanaceae+ail, limace litière-dominante). `dotnet build` OK.
- ⚠️ **Signalements** :
  1. **`fields/population.py` = 449 LDC pur** (873 total, 310 commentaires) > garde-fou
     ~350 — DÉJÀ au-dessus avant ④b (~369), +80 par les 3 triades. À **éclater en
     paquet** `fields/population/` dans un futur sprint refactor (pas dans un tronçon
     catalogue). À arbitrer avec Nico.
  2. **Deux échecs PRÉ-EXISTANTS hors périmètre** (prouvés sur HEAD propre via `git stash`,
     PAS causés par ④b) : `test_senescence` (plante « meurt asphyxié, excès d'eau soutenu »
     à ~2.7 ans sur terre/hum1.5 — modèle eau) ; `test_sim_server` pommier nouaison
     (0 fruit @ S52 — chaîne pollinisation gardée au niveau unitaire : test_fruits 24/24,
     test_ruche 20/20). → dette, à traiter séparément.

**Prochain au choix Nico** : ④c (scinder auxiliaire → coccinelle/chrysope/carabe/
merle/hérisson — résorbe la régression de prédation, re-figé #2) ou ⑤ (pollinisateurs
B, indépendant). Pas d'enchaînement auto ; `/clear` entre tronçons.
