# ⑥ Vue : météo en pièces cuites — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md`, conception §3.4 + E2, `visuals/WeatherLayer.cs`,
`visuals/EclaboussuresLayer.cs`, `visuals/LeafFallLayer.cs`, `visuals/MeteoPlantes.cs`,
`visuals/PlancheAnimations.cs` (poses), `tools/splat/cuire.js`.
Golden attendu : **`bce813af…` INTACT**. Build vert, 0 avertissement.

## Objectif
Pluie, grêle, neige qui tombe et éclaboussures en **pièces splat cuites**, à leur taille réelle au palier,
**plafonnée à ×8** (au-delà, la taille ×8 sert).

## À faire
1. Recettes : goutte-strie (3 inclinaisons : vent faible/moyen/fort), flocon (4 poses qui tournoient),
   grêlon (bille + reflet), couronne d'éclaboussure (4 poses). Cuites ×0,5 → ×8.
2. `WeatherLayer` reste « vitre » (CanvasLayer) ; il choisit la taille par le palier courant et dessine
   les pièces en un lot ; mouvement = fonction du temps au hash (inchangé), nombre borné (inchangé).
3. `EclaboussuresLayer` : couronne en 4 poses ; `LeafFallLayer` : pièces de feuille de ⑤ (si ⑤ n'est pas
   fait, garder l'ancien dessin et le noter).
4. Flash d'orage, stries de vent, nébulosité, brume : inchangés.
5. Interrupteur Maj+F11 : ancien dessin.

## Mesures
Captures (bancs avec pluie, orage, grêle, neige) ×0,5/×2/×8/×32 ; `mesures/06_*` ; ms par image en averse.

## Ne PAS faire
Changer la météo ou sa fréquence. `data/code/`, `test_epaisseur_500ans`, DeepSeek.

## F5
Pluie lisible sans masquer le jardin à ×32 ; flocons qui tournoient ; grêle distincte de la pluie.

## Fin
`00_etat.md`, commit `feat(tapis⑥) : …`.
