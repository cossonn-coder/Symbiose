# ② Ledger `sim/journal.py` + `consigner` + câblage driver

> Lire d'abord `00_etat.md` + `docs/narration/voix/conception_voix_narratives.md` (§1.3).
> Tronçon **substrat partagé** : on crée le ledger d'événements opt-in et son point
> d'entrée **hors tick** appelé par le DRIVER. Dépend de ① (`sim.evenements`). Premier
> geste : RE-MESURER les hashs golden.

## Objectif
Créer `sim/journal.py` : un **ledger append-only par joueur**, alimenté **hors tick**
par `journal.consigner(gs, player, log, semaine)` (qui lit `evenements.evenements(log)`),
câblé dans le driver serveur **après** le tick et **avant** le vidage du log. État
**opt-in** → pas de joueur = pas de clé = **no-op golden** (miroir de `maitrise`/`vigueur`).

## À faire

### A. État + `ensure_player` (`sim/journal.py`)
- État : `gs["journal"][player] = {"entries": [...], "resume": {...}}` (doc §1.3).
- `ensure_player(gs, player)` **opt-in** (miroir de `maitrise.ensure_player_maitrise`) :
  crée la clé seulement si appelée. Le golden ne l'appelle jamais → aucune clé.
- Entrée = `{"semaine": int, "zone": (tile_id, r, c), "kind": str, "cause": str|None,
  "espece": str|None}`.
- `entries` **append-only borné** à `JOURNAL_MAX = 200` (placeholder D12.4, knob en tête
  de module). Au-delà : **replier la plus ancienne** dans `resume[(kind, cause)] += 1`
  (compteur agrégé) avant de l'enlever d'`entries`.

### B. `consigner(gs, player, log, semaine)` (`sim/journal.py`)
- `ensure_player(gs, player)` ; pour chaque `Evenement` de `evenements.evenements(log)` :
  construire l'entrée et l'appender (avec bornage A).
- **PUR au sens golden** : lit le `log`, n'avance aucun tick, ne touche aucun champ
  écologique. Aucun RNG.

### C. Câblage driver (`tools/simserver/commands.py::cmd_step_week`)
- ~L132 : APRÈS `self.engine.tick_semaine()` et **AVANT**
  `self.engine.game_state["log"].clear()` (L133), appeler
  `journal.consigner(gs, gs["current_player"], gs["log"], semaine)`.
- Le serveur enregistre déjà un joueur (`current_player="joueur_1"`, `V.ensure_player`)
  → en jeu réel le ledger se remplit ; le golden tourne **hors serveur** → intact.

## Couches
`sim/journal.py` au niveau `sim`, au-dessus du tick. Il importe `sim.evenements` (①).
**`engine` ne l'importe JAMAIS** : c'est le DRIVER (`tools/simserver`) qui appelle
`consigner`, exactement comme le hook hors tick décrit au §1.3.

## Définition de done
- `sim/journal.py` créé (`ensure_player`, `consigner`, `JOURNAL_MAX`, bornage→`resume`).
- Câblage `cmd_step_week` en place (entre tick et `log.clear()`).
- `tests/test_journal.py` (NOUVEAU) : **sans joueur → aucune clé `journal`** (preuve
  no-op golden) ; avec joueur → les entrées s'accumulent à partir d'un log jouet ;
  bornage `JOURNAL_MAX` → la plus ancienne se replie dans `resume[(kind,cause)]`.
- **Golden INTACT** : `tests/test_golden.py` + `tests/population_hash.txt` bit-identiques
  (le golden ne crée pas de joueur `journal`). Si ça bouge → fuite dans le tick, STOP.
- MAJ `00_etat.md` (② → FAIT) puis commit.

## Pièges
- **Opt-in strict** : ne JAMAIS créer `gs["journal"]` au niveau du tick/engine. Seul
  `consigner` (appelé par le driver) crée la clé. Sinon le golden bouge.
- Le câblage doit être **avant** `log.clear()` (L133) — après, le log est vide.
- ⚠ **Signaler à Nico** (cf. `00_etat.md` « dépendance connue ») : `maitrise_detection.detecter`
  n'est **pas câblé** dans la boucle serveur non plus. C'est le **jumeau** de `consigner`
  (même endroit : après tick, avant `log.clear()`). ② **peut** le câbler dans la foulée
  si c'est trivial (les paliers progresseraient alors en jeu réel) — sinon **laisser à
  D12**, ne pas forcer. Ça ne touche pas le golden (qui tourne hors serveur). **Mentionner
  le choix fait dans `00_etat.md`.**
