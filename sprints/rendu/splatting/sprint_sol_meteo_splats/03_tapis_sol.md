# ③ Vue : le tapis du sol — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md` (①②), conception §3.2 + E6-E8,
`world/SolMaillage.cs`, `world/SolMateriau.cs`, `world/SolTexture.cs`, `world/WorldView.Monde.cs`,
`world/WorldView.Relief.cs`, `visuals/PaletteIndexee.cs` + `palette_indexee.gdshader` (codes, LUT, soleil),
`visuals/DecorLayer.Hauts.cs` (permutation d'atlas par palier, construction hors fil principal),
`visuals/BudgetCuisson.cs`, et les couches remplacées : `CouvertureLayer`, `LitterLayer`, `MulchLayer`,
`SnowLayer` (+ `world/WorldView.Tapis.cs`, `WorldView.Paillage.cs`).
Golden attendu : **`bce813af…` INTACT**. Build vert, 0 avertissement.

## Objectif
Le dessus des plots devient un **tapis de matériaux** au pixel natif de chaque palier, mêlés par une
**carte des champs** et un **seuil par hauteur** ; terre, tapis vert, litière fine, paillis et neige sont
peints par le sol lui-même (eau, marais, craquelé = ④).

## Modèle (intention ; le placement exact est à toi, vérifié au code)
- **Carte des champs par tuile** : 1 texel par plot, réécrite uniquement quand le bloc du snapshot change
  (jamais par image — mémoire « pas de recalcul dans un tick »). Quantités en filtré (bords organiques),
  catégories au plus proche (type de sol, nature du paillis, n° de palette du tapis vert = teinte de
  l'espèce dominante comme `CouvertureLayer` la calcule, agrégat des petites plantes compris).
  `snow` est un scalaire par tuile : uniform ou canal constant.
- **Shader du tapis** (fichier `.gdshader` propre) : UV du matériau dérivées des coordonnées MONDE (le grain
  reste attaché au sol quand la vue pivote, D35), texel = pixel écran au palier courant ; variante au hash
  de la cellule ; couches bas → haut : terre (palette du type de sol) → tapis vert → litière fine → paillis
  → neige ; une couche paraît là où `quantité > 1 − hauteur(ton) du dessous` ; sortie = code indexé →
  même LUT et même soleil réel que les plantes.
- Matériaux du palier courant seulement en mémoire, comptés dans `BudgetCuisson` ; permutation au
  changement de palier hors fil principal (patron `DecorLayer.Hauts.cs`), repli = palier voisin en attendant.
- Flancs du micro-relief : matériau flanc.
- **Interrupteur** Maj+F11 / `SYMBIOSE_SPLATS=0` : ancien `SolTexture` + anciennes couches, intacts.
  Les couches fusionnées ne dessinent plus quand le tapis est actif (leurs données restent lues :
  picking, info-bulle, hystérésis).

## Mesures
- Banc capture (`tools/capture_vm.sh`, monde `full`) ×0,5 → ×32 avant (`SYMBIOSE_SPLATS=0`) / après :
  sol nu, tapis vert, litière, chaque nature de paillis, neige ; 4 saisons ; rotation D35 (`-r`). `mesures/03_*`.
- ms de réécriture d'une carte, ms par image, draw calls avant/après, Mo des matériaux résidents
  [VM llvmpipe : volumes seuls transposables].
- Chaque signe d'avant reste lisible (philo #5) : le dire capture par capture.

## Ne PAS faire
Eau, marais, mare, craquelé, éclaboussures (④). Données neuves au pont. `data/code/`,
`test_epaisseur_500ans`, DeepSeek, `vendor/`. Grossir `WorldView.cs` (partials neufs ≤ 300 LDC).

## F5
Bords organiques entre sol nu et tapis ; nature du paillis reconnaissable à ×1 ; neige mince dans les
creux ; soleil qui tourne sur le grain ; à-coup au changement de palier.

## Fin
`00_etat.md`, commit `feat(tapis③) : …`.
