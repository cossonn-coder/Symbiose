# Sprint implémentation météo — état partagé

> **État léger, mis à jour en fin de chaque sous-sprint.** La spec de référence
> figée est [`data/code/CONCEPTION_METEO.md`](../../data/code/CONCEPTION_METEO.md)
> (Sprint conception météo, 2026-06-03). Couvre **D16** + **Z2**.
>
> Boucle : lancer `0N` → travailler → **vérifier/re-figer le golden** → mettre à
> jour ce fichier → commit → `/clear` → lancer `0N+1`.

## Où on en est

- **Sous-sprint 01 (déterminisation) : FAIT.** Météo + ravageurs déterminisés ;
  `weather_at(seed, week)` pure livrée dans `sim/weather.py`.
- **Sous-sprint 02 (température) : FAIT.** Champ `temperature` ambiant (normales
  saisonnières + deltas météo hebdo), gate `ok_temp` dans la croissance,
  évaporation couplée à la température, **météo passée en cadence hebdomadaire**
  (décision Nico). Reste 03/04.
- **Sous-sprint 03 (réponses médiées) : FAIT.** Gène `rusticite_froid` ajouté au
  vecteur génétique ; gel et grêle quittent la voie `health` plate pour un dégât
  **médié** (`sévérité_milieu × susceptibilité_gène × (1 − protection_paillage)`,
  helper `Engine._mediated_damage`). Gel piloté par le MILIEU (température < 0),
  pas par le nom de l'événement. Reste 04. ⚠ **Pas de kickoff `03_*.md`
  pré-écrit** (absent du disque) : travaillé directement depuis la spec figée
  `CONCEPTION_METEO.md` §2.3 + §7 #3-4 et les notes de passation du 02.
- **Sous-sprint 04 (forecast + signes) : FAIT.** `weather_signs(seed, week,
  horizon=2)` pure livrée dans `sim/weather.py` + `@dataclass WeatherSign(kind,
  in_weeks, signs, signed)` + table `SIGN_TABLE` (§4.1) + masque `is_signed`
  (canal `K_SIGN`, §4.3). **Read-only** : golden **INCHANGÉ** (`63bfdac4…` PASS
  *sans* `--capture`) → aucun couplage n'a fui. Test dédié `tests/test_signes.py`
  (8/8). **Sprint météo d'implémentation TERMINÉ.**
- Conception **figée** (`CONCEPTION_METEO.md`).

## Découpage (4 sous-sprints autosuffisants)

| # | Fichier | Objet | Impact golden |
|---|---|---|---|
| 01 | `01_determinisation.md` | `weather_at(seed,week)` pure + `WeatherEvent` + catalogue/saisonnalité ; retirer `random.seed(42)` | **re-figer 1×** |
| 02 | `02_temperature.md` | Champ `temperature` ambiant + normales saisonnières + gate `ok_temp` + couplage évaporation | **re-figer 1×** |
| 03 | `03_reponses_mediees.md` | Gène rusticité au froid + réécriture `appliquer_alea` (gel/grêle/verse = milieu × gène × protection ; fin voie `health` directe) | **re-figer 1×** |
| 04 | `04_forecast_signes.md` | `forecast(seed,week,horizon)` + masque de signe déterministe + table signe→événement (côté données, pas de rendu) | **neutre** (read-only) |

## Hors périmètre (ce sprint NE fait PAS)

- **Vigueur** (préparation/réaction) — gated sur D11 (non implémentée).
- **Paliers de maîtrise météo** (bascule interprétative, prévisibilité
  transcendant) — gated sur D12 (non implémentée).
- **Rendu UI** des signes (sprites oiseaux/ciel/anneau) — côté Godot, plus tard.
- Portage **C#** — dette D24.

On livre le **cœur de simulation** (météo déterministe, température, couplage,
forecast + structure des signes). Les couches Vigueur/palier/UI viendront s'y
brancher quand D11/D12 existeront.

## Discipline golden

Chaque sous-sprint qui change la simulation **régénère le golden une fois** puis
le re-fige, et **consigne ici le nouveau hash** (avant → après) + la raison.
Aucun changement de comportement non documenté.

## Journal des hash golden

- **01** : `fbb0c16b…` → `a2fefba2…`. Raison : tirage météo/ravageur + 3 effets
  discrets passés de RNG live à `_hash_noise` → séquence déterministe différente
  (mêmes types d'événements, garden survit 30 ans, contraste auxiliaires
  préservé). PASS reconfirmé après capture.
- **02** : `a2fefba2…` → `4bcae3a3…`. Raison : (a) nouveau gate `ok_temp` dans
  `_avancer_stades` (croissance bloquée sous `temp_min_growth`, défaut 5 °C →
  stagnation hivernale semaines ~1-8) ; (b) météo passée en **hebdomadaire**
  (`weather_at` consulté chaque semaine, `P_EVENT` 0.60→0.15) → nouvelle séquence
  d'événements + log enrichi (lignes 🌤 hebdo, ❄ froid, t=…°C sur les avancées) ;
  (c) évaporation couplée à la température. Vérifs : déterminisme OK (2 runs
  identiques), jardin vivant à 30 ans (9 tuiles, comptes 9-10/tuile), génétique
  20/20, contraste auxiliaires préservé (0 vs 29). PASS reconfirmé après capture.
- **03** : `4bcae3a3…` → `63bfdac4…`. Raison : gel et grêle abandonnent la voie
  `health` plate (`ReduceHealth(1)` sur tous les semis) pour un dégât **médié par
  le gène × le paillage**, mappé en points de santé entiers (floor) → nouvelle
  séquence de santé/mortalité des semis. Le gel devient piloté par la température
  ambiante (temp < 0), plus par le nom de l'événement. Vérifs : déterminisme OK
  (2 runs, hash sortie identique), jardin vivant à 30 ans (9 tuiles, 8-9/tuile vs
  9-10 avant — mortalité modérée attendue ; score 7755→7475), génétique 20/20,
  contraste auxiliaires préservé (0 vs 23). PASS reconfirmé après capture.
- **04** : `63bfdac4…` → `63bfdac4…` (**INCHANGÉ**). Raison : aucune. 04 est
  read-only sur la simulation (`tick_semaine` non touché) — il ne fait que LIRE
  `weather_at` en avance et classer. Golden PASS *sans* `--capture` = preuve
  qu'aucun couplage n'a fui dans la sim. `test_signes` 8/8, génétique/auxiliaires
  inchangés, `main.py` exit 0.

## Décisions prises en cours de route

- **La spec §0 se trompait** : la météo n'était PAS le dernier îlot non conforme.
  `sim/effects.py` avait **3 `random.random()` live** (add_rondelle, reduce_health,
  PropagateDisease), masqués par la béquille `random.seed(42)`. Décision Nico
  (Path A) : les déterminiser aussi, sinon « déterminisme sans random.seed »
  impossible et golden non reproductible. Migrés vers `_hash_noise` (canaux
  **week·19 / week·23 / week·29**, décorrélés des flux existants 1/3/5/11/13/17).
- **`sim/weather.py` créé** (kickoff l'autorisait) : `WeatherEvent(kind, intensity,
  duration_weeks, scope)` + `weather_at(seed, week)` pure (catalogue + saisonnalité
  §1.3) + `forecast()` (offert d'avance, pour le sous-sprint 04). Canaux-sentinelles
  `K_OCC/K_PICK/K_MAG/K_PEST` aux coords `90_00x` (hors grille 6×8). `P_EVENT=0.60`
  (calibrage post-test).
- **Cadence préservée** (couplage inchangé, 01) : `weather_at` consulté au **début
  de saison** seulement, mappé vers les effets `Alea` EXISTANTS via `WEATHER_ALEA`
  (dans `engine.py`). Mappings approximatifs (Sécheresse≈Canicule, Grêle≈santé,
  Redoux=neutre) à remplacer par température (02) + réponses médiées (03).
  → **À reprendre en 02/04** : pour que le forecast soit honnête (cohérence §3),
  il faudra que l'engine consulte/applique la météo de façon hebdomadaire, pas
  seulement au passage de saison.
- **Code conservé** : `ALEAS_METEO` gardé (supplanté, commenté) ; `ALEAS_RAVAGEURS`
  toujours utilisé via canal `K_PEST`.
- **`random.seed(42)` + imports `random` orphelins retirés** des 4 fichiers
  (`main.py`, `test_golden.py`, `test_auxiliaires.py`, `test_genetique.py`).

### Sous-sprint 02

- **Cadence météo HEBDOMADAIRE actée (décision Nico).** `weather_at(seed, week)`
  est désormais consulté **chaque semaine** dans `tick_semaine` (bloc « 1. Météo
  hebdomadaire »), plus seulement au début de saison. Le **ravageur** reste, lui,
  au début de saison (bloc « 1b », canal `K_PEST` inchangé). Conséquence directe :
  le **forecast (04) sera pleinement read-only et honnête** (ce qui est prévu =
  ce qui arrive, même fonction pure rejouée).
- **`P_EVENT` 0.60 → 0.15** (`sim/weather.py`) : en hebdo, 0.60 effondrait le
  jardin. 0.15 vise ~8 événements notables/an. Calibrage post-test.
- **Température = champ ambiant** (`EcoFields.temperature`, `GridField` avec
  `min_val=-20` pour autoriser le gel). Écrit chaque semaine par l'engine :
  `temp_norm(wiy, year_fraction, phase)` + `temperature_delta(event)`. Spatialement
  uniforme en 02 (deltas gel/canicule/redoux sont `global`) ; le champ est prêt
  pour de la localité (grêle/patch) en 03+.
- **`temp_norm` dans `sim/weather.py`** (couche `sim`, peut lire `fields.noise`) :
  `T_MOY=11`, `T_AMP=7`, + dérive interannuelle `climate_stress × DRIFT_TEMP(=12)`,
  `phase` dérivée du seed (caractère d'année, philo #7). Hiver ~4 °C, été ~18 °C.
- **`GridField` étendu** : param `min_val` (défaut 0.0 → **aucun** changement de
  comportement pour les champs existants, golden des autres champs intact) +
  méthode `fill()`. Surgical.
- **Gel/canicule/redoux migrés vers la TEMPÉRATURE** (`TEMP_DRIVEN` dans
  `weather.py`) : plus d'effet `WEATHER_ALEA` pour eux. Les autres (Sécheresse,
  Tempête, Grêle, Pluie prolongée) **gardent leur mapping `WEATHER_ALEA`** appliqué
  hebdo. → **À reprendre en 03** : Grêle fait encore un `ReduceHealth` direct sur
  les semis (voie `health`) ; c'est exactement la voie à réécrire (milieu × gène
  de rusticité × protection). Le gel ne fait plus QUE gater la croissance — le
  **dégât tissulaire du gel** (médié par gène) est à ajouter en 03.
- **`temp_min_growth` = attribut de classe** (`PlantBase`, défaut 5 °C, extensible
  par espèce comme `longevity_years`). Aucune espèce ne l'override encore — tuning
  post-test.
- **Couplage évaporation↔température** dans `tick_hydrology` : `evap = EVAPORATION
  − EVAP_TEMP_COEF·max(0, temp−EVAP_TEMP_REF)`, borné par `EVAP_MIN=0.975`. Chaud →
  assèche un peu plus (canicule → stress hydrique émergent), jamais brutal.

### Sous-sprint 03

- **Gène `rusticite_froid` ajouté** à `GENE_NAMES` (`plants/genetics.py`). >1 =
  plus rustique → susceptibilité < 1 au gel. **Héritage automatique** : `child_genes`
  boucle sur `GENE_NAMES` avec un canal de hash décorrélé par index (`week*29+i,
  k=4*i`) → ajouter l'index 1 **ne touche pas** les tirages de `hauteur` (index 0).
  Les gènes ne sont **pas** sérialisés dans le golden → l'ajout du gène seul est
  golden-neutre ; c'est la **réécriture du dégât** qui change le golden.
- **Helper `Engine._mediated_damage(tile, eco, severity, reason, gene_name)`** :
  `effectif = sévérité × (1/gène) × (1 − protection_paillage)`, mappé en points de
  santé entiers par division entière (`DAMAGE_STEP=0.55`), déterministe. Vise le
  vrai stade « semis » (même garde-fou pérennes que `appliquer_alea`). Nécromasse
  ∝ hauteur **seulement pour les morts de ce dégât** (pas de double-comptage,
  contrairement au `appliquer_alea` historique — propre car golden re-figé).
- **Gel = piloté par le MILIEU** : `tick_semaine` déclenche le dégât quand
  `temp_now < TEMP_FROST_DAMAGE (0 °C)`, peu importe le nom de l'événement (gelée
  tardive OU dérive froide). C'est la forme la plus pure « flux→contrainte→réponse ».
  Gène = `rusticite_froid`. Constantes : `FROST_SEVERITY_REF=6.0`.
- **Grêle = impact physique localisé** : médiée par la protection (paillage) +
  l'intensité (`HAIL_SEVERITY_REF=1.45`), **sans gène** (le froid n'aide pas contre
  la grêle). Sortie de la boucle `WEATHER_ALEA` (entrée dict conservée, commentée
  « SUPPLANTÉ »). `appliquer_alea` mode `health` toujours utilisé par les
  **ravageurs** (Limaces/Chenilles) — hors périmètre météo, intact.
- **Protection** : seul `paillage` existe comme rondelle protectrice
  (`PAILLAGE_PROTECT=0.25`, cap 1.0 = 4 rondelles). Les **voiles d'hivernage**
  (gel/grêle) et **tuteurs** (verse) de la spec §6.1 sont des structures de
  préparation **gated sur la Vigueur (D11, hors périmètre)** → non implémentés.
- **VERSE (tempête) différée** : `dégât ∝ gène hauteur × absence de tuteur` (§2.3)
  exige un **système de tuteur** qui n'existe pas (gated D11). Le gène `hauteur`
  existe déjà → verse sera « prêt côté gène » dès que le tuteur arrivera. Tempête
  garde pour l'instant son effet `paillage −1` (dispersion) via `WEATHER_ALEA`.
- ⚠ **Observation à creuser (post-test, pas un bug)** : sur 40 ans, **quasi aucune
  plante vivante ne porte un gène non neutre** — le jardin devient dominé par les
  **pionnières de la succession spontanée** (`SeedBank-sol`), qui n'ont pas de
  vecteur génétique. Seules les lignées **cultivées qui se reproduisent** portent
  `rusticite_froid`. La médiation **mord bien** (survie/score baissent), mais la
  *sélection visible du froid* restera discrète tant que les populations vivantes
  sont quasi-neutres. Calibrage/émergence à revisiter (intensités de gel, balance
  pionnières/cultivées), pas en 03.

### Sous-sprint 04

- **Forme du retour `weather_signs` actée (décision Nico)** : **structure
  COMPLÈTE + flag `signed`**. `weather_signs` renvoie TOUS les événements à venir
  (calme exclu), chacun portant `signed: bool`. L'appelant (couche palier/UI,
  **D12, hors périmètre**) filtre : afficher les `signed=True` sous transcendant,
  tout révéler au transcendant — **sans re-toucher `weather.py`** (« marche
  transcendant gratuite », data-driven). L'événement lui-même ne change jamais ;
  seule la *visibilité* du signe dépend de la maîtrise (philo #3 intacte).
- **`is_signed(seed, week)`** indexé sur la **semaine de l'ÉVÉNEMENT** (pas la
  semaine d'observation) → un événement est signé (ou non) de façon **stable**,
  qu'on l'observe à j-1 ou j-2. Canal `K_SIGN=(90_005,0)`, seuil `> 0.20`.
  Mesuré **82.1 %** signés sur 669 événements (cible ~80 %).
- **`SIGN_TABLE` recopiée fidèlement de §4.1.** La spec groupe « Canicule /
  sécheresse » → les deux `kind` **partagent** le tuple `_SIGNES_CHALEUR_SEC` :
  c'est l'**ambiguïté voulue** (un même signe pointe vers ≥ 2 événements). Test
  trouve **4 signes partagés**.
- **Cohérence forecast == réalité prouvée** (pas seulement « par construction ») :
  sur 1040 semaines × horizon 2, le `kind` annoncé == `weather_at(seed, week+k)`
  réel. Acquis grâce à la **cadence hebdomadaire** actée en 02.
- **Read-only strict** : `weather.py` reste pur (aucun `print`, aucun champ
  écrit, n'importe que `fields`). `tests/test_signes.py` créé (style `check`/
  ✅❌/`SystemExit`, lancé `python3 -m tests.test_signes`).
- **Hors périmètre confirmé non fait** : rendu des signes (sprites Godot),
  paliers/bascule interprétative du carnet (D12), révélation transcendant (UI).
</content>
