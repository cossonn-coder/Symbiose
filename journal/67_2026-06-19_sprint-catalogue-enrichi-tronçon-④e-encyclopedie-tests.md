# 2026-06-19 — Sprint CATALOGUE ENRICHI · tronçon ④e : encyclopédie (blurb/interconnexions) + tests + stub pont — golden NEUTRE — ④e CLOS, refonte faune B close côté Python

## Contexte

Dernier tronçon Python de la **faune nommée** (modèle B). Les 3 scissions
④b/c/d ont produit **10 espèces NOMMÉES** réparties en 3 catégories trophiques.
④e ne crée **aucune dynamique** : il pose la **métadonnée d'encyclopédie**
(blurb naturaliste + graphe d'interconnexions) sur chaque espèce, complète la
suite de tests, et documente le stub pont par espèce. **Métadonnée jamais lue
par `tick` → golden NEUTRE par construction.**

## Ce qui est fait

### `fields/faune_encyclo.py` (NOUVEAU — donnée pure, 0 import)

Module dédié (pas dans `population.py`, déjà au-dessus du garde-fou ~350 LDC —
kickoff §4). Dict `FAUNE_ENCYCLO {name: (blurb, interconnexions)}` pour les 10
espèces + helper `encyclo_meta(name)` → `{"blurb":…, "interconnexions":…}`
(splat dans `TrophicSpec` ; espèce inconnue → dict vide, pas d'exception).

### `fields/population.py`

`TrophicSpec` gagne deux champs de **DONNÉE PURE**, jamais lus par `tick` :
`blurb: str=""` + `interconnexions: tuple=()`. Import de `encyclo_meta` ; les 10
`TrophicSpec(...)` reçoivent `**encyclo_meta("…")`. Aucune logique nouvelle.

### `fields/__init__.py`

Ré-export `FAUNE_ENCYCLO, encyclo_meta` (API publique du paquet `fields`).

### `tools/simserver/serialize.py` — stub pont (commentaire seul)

Commentaire du bloc sprites mis à jour (C10) : le snapshot émet **DÉJÀ** par
espèce (clé `f.spec.name`, 10 clés depuis ④b/c/d). Reste pour ⑥ : table sprite
par espèce côté client + protocole `target.espece` (C9). **AUCUN changement de
comportement** — la sérialisation par espèce était acquise dès ④b.

## Golden — NEUTRE

| hash | ④d | ④e |
|------|----|----|
| smoke `golden_hash` | `9be1c05a7282…` | **`9be1c05a7282…` INCHANGÉ** |
| `population_hash` | `58ecf6d89e21…` | **`58ecf6d89e21…` INCHANGÉ** |

La métadonnée n'est jamais tickée → aucun chemin de simulation touché. Neutre
prouvé, pas seulement attendu.

## Validation

- **Suite enrichie** `tests/test_faune_dediee.py` — +5 fonctions (→ 17 au
  total), invariants ④e :
  - `test_couverture_dix_especes` : 10 espèces, 3 catégories peuplées.
  - `test_triade_et_salts` : triade complète, 10 salts distincts.
  - `test_phenologie_hivernale` : phénologie hiver nulle (puceron/doryphore) vs
    lombric quasi annuel.
  - `test_metadata_encyclo` : blurb non vide pour les 10.
  - `test_graphe_symetrique` : `predators ⊆ interconnexions` ; sous-graphe des 10
    espèces **SYMÉTRIQUE**.
- **Correction de données pendant le dev** : `herisson.interconnexions` devait
  inclure `lombric` (le hérisson est prédateur du lombric) → symétrie rétablie +
  blurb mis à jour. `interconnexions` n'est donc pas un champ libre : contraint
  par 2 invariants testés.
- `test_golden` PASS (hash inchangé) ; `test_faune_dediee` 17/17,
  `test_population`, `test_attraction`, `test_structures` (65/65),
  `test_fruits` (24/24), `test_ruche` (20/20), `test_vigueur` (135/135),
  `test_biennial`, `test_evergreen`, `test_catalogue_lot2` (16/16).
- Filet C# `~/.dotnet/dotnet build Symbiose.csproj` : **exit 0** (④e Python pur).
  Note : `dotnet` PAS dans le PATH du shell non-interactif → `~/.dotnet/dotnet`.

## Bilan refonte faune B (④ close côté Python)

`auxiliaire`/`ravageur`/`detritivore` (3 champs abstraits) → **10 espèces
NOMMÉES** sur le patron data-driven, chacune avec SA triade
(nourriture/prédateur/habitat). 3 re-figeages **localisés et maîtrisés** :

| tronçon | golden | pop-golden |
|---------|--------|-----------|
| ④a (filet) | `5fddfe54…` NEUTRE | `5e6e688f…` NEUTRE |
| ④b ravageur | `63d50eeb…` | `1f7dcda8…` |
| ④c auxiliaire | `53327632…` | `e707002f…` |
| ④d détritivore | `9be1c05a…` | `58ecf6d8…` |
| ④e encyclo | `9be1c05a…` NEUTRE | `58ecf6d8…` NEUTRE |

`vigueur_hash` `e63b9d7f…` **INCHANGÉ tout du long** (la Vigueur joueur ne dépend
pas de la régulation faune).

## Signalements (carte blanche)

1. **`fields/population.py` toujours > garde-fou ~350 LDC** → à éclater en paquet
   `fields/population/` dans un sprint refactor dédié (hors tronçon catalogue).
2. **Mêmes deux échecs PRÉ-EXISTANTS, hors périmètre** : `test_senescence`
   (~2.7 ans, modèle eau) ; `test_sim_server` pommier nouaison (0 fruit @ S52).
3. **Frontière ⑥** : la sérialisation par espèce est acquise, mais le client
   Godot n'a pas encore de table sprite par espèce ni le protocole
   `target.espece` (réacheminement des actions ciblées). C'est le vrai travail
   pont restant.

## Reste / prochain (choix Nico, pas d'enchaînement auto)

⑤ (pollinisateurs B : bourdon/osmie, registre data-driven, re-figeage maîtrisé
pollen/nouaison) ou ⑥ (vue Godot + sprites + encyclopédie + `target.espece`).
`/clear` entre tronçons.
