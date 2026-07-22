# Tronçon ② — Champs : catena topographique

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + ce fichier. Doc complet :
> `docs/vegetal/genetique/conception_diversite_fondatrice.md`. Le flag `heterogene` a été
> introduit au ① (`init_eco`) — on le réutilise ici.

## Objectif
Que les champs édaphiques de sol démarrent **hétérogènes**, structurés par la
**topographie** (catena : versant plus sec/pauvre, fond plus humide/riche) →
terrain lisible et jamais identique (philo #5/#6/#7), cohérent avec la diversité
génétique du ①.

## Contexte moteur (déjà en place)
- `fields/ecofields/container.py` :
  - `EcoFields.__post_init__` initialise les champs. **Uniformes** à l'init : `ph`
    (= `PH_PAR_SOL[soil_type]`), `n/p/k` (= `NUTRIENT_INIT_PAR_SOL[soil_type]`),
    `structure_sol` (= `STRUCTURE_INIT_PAR_SOL[soil_type]`), `microbiome`, `humidite`.
  - Déjà hétérogènes via `init_eco` : `om_stable` (`_init_heterogene`, D56),
    `altitude` (canal `stable_str_hash(tile_id+"_alt")`).
  - `_init_heterogene(self, grid, plancher)` : pose `plancher × facteur`,
    `facteur = 1 + INIT_AMPLITUDE·(2·bruit−1)`, `bruit = _hash_noise(stable_str_hash
    (tile_id), 0, r, c)`.
  - `init_eco(tile_id, rows, cols, humidite, fertilite, microbiome, soil_type,
    heterogene=False)` : construit la tuile. Pose `om_stable` (491), force
    humidite/microbiome/npk uniformes (492-499), `epaisseur_sol` (505-507),
    `altitude` (515-519). **ORDRE ACTUEL : altitude posée APRÈS les édaphiques.**
- `fields/ecofields/constants.py` : `INIT_AMPLITUDE`, `PH_PAR_SOL`, `PH_MIN/MAX`,
  `NUTRIENT_INIT_PAR_SOL`, `STRUCTURE_INIT_PAR_SOL`, `ALT_BASE`, `ALT_AMPLITUDE`,
  `ALT_MAX`. Y ajouter les amplitudes propres.
- `fields/noise.py` : `_hash_noise(seed,week,r,c)`, `stable_str_hash(text)`.

## Modèle / implémentation

### a) Réordonner `init_eco`
Poser l'**altitude AVANT** les champs édaphiques (elle doit exister pour que la
catena la lise). Puis, SI `heterogene`, hétérogénéiser les édaphiques en dérivant
de l'altitude déjà posée.

### b) Primitive généralisée (catena)
Nouvelle méthode `EcoFields._init_catena(self, grid, base, amplitude, canal_suffixe,
poids_topo, sens_topo)` :
```
seed_c = stable_str_hash(self.tile_id + canal_suffixe)
for r,c:
    alt = self.altitude.at_plot(r, c)
    topo = sens_topo * _recentre(alt)        # ∈ [-1,1], normalisé sur [ALT_BASE±ALT_AMPLITUDE]
    bruit = 2*_hash_noise(seed_c, 0, r, c) - 1   # ∈ [-1,1] décorrélé
    facteur = 1 + amplitude * (poids_topo*topo + (1-poids_topo)*bruit)
    grid.set(r, c, base * facteur)
```
- `base` = valeur uniforme héritée (`PH_PAR_SOL[...]`, `NUTRIENT_INIT[...]`, etc. ou
  la valeur du param `microbiome`/`fertilite` passée).
- `sens_topo` : **NPK/microbiome = −1** (riches en BAS = altitude basse) ;
  `structure_sol` = +1 ou faible (sol de versant mieux structuré) ; `ph` = topo
  faible (surtout roche-mère → `poids_topo` bas).
- **Amplitudes PROPRES** (nouvelles constantes, valeurs de DÉPART, calibrage F5) :
  `PH_INIT_AMPLITUDE=0.03` (PETITE — portes `bell`), `NPK_INIT_AMPLITUDE=0.20`,
  `STRUCTURE_INIT_AMPLITUDE=0.10`, `MICROBIOME_INIT_AMPLITUDE=0.20`.
- `poids_topo` par champ (ex. NPK/microbiome 0.6, structure 0.4, pH 0.2).
- Le `GridField.set` **borne** déjà (min/max) → écrête les valeurs extrêmes.

### c) Appliquer dans `init_eco` (sous `if heterogene:`)
Après l'altitude : `_init_catena` sur `n`, `p`, `k`, `structure_sol`, `microbiome`,
et `ph`. **NE PAS** toucher `humidite` (exclue — ruissellement) ni
`temperature*`/`om_stable`/`altitude`.

## Golden
**Re-figé (ECO)**, annoncé. Cause : le harnais `test_golden` passe `heterogene=True`
(posé au ①) → les champs édaphiques deviennent hétérogènes → la ligne `ECO ...` et,
par ricochet, la biologie (germination pH/thermique, NPK/Liebig) dérivent de façon
déterministe. Re-figer APRÈS avoir vérifié : amplitudes petites, pas de plot
hors-fenêtre catastrophique (mortalité de masse). Consigner le nouveau hash.
> Si la dérive est trop violente (mortalité anormale), BAISSER les amplitudes avant
> de re-figer — ne jamais re-figer une dérive pathologique.

## Tests
- **Neuf** (compléter `tests/test_diversite_fondatrice.py` ou dédié) : (1)
  `heterogene=True` → champ non uniforme (variance > 0) ; (2) `heterogene=False`
  (défaut) → champ STRICTEMENT uniforme (non-régression tests ciblés) ; (3)
  décorrélation — deux champs à canaux ≠ ne sont pas identiques plot-à-plot ; (4)
  déterminisme — même tile_id → même motif.
- **Ne pas toucher** les tests unitaires qui appellent `init_eco` sans `heterogene`
  (défaut False → intacts).

## NE PAS faire
- Ne pas hétérogénéiser `humidite`, `temperature*`, `om_stable`, `altitude`.
- Ne pas relever les amplitudes « pour voir » (portes dures pH/NPK).
- Ne pas retirer le flag / changer son défaut (False).

## Fin de tronçon
Golden re-figé + hash consigné, tests verts, `00_etat.md` mis à jour, commit.
