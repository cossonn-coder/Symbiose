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

## §REPRISE
Conception FIGÉE. Livré : `docs/conception/CONCEPTION_SOMMET_TROPHIQUE.md` +
kickoffs 01/02/03 + ce fichier. Reste : commit (doc + kickoffs + maj DETTE/journal),
puis `/sprint-auto sprint_sommet_trophique`. Chaque tronçon d'exécution met à jour
CE fichier (hash golden re-figé consigné à ① et ②).
