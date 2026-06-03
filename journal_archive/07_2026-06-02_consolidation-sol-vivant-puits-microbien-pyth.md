<!-- Archivé depuis journal.md le 2026-06-03 (Sprint refactor structurel) -->

## 2026-06-02 — Consolidation sol vivant : puits microbien (Python)

### Contexte

Mini-sprint de calibrage faisant suite au Sprint sol vivant. Deux points
d'attention relevés : (1) le microbiome n'avait **aucun puits** (montait et
plafonnait à 3.0), (2) la succession reste **pionnière** après saccage.

### Axe 1 — Puits microbien modulé par la famine (FAIT)

`tick_decomposition` : ajout d'une mortalité microbienne **modulée par la
disponibilité de carbone frais**. `famine = 1 − min(1, om_fresh/MICROBE_FOOD_REF)`
(0 si rassasié, 1 si épuisé) ; `microbiome *= 1 − MICROBE_DECAY_MAX*famine`.
Le microbiome devient un **solde** apports (exsudats/OM) − pertes : il monte
sous couvert végétal, redescend sur sol nu. Constantes : `MICROBE_FOOD_REF` 1.0,
`MICROBE_DECAY_MAX` **0.006** (0.015 d'abord testé, trop violent → effondrement
à 0.37 ; ramené à 0.006).

**Validé** : `main.py` 500 ans exit 0, déterminisme tenu. Gradient lisible —
sol couvert dense (récit C, 44 plantes) microbiome ~1.5 / vitalité 0.58 ;
sol clairsemé (A/B, 8-11 plantes) microbiome ~0.6 / vitalité ~0.40. Le
microbiome **suit la couverture du sol** sans s'effondrer. Carte de vitalité
`main.py` plus contrastée (plots nus ~0, couverts ~0.5).

### Axe 2 — Diversité de succession (DIAGNOSTIQUÉ, DIFFÉRÉ)

Diagnostic confirmé sur un saccage à perturbation **réaliste** (non pinnée) :
le sol reste **100 % Bourse-à-pasteur (0 pérenne) sur 150 ans** même quand il
redevient riche. Cause double : (1) `_succession`/`_spring_flush` ne favorisent
les pérennes que sur sol **pauvre** (jamais sur sol mûr) ; (2) après une phase
pionnière, la **banque de graines ne contient que `pioneer`** — les pérennes
n'ont aucune source d'amorçage. C'est de la vraie succession écologique
(pionnier → prairie → climax), cœur du « jardin qui mûrit ». **Décision Nico :
différer en mini-sprint dédié** (dette **D25**) plutôt qu'un patch.

### Ce qui a été produit

- `data/code/fields.py` — puits microbien (`MICROBE_FOOD_REF`,
  `MICROBE_DECAY_MAX`, mortalité ∝ famine dans `tick_decomposition`)
- `journal.md`, `CLAUDE.md` (backlog : mini-sprint succession), mémoire ; commit

---
