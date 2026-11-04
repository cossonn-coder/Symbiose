# Sprint FORMES DES PLANTES (reste de D118 (A)) — état

**Conception figée le 2026-11-04** : `docs/rendu/pixelart/conception_formes_plantes.md`. 6 tronçons, à exécuter par `/sprint-auto sprint_formes_plantes`.

## Décisions clés

1. 33 espèces : port dessiné par la vue (7 ports + fiche), sans dessiner leurs segments. Tomate, lierre, jasmin gardent leurs segments.
2. Taille : clic sur la plante, coupe visible par hints du pont (`rabattu`, `pince`). Arbres, tomate, lierre, jasmin gardent le segment.
3. Formes seules ; le reste demeure dans D118 réduite.
4. Plus de squelette pour les herbacées à port, après les ports (conception §4.6).

Golden attendu : **inchangé partout**, `a10b7225…` à l'ouverture. Vérifié par patch mémoire pour les segments et pour leur retrait [smoke], à revérifier au ② pour les hints et au ⑤ pour le retrait. Tout écart est une anomalie à remonter, pas un re-figeage.

## Carte des tronçons

| # | Kickoff | Contenu | État |
|---|---|---|---|
| ① | `01_banc_fiches.md` | Banc, mesure des silhouettes, « avant », 36 fiches | **fait, code non committé** |
| ② | `02_socle_rosettes.md` | Socle des ports, taille, rosettes (7) | **fait, code non committé** |
| ③ | `03_tiges.md` | Tiges à feuilles étagées (12) | **fait, code non committé** |
| ④ | `04_chaumes_tapis_buissons.md` | Chaumes, couvre-sols, buissons, courgette (13) | à faire |
| ⑤ | `05_squelette_moteur.md` | Plus de squelette pour les herbacées à port, perf | à faire |
| ⑥ | `06_grimpantes_grammaire_bilan.md` | Haricot, tomate, lierre, jasmin, fleurs et feuilles SNES, bilan | à faire |

## Garde-fous

- Ne JAMAIS lancer `tests/test_epaisseur_500ans.py`. Mesures ≤ 3 ans de jeu.
- Déjà rouges avant ce sprint : `test_succession`, `test_edaphique`, `test_parasite`.
- Vérifier la charge VM (`uptime`) avant toute mesure de temps. Chaque chiffre porte sa limite entre crochets.
- `PlantRenderer.Prairie.cs` (301 LDC) et `PlantRenderer.Organs.cs` (292) ne doivent pas grossir : code neuf dans des partials neufs.

## Bilans

(rempli par chaque tronçon : ce qui est fait, mesures, écarts, ce que le suivant doit savoir)

### ① Banc, mesure, fiches

- **Fait** : `bancs/planche_especes.py` (+ registre, s20, `POSITIONS`), `tests/bancs/test_planche_especes.py`, `tools/mesure_silhouettes.py`, `mesures/avant.md`, `docs/vegetal/croissance/fiches_herbacees.md`. Golden intact `a10b7225…`. Rendu et catalogue non touchés.
- **Mesure avant** : 34 espèces sur 40 dessinées à 88-91 cm à ×4, quelle que soit `height_cm` ; 28 paires confondues à ×4, 14 à ×1 ; hauteur hors tolérance 30 sur 40 à ×4, 28 à ×1 [seed 42, n=1 capture, VM]. La mesure concorde avec l'œil.
- **Seuils recalibrés** (conception §6) : grille 4×4 à ×1 (sinon cible déjà atteinte, 3 paires) ; hauteur ±20 % ou ±15 cm. Le reste inchangé.
- **Fleurs et fruits : forcés dans la fabrique** (`floraison` 1, fruits mûrs sur les 4 `fruitier`, patron `verger_floraison`). Banc court sans forçage : 3 espèces sur 40 en fleur et 0 fruit en 8 semaines depuis s20 [n=1 run, VM] ; depuis s1, chaque espèce fleurit à sa date sur 30 semaines, jamais ensemble, et 2 fruitières sur 4 nouent [n=1 run, VM].
- **Capture à `-w 0` obligatoire** : le banc est un état posé. Si on lance la saison, 38 pieds sur 40 sont morts en s26, surtout par herbivorie [départ s20, n=1 run, VM], microbiome 0,6 ou 0,7. Depuis s1, 4 morts sur 30 semaines [n=1 run, VM]. Non diagnostiqué, ressemble à D64 et à la mortalité de `foret_ports` (D127) ; aucune correction ici.
- **Écarts au kickoff** : squelette posé par `grow_plant` sur 52 semaines (`_adulte` seul laisse 1 segment aux non procédurales : `pre_croitre` n'agit pas sur elles) ; lierre et jasmin à 3 ans. Ortie et lupuline (`minette`) sont déjà parmi les 36 : la liste reste à 36.
- **Pour les suivants** : point visé reculé d'une demi-hauteur (`centre_de`), la plante entière tient au cadre à ×4 jusqu'à 300 cm. Un dossier partiel se mesure (`--especes` à la capture), en supprimant `descripteurs_x*.json` pour recalculer. Espèces qui tiennent mal : début des fiches (ail, pissenlit, minette, consoude, bambou). Fruits sans état moteur à trancher : poivron, bourse-à-pasteur.
- **F5** : rien à valider pour ce tronçon, banc de mesure.

### ② Socle, taille, rosettes

- **Fait** : `visuals/PlantRenderer.Ports.cs` (dispatch, mesure, boîte, lissage, recuisson, fruits, clic), `PortsFiches.cs` (table + 14 palettes manquantes, dont lierre et jasmin), `PortRosette.cs`, `PortTetes.cs`. Moteur : `semaine_coupe`, `semaine_pince` sur `PlantInstance`, `tools/simserver/taille_pont.py`, pont **0.6.7**, test `test_hints_taille`. Golden intact `a10b7225…`, `test_sim_server` 321/321, build vert. Aucune sérialisation de `PlantInstance` à part le snapshot (pas de save à casser).
- **Mesure** : les 7 rosettes dans aucune paire confondue et dans la tolérance de hauteur, ×1 et ×4 [seed 42, n=1 capture, VM]. Paires : ×4 28→15, ×1 14→7 [mêmes conditions, 33 espèces encore génériques] ; hauteur hors tolérance ×4 30→23 [idem]. PNG lus : les 7 se reconnaissent à ×4 et ×8.
- **Effet en jeu** : `full` s26 et s46, ×1 à ×16 : pissenlit et bourse lisibles, plus de 88 cm de bois [seed 42, n=1 run, VM]. Molène, mâche, carotte, ail absents de `full` à ces semaines : vus sur le banc seul. Hampe du pissenlit non vue dans `full`, sa floraison y reste sous le seuil à ces dates.
- **Saut de hauteur** : visible, lissage retenu (⅙ de la cible par semaine, 2 cm minimum). Molène 20→150, seigle 40→140, chanvre 80→250, tournesol 50→180 cm d'un stade à l'autre [catalogue, gènes neutres]. Lissage non capturé en jeu : le banc pose une seule semaine.
- **Perf** (`perf_vm.sh -E 20 -z 4`, `full`) : draw calls 92→83 [n=1 run par côté, VM]. Cache 93,4→77,4 Mo, pages 5→4 [idem]. FPS 11,1→10,3 et 11,6 [n=1 run avant, 2 après, charge 2 à 6, dans le bruit]. **Garde-fou non tenu** : pinceau 0,12→0,19 ms/plante, soit +58 % contre +10 % visés [n=1 run par côté, charge variable], malgré des ellipses à 12 côtés (0,20 sans). Coût par espèce non isolé. À revoir à ③, le poids des rosettes y est le moyen de trancher, ou à Nico d'assouplir le seuil.
- **Recuisson** : `SetStructure` ne salit plus un port si sa clé (hauteur au cm, stade, densité, floraison, automne, hints, fruits, organe) est inchangée, prairie comprise ; `SetSymptoms` sort si la liste est identique. Écrit, compilé, **gain non chiffré** : le banc E applique 0 semaine.
- **`mesure_da`** sur pissenlit, molène à ×4 : tons lus méd. 10 et 8, dérive 51° et 38°, aplat 111 et 68 px [n=1 capture, VM]. Hors grammaire du brief (cible 3-6 tons) : la grammaire reste au ⑥.
- **Écarts au kickoff** : fruits sur port écrits (`PointFruitPort`, `FindFruitNear`) mais **jamais exécutés** : aucune rosette n'est `fruitier`, à vérifier au ④ sur fraisier, courgette, framboisier. Taille non capturée, couverte par le test simserver : l'effet visible de `rabattu` et `pince` reste au F5. Hiver : les 7 ne sont pas `deciduous`, donc le moteur les garde pleines ; pissenlit s46 vérifié en capture, cohérent pour une rosette. **Pour ③ et ④ : consoude, ortie, menthe restent aussi pleines l'hiver, faute de signal moteur.** Clic : `FindPortSous` ajouté, le haut d'une hampe tombait hors de `PickRadiusCm`. Bourse : silicules et tête en graine dessinées comme marques de stade, sans état moteur. `serialize.py` à 400 LDC pile (un import remis sur une ligne pour compenser).
- **Pour les suivants** : ajouter une ligne à `FichesPort` et un `case` dans `DessinerPort` ; la taille au pied, l'ombre, le vent et la recuisson suivent seuls. `BakeCost` compte encore les segments : à revoir au ⑤, où ils disparaissent. Espèces non encore à port : gardent le segment et une palette nouvelle dès ce tronçon.
- **F5** : rosettes en jeu (reconnaissance, hampe qui monte) ; tailler et pincer un pied (se rabat, perd sa tête, repousse) ; clic sur une hampe de molène ; plus de surlignage de segment sur prairie et rosettes.

### ③ Tiges à feuilles étagées

- **Fait** : `visuals/PlantRenderer.PortTige.cs` (collecte axes, rameaux, feuilles ; ordre du peintre), `PortTigeFormes.cs` (losange loin, palmée, gaufrage, soleil, étoile, grappe pendante), 12 lignes `FichesPort` et `FicheTige`, `tools/cout_cuisson.py`. Vue pure, aucune fonction par espèce : tournesol = 1 axe sans rameau, moutarde = 1 axe à 9 rameaux. Golden intact `a10b7225…`, build vert. Moteur non touché. `Mugwort`, `Hemp`, `Mint` : palettes assombries (fiche : colonne sombre, flèche sombre, plaque terne).
- **Silhouettes** : paires ×4 15→3, ×1 7→1 [seed 42, n=1 capture, VM] ; aucune des 12 dans une paire, menthe/basilic séparés ; restent bambou, pâturin, seigle, haricot, myrtille, thym (④⑥). Hauteur hors tolérance ×4 23→15 [idem], ×1 : 16 sur 40 [idem]. Dans les 12 : consoude 78 cm dessinés pour 50 [×4, n=1 capture] assumée (la boîte compte sa nappe de 32 cm, masse plus large que haute, fiche) ; à ×1 seuls moutarde 77 pour 60 et poivron 97 pour 80 dépassent de 1 à 2 cm [n=1 capture], arrondi au pixel.
- **PNG lus** : banc ×1, ×4, ×8 ; `full` s26 et s46, ×1 à ×16 [seed 42, n=1 run, VM] : tournesol et poivron lisibles, plus de 88 cm de bois partout. Les autres tiges ne sont vues que sur le banc à ces dates et à ce cadrage.
- **Garde-fou de cuisson : NON TENU, hors d'atteinte sans perdre les silhouettes. À arbitrer par Nico, seuil non touché.** `full`, `perf_vm.sh -E 20 -z 4`, A/B au même build : pinceau 0,11-0,12 → 0,17-0,21 ms/plante [n=3 runs par côté en alternance, charge de départ 1,8 à 4,9, le premier à 1,8, avant les derniers réglages de rayons de 3 fiches], soit environ +60 % contre +10 % visés. Sans les allègements de ce tronçon : 0,23-0,26 [n=3].
- **Pourquoi** : c'est un effet de mélange, pas de port lourd. Une petite plante à segments coûte 0,04 ms en médiane [`full`, n=3 runs, VM], un port du même âge 0,11 (tournesol, 84 sommets) à 0,19 (basilic, poivron) [`full`, n=3 runs, VM] : l'envoi seul du lot en prend 0,04 à 0,06 [n=1 run, VM]. À l'adulte, c'est l'inverse : médiane des 12 tiges 0,90 → 0,62 ms, des 7 rosettes 0,50 → 0,35 ms contre 0,84-0,92 pour les 13 génériques [banc, ×4, n=6 à 16 coups par espèce, à froid, 1 passe par côté].
- **Allégé** (silhouettes conservées, PNG lus) : `LotTriangles.DessinerSansMaille` (triangle array, ports et prairie, sans ArrayMesh, env. −0,05 ms par coup [n=3 contre n=2 runs, `full`]) ; disques et ellipses à 4 ou 6 côtés sous 4 px ; ombre de feuille et plume complète dès ×8 seulement. Effet visible à ×4 : rosettes un peu moins séparées par l'ombre, à juger au F5.
- **Le reste de la perf ne se dégrade pas** : FPS 9,4-11,0 → 11,1-11,4 [n=3 par côté, dans le bruit], draw calls 92-96 → 87-90 [n=3 par côté], `cache` non comparable (ligne lue en début de run). Options pour Nico : assouplir le seuil, le rapporter à l'adulte, ou le mesurer en durée totale de cuisson ; repli possible : garder les segments sous un stade.
- **`mesure_da`** ×4 : tournesol, ortie, chanvre : tons lus méd. 3, 6, 3 ; noir 0 % ; dérive 15°, 34°, 16° [n=1 capture, VM]. Grammaire au ⑥.
- **Écarts au kickoff** : `cout_cuisson.py` et la trace `SYMBIOSE_COUT_CUISSON` ajoutés pour isoler le coût. Formes neuves : cœur, scie, palmée ; lancéolée reprise du plantain. Poivron : moteur non `fruitier`, donc organe `fruit` montré par une **marque de stade** ronde et rouge, sans état ni récolte. Tête de tournesol fanée idem. **Hiver : les 12 ne sont pas `deciduous`, le tournesol reste feuillu en s46** [`full`, n=1 run], faute de signal moteur. Clic : la bande de tige vaut pour toute tige.
- **Pour les suivants** : `PoserEllipse`, `PoserDisque` s'allègent seuls ; `DessinerSansMaille` pour tout lot de pinceau. `tools/cout_cuisson.py --zoom 4` donne le coût par espèce. Lire le A/B au même build : charge variable sinon.
- **F5** : reconnaître les 12 en jeu ; vent sur chanvre et tournesol (feuilles attachées à l'axe plié) ; tailler et pincer basilic et ortie ; clic sur une tige de chanvre ; pieds morts ; rosettes à ×4 sans ombre de feuille.

## §REPRISE

Lire `CLAUDE.md`, ce fichier, la conception, puis le prochain kickoff « à faire » : ④ `04_chaumes_tapis_buissons.md`. Patron d'un port : `visuals/PlantRenderer.PortTige.cs`. Rejouer la mesure : `mesures/avant.md`. Point ouvert : **seuil de durée de cuisson à arbitrer par Nico** (bilan ③).
