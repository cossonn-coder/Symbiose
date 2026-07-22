# CONCEPTION — Sommet trophique : super-prédateur (T1) + herbivore vertébré (T7)

> **Statut : FIGÉ 2026-07-11** (`/conception`, arbitrages Nico Q1-Q3).
> **Nature : SPRINT `/sprint-auto`** — moteur + vue, golden **re-figé de façon
> maîtrisée** (tronçons ① et ②). Comble les trous **T1** et **T7** du référentiel
> `docs/meta/calibrage/conception_completude_ecosysteme.md` (D61, §3). Premier `/conception` d'ajout
> d'espèces nourri par ce référentiel.

---

## §0. Pourquoi ce couple

Le référentiel D61 recense la **boucle ouverte la plus grave** : les
consommateurs intermédiaires du jardin (merle, hérisson, coccinelle, carabe…)
n'ont **aucun puits** — leur population n'est régulée que par la ressource
(bottom-up), jamais par le haut. Un écosystème téléonomique **ferme le sommet**.

Deux fonctions couplées :
- **T1 / D1 — super-prédateur** : le niveau 3 qui régule les niveaux 2 (top-down).
- **T7 / B4 — herbivore vertébré** : une **proie crédible** pour ce super-prédateur
  (un rapace ne vit pas de coccinelles). T7 n'a de sens qu'avec T1, et
  réciproquement — d'où le sprint unique.

Le taxon découle de la fonction (règle D61) : on n'ajoute que ce qui **ferme un
flux**, pas une liste à cocher.

---

## §1. Ce que le modèle existant permet (rappel — source de vérité `data/code/`)

La faune est **data-driven** (`fields/population/spec.py:TrophicSpec`), tickée par
`PopulationField` (`field.py`) :

```
capacité = clamp(res_w·resource_fn + hab_w·habitat_fn + signal_fn)
survie   = phénologie · chaleur · (1 − pred_w·Σ prédateurs) · (1 − disturb_w·perturbation)
cible    = capacité · survie
champ'   = clamp(champ·inertie + cible·(1−inertie), 0, MAX)
```

Conséquences directes pour ce sprint :
- **Un puits top-down = lister un nom dans `predators=(...)`.** Le champ nommé est
  résolu au tick (`vie_macro.py:_predator_field`), sa densité rabote la `survie` de
  la proie. **À densité 0 → +0 → golden neutre.** Aucune mécanique neuve.
- **Ordre de tick = toutes les proies avant tous les prédateurs**
  (`registry.build_population_specs`). Le décalage d'inertie proie↔prédateur PRODUIT
  le **boom-bust** émergent (philo #1/#2 : jamais de malus scripté, un puits sur un
  champ). Le super-prédateur tick donc **en DERNIER**, le campagnol **en position
  proie** (avant merle/limace, ses co-proies, et avant les super-prédateurs).
- Ressource d'un prédateur = densité de ses proies : helper existant
  `_espece_grid(name)` (`resources.py:337`) lit `eco.populations[name]`, robuste si
  le champ n'existe pas encore (grille nulle).
- Empreinte racinaire d'une plante : `p.root_plots` (mémoïsé, `plants/base/
  instance.py:283`) — support de la grille-ressource du campagnol.
- 5 voix faune : encyclopédie = `fields/faune_encyclo.py` (`encyclo_meta`, DONNÉE
  PURE golden-neutre). **INVARIANT testé** : tout `predators` d'une espèce ⊂ ses
  `interconnexions`, et le sous-graphe trophique entre espèces nommées est
  **SYMÉTRIQUE** (si A cite B, B cite A).

---

## §2. Les trois espèces (arbitrages figés)

### 2.1 `campagnol` — herbivore vertébré (T7, proie)
- **Catégorie NEUVE `herbivore_vertebre`** (Q3) — distincte de `ravageur` : il ronge
  **racines/bulbes/écorce**, pas le feuillage. La conflater avec le ravageur collerait
  le mauvais signe (criblage foliaire) sur un dégât de collet.
- **resource_fn** = biomasse racinaire perçue : Σ plantes vivantes, poids réparti sur
  `p.root_plots`, pondéré par **préférence d'organe/famille** (bulbes Amaryllidaceae,
  tubercules/légumes-racines, **jeune écorce** des ligneux) — placeholders, calibrage
  post-test. Normalisé par une référence (`ROOT_REF`).
- **habitat_fn** = **galeries** : sol non remué + couvert (paillage, herbe dense) —
  réutilise `_undisturbed_grid`/`_avec_abri_paillage`. Le campagnol fuit le sol nu et
  fraîchement bêché (perturbation le chasse déjà via `disturb_w`).
- **predators** = `("rapace", "couleuvre")` (câblé au tronçon ②).
- **Fenêtre** : large (actif quasi toute l'année, dortoir en galerie l'hiver) —
  `daylen_min≈8.5, daylen_full≈10.0` (comme le lombric).
- **Salt dédié** : `0x2AF001`.

### 2.2 `rapace` — super-prédateur aérien (T1)
- **Catégorie NEUVE `super_predateur`**.
- **resource_fn** = densité **campagnol + merle** (somme de `_espece_grid`,
  normalisée) : le rapace chasse le rongeur en terrain découvert et prélève l'oiseau.
- **habitat_fn** = terrain **ouvert avec perchoir** : présence d'un point haut
  (arbre adulte / bordure de maison) + ciel dégagé. Placeholder simple (réutilise un
  habitat de base + bump perchoir), calibrage post-test.
- **predators** = `()` (sommet de chaîne — son frein est la ressource + la fenêtre).
- **Fenêtre** : large (résident/estivant), `daylen_min≈9.0, daylen_full≈11.0`.
- **Salt dédié** : `0x2B0001`.

### 2.3 `couleuvre` — super-prédateur terrestre (T1)
- **Catégorie `super_predateur`**.
- **resource_fn** = densité **campagnol + limace** : chasse au sol (rongeurs dans les
  galeries, mollusques dans le paillis humide).
- **habitat_fn** = sol **ensoleillé non remué avec cache** (piles de bois/pierres,
  litière) — réutilise `_undisturbed_structure_grid`/`_pile_grid`. La couleuvre a
  besoin de thermoréguler (soleil) ET de se cacher.
- **predators** = `()` (sommet).
- **Fenêtre** : héliophile estivale, `daylen_min≈11.0, daylen_full≈13.0` (hiberne).
- **Salt dédié** : `0x2B1001`.

### 2.4 Câblage des puits (tronçon ②)
| Proie | `predators` avant | `predators` après |
|---|---|---|
| campagnol | () | ("rapace", "couleuvre") |
| merle | () | ("rapace",) |
| limace | ("carabe","herisson") | ("carabe","herisson","couleuvre") |

Le **hérisson reste sans puits** (Q2) : quasi-apex du jardin, très peu prédaté dans
la réalité ; son frein reste habitat + fenêtre. On l'assume — pas de blaireau/grand-duc
ajouté juste pour cocher la boucle.

Les auxiliaires **insectes** (coccinelle/chrysope/carabe) restent aussi sans puits :
hors périmètre T1 (le référentiel D1 vise « hérisson/merle/rongeurs »). Leur frein
est l'habitat + la fenêtre (D61 §5.5, « sommets de chaîne de jardin »).

---

## §3. Dégât du campagnol sur les plantes (canal racinaire dédié — Q3)

Nouvelle perturbation **`root_herbivory`** (`sim/effects/perturbations.py`), miroir
léger de `herbivory_pressure` mais lisant `category_density("herbivore_vertebre")` :

```
pression_racine = category_density("herbivore_vertebre", r, c) · ROOT_HERBIVORY_GAIN
```

- **Modeste** (le campagnol est d'abord une proie ; son herbivorie est secondaire) :
  ronge le collet / écorce → `ReduceHealth` faible quand la densité locale est haute,
  bascule létale seulement sur jeune ligneux annelé (placeholder, calibrage post-test).
- **Signe diégétique PROPRE** (`sim/semiologie.py`) : ex. `rongeur_racinaire` —
  « plante qui jaunit/flétrit par la base sans cause foliaire, jeune tige écorcée au
  ras du sol ». Distinct du criblage foliaire du ravageur (indice d'apprentissage
  #5/#6 : la cause est souterraine, on l'infère).
- Flux respecté (#1/#2) : campagnol (champ) → pression racinaire (contrainte) →
  réponse de la plante. Jamais un `-santé` scripté sur l'espèce.

---

## §4. Les 5 voix (règle projet, D61 §0)

Chaque espèce reçoit les voix **au standard des 15 espèces faune existantes** :
- **Encyclopédie** (`faune_encyclo.py`) : `blurb` naturaliste (ce qu'on VOIT, pas la
  cause) + `interconnexions`. Respecter l'**INVARIANT symétrie** : ajouter
  `rapace`/`couleuvre` dans les interconnexions de `campagnol`/`merle`/`limace`, et
  réciproquement (sous-graphe trophique symétrique — le test le vérifie).
- **Carnet** : concepts que l'espèce illustre (régulation top-down, chaîne trophique,
  boom-bust) — via le dispositif carnet existant si l'espèce y est rattachable.
- **Événements** : marqueurs de cycle de vie au ledger (apparition d'un super-prédateur
  = événement rare et marquant, cohérent « histoire émergente »).
- **Pages secrètes** : lore optionnel (le rapace en vol, la couleuvre au soleil sur la
  pile de bois — matière poétique) — facultatif §7 de la règle voix.
- **Magazine** : **sans objet** pour la faune sauvage (on n'achète pas un rapace) —
  comme les 15 espèces existantes.

---

## §5. Découpage en tronçons (perf-first, golden re-figé maîtrisé)

### ① campagnol (proie) + dégât racinaire — **golden re-figé #1**
Ajoute `campagnol` (catégorie `herbivore_vertebre`, resource racine, habitat galeries,
`predators=()` encore), la grille-ressource racinaire, le salt, les 5 voix, la
perturbation `root_herbivory` + le signe. **Re-figeage annoncé** : l'herbivorie
édaphique apparaît là où le campagnol prolifère → dérive localisée sur les plantes à
racines exposées. Test : le campagnol pousse sur les plots racinaires, la plante
souffre à densité haute, la vue reste hors-scope.

### ② super-prédateurs (sommet) — **golden re-figé #2**
Ajoute `rapace` + `couleuvre` (catégorie `super_predateur`, resource = densité proies,
`predators=()`), leurs salts, leurs 5 voix ; **câble les puits** (§2.4). Tickés en
DERNIER (proie avant prédateur). **Re-figeage annoncé** : top-down sur
campagnol/merle/limace → boom-bust sur toute la chaîne. Test : montée du super-prédateur
là où les proies abondent, reflux consécutif des proies (décalage d'inertie).

### ③ vue Godot + pont — **golden intact**
Pont expose les 3 nouveaux champs **par espèce** (pattern ⑥b catalogue enrichi) ;
`MacroLife.cs` rend les sprites campagnol/rapace/couleuvre ; mapping du signe
`rongeur_racinaire` côté `PlantRenderer` (canal texture/teinte, cf. sémiologie D48) ;
rendu des entrées d'encyclopédie. Aucune écriture moteur → golden préservé. Point F5
Nico à la fin.

**Coût perf** : 3 nouveaux `PopulationField`. rapace/couleuvre lisent des grilles de
densité DÉJÀ calculées (cheap) ; campagnol = 1 balayage plantes (grille racine,
mémoïsable comme les empreintes). Budget ≤ +10 %/tronçon (à confirmer au chiffrage ②).

---

## §6. Ce que ce sprint ne fait PAS
- N'ajoute **aucun autre trou D61** (parasitoïde T2, pathogène T3… = `/conception`
  dédiées ultérieures).
- Ne régule **pas** le hérisson ni les auxiliaires insectes (hors périmètre, §2.4).
- Ne relève **jamais** la barre de taille : si un fichier gonfle, `/refactor`.
- Ne re-fige le golden **que** aux tronçons ① et ② (annoncés) ; ③ le préserve.

---

## §7. Après le sprint (maintenance D61)
Repasser dans `docs/meta/calibrage/conception_completude_ecosysteme.md` : T1 (D1) et T7 (B4) de ⚠️ → ✅,
colonne « Incarné par » = `rapace`/`couleuvre` (D1), `campagnol` (B4) ; lancer
`/audit-projet ecosysteme`. Mettre à jour `DETTE.md` (D61 pointeur) et `journal.md`.
