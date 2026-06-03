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
</content>
