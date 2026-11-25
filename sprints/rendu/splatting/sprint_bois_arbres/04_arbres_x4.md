# ④ Arbres au palier ×4 — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/rendu/splatting/conception_bois_arbres.md` (C5, §3.5).
Golden attendu : **`bce813af…` INTACT**. Build vert, 0 avertissement.

## Objectif
1. **Fleurs d'arbre ×4** : aujourd'hui posées une à une avec un plafond (`FleursArbreMax`,
   `PlantRenderer.FleursArbre.cs:39,108`) → couronne clairsemée comparée aux anciennes gerbes de
   fleurs (constat du sprint (a) ④bis). Les poser en **bouquets cuits** (recette splat d'un bouquet
   de corolles, à partir de `tete_corolle`) à la densité de `Floraison`, sur le petit bois de ③.
   Voir aussi `PlantRenderer.GerbesFleurs.cs` (gerbes de fleurs existantes).
2. **Masses de feuillage ×4** : capturer d'abord EN ÉTÉ (`houppiers`, plusieurs essences, et `full`)
   — les gerbes portent déjà les touffes splat depuis (a) ⑤. Ne corriger que ce que l'image montre
   (consigner le constat, même « rien à faire »).

## Mesures
- `verger_floraison` ×4 (pommier, cerisier en fleur) avant/après ; `houppiers` ×4 été ; `full` ×4.
- Nombre de tracés par arbre ×4 avant/après ; poids `assets/splats/`. Captures `mesures/04_*`.

## Ne PAS faire
- Tirer des fleurs au hasard hors de `Floraison` du moteur (philo #5 : la densité est un indice).
- `data/code/`, `test_epaisseur_500ans`, DeepSeek.

## Fin
`00_etat.md`, commit.
