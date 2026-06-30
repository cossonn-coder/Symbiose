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
- [x] ① Correctif T_air pluie + banc/oracle `pluie_thermique` — RE-FIGÉ
      (golden `2d9b9de1c15abdf4f34bf41a0e6ee72eec5445962c9ae34f01e1ff40a79604af`,
      ex-`0d3ca606…`). `TEMP_DELTA_BASE` alimenté `Pluie prolongée: -3.0`,
      `Orage: -2.0` ; pluie EXCLUE de `TEMP_DRIVEN` (garde son humidité via
      WEATHER_ALEA). Banc `pluie_thermique` + helper `champs_climat` (oracle) +
      test (4 couplages, 11/11 OK). Build C# non concerné.
- [x] ② Porte thermique NEUTRE (`bell(T_sol,…)` aux 2 points actifs) — INTACT
      (golden `2d9b9de1…` inchangé). Attributs `t_germ_opt=18.0`/`t_germ_tol=300.0`
      sur `PlantBase` (patron pH) ; porte `bell(T_sol,t_germ_opt,t_germ_tol)` ajoutée
      après la porte pH dans `_lever_grains_en_attente` (point 1) ET `succession`
      (point 2, via dict `arch_temp` + nouveau param `germination_candidates(arch_temp=)`).
      `spring_flush` NON touché (suppression au ⑤). **ÉCART au kickoff** : le littéral
      `t_germ_tol=30.0` prévu faisait DÉRIVER le golden (`bell` ≈ 0.67–0.77 sur la plage
      T_sol réelle −1→+33 °C → flips de germination) ; sweep → **300.0** = plus petite
      demi-largeur qui garde le golden INTACT (`bell` ≈ 0.996–0.997). Build C# non concerné.
- [ ] ③ `T_GERM_FLOOR` + typage de tout le catalogue — RE-FIGÉ
- [ ] ④ Gène `germination_thermique` — RE-FIGÉ
- [ ] ⑤ Suppression `spring_flush` (flush émergent) — RE-FIGÉ
- [ ] ⑥ Banc multifacteur `germination_multifacteur` + oracles — NEUTRE
- [ ] ⑦ Voix narratives (encyclopédie + carnet) — NEUTRE

## §REPRISE
Tronçons ①② CLOS (non commités — Nico commit). Golden INTACT `2d9b9de1…`.
La plomberie thermique est posée et NEUTRE (`bell(T_sol,…)` aux 2 points actifs ;
`spring_flush` reste sur ⑤). **Note pour ③** : `t_germ_tol` par défaut a dû être
porté à **300.0** (pas 30.0 — voir écart au ②) pour la neutralité ; au ③, le typage
par espèce DOIT donner des `t_germ_tol` BIEN plus étroits (ordre 5–15 °C) pour que
la porte morde, sinon aucune sélection thermique. Prochain : ③ « `T_GERM_FLOOR` +
typage du catalogue » — RE-FIGÉ maîtrisé attendu. Lire `CLAUDE.md` + ce fichier +
`03_*.md`, lancer `python3 -m tests.test_golden` AVANT (doit afficher `2d9b9de1…`).
