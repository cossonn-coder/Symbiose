# CONCEPTION — Génétique infinitésimale (D139, sprint ① sur 3)

> Figée le 2026-11-16 (`/conception` D139). Étude préalable :
> [`etude_genetique_realiste.md`](etude_genetique_realiste.md) (option **B** retenue).
> Suite : [`conception_niche_thermique.md`](conception_niche_thermique.md) (sprint ②),
> [`conception_caracteres_vivants.md`](conception_caracteres_vivants.md) (sprint ③).
> Sprint : `sprints/vegetal/genetique/sprint_genetique_infinitesimale/`.

## 1. Pourquoi

Constat de Nico (F5 du 2026-11-16) : « la génétique me semble très faible, trop peu
d'impact ». Mesuré : les gènes sont des facteurs sans unité autour de 1,0. La seule source de
diversité est une mutation fixe (σ = 0,05). L'ampleur réelle est sous-estimée d'un facteur
10 environ (`etude` §2.5). Nico a demandé une génétique **alignée sur la réalité**.

## 2. Décisions (Nico, 2026-11-16)

- **G1 — Modèle infinitésimal** (Fisher). Un caractère est une valeur continue dans sa
  **vraie unité** (°C, semaines, facteur quand il n'existe pas d'unité naturelle).
- **G2 — La diversité vient du brassage**, pas de la mutation. La mutation n'est qu'un filet.
- **G3 — Consanguinité F par plante.** L'autofécondation fixe les lignées, le croisement
  les mélange.
- **G4 — `autofecondation` devient un gène** (taux d'autofécondation par plante). C'est le
  moteur de F. Ce gène a été proposé par Nico (lot 3) et déplacé dans ce sprint.
- **G5 — Les gènes coûtent.** Deux compromis réels entrent ici : la **dépression de
  consanguinité**, et le compromis **précocité ↔ taille**. Les autres viennent avec leurs
  caractères (sprints ② et ③).
- **G6 — Multiplier les gènes autant qu'il faut.** Coût mesuré ≈ 0,1 % du tick par gène
  [smoke 2 tuiles × 4 ans, cProfile, 2026-11-16]. La RAM n'est pas une contrainte.

## 3. Le registre des caractères

Une table unique, dans `plants/genetics.py` ou un module voisin de la couche `plants` si la
taille l'exige. Elle déclare chaque caractère :

| Champ | Sens |
|---|---|
| `unite` | `"facteur"`, `"°C"`, `"semaines"`, `"probabilité"` |
| `neutre` | valeur d'un individu moyen de l'espèce (1,0 pour un facteur, 0 pour un décalage) |
| `sigma_a` | **diversité génétique additive de l'espèce** (écart-type, dans l'unité) |
| `bornes` | bornes dures physiologiques (remplace `clamp_gene` global) |
| `adaptogene` | lié à une mémoire d'exposition (plasticité existante) |

Une espèce peut surcharger `neutre` et `sigma_a` par un dictionnaire de classe, par exemple
`genetique = {"autofecondation": {"neutre": 0.95}}`. C'est **par espèce**, pas par plante.

`plant.gene(name)` renvoie la valeur du caractère, ou son **neutre** s'il est absent, et non
plus 1,0. Les consommateurs actuels restent valides tant qu'un caractère reste un `facteur`.

**Ordre des gènes : ajout EN QUEUE uniquement.** Les canaux de hash sont indexés par
position (garde-fou existant).

### Valeurs de départ (calibrage F5)

| Caractère | Unité | Neutre | σ_A | Note |
|---|---|---|---|---|
| hauteur, vigueur, resistance_pathogene, tolerance_secheresse, tolerance_ombre, tolerance_asphyxie, port_trapu, rusticite_froid | facteur | 1,0 | 0,10 | inchangés ici (`rusticite_froid` est refondu au sprint ②) |
| `germination_thermique` | °C (abaissement de l'optimum de levée) | 0 | 1,5 °C | avant : 3,5 °C × (g−1) avec σ 0,10, soit ±0,35 °C |
| `phenologie_florale` | semaines d'avance du tempo de vie | 0 | ≈ 1 semaine, à mesurer | pilote toujours les 3 horloges (floraison, abscission, sénescence) |
| `autofecondation` (neuf) | probabilité | par espèce : `self` 0,95 · `insect` 0,15 · `wind` 0,05 | 0,05 | borné [0, 1] |

Les fourchettes viennent de la littérature (`etude` §2.4-2.5) et sont **non revérifiées
espèce par espèce**. Le banc ③ les confronte à la réponse à la sélection mesurée.

## 4. L'hérédité

Notations : `a` = valeur d'un caractère, `F` = consanguinité ∈ [0, 1], `z` = tirage
gaussien **déterministe** (hash par canal, comme aujourd'hui).

**Enfant croisé** (mère m, père p) :

    â      = (a_m + a_p) / 2
    σ_s²   = ½ · σ_A² · (1 − (F_m + F_p)/2)     # brassage (échantillonnage mendélien)
    σ_μ²   = H_MUT · σ_A²                        # filet de mutation, H_MUT = 0,01
    a      = borne(â + z₁·σ_s + z₂·σ_μ)
    F      = 0                                   # partenaires supposés non apparentés

**Enfant autofécondé** : `â = a_m`, `σ_s² = ½·σ_A²·(1 − F_m)`, `F = (1 + F_m)/2`.

**Croisé ou autofécondé ?** Le choix se fait graine par graine, par hash déterministe
contre le gène `autofecondation` de la mère. Le **repli actuel** quand aucun père n'est
disponible reste celui du code (`sim/reproduction.py`, vers les lignes 120-136 ; le vérifier
avant de toucher).

**Introgression** (père d'une autre espèce de la même famille) : même formule, avec la
valeur du père dans **son** unité. Si les neutres diffèrent, le père contribue par son
**écart à son neutre**, ajouté au neutre de la mère.

`H_MUT = 0,01` est un choix de jeu (réel ≈ 0,001). Il évite qu'une lignée autogame se fige
pour toujours.

## 5. Fondateurs, semences, banque de graines

- **Fondateur sauvage** (`founder_genes`, banque ensemencée) : `a = neutre + σ_A·z`, `F = 0`.
- **Semence cultivée** (cultivées de démarrage, `planter` sans lignée) : c'est une
  **variété**. Toutes les graines d'une même variété partagent un centre
  `neutre + σ_A·z_variété` (hash espèce + seed du monde). Autour de ce centre, la dispersion
  vaut `σ_A·√(1 − F)`, avec `F = 0,9` si l'espèce est autogame et `F = 0` sinon. Les
  tomates achetées se ressemblent ; les courges, non.
- **Banque de graines** (`GeneStat`) : moyenne et variance par caractère, **plus la moyenne
  de F** par espèce et par parcelle. Une graine tirée du pool : `a ~ N(moyenne, variance)`,
  `F = moyenne F`. Les valeurs initiales de `GeneStat` prennent le **neutre** du caractère.

## 6. Les compromis de ce sprint

- **Dépression de consanguinité.** Un enfant consanguin d'une espèce **allogame** pousse
  moins : `vigueur effective × (1 − DI · F · (1 − s_espèce))`, avec `DI = 0,3` et
  `s_espèce` le neutre d'`autofecondation`. Les autogames l'ont purgée (facteur ≈ 1). La
  formule s'applique au même endroit que `cout_defense` (compromis croissance/défense
  existant). Pas de malus direct sur la santé.
- **Précocité ↔ taille.** Une avance de floraison réduit la hauteur atteinte
  (`hauteur × (1 − K_PREC · avance_semaines)`, `K_PREC = 0,03`), et un retard l'augmente,
  dans les bornes. C'est réel : une plante qui fleurit tôt a eu moins de temps pour croître.

## 7. Ce qui se voit

- **Diversité visible** : les tailles, les dates de floraison et les levées se dispersent
  davantage (σ réalistes).
- **Lignées** : une planche de tomates issues de graines récoltées se ressemble de plus en
  plus ; une planche de courges reste bigarrée.
- **Pont** : les gènes sont exportés avec leur unité, et F aussi. Le survol de debug (touche G)
  affiche « levée −2,1 °C », « floraison +1 sem. », « lignée fixée (F 0,94) ».
- **Voix** : une entrée d'encyclopédie et de carnet « lignée » (concept). Le carnet note
  quand le joueur sème ses propres graines récoltées. Le texte n'est interprétatif qu'au
  palier de maîtrise.

## 8. Golden et perf

- Tronçon ① : refactor pur, golden **INTACT**.
- Tronçon ② : l'hérédité change toutes les valeurs de gènes → golden **RE-FIGÉ LARGE**
  annoncé.
- Tronçon ③ : unités et compromis → golden **RE-FIGÉ** annoncé.
- Tronçon ④ (vue) : golden **INTACT**.
- Perf : **O(1) par naissance** (2 tirages de plus par caractère) et O(1) par plante pour les
  compromis. Budget ≤ +2 % de tick, **mesuré** au ② (profil avant/après sur le smoke).

## 9. Hors périmètre

- Consanguinité biparentale (voisins apparentés) : F = 0 au croisement, limite assumée.
- Allèles, dominance, locus : option C de l'étude, écartée.
- Les nouveaux caractères appartiennent aux sprints ② (thermiques) et ③ (19 caractères
  vivants).
