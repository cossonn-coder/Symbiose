# Sprint éclairement — ombres portées pixel-exact (Option A) et pérennes
# ligneuses

**Statut** : à faire — conception close, recadrée le 2026-05-29
**Prérequis** : Sprint conception éclairement & reproduction terminé
(voir entrée datée dans `journal.md`)
**Estimation** : 1 sprint code conséquent. Peut absorber tout ou partie du
Sprint 3 (portage `effects.py`/`engine.py`) puisqu'on touche au tick hebdo.
**Objectif** : poser l'éclairement spatial **Option A** (canopée + lumière
au pixel-sol, chimie du sol au plot) avec ombres portées astronomiques, et
l'architecture temporelle polymorphe des pérennes ligneuses.

> **La génétique (D17 + D22) est sortie de ce sprint** — elle constitue le
> Sprint génétique/reproduction (`sprints/sprint_genetique.md`). Ici,
> `genetic_factor` est **neutre (1.0)**.

---

## Avant de commencer

Tu démarres dans une session vide. Pour comprendre où on en est :

1. **`CLAUDE.md`** est déjà chargé. Lis-le complètement (surtout « Échelle
   spatiale actée » et le système D20-D21).
2. **`journal.md`** — lis l'entrée `2026-05-29 — Sprint conception
   éclairement & reproduction (recadrage Z7)`. Elle contient toutes les
   décisions d'architecture de ce sprint.
3. **Code à lire avant** :
   - `data/code/fields.py` — `GridField`, `LightField` (v3, à remplacer),
     `EcoFields`. C'est la source de vérité.
   - `core/GridField.cs` — déjà en **v4** (OM tri-compartiment, rain
     feedback, `PathogenPressure`). **Le Python est en retard ici.**
   - `core/PlantData.cs` — `GrowthStage.Strate` (qualitatif) sera remplacé
     par des données métriques (hauteur + rayon par stade).
   - `core/TileData.cs` — `Tile` (6×8 plots), `HexToScreen` (96×48 obsolète).

---

## Décisions d'architecture (rappel condensé)

### Option A — maillage adaptatif
- **Canopée + lumière au pixel** ; **chimie du sol au plot**.
- **Un seul pont** pixel↔plot : la photosynthèse lit la lumière-pixel sous
  l'empreinte de canopée → module la croissance. Le souterrain reste en
  monde-plot, inchangé.
- Espace lumière = **top-down cartésien** (en cm), jamais iso écran.

### Échelle
- **1 plot = 50×50 cm** ; monde 3×3 tuiles × (6×8) = 432 plots = 12×9 m.
- Résolution lumière = **2 cm/px-sol** (~270 k px monde, ~5,4 MB).
- Position des plantes **continue** (`x_cm, y_cm`) ; plot-foyer =
  `floor(pos / 50 cm)`.
- Orientation par défaut : Nord en haut, soleil au Sud (à confirmer).

### Modèle d'ombre (D20)
- Soleil par **calcul astronomique** (latitude ~49°N), déterministe, 4
  tranches (matin/midi/soir/nuit) × saisons.
- `longueur_ombre = hauteur / tan(élévation)`, direction opposée à l'azimut.
- Ombre = **capsule** (disque de canopée glissé), rasterisée en pixels-sol.
- Opacité **par espèce** → `foliage_density`. Cumul **multiplicatif**.
- **Plancher de lumière diffuse ~15 %** (rien ne descend à 0).
- **Intégrale journalière** = moyenne des 3 tranches éclairées pondérée par
  l'intensité solaire → pilote la photosynthèse.

### Empreintes & croissance
- Canopée = disque de **rayon tabulé par stade**.
- Racines = **rayon racinaire continu** (cm → plots exploités pour l'uptake).
  Remplace `RootOffsets`.
- `current_height = canopy_height_potential × genetic_factor(=1.0) ×
  growth_factor`. Boucle de feedback lumière→croissance→ombre.

### Pérennes ligneuses (D21)
- **Base commune polymorphe** : annuelles et arbres exposent la même
  interface (`current_height`, `canopy_radius`, `foliage_density`,
  `root_radius`). Seule la logique de croissance diffère.
- `age_years` (+1/52 par tick) ; courbe âge→(hauteur, rayon) =
  **interpolation des points tabulés**.
- `foliage_density` **saisonnière** (caduc nu l'hiver = pas d'ombre).
- Arbres : figuier + pommier = jardin, cerisier intermédiaire, **noyer +
  chêne = sujets de lisière**.

---

## Audit botanique — 14 espèces actuelles

Hauteurs **potentielles** (cm) par stade — à compléter par un **rayon de
canopée** par stade et une **`foliage_density`** par espèce (à calibrer) :

| Espèce | Famille | Type | Semis | Jeune | Adulte | Mature |
|---|---|---|---|---|---|---|
| Tomate | Solanaceae | annuel tuteurée | 5 | 30 | 100 | 150 |
| Basilic | Lamiaceae | annuel bas | 3 | — | 25 | 40 |
| Haricot | Fabaceae | annuel grimpant | 5 | 30 | 150 | 200 |
| Trèfle | Fabaceae | couvre-sol vivace | 2 | — | 15 | — |
| Tournesol | Asteraceae | annuel haut | 5 | 50 | 180 | 250 |
| Poivron | Solanaceae | annuel moyen | 5 | — | 60 | 80 |
| Bourse-à-pasteur | Brassicaceae | adventice annuel | 3 | — | 25 | 40 |
| Minette | Fabaceae | vivace rampante | 3 | — | 30 | — |
| Pâturin | Poaceae | graminée vivace | 3 | — | 30 | — |
| Pissenlit | Asteraceae | rosette + hampe | 3 | 8 | 30 | — |
| Ortie | Urticaceae | vivace haute | 5 | — | 120 | — |
| Prêle | Equisetaceae | vivace moyenne | 5 | — | 60 | — |
| Plantain | Plantaginaceae | rosette plaquée | 3 | — | 15 | — |
| Molène | Scrophulariaceae | bisannuelle haute | 5 | — | 200 | — |

> Attention rosettes (pissenlit, plantain) : basses **et** larges → rayon de
> canopée **non** proportionnel à la hauteur. C'est pourquoi le rayon est
> tabulé par stade, pas dérivé d'un ratio.

## Arbres pérennes — 5 espèces premières (D21)

Courbe hauteur (cm) par âge — à compléter par rayon de couronne et
`foliage_density` (caduc) :

| Arbre | 5 ans | 10 ans | 20 ans | 50 ans | Centenaire | Statut |
|---|---|---|---|---|---|---|
| Figuier | 200 | 400 | 500 | — | — | jardin |
| Pommier | 200 | 350 | 500 | 700 | — | jardin |
| Cerisier | 250 | 500 | 700 | 900 | 1000 | intermédiaire |
| Noyer | 300 | 600 | 1000 | 1500 | 2500 | lisière |
| Chêne | 200 | 400 | 700 | 1500 | 3000 | lisière |

## Hauteurs des structures fixes
Mare 0 · brise-vent (haie) 150 · pergola 250 · maison normande 700 (cm).

---

## Sous-objectifs

### 0. Réalignement OM Python → v4 (préalable, D10)
Porter vers `fields.py` l'OM tri-compartiment (`om_fresh/active/stable`),
le rain-feedback végétal et le `PathogenPressure` déjà présents en C#.
**Sans ça, le test de parité est impossible.**

### 1. `data/code/fields.py` — `LightField` v2 pixel-sol
- Grille pixel-sol top-down (array numpy 2D), 2 cm/px, couvrant la tuile.
- 4 tranches + intégrale par pixel.
- Soleil astronomique : `solar_angle(saison, tranche)` → (azimut, élévation).
- `recompute(plants, structures, season)` : reset, projeter chaque
  ombre-capsule (cumul multiplicatif, plancher 15 %), calculer l'intégrale.
- `daily_integral_under(footprint)` : moyenne de l'intégrale sous une
  empreinte de canopée → photosynthèse.

### 2. `data/code/models.py` — empreintes et hauteurs
- `canopy_height[stade]` et `canopy_radius[stade]` sur `PlantData`.
- `foliage_density` (base) sur `PlantData`.
- Position continue + `current_height` (propriété calculée) sur
  `PlantInstance` ; `root_radius` → plots exploités.

### 3. `data/code/perennials.py` — pérennes ligneuses
- Interface commune (mixin/base) avec les annuelles pour la lumière.
- `PerennialWoodyData` + instance : `age_years`, courbes interpolées,
  `foliage_density` saisonnière.
- Intégration au `tick_week` de `engine.py`.

### 4. Portage C#
- `core/LightField.cs` (extraire de `GridField.cs` + réécrire pixel-sol).
- `core/PlantData.cs` : hauteurs + rayons + `foliage_density`.
- `core/PerennialWoody.cs` + interface commune.

### 5. Audit catalogue
- `PlantCatalogue.cs` : renseigner hauteurs + rayons + densités (14 espèces).
- `PerennialCatalogue.cs` : 5 arbres premiers.

### 6. Tests parité Python ↔ C#
- 1 saison simulée avec ombres + photosynthèse modulée par l'intégrale.
- Mêmes seeds, états finaux identiques (OM réaligné au préalable).

---

## À produire à la fin de la session

- [ ] OM réaligné Python→v4 (D10)
- [ ] `fields.py` : `LightField` v2 pixel-sol top-down
- [ ] `models.py` : empreintes (hauteurs + rayons par stade), position continue
- [ ] `perennials.py` : arbres pérennes polymorphes
- [ ] `core/LightField.cs` extrait + réécrit
- [ ] `core/PlantData.cs` + `core/PerennialWoody.cs`
- [ ] `PlantCatalogue.cs` audité + `PerennialCatalogue.cs`
- [ ] Test parité Python ↔ C# sur 1 saison
- [ ] `journal.md` : entrée datée de calibration
- [ ] `CLAUDE.md` : architecture courante mise à jour
- [ ] Memory : `project_status.md`, `project_python_source.md`
- [ ] Commit avec message HEREDOC

---

## Critère de fin

Le `LightField` pixel-sol calcule correctement les ombres-capsules
astronomiques à chaque tick hebdo, la photosynthèse utilise l'intégrale
journalière sous l'empreinte de canopée, les annuelles et les 5 arbres
pérennes partagent l'interface lumière (croissance par stade vs par âge),
toute plante a hauteur + rayon + `foliage_density` calibrés, `genetic_factor`
neutre 1.0, parité Python ↔ C# vérifiée sur 1 saison après réalignement OM.
