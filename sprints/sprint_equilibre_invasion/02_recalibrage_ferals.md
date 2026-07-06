# Tronçon ② — Recalibrage des freins férals (onset ~2-3 saisons, N~650/8 tuiles)

**Prérequis de lecture** : `CLAUDE.md`, `00_etat.md`,
`docs/conception/CONCEPTION_EQUILIBRE_INVASION.md` §7. **SEUL tronçon qui
re-fige le golden** — dérive localisée, maîtrisée, ANNONCÉE.

## Objectif
Faire tenir la population à 8 tuiles : ralentir l'onset de l'invasion (friche en
**~2-3 saisons**, pas < 1) et amener N à un plateau **~600-700 à 8 tuiles** (vs
1043+ mesuré). La vis A avait été calibrée sur **2 tuiles** (« ~190 »), d'où la
dérive à l'échelle réelle.

## Fichiers à toucher (knobs — PAS le cutoff dur)
- `data/code/sim/succession.py` : `COUVERTURE_GERM_EXP` (=4.0), éventuellement la
  base de la vague de printemps (chercher le terme de germination férale de base).
- `data/code/fields/seedbank.py` : taux d'enrichissement
  `tick_disturbance_enrichment` / `tick_late_succession_enrichment`
  (`SEED_*_GAIN`) — sources de la pression férale.
- **Ne PAS** toucher `COUVERTURE_ADVENTICE_SEUIL` (cutoff dur) ni
  `sim/capacite.py` (backstop pur-perf, doit rester non-firé).

## Méthode (mesurée)
1. Baseline : `python3 -m tools.diag_population --config full` (trajectoire
   actuelle, N~1043 an5).
2. Itérer sur les knobs par petits pas ; re-mesurer la trajectoire à chaque essai.
   Cible : N plateau ∈ [600,700] à l'an 6, oscillation saisonnière bornée (pas
   d'enveloppe croissante), et cultivées non balayées avant ~2-3 saisons (vérifier
   la persistance des cultivées de `build_world_full` dans la compo).
3. Figer les valeurs retenues.

## Golden
**RE-FIGÉ** (localisé, annoncé). Après calibrage :
- relancer `python3 -m tests.test_golden` → il ÉCHOUE (attendu) → inspecter la
  dérive (doit être cohérente : moins de germination férale), puis **mettre à
  jour** `tests/golden_hash.txt` avec le nouveau hash + consigner l'ancien→nouveau.
- idem `tests/population_hash.txt` (`test_population`) — re-figé POUR LA MÊME
  CAUSE (moins de vie férale → densités macro changent). Vérifier que les
  invariants structurels de `test_population` tiennent (bornes ∈[0,max], cap
  sprites, positions indépendantes de la semaine).
- suite complète verte (hors `test_epaisseur_500ans`, INTERDIT).

## NE PAS
- Pas de nerf qui rende les cultivées invincibles (philo #2 : on borne la
  PRESSION férale, on ne buffe pas les cultivées).
- Pas de RNG. Pas de re-figeage NON annoncé d'un autre digest.

## Vérif / F5
`diag_population --config full` post-calibrage : N plateau ~650, enveloppe non
croissante. Consigner la trajectoire avant/après dans `00_etat.md`.
