# Tronçon ① — Infrastructure : paquet `bancs/` + registre + 1er banc bout-en-bout

> Sprint « bancs d'essai ». État partagé : `00_etat.md` (lire d'abord).
> Ce tronçon POSE LE PATTERN que ②③④ réutilisent : paquet de fabriques, registre,
> branchement `cmd_init`, cadre d'oracle. Il livre **un banc complet de bout en
> bout** (`secheresse_sable`) pour valider toute la chaîne init→step→signe.
> **Golden NEUTRE attendu** : rien n'est branché pour `smoke`/`full`.

## Objectif
À la fin : `init config="secheresse_sable"` monte un monde minimal où une plante
soumise à un déficit hydrique soutenu finit par montrer le signe `secheresse`, et
un test `tests/bancs/` l'asserte automatiquement. Le golden reste `2ab026ad…`.

## Périmètre

### 1. Paquet `data/code/bancs/`
- `bancs/base.py` — helpers communs réutilisés par tous les bancs :
  - `build_banc_tile(name, soil, rows, cols, ox, oy, **champs)` — variante de
    `main.build_tile` (`main.py:54`) qui laisse forcer n'importe quel champ éco
    (`humidite`, `ph`, `n`/`p`/`k`, `microbiome`…) via `eco.<field>.set` /
    `init_eco` (cf. `fields/ecofields/container.py:852`). Sert de brique unique.
  - `monde(tiles, ecos, house=None, banque=None)` — emballe le tuple de retour
    standard `(tiles, ecos, house, banque)` avec défauts (`House()`, banque vide).
  - (préparer pour ③④) `force_memoire(plant, nom, valeur)` et `vieillir(plant,
    ans)` — forçage déterministe d'un état pré-chargé (accélération). Poser au
    moins la signature ici si non utilisé par ce banc.
- `bancs/climatique.py` — `secheresse_sable()` : 1 tuile `sable` petite (ex.
  8×8), `humidite` initiale BASSE, une plante non xérophile (ex. `Basil` ou
  `Tomato`) posée, **aucun arrosage**. Le déficit s'installe au fil des semaines
  (météo déterministe) → `drought_memory` monte → signe `secheresse`.
- `bancs/__init__.py` — registre :
  ```python
  from .climatique import secheresse_sable
  BANCS = {"secheresse_sable": secheresse_sable}
  ```
  (②③④ ajoutent leurs entrées ici.)

### 2. Branchement `cmd_init` (`tools/simserver/commands.py:45`)
Après les cas `smoke`/`full`, AVANT le `else` d'erreur :
```python
from bancs import BANCS
...
elif config in BANCS:
    tiles, ecos, house, banque = BANCS[config]()
```
Adapter `game_state` : `player_seed_bank = banque` (ou `_banque_initiale("smoke")`
si la fabrique renvoie `None`). **Ne pas toucher** les branches `smoke`/`full`.

### 3. Cadre d'oracle `data/code/tests/bancs/`
- Identifier d'abord l'**API de lecture des signes** : `sim/semiologie.py`
  (fonction d'agrégation ~l.199-215 qui renvoie la liste `{cause, intensity}`
  d'une plante). Repérer le point d'appel réel (probablement dans le snapshot /
  `serialize.py`) pour lire EXACTEMENT ce que la vue reçoit.
- `tests/bancs/oracle.py` — helper `run_banc(nom, semaines)` (monte le monde via
  la même fabrique, fait tourner N `step_week`, renvoie l'état) +
  `signes_du_plot(eco/tile, plant)` → set des causes. Déterministe.
- `tests/bancs/test_climatique.py` — `test_secheresse_sable()` : après N semaines
  (calibrer N pour franchir le seuil), `assert "secheresse" in signes(plante)`.

## Knobs
Humidité initiale du sable, taille tuile, espèce, N semaines — valeurs de départ
raisonnables, commentées. Viser un oracle qui passe en **< ~15 semaines** (banc
rapide à observer au F5).

## Vérifs
- `python3 -m tests.test_golden` depuis `data/code/` → **hash inchangé**
  `2ab026ad…`. Si dérive : une fabrique a touché une couche partagée (un import
  à effet de bord, une mutation d'un objet du catalogue) — STOP.
- `python3 -m tests.bancs.test_climatique` (ou via le runner du dépôt) → vert.
- `python3 tools/sim_server.py` ou un appel scripté : `init config="secheresse_sable"`
  répond `ok` + `world` (vérifie le branchement de bout en bout).
- Garde-fou taille (`tools/compte_ldc.py`) : modules `bancs/*` < ~350 lignes pur.

## Sortie
MAJ `00_etat.md` (① clos, hash golden confirmé NEUTRE, journal : pattern posé,
API de lecture des signes identifiée — la NOTER pour ②③④). Commit. `/clear` avant
`02_edaphique.md`.
