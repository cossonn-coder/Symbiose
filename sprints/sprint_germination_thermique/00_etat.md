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
- [x] ④ Gène `germination_thermique` — RE-FIGÉ MAÎTRISÉ
      (golden `2b99457b71a1382afd8f171d644d843525a1f99c1a8a00322f77de553ba984d3`,
      ex-`f4a652e0…`). Gène ajouté EN QUEUE de `GENE_NAMES` (`plants/genetics.py`,
      canaux de hash préservés) ; `clamp_gene`[0.40,1.60]/`neutral_genes`=1.0 le
      gèrent déjà ; héritage AUTO via `child_genes` (zéro code ajouté). Constante
      `GERM_GENE_SHIFT=3.5 °C` posée à côté de `T_GERM_FLOOR` (`fields/ecofields/
      constants.py`). Décalage `t_opt_eff = t_germ_opt − GERM_GENE_SHIFT·(gène−1)`
      injecté aux 2 points actifs de `succession.py` : grain PROPRE
      (`grain.genes.get`) + pool FÉRAL (helper `_germ_gene_mean`, `GeneStat.mean`,
      défaut 1.0 propre). Sélection darwinienne ÉMERGENTE (zéro code dédié).
      **Dérive golden = clé de gène ajoutée au vecteur sérialisé UNIQUEMENT** :
      prouvé par `GERM_GENE_SHIFT=0` ⇒ MÊME hash `2b99457b…` (comportement de sim
      STRICTEMENT inchangé au démarrage, le pool féral neutre 1.0 ne décale rien sur
      2 ans de smoke ; la sélection émerge plus tard). 46 plantes (= ③). Suites
      connexes vertes (planter, competition, catalogue_lot2, biennial, evergreen,
      encyclopedie, signes). **test_population HORS périmètre** : son `population_hash`
      (`4928300b…`) était DÉJÀ périmé sur l'état git propre du ③ (échouait avant ④,
      obtenu `95be03f6…` identique avec/sans mon gène) → à re-figer côté sprint
      population, pas ici. Build C# non concerné. LDC succession.py 202 code-pur (🟢).
- [x] ⑤ Suppression `spring_flush` (flush émergent) — RE-FIGÉ MAÎTRISÉ
      (golden `ae445d3fa2df9b8d95b45f663552f75de113eb540ed9066e81eb8d034b1a8e3c`,
      ex-`2b99457b…`). Fonction `spring_flush` ENTIÈRE supprimée de `sim/succession.py`
      (le ×2.5 calendaire de semaine 1) ; appel + bloc `if week_in_year ==
      SAISONS["printemps"].start` retirés de `sim/engine/boucle.py:171-176` (import
      `succession` nettoyé ligne 33 ; `SAISONS` CONSERVÉ, encore utilisé l.436) ;
      export retiré de `sim/__init__.py:18`. Orphelins de mesure nettoyés dans
      `tests/_mesure_competition.py` (compteur + print « spring flush » morts).
      `grep -rn spring_flush data/code/` = VIDE. **Dérive golden COHÉRENTE** : la
      vague de printemps n'est plus dopée par un proxy calendaire, elle ÉMERGE de la
      porte thermique (②③④). Vérif de sens OK — germinations par saison (2 ans) :
      hiver 27 / printemps 37 / été 41 / automne 36 → levées concentrées aux saisons
      chaudes (plancher `T_GERM_FLOOR` freine l'hiver), pas d'effondrement. 48 plantes
      vivantes (vs 46 au ④), jardin VIVANT. Suites connexes vertes (planter 18/18,
      competition 14/14, biennial, evergreen, encyclopedie 18/18, signes 8/8). Build C#
      non concerné. LDC succession.py 142 code-pur (🟢, ex-202).
- [x] ⑥ Banc multifacteur `germination_multifacteur` + oracle — NEUTRE
      (golden `ae445d3f…` INCHANGÉ). Banc dans `bancs/climatique.py` (thème
      thermique) : DAMIER de tuiles 12×12 (144 grains/tuile) identiques sauf UN
      facteur balayé. Deux balayages — T_sol ∈ {0,5,8,11,14,18,22,26,30} °C ×
      {tomate FRILEUSE opt22/tol7, carotte RUSTIQUE opt13/tol10}, et pH ∈
      {4,5,6,6.8,7.5,8.5} × carotte (à T_sol 18 °C). Helper `_gmf_tile` (niche
      ouverte + succession férale COUPÉE + grain sur chaque plot). Enregistré dans
      `BANCS`. Oracle `test_germination_multifacteur` (tests/bancs/
      test_climatique.py) : 9 checks en TENDANCE/BORNE, tous OK — levée NULLE sous
      `T_GERM_FLOOR` (0 °C), carotte croît 5→14 puis décroît 18→30, tomate croît
      11→26, carotte > tomate au frais (11 °C : 0.68 vs 0.13), cloche pH (6.8 >
      4.0 ET > 8.5), niche ∝ lumière. **DÉCISION DE DESIGN (fenêtre = 1 TICK)** :
      T_sol forcée RELAXE vers l'équilibre air-piloté (THERMAL_INERTIA 0.5,
      ~6 sem) → le gradient n'est NET qu'au 1er tick ; `eco.lumiere` est
      ENTIÈREMENT recalculée par `tick_light` chaque tick (un forçage de champ est
      écrasé) → la sensibilité lumière est assertée par LECTURE DIRECTE de
      `niche_index` (pure), pas par balayage engine. pH/T_sol passent par l'engine
      (1 tick). Pure composition → golden NEUTRE (vérifié `ae445d3f…`). Suite
      climatique 20/20. Build C# non concerné. LDC : climatique.py 75 code-pur
      🟢, test 105 🟢. (semis_tempere « poivron » FAIL pré-existant, hors périmètre.)
- [x] ⑦ Voix narratives (encyclopédie + carnet) — NEUTRE
      (golden `ae445d3f…` INCHANGÉ, corpus/carnet read-only hors tick). **Encyclopédie**
      (`sim/encyclopedie_corpus.py`) : concept TRANSVERSAL NEUF `germination_thermique`
      dans `CONCEPTS` (≠ espèce, comme `rosee`/`gelee_blanche`) — N1 « rien ne lève
      encore puis ça perce, chacune à son heure », N2 fenêtre de réveil + plancher froid
      + rustiques vs thermophiles (sans chiffre HUD, philo #5), N3 vague de printemps
      ÉMERGENTE (pionnières au frais → frileuses à la chaleur) + sélection darwinienne
      (lignées qui lèvent plus tôt). Plus, fenêtre thermique de levée ajoutée au N2 (et
      succession au N3) des espèces typées saillantes : tomate, poivron, courgette,
      basilic, figuier (frileuses) ; mâche, carotte, bourse_pasteur, paturin (rustiques).
      Texte botanique existant NON réécrit (ajout d'une phrase ciblée). **Carnet**
      (`sim/carnet.py`) : gabarit INTERPRÉTATIF de `germination` enrichi (« le sol a
      enfin atteint sa chaleur de réveil — mes lignées lèvent plus tôt chaque année »),
      descriptif intact. Mapping `germination → succession` figé (doc §5.0) NON touché ;
      `stagnation/froid → météo` couvre déjà « le froid retient ». DÉCISION : pas
      d'entrée carnet « non-levée » — une graine qui ne lève PAS n'émet aucun marqueur
      au ledger, donc rien à tabuler sans toucher le moteur (interdit, golden neutre) ;
      ces descriptifs « rien ne lève encore » sont portés par l'encyclopédie. Golden
      `ae445d3f…` inchangé ; suites vertes : encyclopedie 18/18, carnet 19/19, journal
      15/15, pages 49/49. Build C# NON concerné. LDC corpus 227🟢 / carnet 137🟢.

## §REPRISE
Tronçons ①②③④⑤⑥ CLOS (non commités — Nico commit). Golden STABLE depuis ⑤
`ae445d3fa2df9b8d95b45f663552f75de113eb540ed9066e81eb8d034b1a8e3c` — le ⑥ est
NEUTRE (banc/oracle pur, jamais monté au smoke/full), golden VÉRIFIÉ inchangé.
Le banc `germination_multifacteur` (registre `BANCS`) outille le calibrage des
portes de germination (T_sol, pH, frileuse vs rustique, lumière) ; son oracle
(`tests/bancs/test_climatique.py::test_germination_multifacteur`, 9 checks en
tendance/borne, 20/20 sur la suite climatique) valide le SENS des portes ②③④⑤.
Fenêtre d'observation = 1 tick (T_sol forcée relaxe ensuite ; lumière recalculée
par l'engine donc assertée par lecture directe de `niche_index`). Fichiers ⑥ :
`bancs/climatique.py`, `bancs/__init__.py`, `tests/bancs/test_climatique.py`.
**À signaler à Nico** : (a) `tests/test_population.py` a un `population_hash`
(`4928300b…`) PÉRIMÉ depuis le ③ — re-figer à `95be03f6…` quand Nico jugera
(hors périmètre thermique) ; (b) banc `semis_tempere` « poivron » FAIL
PRÉ-EXISTANT (sur git propre, indépendant de ⑥) — calibrage à voir hors sprint.
**Note pour ⑦** (voix narratives encyclopédie+carnet) : NEUTRE prévu. Lire
`CLAUDE.md` + ce fichier + `07_*.md`, lancer `python3 -m tests.test_golden` AVANT
(doit afficher `ae445d3f…`).
