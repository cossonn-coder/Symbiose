# Tronçon ② — Spatial LOD LightField (bit-identique) + cache géométrique

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` + `docs/perf/run_eternel/conception_perf_run_eternel.md`
> §2(M2)/§5. Lancement depuis `data/code/`. Fichier cœur : `fields/light.py`.

## Objectif
Couper le coût super-linéaire de `LightField.compute` (~53 % du CPU, dette D32) **sans
changer d'un bit** le résultat (golden intact, comme le passage gather→scatter D32). Deux
leviers :
1. **Spatial hash** de la boucle « lumière REÇUE par plante » (`light.py:240-263`),
   aujourd'hui **O(N²)** : chaque plante parcourt tous les voisins plus hauts.
2. **Cache géométrique** : réutiliser le champ quand la géométrie n'a pas changé (temps
   figé / planification).

## Contexte moteur (déjà en place)
`fields/light.py` produit deux choses par tick (lire le fichier en entier d'abord) :
- **lumière reçue par plante** (`self.received[id(p)]`) : boucle l.240-263. Pour chaque
  plante, pour chaque tranche solaire, pour 5 échantillons sous sa canopée, parcourt
  `order` (plantes triées hauteur DÉCROISSANTE) et multiplie `att *= (1.0 - qd)` pour
  chaque voisine PLUS haute dont la capsule couvre l'échantillon. Le `break` sur
  `qh <= ph` limite déjà, mais au pire (peuplement de hauteurs proches) c'est O(N²).
- **lumière-sol par plot** (scatter, l.276-325) : DÉJÀ élagué par bounding-box de capsule
  (D32). Coût ∝ plantes × bbox. Le laisser tel quel ici (le gros gain O(N²) est sur la
  lumière reçue).

## Levier 1 — spatial hash de la lumière reçue (BIT-IDENTIQUE)
Construire, une fois par `compute`, un index spatial des plantes-obstacles (les `infos` /
`order`) par cellule de grille (bucket = plot-foyer, ou grille au pas ≈ rayon max de
canopée). Pour un échantillon `(sx, sy)` donné, ne consulter QUE les buckets dont une
capsule PEUT atteindre l'échantillon (bucket courant + voisins dans le rayon de capsule
max). Puis, parmi ces candidats, itérer **exactement** les voisines plus hautes dont
`_point_in_capsule` renvoie True — **dans le même ordre hauteur-décroissante** que
`order`.

**Invariant bit-à-bit (CRITIQUE)** : le produit `att` doit accumuler les mêmes facteurs
`(1.0 - qd)` dans le **même ordre** qu'aujourd'hui. Le spatial hash ne fait qu'ÉLAGUER des
plantes dont la capsule ne couvre PAS l'échantillon (elles renvoyaient déjà False dans
`_point_in_capsule` → facteur 1.0, sans effet). Retirer un facteur 1.0 est neutre en
flottant → **résultat identique**. Donc : après avoir collecté les candidats d'un
échantillon, les **trier par hauteur décroissante** (même clé que `order`, départages
identiques) avant d'appliquer les facteurs. Si deux plantes ont exactement la même
hauteur, préserver l'ordre relatif de `order` (tri stable sur la même séquence source).

**Piège** : ne pas oublier les **squelettes debout** (`infos` inclut les morts `seche`,
l.213-217) et le fait que `order` est trié sur TOUTES les `infos`. L'index spatial doit
contenir les mêmes obstacles que `order`.

## Levier 2 — cache géométrique (temps figé)
Mémoriser un **hash de géométrie** = (saison, house, tile_origin, et pour chaque plante
vivante : `x_cm, y_cm, current_height, canopy_radius_at, foliage_density_at`). Si ce hash
est identique à l'appel précédent sur la même tuile → **réutiliser** `self.data` et
`self.received` tels quels (return immédiat). Sinon recomputer.
- En **temps figé** (planification : aucune croissance) le hash est stable → coût ≈ 0.
- Dans le **golden** et en saison, la géométrie change chaque semaine (croissance) → cache
  MISS → recompute → résultat identique. **Golden neutre par construction.**
- Attention déterminisme : le hash doit être une fonction PURE de l'état géométrique, pas
  de `id()` ni d'ordre non déterministe. Utiliser des tuples de flottants arrondis de
  façon STABLE (ou les flottants bruts si reproductibles). Le cache est un pur
  memo : jamais de faux hit (si doute, préférer recomputer).

## Golden attendu
**INTACT** — hash `061934db09ad646a01f19b8f4d0b677f13438e87bce2f8531527be425e7c22a8`.
C'est le test décisif du tronçon : si le hash bouge, l'élagage a retiré un facteur ACTIF
ou changé l'ordre → **bug**, on corrige, on ne re-fige JAMAIS. Vérifier :
`python3 -m tests.test_golden`.

## Mesure (attendue, à reporter)
Avant/après via `python3 -m tools.profile_tick 52 20` (2 tuiles) ET une variante 8 tuiles
si `profile_tick` le permet. Reporter ms/tick et % LightField. Gain attendu : croissant
avec la densité (le régime qui plante). Si le gain est décevant sur 2 tuiles (faible N),
le mesurer sur 8 tuiles où l'O(N²) mord.

## Ce qu'il NE faut PAS faire
- Ne PAS numpy-vectoriser ici (réserve — l'ordre de sommation float casserait le bit-à-bit).
- Ne PAS toucher au scatter lumière-sol (déjà élagué D32), sauf gain bit-identique évident.
- Ne PAS changer les formules solaires/capsules — uniquement QUI on visite, pas COMMENT on
  calcule.
- Ne PAS dépasser la bande de taille (`tools/compte_ldc.py` sur `light.py`) : si l'ajout
  fait gonfler `light.py` au-delà de ~300 LDC pur, extraire l'index spatial dans un module
  voisin (`fields/light_index.py` p.ex.), imports intacts.

## Fin de tronçon
Mettre à jour `00_etat.md` (gain mesuré, golden intact confirmé). Commit.
