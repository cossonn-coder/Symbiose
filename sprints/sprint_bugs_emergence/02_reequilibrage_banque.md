# ② Rééquilibrage de la banque-sol — déverrouiller la succession (S3)

> Kickoff autosuffisant. Lire AVANT : `CLAUDE.md`, `00_etat.md`,
> `docs/conception/CONCEPTION_BUGS_EMERGENCE.md` (volet S3, fix (a)+(b)).
> Source de vérité = Python `data/code/`. Lancement depuis `data/code/`.

## Objectif
Casser le verrou de succession qui laisse Capsella (pioneer) envahir tout et
« bloquer la germination ». Deux leviers couplés, tous les deux flux-based
(philo #2) et déterministes (philo #3), dans la banque-sol.

## Cause à corriger (rappel)
Les tardifs (nitrogen_fixer/grass/competitor) n'entrent en banque que via
`tick_late_succession_enrichment`, gaté sur `soil_memory_deep ≥ 0.2` (décennal,
jamais atteint) → seul pioneer alimente la banque (`tick_disturbance_enrichment`,
sans porte) → `germination_candidates` ne renvoie que pioneer. Diagnostic complet
dans `00_etat.md`.

## Fichiers à toucher
- `fields/seedbank.py` :
  - `tick_late_succession_enrichment` — la clé du fix (a).
  - `tick_disturbance_enrichment` — le fix (b).
  - constantes `SEED_LATE_GAIN`, `SEED_LATE_MIN_MATURITY`,
    `SEED_COMPETITOR_MATURITY`, `SEED_DISTURBANCE_GAIN`.
- `fields/ecofields/sol.py` — l'appelant `tick_late_succession_enrichment(...)` et
  `tick_disturbance_enrichment(...)` (méthode `tick_soil_*`, autour des lignes
  27-28). Il faut leur passer de quoi calculer l'`om_index` (le container `self`
  a `om_active`/`om_stable` — fournir un accès par plot).
- `bancs/` — ajouter un banc « bascule pionnier→prairie » (voir plus bas).

## Modèle
**(a) Facilitation OM des tardifs.** Remplacer le gate `soil_deep` par un indice
OM réactif, calculé par plot :

```
om_index = clamp((om_active[r][c] + om_stable[r][c]) / OM_FACILITATION_REF, 0, 1)
```

- nitrogen_fixer & grass : amorcés dès `om_index ≥ OM_FIXER_GRASS_MIN` (~0.05) ;
- competitor : dès `om_index ≥ OM_COMPETITOR_MIN` (~0.20) ;
- gain ∝ `om_index` (les tardifs affluent d'autant plus que le sol est bâti),
  avec `SEED_LATE_GAIN` relevé pour qu'ils ACCUMULENT vraiment (calibrer pour une
  bascule en ~5-15 ans selon secteur, pas 30+).

`OM_FACILITATION_REF`, `OM_FIXER_GRASS_MIN`, `OM_COMPETITOR_MIN` = nouvelles
constantes documentées. Garder la structure « trickle par plot » existante.

**(b) Bride de l'emballement pioneer.** Moduler l'apport pioneer par la maturité
OM du plot :

```
pioneer_gain = disturbance · SEED_DISTURBANCE_GAIN · (1 − om_index)
```

Sur sol nu (`om_index≈0`) le pioneer afflue comme avant ; sur sol bâti il se
tarit → le tapis Capsella cesse de se sur-alimenter, les tardifs prennent le
relais. Émergence de la bascule.

## Banc de validation (déterministe)
Ajouter dans `bancs/` un banc « succession_bascule » : monde pionnier, simulé
N années, oracle en TENDANCE (patron `bancs/climatique.py`) vérifiant :
- part pioneer en couvert DÉCROÎT après le pic (ne reste pas ~95 %) ;
- part cumulée fixer+grass+competitor CROÎT et dépasse un seuil (ex. > 40 %) avant
  ~15 ans ;
- présence des tardifs dans la banque-sol (`sbFix`/`sbGra`/`sbCmp` non nuls).
Réutiliser le patron d'oracle en tendance/borne (pas de hash figé — un banc décrit
un monde, l'oracle décide quoi observer). Le script jetable `/tmp/diag_symbiose.py`
sert de référence comportementale (composition an par an).

## Golden attendu
**RE-FIGÉ (c'est le BUT du tronçon : la trajectoire de succession change).**
Relancer `python3 -m tests.test_golden`, vérifier que la dérive est COHÉRENTE
(les tardifs apparaissent, pioneer ne sature plus), consigner le nouveau hash
dans le test + `00_etat.md` avec la raison. Idem `test_population` si cascade
T_sol→vie macro (patron connu). Re-figeages annoncés uniquement.

## À NE PAS faire
- Ne pas scripter la bascule (pas de « à l'année X, remplacer pioneer ») : elle
  doit ÉMERGER du flux OM (philo #2).
- Ne pas supprimer `soil_deep` du reste du moteur (il sert ailleurs) — on ne
  change QUE le signal d'amorçage des tardifs.
- Pas de RNG live.

## Clôture
`00_etat.md` (§REPRISE + hash golden), D25/D56 dans `DETTE.md` (succession
re-déverrouillée). Commit.
