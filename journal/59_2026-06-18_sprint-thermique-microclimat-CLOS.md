# 2026-06-18 — Sprint THERMIQUE & MICROCLIMAT — SPRINT CLOS (10 tronçons)

> Conception : `docs/conception/CONCEPTION_THERMIQUE_MICROCLIMAT.md`.
> Branche `sprint/thermique-microclimat`. État détaillé tronçon par tronçon :
> `sprints/sprint_thermique_microclimat/00_etat.md` (§REPRISE).

Spatialiser la thermique (jusqu'ici uniforme) en la couplant au `LightField` :
tout émerge des champs déjà calculés (philo #2/#3 — flux → contrainte → réponse).
**10 tronçons, tous CLOS.**

## Ce qui a été construit (moteur Python ①→⑧, vue Godot ⑨⑩)

- **① socle T_sol diurne** — champ `temperature_sol` + helper pur
  `fields/ecofields/thermique.py` (calcul sorti du conteneur, `tick_thermique`
  délègue). Surchauffe solaire `GAIN_SOLAIRE·lum·intensité`, inertie lerp.
  `tick_hydrology` lit la T sol → évaporation spatialisée.
- **② refroidissement évaporatif** — chaleur latente : `cible −= REFROID_EVAP·hum`
  (cercle vicieux sécheresse).
- **③ isolation par le couvert** — `cible −= ISOLATION_COUVERT·litière_norm`
  (litière de la décompo → thermique : interconnexion des acteurs).
- **④ nébulosité** — `cible ×= (1 − K_NEBUL_DIURNE·nébulosité)` ; 1re entrée de la
  MÉTÉO dans la carte T_sol (scalaire/tick, couche respectée).
- **⑤ T ressentie → croissance** — le gate lit `T_PLANTE_ALPHA·t_air + (1−α)·t_sol`
  local ; 1re croissance SPATIALISÉE (GDD locaux).
- **⑥ gel nocturne localisé** — carte nocturne SÉPARÉE `t_min_nuit_at` (le soleil
  ne joue plus la nuit), `severity_fn` par plante dans `mortalite.py`. Paillage à
  deux échelles (rondelle joueur + litière émergente).
- **⑦ Neige + Orage** — ajoutés au catalogue ; Neige thermique (−6 °C → gel + manteau),
  Orage = pluie + vent composite ; **manteau neigeux** `eco.snow` par tuile (effet
  igloo : sous bon manteau `T_min_nuit → T_air`).
- **⑧ snapshot météo + carte T** — pont 0.5.0 : blocs `weather` (scalaire global +
  signes diégétiques) + `temperature[tile]{snow, t_sol}`. Helper partagé
  `weather_state` (un seul calcul météo, jamais deux qui dérivent).
- **⑨ rendu Godot météo** — `WeatherLayer` (ambiance écran : nébulosité, précip par
  kind, flash orage) + `SnowLayer` (manteau par tuile, monde). Vue pure.
- **⑩ heatmap T sol (F7)** — `SoilTempOverlay` : calque exact de `FieldOverlay`,
  source = snapshot `t_sol[r][c]`, palette/échelle `temperature` partagées (FIXE
  −5..35 °C). Overlay SÉPARÉ de F6 (qui montre l'air uniforme) : les deux coexistent.
  Vue pure.

## Goldens

① `50a6fd2d…` → ② `7cfef331…` → ③ `aab6c60a…` → ④ `c8af9e11…` → ⑤ `b1173a78…`
(⑥ NEUTRE) → ⑦ `5fddfe54…` (+ `population_hash` `5e6e688f…`) → ⑧⑨⑩ NEUTRES.
Chaque re-figeage est **maîtrisé et tracé** (cascade physique humidité→croissance→
succession, jamais un bug d'isolation). ⑨⑩ NEUTRES par construction (zéro Python).

## Knobs introduits

`GAIN_SOLAIRE=15` (placeholder), `REFROID_EVAP=6.0`, `ISOLATION_COUVERT=4.0`,
`LITIERE_REF=2.0`, `K_NEBUL_DIURNE=0.8` + table `NEBULOSITE`, `T_PLANTE_ALPHA=0.5`,
`RAYONNEMENT_NOCTURNE=5.0`, `SNOW_ACCUM`/`SNOW_MELT_BASE`/`SNOW_MELT_WARM`,
`TEMP_DELTA_BASE["Neige"]=-6.0`, `ORAGE_VENT`.

## Dette ouverte (reportée)

- **D37** vent continu · **D38** rosée/hygrométrie (reportés du sprint).
- `container.py` = **372 ldc** code pur (> ~350) — candidat éclatement (mixin décompo).
- `test_pommier_fruite` (smoke pont 14b) échoue depuis le re-figeage LARGE de ⑦ —
  à traiter HORS sprint.

## Clôture

**SPRINT THERMIQUE & MICROCLIMAT CLOS.** Filet `dotnet build` vert (0/0) au ⑩.
F5 = Nico. Prochain = choix Nico (BACKLOG.md / DETTE.md), pas d'enchaînement auto.
