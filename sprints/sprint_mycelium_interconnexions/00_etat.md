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
| ① | Champ `mycelium` + dynamique (effets §2 DÉBRANCHÉS, repos neutre) | `01_champ_mycelium.md` | ✅ FAIT (golden BIT-IDENTIQUE) |
| ② | Saprophyte (décompo `bois`) + liant (`om_stable`) | `02_saprophyte_liant.md` | ✅ FAIT (golden RE-FIGÉ maîtrisé `9d13d4a7…`) |
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
- smoke `tests/test_golden.py` : `9d13d4a7b88855e6e710dcf5fb22c6471b88a0f30f83d6f40e40b8eb6c8219d4`
  > ② RE-FIGÉ MAÎTRISÉ : `2ab026ad…` (①, bit-identique) → `9d13d4a7…` (②). Dérive
  > **localisée et bornée** : branchement saprophyte (terme `×(1+ALPHA_SAPRO·mycelium)`
  > sur la décompo du SEUL `bois`) + liant (apport TRÈS LENT `LIANT_K·mycelium` à
  > `om_stable`). Preuve d'isolation : `ALPHA_SAPRO=0` & `LIANT_K=0` ⇒ on retrouve
  > EXACTEMENT `2ab026ad…` → toute la dérive vient des deux termes du ②, rien d'autre.
  > Ampleur : `om_stable` moyenne +0.001 (max local 0.40-0.47), mycélium s'installe
  > réellement dans le smoke (max 0.74 sur T1, là où bois humide + om_active). Aucun
  > autre tissu/champ touché.
- population `tests/test_population.py` : `6056713d4dd1e2a79964411961909545433f8513a530a2b39151cbe6aabe471b`
  (INCHANGÉ au ② — rien ne touche la faune).
> Mesurés AVANT toute modif. ① bit-identique (mycélium nul au repos) ; ② RE-FIGÉ
> (cf. supra) ; ③④ re-figent de façon maîtrisée (noter chaque transition ici). ⑤ ~intact.
> NB : 1 check rouge PRÉEXISTANT dans `tests/test_sim_server.py` (« pommier pré-âgé
> — 0 fruits @ S52 »), sans rapport avec ce sprint — baseline, pas une régression.

## REPRISE (démarrage à froid)
**①② FAITS.**
- **①** : champ `mycelium` (`fields/ecofields/mycelium.py`, `tick_mycelium` pur) déclaré
  dans `container.py`, tické dans `sim/engine/boucle.py` (après `tick_structure`, avant
  diffusion), knobs dans `constants.py`. Golden bit-identique `2ab026ad…`.
- **②** : 1er rôle BRANCHÉ. SAPROPHYTE = terme `d *= 1 + ALPHA_SAPRO·mycelium` sur la
  décompo du SEUL tissu `bois` dans `tick_decomposition` (`container.py`, boucle
  parcelles) ; LIANT = apport TRÈS LENT `LIANT_K·mycelium` à `om_stable` en fin de
  `tick_mycelium`. Knobs `ALPHA_SAPRO=1.5` / `LIANT_K=0.0005` dans `constants.py`
  (PLACEHOLDERS). Golden **RE-FIGÉ MAÎTRISÉ** `2ab026ad…` → `9d13d4a7…` (dérive isolée
  aux deux termes, cf. §Hash). Population inchangé `6056713d…`. `test_mycelium.py` 13/13,
  `test_structures.py` 65/65.
**Prochain : `03_mycorhize.md`** (boost `p` borné dans `plant_uptake` + miroir `qi_local` ;
re-figeage golden maîtrisé attendu — l'uptake P là où le réseau touche des racines vivantes).
