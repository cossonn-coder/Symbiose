# ② — Super-prédateurs (rapace + couleuvre) + câblage des puits + voix

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Conception :
> `docs/faune/trophique/conception_sommet_trophique.md` §2.2-§2.4, §4. Prérequis : ① fait
> (`campagnol` existe, catégorie `herbivore_vertebre`).
> **Golden re-figé MAÎTRISÉ #2 (annoncé) — top-down boom-bust sur la chaîne.**

## Objectif
Fermer le sommet trophique : deux super-prédateurs data-driven qui régulent
campagnol/merle/limace **par le haut** (philo #1/#2 : puits sur un champ, jamais un
malus scripté). Le décalage d'inertie proie↔prédateur produit le **boom-bust**.

## Fichiers
- `fields/population/registry.py` :
  - 2 `TrophicSpec` NEUVES, **catégorie `super_predateur`** :
    - `rapace` : salt `0x2B0001`, `resource_fn = _proies_grid(("campagnol","merle"))`
      (somme normalisée, cf. Modèle), `habitat_fn` = terrain ouvert + perchoir,
      `predators=()`, fenêtre `daylen_min≈9.0, daylen_full≈11.0`,
      `**encyclo_meta("rapace")`.
    - `couleuvre` : salt `0x2B1001`, `resource_fn = _proies_grid(("campagnol",
      "limace"))`, `habitat_fn` = sol ensoleillé non remué + cache (réutiliser
      `_undisturbed_structure_grid`/`_pile_grid`), `predators=()`, fenêtre
      héliophile estivale `daylen_min≈11.0, daylen_full≈13.0`, `**encyclo_meta`.
  - Les insérer **en toute fin d'ordre de tick** (prédateurs après toutes les proies).
  - **Câbler les puits** (§2.4) : `campagnol.predators=("rapace","couleuvre")`,
    `merle.predators=("rapace",)`, ajouter `"couleuvre"` à `limace.predators`
    (→ `("carabe","herisson","couleuvre")`).
- `fields/population/resources.py` : helper `_proies_grid(noms)` = somme des
  `_espece_grid(nom)` normalisée (généralise le patron libellule→moustique). Habitats
  neufs si besoin (perchoir rapace) — sinon réutiliser les grilles existantes.
- `fields/faune_encyclo.py` : `FAUNE_ENCYCLO["rapace"]`/`["couleuvre"]` (blurb +
  interconnexions). **INVARIANT symétrie** (testé) : compléter les interconnexions
  réciproques — `rapace↔campagnol`, `rapace↔merle`, `couleuvre↔campagnol`,
  `couleuvre↔limace` (chaque `predators` ⊂ `interconnexions`, sous-graphe trophique
  symétrique).
- Voix (§4) : carnet (concept régulation top-down / chaîne trophique), événements
  (arrivée d'un super-prédateur = événement rare marquant au ledger), pages secrètes
  si lore (rapace en vol, couleuvre au soleil). Magazine n/a.
- `tests/test_population.py` : rapace/couleuvre présents ; densité nulle sans proie ;
  montent là où campagnol/merle/limace abondent ; les proies refluent quand le
  super-prédateur est haut (boom-bust). Vérifier l'invariant symétrie du graphe.

## Modèle
`capacité_super = res_w·_proies_grid + hab_w·habitat`. `survie` standard, `predators=()`.
Ordre de tick : campagnol/merle/limace (proies, déjà en place) → PUIS rapace/couleuvre.
Effet puits : la `survie` de chaque proie est rabotée par `(1 − pred_w·densité_super)`
là où le super-prédateur est présent.

## Golden
**Re-figé MAÎTRISÉ #2** : le câblage des puits change la survie de merle/limace/campagnol
présents dans le smoke → densités décalées (boom-bust). Consigner le NOUVEAU hash golden
dans `00_etat.md` + explication (top-down). Isoler la dérive : insérer les specs en fin
d'ordre pour ne pas décaler inutilement le reste.

## Ce qu'il NE faut PAS faire
- Ne PAS donner de puits au hérisson ni aux auxiliaires insectes (hors périmètre, Q2/§2.4).
- Ne PAS ajouter de 3ᵉ super-prédateur (belette écartée, Q1).
- Pas de RNG : positions sprites par `_hash_noise(seed, salt+slot, r, c)`.
- Ne pas relever la barre de taille (résorption `/refactor` si dépassement signalé).

## F5 (préparé pour ③)
- Rapace en vol au-dessus des zones à campagnols ; couleuvre lovée près des piles de
  bois au soleil ; reflux visible des proies après un pic de prédateur.
