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
| ① | Extraire `sim/evenements.py` (refactor pur) + élargir le parseur | `01_evenements.md` | ✅ FAIT |
| ② | Ledger `sim/journal.py` + `consigner` + câblage driver | `02_journal.md` | ✅ FAIT |
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

## Avancement / REPRISE

**① FAIT** (refactor pur, golden INTACT) :
- Créé `data/code/sim/evenements.py` (module PUR, niveau `sim`, 119 ldc) : type
  partagé `Evenement(kind, tile_id, pos, espece, cause)` + **deux API** :
  - `_evenements(log)` — déplacé TEL QUEL depuis `maitrise_detection` (kinds
    `avance/stagne/repro`), ré-importé par `maitrise_detection` → comportement
    inchangé (choix : NE PAS renommer les kinds historiques, sinon `detecter()` +
    `test_maitrise_detection[8]` cassent ; refactor strictement pur).
  - `evenements(log) -> list[Evenement]` — NOUVEAU, élargi pour le carnet ② :
    kinds `germination/stagnation/reproduction/mort/nouaison/abscission/ravageur`.
- `maitrise_detection.py` : regex/`_CLE_DE_NOM`/`_raison_stagnation`/`_evenements`
  RETIRÉS (déplacés), réimport `from sim.evenements import _evenements`.
  `_CLE_DE_CLASSE` reste (naturalisation férale).
- Élargissements parseur : **`🌊 noyé`** (stagnation, absente de l'ancien parseur),
  morts `🪦` (sénescence/asphyxie) + `✗` (conflit), `🍎 Nouaison`, `🍂 Abscission`,
  `🐛` ravageur (aléa sans pos/espèce). **Disambiguation** 🍂 (Abscission ≠
  Nécromasse/Chute fruit), 🍎 (Nouaison ≠ header Récolte), ❄ (stagne froid ≠
  header gel).
- **TODO nommés** (pas de marqueur source dans le log → non parsés, conforme
  kickoff) : `floraison` (header `🌸` seul, pas de ligne per-plante), `acclimatation`
  (signe de rendu `sim/semiologie.py`, jamais émis au log), mort `gel`/annual/
  monocarpie (cause non distinguable proprement). À brancher si le moteur émet
  un jour ces marqueurs.
- Tests : `tests/test_evenements.py` NOUVEAU (18/18 — parité historique +
  kinds élargis + disambiguation). `test_maitrise_detection` 20/20 vert.
  **Golden `db5e7c66…` + population `9ba39ab7…` bit-identiques** (inchangés).

**② FAIT** (ledger hors tick, golden INTACT) :
- Créé `data/code/sim/journal.py` (module niveau `sim`, ~50 ldc) : `JOURNAL_MAX=200`
  (knob D12.4 en tête), `ensure_player(gs, player)` OPT-IN (miroir de
  `maitrise.ensure_player_maitrise`), `consigner(gs, player, log, semaine)` qui lit
  `evenements.evenements(log)` (① élargi) et appende des entrées
  `{semaine, zone, kind, cause, espece}`. `zone = (tile_id, r, c)` ou `(tile_id,)` si
  l'événement n'a pas de pos (ravageur de saison). Bornage `_appender` : au-delà de
  `JOURNAL_MAX`, la plus ancienne se replie dans `resume[(kind, cause)] += 1` (FIFO).
  PUR : aucun RNG, aucun champ écolo touché.
- Câblage driver `tools/simserver/commands.py::cmd_step_week` : import
  `from sim import journal as J` ; appel `J.consigner(gs, gs["current_player"],
  gs["log"], gs["week"] - 1)` APRÈS `tick_semaine()` et AVANT `gs["log"].clear()`.
  `week` est déjà incrémenté par le tick (boucle.py:422) → la semaine simulée est
  `week - 1`. Le serveur a déjà un joueur (`current_player="joueur_1"`) → ledger se
  remplit en jeu réel ; golden hors serveur → aucune clé `journal` → intact.
- Tests : `tests/test_journal.py` NOUVEAU (15/15 — opt-in no-op, accumulation datée +
  isolation par avatar, bornage→resume). `test_evenements` 18/18, `test_maitrise_detection`
  20/20 verts. **Golden `db5e7c66…` + population `9ba39ab7…` bit-identiques** (inchangés).

**DÉCISION `detecter` : NON câblé** (choix assumé, signalé à Nico). `maitrise_detection.detecter`
a la même signature que `consigner` et irait au même endroit (trivial à brancher), MAIS
ce n'est PAS neutre côté gameplay : il crédite des preuves et fait progresser les paliers
en jeu réel, ce qui pilote ensuite carnet/encyclopédie/magazine. C'est une décision D12
que Nico doit prendre sciemment, pas un effet de bord du tronçon « ledger ». Le golden
n'est pas concerné (tourne hors serveur), donc rien ne presse. À trancher quand Nico veut
activer la progression de maîtrise en F5.

**PROCHAIN = ③** (`03_carnet.md`) : carnet (`carnet_lire`, `CONCEPT_DE`, gabarits 2
registres §5) + D43. Lecteur read-only par-dessus le ledger ②.
