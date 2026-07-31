## 2026-07-31 — Sprint RYTHMES MO (D77 + D40) — CLOS (`/sprint-auto`, ①→③)

**Décision :** un seul levier — le dénominateur `/3.0` qui écrasait le
microbiome — résout D77 (calibration des modulateurs de RYTHME microbiome/MO)
**et** D40 (sensibilité T°/humidité Q10 de la décompo). Découverte cardinale
confirmée à l'exécution : **D40 était déjà codé mais INERTE**. La cloche Q10
(`microbe_clim_factor`, sprint météo→champs ④) multipliait un `microbiome/3.0`
plafonné à ~0,08 → swing saisonnier réel +12 % au lieu d'allumer le ×5. **D40 ≡
D77.**

**Constante neuve `MICROBE_RHYTHM_REF = 0.6`** (≠ `MICROBE_EFFECT_REF`, même
valeur au départ) : découple le réglage de la DYNAMIQUE MO de celui de la
lisibilité VUE. Cap `min(1.0,·)` **structurel** (piège `microbiome max_val=3.0`
→ quotient jusqu'à 5,0 sans cap → décompo divergente) ajouté aux 3 sites A qui
ne l'avaient pas.

**① Décompo cœur** (`298d37b…`) : les deux `/3.0` de `matiere_organique.py`
(`decomp_speed:96`, `tick_decomposition:133`) → `min(1.0, microbiome/RHYTHM_REF)`.
**D40 allumé** : swing saisonnier décompo **+12,2 % → +55,2 %** (microbiome 0,5,
humidité optimale). Golden **RE-FIGÉ LARGE** (prévu) : cascade
décompo→MO→NPK→humus→vitalité.

**② Readers périphériques + herbivorie** (`9ad035f…`) : 4 readers migrés vers
`RHYTHM_REF` — soil_memory (`sol.py:81`, **cap ajouté**), lombric
(`resources.py:316`, **import paresseux** : `fields/population` n'importe jamais
`ecofields` au top-level, cycle via `container.py` → écart de prescription du
kickoff corrigé d'emblée), détox allélo (`allelopathie.py:43`), bascule létale
herbivorie (`perturbations.py:438`). **Seuil `HERBIVORY_LETHAL_MICRO` re-dérivé
0.20 → 0.05** au banc (échelle `/0.6`) : sol vivant médian `micro_norm` 0.18 vs
sol bêché ~0 → 0.05 siège dans le creux. L'ancien 0.20 sur `/3.0` lisait ~0.017
partout = « sol mort » TOUJOURS vrai (bascule cassée, réparée). Golden **RE-FIGÉ**
(prévu, soil_memory→succession + herbivorie) + 2ᵉ golden `population_hash`
`cc886bd… → c59e0dd…` (tick lombric ; assertions comportementales toutes vertes).

**③ Banc de mesure + verdict D41** (golden **INTACT** `9ad035f…`) : nouveau
`tools/banc_favorabilite.py` (mesure pure, réutilise `FIELD_NORM`/`dispo`/
`microbe_clim_factor`/`RHYTHM_REF`). `FieldOverlay.cs` expose déjà om/npk/
microbiome → aucun C# à câbler.

**Question / VERDICT D41 = NO-GO.** Favorabilité D41 directe
(`Liebig(min N,P,K) × fenêtre pH`, calculée SANS `qi_local`) sur jardin sain
(seed 42, 20 ans) : **médiane 0.000, max 0.012** sur 96 plots. Le pH n'est pas
le frein (`dispo(6.8,P)≈0.91`) — c'est la **carence NPK absolue** (P/K ~0.003
sur 0–3). La recalibration allume bien l'aval MO (`om_stable` grimpe 0.16→1.31)
mais **ne relève PAS la ligne de base NPK** : l'uptake + le lessivage vident P/K
aussi vite que la minéralisation les relâche. **L'hypothèse §5 de la conception
(« la ligne de base NPK d'un jardin sain remonte ») est RÉFUTÉE par la mesure.**
Conséquence : D41 (mort édaphique chronique) **ne peut pas partir en /conception
contre ce sol** — une voie « mort » sur la favorabilité brute condamnerait tout
sol sain. Le vrai blocage amont est l'**équilibre uptake↔minéralisation P/K**,
pas le rythme microbien.

**Golden final `9ad035f18916813dbd194f0d7b76c11178229c63203dccd832bdf4ea3175411c`**
(re-figé maîtrisé depuis le `57c166d8…` de référence — la première dérive du
digest depuis longtemps, entièrement prévue et annoncée par les kickoffs ① et ②).
`population_hash = c59e0ddb…`. Build C# non concerné (Python pur). Refactor
auto-léger **no-op** (aucun fichier > 400 LDC ; `banc_favorabilite.py` = 87 LDC).

DETTE : **D40 → ✅ CLOS**, **D77 → ✅ CLOS**, **D41 → précondition MESURÉE = NON
atteinte (NO-GO)** — reformulée vers le déséquilibre uptake↔minéralisation P/K.
Reste **F5 Nico** : litière saisonnière visible (D40, F6 sur `om_fresh`/
`om_active`), heatmaps N/P/K qui resteront « pauvres » (attendu, = le NO-GO, pas
un bug), `om_stable` qui verdit avec les années, aucune mort en masse par
artefact de recalibration.
