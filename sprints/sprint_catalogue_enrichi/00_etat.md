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
| ④ | Faune nommée — **modèle B, champ dédié par espèce** (RE-DÉCOUPÉ a→e, voir ci-dessous). ~~parfums (A)~~ CADUC | re-figé MAÎTRISÉ large | ✅ |
| ④a | Scaffolding catégorie : `TrophicSpec.category` + `category_density` + 6 consommateurs recâblés | **NEUTRE** | ✅ |
| ④b | Scinder `ravageur` → puceron/limace/doryphore | re-figé #1 | ✅ |
| ④c | Scinder `auxiliaire` → coccinelle/chrysope/carabe/merle/hérisson | re-figé #2 | ✅ |
| ④d | Scinder `detritivore` → lombric/cloporte (decomp→lombric, fruit pourri→cloporte) | re-figé #3 | ✅ |
| ④e | Encyclopédie (blurb/interconnexions) + tests + stub pont | NEUTRE | ✅ |
| ⑤ | Faune nommée — **nouveaux pollinisateurs** (bourdon, osmie) : registre data-driven | re-figé maîtrisé (pollen/nouaison) | ✅ |
| ⑥a | Python : encyclopédie 5 pollinisateurs + protocole pont `target.espece` | NEUTRE | ✅ |
| ⑥b | C# / Godot : table sprite par espèce + butineurs B + heatmaps + bascule client `target.espece` | NEUTRE (vue) | ⬜ |

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

**④c CLOS** le 2026-06-19 — `auxiliaire` scindé en 5 champs NOMMÉS (modèle B), golden
**re-figé MAÎTRISÉ #2** :
- `build_population_specs()` pose 5 specs `category="auxiliaire"`, triades PROPRES,
  via la fabrique `_espece_grid(name)` (chasse SA proie fraîchement mise à jour) :
  - **coccinelle** = héritière du champ `auxiliaire` (salt identique → continuité
    sprites) ; proie `puceron`, habitat `_stability_grid`, fenêtre estivale 10/13.
  - **chrysope** = proie `puceron`, habitat `_auxiliaire_habitat_grid` (rondelle), 10/13.
  - **carabe** = proie `limace`, habitat `_undisturbed_structure_grid` (sol non perturbé
    + bump des structures `pile`/bois mort), fenêtre précoce 9/12.
  - **merle** = OMNIVORE : nourriture `_merle_food_grid` (fruit FRAIS `_aux_fruit_signal`
    repromu de signal additif en RESSOURCE + agrégat `category_density("detritivore")`),
    habitat plancher uniforme `MERLE_BASE_HABITAT=0.20`, fenêtre large 8.5/10.
  - **hérisson** = proie `limace`, habitat `_pile_grid` (NUL sans pile posée → dépend
    ENTIÈREMENT d'un aménagement joueur), fenêtre 9/12.
- **Boucles proie↔prédateur ACTIVES** : les prédateurs nommés posés en ④b
  (coccinelle/chrysope sur puceron, carabe/hérisson sur limace) existent enfin comme
  champs → `_predator_field` les résout → prédation appliquée (avec un lag d'une
  semaine, ils tickent après les ravageurs) → **résorbe la régression transitoire ④b**.
- **Habitats sur STRUCTURES** (`pile`, ⑤) lus en duck-typing sur `eco.structures`
  (comme `_abeille_habitat_grid` lit les ruches — pas de cycle de couche). À ZÉRO
  structure (cas du smoke) → termes nuls → cette part reste **golden NEUTRE**.
- **Réconciliation kickoff↔doc** : le kickoff disait `_ravageur_grid` → SUPPRIMÉ,
  mais le doc figé §4 liste le **pont syrphe inchangé** (il lit `_ravageur_grid`).
  Décision : `_ravageur_grid` CONSERVÉ pour le seul pont syrphe (doc = source de
  vérité) ; retiré uniquement comme ressource des auxiliaires (désormais `_espece_grid`).
- `signal_fn=_aux_fruit_signal` RETIRÉ de l'auxiliaire (devient la ressource du merle) ;
  `_rav_fruit_signal` reste utilisé par la limace.
- **Re-figeage attribuable** : golden `63d50eeb…` → **`533276328199…`** ;
  pop-golden `1f7dcda831…` → **`e707002f435b…`** ; vigueur-traj **`e63b9d7f…` INCHANGÉ**
  (la trajectoire Vigueur joueur ne dépend pas de la régulation des ravageurs).
- ~7 suites adaptées (clé `auxiliaire`→`coccinelle` ou `category_density`, listes
  d'espèces 8→12). Test neuf : `test_faune_dediee.py` +4 fonctions (5 auxiliaires,
  proies propres, habitats `pile`, merle omnivore) → 10 fonctions au total, vertes.
  `dotnet build` OK (0 erreur — ④c est Python pur).
- ⚠️ **Signalements** :
  1. **`fields/population.py` toujours > garde-fou ~350 LDC** (encore alourdi par les
     5 triades) → à **éclater en paquet** `fields/population/` dans un futur sprint
     refactor (hors tronçon catalogue). À arbitrer avec Nico.
  2. **Mêmes deux échecs PRÉ-EXISTANTS hors périmètre** (re-prouvés sur HEAD ④b via
     `git stash`, PAS causés par ④c) : `test_senescence` (~2.7 ans) ; `test_sim_server`
     pommier nouaison (0 fruit @ S52, suite 183/184). → dette, à traiter séparément.
  3. **Observation** : `test_auxiliaires.py` (diagnostic NON-assertif) montre désormais
     **0 dégât herbivorie sur les DEUX tuiles** (AUX et TÉMOIN) sur 30 ans — conséquence
     attendue des boucles refermées (coccinelle régule le puceron même sans rondelle).
     Le scénario ne distingue plus AUX/TÉMOIN ; à revisiter si on veut re-mesurer
     l'effet attire-auxiliaire (le levier est désormais l'HABITAT, pas la simple
     présence). Pas un blocage : aucune assertion, script de mesure.

**④d CLOS** le 2026-06-19 — `detritivore` scindé en 2 champs NOMMÉS (modèle B),
golden **re-figé MAÎTRISÉ #3**. Dernière scission, l'écosystème faune est refermé :
- `build_population_specs()` pose 2 specs `category="detritivore"` en **position
  PROIE** (après ravageurs, avant auxiliaires → prédateurs les lisent frais) :
  - **lombric** = héritier du champ `vers_de_terre` (salt identique → continuité
    sprites) ; humus du sol (`_soil_food_grid` / habitat `_undisturbed_grid`),
    proie `(merle, herisson)`, fenêtre LARGE `8.5/10`. **Pilote `decomp_speed`.**
  - **cloporte** = litière + fruit pourri (`_litter_grid` / `_humide_litiere_grid`),
    proie `(carabe, herisson)`, `signal_fn=_rav_fruit_signal`, fenêtre `9/12`.
- `signal_fn=_rav_fruit_signal` **retiré de la limace** (le pourri passe au cloporte,
  défaut « cloporte seul » du kickoff §C13).
- Recâblages moteur : `_merle_food_grid` lit `_espece_grid("lombric")` (était
  `category_density("detritivore")` — le merle mange le ver, pas le cloporte) ;
  `container.py` `decomp_speed` + `tick_decomposition` → `populations["lombric"]` ;
  `gestes.py:becher` → `["lombric"]` ; `constants.py` commentaire maj. C5 vigueur
  **inchangé** (`_vigueur_categorie("detritivore")` somme auto depuis ④a).
- **Re-figeage attribuable** : golden `533276328199…` → **`9be1c05a7282…`** ;
  pop-golden `e707002f435b…` → **`58ecf6d89e21…`** ; vigueur-traj **`e63b9d7f…`
  INCHANGÉ**. Causes (toutes ④d) : ordre de tick (détritivores en proie), prédation
  du lombric active (merle/hérisson, était 0), cloporte neuf, limace perd le pourri,
  `decomp_speed` sur lombric seul.
- ~4 suites adaptées (clé `vers_de_terre`→`lombric`/`cloporte`, listes 12→13).
  Test neuf : `test_faune_dediee.py` +2 fonctions (2 détritivores nommés, decomp suit
  le lombric) ; `test_attraction` 2 tests renommés ravageur→détritivore.
  `dotnet build` OK (Python pur).
- ⚠️ **Signalements** : (1) `fields/population.py` toujours > garde-fou ~350 LDC →
  éclatement en paquet `fields/population/` dans un sprint refactor dédié. (2) Mêmes
  deux échecs PRÉ-EXISTANTS hors périmètre (`test_senescence` ~2.7 ans ;
  `test_sim_server` pommier nouaison 0 fruit @ S52). (3) Dette détritivore littérale :
  `decomp_speed` ne lit que le lombric (humus), le cloporte (litière) ne décompose
  pas encore — choix assumé kickoff §5.3.

**④e CLOS** le 2026-06-19 — encyclopédie + tests + stub pont, golden **NEUTRE**.
**④ (faune nommée) COMPLET côté Python.**
- `fields/faune_encyclo.py` (NOUVEAU, donnée pure 0 import) : `FAUNE_ENCYCLO`
  {name: (blurb, interconnexions)} sur les 10 espèces + `encyclo_meta(name)`
  (splat dans `TrophicSpec` ; inconnu → vide). Séparé de `population.py` (déjà
  > garde-fou).
- `TrophicSpec` gagne `blurb`/`interconnexions` = **DONNÉE PURE jamais lue par
  `tick`** ; `fields/__init__.py` ré-exporte ; `serialize.py` = commentaire stub
  (snapshot par espèce DÉJÀ acquis depuis ④b, clé `f.spec.name`).
- `test_faune_dediee.py` → 17 fonctions (+couverture 10 espèces, salts distincts,
  phénologie hiver, blurb non vide, `predators ⊆ interconnexions`, graphe
  SYMÉTRIQUE). Correction data : `herisson` cite `lombric` (symétrie).
- Golden `9be1c05a…` / pop `58ecf6d8…` **INCHANGÉS** (neutre prouvé) ; `dotnet
  build` OK.

**Bilan refonte faune B** (3 re-figeages localisés, vigueur `e63b9d7f…` inchangé) :
④a NEUTRE (`5fddfe54`) → ④b `63d50eeb` → ④c `53327632` → ④d `9be1c05a` (golden
final) → ④e neutre. 3 champs abstraits → 10 espèces nommées data-driven.

**Frontière ⑥** : sérialisation par espèce acquise ; reste table sprite par
espèce côté client + protocole `target.espece` (réacheminement actions ciblées).

**⑤ CLOS** le 2026-06-19 — 2 pollinisateurs NOMMÉS (bourdon, osmie) ajoutés au
registre data-driven `build_pollinator_registry()` (modèle `PollinatorSpec`),
golden **re-figé MAÎTRISÉ** (pollen → nouaison) :
- `fields/population.py` : salts `_SALT_BOURDON=0x2AD001` / `_SALT_OSMIE=0x2AE001` ;
  `POLLINATOR_NAMES` 3→5 (load-bearing : lu par butineurs + `pollinator_density`
  + `vigueur_macro`) ; attractivités `_ATTRACT_BOURDON` (Fabaceae/Lamiaceae=1.0,
  Solanaceae=0.65 *buzz pollination*) / `_ATTRACT_OSMIE` (Rosaceae=1.0,
  Apiaceae=0.85) ; foragers `_FORAGER_BOURDON` (n_max=8, deposit=0.6) /
  `_FORAGER_OSMIE` (n_max=5, deposit=0.6) ; `_osmie_habitat_grid` (rondelle
  pollinisateur + bump structures `pile` = niche-bois, duck-typing comme les
  habitats ④c) ; 2 entrées registre — bourdon (daylen 9.5/12.0 précoce), osmie
  (10.0/12.5 printanier, habitat dédié). `bridge=None` (pas de pont larvaire).
- `ecofields/container.py` : commentaire maj (5 pollinisateurs).
- **Re-figeage attribuable** : golden `9be1c05a…` → **`f7e1a9b43b24…`** (plus de
  pollen → plus de nouaison → fruits → aval décompo) ; pop-golden `58ecf6d8…` →
  **`a39834dfb1e6…`** (dérive PUREMENT ADDITIVE : 13 champs existants byte-identiques,
  bourdon/osmie ajoutés au digest, ni proie ni prédateur) ; vigueur-traj
  **`e63b9d7f…` INCHANGÉ**.
- Tests : `test_faune_dediee.py` +section 9 (5 fonctions, 26 checks pollinisateurs B) ;
  `test_population.py` `GUILDS` += bourdon/osmie ; `simserver/macro.py`+`fields.py`
  GUILDES 13→15. `dotnet build` OK.
- ⚠️ **Signalements** : (1) `fields/population.py` toujours > garde-fou ~350 LDC
  (alourdi par les 2 triades pollinisateurs) → éclatement en paquet
  `fields/population/` dans un sprint refactor dédié. (2) Mêmes deux échecs
  PRÉ-EXISTANTS hors périmètre (`test_senescence` ~2.7 ans ; `test_sim_server`
  pommier nouaison 0 fruit @ S52 — suite 183/184). (3) Encyclopédie
  (blurb/interconnexions) des pollinisateurs NON faite (jamais eu d'entrée
  `FAUNE_ENCYCLO`) → reste à ⑥ avec sprites + `target.espece`, comme prévu §7.3.

**⑥ scindé** (2026-06-19, avec Nico) en **⑥a (Python testable)** + **⑥b (C#/Godot,
F5 = Nico)** — deux natures de travail : ⑥a vérifiable bout en bout (golden + suite
+ `dotnet build`), ⑥b ne l'est qu'au `dotnet build` (rendu visuel = F5 Nico).
Cadrage validé : encyclo = **données seules des 5 pollinisateurs** (pas d'UI Godot,
n'existe pas → sprint séparé) ; sprites = **placeholders procéduraux par espèce**
(pas de PNG d'insectes).

**⑥a CLOS** le 2026-06-19 — Python pur, golden **NEUTRE** (donnée pure + repli
protocole sans effet moteur) :
- **Encyclopédie des 5 pollinisateurs** (`fields/faune_encyclo.py`) : abeille,
  syrphe, papillon, bourdon, osmie ajoutés à `FAUNE_ENCYCLO` (blurb + graphe).
  Aucun pollinisateur n'avait d'entrée jusque-là (ni les 2 de ⑤ ni les 3 anciens).
  Tokens non-trophiques : `fruit`, `ruche`/`miel`, `pile`, `chenille`/`syrphe_larve`,
  `puceron`. Hors sous-graphe trophique symétrique (pas de proie réciproque).
- **Splat** : `build_pollinator_specs()` (population.py) ajoute `**encyclo_meta(
  ps.name)` au `TrophicSpec` généré → les 5 portent blurb/interconnexions. DONNÉE
  PURE jamais lue par `tick`.
- **Protocole `target.espece`** (`tools/simserver/actions.py:ecraser`) : clé
  canonique `espece`, `guilde` accepté en repli (`target.get("espece",
  target.get("guilde", "puceron"))`) → pas de casse client entre ⑥a et ⑥b. Variable/
  message renommés `guilde`→`espece` ; commentaire stub `serialize.py` maj.
- **3 goldens INCHANGÉS** : golden `f7e1a9b4…`, pop-golden `a39834df…`, vigueur-traj
  `e63b9d7f…`. Tests neufs : `test_faune_dediee.py` section 10 (encyclo
  pollinisateurs) ; `tests/simserver/actions.py` bascule clé `espece` + cas repli
  `guilde`. Suite verte SAUF 2 échecs PRÉ-EXISTANTS (`test_senescence` ~2.7 ans ;
  `test_sim_server` pommier nouaison 0 fruit @ S52 → 184/185). `dotnet build` OK.
- Confirmé : le snapshot `sprites` émet **15 clés d'espèce** (10 trophiques + 5
  pollinisateurs) — sérialisation par espèce prête pour la table sprite client ⑥b.
- ⚠️ Signalement inchangé : `fields/population.py` toujours > garde-fou ~350 LDC →
  éclatement en paquet `fields/population/` dans un sprint refactor dédié.

**Reste : ⑥b (vue Godot, C#)** — clôt le sprint. `MacroLife.cs` mappe encore les 3
anciennes guildes (`ravageur`/`auxiliaire`/`vers_de_terre`) → les 10 espèces
nommées tombent en point gris `GuildeInconnue` : étendre la table sprite par espèce
(placeholders procéduraux). + butineurs bourdon/osmie (`ForagerLayer.cs`), heatmaps
par catégorie (`FieldOverlay.cs`), émission `target.espece` (`WorldView.Actions.cs`).
Pas d'enchaînement auto ; `/clear` avant ⑥b.
