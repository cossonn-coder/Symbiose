# ③ Tous les détails des feuilles et organes, cuits

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (compte rendu ② : tailles), la conception, et
dans `../sprint_precuisson_splats/00_etat.md` les comptes rendus ③ (COUCHES : une pièce par
couche et par vue, une palette par couche) et ④ (défaut 3 : marques non posées sur une
feuille-pièce).

## Objectif
Consigne de Nico (E10) : **« tous les détails des feuilles doivent être présents quand on
zoome, que ce soit beau à chaque niveau de zoom »**. Aujourd'hui, quand une feuille ou un
organe devient une pièce splat, ses détails vectoriels disparaissent.

## À faire
1. **Inventaire exhaustif, au grep** (pas de DeepSeek), de tout détail vectoriel posé sur
   une feuille ou un organe, avec son palier d'apparition. Au minimum :
   - les marques de fiche `MarqueFeuille` (`PlantRenderer.PortsFiches.cs:22` : Duvet,
     Gouttes, Eclat, Revers, Nervures ; Pli et Gaufre sont déjà cuits en relief) ;
   - les surfaces `Surface` (Poils, Pruine, Glandes, `PlantRenderer.PaliersHauts.cs:218`) ;
   - les nervures ×16 et nervures secondaires ×32 ;
   - les étamines ×32 ;
   - la pruine des fruits ×32.

   Chercher aussi dans les `Port*.cs`, `Prairie.cs`, `Flower.cs`, `FleurSnes.cs`, `Organs.cs`.
   Le tableau (détail → espèces → palier → fichier:ligne) va dans le compte rendu.
2. **Cuire chaque détail en COUCHE** (mécanisme `couches` de `cuire.js`, palette propre
   posée à l'assemblage), sur les recettes que portent les espèces concernées, aux 3 tailles
   du ②. Exemples d'intention :
   - duvet = poils fins splat sur le limbe ;
   - nervures pâles = couche de nervures ;
   - gouttes du drosera = perles au bout des poils ;
   - revers argenté = couche des faces tournées vers le bas ;
   - éclat = reflet clair ;
   - étamines = couche de la corolle ;
   - pruine = voile clair du fruit.

   Les détails de **couleur** de santé (nécrose, taches, givre) restent peints par-dessus
   (D5 du sprint (a)).
3. **Vue** : poser chaque couche à partir du palier où elle se lit, avec un seuil par
   détail dans une table unique, déterminé en regardant les planches de contrôle. Le but :
   aucun palier où un détail « saute » laidement, et aucun palier surchargé. L'ancien dessin
   vectoriel des détails ne s'applique plus sur une pièce.
4. **Sonde ×64** (hors affichage, décision de Nico) : cuire `feuille_composee` avec sa
   couche de duvet à ×64. Mesurer le temps par pièce, le poids de la planche et la taille en
   px, et produire une planche de contrôle `mesures/sonde_x64.png`. Les splats se voient-ils
   un par un ? Aucun branchement dans la vue. Ces chiffres serviront au proof of concept
   « chanvre ×64 » prévu après S3.

## Mesures attendues
Poids (alerte 200 Mo), temps de cuisson, et captures ×8/×16/×32 avant/après sur :
bourrache ou consoude (poils), lierre (nervures pâles), drosera (gouttes), armoise
(revers), ail (pruine), une fleur (étamines), tomate (poils glanduleux).

## Ne pas faire
- Créer de nouvelles recettes d'organe (c'est ④).
- Toucher `data/code/` ou `vendor/`.
- Lancer `test_epaisseur_500ans`, appeler DeepSeek.

## Fin
Build vert, golden intact, LDC. Compte rendu ③ avec le tableau d'inventaire et les seuils
par détail. Point F5 : chaque détail apparaît-il au bon zoom ?
