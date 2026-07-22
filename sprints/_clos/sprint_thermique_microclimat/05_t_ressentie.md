# Tronçon ⑤ — T ressentie (mix air/sol) → croissance

> Sprint thermique-microclimat. Conception : `docs/champs/climat/conception_thermique_microclimat.md`
> (§2.4, §3). Kickoff **autosuffisant** (relançable à froid).
> Pré-requis : ④ CLOS (carte thermique DIURNE complète à 4 termes ; knobs
> `K_NEBUL_DIURNE=0.8` + table `NEBULOSITE` ; golden re-figé `c8af9e11…`).

## Objectif

Jusqu'ici le champ `temperature_sol` (microclimat de surface, calculé par
`tick_thermique` en 2b) **n'agit que sur l'hydrologie** (évaporation, ①). La
**croissance** lit toujours `eco.temperature` (T_air uniforme). Ce tronçon
**branche enfin T_sol sur la croissance** : le gate de stade bascule de T_air
nu vers une **T ressentie** = mélange air/sol local. Premier émergent visible :
un **coin chaud et ensoleillé pousse plus vite** qu'un coin frais/ombragé de la
même tuile (GDD locaux), et un coin surchauffé peut **stagner de chaud** (si le
gate a un plafond — pas le cas aujourd'hui, voir §note).

## Modèle (§2.4)

```
T_plante[r,c] = α · T_air + (1 − α) · temperature_sol[r,c]      (α = T_PLANTE_ALPHA = 0.5)
```

- Une feuille n'est PAS à la température du sol nu : son feuillage est dans
  l'air, modéré par le microclimat. D'où le **mélange** (pas T_sol pur).
- `α = 0.5` : poids égal air/sol (placeholder, calibrage post-test).
- T_sol est déjà spatialisée (soleil/ombre/humidité/litière/nuages) → la T
  ressentie hérite de toute cette hétérogénéité **sans nouveau calcul de champ**.

## Étapes

1. **`fields/ecofields/constants.py`** — dans le bloc « Microclimat de surface
   T_sol », ajouter sous les knobs ④ :
   ```python
   # T ressentie par la plante (tronçon ⑤) : le gate de croissance ne lit plus
   # T_air nu mais un mélange air/sol local. α = poids de T_air ; (1−α) = poids
   # de temperature_sol (microclimat déjà spatialisé). À α=0.5, air et sol pèsent
   # autant. C'est ce qui spatialise ENFIN la croissance (GDD locaux émergents).
   T_PLANTE_ALPHA = 0.5
   ```

2. **`sim/engine/croissance.py`** — dans `_avancer_stades`, ligne ~32, remplacer
   la lecture T_air nue par la T ressentie. Importer `T_PLANTE_ALPHA` depuis
   `fields` (le paquet ré-exporte les constantes ecofields — vérifier ; sinon
   `from fields.ecofields.constants import T_PLANTE_ALPHA`). Remplacer :
   ```python
   temp  = eco.temperature.at_plot(r, c)       # température ambiante (météo 02)
   ```
   par :
   ```python
   t_air  = eco.temperature.at_plot(r, c)            # T_air (masse, uniforme — météo 02)
   t_sol  = eco.temperature_sol.at_plot(r, c)        # microclimat de surface local (①–④)
   temp   = T_PLANTE_ALPHA * t_air + (1.0 - T_PLANTE_ALPHA) * t_sol   # T ressentie (⑤)
   ```
   Garder le nom `temp` → le reste du gate (`ok_temp`, logs `t={temp:.1f}°C`)
   est inchangé. Le commentaire `(météo 02)` du log devient « T ressentie ».

3. **Golden** — `python3 -m tests.test_golden`. **Échec attendu** : le gate de
   stade voit maintenant des températures locales (plus chaudes au soleil, plus
   fraîches à l'ombre/humide) → les dates d'avancement de stade bougent →
   cascade croissance/reproduction/succession. Vérifier la traçabilité (les logs
   `🌱 … t=…°C` montrent des T ≠ T_air selon le plot) puis re-figer (`--capture`).

4. **Suites ciblées** : `test_croissance` **va probablement bouger** (c'est le
   cœur du tronçon) — l'inspecter, comprendre la dérive, et la **mettre à jour
   si elle code en dur des seuils T_air**. `test_eau`, `test_population`,
   `test_genetique` doivent rester PASS (T_sol ne les touche pas directement).
   ⚠️ Si `test_croissance` casse sur des assertions de valeurs, c'est attendu :
   raconter la dérive à Nico, ajuster les attendus, NE PAS neutraliser le test.

## Invariant golden

- **Dérive attendue** : croissance spatialisée (GDD locaux) → dates de stade,
  floraison, reproduction, succession décalées (traçable au mécanisme T ressentie).
- **Doit rester** : déterminisme (T_sol déterministe), T_air (`temperature`)
  toujours uniforme et inchangée, `tick_thermique` inchangé (⑤ ne touche que la
  LECTURE côté croissance). Le **gel** lit encore T_air (c'est ⑥, séparé).

## Note (plafond chaud)

Le gate actuel n'a qu'un **seuil bas** (`ok_temp = temp >= temp_min_growth`) :
pas d'optimum ni de plafond. Donc « stress chaud » n'émerge PAS encore — un plot
surchauffé pousse juste plus vite (jamais moins). Un plafond thermique
(`temp_max_growth`) est un raffinage possible mais **hors scope ⑤** (ne pas
l'ajouter sans décision de Nico — philo #2, pas de malus direct gratuit).

## Validation

- `python3 -m tests.test_golden` re-figé.
- `python3 main.py 3` tourne sans crash.
- Vérif mécanisme (print jetable) : pour une même plante, `temp` ressentie
  diffère du `t_air` du plot (plus chaud au soleil sec, plus frais à l'ombre/humide).

## À faire en fin de tronçon

- Mettre à jour `00_etat.md` (statut ⑤ ✅ + nouveau hash dans §REPRISE +
  noter si `test_croissance` a été re-calibré).
- Commit : `feat(thermique) : tronçon ⑤ T ressentie (mix air/sol) → croissance spatialisée — golden RE-FIGÉ MAÎTRISÉ`.
- Écrire le kickoff `06_gel_nocturne.md` avant le `/clear`.
