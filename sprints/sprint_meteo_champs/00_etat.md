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
| ① | Humidité médiée (retrait deltas plats + `PLUIE_APPORT`) | `01_humidite_mediee.md` | ⬜ À FAIRE |
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
(rien encore — démarrer par `01_humidite_mediee.md`)
