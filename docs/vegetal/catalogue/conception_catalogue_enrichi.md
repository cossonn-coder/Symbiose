# CONCEPTION — CATALOGUE ENRICHI (plantes + animaux nommés)

> Conception **figée** le 2026-06-18 (Sprint catalogue enrichi, tronçon ①).
> Doc de RÉFÉRENCE à étudier — **aucun code écrit** (golden intact par
> construction). Les tronçons d'implémentation ②+ dérivent de la §7.
> Sources lues : `plants/catalogue.py`, `plants/species/*`, `plants/perennials.py`,
> `plants/base/familles.py`, `fields/population.py`, `fields/lifecycle.py`,
> `fields/foragers.py`, `fields/apiculture.py`, les `docs/conception/*`.

---

## 1. Intention & cadrage

Le moteur a accumulé, sprint après sprint, des **features écologiques riches** :
thermique/microclimat, pollinisation & cycle de vie, décomposition/compost,
vigueur/maîtrise, écrasement, compétition intra-plot, succession. Chacune lit des
**champs de donnée** portés par les espèces (`winter_strategy`, `floraison`,
`fruitier`, `archetype`, `resistance_ecrasement`, `strate`…). Or le **cast actuel
les exerce inégalement** : beaucoup de leviers existent dans le modèle mais
restent **morts** faute d'une espèce qui les active (aucune `evergreen`, aucune
`biennial`, une seule famille mellifère profonde, pas d'ombellifère pour les
syrphes, faune réduite à des guildes abstraites…).

**Objet du sprint** : étoffer le catalogue — plantes ET animaux — pour
**souligner l'inclusion de chaque espèce dans les features déjà développées**.
Côté faune, on passe de **guildes abstraites** à des **espèces NOMMÉES**
rattachées aux guildes existantes (patron data-driven `TrophicSpec`/
`PollinatorSpec`).

**Cadrage (décisions du 2026-06-18, `00_etat.md`)** :
- **Doc d'abord** (ce tronçon, golden intact), implémentation en lots ensuite.
- **Périmètre = plantes ET animaux** → gros sprint, découpé.
- **Pas de refonte moteur, pas de 5ᵉ guilde** sauf décision contraire ci-dessous.
- **Interconnexion obligatoire** ([[regle_interconnexion_acteurs]]) : chaque
  ajout doit être relié aux autres acteurs — c'est le but même du sprint.

---

## 2. Audit de l'existant — le vocabulaire de raccordement

### 2.1 Les champs de donnée qui relient une espèce à une feature

| Feature | Champs lus (où) | Ce qu'ils encodent |
|---|---|---|
| **Thermique / gel** | `winter_strategy` (die/dormant/evergreen), `deciduous`, `foliage_density` (→ ombre → T_sol), `temp_min_growth` | gélive vs rustique ; ombre portée ; couvert hivernal (litière) |
| **Pollinisation** | `floraison` (gates `gdd_floraison`/`bloom_daylen_*`), `pollination_mode` (insect/wind/self), **famille** (→ `_ATTRACT_*`) | quand/combien de nectar, perçu par quel type |
| **Cycle de vie** | famille hôte (ressource larvaire = feuillage), `LifeCycleBridge` | plante-hôte des chenilles ; proie des larves de syrphe |
| **Décompo / compost** | `fruitier` + `maturity_years`, tissus de litière (`feuille`/`fruit`/`tige`/`bois`), `reproduction_rate` | fruits tombés (attraction faune), qualité/azote de la litière |
| **Vigueur / maîtrise** | **famille** botanique + concept écologique (5 paliers chacun), organes comestibles (`manger`), effets `recolte` | à quel axe de maîtrise l'espèce contribue ; Vigueur rendue |
| **Écrasement** | `resistance_ecrasement`, `stimulation_ecrasement` | plie/casse sous le pied ; repart ou non |
| **Compétition intra-plot** | `strate`, `foliage_density`, `shade_tolerance`, `space_tolerance_weeks`, `root_radius` | qui ombre qui ; qui encaisse la promiscuité |
| **Succession** | `archetype` (pioneer/nitrogen_fixer/grass/competitor), `rarity`, `reproduction_rate` | place dans la dynamique sol-nu → climax |

### 2.2 Les 17 plantes actuelles

| Nom | Famille | Cycle | Hiver | Strate mature | Fruitier | Mots-clés saillants |
|---|---|---|---|---|---|---|
| Tomate | Solanaceae | annual | die | moyenne | **oui** | Mellifère, Compagne, Tuteur |
| Poivron | Solanaceae | annual | die | moyenne | — | Mellifère, Compagne |
| Haricot | Fabaceae | annual | die | grimpante | — | Fixatrice N₂, Grimpante |
| Trèfle | Fabaceae | perennial | dormant | sol | — | Fixatrice N₂, Couvre-sol, Mellifère |
| Tournesol | Asteraceae | annual | die | haute | — | Mellifère, Structurante, Accumulatrice |
| Basilic | Lamiaceae | annual | die | basse | — | Compagne, Mellifère, Dynamisante |
| Achillée | Asteraceae | perennial | dormant | basse | — | **Auxiliaire**, Mellifère, Médicinale |
| Phacélie | Boraginaceae | annual | die | basse | — | **Auxiliaire**, Mellifère, Engrais vert |
| Bourse-à-pasteur | Brassicaceae | annual | die | basse | — | Pionnière, Compost (`pioneer`) |
| Minette | Fabaceae | perennial | dormant | sol | — | Fixatrice N₂ (`nitrogen_fixer`) |
| Pâturin | Poaceae | perennial | dormant | basse | — | Couvre-sol, Invasive (`grass`) |
| Pissenlit | Asteraceae | perennial | dormant | basse | — | Accumulatrice, Bioindicatrice (`competitor`) |
| Figuier | Moraceae | perennial | dormant (caduc) | haute | **oui** | Fruitier, Ombre dense |
| Pommier | Rosaceae | perennial | dormant (caduc) | haute | **oui** | Fruitier, Mellifère |
| Cerisier | Rosaceae | perennial | dormant (caduc) | haute | **oui** | Fruitier, Mellifère |
| Noyer | Juglandaceae | perennial | dormant (caduc) | haute | — | Anémophile, Ombre dense |
| Chêne | Fagaceae | perennial | dormant (caduc) | haute | — | Anémophile, Centenaire |

**Familles présentes (11)** : 5 avec **classe + effets familiaux** (Solanaceae
mildiou, Fabaceae N₂, Asteraceae mellifère, Lamiaceae répulsif, Poaceae hydrique)
+ 6 en **simple chaîne `family`** sans effets (Brassicaceae, Boraginaceae,
Moraceae, Rosaceae, Juglandaceae, Fagaceae).

### 2.3 La faune actuelle — guildes & types

| Guilde / type | Ressource | Habitat | Prédateurs | Pont larvaire |
|---|---|---|---|---|
| **ravageur** | feuillage (santé×canopée) | monoculture (1−diversité) | auxiliaire, syrphe_larve | — |
| **auxiliaire** | le ravageur (proie) + fruit frais | nectar (rondelle) + stabilité | — | — |
| **vers_de_terre** | microbiome + MO (om_fresh/active) | sol non perturbé | — | — |
| **abeille** (poll.) | nectar = floraison×attractivité abeille | rondelle poll. + bump ruche | — | — |
| **syrphe** (poll.) | nectar (préf. composées/ombellifères) | rondelle auxiliaire | — | syrphe_larve→syrphe |
| **papillon** (poll.) | nectar (préf. tubulaires) | rondelle poll. | — | chenille→papillon |

**Constat clé** : seuls les **pollinisateurs sont nommés** (registre
`PollinatorSpec` data-driven). Ravageur, auxiliaire, vers de terre restent des
**guildes anonymes** — le joueur voit « un nuisible », pas « un puceron ».

---

## 3. Matrice espèce × feature (EXISTANT) — révéler les trous

`++` = exerce fortement · `+` = exerce · `—` = n'exerce pas / inerte.

| Espèce | Thermique | Pollinis. | Cycle vie | Décompo | Vig/Maît | Écras. | Compét. | Success. |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Tomate | + (die) | + abeille faible | hôte | ++ fruit | ++ manger/récolte | + casse | + moyenne | — |
| Poivron | + (die) | + | hôte | + | + récolte | + | + | — |
| Haricot | + (die) | + | hôte | + | + récolte | + casse | + grimpante | + pionnière |
| Trèfle | ++ dormant | ++ mellifère | — | + N₂ | + manger | ++ piétinable | ++ couvre-sol | ++ N₂ |
| Tournesol | + (die) | ++ mellifère | hôte | + tiges | + récolte | ++ décapité | ++ haute/ombre | + structurante |
| Basilic | + (die) | + | hôte | + | ++ manger | + pincement | + bas | — |
| Achillée | ++ dormant | ++ syrphe/auxil. | — | + | + médicinale | ++ stolons | + bas | — |
| Phacélie | + (die) | ++ abeille/syrphe | — | + engrais vert | + | + | + engrais vert | + |
| Bourse-à-p. | + (die) | + (Brassic.) | hôte | ++ MO/compost | + | + rosette | + | ++ `pioneer` |
| Minette | ++ dormant | + mellifère | hôte | + | + | ++ rampant | ++ couvre-sol | ++ `nitrogen_fixer` |
| Pâturin | ++ dormant | — (anémophile) | — | + MO racin. | + | ++ **talle** | ++ hydrique | ++ `grass` |
| Pissenlit | ++ dormant | + mellifère | — | + | + accumul. | ++ rosette | ++ pivot | ++ `competitor` |
| Figuier | ++ caduc | — | — | ++ fruit/feuille | + manger | inécrasable | ++ ombre dense | — climax |
| Pommier | ++ caduc | ++ mellifère | hôte | ++ fruit | ++ manger/récolte | inécrasable | ++ haute | — |
| Cerisier | ++ caduc | ++ mellifère | hôte | ++ fruit | + manger | inécrasable | ++ haute | — |
| Noyer | ++ caduc | — anémophile | — | ++ feuille coriace | + | inécrasable | ++ ombre dense | + lisière |
| Chêne | ++ caduc | — anémophile | — | ++ feuille coriace | + | inécrasable | ++ ombre dense | ++ sentinelle |

### 3.1 Trous nommés

1. **Thermique** — *aucune* espèce `evergreen` (le levier `winter_strategy=
   "evergreen"` est codé mais **jamais exercé**) ; pas de **couvre-sol d'hiver**
   actif en jours courts ; la palette « gélive (die) » est sur-représentée chez
   les cultivées. → manque des **rustiques persistantes** pour rendre le gel
   nocturne ⑥ lisible (qui meurt / qui tient sous le manteau neigeux).
2. **Cycles de vie** — `life_cycle="biennial"` codé mais **jamais utilisé** : pas
   une seule **bisannuelle** (rosette qui passe l'hiver puis monte à fleur l'an 2).
3. **Pollinisation** — mellifères **profondes** (abeille) concentrées sur
   Lamiaceae/Boraginaceae à 1 espèce chacune ; **aucune Apiaceae** (ombellifères :
   la ressource n°1 des **syrphes** et auxiliaires !) ; **aucune plante-hôte
   dédiée aux chenilles** (les ponts larvaires existent mais s'appuient sur le
   feuillage générique, pas sur une vraie plante-nourricière nommée).
4. **Décompo** — fruitiers limités à 1 annuelle (tomate) + 3 arbres ; pas de
   **biomasse-paillis** dédiée (accumulatrice à couper-déposer) ; litière peu
   contrastée en **azote** (riche/molle) vs **carbone** (coriace).
5. **Familles** — 6 familles n'ont qu'**une** espèce ; Rosaceae uniquement en
   arbres (0 herbacée) ; familles-clés absentes : **Apiaceae** (ombellifères),
   **Cucurbitaceae** (gros fruits), **Amaryllidaceae** (Allium répulsifs),
   **Urticaceae** (ortie, hôte/indicatrice).
6. **Faune** — non nommée hors pollinisateurs : pas de **puceron**, **coccinelle**,
   **carabe**, **limace**, **lombric**, **hérisson**, **oiseau** identifiables.
   Pas de pollinisateur **précoce/par temps frais** (bourdon) ni **niche-bois**
   (abeille solitaire). Le `signal fruit` ④ appelle « le ravageur/l'auxiliaire »
   sans visage.

---

## 4. Plantes à AJOUTER — sélection raisonnée par niche

Ordre de grandeur visé : **~10 plantes**, chacune justifiée par la/les feature(s)
qu'elle débloque. `foliage_density` indicatif ; l'attractivité florale est
**héritée gratuitement** de la famille via `_ATTRACT_*` (sauf famille nouvelle,
à déclarer — voir §7).

### 4.1 Rustiques & persistantes (débloquent le GEL ⑥ + l'hiver)

- **Thym** *(Thymus, Lamiaceae)* — `perennial` / **`evergreen`** / couvre-sol /
  `foliage_density≈0.35`. Mots-clés : Aromatique, Mellifère, Médicinale,
  Couvre-sol. **Premier usage d'`evergreen`** → un coussin qui reste vert sous le
  gel (lit ⑥), nectar abeille (Lamiaceae=1.0), répulsif familial (Lamiaceae),
  comestible (manger feuille). `resistance_ecrasement` haute (coussin).
- **Lavande** *(Lavandula, Lamiaceae)* — `perennial` / **`evergreen`** / strate
  basse-moyenne / `≈0.45`. Aromatique, Mellifère, Structurante, Médicinale.
  Nectar **abeille ET papillon**, sous-arbrisseau persistant (gel ⑥), médicinale.
- **Mâche** *(Valerianella, **Caprifoliaceae** — famille nouvelle)* — `annual`
  très rustique / strate sol / `≈0.30`. Couvre-sol d'**hiver** : germe et couvre
  en **jours courts**, résiste au gel → exerce ⑥ « qui tient quand tout meurt » et
  donne un couvert vivant hors saison. Comestible (manger feuille).

### 4.2 Pollinisation & cycle de vie (ombellifères + hôtes + mellifères)

- **Carotte** *(Daucus, **Apiaceae** — famille nouvelle, CLÉ)* — **`biennial`** /
  rosette an 1 → ombelle an 2 / `≈0.40`. Première **ombellifère** : ressource n°1
  des **syrphes/auxiliaires** (à câbler dans `_ATTRACT_SYRPHE`), **plante-hôte du
  machaon** (pont chenille→papillon nommé), racine comestible (manger),
  **première bisannuelle**.
- **Bourrache** *(Borago, Boraginaceae)* — `annual` à fort ressemis / strate
  basse-moyenne / `≈0.45`. Mellifère **abeille** majeure (Boraginaceae=1.0),
  fleurs **comestibles** (manger), ressemis spontané (succession douce). Renforce
  une famille à 1 espèce.
- **Moutarde** *(Sinapis, Brassicaceae)* — `annual` / **engrais vert** pionnier /
  `≈0.40`. Mellifère **syrphe** (Brassicaceae=0.90), couvre-sol rapide, biomasse
  enfouissable (compost) → succession + pollinisation + Brassicaceae renforcée.

### 4.3 Décompo & biomasse (litière différenciée + attraction faune)

- **Consoude** *(Symphytum, Boraginaceae)* — `perennial` / **accumulatrice
  dynamique** / `≈0.55`. Racine profonde (remonte le K/P), **biomasse-paillis** à
  couper-déposer → litière **azotée** (compost ④/⑤), mellifère abeille/bourdon.
  L'engrais vert vivace qui manque.
- **Ortie** *(Urtica, **Urticaceae** — famille nouvelle)* — `perennial` /
  indicatrice d'**azote** / `≈0.50`. **Interconnexion maximale** : plante-hôte des
  chenilles (paon-du-jour, vulcain → pont chenille→papillon), litière très
  azotée (compost), **bioindicatrice** (sol riche), comestible (manger). Le nœud
  qui relie cycle-de-vie ↔ décompo ↔ succession ↔ alimentation.
- **Courgette** *(Cucurbita, **Cucurbitaceae** — famille nouvelle)* — `annual` /
  **`fruitier`** / couvre-sol **étalé** / `≈0.60`. Gros fruits → forte **attraction
  animale** au sol (signal fruit ④, frugivores/charognards nommés), mellifère
  (fleurs), étalement horizontal → exerce la **compétition** par occupation de sol.

### 4.4 Compagne répulsive (interconnexion ravageur ↔ plante)

- **Ail** *(Allium, **Amaryllidaceae** — famille nouvelle)* — **`biennial`** /
  strate basse / `≈0.20`. **Répulsif** (effet familial type Lamiaceae) → fait
  baisser localement la pression `ravageur` (interconnexion directe avec la faune
  nommée du §5), compagnon classique des Solanaceae/Rosaceae, comestible.

> **Bilan trous comblés** : `evergreen` (thym, lavande), `biennial` (carotte, ail),
> 4 familles nouvelles (Apiaceae, Cucurbitaceae, Urticaceae, Amaryllidaceae +
> Caprifoliaceae = 5), ombellifère-syrphe (carotte), hôtes de chenilles (carotte,
> ortie), couvre-sol d'hiver/gel (mâche, thym), accumulatrice-paillis (consoude),
> fruitier supplémentaire (courgette), répulsif (ail).

---

## 5. Animaux NOMMÉS à AJOUTER

### 5.1 Modèle retenu — TRANCHÉ

Deux options pesées (kickoff §5) :

- **(A) « parfum » d'une guilde** — variante de **sprite** + entrée
  **encyclopédie**, **même champ** de population. Coût moteur **nul**, **golden
  NEUTRE** (le tick ne change pas ; seule la couche perception choisit un sprite
  parmi N par hash déterministe). La guilde reste la dynamique ; le nom est une
  **lecture** du joueur.
- **(B) champ dédié** — une vraie entrée `TrophicSpec`/`PollinatorSpec`. Coût =
  un `PopulationField` de plus (le mécanisme générique l'absorbe sans recodage),
  mais peut **toucher la dynamique** (prédation, nectar, pollen) → golden re-figé.

**Décision** :
- **Défaut = (A) parfum** pour **ravageur, auxiliaire, vers_de_terre** : ce sont
  des guildes à champ unique, les nommer est un fait de **perception** → le moins
  invasif, golden neutre. ✔ cohérent avec « pas de 5ᵉ guilde ».
- **Exception = (B) champ dédié** réservée aux **nouveaux pollinisateurs**
  (bourdon, abeille solitaire) : c'est le **seul** endroit où le patron est
  **déjà** multi-champ data-driven (`build_pollinator_registry`) → ajouter un type
  = ajouter une **entrée de donnée**, sans mécanisme neuf. Impact golden à peser
  (§7 : un pollinisateur de plus dépose du pollen → nouaison) → **maîtrisé**.

### 5.2 Catalogue nommé proposé

| Nom FR | Guilde (rattachement) | Modèle | Ressource / proie | Habitat / niche | Pont | Fenêtre |
|---|---|---|---|---|---|---|
| **Puceron** | ravageur | A parfum | feuillage (sève) | monoculture, jeunes pousses | — | estival |
| **Limace** | ravageur | A parfum | feuillage tendre | sol humide, sous litière | — | humide/frais |
| **Doryphore** | ravageur | A parfum | feuillage (Solanaceae) | près des Solanaceae | — | estival |
| **Coccinelle** | auxiliaire | A parfum | pucerons | nectar + stabilité | — | estival |
| **Carabe** | auxiliaire | A parfum | limaces, larves (sol) | sol non perturbé, sous structures | — | nocturne |
| **Chrysope** | auxiliaire | A parfum | pucerons | nectar | — | estival |
| **Merle** *(frugivore)* | auxiliaire | A parfum | **fruit frais** (signal ④) | haies, structures hautes | — | toute saison |
| **Hérisson** | auxiliaire | A parfum | limaces (nocturne) | **piles/tas** (structures ⑤) | — | nocturne |
| **Lombric** | vers_de_terre | A parfum | MO + microbiome | sol non perturbé | — | quasi annuelle |
| **Cloporte** | vers_de_terre | A parfum | litière en décompo | sous litière/structures | — | humide |
| **Bourdon** | pollinisateur | **B type** | nectar (Fabaceae/Lamiaceae) | rondelle poll. | — | **précoce/frais** (jours courts tolérés) |
| **Osmie** *(abeille solitaire)* | pollinisateur | **B type** | nectar (Rosaceae/Apiaceae) | **bois/structures** | — | printanier |

### 5.3 Interconnexions explicites (règle Nico)

- **Puceron → coccinelle/chrysope/syrphe-larve** : la proie nommée nourrit trois
  prédateurs nommés (boucle proie↔prédateur existante, rendue lisible).
- **Limace → carabe/hérisson** : prédateurs **nocturnes** (lit la fenêtre
  photopériodique des guildes) qui **habitent les structures** posables (piles du
  décompo ⑤) → relie faune ↔ structures.
- **Doryphore ↔ Solanaceae / Ail répulsif** : ravageur spécialiste contré par la
  compagne répulsive du §4.4 → relie faune ↔ plante compagne.
- **Fruit tombé (courgette, pommier) → merle (frais) / charognards (pourri)** :
  donne un visage au `signal_fn` ④ déjà codé.
- **Bourdon → carotte/consoude/fèves précoces** : pollinisateur de **début de
  saison** (là où l'abeille n'est pas encore là) → comble la fenêtre
  photopériodique précoce.
- **Carotte/ortie (hôtes) → chenille → papillon** : la plante-hôte nommée donne
  une assise au pont larvaire générique.

---

## 6. Matrice NOUVELLE espèce × feature

| Ajout | Thermique | Pollinis. | Cycle vie | Décompo | Vig/Maît | Écras. | Compét. | Success. |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Thym | **++ evergreen** | ++ abeille | — | + | ++ manger/médic. | ++ coussin | + couvre-sol | + |
| Lavande | **++ evergreen** | ++ abeille/papillon | — | + | + médicinale | + | + structurante | — |
| Mâche | **++ hiver/gel** | + | — | + | + manger | + | ++ couvre-sol hiver | + |
| Carotte | + | ++ **syrphe** | **hôte machaon** | + | ++ manger racine | + | + | + **biennial** |
| Bourrache | + (die) | ++ abeille | — | + ressemis | + manger fleur | + | + | + |
| Moutarde | + (die) | ++ syrphe | — | ++ engrais vert | + | + | ++ couvre-sol | ++ pionnière |
| Consoude | ++ dormant | + abeille/bourdon | — | **++ paillis azoté** | + accumul. | ++ repart | + | + |
| Ortie | ++ dormant | + | **hôte chenilles** | **++ azote** | + manger/indic. | ++ repart | + | ++ indicatrice |
| Courgette | + (die) | + | hôte | **++ gros fruit** | ++ manger | + | ++ **étalé** | — |
| Ail | + dormant | — | — | + | + manger | + | + | + **répulsif→ravageur** |
| Puceron | — | — | (proie) | — | (signe) | — | — | — |
| Coccinelle | — | — | — | — | (signe) | — | — | — |
| Hérisson | — | — | — | **habite structures** | (signe) | — | — | — |
| Merle | — | — | — | **fruit frais ④** | (signe) | — | — | — |
| Bourdon | **+ froid** | **++ précoce** | — | — | (signe) | — | — | — |
| Osmie | — | ++ Rosaceae/Apiaceae | — | niche bois | (signe) | — | — | — |

**Chaque ajout exerce au moins une feature ; chaque feature gagne en richesse** :
le gel ⑥ a enfin des persistantes (thym, lavande, mâche), les syrphes ont leur
ombellifère (carotte), le compost a sa biomasse azotée (consoude, ortie), les
ponts larvaires ont leurs hôtes (carotte, ortie), la faune a des visages.

---

## 7. Partage DOC vs CODE & découpage des tronçons ②+

### 7.1 Ce qui est DONNÉE PURE (ajout de classes/entrées, peu ou pas de moteur)

- **Plantes en familles DÉJÀ cataloguées** (Lamiaceae, Boraginaceae, Brassicaceae) :
  thym, lavande, bourrache, consoude, moutarde → nouvelles **classes d'espèces**
  (`plants/species/*`) + entrées de `PLANT_CATALOGUE`. Héritent l'attractivité
  florale **gratis**. Golden re-figé MAÎTRISÉ **si** elles fleurissent dans la
  fenêtre du smoke, sinon neutre.
- **Animaux « parfum » (A)** : ravageur/auxiliaire/vers nommés = variantes de
  **sprite** + **encyclopédie** → couche perception/Godot, **golden NEUTRE**.

### 7.2 Ce qui demande un MÉCANISME nouveau (à isoler / vérifier)

- ⚠️ **`life_cycle="biennial"`** (carotte, ail) : valeur **codée mais jamais
  exercée** (`longevity` la mappe à 2 ans). À **vérifier** : le moteur gère-t-il
  la rosette-an-1 → montaison-an-2 (succession/sénescence) ? Possible **trou**.
- ⚠️ **`winter_strategy="evergreen"`** (thym, lavande) : codée, jamais exercée. À
  vérifier dans la boucle hivernale (`die`/`dormant` sont les seuls chemins
  testés). Possible trou.
- **Familles NOUVELLES** (Apiaceae, Cucurbitaceae, Urticaceae, Amaryllidaceae,
  Caprifoliaceae) : ajouter la chaîne `family` ; surtout **câbler `_ATTRACT_*`**
  (Apiaceae→syrphe élevé !) sinon elles tombent sur `_ATTRACT_DEFAUT`. Décider si
  elles portent un **effet familial** (Amaryllidaceae répulsif type Lamiaceae,
  Urticaceae injection azote).
- **Plante-hôte des chenilles** : aujourd'hui le pont lit le **feuillage
  générique**. Rattacher la chenille à une **famille-hôte** nommée (carotte/ortie)
  = petite extension data du `LifeCycleBridge` (`resource_fn` filtrée par famille)
  — à peser, ou rester générique (parfum seulement).
- **Nouveaux pollinisateurs (B)** : bourdon, osmie = entrées
  `build_pollinator_registry` (données : attractivité + fenêtre + forager). Le
  mécanisme générique les absorbe, **mais** ils déposent du pollen (foragers) →
  **nouaison** → golden re-figé **MAÎTRISÉ** (dérive attribuable au seul nouveau
  type).

### 7.3 Découpage proposé des tronçons (esquisse — kickoffs écrits APRÈS)

| # | Lot | Contenu | Impact golden attendu |
|---|---|---|---|
| ② | **Plantes lot 1 (familles connues)** | thym, lavande, bourrache, consoude, moutarde | re-figé MAÎTRISÉ (floraison) ou neutre |
| ③ | **Plantes lot 2 (familles + cycles neufs)** | carotte, ortie, courgette, mâche, ail + 5 familles + `_ATTRACT_*` + **vérif `biennial`/`evergreen`** | re-figé MAÎTRISÉ + corrections moteur éventuelles |
| ④ | **Faune nommée — parfums (A)** | puceron/limace/doryphore, coccinelle/carabe/chrysope/merle/hérisson, lombric/cloporte (perception + encyclopédie) | **NEUTRE** |
| ⑤ | **Faune nommée — pollinisateurs (B)** | bourdon, osmie (registre data-driven) | re-figé MAÎTRISÉ (pollen/nouaison) |
| ⑥ | **Vue Godot / sprites / encyclopédie** | sprites des nouvelles plantes + variantes faune, entrées encyclopédie, hôtes/ponts | NEUTRE (vue) |

> Ordre conseillé : ②→③ (plantes d'abord, elles fondent les ressources de la
> faune), puis ④→⑤ (faune), ⑥ en clôture vue. ④ étant golden-neutre, il peut
> s'intercaler tôt si Nico veut voir des bestioles nommées rapidement.

---

## 8. Lien version physique

Le catalogue est la **source commune** des deux versions : chaque espèce/animal
nommé nourrit une **carte** (tuiles 3D + cartes type MTG) et une **entrée
d'encyclopédie** ingame. Les ajouts ci-dessus enrichissent donc aussi le deck
physique — en particulier les **interconnexions** (hôte↔papillon, fruit↔frugivore,
répulsif↔ravageur) qui font de bonnes **synergies de cartes**. À garder en tête au
moment des sprites/encyclopédie (⑥) : nommer = donner une carte. Pas d'implication
moteur ici, simple cohérence de design.
