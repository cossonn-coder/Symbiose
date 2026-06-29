# Sprint MÉTÉO → CHAMPS (dont rosée) — état partagé

> **Conception FIGÉE** → source de vérité = `docs/conception/CONCEPTION_METEO_CHAMPS.md`
> (la lire d'abord, §0→§7). Ce fichier = état léger + carte des sous-sprints, mis à
> jour en fin de **chaque** tronçon. Boucle projet : `0N` → coder → vérifier/re-figer
> golden (ANNONCÉ) → MAJ ce fichier → commit → `/clear` → `0N+1`.

## En une phrase
On remplace le couplage météo→champs **provisoire** (deltas plats `WEATHER_ALEA`) par
des **flux médiés** (philo #2) et on **complète les flux manquants** — rosée/gelée
blanche, lessivage NPK par la pluie, microbiome climatique — pour que chaque événement
agisse sur **tous** les champs qu'il influence réellement.

## Invariant GOLDEN (vaut pour TOUS les tronçons)
- Golden = **smoke test** (`tests/test_golden.py`, 2 tuiles × 4 ans) + `tests/population_hash.txt`.
- Ce sprint **modifie la physique du tick** → le golden **VA BOUGER** dès ①. Chaque
  re-figeage est **maîtrisé et ANNONCÉ** : vérifier que la dérive est *localisée et
  expliquée* (humidité/microbiome dans le sens attendu), JAMAIS aveugle.
- Re-figer (depuis `data/code/`) : `python3 -m tests.test_golden --capture` (+ population
  si elle bouge). **Consigner le nouveau hash ici** à chaque cran, avec la justification.
- Déterminisme philo #3 : **aucun RNG neuf** (la météo est déjà tirée par `_hash_noise`).

## Décisions structurantes (détail dans le doc)
- **Refonte propre** : on RETIRE les entrées humidité de `WEATHER_ALEA` (Canicule,
  Sécheresse, Pluie prolongée, Orage), on ne les empile pas (décision Nico).
- **Assèchement émergent** : Canicule/Sécheresse sèchent par l'évaporation∝T_sol DÉJÀ
  en place (le delta plat `−0.4` faisait double-emploi). Apport pluie ∝ intensité via
  `PLUIE_APPORT` (table PURE côté `fields`, miroir de `PRECIP_NORM`).
- **Rosée = face douce du gel** : un seul thermomètre nocturne `t_min_nuit_at`. >0 °C →
  rosée liquide (humidité+) ; ≤0 °C → gelée blanche (fonte différée + dégât foliaire léger).
- **Lessivage NPK existe DÉJÀ** (`tick_decomposition` ~L650, CEC) → ③ l'AMPLIFIE par
  l'eau drainée (perte déjà retournée par `tick_hydrology`, `container.py:392`), ne le recrée pas.
- **Microbiome** : ajouter une cloche T + facteur humidité (terme multiplicatif, pas de champ neuf).
- **Couches** : calcul pur dans `fields/ecofields/`, câblage d'ordre dans `sim/engine/boucle.py`.

## Carte des sous-sprints (5, ordre = dépendances)
| # | Sujet | Kickoff | État |
|---|-------|---------|------|
| ① | Humidité médiée (retrait deltas plats + `PLUIE_APPORT`) | `01_humidite_mediee.md` | ✅ FAIT (golden+pop re-figés) |
| ② | Rosée & gelée blanche (`tick_rosee`, point de rosée, continuum) | `02_rosee_gelee_blanche.md` | ⬜ À FAIRE |
| ③ | Lessivage NPK par la pluie | `03_lessivage_npk.md` | ⬜ À FAIRE |
| ④ | Microbiome climatique | `04_microbiome_climatique.md` | ⬜ À FAIRE |
| ⑤ | Interconnexions vivantes + voix + pont snapshot | `05_interconnexions_voix.md` | ⬜ À FAIRE |

Dépendances : ① fonde l'hydrique propre ; ② dépend de ① (point de rosée lit l'humidité
médiée) ; ③④ dépendent de ① mais sont indépendants entre eux ; ⑤ dépend de ② (rosée à
exposer/relier). Déroulés en série pour un golden vérifié à chaque cran.

## Constantes neuves (placeholders D-calibrage, en tête de `constants.py`)
`PLUIE_APPORT` · `ÉCART_ROSÉE_SEC` · `GAIN_HUM_ROSÉE` · `ROSÉE_PAR_DEGRÉ` ·
`GIVRE_SEVERITY_REF` · `LESSIVAGE_PLUIE_K` · `MICROBE_T_OPT` · `MICROBE_T_TOL`.
Valeurs définitives = F5 / bancs d'essai.

## Conventions
- Source de vérité = Python `data/code/`. Lancement depuis `data/code/`
  (`python3 main.py`, `python3 -m tests.test_golden`, `python3 -m tests.test_population`).
- Tables météo (`PLUIE_APPORT`) PURES côté `fields` (pas d'import inverse vers `sim`,
  miroir de `NEBULOSITE`/`PRECIP_NORM`). Calcul rosée/microbiome = helper pur isolé
  (comme `thermique.py`), conteneur expose une fine méthode déléguée.
- Tout garder (scripts de mesure inclus). Un fichier à la fois sauf synchro cohérente
  avant commit. Français + commentaires pédagogiques au cœur des fichiers.

## Hors périmètre (dette)
- **pH par la pluie** (acidification) → dette mineure (dérive pH déjà modélisée).
- Rendu Godot des gouttes/givre = exposition au snapshot faite en ⑤, **rendu C#** = dette D24.
- Calibrage numérique des constantes = F5 / bancs d'essai.

## Avancement / REPRISE

### ① Humidité médiée — FAIT (2026-06-29)
**Fichiers touchés** : `fields/ecofields/constants.py` (table `PLUIE_APPORT`),
`fields/ecofields/container.py` (`tick_hydrology(pluie_event=0.0)` + infiltration
∝ structure, bornée ≥ 0), `sim/engine/aleas.py` (`WEATHER_ALEA` : entrées humidité
Canicule/Sécheresse/Pluie prolongée/Orage neutralisées en `mode="none"`, originaux
conservés en commentaire ; vent/gel/grêle intacts), `sim/engine/boucle.py`
(`pluie_event = PLUIE_APPORT.get(event.kind, 0.0)` passé à `tick_hydrology`),
`fields/__init__.py` (ré-export `PLUIE_APPORT`).

**Golden RE-FIGÉ (annoncé)** :
- `tests/golden_hash.txt` : `db5e7c66…` → **`b2a8993288318b98936e3625dc0e68b119f39fef351ebfa49e2942a7c0d46d65`**
- `tests/population_hash.txt` : `9ba39ab7…` → **`cd15346047b53fdcecbb7acb55b10b41fe0977a302fda25e31c4edcf0674edd1`**

**Dérive — LOCALISÉE et EXPLIQUÉE (humidité, sens attendu)** : l'humidité finale du
smoke CHUTE fortement (T0 0.87→0.105, T1 0.82→0.013). Les anciens deltas plats
étaient nets POSITIFS (Pluie +0.5, Orage +0.5 ≫ Canicule/Sécheresse −0.4) et
gonflaient artificiellement l'humidité ; le nouveau flux (BASE_RAIN + PLUIE_APPORT
infiltré ∝ structure terre 0.7, puis évaporation∝T_sol + drainage 0.993) produit un
sol réaliste, beaucoup plus sec — exactement le « plus sec et spatial » voulu §2.1.
Dérive secondaire cohérente : microbiome ↑ (T0 0.076→0.323, sol plus sec change la
dynamique famine), NPK légèrement décalés (uptake/lessivage lisent l'humidité),
champs population (vers/détritivores) re-figés (lisent l'humidité). AUCUN re-figeage
aveugle. Suites hydro vertes : test_eau, test_conteneur, test_substrat,
test_confinement, test_couplage (rétrocompat `pluie_event=0` ⇒ conteneurs bit-identiques).

**⚠ FINDING à arbitrer par Nico (hors périmètre ①, NON corrigé)** :
`tests/test_biennial.py` PASSAIT avant, FAIL maintenant. Ce n'est PAS un bug de ①
mais un **off-by-one** exposé par l'humidité réaliste. Le gate `_bolt_bloque`
(`croissance.py:74`) libère la montaison dès `age_years >= 1.0`, ce qui est VRAI
exactement au tick 52 (52/52=1.0) → la carotte monte à fleur à w52. Or le test
compte w52 comme « an 1 » (`w <= 52`) → assertion `y1_max_stage < bolt` échoue.
Avant ①, le test ne passait QUE PAR CHANCE : la tuile-test inondée par les deltas
plats atteignait `hum=2.617 > HUM_NOYE(2.6)` pile à w52 → stagnation « noyé » →
montaison retardée à w53. Question de design à trancher (w52 = fin an 1 ou début
an 2 ?) → corriger soit la borne du gate, soit la fenêtre du test. Laissé ROUGE
volontairement (retour sur livrable = arbitrage Nico, pas de patch silencieux).

**Build C#** : non concerné (aucun fichier C# touché).
