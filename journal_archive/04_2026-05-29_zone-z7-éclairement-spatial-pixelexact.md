<!-- Archivé depuis journal.md le 2026-06-03 (Sprint refactor structurel) -->

## 2026-05-29 — Zone Z7 : éclairement spatial pixel-exact

### Contexte

Immédiatement après la clôture du Sprint conception bis, Nico identifie
une **7e zone blanche majeure** non couverte par les 6 précédentes :
**le calcul d'ensoleillement par pixel en fonction des ombres portées
par les canopées et structures, à chaque tranche horaire.**

Argument : en permaculture, la micro-géographie des ombres est
constitutive du gameplay. Tu plantes une salade sous un fruitier
exprès, un brise-vent à l'ouest pour adoucir le soleil couchant, tu
exploites une ombre matinale. Le `LightField` actuel (Python + C#) est
trop pauvre — il n'a pas la notion d'ombres portées.

### Décisions Z7 actées

- **Granularité spatiale : pixel exact** (78×57 par tuile). Coût
  mémoire : ~800 KB à 9 tuiles, ~4,4 MB en long terme. Coût CPU :
  < 1 ms par recalcul complet, hebdomadaire. **Trivial.**
- **Granularité temporelle : 4 tranches** (matin / midi / soir / nuit)
  + **intégrale journalière** d'ensoleillement cumulée par pixel.
  L'intégrale pilote la photosynthèse — c'est elle qui compte
  biologiquement.
- **Hauteur des canopées et structures stockée en cm** (range 0 à
  3000+). `PlantData.canopy_height_potential` par stade pour annuelles,
  par courbe d'âge pour pérennes ligneuses.
- **`current_height` calculée** :
  `canopy_height_potential × genetic_factor × growth_factor`
  - `genetic_factor` ∈ [0.7, 1.3], hérité de la graine (D22)
  - `growth_factor` ∈ [0.4, 1.2], modulé par Vigueur / eau / nutriments
- **Boucle de feedback** : la lumière reçue affecte la hauteur, qui
  affecte les ombres portées, qui affectent la lumière reçue des voisins.
  Émergence écologique.
- **Recalcul hebdomadaire** (à chaque tick simulation). Pas en temps
  réel — inutile.
- **Algorithme** : projection d'ombre trapézoïdale par ombrageur (et
  non raycast par pixel). O(ombrageurs × pixels_par_ombre) ≈ 160 000 ops.

### Hauteurs structures actées

- Mare : 0 cm
- Brise-vent (haie taillée) : 150 cm
- Pergola : 250 cm
- Maison normande : 700 cm

### Arbres pérennes — 5 espèces premières (D21)

| Arbre | 5 ans | 10 ans | 20 ans | 50 ans | Centenaire |
|---|---|---|---|---|---|
| Figuier | 200 | 400 | 500 | — | — |
| Pommier | 200 | 350 | 500 | 700 | — |
| Cerisier | 250 | 500 | 700 | 900 | 1000 |
| Noyer | 300 | 600 | 1000 | 1500 | 2500 |
| Chêne | 200 | 400 | 700 | 1500 | 3000 |

Les autres arbres (poirier, prunier, châtaignier, frêne, tilleul,
bouleau, saule, aulne, peuplier, érable…) constituent la dette D23
(catalogue arbres étendu) — à compléter une fois le squelette validé.

### Audit botanique — 14 espèces actuelles

Hauteurs potentielles (cm) à intégrer dans `PlantData` :

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

**Important écologique** : ces hauteurs sont des **potentiels**, modulés
par `genetic_factor × growth_factor`. Deux haricots côte à côte n'ont
jamais exactement la même taille. Sélection artificielle possible
émergente (récolter les plantes les plus hautes favorise la lignée).

### Nouvelles dettes techniques (D20-D23)

- **D20** : système d'éclairement spatial pixel-exact (`LightField` v2,
  ombres portées, 4 tranches + intégrale, recalcul hebdomadaire)
- **D21** : système temporel des pérennes ligneuses (âge en années,
  courbe pluri-décennale, distinct du `GrowthStage`)
- **D22** : héritage génétique de la graine (`genetic_factor` ∈ [0.7,
  1.3], distribution gaussienne, hérité à la fécondation, généralisable
  à d'autres caractères que la hauteur)
- **D23** : catalogue arbres pérennes étendu (poirier, prunier,
  châtaignier, frêne, tilleul, bouleau, saule, aulne, peuplier,
  érable…) — différée post-validation du squelette

### Sprint dédié créé

Kickoff autosuffisant `sprints/sprint_eclairement.md` rédigé.
Le sprint peut **absorber tout ou partie du Sprint 3 (portage
simulation)** parce que toucher au `LightField` et ajouter la nouvelle
classe `PerennialWoody` impose de toucher au tick hebdomadaire — autant
porter `effects.py` et `engine.py` dans la foulée.

À décider en début de session selon l'énergie disponible.

### Ce qui a été produit pour Z7

- Cette entrée `journal.md`
- `sprints/sprint_eclairement.md` (kickoff autosuffisant)
- `CLAUDE.md` mis à jour (Systèmes à concevoir D20-D23, backlog actif)
- Mémoire actualisée (`project_status.md`)
- Commit dédié

---
