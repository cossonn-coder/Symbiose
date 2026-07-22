# ② Normalisateurs d'effet du microbiome — côté TICK

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + ce fichier. Spec de
> référence : `docs/meta/calibrage/conception_calibration_realiste.md` (§2.1, §2.2, §7②).
> **Prérequis : tronçon ① terminé** (constantes `MICROBE_EFFECT_REF`, `OM_ACTIVE_REF`
> déjà dans `constants.py`). Ce tronçon RE-FIGE LE GOLDEN LARGE (annoncé).

## Objectif

Réaligner les lecteurs **d'EFFET du microbiome dans le TICK** sur `MICROBE_EFFECT_REF`
(≈ plage réelle), pour que la **rétroaction rhizosphère** redevienne discriminante :
un sol pauvre n'obtient ~aucun bonus, un sol riche un bonus réel (jusqu'à 40 %). Le
microbiome, aujourd'hui mécaniquement inerte (bonus ~4 % même sain), redevient utile.

## Contexte (déjà établi)

Le microbiome opère (moyenne) ~[0, 0.35], plot riche ~0.5. Trois lecteurs d'effet
le divisent par 3.0 → effet quasi-nul en permanence. `MICROBE_EFFECT_REF = 0.6`
donne : plot 0.05 → ×1.03 (nul, correct sol pauvre) ; plot 0.4 → ×1.27 ; plot ≥0.6
→ ×1.40 (plein). Cf. table §2.1 du doc.

## À faire — SITES EXACTS (ne toucher QUE ceux-ci)

1. **`fields/ecofields/uptake.py:63`** — bonus d'assimilation (le site phare) :
   `micro_norm = min(1.0, self.microbiome.at_plot(r, c) / 3.0)` →
   `/ MICROBE_EFFECT_REF`. Importe la constante.
2. **`fields/ecofields/sol.py:121`** — protection maladie (`disease` logistique) :
   `micro_norm = min(1.0, self.microbiome.at_plot(r, c) / 3.0)` →
   `/ MICROBE_EFFECT_REF`.
3. **`sim/vigueur_plante.py:82`** — terme microbiome de `qi_local` UNIQUEMENT :
   `micro = min(1.0, eco.microbiome.at_plot(r, c) / FIELD_NORM)` →
   `/ MICROBE_EFFECT_REF` (importe-la depuis `fields.ecofields`, à côté des imports
   existants `UPTAKE_MICRO_BONUS`, etc.).
   ⚠ **NE PAS toucher la ligne 81** (`fert = min(1.0, nutri / FIELD_NORM)`) : les
   NUTRIMENTS restent sur `FIELD_NORM = 3.0` (échelle NPK, calibration P2). `qi_local`
   est une façade golden-NEUTRE ; ce site ne re-fige pas le golden, mais on l'aligne
   pour la cohérence de la Vigueur perçue.

## Ce qu'il NE faut PAS faire (rester chirurgical)

- **`sim/engine/croissance.py:241`** (`micro_norm = ... / 3.0`) → **INTOUCHÉE** :
  c'est la référence de SATURATION qui fixe la dynamique/équilibre du microbiome.
  La changer déplacerait la trajectoire du champ (hors périmètre, cf. doc §2.1).
- **Modulateurs de rythme hors périmètre (dette D-cal, §6 du doc) — INTOUCHÉS :**
  `matiere_organique.py:96` et `:133` (vitesse décompo), `sol.py:71` (soil_memory),
  `fields/population/resources.py:255` (ressource lombric),
  `fields/ecofields/allelopathie.py:43` (détox), `sim/effects/perturbations.py:364`
  (bascule létale). Reshaperaient tout le modèle MO → autre sprint.
- Les `om_stable/5.0` (CEC/lessivage `matiere_organique.py:223`, `hydrologie.py:144`)
  → INTOUCHÉS (accumulateur centennal correct).
- Les nutriments / `fertilite_index` → INTOUCHÉS (P2).

## Golden
**Re-figé LARGE, annoncé et VOULU.** Réaligner `uptake` rouvre la cascade uptake →
NPK → croissance → exsudats → microbiome : la quasi-totalité du digest bouge. C'est
la dérive attendue (le microbiome devient mécaniquement utile). Procédure :
1. `python3 -m tests.test_golden` → FAIL large attendu. **Sanity-check** le sens :
   la vitalité des plantes et l'assimilation doivent globalement s'AMÉLIORER là où le
   microbiome est présent (pas de régression aberrante, pas de morts en masse). Lance
   `tools/banc_calibration.py` : le microbiome doit maintenant produire un effet
   d'uptake visible (comparer bonus avant/après sur un sol riche).
2. Re-capture : `python3 -m tests.test_golden --capture`. Note le hash dans
   `00_etat.md` avec une phrase de justification (dérive = réalignement effet
   microbiome tick).
3. Relance les 11 suites ciblées : investigue toute casse (une suite qui encode
   l'ancien effet quasi-nul du microbiome peut légitimement demander re-capture — à
   signaler, pas à masquer).

## Fin de tronçon
Mets à jour `00_etat.md` (§REPRISE + nouveau hash + note dérive), commit (fichiers
nommés : `fields/ecofields/uptake.py`, `fields/ecofields/sol.py`,
`sim/vigueur_plante.py`, `tests/golden_hash.txt`, `00_etat.md`), puis tronçon ③.
