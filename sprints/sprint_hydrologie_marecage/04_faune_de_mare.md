# ④ — Faune de mare (moustique + libellule) + voix

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Conception :
> `docs/conception/CONCEPTION_HYDROLOGIE_MARECAGE.md` §4 + §9. Prérequis : ②③ faits
> (`eau_surface`/`marais_memory`). **Golden population NEUTRE ou maîtrisé annoncé.**

## Objectif
Faire grouiller le marais : une guilde aquatique data-driven — `moustique` (proie,
prolifère sur l'eau stagnante) et `libellule` (auxiliaire, prédateur du moustique).
Prépare la proie que la carnivore mangera (⑥).

## Fichiers
- `fields/population/registry.py` : 2 `TrophicSpec` neuves (+ salts décorrélés dans
  la table `_SALT_*`). Suivre le patron des espèces existantes (puceron/carabe…).
- `fields/population/resources.py` : `resource_fn` neuves — `_eau_stagnante_grid`
  (lit `eco.eau_surface`/`marais_memory`) pour le moustique ; la libellule réutilise
  `_espece_grid("moustique")` ; `habitat_fn` = flaque/marais (helper neuf).
- `fields/faune_encyclo.py` : `encyclo_meta("moustique")`/`("libellule")` (blurb +
  graphe encyclopédie, DONNÉE pure jamais lue par le tick).
- Voix (§9) : encyclopédie 3 niveaux, carnet (`CONCEPT_DE` → concept `marais`/`eau`),
  pages secrètes si lore, magazine (n/a faune), événements (arrivée libellule).
  Fichiers voix selon `CONCEPTION_VOIX_NARRATIVES.md` (corpus `sim/`).
- `tests/test_population.py` : présence des 2 espèces, moustique nul sans flaque,
  monte avec `eau_surface`, libellule suit le moustique.

## Modèle
`moustique` : `category="ravageur"` (ou `"aquatique"`), `resource_fn` ∝ `eau_surface`
(+ `marais_memory`), `predators=("libellule",)`, fenêtre estivale (chaleur).
`libellule` : `category="auxiliaire"`, `resource_fn=_espece_grid("moustique")`,
`habitat_fn` = flaque + perchoir (végétation haute), `predators=()`. Ordre de tick :
moustique (proie) AVANT libellule (prédateur), comme la chaîne existante.

## Golden
Le smoke n'a pas de flaque → moustique/libellule densité nulle. `test_golden` (écolo)
**inchangé**. Le golden de POPULATION peut bouger si l'ordre de tick est décalé par
l'insertion → re-figeage population **MAÎTRISÉ annoncé** (isoler : insérer les specs
en fin d'ordre pour minimiser). Consigner le nouveau hash population dans `00_etat.md`
avec explication. Écolo NEUTRE.

## Ce qu'il NE faut PAS faire
- Ne pas coder le puits carnivore ici (c'est ⑥ — la plante n'existe pas encore).
- Ne pas oublier les **5 voix** de chaque espèce (règle projet).
- Pas de RNG : positions sprites par `_hash_noise(seed, salt+slot, r, c)` (patron).

## F5
- Nuée de moustiques au-dessus des flaques, libellules en vol stationnaire (⑧) ?
