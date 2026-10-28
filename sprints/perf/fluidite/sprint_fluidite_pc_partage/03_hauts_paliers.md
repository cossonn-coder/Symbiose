# ③ Hauts paliers ×4 ↔ ×32 — mesurer l'envoi au GPU, puis agir

Lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/perf/fluidite/conception_fluidite_pc_partage.md`
§2 et §4 ③, et la section « Run PC du 2026-10-27 — rapport Z » de
`sprints/perf/fluidite/sprint_fluidite_pc_leviers/00_etat.md`. **Golden intact.** Filet :
`dotnet build Symbiose.csproj`. Pas d'appel DeepSeek.

## Contexte
Rapport Z au PC [n=1 aller-retour] : ×0,5 ↔ ×4 pire 44-82 ms (OK) ; ×4 ↔ ×32 pire 99-453 ms,
×8→×4 = 453 ms dont 10 ms attribués aux postes ; ×16→×8 301 dont 116. Postes attribués :
`plantes _Draw` jusqu'à 83 ms, `plantes vectoriel` jusqu'à 56 ms. Hypothèse NON mesurée :
création/envoi de textures (cuisson des plantes en images plus grandes aux hauts paliers)
ou de maillages au GPU au moment du cran.

## (a) Mesurer d'abord
- Outil existant : `world/WorldView.ZoomJournal.cs` (touche Z, balayage
  `tools/perf_vm.sh -Z SEC`), postes `visuals/PerfPostes.cs`, `world/WorldView.PerfMesure.cs`.
- Ajoute par image de la fenêtre de cran : delta de mémoire vidéo / textures / tampons
  (`Performance.Monitor.RenderVideoMemUsed`, `RenderTextureMemUsed`,
  `RenderBufferMemUsed` — vérifie les noms exacts de l'API Godot 4.6 C#), nombre de
  textures créées ou mises à jour (compte dans le chemin de cuisson
  `PlantRenderer.Bake.cs` / `BakeQueue`, et toute autre création de texture/maillage que
  tu trouves au cran), surface en pixels cuite dans l'image. Colonnes au rapport Z.
- Balayage VM `-Z 4 -S 1521550718 -w 90 -c 1650,950` [n=1] : sur llvmpipe le coût d'un
  envoi n'est pas celui du PC, mais les **volumes** (Mo envoyés, textures créées par
  image au cran) sont transposables — c'est eux qu'on regarde.

## (b) Agir sur ce que la mesure montre
Exemples (à choisir selon la mesure, un seul ou deux, pas tout) : plafonner le volume
de cuisson envoyé par image aux hauts paliers (budget en pixels, pas seulement en ms) ;
ne pas recréer une texture de taille identique (réutiliser / `Update`) ; garder la cuisson
du palier précédent plus longtemps. Si la mesure n'explique pas le non-attribué, ne
force pas un levier : consigne le constat et la prochaine hypothèse dans `00_etat.md`
et en note D116.

## Ne PAS faire
Changer le LOD visuel (DA, D112 m) ; toucher `data/code/` ; retirer des colonnes
existantes du rapport Z.

## Fin de tronçon
`00_etat.md` §③ (mesure, levier, avant/après balayage VM), commit. F5 au ④ : touche Z
après un aller-retour ×0,5 → ×32 → ×0,5.
