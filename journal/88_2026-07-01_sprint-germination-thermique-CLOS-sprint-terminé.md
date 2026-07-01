# 2026-07-01 — Sprint GERMINATION THERMIQUE (①→⑦) — SPRINT TERMINÉ

> Conception figée : `docs/conception/CONCEPTION_GERMINATION_THERMIQUE.md`.
> État partagé : `sprints/sprint_germination_thermique/00_etat.md`. Exécution en
> `/sprint-auto` (7 tronçons), clôture manuelle (recalibrage banc + journal).

## But
Brancher la **levée des graines sur la température du sol** — la vague de
printemps doit ÉMERGER du réchauffement, pas d'un proxy calendaire. Suppression
de l'artefact `spring_flush` (×2.5 en semaine 1), porte
`bell(T_sol, t_opt_eff, t_germ_tol)` aux 3 points de germination (patron exact de
la porte pH), gène `germination_thermique` en queue de `GENE_NAMES` → sélection
darwinienne **émergente** (pool-sol imprimé dans le sol, zéro code dédié).

## Tronçons (golden en cascade, chaque cran maîtrisé & annoncé)
- **①** Correctif amont : la **pluie refroidit l'air** (`Pluie prolongée −3.0`,
  `Orage −2.0` dans `TEMP_DELTA_BASE`, pluie exclue de `TEMP_DRIVEN` → garde son
  humidité). Banc/oracle `pluie_thermique` + helper `champs_climat`. Golden re-figé
  `2d9b9de1…` (ex-`0d3ca606…`).
- **②** Porte thermique `bell(T_sol,…)` posée aux 2 points actifs (`succession.py`),
  attributs `t_germ_opt/t_germ_tol` littéraux sur `PlantBase` (couche `plants`
  n'importe jamais `fields`). NEUTRE — golden `2d9b9de1…` intact. Écart au kickoff :
  `t_germ_tol=300.0` (et non 30) = plus petite demi-largeur qui garde `bell ≈ 0.996`
  sur la plage T_sol réelle, donc golden strictement inchangé.
- **③** Plancher `T_GERM_FLOOR=5.0 °C` (court-circuit binaire sous ~5 °C) + **typage
  des 27 espèces** (frileuses opt 20–24/tol 6–8, rustiques opt 10–13/tol 10–14, reste
  interpolé). Golden re-figé `f4a652e0…` : dérive cohérente et localisée à la
  germination FÉRALE (198→145 levées/2 ans, 50→46 plantes, jardin vivant).
- **④** Gène `germination_thermique` EN QUEUE de `GENE_NAMES` (canaux de hash
  préservés), `t_opt_eff = t_germ_opt − GERM_GENE_SHIFT·(gène−1)` (SHIFT 3.5 °C) sur
  grain propre + pool féral (`GeneStat.mean`). Golden re-figé `2b99457b…` — prouvé
  que la dérive = **seulement** la clé ajoutée au vecteur sérialisé (`GERM_GENE_SHIFT=0`
  ⇒ même hash : la sim est strictement inchangée au démarrage, la sélection émerge
  plus tard).
- **⑤** Suppression **intégrale** de `spring_flush` (fonction + appel `boucle.py` +
  export `sim/__init__.py` + orphelins de mesure). Golden re-figé `ae445d3f…` : la
  vague de printemps n'est plus dopée, elle ÉMERGE de la porte thermique (germinations
  par saison concentrées aux saisons chaudes, plancher froid mordant l'hiver).
- **⑥** Banc multifacteur `germination_multifacteur` (`bancs/climatique.py`, damier
  12×12) + oracle 9 checks en tendance/borne — outille le calibrage des portes (T_sol,
  pH, frileuse vs rustique, lumière). NEUTRE — golden `ae445d3f…` inchangé.
- **⑦** Voix narratives : concept transversal NEUF `germination_thermique` dans
  l'encyclopédie (`CONCEPTS`, 3 niveaux) + fenêtre thermique ajoutée aux fiches des
  espèces typées saillantes ; gabarit interprétatif `germination` enrichi dans le
  carnet. NEUTRE — golden `ae445d3f…` inchangé (corpus read-only hors tick).

## Cascade & clôture
- **Golden FINAL = `ae445d3f a2df9b8d95b45f663552f75de113eb540ed9066e81eb8d034b1a8e3c`**,
  stable depuis ⑤ (⑥⑦ neutres).
- **Re-figeage `population_hash`** (`tests/test_population.py`) `4928300b…`→`95be03f6…` :
  cascade attendue T_sol → vie macro, DÉJÀ périmé sur l'état propre du ③ (indépendant du
  gène ④). Décision Nico d'entériner (commit `767ce2d`).
- **Recalibrage banc `semis_tempere`** (biotique, FAIL pré-existant « poivron non levé ») :
  le poivron (`t_germ_opt=24`, la Solanaceae la plus thermophile) exige désormais un sol
  chaud. Fix porté dans le **harnais d'oracle**, pas dans la fabrique — le banc décrit un
  monde statique, l'oracle décide QUAND l'observer (comme `run_banc_trace` pour la
  floraison transitoire du verger) : paramètre optionnel rétrocompatible `week_depart=1`
  sur `_monter`/`run_banc`, observation du semis en plein été (`week_depart=20`). Amorce
  `temperature_sol=24.0` **retirée** (inefficace : l'inertie thermique la relaxe vers T_air
  dès le 1er tick). Test biotique 9/9, golden INCHANGÉ (un banc ne monte jamais pour
  smoke/full). Commit `fix(bancs) : recalibre semis_tempere en saison chaude`.

## Décision de design consignée
**Les dérives en CASCADE d'un sprint moteur sont entérinées à la clôture, pas
combattues** : quand une mécanique nouvelle (ici la lecture de T_sol par la
germination) modifie légitimement un état aval (vie macro → `population_hash`) ou
invalide une hypothèse de banc (semis en hiver), on **re-fige/recalibre en le
signalant** (dérive localisée, expliquée, prouvée cohérente), on ne rétro-adapte pas
le moteur pour préserver un hash. Le golden reste la référence *comportementale*,
son re-figeage est un acte maîtrisé.

## Reste (hors sprint)
Rien de bloquant. Le banc `germination_multifacteur` reste disponible pour le
calibrage fin des portes de germination (T_sol, pH, frileuse vs rustique) au F5.
Aucun point F5 (moteur pur, C# non concerné sur tout le sprint).
