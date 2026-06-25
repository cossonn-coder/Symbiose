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
| ③ | Mycorhize (boost `p` borné dans `plant_uptake` + miroir `qi_local`) | `03_mycorhize.md` | ✅ FAIT (golden RE-FIGÉ maîtrisé `00c1984a…`) |
| ④ | Faune fongivore + carpophores échantillonnés | `04_faune_carpophores.md` | ✅ FAIT (golden smoke RE-FIGÉ maîtrisé `db5e7c66…` ; population RE-FIGÉE `9ba39ab7…` ; carpophores NEUTRES) |
| ⑤ | Structures niveau tuile + colonisation fongique + bêchage event-driven | `05_structures_tuile.md` | ✅ FAIT (golden + population INCHANGÉS `db5e7c66…`/`9ba39ab7…` — event-driven + structures-vides) |
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
  > ③ RE-FIGÉ MAÎTRISÉ : `9d13d4a7…` (②) → `00c1984a6bdff1c711fd5f5bdca5e1ffed8aaca14f8aa78c2c7999c60a2c6ea0` (③).
  > Dérive **localisée au phosphore prélevé** : la mycorhize amplifie le FLUX de `p`
  > (P SEULEMENT) sous l'empreinte racinaire là où `mycelium` > 0 → la plante puise
  > un peu plus de P → le STOCK résiduel `p` baisse légèrement. Sur les 60 lignes du
  > digest final, SEULES 2 changent, et UNIQUEMENT le champ `p` : T0 0.32→0.312,
  > T1 0.864→0.856. AUCUN autre champ (N, K, microbiome, om_*, soil_memory, vitalité)
  > ni AUCUN attribut de plante ne bouge. Preuve d'isolation : `MYCO_P_BONUS=0` ⇒ on
  > retrouve EXACTEMENT `9d13d4a7…` → toute la dérive vient du seul boost P, rien d'autre.
  > Philo #2 respectée (on amplifie un flux que le sol REND DISPONIBLE, pas la plante ;
  > Liebig `min(besoin,stock)` + fenêtre pH `dispo(ph,"P")` restent limitants).
  > ④ RE-FIGÉ MAÎTRISÉ : `00c1984a…` (③) → `db5e7c660f040e4b084d0fbc76350d25b0dbd169edf15699619c5de9b3ce207f` (④).
  > Le smoke A dérivé (contrairement au « viser inchangé » optimiste du kickoff, qui
  > prévoyait le cas « sinon re-figer, expliqué »). CAUSE : le terme fongivore gonfle
  > le `lombric` (détritivore du sol) là où `mycelium` > 0 ; or `lombric` est lu par la
  > BIOTURBATION du sol (`structure.py`/`container.py` ④d, déjà branché) → un poil plus
  > de décompo de la MO. Dérive **localisée** : sur les 60 lignes ECO, SEULES 2 changent,
  > UNIQUEMENT om_active/om_fresh/organic_mat (T0 om_active 0.527→0.526 ; T1 k 0.219→0.218,
  > om_fresh 0.311→0.310), ampleur ~0.001 (niveau d'arrondi). AUCUN attribut de plante,
  > aucun autre champ. Preuve d'isolation : `FONGIVORE_GAIN=0` ⇒ on RETROUVE EXACTEMENT
  > `00c1984a…` → toute la dérive vient du seul terme fongivore (via lombric→sol), rien
  > d'autre. Philo #2 respectée : flux (mycélium→faune) → biologie (bioturbation), pas un
  > bonus direct. Les CARPOPHORES sont NEUTRES (perception pure, hors digest smoke).
- population `tests/test_population.py` : `6056713d4dd1e2a79964411961909545433f8513a530a2b39151cbe6aabe471b`
  (INCHANGÉ au ②③ — rien ne touche la faune).
  > ④ RE-FIGÉ MAÎTRISÉ : `6056713d…` → `9ba39ab7cf4757b662285f2fd4611d6fe38bf3ebc9d4c3ee5302f4cd3df22876`.
  > Dérive **localisée à 2 guildes** sur les 210 lignes : `T1/lombric` (la cible directe
  > du signal fongivore) + `T0/merle` (son prédateur, propagation boom-bust attendue).
  > Aucune autre guilde ne bouge. Isolation : `FONGIVORE_GAIN=0` ⇒ rien ne change.
  > ⑤ INCHANGÉ (smoke `db5e7c66…` + population `9ba39ab7…` BIT-IDENTIQUES). Tout ⑤ est
  > EVENT-DRIVEN (bêchage au geste) OU confiné aux structures posées. Le smoke et le test
  > population ne POSENT AUCUNE structure → `tick_structures` reste no-op STRICT (boucle
  > vide, invariant préservé) ⇒ la colonisation/maturation/ensemencement mycélien ne
  > tourne jamais hors d'un bac/pile joueur. Le malus `becher` sur `mycelium` n'entre pas
  > dans le tick (geste). Donc AUCUNE dérive — pas de re-figeage.
> Mesurés AVANT toute modif. ① bit-identique (mycélium nul au repos) ; ②③ RE-FIGÉS
> (cf. supra) ; ④ RE-FIGÉS (smoke + population, cf. supra). ⑤ INCHANGÉ (event-driven).
> NB : 1 check rouge PRÉEXISTANT dans `tests/test_sim_server.py` (« pommier pré-âgé
> — 0 fruits @ S52 »), sans rapport avec ce sprint — baseline, pas une régression.

## REPRISE (démarrage à froid)
**①②③④⑤ FAITS — SPRINT MOTEUR CLOS. Reste ⑥ (vue Godot, différé).**
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
- **③** : 2e rôle BRANCHÉ. MYCORHIZE = boost du FLUX prélevable de `p` (P SEULEMENT,
  jamais N/K) dans `plant_uptake` (`container.py`, boucle N/P/K) : `besoin *= 1 +
  MYCO_P_BONUS·mycelium.at_plot(r,c)` quand `nut == "P"`, AVANT le `min(besoin,stock)`
  Liebig. MIROIR read-only dans `qi_local` (`sim/vigueur_plante.py`) : même boost P
  appliqué à `eco.p` avant le `min(n,p,k)`. Knob `MYCO_P_BONUS=0.40` dans `constants.py`
  (PLACEHOLDER, patron `UPTAKE_MICRO_BONUS`), exporté par `fields/ecofields/__init__.py`
  (via `from .constants import *`). Golden **RE-FIGÉ MAÎTRISÉ** `9d13d4a7…` → `00c1984a…`
  (dérive = seul champ `p` qui baisse, cf. §Hash ; isolation `MYCO_P_BONUS=0` ⇒ `9d13d4a7…`).
  Population inchangé `6056713d…`. `test_mycelium.py` 19/19 (6 checks ③ ajoutés, section K).
- **④** : faune fongivore + carpophores. FAUNE = terme ADDITIF `signal_fn=_mycelium_signal`
  (knob `FONGIVORE_GAIN=0.35`, PLACEHOLDER) sur la capacité du `lombric` (détritivore du
  sol, collemboles fongivores) dans `fields/population.py` — patron de l'attraction fruit
  (`_aux_fruit_signal`) ; mycelium=0 ⇒ signal nul. CARPOPHORES = `sample_carpophores(eco,
  seed, week_in_year)` (perception PURE, AUCUN état moteur, `@dataclass Carpophore`),
  échantillonnés du champ `mycelium` quand réseau dense (≥0.30) + sol humide (≥1.5) +
  AUTOMNE (range 27-39, dupliqué pour ne pas importer `sim`) ; zéro RNG (`_hash_noise`,
  salt `0x2AF001`). Exposés au pont (`serialize.py`, bloc `carpophores` CREUX par tuile,
  protocole **0.5.8**). Golden smoke RE-FIGÉ MAÎTRISÉ `00c1984a…` → `db5e7c66…` (dérive
  via lombric→bioturbation, 2 lignes ECO, cf. §Hash) ; population RE-FIGÉE `6056713d…` →
  `9ba39ab7…` (lombric+merle, cf. §Hash). Carpophores NEUTRES (perception). `test_mycelium.py`
  30/30 (11 checks ④, sections L faune + M carpophores). `test_structures.py` 65/65,
  `test_sim_server.py` 205/206 (le 206e = baseline pommier pré-âgé, hors sprint).
  **VUE C# différée au ⑥** (Option B) : seul le moteur Python est branché.
- **⑤** : structures au niveau TUILE + colonisation fongique + bêchage event-driven.
  (A) `Structure` rattachée à la TUILE : `poser_bac`/`poser_pile` refusent EN AMONT un
  2ᵉ du même kind (au plus UN bac + UNE pile par tuile, `compost.py`) ; helper
  `structure_de_tuile(eco, kind)` (ré-exporté `ACT.*`) résout l'unique structure ;
  `composter`/`empiler` acceptent déjà N'IMPORTE QUEL plot de la tuile (plot = simple
  ancrage rendu). (B/C) `Structure.colonisation ∈ [0,1]` (champ neuf sur la dataclass)
  croît au `tick_structures` tant qu'il reste du contenu (`COLONISATION_K`), MODULE la
  maturation (`mult ×= 1 + COLONISATION_MATUR·colonisation`, voie fongique §3.3) ET
  ENSEMENCE `eco.mycelium` au plot d'ancrage (`COLONISATION_SEED`) → la faune fongivore
  ④ (`_mycelium_signal`→lombric) + les carpophores s'installent sur le BAC (§3.4, MÊME
  patron qu'④, zéro terme de faune neuf) ; décline à vide. (D) `becher` retire un quantum
  `BECHAGE_MYCELIUM_MALUS` de `mycelium` au plot (`gestes.py`, EVENT-DRIVEN, miroir EXACT
  de ses malus lombric/microbiome/structure_sol ; clampé ≥0, no-op si réseau nul) ;
  `grelinette` NE TOUCHE PAS `mycelium` (préserve, double peine pédagogique). PAS le champ
  `disturbance` (environnemental, ≠ travail joueur). Knobs `COLONISATION_K=0.10`/
  `COLONISATION_MATUR=1.0`/`COLONISATION_SEED=0.05`/`BECHAGE_MYCELIUM_MALUS=0.5` dans
  `constants.py` (PLACEHOLDERS). Golden smoke + population BIT-IDENTIQUES `db5e7c66…`/
  `9ba39ab7…` (event-driven + structures-vides au smoke). `test_mycelium.py` 34/34
  (section N bêchage), `test_structures.py` 80/80 (16 un-par-tuile, 17 colonisation,
  18 déterminisme). `test_sim_server.py` 205/206 (206e = baseline pommier pré-âgé, hors
  sprint). C# NON concerné (kickoff ⑤ Python pur, vue au ⑥). **SPRINT MOTEUR ①→⑤ CLOS.**
**Prochain : `06_epandre_vue.md`** (`epandre` 2 clics protocole pont + vue Godot :
carpophores, tas colonisé, palette overlay `mycelium`) — **Godot différé** (Option B,
intégration en pause). Seul tronçon restant du sprint.
