# Tronçon ⑤ — Fenêtres pH par espèce (noyau) + chlorose alcaline + indicatrices

> Sprint physico-chimie du sol. Conception : `docs/conception/CONCEPTION_SOL_PH.md`
> §2.3 (fenêtre d'espèce), §2.2 (chlorose), §3 (constantes), §5 (interconnexions).
> Kickoff **autosuffisant** (relançable à froid). Python depuis `data/code/`.
> Tronçons ① (champ `ph` hérité + dérive, inerte), ② (champs `n`/`p`/`k` posés),
> ③ (bascule Liebig : `fertilite` supprimé, uptake plafonné, CEC, lessivage diff.),
> ④ (cloches `dispo_i(ph)` sur uptake N/P/K + microbiome) **déjà CLOS**.
> Golden figé `d8856261bbe49787…`.

## Objectif

Le pH module aujourd'hui la **disponibilité des nutriments** (④) mais **chaque
espèce vit indifféremment à n'importe quel pH**. Le ⑤ donne à chaque espèce une
**fenêtre d'acidité** (`ph_opt`/`ph_tol`) qui pilote **deux portes** :
- **germination / succession** : une espèce ne s'installe pas hors de sa fenêtre
  (une myrtille ne lève pas sur calcaire) ;
- **croissance / vigueur** : elle dépérit doucement en bord de fenêtre.

Plus la **chlorose alcaline reportée du ④** : une espèce **acidophile** (`ph_opt`
bas) sur sol alcalin (`ph > CHLOROSE_PH`) subit un lockout du fer → **malus de
vigueur** (l'indice visuel jaunissement = vue, tronçon ⑨). Plus les **indicatrices
d'acidité** (oseille, prêle) qui SIGNALENT un sol acide au joueur.

## Le modèle (CONCEPTION §2.3 + §2.2)

### Cloche d'espèce
```
bell(ph ; ph_opt, ph_tol) = exp( −((ph − ph_opt) / ph_tol)² )      ∈ ]0,1]
```
- `ph_opt` : pH optimal de l'espèce. `ph_tol` : demi-largeur de tolérance.
- **Défaut NEUTRE** : `ph_tol` LARGE (≈ 3.0) ⇒ `bell ≈ 1.0` sur toute la plage
  [4.0, 8.5] → une espèce non spécifiée est insensible au pH (golden ~neutre).
- C'est la **même forme** que `dispo` du ④ (gaussienne) — réutiliser le helper pur
  `dispo`-like, ou ajouter `bell(ph, opt, tol)` dans `nutriments.py` /
  `vigueur_plante.py` (calcul pur, zéro RNG).

### Noyau démonstrateur (le reste du catalogue = `ph_tol` large ⇒ neutre)
| Espèce | type | `ph_opt` | `ph_tol` |
|---|---|---|---|
| **Myrtille** (à AJOUTER au catalogue) | acidophile/calcifuge | 4.8 | 0.8 |
| Lavande / thym | calciphile | 7.4 | 1.1 |
| Oseille, prêle | **indicatrices acidité** | 5.0 | (UnlockCondition `ph < 5.5`) |

> ⚠️ La myrtille n'existe peut-être pas encore — vérifier au grep dans
> `plants/species/` (sauvages/aromatiques). Si absente, l'AJOUTER (espèce
> acidophile = le démonstrateur roi de la chlorose). Lavande/thym/oseille/prêle :
> grep leur présence ; si absentes, soit les ajouter, soit choisir un substitut
> déjà présent et le NOTER.

### Chlorose alcaline (reportée du ④)
```
si plante.acidophile (ph_opt < SEUIL_ACIDOPHILE, ex. 5.5) ET ph_local > CHLOROSE_PH (7.6) :
    facteur_chlorose < 1.0   (malus de vigueur, lockout du fer)
```
Appliqué côté `sim/vigueur_plante.py` (là où `qi_local` lit déjà `min(n,p,k)`).
**Pas un gate de mort** (philo #2) : un facteur de vigueur qui fait dépérir, pas
disparaître. L'indice visuel (jaunissement) = tronçon ⑨ (vue).

## Constantes (CONCEPTION §3 — à ajouter dans `fields/ecofields/constants.py`)
```python
CHLOROSE_PH       = 7.6     # au-dessus, chlorose ferrique des acidophiles (posée ICI, pas au ④)
SEUIL_ACIDOPHILE  = 5.5     # ph_opt en deçà duquel l'espèce est dite « acidophile » (sensible à la chlorose)
CHLOROSE_MALUS    = 0.5     # facteur de vigueur min à chlorose pleine (placeholder, calibrage post-test)
PH_TOL_DEFAUT     = 3.0     # demi-largeur LARGE par défaut → bell ≈ 1.0 (espèce pH-neutre)
```
Et **attributs de classe** dans `plants/base/familles.py` (`PlantBase`), façon
`temp_min_growth`/`gdd_floraison` (défauts NEUTRES) :
```python
ph_opt: float = 6.8          # pH optimal (défaut ≈ neutre)
ph_tol: float = PH_TOL_DEFAUT  # demi-largeur large → insensible par défaut
```
Override par espèce dans `plants/species/*.py` (myrtille 4.8/0.8, lavande 7.4/1.1…).

## Greffes exactes (repères, à re-vérifier au grep)

1. **Attributs espèce** — `PlantBase.ph_opt`/`ph_tol` (défauts neutres) dans
   `plants/base/familles.py` (~ligne 77, près de `temp_min_growth`). Override dans
   les espèces du noyau démonstrateur.

2. **Helper pur** — `bell(ph, opt, tol)` dans `nutriments.py` (à côté de `dispo`,
   même gaussienne) OU réutiliser `dispo` avec signature généralisée. Garder pur.

3. **Croissance / vigueur** — `sim/vigueur_plante.py` :
   - `qi_local` (ou `vigueur_plante`) : multiplier par `bell(ph_local, plante.ph_opt,
     plante.ph_tol)` — la plante hors fenêtre puise/croît moins. `ph_local` = moyenne
     `eco.ph.at_plot` sur `root_plots` (miroir de la lecture `min(n,p,k)`).
   - **Chlorose** : si `plante.ph_opt < SEUIL_ACIDOPHILE` ET `ph_local > CHLOROSE_PH`
     → facteur `CHLOROSE_MALUS` (ou gradué). Multiplie la vigueur.

4. **Germination / succession** — `fields/seedbank.py:233` (`niche_index`) et
   `sim/succession.py` (les 3 appels `niche_index` ~lignes 89/178/256). Porter la
   fenêtre pH comme FACTEUR de niche : une espèce hors fenêtre a une niche ≈ 0 → ne
   s'installe pas. **Vérifier la signature de `niche_index`** (a-t-elle accès au `ph`
   du plot et à l'espèce candidate ?). Greffe la plus délicate — lire d'abord.

5. **Indicatrices acidité** (oseille/prêle) — mécanique `UnlockCondition` côté
   catalogue (C#) ; côté Python, c'est leur **fenêtre pH basse** qui les fait
   prospérer SUR sol acide (succession). L'« indication » = leur présence visible.
   Vérifier comment les indicatrices existantes (catalogue `.Indicatrices.cs` côté
   C#, ou `archetype`/`keywords` côté Python) sont déjà modélisées avant d'ajouter.

## Golden attendu

**~NEUTRE** (CONCEPTION §4) : les espèces du noyau démonstrateur sont **neuves**
(myrtille/lavande) ou absentes du smoke (2 tuiles terre+argile, ph 6.8/7.0). Les
espèces déjà présentes gardent `ph_tol` LARGE → `bell ≈ 1.0` → cœur inchangé.
**Vérifier** : si une espèce du smoke reçoit un `ph_opt` ≠ 6.8, tracer la dérive.
La chlorose ne se déclenche PAS dans le smoke (pas d'acidophile sur ph > 7.6).
Si dérive ⇒ re-figer MAÎTRISÉ et annoncer ; sinon golden NEUTRE inchangé.

## À faire en fin de tronçon
- Ajouter `CHLOROSE_PH`/`SEUIL_ACIDOPHILE`/`CHLOROSE_MALUS`/`PH_TOL_DEFAUT` +
  attributs `ph_opt`/`ph_tol` + helper `bell`.
- Brancher fenêtre sur germination/succession ET croissance/vigueur + chlorose.
- Ajouter le noyau démonstrateur (myrtille acidophile au minimum).
- Vérifier suites (vigueur, population, lifecycle) + golden (NEUTRE ou re-figé
  maîtrisé annoncé). `test_senescence` reste rouge = D39 pré-existante (pas ⑤).
- MàJ `00_etat.md` (⑤ ✅, hash, dérive, note taille) ; `main.py` 50+ ans OK.
- Commit : `feat(sol) : tronçon ⑤ fenêtres pH par espèce (noyau) + chlorose alcaline + indicatrices — golden …`.
- Écrire `06_amendements_ph.md` avant le `/clear` (volet pH §2.4 : rondelles
  `chaux`/`soufre`, event-driven, `AMEND_PUSH` progressif sur saisons, golden NEUTRE).
