# Sprint implémentation météo — état partagé

> **État léger, mis à jour en fin de chaque sous-sprint.** La spec de référence
> figée est [`data/code/CONCEPTION_METEO.md`](../../data/code/CONCEPTION_METEO.md)
> (Sprint conception météo, 2026-06-03). Couvre **D16** + **Z2**.
>
> Boucle : lancer `0N` → travailler → **vérifier/re-figer le golden** → mettre à
> jour ce fichier → commit → `/clear` → lancer `0N+1`.

## Où on en est

- Conception **figée** (`CONCEPTION_METEO.md`). Implémentation **pas commencée**.
- Pivot à porter : `random.choice(ALEAS_METEO)` (RNG live, viole philo #3) →
  fonction pure `weather_at(seed, week)` via `_hash_noise`.

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

- _(à remplir au fil des sous-sprints)_

## Décisions prises en cours de route

- _(vide au démarrage — voir `CONCEPTION_METEO.md` pour les décisions figées)_
</content>
