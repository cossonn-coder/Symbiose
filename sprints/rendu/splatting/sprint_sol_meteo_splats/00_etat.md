# sprint_sol_meteo_splats — état (famille (e) du programme splats + POC ×64)

**Conception FIGÉE le 2026-11-26** (`/conception`, Nico : lot 1 arbitré puis « carte blanche ») →
`docs/rendu/splatting/conception_sol_meteo_splats.md` (LIRE §1 constat, §2 décisions E1-E8, §3 modèle).
Golden attendu : **`bce813af…` INTACT à chaque tronçon** (vue + outillage ; `data/code/`, pont
`data/code/tools/simserver` compris, jamais modifié → aucune donnée neuve au snapshot).
Contexte : `backlog_splatting.md` ; méthode `conception_precuisson_splats.md` ; règle pixel natif par
palier = L2 de `conception_lisiere_chargement.md` ; faits mesurés S3 dans
`sprints/rendu/splatting/sprint_lisiere_chargement/00_etat.md` (atlas ×32 lisière 100,8 Mo, à-coup ×32).

## Faits vérifiés au code (2026-11-26)
- Caméra `Camera2D`, paliers `ZoomSteps = {0,5 1 2 4 8 16 32}` (`world/WorldView.Camera.cs:22`), rendu
  `gl_compatibility`. Plot = losange 39×19,5 px canvas à ×1 (`WorldView.Projection.cs:32`).
- Sol : `world/SolTexture.cs` (losange 39×20 par type × orientation, 3 types terre/argile/sable,
  `WorldView.Monde.cs:113`), `SolMaillage` (1 maille par tuile), `SolMateriau` (shader 2 lignes).
- Couches au sol en couleurs littérales : `visuals/CouvertureLayer`, `LitterLayer`, `LeafLitterLayer`,
  `StrawLitterLayer`, `DeadWoodLayer`, `MulchLayer`+`MulchMotifs`, `PuddleLayer`(+`.Eau`/`.Mare`/`.Signaux`),
  `SnowLayer`, `TracesSolLayer`+`TracesSolMotifs` ; montage dans `world/WorldView.SolCanvas.cs`, `.Paillage.cs`…
- Météo : `visuals/WeatherLayer.cs` (CanvasLayer), `EclaboussuresLayer`, `LeafFallLayer`, `MeteoPlantes`.
- Données snapshot : `couverture`, `litiere`, `paillage`, `eau_surface`, `marais`, `sol_sec` (< 0,5 seul),
  `traces_sol`, `temperature[tile].snow` (scalaire/tuile), `weather`.
- Écorce : `EcorceReductionMax` = 2 (`visuals/DecorLayer.Charpente.cs:42`), `EcorceMinPx` (`PlantRenderer.Ecorce.cs:27`) ;
  bandes cuites ×4-×32 par `tools/splat/cuire_ecorces.js`.
- Plafonds `PlantBaker` : `MaxSidePx` = `MaxAtlasPx` = 16384 ; `BudgetCuisson` 1 Go.
- Outil : `tools/splat/cuire.js` (`--paliers`, `boites`, `--echelles`), `cuire_ecorces.js` (bandes périodiques,
  couture mesurée, parallèle `--liste | xargs -P`). Banc capture VM : `tools/capture_vm.sh`.

## Décisions (détail dans la conception §2)
E1 tapis pavable + kit d'objets épars + eau au shader · E2 météo cuite, taille par palier plafonnée ×8 ·
E3 écorce sous ×4 jointe · E4 POC chanvre ×64 en ⑧ · E5 une géométrie / plusieurs palettes · E6 seuil
par hauteur · E7 jamais réduire une cuisson fine · E8 interrupteur Maj+F11 / `SYMBIOSE_SPLATS=0`.

## Tronçons (golden `bce813af…` intact partout)
| # | Kickoff | État |
|---|---|---|
| ① | `01_atelier_materiaux.md` — tore iso, variantes, couture (porte de décision) | à faire |
| ② | `02_bibliotheque_materiaux.md` — ~10 géométries × 7 paliers | à faire |
| ③ | `03_tapis_sol.md` — shader du tapis + carte des champs | à faire |
| ④ | `04_eau_sec.md` — flaques, marais, mare, craquelé, éclaboussures au sol | à faire |
| ⑤ | `05_objets_epars.md` — feuilles, tiges, bois mort, traces | à faire |
| ⑥ | `06_meteo.md` — pluie, grêle, neige, couronnes, feuilles en chute | à faire |
| ⑦ | `07_ecorce_bas.md` — bandes ×0,5/×1/×2 | à faire |
| ⑧ | `08_poc_x64.md` — chanvre ×64 sur son sol, capture + mesures | à faire |
| ⑨ | `09_revue_f5.md` — revue, liste F5 (e), clôture | à faire |
Ordre : ①→②→③→④ ; ⑤⑥⑦ après ① ; ⑧ après ②③ ; ⑨ en dernier.

## Comptes rendus
(à remplir par chaque tronçon : fait, écarts au kickoff, mesures avec leurs limites entre crochets, F5)

## §REPRISE
Sprint prêt pour `/sprint-auto sprint_sol_meteo_splats`. Prochain : ①.
