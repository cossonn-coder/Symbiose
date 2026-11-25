# ③ Rubans des graminées et petit bois — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md` (comptes rendus ①②), `docs/rendu/splatting/conception_bois_arbres.md`
(C2, §3.4).
Golden attendu : **`bce813af…` INTACT**. Build vert, 0 avertissement.

## Objectif
1. Les **brins et rubans des graminées** (dernier reste dessiné des herbacées, E9 de S1) passent
   par le ruban texturé de ①/② : bande cuite de limbe de graminée (nervures parallèles, cœur plus
   clair, bord), plaquée sur la géométrie que la vue calcule déjà — le vent plie toujours le brin.
2. Le **petit bois dérivé** des arbres (rameaux, brindilles : `DrawPetitBois`,
   `PlantRenderer.Houppier.cs:57`, `BoisDuHouppier`) devient un tube avec l'écorce « rameau » de
   son essence, accroché à la courbe de son porteur (géométrie unique de ①).

## À faire
- Crochets : `PoserBrin` (`PlantRenderer.Graminees.cs:44` — calcule déjà bords gauche/droit par
  point, il manque u/v), `PoserRubans` (`PlantRenderer.PortChaume.cs:105`), dactyle, fétuque, et
  tout autre appelant de `PoserBrin` (grep). Lot de triangles `_lotPrairie` : vérifier que la
  texture passe (sinon un lot texturé dédié).
- Recette(s) splat de bande de graminée (largeurs de la vue : `RubanCm` des fiches, brins du
  dactyle/fétuque) ; tons d'espèce, de saison (paille) et de santé gardés par la palette.
- Ancien dessin intact derrière l'interrupteur.

## Mesures
- `planche_especes` (blé, seigle, dactyle, fétuque, pâturin) ×2/×8/×16/×32 avant/après, AVEC vent
  (`-v`) : le brin ploie toujours. `houppiers` ×8/×16 : petit bois.
- Poids `assets/splats/`. Captures `mesures/03_*`.

## Ne PAS faire
- Remplacer la géométrie du brin par une pièce fixe (la prairie ne ploierait plus — constat du (a) ④bis).
- `data/code/`, `test_epaisseur_500ans`, DeepSeek.

## Fin
`00_etat.md`, commit.
