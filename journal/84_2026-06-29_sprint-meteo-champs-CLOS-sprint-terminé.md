## 2026-06-29 — Sprint MÉTÉO → CHAMPS (dont rosée) — SPRINT TERMINÉ (exécution autonome `/sprint-auto`)

**Objet.** Remplacer le couplage météo→champs *provisoire* (deltas plats
`WEATHER_ALEA`) par des **flux médiés** (philo de design #2) et **compléter les
flux manquants** — rosée/gelée blanche, lessivage NPK par la pluie, microbiome
climatique — pour que chaque événement météo agisse sur **tous** les champs qu'il
influence réellement. Conception figée au préalable :
`docs/conception/CONCEPTION_METEO_CHAMPS.md`. Exécution en 5 tronçons par
`/sprint-auto` (orchestrateur + sous-agents au contexte frais).

**Invariant golden.** Ce sprint modifie la physique du tick → le golden (smoke
2 tuiles × 4 ans) **a bougé à chaque cran**, chaque re-figeage **maîtrisé et
annoncé** (dérive localisée + expliquée, jamais aveugle, 50/50 plantes vivantes
à chaque étape). Aucun RNG neuf (philo #3 — la météo est déjà tirée par
`_hash_noise`).

**Trajectoire du golden / population :**
- ① `db5e7c66…` → `b2a89932…` (pop `9ba39ab7…` → `cd153460…`)
- ② `b2a89932…` → `bf3c5c95…` (pop `cd153460…` → `239766b6…`)
- ③ `bf3c5c95…` → `18ef4f04…` (pop INCHANGÉE `239766b6…`)
- ④ `18ef4f04…` → `8f8b6741…` (pop `239766b6…` → `1d89da0a…`)
- ⑤ `8f8b6741…` → **`11eceeb9…`** (pop `1d89da0a…` → **`ef5d62aa…`**)

**Tronçons.**
- **① Humidité médiée.** Retrait des deltas plats humidité de `WEATHER_ALEA` ;
  table PURE `PLUIE_APPORT` côté `fields` (miroir `PRECIP_NORM`) ; `tick_hydrology`
  infiltre `BASE_RAIN + pluie_event` ∝ structure du sol, borné ≥ 0. Assèchement
  désormais **émergent** via l'évaporation∝T déjà en place. **Décision :** humidité
  plus réaliste (plus sèche) = comportement attendu §2.1.
- **② Rosée & gelée blanche.** Helper pur `fields/ecofields/rosee.py` (miroir
  `thermique.py`) : `tick_rosee` relit `t_min_nuit_at`, dérive un point de rosée
  local, dépose la condensation en continuum — rosée liquide (>0 °C → humidité+)
  ou gelée blanche (≤0 °C → champ `givre` + **fonte différée**). Signes diégétiques
  `💧 rosée` / `❄ gelée blanche`. **Décision :** dégât foliaire du givre (§C, marqué
  *OPTION* au kickoff) DIFFÉRÉ — `GIVRE_SEVERITY_REF` réservée, à câbler plus tard.
- **③ Lessivage NPK.** AMPLIFIE le lessivage EXISTANT (`tick_decomposition`, CEC)
  par l'eau drainée — ne le recrée pas. `tick_hydrology` mémorise sa perte de
  drainage (`drainage_last`), `tick_decomposition` la lit et élève la rétention à
  une puissance > 1. Hiérarchie d'ions **N≫K>P** (phosphore épargné). Population
  inchangée.
- **④ Microbiome climatique.** Terme MULTIPLICATIF `f_clim = f_temp · f_hum` sur
  l'activité microbienne (PAS de champ neuf). Cloche gaussienne en T (~20 °C),
  facteur humidité, plancher 0.05. Effet : litière qui s'accumule l'hiver/au sec
  (recyclage ralenti par le climat normand), repart au réchauffement.
- **⑤ Interconnexions + voix + pont.** (A) faune abreuvée par la rosée
  (`eco.rosee_last` lu par les habitats limace/cloporte) ; (B) captation foliaire
  (un couvert en `drought_stress` capte la rosée → soulagement marginal = seule
  source de la dérive golden de ⑤) ; (C) voix : parsing rosée/gelée dans
  `evenements.py`, concept « météo » au carnet + fiche encyclopédie (dict `CONCEPTS`
  séparé) + 2 pages secrètes (P21 rosée de la Saint-Jean, P22 herbier de la gelée
  blanche) ; (D) pont snapshot : bloc `condensation` sparse, protocole 0.5.9 →
  **0.5.10**.

**Effet de bord corrigé.** ① a exposé un off-by-one latent du **gate des
bisannuelles** (`croissance.py`) : la montaison s'ouvrait dès `age_years >= 1.0`,
soit pile en semaine 52 où l'âge accumulé vaut ~1.0 au bruit flottant près →
`test_biennial` (jusque-là vert par chance d'une tuile inondée) cassait.
**Décision Nico (option B) :** corriger le gate avec une marge d'un demi-tick
(`ANNEE_1 = 1.0 + 0.5/52`) → rosette toute l'an 1, montaison en semaine 53.
Golden neutre (aucune bisannuelle dans le smoke). Commit séparé `8bdc39d`.

**Tests.** Toutes les suites vertes (`golden`, `biennial`, `rosee` 10/10,
`evenements`, `carnet`, `encyclopedie`, `pages` 49/49, `journal`, `magazine`,
`signes`, `population`, `lessivage` 7/7, `microbiome_clim` 12/12).
`test_sim_server` reste **205/206** — la seule rouge est le **pommier pré-âgé qui
ne noue pas de fruits**, **PRÉ-EXISTANTE** (déjà rouge sur la baseline `f7811b5`,
sans rapport avec ce sprint, à investiguer hors sprint).

**À valider F5 (Nico).** Calibrage des constantes placeholders (`PLUIE_APPORT`,
`ROSÉE_*`, `LESSIVAGE_PLUIE_K`, `MICROBE_T_OPT/_TOL`, etc.) — observer en jeu que
l'humidité réaliste ne déséquilibre pas la croissance, et la litière/recyclage
saisonnier. **Dette :** rendu C# des gouttes/givre (D24), dégât foliaire du givre
(②, option différée), pommier pré-âgé `test_sim_server` (pré-existant).
