# ① Atelier des matériaux pavables (porte de décision) — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/rendu/splatting/conception_sol_meteo_splats.md` (§3.1),
`tools/splat/README.md`, `tools/splat/cuire_ecorces.js` (patron : bande périodique + couture mesurée +
parallèle), `tools/splat/cuire.js` (options, format des planches), `tools/splat/lib/codes.js`,
`world/WorldView.Projection.cs` (projection iso, rotation D35).
Golden attendu : **`bce813af…` INTACT**. Aucun fichier C# touché.

## Objectif
Un outil `tools/splat/cuire_tapis.js` qui cuit un **matériau pavable** : une scène de splats posée sur un
plan horizontal **en tore** de côté P cm, photographiée par une caméra orthographique **identique à la
projection du jeu** (losange 39×19,5 px par plot de 50 cm à ×1), en codes de planche splat (ton = volume,
orientation, A), à un palier donné. Une première recette : `recettes/tapis_terre_motteuse.js`.

## À faire
1. Vérifier au code la projection (`WorldToScreen`, `TileWPx/TileHPx`, élévation implicite du 2:1) et en
   déduire la caméra de cuisson. Cellule périodique = boîte englobante du losange de côté P
   (78×39 px à ×1 pour P = 1 m [calculé]) — à confirmer.
2. Tore : chaque splat dont l'empreinte déborde est recopié décalé de ±P (x, y, et les coins).
3. **Variantes à bord commun** : splats touchant la bande de bord = communs (graine du matériau),
   intérieur = graine de la variante. Nombre par palier : 4 (×0,5-×4), 2 (×8), 1 (×16, ×32) ; P = 1 m ;
   option `--echelles`/`--paliers` acceptant **64** avec P = 50 cm (préparation ⑧).
4. Sortie : `assets/splats/tapis_<geometrie>_x<z>.png` (+ variantes) + `assets/splats/tapis.json`
   (cellule, période, variantes, hauteur moyenne des tons…). Déterministe (deux cuissons = mêmes octets).
5. Planche de contrôle (`--controle`) : la cellule pavée 3×3 en couleurs de contrôle, variantes mêlées
   au hash, pour voir la couture et la répétition à l'œil.

## Mesures (porte de décision — écrire dans `00_etat.md`)
- **Couture** : texels différents entre bords opposés = 0 attendu (comme `couture_texels`).
- Temps de cuisson par palier et par variante [VM, charge notée via `uptime`, n=…], poids PNG par palier.
- **Le ton sert-il de hauteur ?** histogramme des tons de la terre motteuse : il faut des creux (0-1) et des
  bosses (3-4) en proportions utilisables par le seuil E6, sinon ajuster la recette.
- Extrapolation à ~10 géométries × 7 paliers : durée, Mo git (alerte `assets/splats/` 200 Mo, 67 Mo avant).

**Porte** : si la couture n'est pas nulle, si le pavage 3×3 montre une grille, ou si l'extrapolation
dépasse ~150 Mo git ou ~24 h de cuisson, s'arrêter et consigner (retour conception), sans contournement.

## Ne PAS faire
- Toucher la vue. `data/code/`, `test_epaisseur_500ans`, DeepSeek, `tools/splat/vendor/`.

## Fin
`00_etat.md` (compte rendu ①), commit `feat(tapis①) : …`.
