# 2026-06-20 — Fix dette D39 : régression `test_senescence` (asphyxie chronique)

## Contexte
`tests/test_senescence.py` était ROUGE depuis le sprint thermique (commit
`4b70032`, tronçon ⑦ : ajout des événements de précipitation Neige/Orage). Le
pommier isolé mourait **par asphyxie** (cause « autre ») au lieu de mourir de
**sénescence** dans la fenêtre attendue [49 ; 112] ans.

À la reprise (après le sprint physico-chimie ⑧ `structure_sol`), la mort
intervenait à **34,3 ans** (et non plus 2,7 : `structure_sol` avait déplacé le
point via `excess×(2−structure)`), mais c'était **toujours une asphyxie**, pas la
sénescence.

## Diagnostic
La météo est **GLOBALE** : `weather_state(seed, week)` est appelée dans
`sim/engine/boucle.py:88`. Ses événements de précipitation (« Pluies »,
« Pluie prolongée », « Orage », chacun **+0,5 humidité** via `WEATHER_ALEA`,
`sim/engine/aleas.py`) sont appliqués au sol de la tuile (`boucle.py:134-136`).
Ils gorgent durablement le sol → `asphyxie_memory` franchit
`ASPHYXIE_HEALTH_SEUIL` (`sim/engine/mortalite.py`) et tue l'arbre avant la
sénescence age-based.

Le test choisissait déjà une humidité de confort (1,5) pour éviter les deux
stress hydriques, et neutralisait déjà la germination spontanée — mais il
n'isolait **pas** la météo humide introduite deux sprints plus tard.

## Décision — piste (a) : ré-isoler le test
Conformément à la reco de la dette et à l'intention du test (vérifier la VOIE de
mort par sénescence sur un arbre vieilli seul) : donner au test un **climat de
laboratoire** sans précipitation ni gel. La piste (b) — revoir le drainage du
modèle eau — a été écartée : plus large, croise D37 (vent/évaporation), et
risquerait de re-figer le golden, hors périmètre d'un fix de test.

## Implémentation — `tests/test_senescence.py` UNIQUEMENT
Monkeypatch chirurgical : `_boucle.weather_state = _meteo_labo`, où
`_meteo_labo(seed, week)` renvoie `(CALME, 15.0, 0.1)` —
`CALME = WeatherEvent("Beau temps", …)` déjà exporté par `sim.weather`,
température douce 15 °C > `TEMP_FROST_DAMAGE=0` (→ pas de gel), nébulosité 0.1
(ciel clair neutre). Posé à côté de la neutralisation de germination (même esprit
d'isolation), documenté dans l'en-tête de module et le docstring.

**Aucun fichier moteur touché.**

## Vérifications
- `python3 -m tests.test_senescence` → `PASS — pommier mort de sénescence à
  59.8 ans (longévité 70, onset 49)`, ∈ [49 ; 112]. ✅
- `python3 -m tests.test_golden` → golden INTACT `e209e8d8…` (le fix ne touche
  que le double de test, event-driven hors moteur). ✅

## Suites
- DETTE.md : **D39 → 🟢 ✅**.
- Incohérence repérée mais **non incluse sans accord de Nico** : D30
  (structure/compaction sol) est encore marquée ouverte alors que le tronçon ⑧
  physico-chimie l'a implémentée (`structure_sol`, commit `1e591e3`). À confirmer.
