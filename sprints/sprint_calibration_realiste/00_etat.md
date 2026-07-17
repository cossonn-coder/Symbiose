# 00_etat — sprint CALIBRATION RÉALISTE (P1)

**Statut : CONCEPTION FIGÉE (2026-07-17), prête pour `/sprint-auto`. 3 tronçons.**
Doc : `docs/conception/CONCEPTION_CALIBRATION_REALISTE.md`. Kickoffs 01/02/03.
Source : `BRIEF_CHAMPS_CONCEPTION.md` P1 (verdicts 1 + 5) + `audit_champs.md`.
Date d'ouverture : 2026-07-17.

## Carte des tronçons
- **① 01_banc_metrique_vitalite_vue.md** — ✅ FAIT (2026-07-17). `tools/banc_calibration.py`
  créé + métrique vitalité SOL réalignée (VUE seule). Golden re-figé LOCALISÉ (SEUL le
  champ "vitalite" des 2 lignes ECO a bougé, diff vérifié). Nouveau hash + poids ci-dessous.
- **② 02_normalisateurs_effet_tick.md** — ✅ FAIT (2026-07-17). uptake:63 + maladie
  sol:121 + qi_local microbiome (vigueur_plante:82) réalignés `/3.0`→`/MICROBE_EFFECT_REF`.
  Golden re-figé LARGE (rétroaction rhizosphère rouverte). Nouveau hash + note ci-dessous.
- **③ 03_vue_godot_overlay_banc.md** — overlay F6 microbiome (FixMax 3→0.6) + overlay
  vitalité sol + banc F5. Golden INTACT.

## Objet
Couple les verdicts 1 (microbiome tient-il en nominal ?) et 5 (recalibrer
l'échelle `vitalite`). But : que le sol vivant se LISE et FONCTIONNE à sa vraie
plage d'opération.

## Découvertes empiriques (banc de mesure, scratchpad/bench.py + bench2.py)
Mesuré sur monde smoke DENSE (2×6×8) ET monde LÂCHE (2×12×16, même nb de plantes),
10 ans, seed 42 :

1. **DEUX « vitalités » conflées dans l'audit :**
   - `plant.vitalite` (santé plante) — SAINE dans les deux mondes (0.5–0.75 moy,
     médiane 0.7–1.0). N'est JAMAIS 0.02. Poids trophique réel (`resources.py`
     ×6), nourrit les exsudats (`croissance.py:228`), **hashée au golden**.
   - `eco.vitalite` (métrique SOL, snapshot "vitalite") — ~0.01 dans les deux
     mondes, **plus basse en lâche**. **AUCUN consommateur dans le tick** (grep
     vide) → VUE pure. Le « 0.02 » de l'audit = TOUJOURS cette métrique sol.

2. **Le « microbiome décroche » n'est PAS un artefact du monde smoke.** Il décline
   0.34→0.02 en DENSE comme en LÂCHE. Abaisser `MICROBE_FOOD_REF` 1.0→0.15 (famine
   quasi off) ralentit mais n'arrête pas (an 10 : 0.019→0.030). C'est le champ qui
   RELAXE depuis son semis généreux (0.3) vers son équilibre bas réel, fixé par
   l'apport d'exsudats limité par la lumière (~0.18).

3. **RACINE COMMUNE = mismatch d'échelle.** Le microbiome opère dans [0, ~0.35]
   mais TOUS ses consommateurs divisent par 3.0 (`FIELD_NORM`) :
   - `uptake.py:63` (TICK/golden) → bonus réel ~4 % au lieu de 40 %.
   - `sol.py:121` protection maladie (TICK) → quasi-nulle même sol sain.
   - `sol.py:136` + `vigueur_plante.qi_local` + vitalité VUE → ~0.01.
   L'`om_active`/`om_stable` /5.0 idem (opèrent à ~0.6). Donc même un sol au pic
   (microbiome 0.35) est mécaniquement quasi-inerte ET lu « mort ».

## Blast radius golden
- Recalibrer la métrique vitalité SOL (verdict 5) = VUE-only → golden re-fige
  UNIQUEMENT le champ "vitalite" des lignes ECO du digest (localisé, propre).
- Recalibrer les normalisateurs microbiome dans uptake/maladie (verdict 1) = TICK
  → golden re-fige LARGE (microbiome→uptake→NPK→croissance). Change l'équilibre.

## Décisions arrêtées (Nico, lot 1, 2026-07-17)
- **D-Q1 : accepter l'équilibre bas + réaligner l'échelle. PAS de plancher.**
  Un microbiome qui suit l'apport de carbone est correct ; on réaligne les
  normalisateurs pour qu'il se LISE et FONCTIONNE à sa vraie plage.
- **D-Q2 : réaligner VUE + TICK.** Vitalité sol lisible (VUE) ET normalisateurs
  uptake/maladie/qi réalignés (TICK) → microbiome enfin mécaniquement utile.
  Golden re-figé LARGE au tronçon TICK, annoncé.
- **D-Q3 : banc en `tools/banc_calibration.py` (conservé) + split** ① VUE, ②
  TICK, ③ vue Godot/overlay F6 + banc F5.

## Design affiné (mesure banc 50 ans — nuances décisives)
- **`om_stable / 5.0` : NE PAS TOUCHER.** Accumulateur centennal réel (moy 0.15→
  2.66 à 50 ans, encore en hausse → ~5 à terme). Jeune sol lit bas = VOULU (#7).
- **`om_active`** plafonne moy ~0.67 → normalisateur cible ~1.0 (÷5 l'écrase).
- **`microbiome`** équilibre moy ~0.05, plot riche ~0.3–0.5, pic transitoire ~2.3
  (an 1-2) → normalisateur EFFET cible ~0.6 (plot riche ≈ 0.7 d'effet).
- **Séparer deux références homonymes** aujourd'hui toutes à 3.0 :
  - **SATURATION-ref** (`croissance.py:241`, borne anti-emballement qui fixe la
    DYNAMIQUE du champ) → **inchangée** (préserve la trajectoire microbiome).
  - **EFFET-ref** (uptake:63, maladie sol:121, vitalité sol:136, qi_local) →
    réalignées à la plage réelle. C'est ce qui re-fige le golden (uptake→NPK→…).
- `fertilite_index/3.0` : dampé par l'effondrement du P mais non nul (N/K portent).
  Revue légère ; la calibration NPK de fond est P2 (sprint séparé, sliders worldgen).
- La métrique vitalité sol pourra demander une revue des POIDS (pénalité disturbance
  0.15 domine les termes positifs écrasés) — calibrer contre des ancres cibles :
  jeune/pauvre ~0.1-0.2, mûr riche ~0.6-0.8, dégradé ~0.05. Somme des poids ≈ 1,
  clamp [0,1] conservés.

## Découpage figé (proposé, à valider OK)
- **① Banc + métrique vitalité VUE** : `tools/banc_calibration.py` + réaligne les
  EFFET-refs LUES PAR LA VUE SEULE (vitalité sol `sol.py:127`). Golden re-figé
  LOCALISÉ au champ `"vitalite"` des lignes ECO.
- **② Normalisateurs TICK** : réaligne uptake:63 + maladie:121 + `qi_local`
  (FIELD_NORM) + om_active. Golden re-figé LARGE annoncé.
- **③ Vue Godot** : overlay F6 vitalité à la nouvelle échelle + snapshot C# +
  banc d'observation F5 (« sol vivant lisible »). Golden intact.

## Tronçon ① — RÉSULTATS (2026-07-17)
- **Fichiers touchés** : `tools/banc_calibration.py` (NEW, outil versionné, banc
  dense 2×6×8 + lâche 2×12×16, `python3 -m tools.banc_calibration [annees]`) ;
  `fields/ecofields/constants.py` (constantes + poids) ; `fields/ecofields/sol.py`
  (méthode `vitalite`) ; `tests/golden_hash.txt` (re-figé).
- **Nouveau hash golden** : `e9a4340058c35c019d657236d6629662bdf540acf2d4ab439de037f940c12ac5`
  (ancien `4f6c4f31…`). Diff VÉRIFIÉ : SEUL le champ `vitalite=` des 2 lignes ECO
  change (T0 0.017→0.178, T1 0.036→0.238) — aucun attribut plante, aucun autre champ
  ECO, aucun log ne bouge. Métrique sans lecteur tick → aucun effet de bord.
- **Constantes ajoutées** (`constants.py`) : `MICROBE_EFFECT_REF = 0.6`,
  `OM_ACTIVE_REF = 1.0`. `sol.py::vitalite` : microbiome/3.0→/MICROBE_EFFECT_REF,
  om_active/5.0→/OM_ACTIVE_REF ; om_stable/5.0 et fertilite_index/3.0 INCHANGÉS.
- **POIDS VIT_W_* RÉÉQUILIBRÉS** (dérive autorisée §D, documentée) :
  ancien 0.35/0.25/0.20/0.20 + disturb 0.15 →
  **VIT_W_MICRO 0.15 · VIT_W_ACTIVE 0.45 · VIT_W_FERT 0.15 · VIT_W_STRUCTURE 0.25**
  (somme positifs = 1.0) · **VIT_W_DISTURB 0.08** (pénalité, abaissée de 0.15).
  Motif mesuré au banc : (1) microbiome (ex-poids dominant 0.35) relaxe vers son
  équilibre bas → un sol MÛR lisait plus BAS qu'un sol JEUNE (inversion) ; (2)
  `disturbance` reste ~0.5 CONSTANT partout → taxe plate qui écrasait toute la bande.
  Poids transféré vers les accumulateurs qui croissent avec la richesse (om_active,
  om_stable).
- **Ancres atteintes** (banc 10 ans, seed 42) : bande MONOTONE et discriminante —
  DENSE jeune ~0.12 (an1) → DENSE mûr ~0.24 (an9, grimpe encore) ; LÂCHE dégradé
  ~0.06 (proche de l'ancre ~0.05). DENSE ≫ LÂCHE (discrimine la densité). Le
  « mûr/riche ~0.5+ » est un palier de PLUS LONG terme (om_stable = accumulateur
  centennal, /5.0 inchangé, philo #7 « jeune sol lit bas »).
- **Suites ciblées** : PASS (génétique, croissance, maîtrise, vigueur, sénescence,
  signes, ombre maison, phototropisme, scatter…). ⚠ `test_population` FAIL mais
  PRÉ-EXISTANT (échoue IDENTIQUEMENT sur le code d'avant ce tronçon, hash obtenu
  inchangé `8290c6a4…` vs attendu stale `8f27b6b2…`) → NON causé par ①, hors
  périmètre. À traiter séparément.

## Tronçon ② — RÉSULTATS (2026-07-17)
- **Fichiers touchés** : `fields/ecofields/uptake.py` (l.63 `/3.0`→`/MICROBE_EFFECT_REF`,
  constante déjà visible via `from .constants import *`) ; `fields/ecofields/sol.py`
  (l.121 protection maladie, idem) ; `sim/vigueur_plante.py` (import `MICROBE_EFFECT_REF`
  depuis `fields.ecofields` + l.82 terme microbiome de `qi_local` ; ligne 81 `fert`
  nutriments INCHANGÉE sur `FIELD_NORM=3.0`, P2) ; `tests/golden_hash.txt` (re-figé).
- **INTOUCHÉS confirmés** : `croissance.py:241` (SATURATION-ref), modulateurs de rythme
  (matiere_organique :96/:133, sol:71, resources:255, allelopathie:43, perturbations:364),
  om_stable/5.0, nutriments/fertilite_index.
- **Nouveau hash golden** : `3076c154dc3d5fbff8a4e32414be6d7ed4ad30b6970cd2c3114d49717b515253`
  (ancien `e9a43400…`). Dérive LARGE = réalignement de l'EFFET microbiome dans le tick
  (uptake→NPK→croissance→exsudats→microbiome). **Sens vérifié** (dump digest avant/après) :
  vitalité plante TOTALE ↑ (20.88→21.47) malgré 2 plantes de moins (reshuffle repro
  mineur, aucune mort de masse, 0 alive=False) ; plusieurs plantes s'améliorent nettement
  là où le microbiome est présent (Bourse-à-pasteur 0.267→0.733, Trèfle 0.733→1.0) ;
  stocks N/P/K du sol BAISSENT (plantes assimilent plus) ; microbiome MONTE (boucle
  vertueuse exsudats). Pas de régression aberrante.
- **Banc (`tools.banc_calibration 10`)** : effet uptake désormais VISIBLE. Bonus
  d'assimilation `(1 + micro_norm·0.40)` à microbiome 0.4 : AVANT ×1.05 → APRÈS ×1.27 ;
  à saturation (≥0.6) ×1.08 → ×1.40 (plein effet). Le microbiome, jusqu'ici inerte
  (~4 % même sain), est enfin mécaniquement utile.
- **Suites ciblées (11)** : PASS — génétique 20/20, croissance 67/67, maîtrise 35/35,
  vigueur 136/136, ombre maison, phototropisme 11/11, sénescence, signes 8/8,
  scatter_sol, scatter_reçue. ⚠ `test_population` FAIL (pré-existant, dette hors périmètre) :
  attendu stale `8f27b6b2…` inchangé, mais **hash obtenu passé de `8290c6a4…` (①) à
  `5ab68dca…`** — ATTENDU : la suite lance un sim moteur complet qui traverse l'uptake
  réaligné, son digest interne bouge donc légitimement. NON re-capturé (hors périmètre,
  pas de masquage) — à traiter avec la dette test_population.

## §REPRISE
Tronçon ② CLOS (non commité — Nico commit). PROCHAIN = **③ 03_vue_godot_overlay_banc.md**
(overlay F6 microbiome FixMax 3→0.6 + overlay vitalité sol + banc F5 ; golden INTACT,
C#). Lire : `CLAUDE.md` + ce fichier + `docs/conception/CONCEPTION_CALIBRATION_REALISTE.md`
+ `03_*.md`. Ordre : ① ✅ → ② ✅ → ③. Chaque tronçon : bosser → golden (voir kickoff) →
maj ce fichier (hash + décisions) → commit → tronçon suivant.
Hash golden courant : `3076c154dc3d5fbff8a4e32414be6d7ed4ad30b6970cd2c3114d49717b515253`.
