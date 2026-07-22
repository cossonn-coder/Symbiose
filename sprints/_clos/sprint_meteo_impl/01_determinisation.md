# Sous-sprint 01 — Déterminisation du tirage météo

> **Kickoff autosuffisant.** Démarre à froid. Lis ce fichier, puis
> [`00_etat.md`](00_etat.md) et la spec [`docs/champs/climat/conception_meteo.md`](../../../docs/champs/climat/conception_meteo.md)
> §0, §1, §3.

## Objectif

Remplacer le tirage météo **non déterministe** par une **fonction pure**, sans
changer (encore) la façon dont les événements agissent. C'est le pivot qui rend
le reste possible. Unité testable, autonome.

**Succès =** déterminisme prouvé (deux runs identiques **sans** `random.seed`) +
golden re-figé une fois + hash consigné dans `00_etat.md`.

## Avant de commencer

1. `git status` propre.
2. Lire dans `sim/engine.py` : `Alea`, `ALEAS_METEO`, `appliquer_alea`, et le
   bloc « 1. Aléas début de saison » de `tick_semaine` (le `random.choice`).
3. Lire `fields/noise.py` : `_hash_noise`, `hash_gauss`, `climate_stress`.
4. Repérer les `random.seed(42)` : `main.py`, `tests/test_golden.py`,
   `tests/test_auxiliaires.py`, `tests/test_genetique.py`.

## Travail

1. Créer une fonction pure **`weather_at(seed, week) -> WeatherEvent`** (proposer
   l'emplacement : `sim/weather.py` neuf, ou dans `sim/engine.py`). Implémente le
   modèle §1.3 : canaux-sentinelles `K_OCC/K_PICK/K_MAG`, catalogue + saisonnalité
   (table §1.3), intensité via `hash_gauss`. `@dataclass WeatherEvent(kind,
   intensity, duration_weeks, scope)`.
2. Brancher `tick_semaine` sur `weather_at(seed, week)` à la place de
   `random.choice(ALEAS_METEO)`. **Garder le couplage actuel inchangé** pour ce
   sous-sprint : on mappe le `WeatherEvent` vers les `Alea` existants (modes
   `field`/`rondelle`/`health`). On ne touche PAS encore à la température ni aux
   réponses médiées (sous-sprints 02/03).
3. Décider le sort des **ravageurs** (`ALEAS_RAVAGEURS`, eux aussi en
   `random.choice`) : les déterminiser de la même façon (canal séparé) — c'est
   cohérent et évite de laisser un RNG live résiduel.
4. **Retirer les `random.seed(42)`** devenus inutiles. Si un test en dépend
   encore pour autre chose, le noter dans `00_etat.md`.

## Vérification (critères de succès)

- **Déterminisme** : lancer `main.py` deux fois **sans** `random.seed` → logs
  identiques. (Prouve qu'aucun RNG live ne subsiste sur le chemin météo.)
- **Golden** : `python3 -m tests.test_golden` échoue (comportement changé,
  attendu) → **régénérer le golden une fois**, vérifier que le diff est cohérent
  avec le changement (mêmes types d'événements, juste une séquence déterministe
  différente), re-figer. Consigner **hash avant → après** + raison dans
  `00_etat.md`.
- `python3 main.py` → exit 0. `python3 -m tests.test_genetique`,
  `tests.test_auxiliaires` → toujours verts (ajuster leur `random.seed` retiré
  si besoin).

## Garde-fous

- Français + pédagogie (Nico vient du C/Python embarqué).
- **Surgical** : ne change que le chemin de tirage météo/ravageur. Pas de
  refactor opportuniste.
- Imports absolus, lancement depuis `data/code/`. Respecter la règle de couches
  (`plants ← fields ← sim ← engine ← main`).
- En fin : mettre à jour `00_etat.md` (hash, décisions), commit, `/clear`.
</content>
