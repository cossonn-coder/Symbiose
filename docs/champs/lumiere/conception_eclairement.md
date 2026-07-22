# Éclairement spatial pixel-exact (zone Z7) — CONCEPTION CLOSE ✅

> **Extraction du tronçon ④** (sprint de rangement documentaire, 2026-07-22).
> Ce thème n'avait pas de document dédié : il vivait **enchâssé** dans
> [`docs/meta/vision.md`](../../meta/vision.md) (section « Z7 ») et dans les
> archives de backlog ([`docs/meta/backlog_historique.md`](../../meta/backlog_historique.md)).
> Contenu repris **verbatim**, statut inchangé. Les deux emplacements d'origine
> portent un pointeur vers ici (règle « zéro perte »).
>
> Voisin de thème : [`conception_maison_ombre.md`](conception_maison_ombre.md)
> (2026-06-07), qui prolonge ce modèle d'ombre avec la maison et les chemins.

## 1. Conception (repris de `docs/meta/vision.md`)

Zone blanche résolue le 2026-05-29 après le Sprint conception bis. Découpée en **deux sprints d'implémentation** : éclairement (D20-D21) puis génétique/reproduction (D17+D22).

### Architecture lumière = Option A (maillage adaptatif)

- **Canopée + lumière au pixel-sol** (top-down cartésien, **2 cm/px**) — structure fine = gameplay des ombres.
- **Chimie du sol au plot** (50 cm) — phénomène diffus, le pixel n'apporte rien.
- **Position des plantes continue** (pixel-sol `x_cm, y_cm`), plot-foyer = `floor(pos / 50 cm)`.
- Espace de simulation lumière = **top-down cartésien**, jamais l'espace iso d'affichage.

### Modèle d'ombre

- **Soleil astronomique** : azimut/élévation calculés par latitude ~49°N (Montmartin-sur-Mer), déterministe. **4 tranches** (matin/midi/soir/nuit) + intégrale journalière. L'intégrale pilote la photosynthèse.
- `longueur_ombre = hauteur / tan(élévation)`, direction opposée à l'azimut. Ombre = **capsule** (disque de canopée glissé sur la longueur d'ombre), rasterisée en pixels-sol.
- **Opacité d'ombre variable par espèce** → champ `foliage_density` (noyer dense ~0.8, bouleau léger ~0.4). Mécanique permaculture : choisir un arbre à ombre légère pour un sous-étage.
- Cumul **multiplicatif** des ombres + **plancher de lumière diffuse ~15 %** (rien ne descend à 0 → sous-bois viable).

### Pérennes ligneuses (D21)

- **Base commune polymorphe** avec les annuelles : `current_height`, `canopy_radius`, `foliage_density`, `root_radius`. Le LightField/photosynthèse les traitent uniformément. Seule la **logique de croissance** diffère (stades discrets vs courbe d'âge).
- `age_years` (+1/52 par tick) ; courbe âge → (hauteur, rayon) = **interpolation spline monotone** entre points tabulés.
- `foliage_density` **saisonnière** — caduc nu l'hiver (levier permaculture majeur : soleil d'hiver sous fruitier caduc, ombre d'été).
- **Arbres requalifiés** : figuier/pommier = jardin, cerisier intermédiaire, **noyer/chêne = sujets de lisière** (un chêne mûr fait la taille du jardin entier).

### Génétique & reproduction (D17 + D22)

- **Deux banques distinctes** : **SeedBank-sol** (génétique vectorielle par espèce, liée au terrain, brassage féral) + **SeedBank-joueur** (lots par espèce, transportable, suit l'avatar lors du déménagement).
- `genetic_factor` devient un **vecteur de gènes extensible** (`{hauteur, vigueur, résistance, sécheresse…}`), seul `hauteur` rempli pour l'instant.
- **Héritage biparental** : père compatible à portée de pollinisation ; `gène_enfant = moyenne(parents) + mutation gaussienne` ; sinon autofécondation. **Pollinisation par espèce** (anémogame/entomogame), rayon modulé par les **pollinisateurs auxiliaires** (favoriser les auxiliaires → meilleures graines).
- **Hybridation inter-espèces** par **introgression sur espèce fixe** — l'enfant garde l'espèce de la mère, les gènes du père décalent ses facteurs vectoriels (parfois hors [0.7, 1.3] = vigueur hybride). **Pas** de génération de nouvelles `PlantData`.

### Hauteurs structures actées

- Mare : 0 cm
- Brise-vent (haie taillée) : 150 cm
- Pergola : 250 cm
- Maison normande : 700 cm

### 5 arbres pérennes premiers calibrés (D21)

| Arbre | 5 ans | 10 ans | 20 ans | 50 ans | Centenaire |
|---|---|---|---|---|---|
| Figuier | 200 | 400 | 500 | — | — |
| Pommier | 200 | 350 | 500 | 700 | — |
| Cerisier | 250 | 500 | 700 | 900 | 1000 |
| Noyer | 300 | 600 | 1000 | 1500 | 2500 |
| Chêne | 200 | 400 | 700 | 1500 | 3000 |

Catalogue arbres étendu (poirier, prunier, châtaignier, frêne, tilleul, bouleau, saule, aulne, peuplier, érable…) = dette **D23**, différée post-validation squelette.

### 14 espèces actuelles — hauteurs potentielles (cm)

| Espèce | Famille | Type | Semis | Jeune | Adulte | Mature |
|---|---|---|---|---|---|---|
| Tomate | Solanaceae | annuel tuteurée | 5 | 30 | 100 | 150 |
| Basilic | Lamiaceae | annuel bas | 3 | — | 25 | 40 |
| Haricot | Fabaceae | annuel grimpant | 5 | 30 | 150 | 200 |
| Trèfle | Fabaceae | couvre-sol | 2 | — | 15 | — |
| Tournesol | Asteraceae | annuel haut | 5 | 50 | 180 | 250 |
| Poivron | Solanaceae | annuel moyen | 5 | — | 60 | 80 |
| Bourse-à-pasteur | Brassicaceae | adventice | 3 | — | 25 | 40 |
| Minette | Fabaceae | vivace rampante | 3 | — | 30 | — |
| Pâturin | Poaceae | graminée vivace | 3 | — | 30 | — |
| Pissenlit | Asteraceae | rosette + hampe | 3 | 8 | 30 | — |
| Ortie | Urticaceae | vivace haute | 5 | — | 120 | — |
| Prêle | Equisetaceae | vivace moyenne | 5 | — | 60 | — |
| Plantain | Plantaginaceae | rosette plaquée | 3 | — | 15 | — |
| Molène | Scrophulariaceae | bisannuelle haute | 5 | — | 200 | — |

**Hauteurs = potentiels**, modulés par `genetic_factor × growth_factor`. Deux haricots côte à côte n'ont jamais exactement la même taille — sélection artificielle possible émergente.

---

## 2. Suivi de clôture (repris de `docs/meta/backlog_historique.md`)

### Zone Z7 — éclairement spatial — CONCEPTION CLOSE ✅
- [x] Décisions actées (pixel exact, 4 tranches + intégrale, hauteurs cm,
      genetic_factor × growth_factor)
- [x] Audit botanique des 14 espèces actuelles
- [x] 5 arbres pérennes premiers calibrés
- [x] Kickoff sprint éclairement rédigé (`sprints/sprint_eclairement.md`)
- [x] **Recadrage conception (2026-05-29)** : Option A (lumière+plantes au
      pixel, sol au plot), échelle 50 cm / 2 cm/px, soleil astronomique,
      empreintes par stade, pérennes polymorphes, génétique biparentale par
      introgression. Voir entrée *Sprint conception éclairement & reproduction*.
- [x] **Implémentation scindée en deux sprints** : éclairement (D20-D21)
      puis génétique/reproduction (D17+D22)
- [x] Implémentation : les deux sprints dédiés sont terminés (Python)
