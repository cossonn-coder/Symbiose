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
- [x] ③ `T_GERM_FLOOR` + typage de TOUT le catalogue — RE-FIGÉ MAÎTRISÉ
      (golden `f4a652e05511ec8c1fc4239c377f8775a3148ef03e58c99e79a3a32c38f7485e`,
      ex-`2d9b9de1…`). Constante `T_GERM_FLOOR=5.0 °C` posée dans
      `fields/ecofields/constants.py` (à côté des constantes thermiques, exportée par
      `import *`). Plancher BINAIRE multiplicatif AVANT la cloche aux 2 points actifs de
      `succession.py` (T_sol < FLOOR → `continue` au point 1 / `arch_temp={a:0.0}` au
      point 2 ; `spring_flush` n'a jamais reçu la porte, supprimé au ⑤). **27 espèces
      typées** `t_germ_opt`/`t_germ_tol` (littéraux) : frileuses opt 20–24/tol 6–8
      (Tomate, Poivron, Haricot, Tournesol, Basilic, Courgette, Figuier méditerranéen),
      rustiques opt 10–13/tol 10–14 (Mâche, Carotte, Moutarde + 4 adventices), reste
      interpolé (vivaces tempérées 14–16, myrtille 13/9). Défaut ligneux tempéré 14/11 sur
      `PerennialWoody`. Dérive golden COHÉRENTE & localisée à la germination FÉRALE :
      198→145 levées/2 ans, 50→46 plantes, jardin VIVANT, 4 archétypes germent toujours
      (le froid hivernal + le typage mordent, pas d'effondrement). Suites connexes vertes
      (planter, competition, catalogue_lot2, lifecycle, biennial, evergreen, encyclopedie,
      signes). Build C# non concerné. LDC OK (cultivees 320 code-pur, jaune mono-responsabilité).
- [ ] ④ Gène `germination_thermique` — RE-FIGÉ
- [ ] ⑤ Suppression `spring_flush` (flush émergent) — RE-FIGÉ
- [ ] ⑥ Banc multifacteur `germination_multifacteur` + oracles — NEUTRE
- [ ] ⑦ Voix narratives (encyclopédie + carnet) — NEUTRE

## §REPRISE
Tronçons ①②③ CLOS (non commités — Nico commit). Golden RE-FIGÉ MAÎTRISÉ au ③
`f4a652e05511ec8c1fc4239c377f8775a3148ef03e58c99e79a3a32c38f7485e` (ex-`2d9b9de1…`).
La porte thermique MORD maintenant : plancher froid `T_GERM_FLOOR=5.0` (binaire, avant
la cloche) + 27 espèces typées (frileuses tol 6–8, rustiques tol 10–14). Dérive
cohérente (germination férale réduite ~27 %, jardin vivant, 4 archétypes OK).
**Note pour ④** : le gène `germination_thermique` s'ajoute EN QUEUE de `GENE_NAMES`
(`plants/genetics.py`, préserve les canaux de hash) ; décale l'optimum effectif
`t_opt_eff = t_germ_opt − GERM_GENE_SHIFT·(gene−1.0)` aux 2 points actifs de
`succession.py` (grain propre `grain.genes` + pool féral `GeneStat.mean`).
`GERM_GENE_SHIFT` = nouvelle constante `fields`/`sim` (~3–4 °C). RE-FIGÉ maîtrisé
attendu (l'héritage neutre 1.0 ne décale rien, mais l'échantillonnage du pool peut
bouger). Lire `CLAUDE.md` + ce fichier + `04_*.md`, lancer `python3 -m tests.test_golden`
AVANT (doit afficher `f4a652e0…`).
