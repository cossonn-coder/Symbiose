# 2026-07-08 — Sprint ÉQUILIBRE DE L'INVASION (D69, ①→⑧) — SPRINT TERMINÉ

`/sprint-auto sprint_equilibre_invasion`. L'invasion d'adventices, jusque-là
**fulgurante et non bornée** à 8 tuiles (cultivées balayées en <1 saison, N qui
grimpait sans plafond, cf. D69), devient **infléchissable par le joueur via le
milieu** (philo #1/#2) : le **paillage** freine la germination férale, épuise la
banque de graines et retient l'humidité. Conception figée le 2026-07-06
(`docs/conception/CONCEPTION_EQUILIBRE_INVASION.md`, arbitrages D1-D12).

## Tronçons livrés
- **① Banc « monde propre » + diag** : preset `config="propre"` dans `cmd_init`
  (seedbank férale vidée + `feral_off` coupe la succession férale, grains plantés
  préservés) + `tools/diag_population.py` (trajectoire N, top-6 espèces). Golden
  INTACT `84d35983…`.
- **② Recalibrage des freins férals** : scalaire global `GERM_PRESSION_FERALE=0.30`
  sur la levée férale (le VRAI knob de plateau : la banque sature sur sol mûr → la
  germination est bornée par la NICHE, pas par les gains de banque ni la vis A
  seule). Cible atteinte : **N plateau ~613/an6** (vs 1043+ non borné), **onset
  ~2 saisons** (pas <1 — la friche revient mais laisse le temps d'agir, #6). **SEUL
  re-figeage du sprint, annoncé** : golden `84d35983…`→**`33c0ea6f…`**, population
  `c2b4a01d…`→`1aa4997d…` (même cause : moins de vie férale). Aucun buff des
  cultivées (#2).
- **③ Paillage moteur** : champ `paillage` ∈[0,1]/plot (`fields/ecofields/paillage.py`)
  + geste `pailler` + 4 effets — germination férale↓ (cutoff/gradué), aging des
  graines enfouies↑ (banque épuisée sous mulch), évapotranspiration↓, décompo→
  `om_stable`. Naît à 0 → no-op strict au repos → golden INTACT.
- **④ Matériau du mulch** : geste `broyer` (bois mort→**BRF**) + `recolter_paille`
  → **stock par nature** dans `game_state`, `pailler` le consomme. **3 natures**
  data-driven (`NATURES_MULCH`) aux propriétés distinctes, chacune branchée sur un
  couplage existant : BRF → litière `bois` (active la faim d'azote `FAIM_N_TISSUS`
  + nourrit le mycélium `bois_fresh_at`, zéro code neuf), paille → humidité, aiguilles
  → acidification pH + allélopathie. Golden INTACT (event-driven, "" au repos → NEUTRE).
- **⑤ Catalogue paille/BRF** : **blé** (Poaceae), **chanvre** (Cannabaceae neuve),
  **sapin** (Pinaceae neuve, conifère persistant acidophile) + **5 voix chacun**
  (encyclopédie 3 niveaux, carnet par `CONCEPT_DE`, pages P30/P31, magazine famille,
  événements ledger). Hors golden smoke 2 tuiles → INTACT.
- **⑥ Paillage ↔ vie macro (abri)** : `PopulationField` lit `paillage` comme
  habitat/abri (colonne `abri_w` par nature, BRF>paille>aiguilles) → 5 guildes
  ombrophiles de sol (limace/lombric/cloporte/carabe/hérisson) colonisent les zones
  paillées en plein soleil. Naît neutre → golden ET population_hash INTACTS.
- **⑦ Auto-paillage par maîtrise** : au palier « maîtrise » (seuil 3), le geste
  `planter` paille le plot d'instinct, nature dérivée du catalogue (`mulch_source`
  → arbre→BRF → sinon paille). Consomme le stock, aucune Vigueur en plus (réflexe
  fondu dans la plantation). No-op sous le seuil → golden INTACT.
- **⑧ Vue Godot + démo** : snapshot expose `paillage` (profondeur+nature) par plot ;
  verbes `pailler`/`broyer` au routeur (protocole **0.5.20**) ; `visuals/MulchLayer.cs`
  (tapis batché teinté par nature, jitter déterministe) + `world/WorldView.Paillage.cs` ;
  gestes cliquables + cycle nature (touche N) + HUD/légende + option `propre` au
  sélecteur ; abri faune déjà rendu via `MacroLife` (émergent ⑥). Démo : **planche
  paillée plein sud** (tomate/basilic/poivron/tournesol pré-mulchés) dans
  `build_world_full`, hors golden smoke → INTACT. `dotnet build` vert.

## Verdict
**Golden final `33c0ea6f…`**, population `1aa4997d…`, `test_sim_server` 245/245,
`dotnet build` vert. Refactor auto-léger : `actions.py` (poussé à 419 LDC par ⑧)
scindé — résolveurs de cible extraits dans `actions_cibles.py` (`CiblesMixin`),
golden bit-identique. **D69 ✅ FAIT.** `test_epaisseur_500ans` INTERDIT (feedback gravé).

## Reste
- **F5 Nico** : planche sud paillée visible ; `pailler`/`broyer` au clic ; contraste
  planche paillée/nue sur les adventices ; faune sous le mulch au soleil ;
  `config="propre"` pour observer les cultivées seules. **Décision tranchée** : le
  stock de mulch **démarre vide** (fidèle à ④, pas de mulch magique) → broyer/récolter
  avant de pailler ; la planche sud est pré-mulchée à l'init.
- **Dette préexistante signalée** : `world/WorldView.Actions.cs` = **468 LDC** 🔴 —
  déjà rouge AVANT ce sprint (433), hors mandat du refactor auto-léger → à traiter en
  `/refactor` ciblé.
- **⚠ Revenir à la perf pure** (D67 LOD émetteurs d'ombre + LightField, poste #1
  depuis `761bbe9`) — priorité annoncée dès la conception D69.
