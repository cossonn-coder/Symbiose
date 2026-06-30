## 2026-06-30 — Conception GERMINATION THERMIQUE (lit T_sol) — FIGÉE

**Décision :** la germination doit lire la **température du sol**, pas le
calendrier. Aujourd'hui la levée module la niche par des portes (ombre,
perturbation, `bell(pH)`) mais **jamais** par `T_sol` ; la seule saisonnalité est
l'artefact calendaire `spring_flush` (`succession.py:236`, ×2.5 selon `week`) — un
`if semaine==1` déguisé qui viole la philo #2/#3.

**Conception arbitrée et validée** (`/conception` phase B, accord Nico « ok tu
peux y aller ») : doc `docs/conception/CONCEPTION_GERMINATION_THERMIQUE.md`.
Philo imposée par Nico = **téléonomie + sélection darwinienne + émergence** : la
vague de printemps doit ÉMERGER de chaque graine germant quand SA température
locale franchit SON seuil, pas d'un calendrier.

**Modèle :** porte multiplicative `niche *= bell(T_sol_local, t_opt_eff, t_germ_tol)`
aux **3 points** de germination (patron exact de la porte pH), `T_sol` déjà
spatialisé (`eco.temperature_sol.at_plot`). Paramètres d'espèce `t_germ_opt`/
`t_germ_tol` **littéraux** sur `PlantBase` (couche `plants` n'importe jamais
`fields`) ; constantes globales `T_GERM_FLOOR` (~5 °C, plancher froid) et
`GERM_GENE_SHIFT` côté `fields`/`sim`. Nouveau gène `germination_thermique` **en
queue** de `GENE_NAMES` (préserve les canaux de hash, héritage automatique) →
**sélection darwinienne émergente** imprimée dans le pool-sol (`GeneStat.mean`),
zéro code de sélection.

**Correctif amont retenu** (Nico « corriger aussi ») : la pluie ne refroidit PAS
l'air aujourd'hui (`Pluie prolongée`/`Orage` absents de `TEMP_DELTA_BASE`,
`weather.py:65`) → on ajoute un delta froid (placeholder ~−2 à −3 °C). Re-figeage
golden au tronçon ①.

**Découpage figé : 7 tronçons** (`sprints/sprint_germination_thermique/`,
kickoffs autosuffisants) — ① correctif T_air pluie + banc `pluie_thermique`
(RE-FIGÉ) ; ② porte thermique NEUTRE (INTACT) ; ③ `T_GERM_FLOOR` + typage de TOUT
le catalogue (RE-FIGÉ) ; ④ gène `germination_thermique` (RE-FIGÉ) ; ⑤ suppression
`spring_flush` = flush émergent (RE-FIGÉ) ; ⑥ banc multifacteur (NEUTRE) ; ⑦ voix
narratives encyclopédie + carnet, OBLIGATOIRE (NEUTRE).

Toilette le fossile `BACKLOG.md:48` (« la germination devrait lire le sol, pas
l'air » — reste de la phrase d'origine, désormais conçu). **Conception seule, pas
d'implémentation** — prête pour `/sprint-auto sprint_germination_thermique`.
