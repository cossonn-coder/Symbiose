# ② Arbres de lisière sur le bois de S2 + sapin du jardin ×8-×32 — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md` (compte rendu ①), `docs/rendu/splatting/conception_lisiere_chargement.md`
(L1, L4, §3.2), `docs/rendu/splatting/conception_bois_arbres.md` (C2, C3, C4),
`visuals/RubanTexture.cs`, `visuals/BandesCuites.cs`.
Golden attendu : **`bce813af…` INTACT**. Build vert, 0 avertissement.

## Objectif
1. Les arbres de la lisière gardent leur architecture (ombre → tronc → charpentières → enveloppe →
   bouquets, `DecorLayer.Houppiers.cs`, `.Branches.cs`) mais leur **charpente** devient un ruban
   lissé (`RubanTexture`) avec l'**écorce cuite de S2** de leur essence (8 essences de
   `DecorLayer.Arbres.cs` : chêne, hêtre, bouleau, charme, sapin, noyer, aulne, saule), un **pied
   évasé**, et le **sapin en étages** (rameaux de plus en plus courts vers le haut). Bouquets = pièces
   splat du ①.
2. Le **sapin du jardin** pose ses aiguilles ×8-×32 en rameaux aplatis (recette du ①) — reste de S2
   (`sprint_bois_arbres/00_etat.md`, « Restes connus »). Crochet côté `PlantRenderer` (rameaux du
   sapin, `RecettesRameaux["FirTree"]`, `PlantRenderer.Rameaux.cs`) : à localiser au code.

## Contraintes
- La lisière reste **UN envoi** : les bandes d'écorce des 8 essences sont recopiées dans l'atlas du
  décor (UV du ruban dans cette bande). Vérifier au code comment `RubanTexture` produit ses
  triangles (`Verser` dans un lot ?) et comment le lot du décor (`LotTriangles`, encodeur de sommets
  `DecorLayer.Indexe.cs`) les accepte ; si impossible proprement, 2 envois au plus, signalé.
- Saison pied par pied, neige, givre, vent : la charpente garde sa classe shader actuelle
  (`ClasseSansSaison`, cf. `DecorLayer.Branches.cs`) et reste dans l'ellipse de l'enveloppe.
- Déterminisme : formes au hash de `SeedSecteur`, zéro `Random`.

## Mesures
- Capture `full`, motif forêt (et ripisylve si un secteur rivière a aulne/saule), ×1/×2/×4, été et
  hiver nu, avant/après. Sapin du jardin : `houppiers` ×8/×16/×32 (`-l`). `mesures/02_*`.
- Construction de maille par palier avant/après (référence 30-37 ms [VM] ; alerte à +50 %),
  draw calls de la lisière.

## Ne PAS faire
- Imposteurs d'arbres entiers (rejeté, L1). Changer la densité ou le placement des arbres.
- `data/code/`, `test_epaisseur_500ans`, DeepSeek, `tools/splat/vendor/`.

## Fin
`00_etat.md`, commit `feat(lisiere②) : …`.
