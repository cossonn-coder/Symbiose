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
| ③ | `03_tiges.md` | Tiges à feuilles étagées (12) | à faire |
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

## §REPRISE

Lire `CLAUDE.md`, ce fichier, la conception, puis le prochain kickoff « à faire » : ③ `03_tiges.md`. Patron d'un port : `visuals/PlantRenderer.PortRosette.cs`. Rejouer la mesure : `mesures/avant.md`. Point ouvert : durée de cuisson (bilan ②).
