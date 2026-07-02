# ② — Rendu : relief extrudé + exposition snapshot + recalage objets

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Prérequis :
> **①a + ①b faits** (le champ `epaisseur_sol` existe et évolue). Conception :
> `docs/conception/CONCEPTION_EPAISSEUR_SOL.md` §4. **Tranche PUR-VUE, golden
> NEUTRE.** Contient des points **F5** (le F5 visuel est à Nico).

## Objectif

**Voir** le sol monter/descendre : chaque plot reçoit un **relief** proportionnel
à son épaisseur, mis à jour au fil des saisons via le snapshot.

## Partie A — Exposition snapshot (Python, golden NEUTRE)

Dans `tools/simserver/serialize.py`, il existe déjà l'exposition d'une grille 2D
par tuile (`temperature.t_sol`, ~ligne 255) :

```python
temperature[tile.tile_id] = {
    ...,
    "t_sol": [[round(eco.temperature_sol.data[r][c], 2)
               for c in range(...)] for r in range(...)],
}
```

Copie ce patron pour exposer `epaisseur[r][c]` par tuile (grille 2D dense, ou
liste creuse à la `litiere` si beaucoup de plots sont au plancher — au choix,
dense est plus simple ici). Ajoute la clé au dict de sortie (~ligne 324 où sont
assemblés `structures`, `litiere`, `temperature`…). **PURE lecture** de
`eco.epaisseur_sol` (déjà rempli par le tick) → golden **NEUTRE**.

Re-bump `ENGINE_VERSION` (`tools/simserver/version.py`) avec entrée changelog.

## Partie B — Relief extrudé (C#, pur-vue)

Le rendu du sol est dans `world/WorldView.Monde.cs` :
- `BuildGround(GDict world)` (~l.60) : bâtit **une fois** un losange **plat**
  (`Sprite2D`/`Polygon2D`) par plot à `WorldToScreen(cx, cy)`.
- `BuildHouse` (~l.176) montre le **patron d'extrusion Z** : `hPx = heightCm *
  PxPerCmZ` (`PxPerCmZ = 0.39 px/cm`), flancs `Polygon2D`, dessus décalé de
  `upWall = new Vector2(0f, -wallCm * PxPerCmZ)`.

Applique ce patron au sol : pour chaque plot, un **flanc iso** sous le losange, le
dessus **remonté de `epaisseur_px = epaisseur_cm * PxPerCmZ`**. Détails à trancher
au F5 :
- **Mise à jour par snapshot** : `BuildGround` est bâti une fois ; le relief doit
  **suivre** l'épaisseur (elle évolue). Option A = reconstruire les flancs à
  chaque snapshot (cf. comment les autres éléments dynamiques lisent le snapshot,
  `world/WorldView.Snapshot.cs`). Option B = moduler un paramètre (`Scale`,
  offset) sans reconstruire. Choisis au F5 selon le coût.
- **Échelle visuelle** : `epaisseur_cm` peut être petite ; un **facteur
  d'exagération** visuel est probablement nécessaire pour que le relief se lise
  (calibrage F5, comme le reste du rendu).

## Partie C — Recalage des objets posés (C#, F5 délicat)

Plantes, litière, macro-vie, structures sont ancrées **sur le sol** via
`WorldToScreen`. Si le sol monte de `epaisseur_px`, leur ancrage vertical doit
**remonter d'autant**, sinon ils flottent ou s'enfoncent. Repère les points
d'ancrage (probablement `WorldView.Projection.cs` / `WorldToScreen`, et les
`Position = WorldToScreen(...)` des renderers : `PlantRenderer`, litière, macro).

Approche recommandée : un **helper d'offset vertical** `EpaisseurOffset(cx, cy)`
qui retourne `-epaisseur_px` au plot foyer, appliqué aux positions des objets
posés. **Ne PAS** disperser le calcul — un seul point de vérité.

C'est **le gros du travail visuel** et l'essentiel du risque F5. Procède
incrémentalement : d'abord le relief sans recalage (objets flottants, mais on voit
le sol bouger), puis le recalage.

## Golden

**NEUTRE.** Partie A = pure lecture. Parties B/C = C# (hors golden Python).
`python3 -m tests.test_golden` doit rester **inchangé**. S'il bouge, tu as touché
le moteur par erreur → annule.

## Ce qu'il NE faut PAS faire

- Ne pas modifier le moteur de simulation (aucun `data/code/` hors serialize.py
  lecture + version bump).
- Ne pas re-figer le golden (cette tranche est neutre).
- Ne pas disperser le calcul d'offset (un seul helper).
- Respecter la **bande de taille** des fichiers C# : si `WorldView.Monde.cs`
  gonfle, sors le relief dans un partial dédié (`WorldView.Relief.cs`) — un
  fichier = une responsabilité.

## Points F5 (Nico)

- Le relief se lit-il bien à l'iso 2:1 ? Facteur d'exagération correct ?
- Les objets posés restent-ils bien accrochés quand le sol monte/descend ?
- Coût de la reconstruction par snapshot acceptable (F4 perf) ?
