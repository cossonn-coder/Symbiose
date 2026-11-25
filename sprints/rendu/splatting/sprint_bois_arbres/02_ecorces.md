# ② Écorces cuites — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md` (compte rendu ①), `docs/rendu/splatting/conception_bois_arbres.md`
(B2, C3, §3.3), `tools/splat/README.md`.
Golden attendu : **`bce813af…` INTACT**. Build vert, 0 avertissement.

## Objectif
Le tube de ① reçoit une **écorce cuite en splats par essence × 3 âges**, plaquée en continu le long
de l'arc, sans couture, éclairée par le soleil réel comme le reste (palette indexée).

## À faire
1. **Maquette C3 d'abord** (mesurée, une essence, ×8/×16/×32) : un pixel est un CODE
   (`PaletteIndexee.cs` : B = 128 | ton << 4 | orientation ; palette via `ModulatePiece`). L'écorce
   cuite porte les TONS ; l'orientation vient de la géométrie du tube. Comparer :
   (a) un petit shader canvas dans le pinceau qui compose le code (ton de la texture + orientation
   calculée du tube) ; (b) des variantes de bande cuites par rotation de 45° et choisies par
   morceau. Retenir sur image + coût ; consigner le choix et pourquoi.
   Vérifier que le pinceau cuit (`PlantBaker`, SubViewport) ET le repli (dessin direct) donnent le
   même rendu.
2. **Recette** `tools/splat/recettes/ecorce.js` (ou nom voisin) : cylindre sculpté PÉRIODIQUE en
   longueur (motif au hash avec période) — la coupure du haut rejoint celle du bas à l'octet près ;
   photographié de face → bande. Partir de `recettes/bois.js` (fissures en solides négatifs,
   lenticelles) et de `couture_bois.js` (la mesure de couture). **12 essences** (`RecettesArbres`,
   `PlantRenderer.Arbres.cs:29`, caractères listés en conception §3.3) × **3 âges** (rameau lisse /
   branche / tronc à rhytidome ; bouleau : blanc à lenticelles, base noire crevassée).
   Format, paliers, résolution en cm/px : à fixer sur la maquette ; le motif doit se lire à son
   échelle réelle (v en cm).
3. **Vue** : plaquage le long du ruban de ① (v = arc en cm ; u en travers). Âge par épaisseur
   (seuils dans la continuité de `EcorcePleineCm`), FONDU sur quelques cm entre deux âges, jamais de
   marche. Couleur = `Ecorce` de la fiche, comme aujourd'hui (`AvecEcorce`). Plante sans essence
   (générique, squelette) : écorce générique (une bande neutre), le squelette garde son bois mort.
4. Neige, givre, symptômes, surbrillance : toujours lisibles par-dessus.
5. Contrôle : planche des 36 bandes (`mesures/controle_ecorces.png`) + mesure de couture le long d'un
   axe (extension de `couture_bois.js` : la jonction v = période doit être invisible).

## Mesures
- Avant/après `houppiers` ×8/×16/×32 sur les 12 essences ; `verger_floraison` planche.
- Temps de cuisson des bandes ; poids `assets/splats/` (65 Mo au départ ; alerte 200 Mo).
- Déterminisme : 2 cuissons = mêmes octets.
- Captures `mesures/02_*`.

## Ne PAS faire
- `data/code/`, `tools/splat/vendor/`, `test_epaisseur_500ans`, DeepSeek.
- Poser des tronçons cuits bout à bout (couture prouvée au sprint (a) ③).

## Fin
`00_etat.md` (choix C3 + mesures), commit.
