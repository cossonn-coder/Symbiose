# ① Bilan hydrique — rosée, épisodes de pluie, transpiration foliaire

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, `docs/champs/sol/conception_sol_qui_respire.md` §0-§1.
**Golden** : RE-FIGÉ annoncé (la météo et l'hydrologie changent partout). Dérive attendue :
humidité plus haute, plus de semaines pluvieuses/couvertes, uptake d'eau ≈ 0 en hiver.
Re-figer UNE fois en fin de tronçon (`python3 -m tests.test_golden --capture`), consigner
l'ancien et le nouveau hash dans `00_etat.md`.

## Objectif

Que le sol du monde `full` respire : recharge d'hiver, creux d'été sans désert. Trois
corrections + un calibrage + un banc.

### 1a. Humidité de l'air → rosée
- Fonction PURE déterministe `(seed, semaine) → humidité de l'air ∈ [0,1]` côté `sim`
  (près de `sim/weather.py` : océanique, saisonnière ; haute sous la pluie, basse sous
  sécheresse/canicule).
- `fields/ecofields/rosee.py::tick_rosee` la reçoit EN ARGUMENT (les `fields` n'importent
  jamais `sim`) et l'utilise à la place de `humidite/3` dans le point de rosée
  (`GAIN_HUM_ROSEE`). Appelant : `sim/engine/boucle.py` (~l.274, `eco.tick_rosee(temp_now,
  nebul)`, via `fields/ecofields/ticks.py`). Défaut d'argument = comportement actuel pour
  les appelants qui ne le passent pas (conteneurs, tests).

### 1b. Épisodes de pluie toutes saisons
- Aujourd'hui (`sim/weather.py`) : `P_EVENT = 0.15`, puis tirage parmi les candidats en
  fenêtre (`_CATALOGUE`) ; « Pluie prolongée » seulement sem. 27-52 ; « Orage » local été.
- Cible : épisodes de pluie hiver ~1 sem/3, printemps & automne ~1/4, été ~1/6 (orages).
  Calendrier moteur : printemps 1-13, été 14-26, automne 27-39, hiver 40-52. Conception
  libre (canal de hash dédié, fréquence par saison, ou catalogue repensé) MAIS : la pluie
  reste un `WeatherEvent` (le préavis `sim/ciel.py` et la nébulosité
  `NEBULOSITE`/`nebulosite_dynamique` le lisent) ; une Sécheresse/Canicule exclut la pluie ;
  **jamais de pluie chaque semaine** en jeu (D-pluie).
- `PLUIE_APPORT` (`fields/ecofields/constants.py`) recalibré : un épisode recharge vraiment.
- Vérifier les tests qui figent des séquences météo : `tests/test_signes.py`,
  `tests/test_vent.py`, et les bancs (`BANC_SEED`, ex. effondrement seed 12345 — banc à
  re-vérifier, l'adapter si son scénario dépendait d'un tirage précis : le signaler).

### 1c. Transpiration foliaire saisonnière
- Constante PAR ESPÈCE (attribut de classe, patron `resilience_base`, PAS un gène) :
  type de feuillage ∈ {`large`, `moyen`, `fin`, `cireux`, `aiguilles`} → coefficient (table
  dans les constantes). Défaut `moyen`. Renseigner tout le catalogue (`plants/species/*`,
  `plants/perennials.py`) : courge/figuier/tournesol `large`, thym/sauge/romarin `cireux`,
  sapin `aiguilles`, graminées/carotte `fin`… (jugement botanique, lister dans le rapport).
- Le prélèvement d'EAU seul (pas les nutriments `BESOIN`) est multiplié par :
  demande climatique (chaleur, ciel clair, vent — mêmes pilotes que l'évaporation) ×
  feuillage présent (≈ 0 si dormant / caduc défeuillé en hiver / hors végétation ; un
  persistant transpire peu en hiver car la demande est faible) × coefficient de feuillage.
  Point d'entrée : `fields/ecofields/uptake.py::plant_uptake` (branche `humidite`) appelé
  par `sim/engine/croissance.py::_apply_uptake` (~l.198). La saison et la météo sont
  connues côté `sim` → les passer en argument (défaut neutre = comportement actuel).

### 1d. Calibrage (cible VALIDÉE par Nico)
- Outil : `mesures/bilan_eau.py <seed> <semaines>` (depuis `data/code/`, `PYTHONPATH=.`).
  L'étendre si besoin (humidité fin d'hiver sem. ~10, fin d'été sem. ~35, population, temps).
- 3 graines (1521550718, 7, 1515525502), monde `full`, 156 semaines :
  humidité médiane annuelle ∈ [1,0 ; 2,0] ; fin d'hiver proche du plafond ; creux fin d'été
  visible sans tomber sous ~0,5. Chiffres avec leur limite entre crochets ([n=…]).
- **Perf** : temps de tick (`tools/profile_monde.py` ou chrono du script) et population
  avant/après. Budget ≤ +10 % de tick. Dépassement ⇒ STOP et remontée dans `00_etat.md`
  (ne pas brider la population pour passer).

### 1e. Banc « pluie chaque semaine » (TEST seulement)
- Un banc serveur (patron `bancs` / `BANC_*` importé par `tools/simserver/commands.py`)
  qui force la pluie chaque semaine. Script de vérification dans `mesures/` qui prouve,
  sans réglage ad hoc : sol au plafond 3,0 puis `eau_surface` > 0, `marais_memory` qui
  monte dans les creux, asphyxie sur argile, recul de la part de plantes en
  `acclimatation`. Les carpophores seront vérifiés au ③. Un maillon muet ⇒ le consigner.

## Ne PAS faire
- Ne pas traiter D107 (canicule à rendre probable chaque été) mais ne pas la rendre plus
  difficile : la canicule reste un aléa d'été qui exclut la pluie.
- Pas de pluie hebdomadaire en jeu ; pas de bonus direct sur les plantes ; pas de RNG.
- Ne pas toucher au mycélium, aux carpophores, au nectar (tronçons suivants).
- Ne jamais lancer `test_epaisseur_500ans`.

## Fin de tronçon
Suites `tests/` vertes (hors 500 ans), golden re-figé + hashes consignés, bump du pont si
le snapshot change (`tools/simserver/version.py`), `00_etat.md` à jour (mesures [n=…]).
