<!-- Archivé depuis journal.md le 2026-06-03 (Sprint refactor structurel) -->

## 2026-06-02 — Sprint éclairement : ombres-capsules astronomiques + pérennes (Python)

### Contexte

Sprint **Python pur** (`sprints/sprint_eclairement.md`), D20 (ombres pixel) +
D21 (pérennes ligneuses). Le sous-objectif 0 (réalignement OM Python→v4, D10)
était **déjà levé** par le Sprint sol vivant du même jour — case cochée
d'avance. `genetic_factor` neutre 1.0 (la génétique D17+D22 reste son propre
sprint). Périmètre choisi par Nico : **Python seul cette session**, **conception
d'abord**, cadrage position **« continu côté lumière, plot côté sol »**.

### Décisions de session (au-delà du kickoff)

1. **Cadrage hybride position** (au lieu du « tout continu » du journal du
   29/05). `PlantInstance` porte `x_cm, y_cm` continus, **lus uniquement par le
   LightField**. Tout le sous-sol (uptake, conflits, soil_memory, succession,
   banque) reste indexé au plot via `plot_foyer` — **zéro revalidation** de ces
   systèmes. Les graines naissent au centre du plot.
2. **LightField analytique, pas de grille pixel.** Le moteur de vérité ne
   consomme la lumière qu'en deux points : lumière reçue par plante
   (photosynthèse + gate de croissance) et lumière-sol au plot (germination,
   niche, banque). Les deux se calculent par **tests point-dans-capsule**, sans
   raster. Conséquences : **pur Python** (pas de numpy, bloqué par PEP 668),
   portage C# trivial, rapide. La grille 2 cm/px actée le 29/05 reste pour le
   **rendu Godot** (`core/LightField.cs` visuel), pas pour la simulation. Toute
   la physique actée est préservée (astro 49°N, cumul multiplicatif, plancher
   15 %, intégrale journalière).
3. **Auto-ombrage résolu par tri hauteur-décroissante.** Une plante lit la
   lumière filtrée par les **seuls voisins plus hauts** (la boucle s'arrête dès
   `hauteur_voisin ≤ hauteur_plante`), jamais par sa propre ombre. La
   lumière-sol, elle, subit **toutes** les ombres.
4. **Extensibilité du catalogue** (demande explicite de Nico). `STRATE_DEFAULTS`
   fournit rayon de canopée / rayon racinaire / densité **par défaut selon la
   strate** ; une espèce n'inscrit que ses **exceptions** (rosette large du
   pissenlit, racines traçantes du pâturin…). Les `foliar_offsets`/`root_offsets`
   dessinés à la main **disparaissent** — `foliar_plots`/`root_plots` sont
   dérivés du rayon. Ajouter une espèce = hauteur(s) + strate, et 0–2 overrides.

### Modèle d'ombre (D20)

Soleil astronomique φ=49°N, 4 saisons × 3 tranches éclairées (matin/midi/soir,
H=±45°/0°). `solar_slice()` → direction d'ombre + `1/tan(élévation)` (longueur)
+ `sin(élévation)` (poids). Élévations obtenues : été 64°, équinoxe 41°, hiver
18° (ombres courtes l'été, longues l'hiver — physique juste). Ombre = **capsule**
(disque de canopée glissé), opacité `foliage_density` par espèce, cumul
multiplicatif, plancher 15 %, intégrale = moyenne des tranches pondérée par
l'intensité.

### Pérennes ligneuses (D21)

`perennials.py` : `PerennialWoody(PlantBase)` **surcharge** l'interface lumière
(courbe d'âge `(age_years, hauteur, rayon)` interpolée). Le LightField les traite
à l'identique des annuelles — **zéro duplication**. `age_years` +1/52 par tick.
`foliage_density_at(saison)` renvoie **0 l'hiver** pour les caducs (soleil
d'hiver au sol sous un fruitier — levier permaculture, validé en test). 5 arbres :
figuier/pommier = jardin, cerisier intermédiaire, noyer/chêne = lisière (chêne
centenaire 30 m / couronne 12 m).

### Empreintes & feedback

`canopy_height/canopy_radius/root_radius` par stade (cm) sur `GrowthStage` ;
`current_height = potentiel × growth_factor`. `growth_factor` intègre lentement
la **lumière reçue** (`0.6 + 0.4·lumière`) → un étiolé reste plus court → ombre
moindre : **boucle de feedback** lumière→croissance→ombre fermée.

### Calibration & validation (run 500 ans)

`main.py` simulé **500 ans sans crash** (4 min 35, exit 0). Succession stable en
**mosaïque oscillante 53–83 % de vivaces** (moyenne ~65 %, pics 80–83 %), 12
plantes survivantes, ni emballement ni extinction. **Dérive assumée** vs le
mini-sprint succession précédent (~80 % stable à 30 ans) : le nouveau modèle
(empreintes au rayon + croissance gated par lumière reçue) installe la prairie
plus lentement (~60 ans) et avec une régénération par trouées. Comportement sain
et **acté tel quel par Nico** (nouvelle cible ~65 %, mosaïque réaliste — pas de
recalibrage vers l'ancien 80 %).

### Reste à faire (hors session Python)

- **Portage C#** (`core/LightField.cs` simulation + `core/PerennialWoody.cs` +
  `PlantData.cs` hauteurs/rayons/densités) et **test de parité** — dette D24.
- 4 espèces du kickoff calibrées mais **pas encore codées en Python** (ortie,
  prêle, plantain, molène — seulement au catalogue C#).
- Grille pixel 2 cm/px pour le **rendu Godot** (overlay heatmap), distincte du
  moteur.

### Ce qui a été produit

- `data/code/models.py` — `STRATE_DEFAULTS`, `GrowthStage` métrique (offsets→rayon),
  interface lumière polymorphe, position continue, `growth_factor`, 10 espèces recalibrées
- `data/code/fields.py` — `LightField` v2 analytique (astro + capsules + intégrale)
- `data/code/perennials.py` — `PerennialWoody` + 5 arbres (nouveau fichier)
- `data/code/engine.py` — `light_received`, `age_years`, feedback `growth_factor`
- `journal.md`, `CLAUDE.md`, mémoire ; commit

---
