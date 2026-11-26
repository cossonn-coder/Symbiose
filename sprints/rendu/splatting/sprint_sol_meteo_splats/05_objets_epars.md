# ⑤ Vue : objets épars au sol en pièces splat — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md`, conception §3.3, `visuals/PlantRenderer.KitSplats.cs`
(patron d'adaptateur), `visuals/SplatPlanches.cs`, `visuals/LeafLitterLayer.cs`, `StrawLitterLayer.cs`,
`DeadWoodLayer.cs`, `TracesSolLayer.cs` + `TracesSolMotifs.cs`, `visuals/LotTriangles.cs`.
Golden attendu : **`bce813af…` INTACT**. Build vert, 0 avertissement.

## Objectif
Les objets qui portent une information propre gardent leur couche et leur logique (semis au hash,
masse, âge, grosseur) ; seule leur **image** devient une pièce splat cuite au palier, en palette indexée.

## À faire
1. Pièces : feuille morte à plat (réutiliser les recettes de feuilles en palette morte ; espèce non
   traçable → forme par défaut, comme aujourd'hui), tige couchée (limbes/tiges existants), bois mort
   (brindille, branche avec bande d'écorce, souche = recette neuve), traces de gestes (empreinte,
   sillon, motte retournée… = ce que `TracesSolMotifs` dessine). Cuites aux paliers où l'objet se lit.
2. Adaptateur par couche sur le patron `KitSplats` ; stade (fraîche → grise → moussue → fragments) =
   palette ; pièce absente → ancien dessin + avertissement.
3. Les objets passent par la palette indexée (soleil réel) ; un lot par couche (pas de draw call en plus).

## Mesures
Captures ×1/×4/×16/×32 avant/après (automne sous un arbre, potager fané, tas de bois, traces de gestes) ;
`mesures/05_*`. Temps de cuisson, Mo git, draw calls.

## Ne PAS faire
Changer quand/combien un objet apparaît (c'est le snapshot). `data/code/`, `test_epaisseur_500ans`, DeepSeek.

## Fin
`00_etat.md`, commit `feat(tapis⑤) : …`.
