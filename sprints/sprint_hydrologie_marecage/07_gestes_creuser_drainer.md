# ⑦ — Gestes joueur `creuser` / `drainer`

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Conception :
> `docs/conception/CONCEPTION_HYDROLOGIE_MARECAGE.md` §6. Prérequis : ①②③ faits.
> **Golden NEUTRE** (event-driven, hors tick — comme tous les gestes joueur).

## Objectif
Deux gestes sur le MILIEU (philo #1), coûteux en Vigueur : `creuser` (façonne une
cuvette qui accumule l'eau) et `drainer` (assèche une flaque/un marais).

## Fichiers
- `sim/actions.py` : `creuser(game_state, player, eco, r, c)` et
  `drainer(game_state, player, eco, r, c)` — patron des gestes existants
  (`becher`/`grelinette`/`ecraser` : coût via `cout_action`, écriture au plot).
- `sim/actions.py` (tables `COUTS`/`OBJETS_TOUCHES`) : coûts (creuser ÉLEVÉ,
  drainer MODÉRÉ-élevé), objets `("terrassement","bêche")`.
- `fields/ecofields/constants.py` : `CREUSER_DELTA` (cm d'altitude retirés),
  `BECHAGE_MICROBIOME_MALUS` (réutiliser) pour la perturbation de creuser.
- `tools/simserver/` (routeur `action` + version) : router `creuser`/`drainer`
  (target plot {r,c}), bump ENGINE_VERSION + changelog + tests pont.

## Modèle
```
creuser : altitude[r][c] = max(0, altitude[r][c] − CREUSER_DELTA)   # cuvette
          + ↓ microbiome (perturbation du sol, comme becher)
          + coût Vigueur ÉLEVÉ (terrassement)
drainer : eau_surface[r][c] = 0.0            # vide la flaque
          marais_memory[r][c] *= (1 − DRAINER_ASSECHE)   # assèchement forcé
          + coût Vigueur MODÉRÉ-élevé
```
`altitude` cesse d'être purement déterministe : le JOUEUR la modifie (event-driven,
hors tick → **golden neutre**). Découverte du geste à la 1ʳᵉ utilisation (D60).

## Golden
**NEUTRE** : gestes event-driven, jamais appelés par le tick. `test_golden`
inchangé. Le smoke ne creuse/draine rien. Vérifier via test pont (le geste
applique bien : altitude baisse, eau_surface se vide).

## Ce qu'il NE faut PAS faire
- Ne pas faire creuser/drainer par le tick (uniquement geste joueur).
- Ne pas oublier le coût Vigueur (`cout_action`) ni la perturbation de creuser.
- Ne pas créer d'UI ici (palette = ⑧/D55).

## F5
- Creuser une cuvette y amène-t-il l'eau (ruissellement ②) ? Drainer assèche-t-il
  visiblement un marais (③) ? Coûts Vigueur crédibles ?
