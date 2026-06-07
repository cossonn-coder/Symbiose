# Sprint Maison & ombre déterministe — état partagé

> État léger partagé entre tronçons (≤ ~25 lignes utiles). Mis à jour en fin de
> chaque sous-sprint. **Conception figée** : `data/code/CONCEPTION_MAISON_OMBRE.md`
> (commit `57ff88f`). Toujours la lire avant un tronçon.

## Ce qu'on construit
La **maison centrale** projette une **ombre déterministe** dans le `LightField`,
les apex **se penchent vers la lumière** (phototropisme branché), et une maquette
montre des secteurs contrastés (S plein soleil / NE semi-ombre / NO ombre) sur un
**cycle annuel**. Maison **8×8×6 m**, calcaire de Montmartin (**albédo borné** =
effet espalier), monde **20×20 m = 40×40 = 1600 plots**, **chemins en pierre**
entre tuiles (→ pas d'ombrage inter-tuiles ; seule la maison ombrage globalement).
Maison **paramétrable** (config terrain : position/empreinte/hauteur/matériau/
climat ; défauts posés ici). `PLOT_CM` inchangé (50 cm).

## Stratégie golden (décision Q4 — SMOKE TEST)
Le golden devient un **smoke test petit & rapide** (petit monde, peu d'années).
Le scénario `main.py` (9 tuiles, 30 ans, pommier sénescent) **cesse d'être le
golden** → devient une **démo/banc d'essai** ; la sénescence ~70 ans passe en
**test long séparé**. Maison + phototropisme couverts par **tests ciblés**
(`test_ombre_maison`, `test_phototropisme`), pas par un hash global gonflé.

## Architecture clé (option B, validée)
Champs lumière **par tuile CONSERVÉS** (pas de `LightField` global — coût ×30
évité). On ajoute un **offset monde par tuile** (`origin_*_cm`) + l'injection de
la **seule maison** comme obstacle dans `compute`. Cf. §1 du doc.

## Découpage (4 tronçons + 1 plus tard ; cf. §9)
- **1 — Monde agrandi + maison INERTE + golden smoke test.** ✅ FAIT (2026-06-07).
  `world/building.py` (`House`, data pure, défauts 8×8×6 m centrée, albédo 0.35) ;
  `Tile.origin_x_cm/origin_y_cm` (inertes, défaut 0, jamais lus par le moteur —
  vérifié par grep) ; `main.py` réécrit en **démo** (8 tuiles + maison + chemins,
  contraste attire-aux conservé) ; **golden = smoke test** 2 tuiles (terre/argile)
  6×8 × 4 ans (~5,6 s, déterministe) ; sénescence ~60 ans sortie en
  `tests/test_senescence.py` (6×6 argile, ~20 s, à la demande). Suite complète
  verte. **Nouveau golden hash** : `8ef7729f…0094a62f`. → `01_*.md`
- **2 — Ombre de la maison dans `LightField`.** ✅ FAIT (2026-06-07). Rectangle
  balayé analytique (`_point_in_swept_rect`) injecté sur **sol ET reçu-plante**,
  test en coords MONDE via `tile_origin` (offset tuile) ; maison **opaque**
  (att=0 → plancher `LIGHT_FLOOR`). **Albédo espalier INCLUS** (option 2, pas 2b) :
  `_wall_albedo_bonus` ajoute la réflexion des faces ENSOLEILLÉES (sud/est/ouest)
  sur ≈ 2,5 m (`WALL_ALBEDO_RADIUS_CM=250`, falloff linéaire), `wall_albedo=0`
  l'annule. Plafond **[LIGHT_FLOOR, 1.0]** conservé (contrat [0,1] aval). Câblé
  `engine→ecofields.tick_light→compute` ; **sans `house` → chemin bit-identique**
  (prouvé : golden inchangé avant ajout maison). `test_ombre_maison` (4 tests :
  N<S, allongement hiver, espalier, déterminisme) vert. Smoke test golden ENRICHI
  d'une maison (T0 nord ombragée, T1 sud albédo) → **nouveau hash
  `0aa2892c…1c8d3678`**. Suite complète verte (genetique 20, croissance 57,
  maitrise 35+20, population, signes 8, vigueur 110, senescence). Coût maison ≈
  **+2,6 %** du tick (ombre +3,5 ms, albédo +6,5 ms / 1600 plots). → `02_*.md`
- **3 — Phototropisme branché dans `growth.py`.** ✅ FAIT (2026-06-07). À l'émission
  d'un segment axial, l'apex tourne vers le **gradient de lumière-sol local**
  (`_phototropic_bias`, différences finies `_light_gradient` sur plots voisins,
  bornes **clampées** → pas de fausse pente en lisière). Déterministe (zéro RNG),
  **borné** : ≤ `MAX_PHOTOTROPISM_TILT`=**12°/émission** + plancher de verticalité
  `MIN_APEX_Z`=**0.30** (lean max acos(0.30)≈72°, jamais à plat). Intensité par
  espèce `PlantBase.phototropism_strength` (l'ancien `phototropism_gain` RÉSERVÉ a
  été **renommé** → ⚠ diverge de `CONCEPTION_CROISSANCE.md` §E qui dit encore
  `phototropism_gain`). **Lumière uniforme/None → biais nul** = structure
  bit-identique (piège §7 couvert). `LightField` du tick (`eco.lumiere`) threadé
  dans `grow_plant(plant, seed, week, light_field=None)` — **4e arg optionnel** →
  tests/outils positionnels (`test_croissance` 57/57) inchangés. `test_phototropisme`
  (11 checks) vert. **Re-figeage maîtrisé** (Tomato + AppleTree procéduraux penchent
  sous l'ombre maison) : **nouveau golden hash `16a1b937…9135dbda`** (stable 2×,
  sénescence pommier inchangée 59.8 ans → dérive cohérente, pas d'emballement).
  Suite complète verte (croissance 57, ombre 4, genetique 20, maitrise 35+20,
  population, signes 8, vigueur 110, senescence). **Valeurs maquette** (tronçon 4) :
  **marqué=0.30** (défaut, Q3), **subtil=0.10** → Nico tranche à l'œil. → `03_*.md`
- **4 — Maquette saisonnière 3 secteurs.** ✅ FAIT (2026-06-07). Outil seul,
  **golden + suite INTACTS** (hash `16a1b937…` inchangé). `render_structure.py` :
  `render_maquette()` → grille **3 secteurs (S/NE/NO, lignes) × 4 saisons
  (colonnes)** dans un vrai `LightField` + maison + albédo, **2 fichiers** subtil
  (`maquette_saison_subtil.svg`, strength 0.10) vs marqué (`…_marque.svg`, 0.30) →
  **Nico tranche à l'œil**. Ombre maison **empilée par tranches diurnes** (umbra
  sombre / pénombre) sur sol éclairé, **plus longue l'hiver** ; volume maison
  tracé ; plant penché (apex vert). Ancien aperçu structure **préservé**
  (`… apercu`). `export_structure.py` : `export_maquette()` → pont JSON
  `maquette_secteurs.json` (mêmes spécimens, pour futur Godot) ; ancien pont
  préservé (`… structure`). **Sujet = TOMATE** (tige unique → signal
  subtil/marqué net ; le pommier branche et noie le signal). Snapshots = 4 saisons
  an 2. **Constats à signaler à Nico** : (a) lumière reçue contrastée **S≈1.00 >
  NE≈0.74 > NO≈0.41** (gradient net) ; (b) la pente vient du gradient de
  lumière-sol **LOCAL = ombre maison + AUTO-OMBRAGE de la canopée** → même en plein
  soleil la plante vigoureuse se penche un peu (réaliste, pas un bug — « S droit »
  pas strictement tenu) ; (c) modèle solaire **symétrique E-O** (angles ±45°) →
  NE/NO diffèrent surtout par la **PHASE** d'ombre, pas la lumière intégrée ;
  l'écart S>NE>NO vient de la PROFONDEUR dans la bande d'ombre. Métrique panneau =
  **pli** (déport horizontal du sommet, cm), ↑ clairement avec strength. → `04_*.md`
- **Sprint maison CLOS côté Python.** Reste **tronçon 5** (plus tard, hors sprint) :
  rendu Godot maison + ombre, portage C# (D24).

## Boucle de travail (rappel CLAUDE.md)
Lancer `0N` → travailler → vérifier le golden/tests → mettre à jour ce fichier →
commit → **`/clear`** → lancer `0N+1`.

## Décisions actées (cf. §8 du doc — Q1-Q6 toutes tranchées)
Chemins en pierre (Q1) · tuiles hétérogènes (Q2) · phototropisme **marqué** défaut,
Nico tranche sur exemples (Q3) · golden smoke test (Q4) · calcaire + albédo +
maison paramétrable (Q5) · maquette annuelle 4 images/saison (Q6).

## Points ouverts (à trancher dans le tronçon concerné, défaut sobre + signaler)
- **1** : ✅ TRANCHÉ. Chemins = **50 cm (1 plot)**, NON simulés (espace monde entre
  tuiles, modèle sobre). Layout figé (cm, monde 2000²) : bandes 11 | chemin |
  16 | chemin | 11 plots dans chaque axe → coins 11×11, arêtes 11×16/16×11,
  maison 16×16 au centre. `origin_*_cm` des tuiles : col0=0/600/1450, idem lignes.
  Golden smoke test = 2 tuiles 6×8 × 4 ans.
- **2** : ✅ TRANCHÉ. Test = `_point_in_swept_rect` analytique (intervalle de `s`
  par axe ∩ [0,longueur]). Albédo : rayon **250 cm**, falloff **linéaire**
  `1−perp/rayon`, faces éclairées via `normale·soleil>0`. **⚠️ Point d'arbitrage
  pour Nico** : la lumière-sol est plafonnée à **1.0** (contrat [0,1] aval :
  shade_memory/growth_factor/niche). En plein soleil ouvert la lumière vaut déjà
  1.0, donc l'espalier du mur **sud** y **sature** (pas strictement > plein champ).
  L'effet reste démontrable là où il y a de la marge (pied du mur **est**,
  partiellement ombré le soir — c'est ce que teste `test_ombre_maison`). Un vrai
  « point chaud > 1 » (microclimat thermique du mur sud) demanderait un **champ
  thermique distinct** → hors périmètre, à décider plus tard si on veut le rendre.
- **3** : ✅ TRANCHÉ (provisoire). `phototropism_strength` **marqué=0.30** (défaut),
  **subtil=0.10** pour la maquette comparative (tronçon 4) → **valeur finale tranchée
  par Nico à l'œil** sur les rendus. Bornes : `MAX_PHOTOTROPISM_TILT`=12°/émission,
  `MIN_APEX_Z`=0.30 (jamais à plat). Tous trois = leviers de module dans `growth.py`.
