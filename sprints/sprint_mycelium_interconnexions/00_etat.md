# Sprint mycélium & interconnexions — état partagé

> **Conception FIGÉE** → source de vérité = `docs/conception/CONCEPTION_MYCELIUM_INTERCONNEXIONS.md`
> (la lire d'abord). Ce fichier = état léger + carte des sous-sprints. Mis à jour
> en fin de **chaque** sous-sprint. Boucle projet : `0N` → coder → vérifier/re-figer
> golden (maîtrisé) → MAJ ce fichier → commit → `/clear` → `0N+1`.

## En une phrase
On promeut le **mycélium** en acteur de plein droit : un **champ scalaire**
`mycelium` dans `EcoFields` (patron `microbiome`) qui pousse sur le bois humide non
travaillé, **décompose le bois** (saprophyte), **lie le sol** (`om_stable`), **se
relie aux racines vivantes** pour faire passer le **phosphore** (mycorhize / wood-
wide-web) et **nourrit la faune** fongivore ; bac/pile passent au **niveau tuile**
et se font **coloniser** par le champignon ; **bêcher casse le réseau**, grelinette
le préserve.

## Décisions structurantes (détail dans le doc de conception)
- **UN seul champ** `mycelium` (`GridField max_val=1.0`, granularité plot, zéro RNG)
  rend les DEUX services (saprophyte + mycorhizien). Distinction au point de
  branchement (décompo vs uptake), pas dans l'état. Décision figée (i).
- **Mycorhize boost `p` SEULEMENT** (pas N/K), borné (`MYCO_P_BONUS`, patron
  `UPTAKE_MICRO_BONUS`). Décision figée (ii). Aide à PUISER, ne déverrouille pas la
  fenêtre pH (philo #2).
- **Carpophores = perception** : sprites échantillonnés déterministes (patron
  `sample_sprites`), DÉRIVÉS du champ, aucun état propre → **golden-neutres**.
- **Travail du sol = EVENT-DRIVEN** : `becher` retire un quantum `mycelium`
  (miroir de son malus microbiome/lombric/structure, `gestes.py:407`) ; `grelinette`
  préserve (`gestes.py:428`). ⚠️ **PAS** le champ `disturbance` (environnemental,
  bruit de succession — ≠ travail joueur).
- **Distinction stricte du pathogène** : ce mycélium est BÉNÉFIQUE (saprophyte +
  mycorhizien). Les maladies fongiques M5 (`sim/effects/perturbations.py`) restent
  un acteur DISTINCT et inchangé. Aucun couplage.
- **Re-figeage golden LARGE annoncé et MAÎTRISÉ** : ② décompo, ③ uptake, ④
  population. ① localisé (présence du champ). ⑤ event-driven (~intact). Chaque
  dérive ANALYSÉE + expliquée au commit. Philo #3 : zéro RNG, knobs explicites.

## Carte des sous-sprints (6, ordre = impact golden croissant)
| # | Sujet | Kickoff | État |
|---|-------|---------|------|
| ① | Champ `mycelium` + dynamique (effets §2 DÉBRANCHÉS, repos neutre) | `01_champ_mycelium.md` | À FAIRE |
| ② | Saprophyte (décompo `bois`) + liant (`om_stable`) | `02_saprophyte_liant.md` | À FAIRE |
| ③ | Mycorhize (boost `p` borné dans `plant_uptake` + miroir `qi_local`) | `03_mycorhize.md` | À FAIRE |
| ④ | Faune fongivore + carpophores échantillonnés | `04_faune_carpophores.md` | À FAIRE |
| ⑤ | Structures niveau tuile + colonisation fongique + bêchage event-driven | `05_structures_tuile.md` | À FAIRE |
| ⑥ | `epandre` 2 clics + vue Godot (carpophores, tas colonisé, overlay) | `06_epandre_vue.md` | À FAIRE (Godot différé) |

## Conventions
- Source de vérité = Python `data/code/`. Lancement depuis `data/code/`
  (`python3 main.py`, `python3 -m tests.test_golden`, `python3 -m tests.test_population`).
- Couches : `mycelium` est un champ de `fields/ecofields/` ; sa dynamique tique dans
  la boucle (`sim/engine/boucle.py`). `fields` n'importe jamais `sim`/`world`.
- Golden : à chaque tronçon qui re-fige, **mesurer le nouveau hash, l'ANALYSER**
  (dérive attendue + localisée) avant de le re-figer. Noter l'ancien → nouveau dans
  ce fichier. ① doit rester proche du repos (champ nul partout au smoke → idéalement
  bit-identique ; si dérive, l'expliquer).
- Knobs explicites (valeurs de départ = placeholders, calibrage post-test) — philo
  #3, déterminisme (zéro RNG, ordre d'itération stable).
- Tout garder (scripts de mesure inclus). Un fichier à la fois sauf synchro
  cohérente avant commit.

## Hash golden de référence (mesurés au démarrage, 2026-06-25)
- smoke `tests/test_golden.py` : `2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646`
- population `tests/test_population.py` : `6056713d4dd1e2a79964411961909545433f8513a530a2b39151cbe6aabe471b`
> Mesurés AVANT toute modif. ① vise idéalement bit-identique (mycélium nul au repos) ;
> ②③④ re-figent de façon maîtrisée (noter chaque transition ici). ⑤ ~intact.
> NB : 1 check rouge PRÉEXISTANT dans `tests/test_sim_server.py` (« pommier pré-âgé
> — 0 fruits @ S52 »), sans rapport avec ce sprint — baseline, pas une régression.

## REPRISE (démarrage à froid)
Rien de fait. Lancer `01_champ_mycelium.md`. Tout le moteur édaphique existe déjà
(`EcoFields` = `fields/ecofields/container.py`, boucle = `sim/engine/boucle.py`).
Le sprint AJOUTE un champ et le branche progressivement, en re-figeant le golden de
façon maîtrisée à chaque rôle.
