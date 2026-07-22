# Brief — suites de `audit_champs.md` pour `/conception`

**Statut : BRIEF de cadrage — verdicts de Nico posés, prêt à découper en passes `/conception`.**
**Date :** 2026-07-17
**Source :** `audit_champs.md` §9 (questions ouvertes) + arbitrages Nico du 2026-07-17.
**Nature :** ce document fige les DÉCISIONS ; chaque passe `/conception` durcira ensuite UN sujet
et produira ses kickoffs `/sprint-auto`. Ne rien implémenter avant conception figée.

---

## Verdicts de Nico (réponses aux 5 questions ouvertes de l'audit)

1. **Microbiome qui décroche (0.34→0.02)** — **NON, ne décroche pas en nominal.** Hypothèse retenue :
   **artefact du monde smoke**, pas dérive de calibration. Vérifié dans le code : le microbiome n'est
   nourri que par les exsudats = `light_received × surface_foliaire × vitalité` (`sim/engine/croissance.py:229`),
   et ne décline que par famine de litière fraîche (`fields/ecofields/matiere_organique.py:216`). Dans le
   monde smoke (2 tuiles, canopée fermée, `lumiere_moy ~0.18`, vitalité ~0.02), lumière ET vitalité sont
   écrasées en même temps → exsudats effondrés → famine. En densité réaliste ça se soutient. **Action :
   confirmer sur un monde représentatif** avant tout ajustement ; ne PAS poser de plancher à l'aveugle.

2. **Phosphore limiteur terminal (p→0.005)** — **ressort VOULU, mais pas obligatoire en permanence.**
   Il faut **au moins un monde où l'on n'est pas limité par NPK**. Décision : rendre les **quantités NPK
   ajustables à la génération du terrain** (sliders d'abondance), pour que la limitation par le phosphore
   soit un **paramètre de monde**, pas une fatalité. Le run éternel exigeant (P s'épuise → pousse vers
   rotation/BRF/amendement) reste un preset ; un preset « sol riche » lève la contrainte.

3. **Priorité de câblage des champs dormants** — **MYCÉLIUM d'abord.** Le `ph` est jugé **anecdotique**
   pour l'instant → différé/déprioritisé. Cible : brancher les effets §2 du mycélium (saprophyte→décompo,
   mycorhize→uptake P, liant→`om_stable`, faune fongivore) qui sont aujourd'hui débranchés
   (`audit_champs.md` §7). Conception mycélium déjà figée en mémoire ([[design_mycelium_interconnexions]])
   — vérifier son état avant de relancer une passe.

4. **Budget perf lumière (~53 % CPU)** — **CORRECTION apportée** : le coût est dominé par les **plantes**,
   pas les bâtiments. La maison est un unique rectangle balayé + passe albédo (coût constant, déjà en
   cache via `geom_key`, `fields/light.py:266`). Un LOD émetteurs existe déjà (D67, `SHADING_POWER_MIN=37.5`).
   Ce qui coûte = **la croissance des plantes casse le cache géométrique chaque semaine** → recalcul.
   **Levier restant = LOD temporel sur la canopée** (recalcul moins fréquent hors changement notable de
   canopée), pas « recalculer les bâtiments moins souvent ». *À valider :* priorité basse tant que le
   monde smoke n'est pas représentatif du vrai profil (mesurer sur 1600 plots avant d'optimiser).

5. **`vitalite_average` très bas en canopée fermée** — **RECALIBRER selon la réalité.** L'échelle actuelle
   sort ~0.02 en monde dense et sert pourtant de poids ET de métrique de succession. Décision : caler
   l'échelle sur une **réalité biologique** (une plante saine en bonnes conditions doit sortir une vitalité
   « lisible », pas 0.02). Impacte tout ce qui lit `vitalite` en pondération → **golden re-figé attendu**,
   à annoncer et maîtriser.

---

## Découpage proposé en passes `/conception` (ordre recommandé)

> Ces sujets sont hétérogènes → une passe `/conception` chacun, pas un mégasprint.
> L'ordre suit la dépendance : d'abord établir un **monde représentatif** (car 1 et 5 en dépendent),
> puis calibrer, puis câbler, puis optimiser.

- **P0 — Banc de mesure représentatif (préalable transverse).** Le monde smoke 2 tuiles fausse 1, 4 et 5.
  Avant de trancher calibration/perf, il faut un scénario de mesure à densité réaliste (pas 1600 plots
  complets si trop lourd, mais assez lâche pour ne pas saturer la canopée). Peut être un simple préalable
  outillage dans la passe « calibration » plutôt qu'une conception à part.

- **P1 — Calibration réaliste (verdicts 1 + 5, couplés).** Confirmer que le microbiome tient en nominal
  (sinon corriger la cause, pas poser un plancher) ET recaler l'échelle `vitalite_average` sur la réalité
  bio. Couplés car les deux se jugent sur le même banc représentatif et `vitalité` nourrit les exsudats
  (donc le microbiome). **Golden re-figé attendu** (échelle vitalité). *Le plus prioritaire.*

- **P2 — NPK ajustable à la worldgen (verdict 2).** Sliders d'abondance N/P/K à la génération du terrain
  + presets (« sol riche » non limité ↔ « sol pauvre » exigeant). Touche la génération de monde, pas le
  tick → golden a priori NEUTRE (les presets par défaut = valeurs actuelles). Choix game design à durcir :
  quels presets, quelle plage, exposés où (école de départ ? Options ?).

- **P3 — Câblage mycélium (verdict 3).** Reprendre [[design_mycelium_interconnexions]] (déjà figée),
  vérifier son actualité, brancher les effets débranchés. Gros gisement d'interconnexions (philo #6).
  Golden LARGE re-figé déjà annoncé dans la conception mémoire.

- **P4 — LOD temporel lumière (verdict 4, priorité BASSE).** À ne lancer qu'après P0 (profil mesuré sur
  monde représentatif). Concevoir un recalcul de canopée moins fréquent que l'hebdo, sans casser le
  déterminisme (golden). Peut rester en dette tant que le profil réel ne le justifie pas.

---

## Garde-fous rappelés

- **Philo #1-#7** : l'audit ne relève aucune violation. Toute passe doit rester en flux → contrainte →
  réponse (jamais de bonus direct), déterministe (zéro RNG vivant), golden préservé ou re-figé maîtrisé+annoncé.
- **Perf-first** : chaque tronçon préserve le golden ou re-fige de façon localisée et expliquée.
- **Rattachements** : DETTE D41 (mort par carence édaphique, bloquée qi_local), D57 (épaisseur), conceptions
  voisines `docs/champs/eau/conception_hydrologie_marecage.md`, `docs/vegetal/allelopathie/conception_allelopathie.md`, `etude_sol_vivant.md`.
- **Ménage** : `data/code/outputs/run10.py` et `ablate.py` (scripts d'audit) restent à retirer manuellement
  si non versionnés (cf. `audit_champs.md` annexe).
