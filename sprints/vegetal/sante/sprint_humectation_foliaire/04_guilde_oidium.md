# ④ La guilde oïdium — l'exception qui interdit la solution unique

**Sprint** : `sprint_humectation_foliaire`
**Golden attendu : NEUTRE — mais à PROUVER, pas à supposer**
**Conception** : `docs/vegetal/sante/conception_humectation_foliaire.md` §2.4
**Prérequis** : ①②③ livrés.

## Objectif

Créer la **seconde** guilde cryptogamique, biologiquement opposée à la première, pour que
le joueur n'ait pas d'optimum unique.

### Le fait biologique (à ne pas simplifier)

Presque toutes les cryptogames du feuillage (mildiou, rouille, tavelure, botrytis)
exigent un **film d'eau liquide** pendant des heures. **L'oïdium est l'exception
notoire** : il germe **sans eau libre**, préfère un air humide avec un feuillage **sec**,
et l'eau libre lui est **défavorable** (elle fait éclater ses conidies — d'où l'aspersion
comme remède contre l'oïdium de la vigne). Son climat : nuits humides + journées chaudes
et sèches, typiquement la fin d'été.

**Conséquence de jeu** : aérer et garder le feuillage sec écrase le mildiou et **ouvre la
porte à l'oïdium** ; asperger fait l'inverse. Pas de geste universellement bon.

## Fichiers à toucher

1. `data/code/plants/base/familles.py` — l'attribut sur `PlantBase` (~ligne 91, à côté de
   `fungal_susceptibility`)
2. `data/code/plants/species/potageres.py` — courgette (~ligne 106)
3. Le pommier (cherche-le : `grep -rn "class Apple\|Malus" plants/`)
4. `data/code/fields/ecofields/constants.py` — constantes oïdium
5. `data/code/sim/effects/perturbations.py` — la fonction `oidium_disease`
6. `data/code/sim/effects/__init__.py` — export (~lignes 28 et 39, patron `fungal_disease`)
7. Le site d'appel des perturbations (`apply_disturbances`, `perturbations.py:513`)

## Modèle

### L'attribut — ADDITIF, pas un enum

```python
fungal_susceptibility: float = 0.5    # EXISTANT — guilde « à eau libre »
oidium_susceptibility: float = 0.0    # NEUF — guilde « air humide, feuillage sec »
```

**Pourquoi additif et non un enum de guilde** : (i) rétrocompatible — défaut 0.0 ⇒ aucun
effet ⇒ golden neutre ; (ii) biologiquement juste — une espèce peut être sensible aux
**deux** (le pommier a tavelure *et* oïdium), ce qu'un enum interdirait ; (iii) aucune
réindexation d'`InoculumField`, qui reste indexé par **famille** seule (l'inoculum ne
distingue pas la guilde).

### Les porteurs — aucune espèce nouvelle

Le porteur d'oïdium **existe déjà** : la **courgette** (`Zucchini`, `Cucurbitaceae`,
`plants/species/potageres.py:94`) est le cas d'école — grandes feuilles molles,
`foliage_density = 0.60`, port étalé, fin d'été chaud.

```python
oidium_susceptibility = 0.9    # Cucurbitaceae : LE cas d'école de l'oïdium
```

Second porteur léger pour que la guilde ne soit pas mono-espèce : le **pommier**,
`oidium_susceptibility = 0.3`.

⚠️ **N'ajoute AUCUNE espèce** (la conception a écarté prêle et vigne — elles restent
candidates pour D26). Donc la règle « toute plante ajoutée = ses 5 voix » ne se
déclenche pas : la courgette et le pommier ont déjà les leurs.

### Les constantes

```python
# --- Guilde OÏDIUM (sprint humectation ④, §2.4) ---
# L'exception cryptogamique : germe SANS eau libre, aime l'air humide et le feuillage
# SEC (l'eau fait éclater ses conidies). Signal = (1 − humectation) × chaleur → fin
# d'été chaude et sèche. Le dilemme avec le mildiou interdit la solution unique.
OIDIUM_BASE   = 0.035   # base avant modulation (ordre de FUNGAL_BASE = 0.04)
OIDIUM_T_REF  = 18.0    # °C — sous ce seuil, aucune pression oïdium
OIDIUM_T_SPAN = 10.0    # °C — amplitude jusqu'à la pression pleine
```

### La fonction — miroir de `fungal_disease`

```python
def oidium_disease(plant, tile, eco, seed: int, week: int,
                   vent_local: float = 0.0) -> list[Mutation]:
    if not plant.is_alive or plant.stage.name == "semis":
        return []
    susc = getattr(plant.plant_class, "oidium_susceptibility", 0.0)
    if susc <= 0.0:
        return []                      # défaut 0.0 → sortie immédiate, coût nul
    susc /= plant.expressed_gene("resistance_pathogene")
    r, c = plant.position
    t_air = eco.temperature.at_plot(r, c)
    chaleur = max(0.0, min(1.0, (t_air - OIDIUM_T_REF) / OIDIUM_T_SPAN))
    if chaleur <= 0.0:
        return []
    # SIGNAL INVERSE du mildiou : feuillage SEC (1 − humectation) × chaleur.
    oidium_sig = (1.0 - plant.wetness_memory) * chaleur
    density = _local_density(plant, tile, same_family=True)
    p = eco.disease_probability(r, c, base_rate=OIDIUM_BASE,
                                family=plant.plant_class.family)
    p *= oidium_sig * (0.4 + density) * susc
    if _hash_noise(seed, week * 47, r, c) < p:
        return [ReduceHealth(plant, 1, reason="oïdium", cause="maladie")]
    return []
```

**Canal de bruit : `week * 47`.** Inventaire vérifié au grep — utilisés :
`week·`{0,2,3,5,7,11,13,17,19,23,29,31,37,41,53,59} ; `week·43` **réservé D41, ne le
prends pas** ; libres : 47, 61, 67. `fungal_disease` tire sur `week·13`.

Note : **pas** de `FUNGAL_VENT_DRY` ici — le vent ne protège pas de l'oïdium (il aide
même à disperser ses conidies). C'est précisément ce qui crée le dilemme. N'ajoute pas
d'assèchement protecteur par symétrie mécanique.

Branche l'appel dans `apply_disturbances` à côté de `fungal_disease`, en passant le même
`vent_local`, et laisse `_cap_chronique` faire son travail si la mutation y est soumise
(vérifie comment `fungal_disease` y est traitée et **fais pareil**).

## Golden — NEUTRE, à PROUVER

Attendu neutre par **double** construction : `oidium_susceptibility` vaut 0.0 par défaut
(sortie immédiate), et ni la courgette ni le pommier ne sont dans le smoke test
(2 tuiles × 4 ans).

⚠️ **Prouve-le, ne le suppose pas.** Vérifie explicitement quelles espèces le golden
exerce (lis `tests/test_golden.py`) et confirme qu'aucune ne porte un
`oidium_susceptibility > 0`. Si le pommier **est** dans le smoke, tu as deux options —
mets son `oidium_susceptibility` à 0.0 et note-le dans `00_etat.md` pour un calibrage F5
ultérieur, **ou** annonce un re-figeage : dans ce cas **demande d'abord**, le kickoff ne
l'autorise pas.

## Ce qu'il ne faut PAS faire

- ❌ Ajouter une espèce (prêle, vigne — écartées, cf. D26).
- ❌ Transformer `fungal_susceptibility` en enum de guilde (casserait 27 espèces).
- ❌ Réindexer `InoculumField` par (famille, guilde) — la conception a tranché non.
- ❌ Créer un gène neuf : `resistance_pathogene` (D22b) médie les **deux** guildes.
- ❌ Prendre le canal `week·43` (réservé D41).
- ❌ Ajouter un assèchement protecteur du vent à l'oïdium (tuerait le dilemme).
- ❌ Re-figer le golden sans autorisation explicite.
- ❌ Lancer `test_epaisseur_500ans` (interdit).

## Vérification

1. `python3 -m tests.test_golden` → hash **inchangé**.
2. Étends `tests/test_humectation.py` : (a) une espèce à `oidium_susceptibility = 0`
   n'attrape **jamais** l'oïdium ; (b) à humectation **basse** + chaleur, la courgette
   attrape l'oïdium ; (c) à humectation **haute**, l'oïdium **s'effondre** alors que le
   mildiou monte — **c'est le test du dilemme**, il doit exister et être explicite ;
   (d) le froid (T < `OIDIUM_T_REF`) annule la pression.
3. `python3 main.py` tourne sans crash.
4. `python3 tools/compte_ldc.py perturbations.py` — le fichier est déjà long (~530 LDC
   avant ce tronçon d'après son sommaire de fonctions). **S'il dépasse 400, signale-le
   dans `00_etat.md`** : il faudra un `/refactor` (scission par concept : nécromasse /
   maladies / stress chroniques / herbivorie). Ne scinde pas toi-même dans ce tronçon.
