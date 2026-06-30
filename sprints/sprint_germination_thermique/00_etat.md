# Sprint « germination thermique » — état partagé

> État léger mis à jour en fin de chaque tronçon. Conception figée :
> `docs/conception/CONCEPTION_GERMINATION_THERMIQUE.md`. Chaque kickoff `0N_*.md`
> est **autosuffisant** (démarrage à froid : CLAUDE.md + ce fichier + le kickoff).

## But en une phrase
Brancher la **levée des graines sur la température du sol** (`bell(T_sol,…)` sur
la niche de germination) pour que la **vague de printemps ÉMERGE** du
réchauffement — supprimer l'artefact calendaire `spring_flush`, avec gène
`germination_thermique` (sélection darwinienne émergente imprimée dans le sol).

## Décisions clés (arbitrées 2026-06-30)
- Porte **multiplicative** `bell(T_sol, t_opt_eff, t_germ_tol)` aux **3 points** de
  germination (`succession.py`), patron exact de la porte pH.
- `t_germ_opt`/`t_germ_tol` **littéraux** sur `PlantBase` (couche `plants` n'importe
  jamais `fields`) ; `T_GERM_FLOOR`/`GERM_GENE_SHIFT` = constantes `fields`/`sim`.
- Gène **en queue** de `GENE_NAMES` (préserve les canaux de hash). Sélection
  darwinienne = émergente (reproduction + héritage + réensemencement), zéro code.
- Correctif amont : la **pluie refroidit l'air** (`Pluie prolongée`/`Orage` →
  `TEMP_DELTA_BASE`, `weather.py:65`).
- **Golden** : re-figé maîtrisé aux ①③④⑤, intact au ②, neutre aux ⑥⑦.

## Avancement
- [ ] ① Correctif T_air pluie + banc/oracle `pluie_thermique` — RE-FIGÉ
- [ ] ② Porte thermique NEUTRE (`bell(T_sol,…)` aux 3 points) — INTACT
- [ ] ③ `T_GERM_FLOOR` + typage de tout le catalogue — RE-FIGÉ
- [ ] ④ Gène `germination_thermique` — RE-FIGÉ
- [ ] ⑤ Suppression `spring_flush` (flush émergent) — RE-FIGÉ
- [ ] ⑥ Banc multifacteur `germination_multifacteur` + oracles — NEUTRE
- [ ] ⑦ Voix narratives (encyclopédie + carnet) — NEUTRE

## §REPRISE
Démarrage du sprint. Lire `CLAUDE.md` + ce fichier + `01_correctif_pluie.md`.
Vérifier l'arbre git propre, lancer `python3 -m tests.test_golden` AVANT pour
capturer le hash de départ, puis attaquer le tronçon ①.
