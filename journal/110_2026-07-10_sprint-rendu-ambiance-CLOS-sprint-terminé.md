# 2026-07-10 — Sprint RENDU AMBIANCE (D58, T1→T6) — SPRINT TERMINÉ

`/sprint-auto sprint_rendu_ambiance`. Rendre le monde attractif au-delà des
plantes. **6 tronçons, golden préservé partout** — T1 moteur NEUTRE, T2→T6 vue
pure (couche B), aucun re-figeage. **Golden final INCHANGÉ**
`24ec11e7983595e71c4587fce8f558a1bec9eb5ec8511bf69ad76e9fdc2b6e91`,
`dotnet build` vert partout.

## Tronçons
- **T1 — Essences forestières** [moteur, NEUTRE] : 3 `PerennialWoody` (gabarit
  `OakTree`) — `BeechTree` (Hêtre, Fagaceae), `BirchTree` (Bouleau, Betulaceae
  NEUVE), `HornbeamTree` (Charme) dans `plants/perennials.py` + inscription
  `PERENNIAL_CATALOGUE`, encyclopédie 3 niveaux chacune, magazine data-driven
  (familles dérivées du catalogue → offre auto). Golden NEUTRE (hash inchangé).
- **T2 — Fleurs par famille** [vue] : `visuals/PlantRenderer.Flower.cs`, `enum
  FlowerShape` (Simple/Ombelle/Capitule/Papilionacee/Epi/Clochette) + table
  `FlowerProfiles[species]`, tracé volumé E4, jitter par hash, LOD (repli Simple
  au dézoom). Couleur inchangée. Ancien `DrawFlower` 5 pétales → `DrawSimple`.
- **T3 — Maison normande** [vue] : `visuals/HouseNode.cs` (granite+ardoise du
  Cotentin) — moellons 2-3 valeurs + variété rousse, joints chaux, chaînages,
  encadrements à larmier, pignon ouest essenté d'ardoise, toit 2 pans + croupe,
  lucarne à bâtière sud, souche brique orangée (pas de fumée = D72). Extraction
  `world/WorldView.Maison.cs`. Palette16 étendu.
- **T4 — Décor ossature** [vue] : `visuals/DecorLayer.cs` — `SurroundingsProfile`
  (couture d'extensibilité par seed), 4 secteurs cardinaux à frontières sinueuses
  (bruit 3-sinus, zéro Random), rivière↔falaise couplées. ZIndex −5, hors picking,
  statique. Chemins enherbés (`FondPierre`→`GazonChemin`).
- **T5 — Décor motifs** [vue] : `visuals/DecorLayer.Arbres.cs` — `enum TreePort`
  (Etale/Ovoide/Elance/Sinueux/Conique) + `Silhouettes[species]` (clé nom
  d'espèce, contrat T1), forêt en scatter gradient lisière→profond (bouleaux
  clairsemés au bord → chêne/hêtre denses au fond), houppier = amas d'ellipses
  volumées, tri peintre par Y. Rivière (reflets dithering), falaise (redans par
  pente), prairie fleurie. Statique, cullé.
- **T6 — Feuilles fidèles au modèle réel** [vue, indépendant] :
  `visuals/PlantRenderer.LeafOutline.cs` — contour authoré par espèce (table
  `LeafOutlines`, **37 espèces feuillues** — le catalogue en compte plus que les
  ~27 annoncés, couverture complète), descripteur `OutlineSpec` (marge
  entière/dentée/lobée, effilement, échancrure basale, composée pennée), tracé
  volumé `DrawVolumePolygon` + folioles + nervures. Dispatch LOD dans `Leaf.cs` :
  ×16+ contour fidèle (repli archétype si non mappé), [4,16[ amas d'ellipses
  inchangé, <4 tache.

## Décisions imprévues (tranchées dans le périmètre)
- **T5** : arbres du décor dessinés en px écran (base via `WorldToScreen`,
  hauteur via `PxPerCmZ`), cohérent `PlantRenderer` ; `DrawVolumeBlob` répliqué
  en static local (le volume de `PlantRenderer` est instance-private).
- **T6** : contours **synthétisés depuis un descripteur par espèce** (authoring
  maintenable, F5-éditable) plutôt que listes de coordonnées brutes ; 37 espèces
  mappées (couverture > les ~27 annoncés). Repli sprite pré-cuit non activé.

## Reste F5 Nico
- Fleurs par famille reconnaissables ; maison granite/ardoise crédible en
  rotation (lucarne sud propre) ; forêt lisière→profondeur, rivière qui reflète,
  falaise à pente crédible, prairie fleurie, fluidité à ×1 ; feuille reconnaissable
  par espèce au zoom ×16/×32 + bascule LOD au dézoom.
- Repli « cuire la forêt en texture » non activé (à décider si trop lourd).

## Clôture
- **Deux commits** : `2714088` (T4+T5 décor, regroupé sur décision Nico — T4
  était non committé d'une exécution antérieure), `cddfd95` (T6 feuilles).
  T1/T2/T3 déjà committés (`b8b655d`/`c3f649f`/`e9d49af`).
- Refactor auto-léger **no-op** : tous les fichiers touchés ≤ 240 LDC pur 🟢.
- **D58 → 🟢 ✅ FAIT.** Dettes ouvertes en parallèle : **D72 vent** (perf-first,
  à concevoir), **D73 terraforming** (moteur, à concevoir).
