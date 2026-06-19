# CONCEPTION — FAUNE NOMMÉE À CHAMP DÉDIÉ (modèle B)

> **Statut : FIGÉ le 2026-06-19.** Doc à ÉTUDIER (pas de questions à trancher —
> les décisions sont prises). Ce document **AMENDE et SUPPLANTE** la §5.1 de
> `CONCEPTION_CATALOGUE_ENRICHI.md` (qui retenait le modèle **A « parfum »** par
> défaut). Le kickoff `sprints/sprint_catalogue_enrichi/04_faune_parfums.md`
> (modèle A) devient **caduc** — conservé en historique, remplacé par les
> tronçons ④a–④e décrits au §7.
>
> Source de vérité moteur : `data/code/`. Couche `fields` (population) + couplages
> `sim`. Golden : re-figeage **MAÎTRISÉ et LARGE** assumé (voir §6).

---

## 0. Pourquoi ce doc existe (la décision de Nico)

La conception catalogue figée disait : ravageur / auxiliaire / vers_de_terre
restent **3 champs de guilde** ; les 10 animaux nommés ne sont que des **parfums**
(variantes de sprite + encyclopédie) lisant le **même** champ. Coût nul, golden
neutre — mais **deux animaux d'une même guilde se comportent à l'identique**.

Nico a tranché le **2026-06-19** (cf. mémoire `regle_interconnexion_acteurs`,
précision FORTE) :

> **Chaque animal doit avoir SA propre source de nourriture, SON prédateur et SON
> habitat.** L'interconnexion doit être *réelle*, pas cosmétique. Et : **les
> guildes deviennent des CATÉGORIES** (étiquettes), les **espèces remplacent les
> champs**.

Conséquence directe : on passe de **3 champs trophiques** à **10 champs
trophiques** (un par animal nommé), la guilde n'étant plus qu'une **métadonnée de
catégorie**. C'est une **refonte de la vie macro**, pas un ajout cosmétique.

> ⚠️ **Hors périmètre ici** : Bourdon et Osmie (pollinisateurs) étaient DÉJÀ en
> modèle **B** (registre `PollinatorSpec` multi-champ). Ils restent au **tronçon
> ⑤**. La couche pollinisateur (`abeille`/`syrphe`/`papillon`, `POLLINATOR_NAMES`)
> n'est **pas** touchée par cette refonte → isolée, golden-neutre pour elle.

---

## 1. Modèle cible — une espèce = un champ, une catégorie = une vue

### 1.1 Ce qui change dans `TrophicSpec`

Ajout d'un champ **`category`** (la guilde rétrogradée en étiquette) :

```python
@dataclass
class TrophicSpec:
    name: str                       # "puceron" (clé de eco.populations, sprite, encyclo)
    category: str                   # "ravageur" | "auxiliaire" | "detritivore"  ← NEUF
    salt: int
    resource_fn: Callable           # SA nourriture (propre à l'espèce)
    habitat_fn: Callable            # SON habitat (propre à l'espèce)
    predators: tuple[str, ...] = () # SES prédateurs (noms d'espèces / larves)
    signal_fn: Callable | None = None
    # … pondérations + fenêtre photopériodique inchangées
    blurb: str = ""                 # texte encyclopédie (donnée ; rendu = ⑥)
    interconnexions: tuple[str, ...] = ()   # graphe relationnel (§5.3 catalogue)
```

- `name` devient une **clé d'espèce** (10 clés au lieu de 3 guildes).
- `category` ∈ {`ravageur`, `auxiliaire`, `detritivore`}. On **renomme**
  `vers_de_terre` → catégorie `detritivore` (lombric **et** cloporte y vivent ;
  « vers de terre » ne décrit que le lombric).
- `predators` référence désormais des **noms d'espèces** (`coccinelle`…) et/ou
  des **champs larvaires** (`syrphe_larve`, `chenille`) — le résolveur existant
  `EcoFields._predator_field` gère déjà les deux **sans modification**.

### 1.2 La couche « catégorie » = une VUE d'agrégation (clé de voûte)

Six consommateurs lisent aujourd'hui `eco.populations["ravageur" | "auxiliaire" |
"vers_de_terre"]` **en dur** (audit §4). Si ces clés disparaissent, **tout casse**
(dont la santé des plantes). Solution : un **helper d'agrégation par catégorie**
sur `EcoFields`, et on **recâble** les six consommateurs dessus :

```python
def category_density(self, category: str, r: int, c: int) -> float:
    """Densité agrégée d'une CATÉGORIE = somme des espèces membres.
    Remplace la lecture directe populations["ravageur"]. La guilde devient
    une VUE calculée, plus un champ stocké."""
    return sum(pf.at_plot(r, c)
               for pf in self.populations.values()
               if getattr(pf.spec, "category", None) == category)
```

> **Pourquoi une somme ?** La pression herbivore subie par une plante = total des
> ravageurs présents (puceron + limace + doryphore), peu importe l'espèce. La
> catégorie restitue exactement le « niveau de guilde » d'avant — c'est le pont
> de continuité qui rend la migration **incrémentale et lisible** (§7).

---

## 2. Matrice TRIADE par animal (les 10 espèces de ④)

Pour chaque animal : **nourriture** (`resource_fn`), **prédateur(s)**
(`predators`), **habitat** (`habitat_fn`), **fenêtre** (photopériode). Les
fonctions marquées *(existe)* sont déjà codées ; *(neuf)* = à écrire ; *(scindé)*
= dérivée d'une fonction de guilde existante.

### Catégorie `ravageur`

| Animal | Nourriture (resource_fn) | Prédateurs | Habitat (habitat_fn) | Fenêtre |
|---|---|---|---|---|
| **Puceron** | feuillage tendre `_foliage_grid` *(existe)* | coccinelle, chrysope, **syrphe_larve** | monoculture + jeunes pousses `_monoculture_grid` *(existe)* | estivale |
| **Limace** | feuillage bas/tendre `_foliage_grid` *(existe, réutilisé)* | carabe, hérisson | sol **humide** + sous-litière `_humide_litiere_grid` *(neuf)* | humide/frais |
| **Doryphore** | feuillage **Solanaceae** `_foliage_solanaceae_grid` *(neuf, filtré famille)* | carabe | proximité Solanaceae, **réduit par ail** (Amaryllidaceae §4.4) `_solanaceae_grid` *(neuf)* | estivale |

### Catégorie `auxiliaire`

| Animal | Nourriture | Prédateurs | Habitat | Fenêtre |
|---|---|---|---|---|
| **Coccinelle** | **puceron** `_espece_grid("puceron")` *(scindé de `_ravageur_grid`)* | — | nectar+stabilité `_stability_grid` *(existe)* | estivale |
| **Chrysope** | **puceron** `_espece_grid("puceron")` *(scindé)* | — | nectar `_auxiliaire_habitat_grid` *(existe)* | estivale |
| **Carabe** | **limace** + larves sol `_espece_grid("limace")` *(scindé)* | — | sol non perturbé + **sous structures (piles ⑤)** `_undisturbed_structure_grid` *(neuf)* | nocturne→large |
| **Merle** | **fruit frais** `_aux_fruit_signal`→resource *(existe, repromu)* + lombric | — | base + structures hautes `_base_habitat_grid` *(neuf, plancher)* | toute saison |
| **Hérisson** | **limace** `_espece_grid("limace")` *(scindé)* | — | **piles/tas (structures ⑤)** `_pile_grid` *(neuf)* | nocturne→large |

### Catégorie `detritivore` (ex-`vers_de_terre`)

| Animal | Nourriture | Prédateurs | Habitat | Fenêtre |
|---|---|---|---|---|
| **Lombric** | MO + microbiome `_soil_food_grid` *(existe)* | merle, hérisson | sol non perturbé `_undisturbed_grid` *(existe)* | quasi annuelle |
| **Cloporte** | **litière en décompo** `_litter_grid` *(neuf)* | carabe, hérisson | sous-litière/structures + humide `_humide_litiere_grid` *(neuf, partagé limace)* | humide |

> ⚠️ **Honnêteté du modèle (à graver dans les docstrings)** : `nocturne` n'est
> **pas** une porte (pas de cycle jour/nuit dans le tick hebdo) → on l'élargit en
> fenêtre photopériodique large + tag d'encyclopédie. `humide` **devient** une
> vraie ressource/habitat (lecture de `eco.humidite`, qui existe) → pas de fausse
> mécanique. C'est un **gain** du modèle B sur le A : la niche est réelle.

---

## 3. Graphe d'interconnexion complet

```
                       ┌─────────── feuillage (plantes) ───────────┐
                       ▼                  ▼                          ▼
                   PUCERON ───┐       LIMACE ──────┐           DORYPHORE
                   ▲  ▲  ▲    │         ▲           │            ▲   │
   (proie de)──────┘  │  │    │ (proie) │           │ (proie)    │   │ réduit par
        COCCINELLE    │  └─ SYRPHE_LARVE│           │            │   ▼
        CHRYSOPE      │     (pont ⑤,    │      CARABE◄───────────┘  AIL (Amaryllidaceae,
        (mangent      │      →syrphe)   │      HÉRISSON               répulsif §4.4)
         puceron)     │                 └──────(mangent limace)
                      │
   nectar/rondelle ◄──┘ (habitat coccinelle/chrysope/merle)

   FRUIT TOMBÉ ──frais──► MERLE (frugivore)
              └─pourri──► CLOPORTE (+ petite part limace)   [signal ④, additif]

   sol/MO ──► LOMBRIC ──(nourrit décompo, decomp_speed)──► humus
              ▲   ▲
              │   └── proie de MERLE / HÉRISSON (oiseaux & insectivores mangent les vers)
   litière ──► CLOPORTE ──(accélère décompo litière)──► humus
              ▲
              └── proie de CARABE / HÉRISSON

   STRUCTURES (piles/bac ⑤) ──habitat──► CARABE, HÉRISSON, CLOPORTE   [faune↔structures]
   PLANTES MELLIFÈRES (rondelle) ──habitat──► COCCINELLE, CHRYSOPE, MERLE  [faune↔plantes]
   PLANTES-HÔTES (carotte/ortie) ──► CHENILLE (pont) ──► PAPILLON   [faune↔cycle de vie]
```

**Boucles proie↔prédateur réelles (boom-bust)** : puceron↑ → coccinelle/chrysope↑
(décalage d'inertie) → puceron↓ ; limace↑ → carabe/hérisson↑ → limace↓. Les
prédateurs auxiliaires n'ont pas de prédateur (sommet de chaîne) ; lombric/cloporte
en ont (merle, hérisson, carabe) → la catégorie détritivore n'est plus un puits
isolé.

---

## 4. AUDIT des points de couplage à recâbler

Tous les endroits qui lisent `populations[guilde]` en dur. **Chacun migre vers
`category_density(...)`** (ou un nom d'espèce précis quand c'est l'intention).

| # | Fichier:ligne | Lecture actuelle | Recâblage |
|---|---|---|---|
| C1 | `sim/effects/perturbations.py:213` | `populations["ravageur"]` → **pression herbivore (SANTÉ plante)** | `category_density("ravageur", r, c)` |
| C2 | `sim/effects/perturbations.py:249` | `populations["auxiliaire"]` → **bascule létale** | `category_density("auxiliaire", r, c)` |
| C3 | `sim/vigueur_macro.py:59` | `populations["ravageur"]` | `category_density("ravageur", …)` |
| C4 | `sim/vigueur_macro.py:65` | `populations["auxiliaire"]` | `category_density("auxiliaire", …)` |
| C5 | `sim/vigueur_macro.py:80` | `populations["vers_de_terre"]` | `category_density("detritivore", …)` |
| C6 | `fields/ecofields/container.py:383,408` | `populations["vers_de_terre"]` → **decomp_speed** | `populations["lombric"]` (le ver, pas le cloporte, fait l'humus du sol ; cloporte = litière, dette si on veut le distinguer) |
| C7 | `sim/actions/gestes.py:308` | `populations[guilde].add(...)` (écraser) | espèce ciblée (le sprite cliqué EST une espèce ; vient du pont) |
| C8 | `sim/actions/gestes.py:420` | `populations["vers_de_terre"].add(...)` | `populations["lombric"]` |
| C9 | `tools/simserver/actions.py:236-246` | `target.guilde`, défaut `"ravageur"` | `target.espece` (protocole pont ↑) → **⑥** |
| C10 | `tools/simserver/serialize.py:138` | sprites = `populations.values()` (par guilde) | par **espèce** (10 clés) + table sprite par espèce → **⑥** |
| C11 | `fields/population.py:365` `_ravageur_grid` | ressource auxiliaire = champ `ravageur` | scindé : `_espece_grid("puceron")` / `("limace")` selon le prédateur |
| C12 | `fields/lifecycle.py:108` métamorphose | `populations[adult]` (papillon/syrphe) | **inchangé** (adultes = pollinisateurs, hors refonte) |
| C13 | signaux fruit `signal_fn` | `_rav_fruit_signal` sur guilde ravageur, `_aux_fruit_signal` sur auxiliaire | `_aux_fruit_signal`→**merle** ; `_rav_fruit_signal` (pourri)→**cloporte** (+ part limace) |
| C14 | pont `syrphe_larve` prédateur de `ravageur` | `predators=("auxiliaire","syrphe_larve")` au niveau guilde | `syrphe_larve` ∈ `predators` du **puceron** (sa vraie proie) |

**Inchangés (à NE PAS toucher, vérifier la neutralité)** :
- `pollinator_density` / `POLLINATOR_NAMES` (abeille/syrphe/papillon) — couche
  pollinisateur isolée.
- `RONDELLE_TYPES` — **aucune nouvelle rondelle par espèce** (ça exploserait) ;
  les auxiliaires partagent la rondelle `auxiliaire`, le lombric la rondelle
  `lombric`. La spécificité vient des `resource_fn`/`predators`, pas des rondelles.
- Ponts `chenille→papillon`, `syrphe_larve→syrphe` (mécanisme `tick_bridges`).

---

## 5. Décisions de conception annexes (figées)

1. **Pas de nouvelle rondelle par espèce.** Les rondelles restent au niveau
   « fonction » (`auxiliaire`, `pollinisateur`, `lombric`). L'identité de l'espèce
   est portée par sa triade (resource/predator/habitat), pas par une rondelle.
2. **`detritivore` remplace `vers_de_terre`** comme nom de catégorie. La
   **rétrocompat du pont** (`target.guilde` défaut `"ravageur"`) est gérée au
   tronçon ⑥ (protocole) — en Python pur, on bascule franc (run éternel, pas de
   save < v1.0 à migrer, cf. CLAUDE.md).
3. **`decomp_speed` reste piloté par le lombric seul** (C6). Le cloporte accélère
   la **litière** (pas l'humus du sol) → si on veut le rendre littéral, **dette**,
   pas ④.
4. **Doryphore « contré par l'ail »** = via l'`adjacency_bonus` Amaryllidaceae
   **déjà posé** en ③ (réduction maladie) + son `_solanaceae_grid` d'habitat
   pondéré par la présence d'ail. Pas de nouvelle action moteur. Effet littéral
   plus fort = dette.
5. **Merle/hérisson sans prédateur** (sommets). Acceptable : ce sont des
   régulateurs ; leur frein est la fenêtre + l'habitat (structures/fruit), pas un
   super-prédateur (hors périmètre jardin).
6. **Calibrage** : toutes les pondérations héritent des défauts de module
   (`DEF_RESOURCE_W`…). Ajustement fin = post-test, hors ④ (comme les guildes).

---

## 6. Impact GOLDEN & perf

### Golden — re-figeage MAÎTRISÉ et LARGE (assumé)

Les champs de population sont **toujours tickés** (ambiants), et la santé des
plantes **lit** la pression ravageur/auxiliaire (C1/C2). Donc le smoke
(2 tuiles × 4 ans) **change** : la dynamique « 1 champ ravageur » devient « somme
de 3 espèces aux ressources/prédateurs distincts ». Le hash golden **bougera** —
c'est **attendu et légitime**, à **annoncer** (pas un bug).

**Stratégie pour garder des re-figeages LISIBLES** : migrer **une catégorie à la
fois** (§7). Chaque étape produit **un** re-figeage attribuable à **une** scission,
au lieu d'un saut opaque unique. L'étape de scaffolding ④a est même **golden
NEUTRE** (agrégat d'un seul champ == le champ).

> Invariant de contrôle : après ④a (refactor pur), `category_density("ravageur")`
> == ancien `populations["ravageur"]` plot par plot → **hash inchangé**. Si le
> hash bouge dès ④a, c'est un **bug** d'agrégation, pas une scission.

### Perf — marginale

3 champs trophiques → 10. Chaque `PopulationField.tick` = O(rows×cols) = 432
plots. On passe de ~6 ticks pop (3 trophiques + 3 pollinisateurs) à ~13. `LightField`
reste 53 % du CPU (cf. `perf_profile_simulation`) ; les populations sont
quasi-gratuites. Quelques `resource_fn` re-scannent les plantes (foliage filtré
famille) → O(plantes×plots) × 2-3 passes de plus. Avec ×339 de marge gameplay,
**négligeable**. À surveiller seulement si on multiplie les filtres famille.

---

## 7. DÉCOUPAGE d'implémentation (migration par catégorie)

Chaque tronçon préserve un golden **localisé** (sauf ④a, neutre). Boucle
habituelle : coder → golden → `00_etat.md` → commit → `/clear` → suivant.

| # | Lot | Contenu | Golden |
|---|---|---|---|
| **④a** | **Scaffolding catégorie** | ajout `TrophicSpec.category` (3 guildes actuelles taguées) + helper `category_density` + **recâblage des 6 consommateurs** (C1–C6,C8) vers `category_density`/espèce. **Aucune scission encore.** | **NEUTRE** (invariant §6) |
| **④b** | **Scinder `ravageur`** | puceron/limace/doryphore (3 specs, `category="ravageur"`) ; `resource_fn` filtrées (foliage, foliage Solanaceae, humide) ; recâble proie auxiliaire (C11) + `syrphe_larve`→puceron (C14) + signal fruit pourri→cloporte placeholder | re-figé MAÎTRISÉ #1 |
| **④c** | **Scinder `auxiliaire`** | coccinelle/chrysope/carabe/merle/hérisson ; predators sur espèces ravageur (C13 merle/fruit frais) ; habitats neufs (structures/piles) | re-figé MAÎTRISÉ #2 |
| **④d** | **Scinder `detritivore`** | lombric/cloporte ; `decomp_speed`→lombric (C6) ; cloporte litière + signal fruit pourri réel (C13) ; predators détritivores (merle/hérisson/carabe) | re-figé MAÎTRISÉ #3 |
| **④e** | **Métadonnée encyclo + tests** | `blurb` + `interconnexions` par espèce ; suite `tests/test_faune_dediee.py` (couverture 10, triades, déterminisme, fenêtres, catégories) ; **stub sérialisation pont** par espèce → préparé pour ⑥ | NEUTRE (donnée+tests) |
| **⑤** | **Pollinisateurs B** (inchangé) | bourdon, osmie | re-figé pollen/nouaison |
| **⑥** | **Vue Godot** | sprites par espèce, encyclopédie, **protocole pont `target.espece`** (C9/C10), table sprite | NEUTRE (vue) |

> Ordre : ④a (filet) **obligatoirement en premier** — il rend les scissions
> suivantes sûres. Puis ④b→④d (une catégorie par /clear), ④e clôt le Python,
> ⑥ la vue. ⑤ indépendant (couche pollinisateur isolée), insérable quand Nico veut.

---

## 8. Lien version physique

Le modèle B **renforce** le deck physique : chaque animal nommé devient une
**carte** à triade propre (sa proie, son prédateur, son habitat) → des **synergies
de cartes réelles** (jouer « pile de bois » attire carabe+hérisson+cloporte ;
planter de l'ail bride le doryphore ; laisser un fruit tomber appelle le merle).
La cosmétique du modèle A n'aurait donné que des illustrations interchangeables ;
B donne des **mécaniques de cartes** — c'est la coexistence rendue jouable des
deux côtés.
