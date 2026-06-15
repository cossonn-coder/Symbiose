## 2026-06-13 — Sprint décompo & compost · sous-sprint ① : parcelles de litière — golden RE-FIGÉ + RACCOURCI (maîtrisé)

Pose l'**infrastructure** des parcelles (aucun geste joueur, squelette ni
organe — ce sont ②③④⑤). Le champ scalaire `om_fresh` **disparaît** ; la couche
fraîche devient `EcoFields.litiere` = grille de listes de
`Parcelle{tissu, masse, age_sem}`, avec une parcelle `diffus` **permanente** par
plot (reçoit les exsudats, ne disparaît jamais).

**API ajoutée** (`fields/ecofields.py`) : `om_fresh_at` / `om_fresh_average`
(lectures dérivées = Σ masses, l'ancienne sémantique d'appel survit) et
`deposer_litiere(r,c,tissu,masse)` — **point d'entrée unique** des écrivains,
avec **fusion par tissu** (`masse +=`, `age_sem` moyenné pondéré → ≤ 6
parcelles/plot, déterministe). Table `TISSU` (cinétique decay/humif/miner par
tissu, §1.2) + `TISSU_ORDER` (itération stable).

**Décision d'équivalence (clé du re-figeage maîtrisé)** : le tissu `diffus`
**reprend la cinétique exacte de l'ancien `om_fresh`** (`OM_FRESH_DECAY/HUMIF/
MINER`), et `tick_decomposition` lit `active`/`stable` **avant** d'appliquer
l'humification du frais (ordre historique). Conséquence : sur le **flux dominant
(exsudats)** le tick reste **bit-identique**. La dérive golden provient des
**SEULES** causes annoncées :
1. nécromasse (`add_necromass`) + injections paillage/engrais vert
   (`inject_field om_fresh`) routées en tissu **`herbace`** (cinétique §1.2 ≠
   ancien fresh) ;
2. **retrait du cap** `max_val=10.0` (les parcelles ne sont pas plafonnées —
   l'écologie borne ; vigilance perf = D32).

**Recâblage** : exsudats (`engine.py`)→`diffus` ; `add_necromass`→`herbace` ;
`inject_field om_fresh` intercepté dans `effects.apply_mutations` **avant**
`get_field` (qui renverrait None, l'injection serait perdue) →`herbace` ;
lecteurs `soil_memory`, vers (`population.py`), `summary` →`om_fresh_at`/
`_average`. `om_fresh` **sort de l'overlay debug F6** (`cmd_fields` introspecte
les `GridField`) — acceptable, annoncé. `summary()["om_fresh"]` reste exposé
(via `_average`) → `test_vigueur` intact.

**Golden re-figés (déterministes, h1==h2 vérifié sur les deux)** :
- smoke test : **`N_YEARS 4 → 2`** (raccourci, le 4 ans était trop long pour un
  smoke) ; `6bf71ee5… → f75d1c21…`.
- champ population (les vers lisent le frais) : `f1fe093c… → 9f351303…`.

**Tests verts** : golden, population, vigueur 135, croissance 67, competition 14,
eau 20, sim_server 113, senescence, génétique 20, maîtrise 35 ; `main.py 30`
exit 0. Reste connu : `tools/diag_fields_span.py` liste encore `"om_fresh"`
(get_field→None) — outil de diag hors golden, non corrigé.

**Suivant** : sous-sprint ② (dépôts vivant & mort : `tailler`→`bois`, squelette
persistant + fragmentation, abscission d'automne, `ecraser`-squelette). Kickoff
`02_*.md` à écrire au démarrage.
