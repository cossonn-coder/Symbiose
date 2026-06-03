<!-- Archivé depuis journal.md le 2026-06-03 (Sprint refactor structurel) -->

## 2026-06-02 — Sprint sol vivant : le sol devient organisme (Python)

### Contexte

Sprint **Python pur** sur le moteur de vérité (`data/code/`), dérivé du dossier
`sprints/etude_sol_vivant.md`. Objectif : faire passer le sol de **décor
réactif** à **organisme** — les racines nourrissent le sol (exsudats), le sol
leur rend des services (minéralisation, uptake), une **vitalité émerge**. Lève
la dette **D10** côté Python (réalignement OM Python → v4 du C#).

Séquence actée (kickoff, validée par Nico) : **socle OM v4 → chantier B
(racines spatiales) → chantier A (boucle rhizosphère) → vitalité dérivée**.
Mycorhizes (chantier C) **différées** en extension future (palier avancé).

### Étape 0 — OM v4 tri-compartiment (D10 levée côté Python)

`organic_matter` mono-compartiment scindé en **`om_fresh` / `om_active` /
`om_stable`** dans `EcoFields`, alignés sur `GridField.cs`. `tick_decomposition`
réécrit en **cascade** : chaque compartiment se décompose à son rythme
(`OM_FRESH_DECAY` 0.08 / `OM_ACTIVE_DECAY` 0.018 / `OM_STABLE_DECAY` 0.0006),
modulé par le microbiome. La masse décomposée se répartit en trois destinations
sommant à 1.0 — **humification** (compartiment suivant), **minéralisation**
(→ `fertilite`, principale sur `active`), **respiration** (perte nette).
Aucune création de carbone. Nécromasse et résidus entrent par `om_fresh`.

### Étape 1 — Chantier B : racines spatiales

`engine.py:_apply_uptake` boucle désormais sur `plant.root_plots` (filtrés aux
bornes), avec `share = 1/nb_plots` (paramètre ajouté à `plant_uptake`) — on
**répartit** la consommation, on ne la duplique pas. Idem pour les
enrichissements `inject_field` « local » (`effects.py`) : répartis sur
l'empreinte racinaire. La **compétition souterraine** devient émergente.

### Étape 2 — Chantier A : boucle rhizosphère ⭐

Nouvelle méthode `engine.py:_apply_exudates` (appelée chaque tick) : chaque
plante vivante dépose des **exsudats** ∝ photosynthèse (lumière reçue × surface
foliaire × santé) sur ses `root_plots` — l'essentiel au `microbiome`, une
fraction (`EXUDATE_OM_SHARE` 0.15) à `om_fresh`. **Rétroaction** : le microbiome
gagne un **bonus d'uptake fertilité** (`UPTAKE_MICRO_BONUS` 0.40, borné).
**Universalisation** : suppression du scripting `microbiome` par famille
(Fabaceae, Medicago) — le microbiome émerge des exsudats de **toutes** les
plantes. Les Fabaceae **gardent uniquement** leur fixation N₂ → `fertilite`.
**Bornage anti-emballement** (piège n°1) : le dépôt microbiome décroît en
×(1 − micro_norm), la boucle converge au lieu d'exploser.

### Étape 3 — Vitalité dérivée

`EcoFields.vitalite(r, c)` — grandeur **dérivée, jamais stockée** (respecte la
décision #2) : combinaison bornée [0,1] de microbiome, `om_active`, `fertilite`,
structure (`om_stable`) moins la perturbation. Intégrée aux logs de saison
(`engine.py`) et au bilan final de `main.py` (carte spatiale + moyenne).
Préfigure la **Vigueur (D11)**.

### Validation (lecture terminal, déterministe)

- **`main.py` 500 ans, exit 0, aucun crash.** Carbone conservé.
- Compartiments aux dynamiques distinctes : `fresh` volatil, `stable`/humus
  monte lentement puis plateau (~6-7).
- **Récit A** (sol nu pauvre micro 0.05) : succession + exsudats → micro 1.3,
  fertilité ↑, vitalité 0.40, 8 plantes.
- **Récit B** (polyculture dense) : sol plus riche que A (fertilité 2-2.8,
  vitalité 0.43-0.46), 11 plantes — la boucle rhizosphère bâtit le sol.
- **Récit C** (sol saccagé : micro/OM à zéro, perturbation 0.9) : régénération
  complète — micro 0→2.1, humus 0→10, fertilité 0→2.95, vitalité 0→0.68 ;
  recolonisation massive (45 pionnières en été). *Observation : la succession
  reste dominée par les pionnières annuelles sous forte perturbation — diversité
  à affiner ultérieurement, hors périmètre de ce sprint.*
- **Déterminisme** confirmé : deux runs identiques au flottant près.

### Ce qui a été produit

- `data/code/fields.py` — OM tri-compartiment, cascade, `vitalite()`, `share`
  + bonus microbiome dans `plant_uptake`, `summary` enrichi
- `data/code/engine.py` — `_apply_uptake` spatial, `_apply_exudates`, log saison
- `data/code/effects.py` — `inject_field` local réparti sur `root_plots`
- `data/code/models.py` — injections `organic_matter` → `om_fresh` ; microbiome
  par famille supprimé (Fabaceae/Medicago gardent N₂ → fertilité)
- `data/code/main.py` — carte de vitalité au bilan final
- `journal.md`, `CLAUDE.md`, mémoire ; commit dédié

### Nouvelle dette

- **D24** (portage C#) : uptake spatial sur `root_plots`, exsudats
  (`_apply_exudates`), bonus microbiome→uptake, et `vitalite()` ne sont **pas
  encore portés** côté C#. À absorber dans le **Sprint 3 (portage simulation)**.

---
