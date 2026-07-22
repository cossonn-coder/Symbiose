# CONCEPTION — Sémiologie foliaire (dette D33)

> Conception figée le 2026-06-20 (Sprint « sémiologie foliaire »). Promeut et
> absorbe la dette **D33**. Première brique posée au tronçon ⑨ du Sprint
> physico-chimie (`chlorose: bool` dans le snapshot). Arbitrages Nico du
> 2026-06-20 : **cumul multi-signes**, **tri par intensité + priorité fixe**,
> **périmètre complet** (chroniques recalculés + événementiels mémorisés).

## 0. Objectif & intuition

Une plante qui souffre **le montre** sur son feuillage, et chaque cause a un
**signe distinct** : ce n'est pas une jauge de santé unique, c'est un
**vocabulaire**. Voir le signe → formuler une hypothèse → consulter → trouver la
cause (philo #6 : observer avant de lire un chiffre ; philo #5 : indices
biologiques visuels en HUD primaire).

Aujourd'hui le rendu ne module la couleur du feuillage que **par saison**
(`tools/render_structure.py:_draw_organs`) et, depuis le ⑨, par un **flag binaire
de chlorose** poussé par le moteur. On généralise : un **ensemble de symptômes**
par plante, chacun **miroir fidèle de la mécanique qui blesse**.

Philosophie tenue : **#2** (le symptôme est une LECTURE d'un flux/contrainte, pas
un malus direct) ; **#3** déterministe ; **#5** lisible sans chiffre ; **#6** un
signe → une hypothèse.

## 1. État de départ

| Brique | Où | Statut |
|---|---|---|
| `chlorose: bool` dans le snapshot | `tools/simserver/serialize.py:117` | OK — à fondre dans `leaf_symptoms` |
| `SetChlorose` / `Chlorotic()` (teinte jaune) | `visuals/PlantRenderer.cs:117-129` | OK — à généraliser, retirer le bool |
| Seuils chlorose `SEUIL_ACIDOPHILE 5.5`, `CHLOROSE_PH 7.6`, `CHLOROSE_MALUS 0.5` | `fields/ecofields/constants.py:305` | OK — réutilisés tels quels |
| `qi_local` (prédicat chlorose source de vérité) | `sim/vigueur_plante.py:82` | OK — le détecteur le miroir |
| `herbivory_pressure` (densité locale `ravageur+chenille`) | `sim/effects/perturbations.py:190` | OK — le détecteur ravageurs le miroir |
| Seuils humidité (`HUM_EXCES`, asphyxie) | hydrologie / `plant_uptake` | OK — sécheresse & asphyxie s'y branchent |
| `ReduceHealth(plant, amount, reason="…")` | `sim/effects/mutations.py:30` | `reason` = chaîne de **log**, jamais stockée → verrou |
| Résolution `ReduceHealth` (applique puis jette) | `sim/effects/resolution.py:232` | à compléter : incrémenter une marque |
| Aléas santé : « Gelée tardive », « Grêle », « maladie fongique » | `aleas.py:31/53`, `perturbations.py:139` | sources des symptômes ÉVÉNEMENTIELS |

## 2. Le modèle

### 2.1 Deux régimes de symptômes

- **Chroniques (recalcul pur, golden NEUTRE)** — état persistant lisible à
  l'instant du snapshot. Détecteurs purs dans `sim/semiologie.py`, appelés depuis
  `_snapshot`, **zéro écriture moteur** (comme le ⑨) :
  - `chlorose` — pH local sous l'empreinte racinaire (miroir `qi_local`)
  - `secheresse` — humidité basse / `drought_memory` (couvre aussi la canicule,
    qui n'est qu'une chute d'humidité)
  - `asphyxie` — excès d'eau / `asphyxie_memory` (au-delà de `HUM_EXCES`)
  - `ravageurs` — densité locale `ravageur + chenille` (miroir `herbivory_pressure`)
  - `senescence` — âge relatif à la longévité + déclin de santé (courbe D27)

- **Événementiels (mémorisés, décroissants)** — pas d'état persistant à relire :
  un coup ponctuel qui doit **laisser une marque qui s'estompe**. Exige
  d'écrire sur la plante → **re-figeage golden maîtrisé probable** (voir §5).
  - `maladie` — « maladie fongique » (`perturbations.py:139`)
  - `gel` — « Gelée tardive » (`aleas.py`)
  - `grele` — « Grêle » feuillage déchiré (`aleas.py`)

  > NB exclus : « fonte des semis » met `health=0` le tick même (la plante
  > devient squelette, pas de feuillage à symptomatiser) ; « mortalité de fond »
  > est une attrition abstraite (bruit), sans signe visuel ; « stress hydrique
  > sévère » et « herbivorie » sont déjà couverts par les détecteurs CHRONIQUES
  > correspondants — on ne mémorise pas en double.

### 2.2 Le champ snapshot `leaf_symptoms`

Remplace le bool `chlorose`. Liste de symptômes, **triée par intensité
décroissante** :

```json
"leaf_symptoms": [
  {"cause": "chlorose",  "intensity": 0.7},
  {"cause": "ravageurs", "intensity": 0.3}
]
```

- `cause` ∈ vocabulaire ci-dessus (chaîne, **extensible** : la vue garde un
  fallback « cause inconnue → pas de teinte », forward-compatible).
- `intensity` ∈ [0,1].
- Liste **vide** = plante saine (pas de `cause: "sain"` factice).
- **Cumul multi-signes** assumé (choix Nico) : plusieurs entrées coexistent.

### 2.3 Tri & priorité fixe (départage à intensité égale)

Clé de tri = `(intensity desc, priorité fixe)`. Ordre de priorité proposé, du
plus aigu/diagnostique au plus lent (knob, ajustable au calibrage) :

```
asphyxie > secheresse > maladie > ravageurs > gel > grele > chlorose > senescence
```

### 2.4 Intensité = rampe sur le SEUIL MÊME de la mécanique

Principe DRY central : chaque détecteur réutilise le seuil de la mécanique qui
agit, pour que **le signe ne puisse jamais mentir** par rapport à la simulation.
Détail des rampes laissé au tronçon (knobs de calibrage), forme générale :
`intensity = clamp01((mesure − seuil_apparition) / (seuil_plein − seuil_apparition))`.
Ex. chlorose : 0 à `CHLOROSE_PH`, 1 quelque part au-dessus ; ravageurs : rampe sur
`herbivory_pressure` ; sécheresse/asphyxie : rampe sur l'écart d'humidité.

### 2.5 Marques événementielles (option A — mémorisation décroissante)

- `ReduceHealth` gagne un champ **`cause: str`** typé (enum canonique) à côté du
  `reason` humain de log. Sites annotés : `perturbations.py`, `aleas.py:112`.
- `PlantInstance` gagne `symptom_marks: dict[str, float]`.
- À la résolution d'un `ReduceHealth` à cause événementielle :
  `marks[cause] = min(1.0, marks[cause] + amount * GAIN)` (knob `GAIN ≈ 0.5`).
- À chaque tick de la plante : `marks[c] *= DECAY` (knob `DECAY ≈ 0.8`), purge
  sous epsilon → une plante soignée retrouve son aspect en ~3-4 semaines.
- `_snapshot` fusionne les marques (événementiels) avec les détecteurs purs
  (chroniques), trie, expose `leaf_symptoms`.

## 3. Rendu (canaux séparés pour un cumul lisible)

Le cumul ne devient boueux que si on superpose des teintes. On sépare donc :

- **Canal couleur** = le symptôme COLORANT dominant (plus forte intensité parmi
  `chlorose` jaune inter-nervaire / `asphyxie` brun terne / `secheresse`
  désaturé-flétri / `senescence` jaune-rouge de fin de vie / `maladie` taches).
  Pose la teinte de base de la feuille (généralise `Chlorotic()`).
- **Canaux texture / forme** = ADDITIFS, non conflictuels avec la couleur :
  `ravageurs` = feuilles criblées/trouées ; `grele` = limbe déchiré ; `gel` =
  bords noircis/brûlés ; `secheresse` = géométrie tombante.

Une plante chlorosée **et** criblée se lit donc : jaune **+** trouée. Les canaux
ne se marchent pas dessus.

## 4. Synthèse biologique (à étudier — Nico)

Repère naturaliste sur ce que chaque signe traduit, pour caler les couleurs/formes :

- **Chlorose ferrique** (sol trop alcalin pour une acidophile) : le limbe jaunit
  **entre les nervures**, qui restent vertes — jaunissement *inter-nervaire*,
  signature distincte du jaunissement uniforme.
- **Carence azotée** (hors périmètre v1, extensible) : jaunissement **uniforme**
  partant des **vieilles** feuilles (azote mobile, la plante le rapatrie vers les
  jeunes pousses).
- **Stress hydrique / sécheresse** : turgescence perdue → feuilles **flétries,
  tombantes**, puis bords desséchés bruns. Couleur globale **désaturée**.
- **Asphyxie racinaire** (engorgement) : racines en anoxie → feuillage **terne,
  brunâtre**, jaunissement mou, sans le contraste net de la chlorose.
- **Herbivorie / ravageurs** : signe de **forme**, pas de couleur — limbe
  **criblé, troué, mordu** sur les bords.
- **Maladies cryptogamiques** (mildiou/oïdium/rouille) : **taches** localisées
  (brunes, blanches farineuses, pustules orangées selon le pathogène).
- **Gel tardif** : tissus éclatés par le givre → **bords noircis**, aspect brûlé.
- **Grêle** : déchirures mécaniques du limbe.
- **Sénescence** : jaunissement-rougissement de **fin de vie** (à distinguer du
  rougeoiement saisonnier d'automne, déjà géré par la couleur saisonnière).

## 5. Impact golden — à plat

- **Détecteurs chroniques (①) : golden NEUTRE.** Lecture pure dans `_snapshot`,
  aucune écriture moteur — même propriété que le ⑨.
- **Marques événementielles (②) : re-figeage maîtrisé PROBABLE.** Ajout d'un champ
  `symptom_marks` sur `PlantInstance` + un pas de décroissance par tick = écriture
  moteur. À vérifier à l'impl : si le scénario smoke 2 tuiles × 4 ans ne déclenche
  aucun gel/grêle/maladie, les marques restent vides et le hash **peut** rester
  neutre ; sinon, dérive **localisée, expliquée et annoncée** (règle de design #3,
  garde-fou golden CLAUDE.md).

## 6. Tronçonnage (gros sprint → 3 sous-sprints autosuffisants)

| # | Contenu | Golden | Pont |
|---|---|---|---|
| ① | `sim/semiologie.py` (détecteurs CHRONIQUES purs) + champ snapshot `leaf_symptoms` (liste triée) ; portage du bool `chlorose` du ⑨ dedans + sécheresse/asphyxie/ravageurs/sénescence. Retrait du bool `chlorose` du pont. | **NEUTRE** | bump `0.5.1` |
| ② | `cause` typé sur `ReduceHealth` + sites annotés ; `symptom_marks` + décroissance sur `PlantInstance` ; remontée maladie/gel/grêle, fusion dans `_snapshot`. | **re-figeage maîtrisé annoncé** | (contenu, pas schéma) |
| ③ | Vue C# : `PlantRenderer` canal couleur (généralise `Chlorotic`) + canaux texture/forme ; retrait `SetChlorose`. F5 Nico. | — | consommation |

Boucle (CLAUDE.md) : lancer `0N` → travailler → vérifier golden → MAJ `00_etat.md`
→ commit → `/clear` → `0N+1`.

## 7. Dette / liens

- Absorbe **D33** (clôturer dans `DETTE.md` en fin de sprint).
- Recoupe **D27** (sénescence/maladies, courbe d'âge), **D31** (ravageurs
  visibles), **D22b** (susceptibilité familiale), physico-chimie ⑨ (brique
  chlorose), NPK (carence azotée = extension future naturelle du vocabulaire).
- Extensible : `carence_n`, `carence_k`, `etiolement` (ombre) s'ajouteront comme
  nouvelles `cause` sans toucher le schéma.
