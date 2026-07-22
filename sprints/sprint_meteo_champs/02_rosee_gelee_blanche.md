# ② Rosée & gelée blanche — cœur thermo-hydrique nocturne

> Lire d'abord `00_etat.md` + `docs/champs/climat/conception_meteo_champs.md` (§3).
> Dépend de ① (le point de rosée lit l'humidité médiée). Premier geste : RE-MESURER
> les hashs golden (référence post-①).

## Objectif
Ajouter `tick_rosee` : lire le thermomètre nocturne `t_min_nuit_at` déjà existant, en
dériver un **point de rosée local**, et déposer la condensation selon un **continuum** —
**rosée liquide** (>0 °C, humidité+) ou **gelée blanche / givre** (≤0 °C, fonte différée
+ dégât foliaire léger). Émettre les signes diégétiques au log. Golden re-figé annoncé.

## À faire

### A. Helper pur `fields/ecofields/rosee.py` (NOUVEAU, miroir de `thermique.py`)
- `tick_rosee(eco, t_air, nebulosite) -> list[str]` (log des signes). Pour chaque plot :
  - `t_min = t_min_nuit_at(eco, r, c, t_air, nebulosite)` (import depuis `thermique`).
  - `hum_norm = min(1, eco.humidite.at_plot(r,c) / 3.0)` (échelle de `tick_thermique`).
  - `t_rosee = t_air − ÉCART_ROSÉE_SEC + GAIN_HUM_ROSÉE · hum_norm`.
  - `cond = max(0, t_rosee − t_min) · ROSÉE_PAR_DEGRÉ`. Si `cond ≤ 0` → rien.
  - **Régime liquide** (`t_min > 0`) : `eco.humidite.add(r, c, cond)`.
  - **Régime givre** (`t_min ≤ 0`) : accumuler `cond` dans l'état givre (B) ; PAS d'eau
    liquide ce tick.
- Pur : zéro RNG, écrit `humidite` (rosée) + l'état givre. Émet un marqueur de log agrégé
  par tuile si la condensation totale dépasse un seuil notable (`💧 rosée` / `❄ gelée blanche`).

### B. État givre + fonte différée (`container.py`)
- Choisir le support le plus sobre (à trancher en codant) : une carte `givre` (GridField,
  comme `snow`) OU un scalaire par plot. Mémorise l'eau condensée gelée non encore restituée.
- Fonte : au tick où `t_min_nuit > 0` sur le plot, reverser le givre accumulé dans
  `humidite` (borné) et remettre l'état à 0. Couplage hydrique réaliste **et sûr**.
- Exposer une fine méthode `eco.tick_rosee(t_air, nebul)` qui délègue au helper (A) +
  gère la fonte différée. **No-op** si pas de condensation (golden-safe par construction).

### C. Dégât foliaire de la gelée blanche (léger, médié) — OPTION
- Réutiliser `_mediated_damage` (`sim/engine/mortalite.py`) avec cause `"givre"`, gène
  `rusticite_froid`, sévérité FAIBLE (`GIVRE_SEVERITY_REF` élevé → dégât plancher).
- **Cible le feuillage établi exposé, PAS les semis** (déjà couverts par le gel
  tissulaire `boucle.py:105` → **pas de double comptage**, périmètres disjoints).
- Si le calibrage rend ça trop brutal : se contenter de B (dépôt + fonte), le dégât est
  l'option « riche ». NOTER le choix dans `00_etat.md`.

### D. Câblage boucle (`sim/engine/boucle.py`)
- Appeler `eco.tick_rosee(temp_now, nebul)` **entre** la thermique (2b, ~L175) et
  l'hydrologie (3, ~L179) : la rosée lit la T_sol/l'humidité de fin de tick précédent
  (cohérent avec l'ordre nocturne), et son dépôt est ensuite drainé/diffusé normalement.
- Le dégât givre (C) s'applique près du bloc gel (~L105) ou dans `tick_rosee` selon le
  découpage choisi — garder déterministe (ordre des tuiles/plots stable).

### E. Constantes (`constants.py`, tête de fichier, calibrage post-test)
`ÉCART_ROSÉE_SEC` (~6 °C) · `GAIN_HUM_ROSÉE` (remonte le point de rosée avec l'humidité
sol) · `ROSÉE_PAR_DEGRÉ` (eau/°C sous le point de rosée) · `GIVRE_SEVERITY_REF`.

## Couches
`rosee.py` dans `fields/ecofields/` (pur, comme `thermique.py`). Câblage d'ordre dans
`boucle.py`. Le dégât médié reste une réponse plante (`mortalite.py`).

## Définition de done
- `fields/ecofields/rosee.py` créé (helper pur) + `eco.tick_rosee` (fine délégation + fonte).
- Câblage boucle entre thermique (2b) et hydrologie (3).
- Constantes nommées en tête de `constants.py`.
- `tests/test_rosee.py` (NOUVEAU) : nuit claire + sol humide + sol nu → rosée déposée ;
  nuit couverte → ~rien (peu de refroidissement) ; sol paillé → moins que sol nu ; régime
  ≤0 °C → givre accumulé puis FONTE différée restitue l'eau au réchauffement ; sol sec →
  peu de rosée (point de rosée bas). Déterminisme : deux runs identiques → mêmes valeurs.
- **Golden re-figé MAÎTRISÉ** : la dérive doit venir des nuits claires du smoke (humidité
  matinale en hausse). Recapturer, **noter hash + justification** dans `00_etat.md`.
- MAJ `00_etat.md` (② → FAIT) puis commit.

## Pièges
- **Tension voulue, pas un bug** : nuit couverte = peu de rosée (peu de refroidissement) ;
  sol desséché = peu de rosée (point de rosée bas). Ne PAS « corriger » ça.
- **Pas de double comptage givre/gel** : givre = feuillage établi ; gel = semis. Disjoints.
- **Ordre** : `tick_rosee` lit l'humidité d'AVANT `tick_hydrology` (comme `tick_thermique`).
  Ne pas réordonner. Déterministe (plots dans l'ordre, zéro RNG).
- Le marqueur de log doit être parsable par `sim/evenements.py` si on veut que le carnet
  (⑤) le capte — choisir un emoji/format cohérent avec l'existant.
