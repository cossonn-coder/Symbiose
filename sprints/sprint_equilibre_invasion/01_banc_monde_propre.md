# Tronçon ① — Banc « monde propre » (`config="propre"`) + diag trajectoire outillé

**Prérequis de lecture** : `CLAUDE.md`, `00_etat.md`,
`docs/faune/trophique/conception_equilibre_invasion.md` §8.

## Objectif
Fournir la **fondation de mesure** du sprint : un preset de monde SANS pionnières
ni adventices, et un outil de trajectoire de population promu dans `tools/`. Sert
à observer les cultivées seules (F5) et à mesurer onset/plateau avant/après ②.

## Fichiers à toucher
1. `data/code/tools/simserver/commands.py` — `cmd_init` : nouveau `config="propre"`.
   Monte le MÊME monde que `"full"` (`build_world_full`) MAIS :
   - **vide la seedbank férale** de chaque `EcoField` (les densités d'archétypes
     à 0 — voir `fields/seedbank.py::SeedBank`, mettre les stocks à 0 après
     construction) ;
   - **coupe la succession férale** : ajoute un flag `game_state["feral_off"]=True`
     lu par `sim/succession.py::succession` (return immédiat si le flag est vrai —
     les grains PLANTÉS continuent de lever via `_lever_grains_en_attente`, seule
     la germination spontanée est coupée).
   `"full"` et `"smoke"` inchangés (flag absent → `False` → comportement actuel).
2. `data/code/sim/succession.py` — au début de `succession()`, `if game_state.get(
   "feral_off"): return log` APRÈS la levée des grains plantés (ou avant la boucle
   férale — les grains plantés doivent quand même lever). Vérifier l'ordre.
3. `data/code/tools/diag_population.py` — **créer** (promotion du script ad-hoc) :
   monte un monde via `SimServer.cmd_init` (config au choix `--config full|propre`),
   grandit à `--week N` (défaut 262), logge tous les 26 ticks : N total,
   composition par espèce (top 6), N par tuile (max). Modèle = le script utilisé
   au diagnostic D69 (cf. historique ; sinon reconstruire depuis `_compo_monde` de
   `tools/profile_monde.py`). Hors ligne, lecture seule.

## Golden
**INTACT** (`84d35983…`). Nouveau config + flag optionnel absent des configs
existantes → aucun tick modifié pour smoke/full. Vérifier `python3 -m
tests.test_golden` inchangé + `python3 -m tests.test_population` inchangé.

## NE PAS
- Ne pas toucher aux constantes de calibrage (c'est ②).
- Ne pas planter la démo sud ici (c'est ⑧).
- Ne pas lancer `test_epaisseur_500ans` (interdit, cf. `00_etat`/mémoire).

## Vérif / F5
`python3 -m tools.diag_population --config propre` → N doit rester ≈ constant
(seulement les cultivées de `build_world_full`, pas d'explosion férale).
`--config full` → reproduit la trajectoire du diagnostic (montée à ~1043).
