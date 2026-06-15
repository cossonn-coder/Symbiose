## 2026-06-03 — Sprint implémentation météo : déterminisation → température → réponses médiées → forecast/signes (Python)

### Contexte

Implémentation de la conception météo figée (`docs/conception/CONCEPTION_METEO.md`),
couvrant **D16** (forecast) + **Z2** (signes). Sprint **gros** découpé en
**4 sous-sprints autosuffisants** (`sprints/sprint_meteo_impl/`), chacun une unité
testable préservant ou re-figeant le golden une seule fois.

### Réalisé (par sous-sprint)

1. **Déterminisation** — `sim/weather.py` créé : `weather_at(seed, week)` PURE
   (catalogue + saisonnalité §1.3) + `WeatherEvent(kind, intensity,
   duration_weeks, scope)` + `forecast`. **Retrait de `random.seed(42)`** : les
   3 derniers `random.random()` live de `sim/effects.py` (add_rondelle,
   reduce_health, PropagateDisease) migrés vers `_hash_noise` (canaux 19/23/29).
   Golden re-figé `fbb0c16b…→a2fefba2…`.
2. **Température** — champ ambiant `EcoFields.temperature` (normales saisonnières
   `temp_norm` + deltas météo `temperature_delta`), gate `ok_temp` dans la
   croissance (stagnation hivernale), couplage évaporation↔température. **Cadence
   météo passée en HEBDOMADAIRE** (décision Nico), `P_EVENT 0.60→0.15`. Golden
   re-figé `a2fefba2…→4bcae3a3…`.
3. **Réponses médiées par gène** — gène `rusticite_froid` ajouté au vecteur
   génétique (héritage décorrélé, golden-neutre tant que le dégât ne change pas) ;
   gel et grêle quittent la voie `health` plate pour un dégât **médié**
   (`sévérité_milieu × susceptibilité_gène × (1 − protection_paillage)`, helper
   `Engine._mediated_damage`). **Gel piloté par le MILIEU** (`temp < 0`), pas par
   le nom de l'événement — forme la plus pure flux→contrainte→réponse. Golden
   re-figé `4bcae3a3…→63bfdac4…`.
4. **Forecast + signes (read-only)** — `weather_signs(seed, week, horizon=2)` PURE
   + `WeatherSign(kind, in_weeks, signs, signed)` + table `SIGN_TABLE` (§4.1) +
   masque `is_signed` (canal `K_SIGN`, §4.3, ~80 % signés). Test dédié
   `tests/test_signes.py` (8/8). **Golden INCHANGÉ `63bfdac4…`** (PASS sans
   `--capture`) → preuve qu'aucun couplage n'a fui dans la simulation.

### Décisions

- **Path A (déterminisation totale)** : les `random.random()` live cachés derrière
  `random.seed(42)` étaient incompatibles avec « déterminisme sans seed global » →
  tous migrés vers `_hash_noise`. Le golden devient vraiment reproductible.
- **Cadence météo hebdomadaire** : `weather_at` consulté chaque semaine (plus
  seulement au passage de saison) → le **forecast est pleinement honnête** (ce
  qui est prévu *est* ce qui tombe, prouvé sur 1040 semaines × horizon 2).
- **Température = champ ambiant (Option B)** : gel/canicule/redoux deviennent des
  **deltas de température** transitoires, plus des malus directs.
- **Retour `weather_signs` = structure complète + flag `signed`** (décision Nico) :
  l'appelant (palier/UI, D12) filtre selon la maîtrise — « marche transcendant
  gratuite » sans re-toucher `weather.py`. L'événement ne change jamais ; seule la
  visibilité du signe dépend du palier (philo #3 intacte).

### Hors périmètre (gated, non fait)

- **Vigueur** préparation/réaction (voiles d'hivernage, tuteurs, brise-vent) —
  gated **D11**. La **verse (tempête)** est « prête côté gène `hauteur` » mais
  attend le système de tuteur.
- **Paliers de maîtrise météo** + bascule interprétative du carnet + révélation
  transcendant côté UI — gated **D12**.
- **Rendu des signes** (sprites oiseaux/ciel/anneau) — côté Godot, plus tard.
- **Portage C#** — dette **D24**.

### Observation à creuser (post-test, pas un bug)

Sur 40 ans, le jardin se fait dominer par les **pionnières de la succession
spontanée** (sans vecteur génétique) → la **sélection visible du froid** reste
discrète tant que les populations vivantes sont quasi-neutres. La médiation mord
bien (survie/score baissent) mais l'émergence génétique demande un recalibrage
(intensités de gel, balance pionnières/cultivées) — sprint ultérieur.

### Hash golden (journal de re-figeage)

`fbb0c16b…` → `a2fefba2…` (01) → `4bcae3a3…` (02) → `63bfdac4…` (03) →
`63bfdac4…` **inchangé** (04, read-only).

---
