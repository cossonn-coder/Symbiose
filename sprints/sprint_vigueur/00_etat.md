# Sprint implémentation Vigueur (D11) — état partagé

> **État léger, mis à jour en fin de chaque sous-sprint.** La spec de référence
> figée est [`data/code/CONCEPTION_VIGUEUR.md`](../../data/code/CONCEPTION_VIGUEUR.md)
> (Sprint conception Vigueur, 2026-06-04). Couvre **D11** (+ prépare D19/D22b/D29/D30).
>
> Boucle : lancer `0N` → travailler → **vérifier le golden écolo (PASS sans
> `--capture`)** → mettre à jour ce fichier → commit → `/clear` → lancer `0N+1`.

## Propriété clé de tout le sprint

Le golden ÉCOLOGIQUE (`tests/test_golden.py`, hash `ee79dd66…f0f947`) est une
succession spontanée pure : **aucune action joueur**. La couche Vigueur joueur
est **event-driven, au-dessus du tick**. Donc le golden écolo **ne doit PAS être
re-figé** par ce sprint. **Si un hash bouge, c'est un bug** (quelque chose a fui
dans le tick déterministe). Contraste avec le sprint météo (qui modifiait de
vraies voies écologiques et re-figeait).

## Où on en est

- **Sous-sprint 1 (couche Vigueur joueur) : FAIT.** Module neuf `sim/vigueur.py`
  (état `game_state["vigueur"][player] = {courante, max_base}` ; `vigueur_max`,
  `regen_rate`, stub `palier_bonus()=1.0` ; `tick_player_vigueur` régen
  plafonnée + `refill_saison`). Hook **gardé** en fin de `Engine.tick_semaine`
  (`if "vigueur" in game_state` → no-op strict, golden écolo intact). Golden
  JOUEUR dédié `tests/test_vigueur.py` (10/10, hash `e63b9d7f…fb621`,
  `vigueur_hash.txt`). Golden écolo **inchangé** (PASS sans `--capture`). Reste 2/3/4.
- **Sous-sprint 2 (coûts d'action) : FAIT.** Primitives `spend`/`gain` ajoutées à
  `sim/vigueur.py` (`spend` renvoie un **ratio d'effort** ∈ [0,1], draine
  `min(cost, courante)`, pas de dette). Nouveau module `sim/actions.py` :
  constantes de coût (`NUL/FAIBLE=5/MODERE=15/ELEVE=30/URGENCE_MULT=1.5`),
  `HARVEST_VIGUEUR_COST=FAIBLE` (le `=0` mort **supprimé** de `engine.py`),
  `HARVEST_GAIN_FULL=15`, helper `maturite`, et 3 actions sur le vivant :
  `recolter` (graduée, net+ sur mûr, Qi→joueur via `harvested=True`, plante
  vivante, gain×ratio), `deraciner` (binaire tout-ou-rien, ÉLEVÉ, Qi→sol via
  `harvested=False`, échoue à vide), `ecraser` (binaire, **comptabilité Vigueur
  seule** — pas d'entité nuisible encore, valide `× URGENCE`). Golden joueur
  étendu (A5–A9) → **32/32**, hash trajectoire passive **inchangé**. Golden écolo
  **inchangé** (`ee79dd66…f0f947`). Reste 3/4.
- **Sous-sprint 3 (façade `vigueur_plante`) : FAIT.** Module neuf
  `sim/vigueur_plante.py` — façade PURE read-only `vigueur_plante(plant, eco) =
  sante × maturite × qi_local × gene("vigueur")`. `sante = health/3` (D27) ;
  `maturite` **déplacé d'`actions.py` ici** (mutualisé, `actions.py` le réimporte) ;
  `qi_local` lit `fertilite`/`microbiome` sous `root_plots` en **miroir de
  `plant_uptake`** (`min(1,champ/3) × (1+micro×UPTAKE_MICRO_BONUS)`, moyenne
  clampée [0,1], `at_plot` renvoie 0 hors grille) ; gène **enveloppé tel quel**
  (D22b stabilisé, §6). Descripteur diégétique qualitatif `decrire_vigueur`
  (imperceptible/chétif/vigoureux/éclatant, philo #5, seuils provisoires). Golden
  joueur étendu (C1–C6) → **51/51**, trajectoire passive **inchangée**. Golden
  écolo **inchangé** (`ee79dd66…f0f947`) — jamais appelé dans le tick. Reste 4
  (optionnel, tandem D19).
- Conception **figée** (`CONCEPTION_VIGUEUR.md`).

## Découpage (suit CONCEPTION_VIGUEUR.md §8)

| # | Objet | Impact golden écolo |
|---|---|---|
| 1 | **Couche Vigueur joueur** : état `game_state["vigueur"]`, cycle (régen passive plafonnée, plein à la saison), interface `vigueur_max`/`regen_rate` + stub `palier_bonus`. Golden joueur créé. | **neutre** (no-op gardé) |
| 2 | **Coûts d'action** : `HARVEST_VIGUEUR_COST` réel ; déracinage / écraser nuisible → dépense ; flag `harvested` → gain joueur (Qi vers le joueur, §4). | **neutre** |
| 3 | **Façade `vigueur_plante`** read-only (`sante × maturite × qi_local × gène`) + lecture diégétique carnet/encyclopédie. Aucun pilotage de sim. | **neutre** |
| 4 | **(optionnel, tandem D19)** action « manger » : organes consommables → gain ∝ maturité. | **neutre** |

## Décisions structurelles actées (avec Nico, 2026-06-04)

- **Emplacement du cycle** : hook gardé DANS l'engine (`tick_player_vigueur` /
  `refill_saison` appelés en fin de `tick_semaine`, gardés par `"vigueur" in
  game_state`). Régen au rythme du tick, fidèle à la spec §2.1. Le golden écolo,
  sans clé `vigueur`, est un no-op strict.
- **Test joueur** : hash déterministe (même patron que `test_golden` /
  `test_signes`), `vigueur_hash.txt` auto-capturé, `--capture` pour re-figer.
- **Opt-in** : `ensure_player(game_state, player)` crée la clé `vigueur`. Tant
  qu'aucun joueur n'est enregistré, la couche n'existe pas.

## Hors périmètre (ce sprint NE fait PAS)

- **Paliers de maîtrise** (contenu réel de `palier_bonus`) — gated D12.
- **Magazine de botanique** — gated D13.
- **Modèle d'organes consommables** — D19 (le sous-sprint 4 ne fixe que la
  comptabilité Vigueur du gain).
- **Auxine / dominance apicale** (réponse riche à `tailler`) — D29, sprint dédié.
- **Champ structure/compaction du sol** (bonus grelinette) — D30, à trancher.
- **Portage C#** — D24.
