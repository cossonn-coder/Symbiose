# Tronçon ⑧ — Snapshot météo + carte température (pont Python→Godot)

> Sprint thermique-microclimat. Conception : `docs/conception/CONCEPTION_THERMIQUE_MICROCLIMAT.md`.
> Kickoff **autosuffisant** (relançable à froid).
> Pré-requis : ⑦ CLOS (catalogue Neige + Orage + manteau neigeux `eco.snow` ;
> golden re-figé LARGE `5fddfe5430dd896de497d5ac9424951f0f29f3f38ad7b50cdb588310a5ffe9f6`,
> `population_hash.txt` re-figé `5e6e688f…`).

## Objectif

Tout le travail thermique (①→⑦) vit côté MOTEUR et n'est PAS encore visible : le
snapshot JSON envoyé à Godot (`tools/simserver/serialize.py::_snapshot`) n'expose
NI l'événement météo courant, NI la température spatialisée, NI le manteau neigeux.
Ce tronçon les EXPOSE en **lecture seule** pour que la vue (⑨ rendu événements, ⑩
heatmap température) ait ses données. **Aucune écriture moteur** → la dérive golden
est **NEUTRE** (pure sérialisation + `weather_at` qui est une fonction PURE).

C'est un tronçon « pont », pas « moteur » : même esprit que les bumps 0.3.6→0.4.1
(squelettes, litière, foragers, structures, alarme) qui n'ont fait qu'AJOUTER des
blocs lecture-seule au snapshot sans toucher le hash.

## Modèle

### A. Bloc `weather` au snapshot (scalaire global du tick)

`_snapshot` connaît `gs["week"]` = **prochaine** semaine à simuler. La météo qui a
produit l'état courant est donc celle de la semaine **déjà simulée** = `week − 1`.
`weather_at` étant PURE, on la **recalcule** (pas besoin de la stocker dans
`game_state`) :

```python
from sim.weather import (weather_at, temp_norm, temperature_delta,
                         weather_signs)
from fields.ecofields.constants import NEBULOSITE
import math
...
seed = gs["seed"]
last = week - 1                       # semaine qui a produit l'état courant
if last >= 1:
    ev   = weather_at(seed, last)
    wiy_last = ((last - 1) % 52) + 1
    yf   = (last - 1) / 52.0
    ph   = (seed & 0xFFFF) / 0xFFFF * 2.0 * math.pi
    tair = temp_norm(wiy_last, yf, ph) + temperature_delta(ev)
    nebul = NEBULOSITE.get(ev.kind, 0.10)
else:                                  # init, rien simulé encore → calme
    ev, tair, nebul = WeatherEvent("Beau temps"), T_MOY, 0.10
```

⚠️ **DRY/cohérence** : ces 4 lignes (`tair`/`nebul`) DUPLIQUENT le calcul de
`boucle.py` étape 1 (lignes ~87-92). Le plus surgical pour ⑧ = recalculer ici
(serialize lit, n'a pas accès au `temp_now`/`nebul` locaux du tick). **Si la
duplication gêne**, sortir un petit helper PUR `sim/weather.py::weather_state(seed,
week) -> (event, t_air, nebul)` et l'appeler des DEUX côtés (boucle.py + serialize) —
**à proposer à Nico** (refactor léger, golden NEUTRE car valeurs identiques). Choix
par défaut : helper partagé (évite que les deux calculs divergent un jour).

Bloc exposé (le manteau `snow` est PAR TUILE → il va plutôt dans le bloc
température §B ; ici le scalaire global) :

```python
"weather": {
    "kind": ev.kind,
    "intensity": round(ev.intensity, 3),
    "scope": ev.scope,                 # "global" | "local" (Orage/Grêle)
    "nebulosite": round(nebul, 3),
    "t_air": round(tair, 2),
    "signs": [                          # préavis diégétique (philo #5), PUR
        {"kind": s.kind, "in_weeks": s.in_weeks,
         "signs": list(s.signs), "signed": s.signed}
        for s in weather_signs(seed, last, horizon=2)
    ] if last >= 1 else [],
}
```

- `signs` = `weather_signs(seed, last, horizon=2)` : les signes des événements à
  venir (1-2 sem). **Read-only**, déjà PUR (« cadeau de la fonction pure »). Le
  filtrage par palier de maîtrise (D12, n'afficher que `signed=True` hors
  transcendant) reste à la charge de la VUE — on expose tout, flag compris.
- Ne PAS recopier la logique de signe ici : `weather_signs` existe déjà.

### B. Carte température + manteau par tuile

`eco.temperature_sol` (GridField) et `eco.snow` (scalaire ⑦) sont des ÉTATS
persistants du conteneur → lecture DIRECTE (pas de recalcul). Exposer dans la
boucle `for tile in gs["tiles"]` existante (à côté de `sprites`/`litiere`/…) :

```python
temperature = {}
...
# dans la boucle par tuile :
temperature[tile.tile_id] = {
    "snow": round(eco.snow, 3),
    "t_sol": [[round(eco.temperature_sol.data[r][c], 2)
               for c in range(eco.cols)] for r in range(eco.rows)],
}
```

- Format : `t_sol` = grille 2D (rows × cols) arrondie 2 déc. Petites tuiles (le
  smoke = 2×N) → volume négligeable ; le monde full (40×40 par tuile) reste
  raisonnable (1 float/plot). **Si le volume inquiète** (mesurer comme au t6·B,
  cf. 0.2.3), basculer en liste plate row-major ou n'exposer que les extrêmes —
  noter, ne pas pré-optimiser.
- `snow` PAR TUILE (manteau uniforme) — la vue dessine un voile blanc ∝ snow.
- T_air est uniforme (déjà dans `weather.t_air`) → ne PAS le dupliquer par plot.

### C. Version protocole

Bump `tools/simserver/version.py::ENGINE_VERSION` → **`0.5.0`** (1er bloc du sprint
thermique au pont ; mineure car schéma étendu, pas cassé). Ajouter l'entrée de
changelog au-dessus (style des bumps précédents) : blocs `weather` (kind/intensity/
scope/nebulosite/t_air/signs) + `temperature` (snow + t_sol par tuile), PUR ajout
lecture-seule → golden NEUTRE, champs optionnels côté vue (tolérance pré-0.5.0).

## Étapes

1. **`tools/simserver/serialize.py`** — bloc `weather` (§A) + bloc `temperature`
   (§B) dans `_snapshot` ; imports en tête. Décider helper partagé vs duplication
   (§A) — proposer à Nico, défaut helper.
2. **(si helper)** `sim/weather.py` — `weather_state(seed, week) -> (WeatherEvent,
   float, float)` PUR ; rebrancher `boucle.py` étape 1 dessus (golden NEUTRE :
   mêmes valeurs). Sinon sauter.
3. **`tools/simserver/version.py`** — `ENGINE_VERSION = "0.5.0"` + changelog.
4. **Golden** — `python3 -m tests.test_golden`. **DOIT rester PASS sans re-figer**
   (`5fddfe54…`) : serialize ne touche pas le moteur, `weather_at`/`weather_state`
   sont pures. Si ça dérive → BUG (le helper a changé une valeur) : tracer, ne pas
   re-figer aveuglément.
5. **Smoke pont** : un petit script qui instancie `SimServer`, fait `init` +
   quelques `step`, lit le snapshot et vérifie : (a) `weather.kind` ∈ catalogue ;
   (b) `weather.t_air` cohérent (≈ normale ± delta) ; (c) `temperature[tile].snow`
   == `eco.snow` ; (d) `t_sol` dimensions rows×cols. Réutiliser le serveur comme
   les tests d'intégration existants (chercher un test pont s'il existe).
6. **Suites ciblées** : croissance / eau / génétique / population restent PASS
   (aucune raison de bouger — pur snapshot).

## Invariant golden

- **NEUTRE** : zéro écriture moteur. Le snapshot LIT `eco.temperature_sol`/`eco.snow`
  (déjà calculés) et RECALCULE la météo par fonction pure. `weather_at`,
  `temp_norm`, `temperature_delta`, `weather_signs` sont toutes pures.
- Si le golden bouge → régression à tracer (probable cause : helper §A qui modifie
  une valeur, ou import à effet de bord). Ne PAS re-figer sans comprendre.

## Validation

- `python3 -m tests.test_golden` PASS **sans re-figer** (hash `5fddfe54…`).
- `python3 main.py 3` exit 0.
- Smoke pont (§5) : blocs `weather` + `temperature` présents et cohérents.

## À faire en fin de tronçon

- Mettre à jour `00_etat.md` (⑧ ✅ + confirmation golden NEUTRE + version 0.5.0 +
  choix helper/duplication).
- Commit : `feat(thermique) : tronçon ⑧ snapshot météo + carte température au pont (0.5.0) — golden NEUTRE (vue)`.
- Écrire le kickoff `09_rendu_godot_evenements.md` avant le `/clear` (rendu C#/Godot
  des événements météo : pluie/neige/vent/grêle/orage + voile de manteau ; dérive
  NEUTRE = vue, filet `dotnet build Symbiose.csproj`).
