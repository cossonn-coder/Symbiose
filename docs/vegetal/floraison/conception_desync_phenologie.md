# CONCEPTION — Désynchronisation phénologique (+ rendu feuilles/segments dès ×1)

> Figé le 2026-07-14 (skill /conception). Sprint : `sprints/vegetal/floraison/sprint_desync_phenologie/`.
> Sujet : les événements de vie des plantes (floraison, fanaison des feuilles,
> déclin sénescent) surviennent **en lockstep** ; on veut les **étaler par
> individu**. + demande de rendu : feuilles ET segments visibles **dès le zoom ×1**.

## 0. Problème observé (Nico, F5)

« Les fleurs sortent toutes en même temps, les feuilles fanent toutes en même
temps. » Un jardin où chaque cohorte agit d'un seul bloc — pas de vie étalée,
pas de nectar soutenu, pas de canopée qui se déshabille progressivement.

## 1. Diagnostic (investigation moteur)

Trois horloges, trois causes **distinctes** :

| Événement | Fichier | Cause de la synchronie |
|---|---|---|
| **Floraison** | `sim/engine/floraison.py` | Double porte GDD (par-plante) ET photopériode (fenêtre globale). Un gène de désync EXISTE (`phenologie_florale`, décale le seuil GDD de `FLORA_GENE_SHIFT·(g−1)`) mais **`FLORA_GENE_SHIFT = 40` est un placeholder** : avec σ=0.10 sur le gène → étalement ≈ **±0.3 semaine** contre ~12-14 GDD/semaine d'été → **imperceptible**. |
| **Fanaison (abscission)** | `sim/engine/decompo.py::_abscission` (déclenché `boucle.py:472`) | Déclenchée aux **`ABSCISSION_WEEKS = (38, 39)` GLOBALES**, pour tous les caducs, **zéro variance**. |
| **Sénescence (onset)** | `sim/engine/mortalite.py::_tick_senescence_health` | Onset au **`SENESCENCE_ONSET = 0.70 × longévité` FIXE** pour tout individu. La *mort* est ensuite dispersée par un hash par-plot, mais le **début du déclin est synchrone par cohorte**. |

**Fil commun** : la désynchronisation exige une **variance phénologique
par-individu**. Elle n'existe que pour la floraison (et calibrée ~50× trop
faible) ; abscission et onset de sénescence n'en ont **aucune**.

### 1bis. Le passage de saison RE-SYNCHRONISE la VUE (Nico, 2026-07-14)

Investigation demandée par Nico (« vérifier que le passage de saison n'est pas un
déclencheur d'affichage ») → **C'EST LE CAS**, et c'est la moitié cachée du bug.
Même une sim parfaitement désynchronisée resterait invisible car la vue re-cale
tout sur la **saison globale** :

| Signal visuel | Où | Gate |
|---|---|---|
| **Couleur feuille** (automne chaud) | `visuals/PlantRenderer.Organs.cs:261` `LeafColor(pal, season, …)` | `WorldView.CurrentSeason` (**globale**) → tout le feuillage vire à l'automne au tick du passage de saison. |
| **Fleurs** | `Organs.cs:298` `organ == "flower"` | Proxy `base["organ"] = repro.get(saison)` (`serialize.py:182`, table `REPRO_BY_SEASON`) → fleurs par **saison×espèce**, jamais par l'état moteur `floraison` (le scalaire par-plante N'EST PAS exporté). |
| **Présence feuille (hiver)** | `foliage_density_at(p, saison)` | Chute binaire à 0 pour caduc en hiver (per-espèce×saison). |

**En revanche, la sénescence VISUELLE est déjà par-plante** : `leaf_symptoms`
(dont `senescence`, `serialize.py:170`) est exporté par individu et `SymptomTint`
le pose sur la feuille → dès que ① jitter l'onset (miroir sémio), le signe se
désync **tout seul**. Il ne reste donc à débrancher de la saison globale que
**(a) les fleurs** et **(b) la teinte automnale du feuillage**.

Analyse GDD (pour comprendre pourquoi la porte photopériode n'est PAS le vrai
coupable) : fenêtre par défaut `[13.5, 16.5] h`. À 45°N le jour ne dépasse jamais
~16 h → `bloom_daylen_max` n'est jamais restrictif ; `bloom_daylen_min = 13.5 h`
s'ouvre vers la semaine 14. Le GDD (`gdd_floraison ≈ 200`) n'est atteint que
vers la semaine 30 → **c'est la porte GDD qui lie**, en plein dans la fenêtre.
Donc **renforcer le décalage GDD par le gène suffit** ; on ne touche PAS la porte
photopériode (knob secondaire, réservé si l'étalement restait insuffisant).

## 2. Modèle retenu — un gène « tempo de vie » partagé

**Décision (arbitrages Q1-Q3, 2026-07-14)** : désync des **trois** horloges via
**un seul gène héritable partagé**, réutilisant `phenologie_florale` comme
**tempo de vie** global. Convention : **`g > 1` = tempo RAPIDE / individu
précoce** — il fleurit tôt, largue ses feuilles tôt, sénesce tôt (chronotype
cohérent). `g = 1.0` (neutre) ⇒ comportement historique **inchangé** (l'effet est
proportionnel à `g − 1`).

Pourquoi le gène plutôt qu'un hash non héritable (option écartée) : le gène est
**héritable** (`child_genes`) → **sélection darwinienne émergente** (déjà en
place), **déterministe** (tiré par hash de position, philo #3, zéro RNG vivant),
et **hétérogène** (philo #7). Bonus émergent : les **clones** (bouture, ramets)
copient les gènes → restent **synchrones** entre eux (biologiquement correct),
tandis que les **semis** (variance `founder_genes` σ=0.10) s'étalent. On ne
renomme PAS le gène (churn + golden : `phenologie_florale` reste sa clé, sa
sémantique est simplement élargie et documentée).

On ne crée **aucun** gène ni système parallèle — on **recalibre** un knob
existant et on **branche** le même gène sur deux sites de plus.

### 2.1 Floraison — recalibrer le décalage
Formule inchangée, constante renforcée :
```
gdd_eff = cls.gdd_floraison − FLORA_GENE_SHIFT · (g − 1)
```
`FLORA_GENE_SHIFT : 40 → ≈ 200` (départ de calibrage). À σ=0.10 et ~12 GDD/sem,
ça donne **±~1.6 semaine à ±σ**, **±~3 semaines à ±2σ** — étalement visible.
Valeur exacte à affiner en F5 (knob de calibrage, pas une vérité).

### 2.2 Fanaison (abscission) — semaine par-individu
Remplacer le déclenchement global 2-semaines par une **fenêtre d'automne** dans
laquelle **chaque plante largue une fois**, à sa semaine propre :
```
semaine_abscission(plant) = round( ABSCISSION_BASE − ABSCISSION_JITTER · (g − 1) )
   bornée dans la fenêtre [ABSCISSION_MIN, ABSCISSION_MAX] de l'automne
```
`g > 1` (précoce) → largue plus tôt. Départ : `ABSCISSION_BASE = 38`,
`ABSCISSION_JITTER ≈ 15` (±σ ⇒ ±1.5 sem), fenêtre `[34, 39]`. Chaque caduque
dépose **une seule fois** sa nécromasse-feuille annuelle à sa semaine (préserve
l'ordre de grandeur du total ; le re-figeage absorbe l'écart exact).

### 2.3 Sénescence — onset par-individu
Jitter de la fraction d'onset, formule de pression inchangée en aval :
```
onset_eff(plant) = clamp( SENESCENCE_ONSET − SEN_ONSET_JITTER · (g − 1), 0.05, 0.95 )
sen = (age_years − onset_eff·L) / ((1 − onset_eff)·L)
```
`g > 1` (précoce) → onset abaissé → sénesce plus tôt. Départ :
`SEN_ONSET_JITTER ≈ 0.5` (±σ ⇒ ±0.05 de fraction de longévité). **Miroir
OBLIGATOIRE** dans `sim/semiologie.py::senescence` (le signe visuel de sénescence
est un « miroir EXACT » de la pression D27 — il doit jitter à l'identique, sinon
le signe et la mort divergent).

### 2.4 Golden — re-figeage contrôlé (annoncé)
Les plantes du golden sont semées via `semer_fondateur` → **variance génétique**
(`g ≠ 1`). L'effet de désync ne s'annule donc PAS sur elles : le golden **dérive**
(floraison → nouaison → litière/eco ; abscission → litière feuille ; onset →
`vitalite`, qui est haché). **Re-figeage LARGE, localisé, expliqué** au tronçon
moteur. Ce n'est PAS un bug : c'est l'effet attendu des knobs qui « mordent »
enfin sur la variance fondatrice. Vérif indépendante du golden : un **test
d'étalement** (spread des semaines de floraison d'une cohorte > 0) prouve que la
désync opère.

## 3. Rendu — feuilles & segments dès ×1

- Deux seuils LOD perf dans `visuals/PlantRenderer.cs` :
  `SegmentDetailMinZoom = 4`, `OrganDetailMinZoom = 8` → en dessous, **silhouette**.
- **Culling déjà en place** (`WorldView.Camera.cs::CullPlants` — viewport + marge
  400 cm, réévalué move/zoom/snapshot). Le point 2 (« ne rendre que l'écran +
  alentours ») est **déjà satisfait**.
- **Décision (Q3)** : abaisser **les deux seuils à 1** (segments ET organes dès
  ×1 ; le palier ×0.5 « monde entier » garde la silhouette). Le culling est le
  **filet perf**. **Vérif F5 obligatoire** : FPS tenu à ×1 (aire large × plantes
  minuscules) ET détail lisible. Si ça rame ou devient du bruit sous-pixel, on
  remonte un cran de façon ciblée (escape hatch documenté).

## 4. Coût perf
- Désync moteur : **~nul** (recalibrage de constantes + arithmétique par-plante
  déjà dans les boucles existantes ; abscission balaie ~6 semaines d'automne au
  lieu de 2, toujours O(plantes/tuile), trivial).
- Rendu ×1 : à **mesurer** en F5 ; culling = filet déjà présent.

## 5. Découpage (perf-first, vue Godot en dernier — règle projet)
- **① Désync des trois horloges** (MOTEUR/sim) — `floraison.py`, `decompo.py` +
  `boucle.py` (fenêtre abscission), `mortalite.py` + `semiologie.py`, constantes.
  **Golden re-figé LARGE, annoncé.** Test d'étalement en garde. Désync AUSSI le
  signe de sénescence visuel (via le miroir sémio → `leaf_symptoms`).
- **② Pont — signaux par-plante pour la vue** (Python, `simserver/serialize.py`
  + éventuel helper phénophase) : exporter `floraison` (scalaire moteur, existe)
  et `automne` (phénophase par-plante ∈ [0,1], ramping vers la semaine
  d'abscission propre de la plante, fonction du tempo gène). **Golden INTACT**
  (hints hors `_PLANT_ATTRS` ; ne PAS toucher `foliage_density_at` qui sert la
  sim/light). Réutiliser la semaine d'abscission par-plante de ①.
- **③ Vue Godot** (C#, `PlantRenderer.Organs.cs` + `PlantStructure`/snapshot lu) :
  **fleurs** dessinées ∝ `floraison` par-plante (remplace le proxy `organ`
  saisonnier) ; **couleur/fondu feuille** ∝ `automne` par-plante (remplace le
  switch `season` global de `LeafColor`) ; abaisser `SegmentDetailMinZoom` et
  `OrganDetailMinZoom` **→ 1** (silhouette gardée au seul palier ×0.5).
  **Golden intact.** Vérif F5 : détail dès ×1 + perf (culling filet) + désync
  VISIBLE (fleurs/feuilles étalées, plus de flip au passage de saison).

## 6. Ce qu'on ne fait PAS (anti-scope-creep)
- Pas de renommage du gène (`phenologie_florale` garde sa clé — golden/churn).
- Pas de nouveau gène, pas de système parallèle.
- Pas de refonte de la porte photopériode (knob secondaire, réservé).
- Pas de désync de la germination (déjà étalée pour le féral, hors sujet).
