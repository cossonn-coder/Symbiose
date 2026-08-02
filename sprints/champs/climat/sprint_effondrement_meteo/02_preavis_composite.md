# Tronçon ② — Préavis dramatique du composé + helper `ciel_semaine`

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` + ce fichier suffit.
> Spec : `docs/champs/climat/conception_effondrement_meteo.md` (§3, §5, §7).

## Objectif
Rendre **lisible** l'effondrement AVANT qu'il frappe. Un effondrement est un
**composé** (plusieurs événements haute intensité rapprochés). Le joueur doit
pouvoir l'anticiper par un préavis diégétique intensifié — « l'hiver de tous les
dangers » — et disposer d'une donnée `ciel_semaine` que le tronçon ④ affichera.

## Contexte (déjà en place)
`weather_at(seed, week)` est **pure et déterministe** ; `forecast(seed, week,
horizon)`, `weather_signs(...)`, `is_signed(...)` existent (`sim/weather.py:216-334`)
et annoncent chaque événement à venir **isolément**. Il manque la lecture du
*composé* et l'agrégat pour la vue.

## À FAIRE
### (a) Détection de convergence — donnée dérivée, read-only, zéro RNG
Ajouter (dans `sim/weather.py` ou un module frère de la couche `sim`, au choix du
sous-agent selon la règle de couches `plants ← fields ← sim`) une fonction PURE qui
évalue `forecast` sur un horizon court et calcule un **niveau de convergence** :
grappe d'événements à forte `intensity` dans une fenêtre resserrée → un scalaire /
énum de gravité. **Ce n'est PAS un nouvel événement** : c'est une *lecture* de la
fonction météo existante (comme le forecast lui-même). Déterministe, sans état,
sans RNG (philo #3).

### (b) Signe diégétique intensifié
Le composé émet un signe renforcé (« l'hiver de tous les dangers » : oiseaux
affolés, ciel plombé, un poids dans l'air) — **donnée** (voix naturaliste, français
accentué), pas de logique de rendu, pas de chiffre (philo #5). Réutiliser le patron
`SIGN_TABLE` / `WeatherSign` de `weather.py`. Rattacher au palier maîtrise climat :
la convergence n'est **nommée** qu'au palier expertise/transcendant (l'événement ne
change pas, seule sa lecture — masque §4.3).

### (c) Helper `ciel_semaine` — équivalent Python de l'encart Godot (④)
Une fonction PURE qui agrège, pour la semaine courante : les signes lisibles 1-2
semaines en avant (`weather_signs`) + le niveau de convergence (a) + l'état
atmosphérique de fond (couleur/nuages implicites via l'événement courant et la
nébulosité `weather_state`). Renvoie une structure immuable (`@dataclass frozen`,
comme `WeatherEvent`/`WeatherSign`) **prête à sérialiser** par le pont en ④.
Read-only : ne lit ni n'écrit aucun champ de simulation. C'est l'équivalent Python
exigé par CLAUDE.md (« toute mécanique Godot a son équivalent Python »).

## Golden
**INTACT.** Tout ici est read-only sur la fonction météo pure — aucun champ, aucun
stade, aucune mort n'est touché. Si le golden bouge, c'est un bug : annuler.

## Test ciblé à AJOUTER
Déterminisme + cohérence : sur seed 12345, la convergence détectée à l'approche de
l'an 26 est **strictement supérieure** à une semaine calme ; `ciel_semaine` est
identique sur deux appels (pureté) ; le nom du composé n'apparaît que si le palier
maîtrise est fourni ≥ seuil.

## NE PAS faire
- Ne pas modifier `weather_at` ni le catalogue d'événements (on LIT, on ne tire pas).
- Ne pas introduire de HUD, de chiffre, d'icône calendrier (philo #5) — donnée seule.
- Ne pas toucher au pont ni à la vue (tronçon ④ les consomme).
- Ne pas introduire de RNG vivant.

## Perf
`forecast` sur horizon court = O(H), une fois par semaine. Négligeable.
