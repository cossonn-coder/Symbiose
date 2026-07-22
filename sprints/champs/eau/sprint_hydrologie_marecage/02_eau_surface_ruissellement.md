# ② — `eau_surface` + ruissellement latéral (`tick_ruissellement`)

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Conception :
> `docs/champs/eau/conception_hydrologie_marecage.md` §2. **Golden RE-FIGÉ LARGE
> ANNONCÉ** (l'eau bouge entre plots). Prérequis : ① fait (`altitude` existe).

## Objectif
L'eau excédentaire ne s'infiltre plus indéfiniment : le surplus fait une **lame de
surface** `eau_surface` qui **ruisselle** vers les plots plus bas, s'infiltre,
s'évapore. Une cuvette accumule (flaque), une bosse s'assèche.

## Fichiers
- `fields/ecofields/container.py` : champ `eau_surface: GridField` (initial 0) +
  registre `get_field`.
- `fields/ecofields/hydrologie.py` : dans `tick_hydrology`, **capturer l'excédent**
  au lieu de l'écrêter — si `h > HUM_CAP`, `eau_surface += (h − HUM_CAP)`, `h = HUM_CAP`.
- `fields/ecofields/hydrologie.py` (ou module neuf `ruissellement.py`) :
  `tick_ruissellement(altitude, epaisseur)` — écoulement double-buffer.
- `fields/ecofields/constants.py` : `HUM_CAP` (= plafond hum actuel), `SEUIL_FLAQUE`,
  `RUISSELLEMENT_FRACTION`, `INFILTRATION_SURFACE`, `EVAP_SURFACE` (placeholders).
- `sim/engine/boucle.py` : appeler `eco.tick_ruissellement(...)` **juste après**
  `tick_hydrology` (~l.215), AVANT `tick_decomposition`.
- `tools/simserver/serialize.py` : bloc `eau_surface` par tuile (liste creuse
  `[r,c,lame]` — la plupart des plots secs) + bump pont/version + tests.
- NOUVEAU `tests/test_ruissellement.py` : conservation de masse, cuvette accumule,
  anti-emballement 500 ans.

## Modèle (déterministe)
`tick_ruissellement` :
1. **Snapshot** `src = copie de eau_surface` (double buffer) ; `dst` = grille neuve.
2. Pour chaque `(r,c)` : `S(r,c) = altitude[r][c] + epaisseur_sol[r][c]`. Voisins
   von Neumann plus bas : `Δk = max(0, S(r,c) − S(voisin_k))`. Si `Σ Δk > 0`,
   distribuer `flux = RUISSELLEMENT_FRACTION * src[r][c]` réparti `∝ Δk/ΣΔk` vers
   chaque voisin descendant ; le reste `src[r][c] − flux` demeure. **Masse conservée**
   (ce qui sort d'un plot entre chez les voisins ; bords du monde = perdu = exutoire).
3. **Infiltration** : `infil = min(dst[r][c], INFILTRATION_SURFACE, HUM_CAP − humidite[r][c])`
   (borné par ce que le sol peut boire) → `humidite += infil`, `dst[r][c] −= infil`.
4. **Évaporation de surface** : `dst[r][c] *= (1 − EVAP_SURFACE)`.
5. `eau_surface = dst`.

⚠️ Lire `src`/`S` du **même instantané** → indépendant de l'ordre de balayage
(déterminisme, philo #3). Zéro RNG.

## Golden
**RE-FIGÉ LARGE ANNONCÉ.** L'eau circule → bilan hydrique par plot modifié
(cuvettes gorgées, bosses sèches). Dérive localisée à la topographie, attendue.
Re-figer `tests/test_golden.py` (nouveau hash consigné dans `00_etat.md` §REPRISE
avec explication). **Non-régression** : `test_senescence` (D39, pommier meurt de
sénescence ~59.8 ans, pas asphyxié) et `test_epaisseur_500ans` (D57) doivent
rester VERTS — si une cuvette gorge le pommier isolé, corriger l'altitude du BANC
de test (pas le modèle). `test_ruissellement` neuf VERT.

## Ce qu'il NE faut PAS faire
- Ne pas ruisseler l'`humidite` des pores (seule `eau_surface` ruisselle).
- Ne pas balayer en place (biais d'ordre = RNG déguisé) — double buffer obligatoire.
- Ne pas créer le marais ici (c'est ③) ; ② s'arrête à la flaque = `eau_surface`.

## F5
- Les flaques se forment-elles dans les cuvettes après une pluie ? Évacuation
  crédible ? Calibrage `RUISSELLEMENT_FRACTION`/`SEUIL_FLAQUE` au banc `tourbiere` (③).
