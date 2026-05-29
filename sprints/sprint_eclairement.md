# Sprint éclairement — ombres portées pixel-exact et architecture des
# pérennes ligneuses

**Statut** : à faire
**Prérequis** : Sprint conception bis terminé (commit `3e9ec34`)
**Estimation** : 1 session dense de conception complétée par un sprint
code conséquent (probablement à fusionner partiellement avec
Sprint 3 portage simulation pour éviter la duplication).
**Objectif** : poser le système d'éclairement spatial pixel-exact avec
ombres portées par canopée et structures, l'architecture temporelle
des pérennes ligneuses (arbres), et l'héritage génétique de la graine.

---

## Avant de commencer

Tu démarres dans une session vide. Pour comprendre où on en est :

1. **`CLAUDE.md`** est déjà chargé. Lis-le complètement.
2. **`journal.md`** — lis surtout les trois entrées du 2026-05-29 :
   - Sprint 0 (gel infrastructure)
   - Sprint conception (12 décisions structurantes)
   - Sprint conception bis (6 zones blanches + Z7 éclairement)
3. **Memory** — `project_game_vision.md` a une section dédiée à
   l'éclairement (Z7).
4. **Code à lire avant** :
   - `core/PlantData.cs` — la classe `GrowthStage` et son champ
     `Strate` (qualitatif "sol/basse/moyenne/haute") sera **numérisé**
     par ce sprint
   - `core/GridField.cs` — le `LightField` C# actuel (probablement
     basique) sera enrichi
   - `data/code/fields.py` — le `LightField` Python actuel à étendre
     pour devenir pixel-exact

---

## Zone Z7 — Pourquoi ce sprint

Le Sprint conception bis a fermé 6 zones blanches. Une **7e zone**
majeure est apparue immédiatement après : la micro-géographie des
ombres est constitutive du gameplay permaculture (planifier une salade
sous un fruitier, un brise-vent à l'ouest, exploiter une ombre
matinale…). Le `LightField` existant est trop pauvre — il n'a pas la
notion d'ombres portées par les canopées.

**Quatre sous-objectifs interconnectés** :
- **D20** : système d'éclairement spatial pixel-exact (ombres portées
  par canopées + structures, 4 tranches journalières + intégrale)
- **D21** : système temporel des pérennes ligneuses (âge en années,
  courbe pluri-décennale, distinct du `GrowthStage` actuel des annuelles)
- **D22** : héritage génétique de la graine (variabilité phénotypique
  intra-espèce — hauteur, vigueur, résistance — facteur génétique
  hérité)
- **Audit botanique** : calibrer les 14 espèces actuelles + 5 arbres
  pérennes premiers (figuier, pommier, cerisier, noyer, chêne)

**D23** (catalogue arbres étendu : poirier, prunier, châtaignier, frêne,
tilleul, bouleau, saule, aulne, peuplier, érable…) est différée
post-validation du squelette de base.

---

## Décisions actées (Z7)

### Granularité spatiale — pixel exact

- Stockage : 1 valeur par pixel × 4 tranches + 1 intégrale = **5 floats
  par pixel**
- Tuile 78×57 = 4 446 pixels → **20 KB par tuile**
- Démarrage 9 tuiles ≈ **800 KB** — négligeable
- Long terme ~50 tuiles ≈ **4,4 MB** — toujours négligeable
- Implémentation : array numpy 2D côté Python, `float[,]` côté C#

### Granularité temporelle — 4 tranches + intégrale

- Tranches : **matin / midi / soir / nuit**
- Angle solaire par tranche déterminé par la saison (variations
  saisonnières au début, déterministe par seed)
- **Intégrale journalière** cumulée d'ensoleillement (somme pondérée
  des 4 tranches) = c'est cette intégrale qui pilote la photosynthèse
  des plantes
- **Recalcul hebdomadaire** (à chaque tick simulation) — < 1 ms par
  recalcul complet, imperceptible

### Hauteur des canopées et structures

- Stockée en **centimètres** (range 0 à 3000+ pour les chênes
  centenaires)
- `PlantData.canopy_height_potential` = ordre de grandeur par stade
  (annuelles) ou par courbe d'âge (pérennes ligneuses)
- `PlantInstance.current_height` = `canopy_height_potential` ×
  `genetic_factor` × `growth_factor`
  - `genetic_factor` ∈ [0.7, 1.3] — hérité de la graine (D22)
  - `growth_factor` ∈ [0.4, 1.2] — modulé par Vigueur / eau /
    nutriments / lumière reçue (boucle de feedback : la lumière reçue
    affecte la hauteur, qui affecte les ombres portées sur les voisins)
- `current_height` recalculée à chaque tick hebdomadaire avant le
  calcul des ombres
- Hauteurs des structures fixes :
  - Mare : 0 cm
  - Brise-vent (haie taillée) : 150 cm
  - Pergola : 250 cm
  - Maison normande : 700 cm

### Algorithme de calcul des ombres

- Pour chaque ombrageur (plante avec `current_height > 0` + structure),
  projeter l'ombre selon l'angle solaire de chaque tranche
- Ombre = polygone trapézoïdal au sol, marqué dans le `LightField`
- Pixel à l'ombre = facteur multiplicatif (ex: 0.3 = 30 % de lumière)
- Combinaison : plusieurs ombres se cumulent multiplicativement
- Intégrale journalière = moyenne pondérée des 4 tranches
- Complexité : O(ombrageurs × pixels_par_ombre) — typiquement
  ~160 000 ops par recalcul complet

---

## Audit botanique — 14 espèces actuelles

Hauteurs **potentielles** (cm) à intégrer dans `PlantData` :

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
| Pissenlit | Asteraceae | rosette + hampe | 3 | 8 (rosette) | 30 (hampe) | — |
| Ortie | Urticaceae | vivace haute | 5 | — | 120 | — |
| Prêle | Equisetaceae | vivace moyenne | 5 | — | 60 | — |
| Plantain | Plantaginaceae | rosette plaquée | 3 | — | 15 | — |
| Molène | Scrophulariaceae | bisannuelle haute | 5 | — | 200 | — |

**Important** : ces hauteurs sont des **potentiels**, modulés en
pratique par `genetic_factor` × `growth_factor`. La variabilité est
fonctionnelle (deux haricots côte à côte ne feront pas la même taille).

---

## Arbres pérennes — 5 espèces premières (D21)

Courbe de croissance par âge en années :

| Arbre | 5 ans | 10 ans | 20 ans | 50 ans | Centenaire |
|---|---|---|---|---|---|
| Figuier | 200 | 400 | 500 | — | — |
| Pommier | 200 | 350 | 500 | 700 | — |
| Cerisier | 250 | 500 | 700 | 900 | 1000 |
| Noyer | 300 | 600 | 1000 | 1500 | 2500 |
| Chêne | 200 | 400 | 700 | 1500 | 3000 |

**Modèle technique pressenti** :
- Nouvelle classe `PerennialWoodyData` distincte de `PlantData`
- Champ `age_years` (float, progresse de 1/52 par tick hebdo simulation)
- Courbe `height_at_age(age)` paramétrée par espèce (fonction
  logarithmique ou logistique calée sur la table ci-dessus)
- `WinterStrategy = "dormant"` mais avec cycle annuel sur dizaines
  d'années
- Pas de `GrowthStage` discret — courbe continue d'âge

---

## Héritage génétique de la graine (D22)

**Modèle pressenti** :
- `Seed` (existante dans `SeedBank`) gagne un champ `genetic_factor`
  ∈ [0.7, 1.3], distribution gaussienne centrée 1.0 σ=0.1
- `genetic_factor` hérité à la fécondation : moyenne pondérée des
  parents + mutation aléatoire
- Affecte d'abord la hauteur, puis le principe se généralise à
  d'autres caractères (vigueur max, résistance pathogène, tolérance
  sécheresse…) — backlog progressif
- Conséquence design : un joueur qui sélectionne ses graines (récolte
  des plantes les plus hautes) favorise une lignée plus haute. Sélection
  artificielle émergente.

---

## Sous-objectifs détaillés

### 1. Étendre `data/code/fields.py` — `LightField` v2
- Remplacer le LightField actuel par une grille pixel-exacte
- 4 tranches + intégrale stockées par pixel
- Méthode `recompute(plants, structures, season)` appelée à chaque tick
- Méthode `daily_integral_at(x, y)` utilisée par la photosynthèse

### 2. Étendre `data/code/models.py` — héritage et hauteurs
- Ajouter `canopy_height_potential` dict (par stade) sur `PlantData`
- Ajouter `genetic_factor` sur `Seed`
- Ajouter `current_height` (propriété calculée) sur `PlantInstance`

### 3. Créer `data/code/perennials.py` — pérennes ligneuses
- Nouvelle classe `PerennialWoodyData` + `PerennialWoodyInstance`
- Courbes d'âge → hauteur pour les 5 arbres premiers
- Intégration au `tick_week` de `engine.py`

### 4. Porter en C#
- `core/LightField.cs` (extraction du composant du `GridField.cs`
  actuel + enrichissement)
- `core/PlantData.cs` : ajouter `CanopyHeightPotential`
- `core/Seed.cs` : ajouter `GeneticFactor`
- `core/PerennialWoody.cs` : nouveau

### 5. Audit catalogue
- `PlantCatalogue.cs` : renseigner les 14 hauteurs (table ci-dessus)
- Créer `PerennialCatalogue.cs` pour les 5 arbres premiers

### 6. Tests parité Python ↔ C#
- 1 saison simulée avec ombres + photosynthèse modulée
- Mêmes seeds, états finaux identiques

---

## À produire à la fin de la session

- [ ] `data/code/fields.py` enrichi (`LightField` v2 pixel-exact)
- [ ] `data/code/models.py` enrichi (hauteurs, héritage graine)
- [ ] `data/code/perennials.py` nouveau (arbres pérennes)
- [ ] `core/LightField.cs` extrait et enrichi
- [ ] `core/PlantData.cs` + `core/Seed.cs` + `core/PerennialWoody.cs`
- [ ] `core/PlantCatalogue.cs` audité avec hauteurs
- [ ] `core/PerennialCatalogue.cs` nouveau
- [ ] Test parité Python ↔ C# sur 1 saison
- [ ] **`journal.md`** : entrée datée `## YYYY-MM-DD — Sprint éclairement`
  consignant les décisions de calibration
- [ ] **`CLAUDE.md`** : mise à jour de l'architecture courante
- [ ] **Memory** : `project_status.md` (dettes résolues), enrichir
  `project_python_source.md` avec le `LightField` v2
- [ ] **Commit** avec message HEREDOC

---

## Critère de fin

Toute plante du catalogue a un `canopy_height_potential` calibré, le
`LightField` pixel-exact calcule correctement les ombres à chaque tick
hebdomadaire, la photosynthèse utilise l'intégrale journalière
d'ensoleillement, les 5 arbres pérennes premiers vieillissent et
grandissent selon leur courbe d'âge, les graines portent leur
`genetic_factor`, parité Python ↔ C# vérifiée sur 1 saison.

**Note d'ordre** : ce sprint peut absorber tout ou partie du
**Sprint 3 (portage simulation)** parce que toucher au `LightField` et
ajouter une nouvelle classe `PerennialWoody` impose de toucher au tick
hebdomadaire — autant porter `effects.py` et `engine.py` dans la
foulée. À décider en début de session selon l'énergie disponible.
