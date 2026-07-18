# 2026-07-18 — Sprint CALIBRATION RÉALISTE — CLOS (`/sprint-auto`, ①→③)

**Objet.** Couple les verdicts 1 (le microbiome tient-il en régime nominal ?) et
5 (recalibrer l'échelle de la métrique `vitalite`) de `BRIEF_CHAMPS_CONCEPTION.md`
(P1) + `audit_champs.md`. But : que le sol vivant se **LISE** et **FONCTIONNE** à
sa vraie plage d'opération. Spec figée : `docs/conception/CONCEPTION_CALIBRATION_REALISTE.md`.

## Diagnostic (mesuré au banc, avant tout code)

- **Deux « vitalités » conflées dans l'audit** : `plant.vitalite` (santé plante,
  hashée au golden) est SAINE dans les deux mondes (dense/lâche) ; `eco.vitalite`
  (métrique SOL, snapshot `"vitalite"`, VUE pure, **aucun lecteur tick**) ~0.01.
  Le « 0.02 » de l'audit = toujours cette métrique sol.
- **Racine commune = mismatch d'échelle.** Le microbiome opère (moyenne) en
  [0, ~0.35], plot riche ~0.5, pic transitoire ~2.3, mais TOUS ses consommateurs
  divisaient par 3.0 → même un sol au pic est mécaniquement quasi-inerte (bonus
  uptake ~4 %) ET lu « mort ».

## Tronçons

**① banc + métrique vitalité SOL (VUE)** — commit `46891ec`, golden RE-FIGÉ
LOCALISÉ prévu `4f6c4f31…`→`e9a43400…`.
- Outil versionné `data/code/tools/banc_calibration.py` (banc dense 2×6×8 +
  lâche 2×12×16, miroir de `test_golden.build_world`, `python3 -m tools.banc_calibration [annees]`, 79 LDC).
- Constantes `MICROBE_EFFECT_REF = 0.6` / `OM_ACTIVE_REF = 1.0` (`fields/ecofields/constants.py`).
- `sol.py::vitalite` : microbiome/3.0 → /MICROBE_EFFECT_REF, om_active/5.0 →
  /OM_ACTIVE_REF ; **om_stable/5.0** (accumulateur centennal, philo #7) et
  **fertilite_index/3.0** (calibration NPK = P2) INCHANGÉS.
- **Poids `VIT_W_*` rééquilibrés** (dérive §D autorisée) : ancien 0.35/0.25/0.20/0.20
  + disturb 0.15 → MICRO 0.15 · ACTIVE 0.45 · FERT 0.15 · STRUCTURE 0.25 (somme=1.0)
  · DISTURB 0.08. Motifs mesurés : microbiome sur-pondéré INVERSAIT la maturité
  (il relaxe vers son équilibre bas) ; disturbance ~0.5 constant = taxe plate qui
  écrasait la bande.
- Diff golden VÉRIFIÉ dump-à-dump : SEUL le champ `vitalite=` des 2 lignes ECO
  bouge (aucun attribut plante, aucun autre champ ECO, aucun log). Métrique sans
  lecteur tick → zéro effet de bord.

**② normalisateurs microbiome côté TICK** — commit `503ce41`, golden RE-FIGÉ
LARGE annoncé `e9a43400…`→`3076c154…`.
- 3 lecteurs d'EFFET réalignés sur `MICROBE_EFFECT_REF` : `uptake.py:63` (bonus
  d'assimilation, site phare), `sol.py:121` (protection maladie logistique),
  `sim/vigueur_plante.py:82` (terme microbiome de `qi_local` ; ligne 81 `fert`
  nutriments laissée sur `FIELD_NORM=3.0`, P2).
- INTOUCHÉS : `croissance.py:241` (SATURATION-ref, fixe la DYNAMIQUE du champ),
  modulateurs de rythme (MO, soil_memory, lombric, allélopathie, perturbations),
  om_stable/5.0.
- Sens de la dérive vérifié (dump digest avant/après) : vitalité plante TOTALE ↑
  (20.88→21.47), boucle vertueuse microbiome, N/P/K du sol assimilés, aucune mort
  de masse. Banc : bonus uptake à saturation ×1.08 → ×1.40 (le microbiome, jusqu'ici
  inerte, redevient mécaniquement utile).

**③ vue Godot — overlay F6 + banc F5** — commit `2a340b9`, golden INTACT `3076c154…`.
- Pont `tools/simserver/commands.py::cmd_fields` : clé synthétique `"vitalite"`
  ajoutée au registre + cas spécial matérialisant la métrique DÉRIVÉE `eco.vitalite`
  en grille row-major à la demande (pure lecture, aucun état stocké).
- `visuals/FieldOverlay.cs` : palette microbiome FixMax `3f`→`0.6f` (la vraie plage
  occupe enfin la bande couleur) + nouvelle palette `vitalite` [0, 0.8]
  parchemin `d8d2c0` → vert profond `2f6f3a` (pauvre→vivant).
- `dotnet build` VERT. Smoke pont OK (registre expose `vitalite`, grille 6×8
  matérialisée, plage init 0.109–0.145).
- **NOTE orchestration** : sous-agent ③ coupé par limite de session (cause externe,
  aucune modif partielle laissée) ; tronçon terminé directement par l'orchestrateur,
  périmètre identique au kickoff.

## Bilan

- **Golden final `3076c154dc3d5fbff8a4e32414be6d7ed4ad30b6970cd2c3114d49717b515253`**
  (2 re-figeages, tous deux prévus par les kickoffs).
- Refactor auto-léger **no-op** (tous les fichiers touchés ≤300 LDC pur 🟢).
- **Dette ouverte** : **D77** (D-cal — modulateurs de RYTHME MO/décompo restés sur
  /3.0-/5.0, §6 du doc, à concevoir avec re-figeage LARGE) ; `test_population` à
  re-figer (hash interne périmé, déplacé par le réalignement uptake du ② — dette
  PRÉ-EXISTANTE hors périmètre, vérifiée bit-à-bit).
- **Reste F5 Nico** (Godot pas sur la VM) : checklist banc dans `00_etat.md` —
  mode technique F6, overlays `microbiome` puis `vitalite`, vérifier qu'un coin de
  sol riche se distingue NETTEMENT d'un coin pauvre (« le sol vivant se lit »).
