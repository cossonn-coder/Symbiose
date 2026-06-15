# Sprint refactor structurel — réorganisation du code en paquets
# + assainissement des gros fichiers de documentation

**Statut** : à faire — conception close le 2026-06-03
**Nature** : sprint **structurel** (zéro changement de comportement). Aucune
mécanique écologique nouvelle. Le succès se mesure à l'**identité de sortie**
avant/après, pas à une fonctionnalité.
**Prérequis** : aucun (peut se faire à tout moment). Idéalement **avant** de
nouveaux gros sprints de mécanique, pour ne pas refactorer une cible mouvante.

> Déclencheur (2026-06-03) : après les sprints sol vivant / succession /
> éclairement / sénescence / génétique, les fichiers ont enflé et mélangent les
> responsabilités. `journal.md` est devenu monolithique et duplique la dette +
> le backlog présents aussi dans `CLAUDE.md`. On assainit avant que ça pourrisse.

---

## État chiffré (HEAD au 2026-06-03)

| Fichier | Lignes | Responsabilités mélangées |
|---|---|---|
| `data/code/models.py` | 1307 | constantes d'échelle + gènes, `GrowthStage`, `PlantInstance`, `ConflictNotification`, `PlantBase` + 5 familles, espèces concrètes, adventices, `StakeSlot`/`Tile`/rondelles, catalogues |
| `data/code/fields.py` | 1058 | `GridField`, `LightField` (+ astronomie), `DisturbanceField`, `SeedBank` + `GeneStat`, `EcoFields`, hashs déterministes, ~50 constantes |
| `data/code/engine.py` | 815 | orchestration du tick + succession + reproduction + transitions saisonnières + aléas |
| `data/code/effects.py` | 570 | mutations, résolution d'effets, perturbations, mortalité |
| `journal.md` | 1438 | log chronologique + dette + backlog (dette/backlog **dupliqués** dans `CLAUDE.md`) |
| `CLAUDE.md` | 312 | instructions projet + backlog + architecture (redondances avec journal) |

Autres modules Python (déjà à bonne taille, à ranger sans découper) :
`perennials.py` 166, `main.py` 168, `seeds.py` 89, `reproduction.py` 111,
`test_genetique.py` 245, `test_auxiliaires.py` 108.

---

## Décisions actées (2026-06-03)

1. **Code → package réorganisé par domaine** (pas un simple découpage à plat).
   `data/code/` devient une arborescence de sous-paquets.
2. **Docs → archiver + source unique** : archiver les vieilles entrées de
   `journal.md` ; sortir la **dette** et le **backlog** dans des fichiers dédiés
   référencés **une seule fois** (fin de la duplication `CLAUDE.md` ↔ `journal.md`).
3. **Filet : golden output déterministe** capturé **avant** tout déplacement, et
   rejoué après **chaque** étape. Le refactor n'est validé que si la sortie est
   **strictement identique** (déterminisme = règle de design #3).

---

## Cible de structure (proposée — ajustable en début de session)

```
data/code/
  __init__.py
  plants/
    __init__.py        # ré-exporte l'API publique du paquet
    base.py            # GrowthStage, PlantInstance, ConflictNotification,
                       #   PlantBase + familles, STRATE_DEFAULTS, helpers
    genetics.py        # GENE_NAMES, GENE_*/MUTATION_SIGMA, clamp_gene, neutral_genes
    species.py         # espèces cultivées + adventices concrètes
    perennials.py      # PerennialWoody + 5 arbres
    catalogue.py       # PLANT_CATALOGUE, WEED_CATALOGUE, PERENNIAL_CATALOGUE
  world/
    __init__.py        # (idem pour chaque sous-paquet)
    tile.py            # RONDELLE_TYPES, StakeSlot, Tile
  fields/
    __init__.py
    noise.py           # _hash_noise, hash_gauss, climate_stress (foundation pure)
    grids.py           # GridField, DisturbanceField
    light.py           # LightField, solar_slice, _point_in_capsule, constantes astro
    seedbank.py        # SeedBank, GeneStat, constantes archétypes/pool
    ecofields.py       # EcoFields, init_eco, inject_patch, constantes hydro/OM
  sim/
    __init__.py
    effects.py         # (déplacé)
    reproduction.py    # (déplacé)
    seeds.py           # (déplacé)
    succession.py      # EXTRAIT d'engine : choisir_archetype, _succession, _spring_flush
    engine.py          # orchestrateur du tick (allégé)
  main.py
  tests/
    __init__.py
    test_genetique.py
    test_auxiliaires.py
    test_golden.py     # NOUVEAU — garde de non-régression déterministe
```

### Règle de couches (les couches basses n'importent jamais les hautes)

```
plants  ←  fields  ←  sim  ←  engine  ←  main
        (genetics et noise = fondations, importées vers le haut uniquement)
```

- `plants/genetics.py` et `fields/noise.py` sont des **fondations pures** (pas
  d'import interne) → tout le monde peut s'appuyer dessus sans cycle.
- **Point de vigilance n°1** : aujourd'hui `fields.SeedBank.sample_genes` fait un
  `from models import clamp_gene` (import paresseux). Après refactor, `clamp_gene`
  vit dans `plants/genetics.py` ; `fields/seedbank.py` doit pouvoir l'importer
  **sans** créer `fields → plants → fields`. Comme `plants` n'importe pas
  `fields`, l'import direct est sûr — supprimer le `from ... import` paresseux.
- **Point de vigilance n°2** : `__init__.py` de chaque paquet ré-exporte l'API
  publique pour que les sites d'appel restent lisibles (`from plants import Tile`
  plutôt que `from plants.base import Tile`).

### Modèle d'exécution (DÉCIDÉ — 2026-06-03)

Choix le plus professionnel **et proportionné** (moteur de référence autonome,
non distribué via pip, à terme porté en C#) :

- **`__init__.py` dans chaque sous-paquet** (`plants/`, `world/`, `fields/`,
  `sim/`, `tests/`) — paquets explicites + ré-export d'API. Pas de namespace
  packages implicites.
- **PAS de `pyproject.toml`** — aucune publication, `data/code/` est une racine
  de distribution incongrue ; ce serait de la cérémonie inutile (YAGNI). À
  ajouter le jour où un vrai besoin d'installation apparaît, pas avant.
- **Imports absolus** (`from plants import Tile`, `from sim.engine import
  Engine`). `data/code/` n'est **pas** un paquet : c'est la racine d'exécution,
  posée sur `sys.path` par l'interpréteur.
- **Convention de lancement, depuis `data/code/`** :
  - `python3 main.py`
  - `python3 -m tests.test_golden` (et idem pour les autres tests). Le `-m`
    garantit que `sys.path[0]` reste `data/code/` (lancer `tests/test_x.py`
    directement casserait `from plants import …`). À documenter dans le README
    du dossier / l'en-tête des tests.

### Migration incrémentale par shims (technique conseillée)

Pour garder `main.py` et les tests exécutables **à chaque étape** :
1. Créer le nouveau module cible, y **déplacer** le code (couper-coller, pas
   réécrire).
2. Dans l'ancien fichier (`models.py`, `fields.py`…), remplacer le code déplacé
   par un **ré-export** (`from plants.base import *`) — shim temporaire.
3. Rejouer le golden output → doit être identique.
4. Mettre à jour les sites d'appel vers les nouveaux chemins, paquet par paquet.
5. **Supprimer les shims** en toute fin, une fois plus aucun import legacy.

---

## Filet de non-régression — golden output (à faire EN PREMIER)

Avant de déplacer une seule ligne :
1. Écrire `tests/test_golden.py` qui exécute un scénario **fixe et déterministe**
   (seed figé, p. ex. le monde de `main.py` ou un scénario réduit dédié) sur N
   années, concatène le `log` complet, et calcule un **hash** (sha256).
2. Capturer le hash de référence sur **HEAD actuel** (avant refactor) et le
   figer dans le test (ou un fichier `tests/golden_hash.txt`).
3. Après chaque étape de migration : `python3 tests/test_golden.py` doit
   reproduire le **même hash**. Toute divergence = le refactor a changé le
   comportement → à corriger avant d'avancer.

> Choisir un N raisonnable (p. ex. 50 ans sur le monde 9 tuiles, ou 200 ans sur
> 1 tuile) : assez long pour exercer succession + sénescence + reproduction +
> hiver, assez court pour itérer vite. Documenter le scénario exact dans le test.

---

## Volet documentation

### `journal.md` — archiver
- Déplacer les entrées datées **antérieures à la dernière** vers
  `journal_archive/journal_2026-05.md` et `journal_archive/journal_2026-06.md`
  (ou un seul fichier d'archive par mois).
- `journal.md` ne garde que : l'en-tête, l'**index** (avec liens vers les
  archives), et les **2-3 dernières** entrées. Une nouvelle entrée pousse la plus
  ancienne vers l'archive.

### Dette + backlog — source unique
- Extraire la **dette technique consolidée** dans `DETTE.md` (racine).
- Extraire le **backlog des sprints** dans `BACKLOG.md` (racine).
- `journal.md` et `CLAUDE.md` ne **dupliquent plus** ces tableaux : ils y
  **renvoient** (un lien chacun). Fin de la triple maintenance.

### `CLAUDE.md` — alléger sans casser l'autosuffisance
- Retirer le backlog dupliqué (→ `BACKLOG.md`) et la dette (→ `DETTE.md`).
- **Mettre à jour la section « Architecture courante »** et la liste « Source de
  vérité » avec la nouvelle arborescence en paquets.
- Garder intactes la philosophie de design, les mécaniques centrales, les
  garde-fous — c'est le fichier chargé à chaque session, il doit rester complet.

---

## Ordre de travail conseillé

1. **Golden output** (`tests/test_golden.py` + hash de référence sur HEAD).
2. Vérifier git à jour (Nextcloud a déjà perdu des fichiers — cf. garde-fou).
3. **Fondations** : `fields/noise.py`, `plants/genetics.py` (déplacer, shim,
   golden OK).
4. **plants/** : `base.py`, `species.py`, `perennials.py`, `catalogue.py`.
5. **world/** : `tile.py`.
6. **fields/** : `grids.py`, `light.py`, `seedbank.py`, `ecofields.py`.
7. **sim/** : `effects.py`, `seeds.py`, `reproduction.py`, `succession.py`
   (extrait d'`engine`), `engine.py` allégé.
8. Déplacer les tests dans `tests/`, mettre à jour leurs imports.
9. **Supprimer tous les shims**, vérifier golden + les 3 tests + `main.py`.
10. **Docs** : archive journal, `DETTE.md`/`BACKLOG.md`, dédup `CLAUDE.md`.
11. Mettre à jour `journal.md` (nouvelle entrée), mémoire, commit dédié.

---

## À produire à la fin de la session

- [ ] `tests/test_golden.py` + hash de référence figé, vert avant/après
- [ ] `data/code/` réorganisé en paquets `plants/ world/ fields/ sim/`
- [ ] shims temporaires supprimés ; aucun import legacy résiduel
- [ ] succession extraite d'`engine` vers `sim/succession.py`
- [ ] tests déplacés dans `tests/`, imports à jour, 3 tests + golden verts
- [ ] `main.py` tourne, sortie identique au golden de référence
- [ ] `journal_archive/`, `DETTE.md`, `BACKLOG.md` créés ; duplication supprimée
- [ ] `CLAUDE.md` allégé + section architecture/source à jour
- [ ] `journal.md`, mémoire mis à jour ; commit dédié

---

## Critère de fin

L'arborescence en paquets est en place, **aucun shim ne subsiste**, la
succession est isolée d'`engine`, les gros docs sont archivés/dédupliqués, et
surtout le **golden output est rigoureusement identique** à celui d'avant
refactor (déterminisme préservé). Les 3 tests existants passent toujours.

## Garde-fous spécifiques à ce sprint

- **Comportement strictement inchangé** — c'est un refactor, pas une réécriture.
  Couper-coller, pas reformuler la logique. Toute « amélioration » au passage est
  hors périmètre (à noter, pas à faire — cf. CLAUDE.md global #3).
- **Ne rien jeter** : scripts de test gardés, code mort éventuel signalé mais non
  supprimé (sauf shims créés par ce sprint, qui sont à retirer).
- **Déterminisme** = invariant non négociable. Si le golden bouge, on s'arrête.
- **Le portage C# n'est PAS concerné** par ce sprint (dette D24, pas prioritaire).

## Zones blanches à trancher en début de session

- Placement exact des constantes (échelle `PLOT_CM`, gènes) : `plants/genetics.py`
  vs un éventuel `constants.py` partagé.
- Granularité de l'archive journal (un fichier par mois vs un seul `journal_archive.md`).
- Scénario précis du golden (monde 9 tuiles court vs 1 tuile long).

> Le modèle d'exécution (`__init__.py` oui / `pyproject.toml` non / imports
> absolus / lancement `python3 -m`) est **déjà tranché** ci-dessus.
