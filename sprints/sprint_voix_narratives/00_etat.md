# Sprint VOIX NARRATIVES — état partagé

> **Conception FIGÉE** → source de vérité = `docs/conception/CONCEPTION_VOIX_NARRATIVES.md`
> (la lire d'abord, §0→§8). Ce fichier = état léger + carte des sous-sprints, mis à
> jour en fin de **chaque** tronçon. Boucle projet : `0N` → coder → vérifier golden
> (doit rester INTACT) → MAJ ce fichier → commit → `/clear` → `0N+1`.

## En une phrase
On implémente en **Python pur** les 4 voix narratives (carnet, encyclopédie, pages
secrètes, magazine) comme **lecteurs read-only** par-dessus un **ledger d'événements
partagé** (`sim/journal.py`), lui-même alimenté **hors tick** par le driver — donc le
**golden écologique reste INTACT à chaque tronçon** (zéro effet dans le tick).

## Invariant GOLDEN (vaut pour TOUS les tronçons)
- `tests/test_golden.py` (smoke `tests/golden_hash.txt`) **et** `tests/population_hash.txt`
  **doivent rester bit-identiques** du début à la fin. Le golden tourne le moteur
  *sans joueur* → aucune clé `journal`/`pages` → no-op strict (miroir de `maitrise`/
  `vigueur`). **Si le golden bouge, c'est un BUG (fuite dans le tick), STOP** — ne
  jamais re-figer.
- `tests/test_maitrise_detection.py` doit aussi rester **vert** après ① (refactor pur).

## Décisions structurantes (détail dans le doc)
- **Substrat = ledger partagé** : un seul flux d'`Evenement` typés parsé depuis le
  `log` du tick. Extraction de `_evenements()` (`sim/maitrise_detection.py`) vers un
  module commun **`sim/evenements.py`** (① refactor pur).
- **État joueur opt-in** : `gs["journal"][player]={"entries":[…],"resume":{…}}` et
  `gs["pages"][player]=set(...)`. Pas de joueur ⇒ pas de clé ⇒ no-op golden.
- **Point d'entrée hors tick** : `journal.consigner(gs, player, log, semaine)` appelé
  par le DRIVER **après** `tick_semaine()` et **avant** que le serveur ne vide le log
  (`tools/simserver/commands.py::cmd_step_week`, ~L132-133). `engine` ne l'importe
  JAMAIS.
- **Encyclopédie 3 niveaux** sur paliers 1/2/3 (A) ; **carnet** bascule interprétatif
  au **palier 3 du concept** (B, `SEUIL_CARNET=3`) ; **magazine** sœurs au **palier 3
  famille** (C). Tout lit l'état `maitrise` déjà implémenté (`sim/maitrise.py`).
- **Pages = lore pur, ZÉRO effet mécanique**, 3 robinets (hasard/récompense/fouille).

## Carte des sous-sprints (6, ordre = dépendances)
| # | Sujet | Kickoff | État |
|---|-------|---------|------|
| ① | Extraire `sim/evenements.py` (refactor pur) + élargir le parseur | `01_evenements.md` | ⬜ à faire |
| ② | Ledger `sim/journal.py` + `consigner` + câblage driver | `02_journal.md` | ⬜ à faire |
| ③ | Carnet (`carnet_lire`, `CONCEPT_DE`, gabarits 2 registres) + D43 | `03_carnet.md` | ⬜ à faire |
| ④ | Encyclopédie (`encyclopedie_index`/`_lire`, fiche tronquée) | `04_encyclopedie.md` | ⬜ à faire |
| ⑤ | Pages secrètes (`pages_trouvees`/`reveler_page`, 3 robinets) | `05_pages.md` | ⬜ à faire |
| ⑥ | Magazine (`magazine_offres`/`acheter_au_magazine`) | `06_magazine.md` | ⬜ à faire |

Dépendances : ① avant tout ; ② dépend de ① ; ③④⑤⑥ dépendent de ② mais sont
indépendants entre eux (déroulés en série pour un golden vérifié à chaque cran).

## Conventions
- Source de vérité = Python `data/code/`. Lancement depuis `data/code/`
  (`python3 main.py`, `python3 -m tests.test_golden`, `python3 -m tests.test_population`,
  `python3 -m tests.test_maitrise_detection`).
- Couches : `evenements`/`journal` sont au niveau `sim`, AU-DESSUS du tick (comme
  `maitrise_detection`, `vigueur`). `engine`/`fields`/`plants` ne les importent jamais.
- **Corpus = livrable éditorial** (doc §5/§6/§7) : recopier fidèlement les gabarits/
  fiches/pages du doc dans des modules de données Python. Ne pas réinventer le texte.
- Placeholders calibrage → **D12.4** : `JOURNAL_MAX=200`, `COUT_MAGAZINE` (élevé),
  `SEUIL_CARNET=3`. Knobs nommés en tête de module.
- Tout garder (scripts de mesure inclus). Un fichier à la fois sauf synchro cohérente
  avant commit. Français + commentaires pédagogiques au cœur des fichiers.

## Hors périmètre (renvoyé, cf. doc §4)
UI Godot des 4 voix (coffret grenier, kiosque magazine, pages du carnet) = **dette
D24** ; protocole pont/commandes serveur pour exposer ces lectures à Godot = D24 aussi ;
D15 (extension terrain) ; calibrage numérique D12.4 ; marqueurs rares bouture/oiseau/
vent (robinet *hasard* s'ancre provisoirement sur `_hash_noise` au passage de saison).

## Dépendance connue à signaler
La **détection de maîtrise** (`maitrise_detection.detecter`) n'est **pas encore câblée**
dans la boucle serveur (elle existe + est testée en isolation). Sans elle, les paliers
ne progressent pas en jeu réel → carnet/magazine restent en mode initial. Le câblage de
`detecter` (symétrique de `consigner`) est du ressort de **D12**, pas de ce sprint —
mais comme les deux hooks sont jumeaux et vont au même endroit (après le tick, avant le
vidage du log), **② peut les câbler ensemble** si trivial. À signaler à Nico, ne pas
forcer (ça ne touche pas le golden, qui tourne hors serveur).
