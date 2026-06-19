# 2026-06-19 — Sprint CATALOGUE ENRICHI · tronçon ⑤ : pollinisateurs B (bourdon/osmie) registre data-driven — golden re-figé MAÎTRISÉ (pollen/nouaison) — ⑤ CLOS

## Contexte

Après la refonte faune B (④, 10 espèces consommatrices nommées), ⑤ étoffe l'autre
volet trophique : les **pollinisateurs**. Patron déjà data-driven depuis le sprint
pollinisation (`PollinatorSpec` + `build_pollinator_registry()`) — on ajoute
**2 espèces nommées** sans refonte moteur : **bourdon** et **osmie**. Re-figeage
golden MAÎTRISÉ attendu : plus de butineurs → plus de pollen déposé → plus de
nouaison → plus de fruits → aval décompo.

## Ce qui est fait

### `fields/population.py`

- Salts dédiés : `_SALT_BOURDON = 0x2AD001`, `_SALT_OSMIE = 0x2AE001`.
- `POLLINATOR_NAMES` 3 → 5 (abeille, syrphe, papillon, **bourdon**, **osmie**).
  Load-bearing : lu par les butineurs, par `pollinator_density` et par
  `vigueur_macro`.
- Attractivités florales propres :
  - `_ATTRACT_BOURDON` : Fabaceae / Lamiaceae = 1.0, Solanaceae = 0.65
    (*buzz pollination* — le bourdon vibre les anthères poricides de la tomate,
    que l'abeille ne sait pas faire).
  - `_ATTRACT_OSMIE` : Rosaceae = 1.0 (abeille maçonne des vergers), Apiaceae = 0.85.
- Foragers : `_FORAGER_BOURDON` (n_max = 8, deposit = 0.6), `_FORAGER_OSMIE`
  (n_max = 5, deposit = 0.6).
- `_osmie_habitat_grid` : habitat = rondelle pollinisateur (plancher) + **bump des
  structures `pile`** (niche-bois — l'osmie niche dans le bois mort), lu en
  duck-typing sur `eco.structures` comme les habitats ④c (carabe/hérisson).
- 2 entrées dans `build_pollinator_registry()` :
  - **bourdon** : photopériode 9.5 / 12.0 (précoce — actif tôt et par temps frais).
  - **osmie** : photopériode 10.0 / 12.5 (printanier), `habitat_fn=_osmie_habitat_grid`.
  - `bridge=None` pour les deux (pas de pont larvaire, contrairement à
    chenille→papillon / syrphe_larve→syrphe).

### `fields/ecofields/container.py`

Commentaire mis à jour (5 pollinisateurs).

## Golden — re-figé MAÎTRISÉ

| hash | ④e | ⑤ |
|------|----|----|
| smoke `golden_hash` | `9be1c05a…` | **`f7e1a9b43b24…39458f985df9dcadfdb9d7fc1a098187c7811e31427466f00990`** |
| `population_hash` | `58ecf6d8…` | **`a39834dfb1e6…ee7a246b8a0720b2da21fe81f1d0ad0ffec877194dcec23811b9`** |
| `vigueur_hash` | `e63b9d7f…` | **`e63b9d7f…` INCHANGÉ** |

- **smoke** : re-figeage vrai. Bourdon + osmie butinent → pollen supplémentaire →
  nouaison accrue → fruits → chaîne décompo en aval. Cause directe et attendue.
- **pop-golden** : dérive **PUREMENT ADDITIVE**, prouvée. Les 13 champs existants
  restent byte-identiques ; seuls bourdon/osmie s'ajoutent au digest. Ils n'ont
  ni proie ni prédateur (pollinisateurs), donc ne perturbent aucune autre densité.
- **vigueur-traj** : INCHANGÉE (la Vigueur joueur ne dépend pas des pollinisateurs).

## Validation

- `test_golden` PASS (hash `f7e1a9b4…`) ; `test_population` PASS (`a39834df…`).
- `test_faune_dediee` : +section 9 (5 fonctions, 26 checks pollinisateurs B) —
  TOUS verts (existence/triades, attractivités buzz/Rosaceae, foragers,
  habitat osmie nul sans pile / bump local avec pile, `pollinator_density` =
  somme bourdon+osmie).
- `test_population.py` `GUILDS` += bourdon/osmie ; `simserver/macro.py` + `fields.py`
  GUILDES 13 → 15 (libellés alignés).
- Suite complète : **183/184**, identique à ④c/④d — les 2 échecs sont
  **PRÉ-EXISTANTS hors périmètre** (re-prouvés sur HEAD ④e) : `test_senescence`
  (mort asphyxie ~2.7 ans, modèle eau) ; `test_sim_server` pommier nouaison 0 fruit
  @ S52 (le pommier meurt « sèche » avant fructif — sans rapport avec ⑤).
- Filet C# `dotnet build Symbiose.csproj` : **exit 0** (⑤ Python pur ;
  `export PATH="$HOME/.dotnet:$PATH"`).

## Signalements (carte blanche)

1. **`fields/population.py` toujours > garde-fou ~350 LDC pur** (encore alourdi par
   les 2 triades pollinisateurs) → à éclater en paquet `fields/population/` dans un
   sprint refactor dédié (hors tronçon catalogue). Déjà signalé ④b/c/d.
2. **Encyclopédie (blurb/interconnexions) des pollinisateurs NON faite** : les
   pollinisateurs n'ont jamais eu d'entrée `FAUNE_ENCYCLO` (cf docstring
   `encyclo_meta`). Reste à ⑥ avec sprites + `target.espece`, comme prévu au doc §7.3.
3. **Mêmes deux échecs PRÉ-EXISTANTS hors périmètre** (cf Validation).

## Reste / prochain (choix Nico, pas d'enchaînement auto)

Ne reste que **⑥** : vue Godot + sprites + encyclopédie + protocole pont
`target.espece` (réacheminement des actions ciblées). `/clear` entre tronçons.
