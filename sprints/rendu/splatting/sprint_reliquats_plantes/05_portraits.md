# ⑤ Portraits ratés (hors arbres)

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (comptes rendus ②③④), la conception, et dans
`../sprint_precuisson_splats/00_etat.md` le compte rendu ⑥ (outil `tools/splat/cuire_portraits.js`
+ `tools/splat/portraits/`, liste « Ratés ou faibles ») et ⑦ (`portraits.json`, clé `cle`).

## Objectif
Refaire les portraits ratés des **herbacées, buissons et lianes**, avec les recettes et
couches définitives (②③④). Les arbres (sapin, bouleau, cerisier, figuier) vont en S2.

## À reprendre (constats du ⑥)
- **Tournesol** : tête minuscule (bornage de l'échelle des têtes [0,5 ; 2]).
- **Thym** : bois bas nus et feuilles qui flottent ; il faut un coussinet (recette ④).
- **Molène** : rosette correcte, mais il manque la grande hampe jaune.
- **Drosera** : rosette verte générique ; il faut du rouge, des tentacules et des gouttes
  (couche ③). Disque de sol énorme au stade jeune.
- **Chanvre** : tige unique clairsemée, pas de feuilles palmées (`feuille_palmee` existe).
- **Lavande** : les cannes brunes dominent.
- **Haricot, jasmin, lierre** : tuteur brun trop présent (l'atténuer) ; jasmin « fin » =
  tige nue.
- **Myrtille** : pas de baies. Cause : pas de `Fruit` dans **sa fiche de vue**
  (`visuals/PlantRenderer.PortsFiches.cs:185`), donc les baies manquent **aussi en jeu**.
  Vérifier au moteur que l'espèce est fruitière (`data/code/plants/`, lecture seule), puis
  ajouter le fruit à la fiche de vue. C'est une modification de la vue, golden intact.
  Capture en jeu avant/après.
- **Framboisier** : garde ses feuilles l'hiver parce que le moteur le dit persistant. Ne
  rien changer au moteur ; le noter comme candidat dette dans le compte rendu (le
  framboisier réel perd ses feuilles).

Les autres portraits se recuisent tels quels s'ils profitent des recettes nouvelles (le
trèfle en particulier). **Recuisson complète** des 156 portraits si l'outil le permet en
temps raisonnable (18 min au ⑥), pour l'homogénéité ; contrôle de déterminisme.

## Mesures attendues
Planches `mesures/controle_portraits_*.png` relues au Read, espèce par espèce. Poids.
Capture `capture_vm.sh -Z encyclo:<clé>` sur 2-3 espèces refaites.

## Ne pas faire
- Les arbres (S2).
- Toucher `data/code/` (lecture seule).
- Lancer `test_epaisseur_500ans`, appeler DeepSeek.

## Fin
Build vert si du C# a été touché, golden intact, LDC. Compte rendu ⑤ : refaits, encore
faibles, candidat dette framboisier.
