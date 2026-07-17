# 00_etat — sprint CALIBRATION RÉALISTE (P1)

**Statut : CONCEPTION FIGÉE (2026-07-17), prête pour `/sprint-auto`. 3 tronçons.**
Doc : `docs/conception/CONCEPTION_CALIBRATION_REALISTE.md`. Kickoffs 01/02/03.
Source : `BRIEF_CHAMPS_CONCEPTION.md` P1 (verdicts 1 + 5) + `audit_champs.md`.
Date d'ouverture : 2026-07-17.

## Carte des tronçons
- **① 01_banc_metrique_vitalite_vue.md** — `tools/banc_calibration.py` + réaligne la
  métrique vitalité SOL (VUE seule). Golden re-figé LOCALISÉ (champ "vitalite" ECO).
- **② 02_normalisateurs_effet_tick.md** — uptake + maladie + qi (terme microbiome).
  Golden re-figé LARGE annoncé (rétroaction rhizosphère rouverte).
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

## §REPRISE
Conception FIGÉE — exécution par `/sprint-auto sprint_calibration_realiste`.
Lire : `CLAUDE.md` + ce fichier + `docs/conception/CONCEPTION_CALIBRATION_REALISTE.md`
+ le kickoff du tronçon courant. Ordre : ① → ② → ③. Chaque tronçon : bosser →
golden (voir kickoff) → maj ce fichier (hash + décisions) → commit → tronçon suivant.
Bancs de mesure de conception (jetables, dans le scratchpad de session) à
formaliser en `data/code/tools/banc_calibration.py` au tronçon ①.
Hash golden : baseline actuel `tests/golden_hash.txt` (à re-capturer au ① puis ②).
