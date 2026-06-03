<!-- Archivé depuis journal.md le 2026-06-03 (Sprint refactor structurel) -->

## 2026-05-29 — Sprint conception éclairement & reproduction (recadrage Z7)

### Contexte

Session ouverte sur « lis `sprints/sprint_eclairement.md` ». La lecture du
kickoff Z7 **et du code réel** (`fields.py`, `GridField.cs`, `PlantData.cs`,
`TileData.cs`) a fait remonter trois frictions entre l'intention du kickoff
et l'état du code. Plutôt que d'implémenter, on a rouvert la conception et
tranché l'architecture en profondeur. **Session de conception pure — aucun
fichier de code touché.**

### Frictions relevées à la lecture

1. **Confusion d'échelle « tuile » vs « plot »** dans le kickoff. La réalité
   du code : monde 3×3 **tuiles**, une tuile = 6×8 **plots** quinconce
   (= 432 plots, déjà cité dans l'UX), un plot = sprite 78×57 px. Le
   « 78×57 » du kickoff désignait donc **un plot**, pas une tuile — chiffrage
   mémoire faux d'un facteur ~48 (sans conséquence, RAM négligeable).
2. **Lumière pixel ↔ photosynthèse par plot.** Tout le moteur indexe par
   plot ; une ombre pixel-exacte traverse les frontières de plots. Le
   mapping pixel↔plot n'était pas défini : vraie zone blanche.
3. **Inversion de la source de vérité (D10).** `GridField.cs` est en v4
   (OM tri-compartiment, rain feedback, `PathogenPressure`) alors que
   `fields.py` est resté en v3. Le test de parité du kickoff est impossible
   tant que l'OM diverge.

### Décisions structurantes

**1. Architecture lumière = Option A (maillage adaptatif).**
- **Décision** : « stop les plots » pour la lumière et les plantes. **Canopée
  + lumière au pixel** (structure fine = gameplay des ombres), **chimie du
  sol au plot** (phénomène diffus et lent — le pixel n'y apporte rien et la
  diffusion lisse de toute façon). Maillage adapté au phénomène.
- **Décision** : un **seul pont** pixel↔plot, propre et unidirectionnel — la
  photosynthèse lit la lumière-pixel sous l'empreinte de canopée → module la
  croissance. Le souterrain reste entièrement en monde-plot (inchangé).
- **Décision** : l'espace de simulation de la lumière est **top-down
  cartésien** (vue de dessus, en cm), **jamais** l'espace iso d'affichage —
  sinon la perspective fausserait les longueurs d'ombre. Le rendu projette en
  iso après coup.
- Écarté : Option B (tout au pixel — refonte totale, revalidation 500 ans,
  gain nul sur la chimie lisse) et Option C (lumière agrégée par plot —
  contredit « stop les plots » et sous-exploite le pixel).

**2. Calibration de l'échelle spatiale.**
- **Décision** : **1 plot = 50×50 cm** (maille potagère permaculture). Monde
  3×3 tuiles × (6×8) = 432 plots = **12×9 m ≈ 108 m²**, jardin familial
  crédible.
- **Décision** : résolution de l'espace-sol lumière = **2 cm/px** (~270 k
  px-sol monde, ~5,4 MB pour 5 floats/px — négligeable).
- **Décision** : orientation par défaut **Nord en haut, soleil culminant au
  Sud** (à confirmer en implémentation).
- **Décision** : le plot ne porte plus la position des plantes — il ne sert
  **que** de maille à la chimie du sol. La position des plantes devient
  **continue** (pixel-sol `x_cm, y_cm`), plot-foyer = `floor(pos / 50 cm)`.

**3. Modèle d'ombre (D20).**
- **Décision** : angles solaires par **calcul astronomique** (latitude
  ~49°N), déterministe, 4 tranches (matin/midi/soir/nuit) × saisons. Bonus :
  arme le palier « météo/climat » transcendant (tout devient prévisible).
- **Décision** : `longueur_ombre = hauteur / tan(élévation)`, direction
  opposée à l'azimut. Ombre = **capsule** (disque de canopée glissé sur la
  longueur d'ombre), rasterisée en pixels-sol.
- **Décision** : opacité d'ombre **variable par espèce** → nouveau champ
  `foliage_density` (noyer dense ~0.8, bouleau léger ~0.4). Mécanique
  permaculture (choisir un arbre à ombre légère pour un sous-étage).
- **Décision** : cumul **multiplicatif** des ombres ; **plancher de lumière
  diffuse ~15 %** (rien ne descend à 0 → sous-bois et plantes d'ombre
  viables).
- **Décision** : **intégrale journalière** = moyenne des 3 tranches éclairées
  pondérée par l'intensité solaire ; c'est elle qui pilote la photosynthèse.

**4. Empreintes des plantes.**
- **Décision** : canopée = disque de **rayon tabulé par stade** (nouvelle
  donnée à calibrer, comme les hauteurs).
- **Décision** : racines = **rayon racinaire continu** (cm → ensemble de
  plots exploités pour l'uptake). **Remplace** les `RootOffsets` discrets,
  cohérent avec la position continue.
- **Décision** : `current_height = canopy_height_potential × genetic_factor
  × growth_factor` ; boucle de feedback lumière reçue → growth_factor →
  hauteur → ombre des voisins au tick suivant.

**5. Pérennes ligneuses (D21).**
- **Décision** : **base commune polymorphe** — annuelles et arbres exposent
  la même interface (`current_height`, `canopy_radius`, `foliage_density`,
  `root_radius`). Seule la **logique de croissance** diffère (stades discrets
  vs courbe d'âge). Le LightField/photosynthèse les traitent uniformément,
  zéro duplication. (Écarté : classe `PerennialWoody` totalement séparée.)
- **Décision** : `age_years` (+1/52 par tick) ; courbe âge→(hauteur, rayon) =
  **interpolation des points tabulés** (spline monotone), aucun calage.
- **Décision** : `foliage_density` **saisonnière** — un arbre caduc
  (`WinterStrategy = dormant`) perd son ombre l'hiver. Levier permaculture
  majeur (soleil d'hiver sous un fruitier caduc, ombre d'été). Généralisé aux
  vivaces dormantes.
- **Décision** : **arbres requalifiés par taille** — figuier + pommier =
  fruitiers de jardin jouables, cerisier intermédiaire, **noyer + chêne =
  sujets structurants de lisière** (un chêne mûr fait la taille du jardin
  entier ; aucune échelle ne le rend « une plante parmi d'autres »).

**6. Génétique & reproduction (D17 + D22) — élargissement assumé.**
- **Décision** : concevoir **D17 (banque de graines par espèce) et D22
  (héritage) ensemble**, car D22 a besoin d'un porteur que l'actuelle
  SeedBank (densités d'archétypes par plot, sans espèces ni génétique) ne
  fournit pas.
- **Décision** : **deux banques distinctes** — **SeedBank-sol** (génétique
  vectorielle par espèce, liée au terrain, brassage féral conservé) +
  **SeedBank-joueur** (lots par espèce, transportable, suit l'avatar).
- **Décision** : `genetic_factor` devient un **vecteur de gènes extensible**
  (`{hauteur, vigueur, résistance, sécheresse…}`), seul `hauteur` rempli pour
  l'instant.
- **Décision** : héritage **biparental** — père compatible à portée de
  pollinisation ; `gène_enfant = moyenne(parents) + mutation gaussienne` ;
  sinon autofécondation. **Pollinisation par espèce** (anémogame/entomogame),
  rayon modulé par les **pollinisateurs auxiliaires** (vraie mécanique
  permaculture : favoriser les auxiliaires → meilleures graines).
- **Décision** : hybridation inter-espèces autorisée entre espèces proches,
  **par introgression sur espèce fixe** — l'enfant garde l'espèce de la mère,
  les gènes du père décalent ses facteurs vectoriels (parfois hors [0.7,1.3]
  = vigueur hybride). **Pas** de génération de nouvelles `PlantData` (écarté :
  trop lourd, sous-système complet).

**7. Séquencement de l'implémentation — découpage en deux sprints.**
- **Décision** : la conception est close, mais l'implémentation se scinde car
  D17+D22 sont devenus un moteur de génétique des populations dont le coût
  dépasse D20.
  - **Sprint éclairement** = D20 (ombres pixel) + D21 (pérennes) +
    calibration des empreintes/densités + **réalignement OM Python→v4**
    (préalable à toute parité). `genetic_factor` **neutre 1.0** en attendant.
  - **Sprint génétique/reproduction** = D17 + D22 complets.

### Données restant à calibrer (Sprint éclairement, en code)

Rayon de canopée par stade et `foliage_density` des 14 espèces ; rayons
racinaires ; courbes âge→(hauteur, rayon, densité) des arbres ; échelle
cm/px (2 cm/px actée) ; pondération des tranches solaires.

### Zones blanches différées

- **Version physique (tuiles 3D + cartes MTG)** : la bascule pixel découple
  la version vidéo (continue) de la version physique (cases). À traiter dans
  une session dédiée — le moteur Python n'est peut-être plus la source unique
  des deux versions.
- Ordre exact du tick hebdomadaire (croissance / lumière / photosynthèse /
  feedback).
- Profondeur racinaire (modèle resté 2D).
- Confirmation de l'orientation du monde.

### Ce qui a été produit dans cette session

- Cette entrée `journal.md` + dette consolidée affinée (D17, D20-D22)
- `CLAUDE.md` mis à jour (Option A, échelle, backlog scindé)
- `sprints/sprint_eclairement.md` réécrit (recadré Option A, sans génétique)
- `sprints/sprint_genetique.md` créé (D17 + D22)
- Mémoire actualisée (`project_status.md`, `project_python_source.md`)
- Commit dédié

---
