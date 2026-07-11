# Sprint SOMMET TROPHIQUE (T1 super-prédateur + T7 herbivore vertébré) — état vivant

> Carnet de bord `/conception` (§0bis). Reconstructible à froid : lire
> `CLAUDE.md` + `docs/conception/CONCEPTION_COMPLETUDE_ECOSYSTEME.md` §3 (D61,
> trous T1+T7) + ce fichier. **PHASE B (figeage) — arbitrages Q1-Q3 tranchés.**

## Arbitrages Nico (2026-07-11, lot 1 — TOUS = reco)
- **Q1 = 2 espèces** : `rapace` (aérien, proies campagnol+merle) + `couleuvre`
  (terrestre, proies campagnol+limace).
- **Q2 = hérisson laissé** peu régulé (quasi-apex du jardin) — noté, pas de puits.
- **Q3 = canal racinaire dédié** : catégorie `herbivore_vertebre` + perturbation
  `root_herbivory` + signe propre, PAS rattaché à `ravageur`.

## Objet
Combler les 2 boucles ouvertes couplées du référentiel D61 :
- **T1 / D1** — super-prédateur : ferme le sommet trophique. Aujourd'hui merle,
  hérisson, coccinelle, carabe n'ont AUCUN puits → régulés seulement bottom-up.
- **T7 / B4** — herbivore vertébré : proie crédible du super-prédateur (couple T1).

## Modèle moteur (vérifié dans le code, 2026-07-11)
- Faune = `TrophicSpec` data-driven (`fields/population/spec.py`) tickée par
  `PopulationField` (`field.py`) : `cible = capacité·survie`,
  `capacité = res_w·resource + hab_w·habitat`,
  `survie = phénologie·chaleur·(1−pred_w·Σprédateurs)·(1−disturb)`.
- **Puits top-down = champ `predators=(...)`** (noms résolus en champs au tick,
  `vie_macro.py:_predator_field`). À densité 0 → +0 → **golden neutre**.
- **Ordre de tick = toutes les proies avant tous les prédateurs**
  (`registry.build_population_specs`) → décalage d'inertie = boom-bust.
- Herbivorie plante = `herbivory_pressure` lit `category_density("ravageur")`
  (`sim/effects/perturbations.py:304`). Signe diégétique via `sim/semiologie.py`.
- 5 voix : encyclopédie faune = `fields/faune_encyclo.py` (`encyclo_meta`,
  donnée pure golden-neutre) ; INVARIANT testé : tout `predators` ⊂
  `interconnexions`, sous-graphe trophique SYMÉTRIQUE.
- Vue : pont expose les champs PAR ESPÈCE (pattern ⑥b catalogue enrichi),
  `MacroLife.cs` rend un sprite/espèce.

## Design proposé (À VALIDER — challengé, non figé)
- **T7 = `campagnol`** (meilleur candidat : ronge racines/bulbes/écorce, proie
  emblématique des rapaces/couleuvres/belettes). Une seule espèce (pas de lapin
  en plus — éviter le sur-ajout).
- **T1 = 2 super-prédateurs** (data-driven, miroir de la scission auxiliaires) :
  - `rapace` (aérien, buse/crécerelle) : proies = campagnol + merle.
  - `couleuvre` (terrestre) : proies = campagnol + limace.
  - → campagnol a 2 prédateurs (réaliste), merle 1 (rapace), limace +1 bonus.
- **Câblage puits** : `campagnol.predators=("rapace","couleuvre")`,
  `merle.predators+=("rapace",)`, `limace.predators+=("couleuvre",)`.
- **Hérisson** : laissé peu régulé (quasi-apex du jardin, peu de prédateurs
  réels — honnête écologiquement ; sinon blaireau/grand-duc = ajout lourd différé).
- **Dégât campagnol** : canal racinaire DÉDIÉ (nouvelle catégorie
  `herbivore_vertebre` + perturbation `root_herbivory` + signe propre « rongé au
  collet/écorcé »), pas rattaché à `ravageur` (éviterait le conflat foliaire/racine).

## Découpage pressenti (3 tronçons, perf-first, golden re-figé MAÎTRISÉ)
1. **① campagnol (proie) + dégât racinaire** — TrophicSpec `campagnol` cat.
   `herbivore_vertebre`, resource=racine/bulbe, habitat=galeries (sol non remué),
   `predators=()` encore, salt dédié, 5 voix, perturbation `root_herbivory` +
   signe. **Golden re-figé #1** (herbivorie édaphique apparaît).
2. **② super-prédateurs (sommet)** — TrophicSpec `rapace`+`couleuvre` cat.
   `super_predateur`, resource=densité proies, `predators=()`, salt, 5 voix ;
   câbler les puits (campagnol/merle/limace) ; tickés en DERNIER.
   **Golden re-figé #2** (top-down boom-bust sur la chaîne).
3. **③ vue Godot + pont** — pont par espèce, `MacroLife.cs` sprites
   campagnol/rapace/couleuvre, mapping signe `root_herbivory` côté `PlantRenderer`,
   rendu encyclopédie. **Golden intact.**

## Coût perf estimé
3 nouveaux `PopulationField`. resource_fn rapace/couleuvre = lecture de grilles de
densité DÉJÀ calculées (cheap). campagnol = 1 balayage plantes pour la grille
racine. Budget ≤ +10 %/tronçon respecté (à confirmer au chiffrage ②).

## Carte des tronçons (FIGÉ — prêt pour /sprint-auto)
- **① `01_campagnol_degat_racinaire.md`** — campagnol (proie, cat.
  `herbivore_vertebre`) + perturbation `root_herbivory` + signe `rongeur_racinaire`
  + 5 voix. **Golden re-figé #1** (herbivorie édaphique).
- **② `02_super_predateurs.md`** — rapace + couleuvre (cat. `super_predateur`) +
  câblage puits (campagnol/merle/limace) + 5 voix. **Golden re-figé #2** (top-down).
- **③ `03_vue_godot.md`** — sprites C# par espèce (pont déjà par espèce, rien à
  changer côté Python) + mapping signe racinaire. **Golden intact.**

## Avancement d'exécution
### ① campagnol + dégât racinaire — FAIT (2026-07-11)
- **TrophicSpec `campagnol`** cat. NEUVE `herbivore_vertebre`, salt `0x2AF001`,
  `predators=()` (les puits arrivent au ②), fenêtre 8.5/10.0 (large/précoce).
  - `resource_fn=_racine_grid` : Σ plantes vivantes stade≥1 de
    `(health/3)·palatabilité_racine` distribuée sur `root_plots`, normalisée
    `ROOT_REF=2.0`. Palatabilité par famille (`Amaryllidaceae` 1.0 → `Poaceae`
    0.20) + bonus ligneux jeune (annélation du collet).
  - `habitat_fn=_avec_abri_paillage(_undisturbed_grid)` : galeries = sol non remué.
- **Perturbation `root_herbivory`** (`sim/effects/perturbations.py`, boucle
  CHRONIQUE) : `pressure = category_density("herbivore_vertebre")·0.16` ;
  < plancher 0.008 → aucun dégât ; ligneux jeune (≤250 cm) & dens ≥ 0.55 →
  LÉTAL −2 (annélation) ; sinon **morsure probabiliste −1** décidée par
  `_hash_noise(seed, week·43, r, c) < pressure` (déterministe, miroir sécheresse/
  ombre). Cappée −1/tick/plante par `_cap_chronique`.
- **Signe `rongeur_racinaire`** (`sim/semiologie.py`, priorité 3.5) : rampe sur
  `category_density`, plancher DRY = `FLOOR/GAIN ≈ 0.05`. Carnet : concept
  `("ravageur","rongeur_racinaire") → "ravageurs"`.
- **5 voix** : encyclopédie `fields/faune_encyclo.py` (blurb + interconnexions
  `rapace`/`couleuvre` en forward-declaration) ; carnet ci-dessus.
- **Golden RE-FIGÉ #1** (prévu au kickoff — apparition de l'herbivorie édaphique) :
  `817cd77298678302516e0632ac97d8145482bd6d239b47de2ef824a784dd0f09`.
  Légitimité PROUVÉE : en neutralisant `root_herbivory` (→ []) le hash retombe
  EXACTEMENT sur l'ancien golden → la dérive vient UNIQUEMENT du dégât voulu
  (éparpillement de morsures −1 sur les plantes appétées : Minette/Fabaceae,
  Pissenlit/Asteraceae, Pâturin/Poaceae, Bourse-à-pasteur/Brassicaceae ;
  pic densité campagnol 0.136 sur T0, le jeune pommier SURVIT).
- **population_hash re-capturé** :
  `96efac284a2425ff198bc485b66645886873a16e302c5a123a1e6da04c8e2239`.
- **Tests** : golden PASS · population PASS · faune_dediee (11 espèces) PASS ·
  stress_chronique PASS (`root_herbivory` neutralisé en labo, confond isolé) ·
  sim_server 269/269 (16 espèces/tuile) · maitrise 35/35 · maitrise_detection
  20/20 · signes · carnet · encyclopedie · mycelium · attraction · evenements —
  tous verts.
- **Taille** : tous fichiers ≤ green sauf `fields/population/resources.py`
  270→**304 LDC** = 🟡 vigilance (une seule responsabilité : grilles-ressources
  du champ population, une fn par guilde). Toléré/signalé, PAS de split.
- **C#** : non concerné (tronçon Python pur).
- **Reste F5 Nico** : rien à ①. Les sprites campagnol côté vue + mapping signe
  `rongeur_racinaire` dans `PlantRenderer` sont le tronçon ③.

### ② super-prédateurs (rapace + couleuvre) — FAIT (2026-07-11)
- **2 TrophicSpec NEUVES** cat. NEUVE `super_predateur`, insérées en TOUTE FIN
  d'ordre de tick (après toutes les proies → elles les lisent FRAÎCHES = boom-bust) :
  - `rapace` salt `0x2B0001`, fenêtre LARGE 9.0/11.0 (chasseur résident) ;
  - `couleuvre` salt `0x2B1001`, fenêtre héliophile estivale 11.0/13.0.
- **Capacité PILOTÉE PAR LE BAS** (décision de design, cf. blocage ci-dessous) :
  `resource_fn=_proies_grid(proies, huntabilité)` = densité de proies (somme
  normalisée `PROIES_REF=1.5`) MULTIPLIÉE par le terrain de chasse ; `habitat_w=0`
  (habitat NUL) → **aucune capacité ne naît d'un terrain vide** : un sommet sans
  proie ne s'installe jamais (philo #2). Rapace = proies (campagnol+merle) × huntabilité
  `_rapace_habitat_grid` (terrain ouvert 0.6 + perchoir ligneux ≥200 cm 0.4, plancher
  `RAPACE_HUNT_FLOOR=0.35`). Couleuvre = proies (campagnol+limace) × cache
  `_undisturbed_structure_grid` (sol non remué + piles).
- **Puits top-down câblés** (§2.4) : `campagnol.predators=("rapace","couleuvre")`,
  `merle.predators=("rapace",)`, `limace.predators=("carabe","herisson","couleuvre")`.
- **Voix** : encyclopédie `faune_encyclo.py` — blurbs rapace (« silhouette en croix…
  sa seule ombre fige le jardin ») + couleuvre (« lovée au soleil… inoffensive pour
  qui la laisse filer ») ; interconnexions RÉCIPROQUES posées (rapace↔campagnol/merle,
  couleuvre↔campagnol/limace) → **sous-graphe trophique SYMÉTRIQUE** (invariant testé,
  vérifié). Carnet : la régulation top-down reste gatée par le concept `ravageurs`
  déjà mappé en ① (le moteur n'émet PAS de ledger de prédation → pas de nouveau
  mapping). Événements « arrivée d'un super-prédateur » : PAS de mécanisme d'arrivée
  d'espèce au ledger aujourd'hui (① n'en a pas créé pour le campagnol non plus) →
  différé, hors périmètre golden-gaté. Pages : lore optionnel (§7), non ajouté
  (aligné sur ①). Magazine : n/a (kickoff).
- **Golden RE-FIGÉ #2** (prévu au kickoff — boom-bust top-down sur la chaîne) :
  `eb46b49deef4590f0b5f44ce0309c0c09bbbd3d9f536aa039ba80108bc25dd5c`.
  Légitimité PROUVÉE : en retirant les SEULS puits (rapace/couleuvre ôtés des
  predators de campagnol/merle/limace), le hash retombe EXACTEMENT sur le golden ①
  `817cd77298…` → la dérive vient UNIQUEMENT de la régulation top-down voulue (les
  nouveaux champs super_predateur sont golden-neutres au digest ; tout le delta est
  le rabotage de survie merle/limace/campagnol).
- **population_hash re-capturé** (2 champs ajoutés à GUILDS + puits) :
  `2431b6b1531183cd3068d9c2b5b83c32e5f02ab630ce612722faedbfe101be80`.
- **Tests** : golden PASS · population PASS (nul-sans-proie, montée-avec-proie,
  puits top-down avec 0.223 < sans 0.303, présence) · faune_dediee PASS (13 espèces,
  symétrie étendue rapace/couleuvre, ressource proies) · sim_server 269/269
  (18 espèces/tuile) · encyclopedie 68/68 · carnet 19/19 · evenements 20/20 ·
  signes 8/8 · maitrise 35/35 · stress_chronique · attraction · mycelium — verts.
- **Taille** : `resources.py` 304→**349 LDC** = 🟡 vigilance (responsabilité unique :
  grilles-ressources du champ population). Toléré/signalé, PAS de split. Autres verts
  (registry 261, faune_encyclo 78).
- **C#** : NON concerné (tronçon Python pur — aucun fichier .cs touché).
- **Blocage/décision imprévue** : le modèle générique fait capacité = res + hab
  (ADDITIF). Un habitat de super-prédateur (terrain ouvert = ~1.0 partout SANS
  plantes) aurait fait DÉCOLLER le prédateur sans aucune proie — anti-écologique et
  contraire à « nul sans proie » (kickoff). Décision : le terrain devient un
  MODULATEUR MULTIPLICATIF de la proie (`_proies_grid(noms, habitat_fn)`) avec
  `habitat_w=0` → le sommet est strictement piloté par le bas. Conserve la préférence
  de terrain (huntabilité) sans créer de capacité fantôme.
- **Reste F5 Nico** : rien à ② (Python pur). Sprites rapace/couleuvre côté vue +
  reflux visible des proies = tronçon ③.

## §REPRISE
② CLOS (non commité — l'orchestrateur commite). Golden re-figé #2
`eb46b49deef4…`, population_hash `2431b6b153…`, prouvé localisé (retombe sur ①
si puits ôtés). PROCHAIN : `/clear` puis `03_vue_godot.md` (sprites C# par espèce
campagnol/rapace/couleuvre + mapping signe `rongeur_racinaire` dans `PlantRenderer`,
pont déjà par espèce → **golden intact**, tronçon C#/F5).
