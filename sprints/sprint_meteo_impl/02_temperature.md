# Sous-sprint 02 — Température ambiante + météo hebdomadaire

> **Kickoff autosuffisant.** Démarre à froid. Lis ce fichier, puis
> [`00_etat.md`](00_etat.md) et la spec [`CONCEPTION_METEO.md`](../../data/code/CONCEPTION_METEO.md)
> §1.1, §1.2, §2.1, §2.2. Le sous-sprint 01 (déterminisation) est **fait** :
> `sim/weather.py` fournit déjà `weather_at(seed, week)` pure + `WeatherEvent`
> + `forecast()`.

## Objectif

Donner au moteur une **température ambiante** qui pilote la croissance et
l'évaporation, et faire de la météo le **moteur hebdomadaire** de cette
température. Aujourd'hui la croissance ne se gate que sur humidité + lumière ;
la météo n'agit qu'au passage de saison. Après 02 : un champ `temperature`
existe, suit les normales saisonnières, est bousculé chaque semaine par la météo,
et conditionne la croissance.

**Succès =** champ `temperature` opérationnel (normales + deltas météo
hebdomadaires) + gate `ok_temp` dans la croissance + évaporation couplée à la
température + **le jardin survit toujours 30 ans** (référence comportementale,
`main.py`) + golden re-figé une fois, hash consigné dans `00_etat.md`.

## Décision de conception à acter au démarrage (poser la question à Nico)

**Cadence hebdomadaire de la météo (recommandée).** En 01, la météo n'est
consultée qu'au **début de saison** (couplage laissé inchangé). Pour que la
température soit dynamique ET que le **forecast soit honnête** (cohérence §3 : ce
qui est prévu = ce qui arrive, le sous-sprint 04 doit rester *read-only*), il faut
que l'engine **consulte et applique `weather_at(seed, week)` CHAQUE semaine**.
C'est le bon endroit pour ce basculement (la température veut être écrite chaque
semaine de toute façon). → **Recommandation : passer la météo en hebdomadaire
dans ce sous-sprint.** Si Nico préfère différer, garder la cadence début-de-saison
et ne faire que les normales + gate (mais alors 04 ne sera pas pleinement
read-only). Acter avant de coder.

> **Garde calibrage (crucial)** : en hebdomadaire, ~60 % des semaines portaient un
> événement avec `P_EVENT=0.60` (valeur 01) → BEAUCOUP trop agressif appliqué
> chaque semaine (le jardin s'effondrerait). **Baisser `P_EVENT`** (viser une
> fréquence d'événements *notables* comparable à avant, p.ex. ~0.10–0.20/semaine)
> et/ou **moduler les effets par l'intensité** pour que `main.py` survive 30 ans.
> Le jardin qui survit est le juge.

## Avant de commencer

1. `git status` propre (le commit de 01 doit être en place).
2. Lire `sim/weather.py` : `weather_at`, `WeatherEvent`, les canaux, `P_EVENT`.
3. Lire `sim/engine.py` : le bloc « 1. Aléas début de saison » (consommateur
   actuel de `weather_at` + `WEATHER_ALEA`), `_avancer_stades` (le gate
   `ok_hum`/`ok_light`), et `tick_hydrology` appelé dans `tick_semaine`.
4. Lire `fields/ecofields.py` : comment `lumiere`/`disturbance` (champs ambiants)
   sont déclarés et tickés, et `tick_hydrology` (évaporation → pluie → drainage).
5. Lire `fields/noise.py` : `climate_stress(year_fraction, phase)` (dérive
   interannuelle, §1.2, à réutiliser tel quel).
6. Repérer où vit le seuil de croissance des espèces (`plants/base.py` /
   `plants/species.py`) pour y ajouter un seuil de température.

## Travail

1. **Normale saisonnière** `temp_norm(week_in_year)` (§1.1) :
   `temp_norm(w) = T_MOY − T_AMP · cos(2π·(w − 4)/52)`, `T_MOY≈11`, `T_AMP≈7`
   (Normandie océanique). Emplacement : proposer `sim/weather.py` (cohésion
   météo/climat) ou `fields/noise.py` (fondation pure). Optionnel : moduler par
   `climate_stress` (§1.2) pour la dérive interannuelle.
2. **Champ `temperature`** dans `EcoFields`, ambiant comme `lumiere`. Chaque
   semaine : baseline = `temp_norm(wiy)` (+ dérive éventuelle), puis **deltas
   météo transitoires** (gel −, canicule +, redoux +) issus du `WeatherEvent` de
   la semaine. Modulés par `WeatherEvent.intensity`.
3. **Météo hebdomadaire** (si décision actée) : dans `tick_semaine`, consulter
   `weather_at(seed, week)` **chaque semaine** et écrire ses deltas température +
   ses effets milieu existants. Les événements gel/canicule/redoux migrent de
   leur mapping provisoire `WEATHER_ALEA` (humidité, 01) vers de **vrais deltas
   de température** — début de remplacement des mappings approximatifs. Garder le
   reste (tempête→paillage, pluie→humidité…) tel quel pour l'instant.
4. **Gate `ok_temp`** dans `_avancer_stades` : ajouter un seuil de croissance par
   espèce (`temp_min_growth`, défaut ~5 °C, extensible par design comme les
   gènes), `ok_temp = temp >= seuil` → `can_grow = ok_hum and ok_light and
   ok_temp`. Logger la stagnation par le froid comme on logge l'ombre/la sécheresse.
5. **Couplage évaporation↔température** dans `tick_hydrology` : chaud → évapore
   plus (facteur croissant avec la température au-dessus d'une référence). Borné
   pour ne pas assécher brutalement.

## Vérification (critères de succès)

- **Déterminisme** : `main.py` deux fois → logs identiques (aucun RNG live
  réintroduit).
- **Survie** : `python3 main.py` exit 0, jardin vivant à 30 ans sur les 9 tuiles
  (comparer l'ordre de grandeur des « vivantes » au run de 01 ; un effondrement
  signale un calibrage `P_EVENT`/intensité trop dur — ajuster).
- **Golden** : `python3 -m tests.test_golden` échoue (gate de croissance changé,
  attendu) → **régénérer une fois** (`--capture`), vérifier la cohérence du diff
  (croissance gatée par le froid en hiver, pas de catastrophe), re-figer.
  Consigner **hash avant → après** + raison dans `00_etat.md`.
- `python3 -m tests.test_genetique`, `tests.test_auxiliaires` → toujours verts /
  contraste préservé.

## Garde-fous

- Français + pédagogie (Nico vient du C/Python embarqué).
- **Multi-fichiers cohérent assumé** (la règle « un fichier à la fois » est
  suspendue pour une synchro logique : `ecofields.py` + `engine.py` + `weather.py`
  + espèces). Rester néanmoins surgical : pas de refactor opportuniste hors
  température/météo.
- Imports absolus, lancement depuis `data/code/`. Respecter la règle de couches
  (`plants ← fields ← sim ← engine ← main`) : `temp_norm` dans `weather` (sim) ou
  `noise` (fields), jamais l'inverse.
- **Calibrage = ressenti, pas dogme** : viser un jardin qui survit et des hivers
  qui ralentissent visiblement la croissance. Les chiffres exacts sont
  post-test.
- Si le sous-sprint déborde (trop de fichiers couplés d'un coup), le **scinder en
  02a** (normales + champ + gate + évaporation, météo encore début-de-saison) et
  **02b** (bascule hebdomadaire + deltas température), chacun re-figeant le golden
  une fois. Préférer cette coupe à un fourre-tout instable.
- En fin : mettre à jour `00_etat.md` (hash, décisions), commit, `/clear`.
