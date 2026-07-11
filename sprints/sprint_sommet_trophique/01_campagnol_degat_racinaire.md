# ① — Campagnol (herbivore vertébré, proie) + dégât racinaire + voix

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Conception :
> `docs/conception/CONCEPTION_SOMMET_TROPHIQUE.md` §2.1, §3, §4. Pas de prérequis.
> **Golden re-figé MAÎTRISÉ #1 (annoncé) — herbivorie racinaire apparaît.**

## Objectif
Introduire le `campagnol` : rongeur qui broute racines/bulbes/écorce. C'est la PROIE
du sprint (le super-prédateur ② en vit). Il tick en position **proie**
(`predators=()` pour l'instant — ses prédateurs arrivent en ②). Il endommage les
plantes par un **canal racinaire DÉDIÉ**, distinct du ravageur foliaire.

## Fichiers
- `fields/population/registry.py` : 1 `TrophicSpec` `campagnol`, **catégorie NEUVE
  `herbivore_vertebre`**, salt `0x2AF001` (ajouter à la table `_SALT_*`). L'insérer
  en **position proie** (avant les auxiliaires, avec les ravageurs/détritivores) pour
  que ② puisse le lire frais. `predators=()`. `**encyclo_meta("campagnol")`.
- `fields/population/resources.py` : `resource_fn` neuve `_racine_grid` — Σ plantes
  vivantes, poids réparti sur `p.root_plots` (mémoïsé, `plants/base/instance.py:283`),
  pondéré par préférence d'organe/famille (bulbes Amaryllidaceae haut, légumes-racines
  haut, jeune écorce ligneuse), normalisé par `ROOT_REF` (placeholder). `habitat_fn` =
  galeries : réutiliser `_avec_abri_paillage(_undisturbed_grid)` (sol non remué + mulch).
- `fields/faune_encyclo.py` : `FAUNE_ENCYCLO["campagnol"]` = blurb naturaliste (ce
  qu'on VOIT : monticules de terre, galeries, plante flétrie sans cause visible) +
  `interconnexions` — laisser `("rapace","couleuvre")` DÉJÀ (le test symétrie n'exige
  la réciproque que quand rapace/couleuvre existeront, en ② ; à densité nulle rien ne
  casse, mais vérifier que le test tolère un nom absent — sinon poser les
  interconnexions campagnol↔prédateurs entièrement en ②).
- `sim/effects/perturbations.py` : perturbation NEUVE `root_herbivory(plant, tile,
  game_state, eco)` — miroir léger de `herbivory_pressure` mais lit
  `eco.category_density("herbivore_vertebre", r, c)` ; pression modeste ·
  `ROOT_HERBIVORY_GAIN` ; `ReduceHealth` faible si densité haute, bascule létale
  seulement sur jeune ligneux annelé (placeholder). L'appeler dans la boucle chronique
  (là où `herbivory_pressure` est sommé, `sim/engine/boucle.py` ~430 / `chronic_muts`).
- `sim/semiologie.py` : signe NEUF `rongeur_racinaire` (miroir du signe herbivorie,
  mais lit la catégorie `herbivore_vertebre`) — « jaunit/flétrit par la base, tige
  écorcée au ras du sol ». Rendu C# = ③.
- Voix (§4) : carnet (`CONCEPT_DE` → régulation/chaîne trophique), événements (arrivée
  campagnol au ledger), pages secrètes si lore (optionnel), magazine n/a. Suivre
  `CONCEPTION_VOIX_NARRATIVES.md`.
- `tests/test_population.py` : campagnol présent ; densité nulle sans plante à racine ;
  monte là où des racines existent ; catégorie `herbivore_vertebre` agrégée.

## Modèle
`capacité = res_w·_racine_grid + hab_w·galeries`. `survie` standard (chaleur ·
phénologie large `daylen_min≈8.5, daylen_full≈10.0` · perturbation — le bêchage le
chasse via `disturb`). Ordre de tick : campagnol AVANT les auxiliaires.
Dégât : `pression_racine = category_density("herbivore_vertebre",r,c) ·
ROOT_HERBIVORY_GAIN`, modeste (le campagnol est surtout une proie).

## Golden
**Re-figé MAÎTRISÉ #1** : dès que le campagnol prolifère sur des plots racinaires du
smoke, `root_herbivory` retire un peu de santé → dérive localisée. Consigner le NOUVEAU
hash golden dans `00_etat.md` + une phrase d'explication (herbivorie édaphique). Si le
smoke n'a AUCUNE plante à racine exposée, le golden peut rester inchangé — vérifier et
consigner le cas réel. Ne PAS toucher aux autres perturbations.

## Ce qu'il NE faut PAS faire
- Pas de prédateur du campagnol ici (c'est ②).
- Ne PAS rattacher le campagnol à `ravageur` (canal racinaire dédié, Q3).
- Pas de RNG : positions sprites par `_hash_noise(seed, salt+slot, r, c)`.
- Ne pas relever la barre de taille : si `resources.py`/`perturbations.py` gonfle au-delà
  de la bande, signaler (résorption `/refactor`), ne pas élargir le seuil.

## F5 (préparé pour ③)
- Monticules de terre / galeries là où le campagnol prolifère ; plante flétrie « par le
  bas » distincte du criblage foliaire.
