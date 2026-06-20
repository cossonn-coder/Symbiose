# CONCEPTION — SOL · Structure / compaction (dette D30)

> Conception figée le 2026-06-19 (Sprint physico-chimie du sol, volet C/3).
> Absorbe la dette **D30**. Étude de fond : `sprints/etude_physicochimie_sol.md`.
> Ordre global du sprint : `CONCEPTION_SOL_PH.md` §6. Volets frères : pH, NPK.

## 0. Objectif & intuition

La **structure** = comment les particules s'agrègent en **grumeaux** poreux qui
laissent circuler eau et air. Un sol compacté (piétiné, battu par la pluie sur sol
nu, semelle de bêchage) devient asphyxiant : l'eau ruisselle ou s'engorge (anoxie),
les racines ne pénètrent plus, la vie aérobie régresse.

Aujourd'hui le bénéfice d'aération **n'a aucun champ où s'inscrire** : `becher`
tape le sol (malus codé ↓vers ↓microbiome) mais `grelinette` est un **no-op**. La
dette D30 avait tranché 3 options ; vu l'élargissement à pH+NPK, **on retient
l'Option B** (champ dédié `structure_sol`) — décision Nico 2026-06-19 — pour
**mutualiser l'infra « champ lent hérité du sol »** construite pour le pH plutôt
que de faire transiter le bénéfice uniquement par les vers (Option A, sobre).

Philosophie : **#2** (la structure module l'infiltration et l'uptake — un flux —
jamais un bonus direct) ; **#3** déterministe ; **#5** lisible par le ruissellement,
l'engorgement, la vigueur racinaire, pas un chiffre.

## 1. État de départ

| Brique | Où | Statut |
|---|---|---|
| `becher` (malus ↓vers ↓microbiome) | `sim/actions.py` | OK — y ajouter ↓`structure_sol` |
| `grelinette` | actions | **no-op à compléter** (↑structure, ↑vers) |
| `populations["lombric"]` (bioturbation) | `fields/population.py` | OK — moteur du ↑structure |
| Asphyxie `HUM_EXCES`, `asphyxie_factor` | `plant_uptake` | OK — pont direct, à aggraver si compacté |
| Modèle eau (infiltration/rétention/drainage) | hydrologie | OK — l'infiltration deviendra ∝ structure |
| `MedicagoLupulina` (racine décompactante) | catalogue | OK — exemple de pivot ↑structure |
| **Champ `structure_sol`** | — | **néant, à créer** |

## 2. Le modèle

### 2.1 Champ `structure_sol ∈ [0,1]` (tronçon ⑧ global)

`GridField` par plot — **1 = grumeleux/aéré, 0 = compacté/battant**. Init hérité du
`soil_type` (table §3 : sable meuble mais pauvre, argile compacte, terre bonne).
Champ **lent** (inertie comme le pH) dérivant sous forces constructrices et
destructrices :

```
d_struct[r,c] = + BIOTURB     · lombric_norm[r,c]          ⟵ vers (constructeur lent)
              + RACINE_PIVOT · presence_pivot[r,c]          ⟵ racines décompactantes
              + GRELINETTE(event présent)                    ⟵ geste : aère sans retourner
              − BATTANCE     · pluie_norm · (1 − couvert_norm) ⟵ pluie sur sol nu
              − BECHAGE(event)                               ⟵ semelle de tassement (cf. 2.2)

structure_sol += d_struct · STRUCT_INERTIA
structure_sol  = clamp(0, 1)
```

`couvert_norm` = litière protectrice (paillage amortit la battance) — réutilise
`om_fresh_at` comme le thermique.

### 2.2 Bêchage : leurre immédiat puis re-tassement

Pédagogie : le bêchage **paraît** ameublir mais re-tasse après. On modélise un
**pic transitoire** : `becher` pose un petit bonus structure qui **décroît sous
zéro** (la semelle), tandis que `grelinette` pose un gain **durable**. (Si trop
lourd à coder, version sobre : `becher` = malus net, `grelinette` = gain net — à
trancher à l'implémentation, défaut = sobre.)

### 2.3 Couplages lecteurs

Trois lecteurs branchés en même temps (tronçon ⑧) :

```
infiltration_factor = structure_sol           # compacté → ruissellement + stagnation surface
asphyxie_factor    ×= (2 − structure_sol)      # compacté + saturé → anoxie aggravée (modèle existant)
uptake_factor      ×= mix(STRUCT_UPTAKE_MIN, 1, structure_sol)  # racines pénètrent moins en sol tassé
```

L'infiltration nourrit l'hydrologie existante : une part de la pluie **ruisselle**
(perdue) quand `structure_sol` est basse, et l'eau infiltrée stagne moins.

## 3. Constantes (placeholders)

```python
STRUCTURE_INIT_PAR_SOL = {"terre": 0.7, "argile": 0.45, "sable": 0.6, "roche": 0.4}
STRUCT_INERTIA   = 0.05     # champ lent (saisons)
BIOTURB          = 0.30     # construction par les vers (× lombric_norm)
RACINE_PIVOT     = 0.10     # décompactage par racines pivots
GRELINETTE_GAIN  = 0.15     # gain durable d'un passage de grelinette
BECHAGE_MALUS    = 0.20     # tassement net (version sobre) ou pic transitoire (version fidèle)
BATTANCE         = 0.15     # dégradation par pluie battante sur sol nu
STRUCT_UPTAKE_MIN = 0.5     # uptake résiduel en sol totalement compacté
```

`grelinette` booste aussi `lombric` (effet secondaire), `becher` conserve son malus
vers/microbiome actuel + ajoute ↓`structure_sol`.

## 4. Tronçon & golden

- **⑧** (global 8) Champ `structure_sol` + dérive + **trois couplages d'un coup**
  (infiltration, asphyxie, uptake) + `grelinette` activée / `becher` complété.
  Golden **RE-FIGÉ MAÎTRISÉ** (dérive hydrologie + uptake, vérifiée localisée).

> Contrairement au pH/NPK, on ne pose pas le champ neutre séparément : la structure
> n'a qu'un tronçon, le re-figé est assumé en une fois. Si la dérive surprend,
> scinder en ⑧a (champ neutre) / ⑧b (couplages) au moment de l'implémentation.

## 5. Interconnexions

`structure_sol` ↔ **vers** (bioturbation ↑, `becher` ↓) · ← **racines pivots**
(catalogue) · ← **paillage/battance** (litière) · → **infiltration** (modèle eau) ·
→ **asphyxie** (`HUM_EXCES`/`asphyxie_factor` existant) · → **uptake racinaire**.
Mutualise l'infrastructure « champ lent hérité du `soil_type` + dérive par gestes »
avec le **pH** (volet A).

## 6. Garde-fous

- **Golden** : un seul tronçon, re-figé **annoncé** ; vérifier que la dérive vient
  bien de l'infiltration/uptake/asphyxie et de rien d'autre.
- **Couches** : `fields` n'importe jamais `sim` ; les events gestes (`grelinette`/
  `becher`) passés en argument depuis l'engine.
- **Taille** : bloc court ; si débordement, `fields/ecofields/structure.py` helper pur.
- **Philo #2/#5** : la compaction agit par flux (infiltration/uptake) → réponse
  biologique (ruissellement visible, vigueur), jamais de malus direct ni de chiffre.
- **Version sobre par défaut** sur le re-tassement (2.2) : ne pas sur-modéliser le
  pic transitoire si le gain pédagogique ne le justifie pas jeu-en-main.
