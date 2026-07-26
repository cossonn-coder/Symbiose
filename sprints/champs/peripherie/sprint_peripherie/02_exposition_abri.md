# ② Exposition & abri — la lisière devient un obstacle

> Sprint **PÉRIPHÉRIE** (D73). Lis d'abord `CLAUDE.md` + `00_etat.md` + le tronçon ①.
> Spec : `docs/champs/peripherie/conception_peripherie.md` §3.1, §3.2, §4.2.
>
> **Golden attendu : INCHANGÉ.** Interdiction de re-figer.

## Objectif

Faire agir la lisière sur **la lumière** et sur **le vent**. C'est le tronçon qui donne
enfin un sens à « couper la forêt » — sans lui, les gestes du ④ seraient creux.

**Le point clé à comprendre avant d'écrire une ligne** : il n'y a **rien à inventer**.
Le moteur traite déjà la maison comme un « obstacle global en coordonnées MONDE », dans
`light.compute(plants, saison, house=…, tile_origin=…)` et dans
`abri._obstacles(plants, house, tile_origin)`. Une lisière est **un obstacle de plus**
du même type. N'écris pas de « masque d'horizon » : ce serait un second système
redondant.

## Fichiers à toucher

- `data/code/fields/light.py` — accepter un paramètre `ceinture=None` et injecter les
  secteurs comme occulteurs (à côté du bloc maison existant).
- `data/code/fields/abri.py` — `_obstacles()` ajoute les secteurs ; porosité.
- `data/code/fields/ecofields/constants.py` — nouvelles constantes.
- `data/code/sim/engine/boucle.py` — passer `ceinture=self.game_state.get("ceinture")`
  aux deux appels (`eco.tick_light`, `eco.tick_abri`).
- `data/code/fields/ecofields/container.py` — passe-plat `tick_light`/`tick_abri`.

`light.py` est à **242 LDC** (bande verte) — si l'ajout le pousse au-delà de 300, extrais
la géométrie de lisière dans `fields/lisiere_geom.py` plutôt que de gonfler.

## Modèle

### A. Ombre de lisière (`light.py`)

Chaque secteur `foret` (ou `falaise`) devient un **rectangle balayé**, exactement comme
la maison : mêmes helpers `solar_slice` + `_point_in_swept_rect`, coordonnées MONDE, la
bande de décor faisant 900 cm de profondeur au-delà du bord du jardin.

- hauteur = `hauteur_canopee` (forêt) ou `altitude_relative` (falaise) ;
- opacité = `densite_ligneuse` (falaise : 1.0, la roche est opaque).

**Ne code aucune règle saisonnière.** Le comportement correct en découle tout seul —
à 49°N, une lisière de 15 m au sud à 9 m du bord donne 47 m d'ombre en hiver (tout le
jardin), 17 m aux équinoxes, 7 m en été (n'atteint pas le jardin). C'est `solar_slice`
qui le produit. Si tu te surprends à écrire `if saison == "hiver"`, tu t'es trompé.

⚠️ **`geom_key`** : ajoute la ceinture à la clé de cache géométrique de `compute`
(quelques scalaires par secteur). Sans ça, une coupe au ④ ne serait jamais prise en
compte. Avec ça, la ceinture étant statique, le cache reste HIT → coût ≈ 0.

### B. Abri & turbulence (`abri.py`)

`_obstacles()` renvoie aujourd'hui des 4-uplets `(cx, cy, hauteur_cm, rayon_cm)`.
**Passe-les en 5-uplets** `(cx, cy, h, rayon, poro)` :

- maison et plantes → `poro = None` ⇒ **branche historique, bit-identique** ;
- secteur de lisière → `poro = 1.0 − densite_ligneuse`.

Un secteur devient un obstacle très large (le bord entier), centré sur le milieu du
bord, à 900/2 cm au-delà de la limite du jardin.

```
# nouvelles constantes (fields/ecofields/constants.py)
REDUCTION_LISIERE_MAX = 0.75   # réduction du vent moyen d'un rideau PLEIN (φ=0)
TURBULENCE_MUR        = 0.45   # surcroît de RAFALE d'un rideau plein

reduction_lisiere  = REDUCTION_LISIERE_MAX * (1.0 - poro)
turbulence_lisiere = TURBULENCE_MUR * (1.0 - poro) ** 2
```

**Pourquoi ces deux formules et pas la parabole de portée des manuels** (lire §3.2 de la
conception avant d'improviser) : la règle « une haie poreuse protège jusqu'à 20-30 H
contre 10-15 H pour un mur » ne s'exprime **pas** à l'échelle du jeu — derrière une
lisière de 15 m, un jardin de 20 m tient entre 0 et 1,3 H, où le mur plein est *le plus*
protecteur. Ce qui s'exprime à 0-3 H, c'est la **turbulence de décollement** : le flux
décroche derrière l'obstacle imperméable et retombe en rafales. D'où la turbulence
**quadratique** — elle ne pénalise que le très dense.

La leçon de design qui en sort : *une lisière trop dense abrite du vent constant mais
fait tomber des rafales ; l'éclaircir un peu réduit la casse sans perdre l'abri.*

**Turbulence** : multiplie la rafale **locale** sur les plots du sillage. `gust_peak` est
calculé dans `sim/engine/boucle.py` et consommé par `_wind_damage`. Deux options — choisis
la plus simple qui n'altère pas le cas sans ceinture : soit un champ `eco.turbulence`
(lazy, comme `eco.vent` / `eco.givre` dans `container.py`), soit un facteur passé à
`_wind_damage`. Sans ceinture ⇒ facteur 1.0 partout ⇒ **strictement inchangé**.

⚠️ Ajoute `poro` à `_signature()` (le cache d'abri), sinon un changement de densité au ④
ne serait jamais vu.

## Tests

Étendre `tests/test_peripherie.py` :

1. **Neutralité** — sans ceinture (`None`), `light.compute` et `compute_abri` produisent
   des champs **bit-identiques** à avant. C'est le test qui protège le golden.
2. **Saisonnalité de l'ombre** — lisière `foret` au SUD, h = 1500 cm : lumière-sol du
   bord nord **fortement réduite en hiver**, **quasi inchangée en été**. Même lisière au
   NORD : effet nul à midi dans les deux cas.
3. **Porosité** — deux secteurs de même hauteur, `densite_ligneuse` 0.9 vs 0.5 : le dense
   réduit **plus** le vent moyen ET produit **plus** de turbulence. Vérifie la
   non-linéarité (l'écart de turbulence est plus marqué que l'écart de réduction).
4. **Perf** — deux ticks consécutifs sans changement de ceinture ⇒ cache HIT sur `light`
   (`compute` renvoie `[]`) et sur `abri`.

## Golden

`python3 -m tests.test_golden` → **INCHANGÉ**. Le golden ne pose ni maison ni ceinture,
et `poro=None` garde la branche historique.

## Ce qu'il NE faut PAS faire

- **Pas de « masque d'horizon »** ni de nouveau système d'occlusion : réutilise
  `_point_in_swept_rect` / `_point_in_capsule`.
- **Ne touche pas la porosité de la maison ni des plantes** (`poro=None`) : ce serait une
  dérive golden non nécessaire → c'est la dette **D94**, pas ce tronçon.
- **Pas de règle saisonnière écrite à la main** : la géométrie la produit.
- **Pas de bonus/malus sur les plantes** (#2) : on n'écrit que des champs du milieu.
- **N'exécute JAMAIS** `test_epaisseur_500ans`.
