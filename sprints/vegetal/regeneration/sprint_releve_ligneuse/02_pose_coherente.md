# ② Pose cohérente — le fruit tombe sous la couronne, la recrue naît où elle peut vivre

À lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/vegetal/regeneration/conception_releve_ligneuse.md` §1, §3.2. Prérequis : ① fait (`SEUIL_SEMIS` existe).

## Objectif
Dans le recrutement direct d'un **arbre**, supprimer l'incohérence mesurée : seuil
de pose 0,35 < seuil de dégât, rayon fixe 150 cm < couronne. La graine tombe sous
la couronne du parent ; elle ne s'installe que là où un semis survit.

## Modèle
`data/code/sim/engine/mortalite.py`, `MortaliteMixin._reproduction`, bloc « 3.
Recrutement direct » (`best, best_light = None, 0.35`) :
- **arbre** (`is_tree = hasattr(cls, "age_curve")`, déjà calculé) :
  rayon de recherche en plots = `int(cls.canopy_radius_at(parent) // 50) + 1`
  (au lieu de `radius_plots` global) ; seuil de pose = `1.0 − SEUIL_SEMIS`
  (lumière de survie d'un semis, importée de `sim.effects.perturbations` — vérifier
  que `mortalite.py` importe déjà depuis `sim.effects` : oui, `apply_mutations…`).
- **non-arbre** (vivace sans archétype) : rayon `radius_plots` et seuil 0,35
  **inchangés**.
Le choix du plot le plus lumineux reste (abstraction « le semis le mieux placé
s'installe ») : le dire en commentaire. `canopy_radius_at` existe sur la classe
(`plants/perennials/base.py`, voie procédurale via `PlantBase`) — vérifier qu'il
rend des cm et ne vaut pas 0 pour un parent mûr.

## Fichiers
- `data/code/sim/engine/mortalite.py`.
- Test neuf (ou ajout à `tests/test_banque_semis.py`) : un arbre mûr isolé sur une
  tuile vide pose sa recrue à une distance ≤ rayon de couronne ; une tuile
  entièrement à lumière < `1 − SEUIL_SEMIS` ne reçoit aucune recrue.

## Golden
**INCHANGÉ** attendu : le pommier du smoke a < 5 ans (`maturity_years` 5) → pas de
reproduction. S'il bouge : STOP, chercher, ne pas re-figer.

## Tests
`tests.test_golden`, `tests.test_banque_semis`, suites reproduction
(`grep -l "_reproduction\|Reproduction" tests/test_*.py`), bancs
`tests/bancs/test_verger_mur.py`. **Jamais `test_epaisseur_500ans`.**

## Ne PAS faire
- Toucher au dépôt banque-sol (`add_species`) ni à l'anémochorie.
- Ajouter une dispersion animale (c'est D42).
