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
| ④a | Scaffolding catégorie : `TrophicSpec.category` + `category_density` + 6 consommateurs recâblés | **NEUTRE** | ⬜ |
| ④b | Scinder `ravageur` → puceron/limace/doryphore | re-figé #1 | ⬜ |
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

**Prochain au choix Nico** : lancer **④a** (filet, golden-neutre — recommandé EN
PREMIER, il sécurise les scissions) ou ⑤ (pollinisateurs B, indépendant). Pas
d'enchaînement auto ; `/clear` entre chaque tronçon a→e.
