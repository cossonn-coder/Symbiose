# ⑥ Vue Godot : revue « beau à chaque palier » et section F5

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (tous les comptes rendus ①→⑤), la conception.

## Objectif
Dernier tronçon (règle « vue Godot toujours en dernier ») : vérifier, image par image, que
les herbacées sont **belles et homogènes à chaque palier, de ×0,5 à ×32**, et corriger les
finitions. On ne crée pas de nouvelle recette ici : un manque important devient un point
pour S2/S3 ou un candidat dette.

## À faire
1. **Échantillon** couvrant tous les ports (rosette, tige, chaume, tapis, buisson, rampante,
   volubile), toutes les marques et les recettes nouvelles du ④. Au minimum : tomate,
   tournesol, fraisier, courgette, carotte, trèfle, plantain, blé, thym, lavande, lierre,
   haricot, drosera, bourrache, myrtille. Par espèce : `tools/capture_vm.sh -b planche_especes
   -l <SEC> -c <x,y>` (positions dans `data/code/bancs/planche_especes.py`, `POSITIONS`),
   avant (`SYMBIOSE_SPLATS=0`) et après.
2. **Lire chaque planche au Read**. Chercher : bascules laides entre paliers (taille,
   détail qui apparaît ou disparaît), restes dessinés, pièces vides, teinte cassée, retour
   au dessin direct à ×32, et monde `full` à ×1 (ensemble).
3. **Finitions** : seuils de palier des couches, choix de classe de taille, petites
   corrections de crochet. Chaque correction donne une capture avant/après.
4. **Mémoire** : au monde `full` et sur `planche_especes`, relever la mémoire de
   précuisson par palier contre le budget de 1 Go (① ), et les ms par image.
5. **Section F5** de `00_etat.md` : liste précise de ce que Nico vérifiera au F5 complet
   (après S3), espèce par espèce et palier par palier. Elle alimentera la liste exhaustive
   de S3.
6. **Clôture du sprint** (si l'orchestrateur ne le fait pas) :
   - `journal/NN_…` et sa ligne dans `journal.md` ;
   - `docs/rendu/splatting/backlog_splatting.md` : S1 clos, S2 « à concevoir » ;
   - `BACKLOG.md` et `DETTE.md` si un candidat dette est retenu.

## Ne pas faire
- Toucher les arbres, le bois ou les brins de graminées (S2).
- Toucher `data/code/`.
- Lancer `test_epaisseur_500ans`, appeler DeepSeek.

## Fin
Build vert, golden `bce813af…` intact, LDC (refactor auto-léger si un fichier dépasse la
bande). Message pour Nico : S1 clos, prochaine étape `/conception` de S2 (arbres).
