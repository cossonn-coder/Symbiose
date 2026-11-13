# Sprint GESTES LISIBLES — état

> Conception figée le 2026-11-13 : `docs/joueur/gestes/conception_gestes_lisibles.md`
> (à lire en entier). Reprend **D136 (a)-(f)**. Hors sprint : (g) structures en volume,
> (h) paysage (après la rivière), outils à trouver/fabriquer (`sprint_outils_atelier`),
> automate à intentions (`sprint_automate_intention`), devenir des fruits (D137), autres
> états du sol (D108).

## But
L'outil bouge (curseur, images précuites), le jardin se souvient (sol-canvas : traces de
gestes + pluie + sécheresse), les messages parlent en mots, aucun geste n'est incompris,
et l'automate joue un plan de test sous nos yeux.

## Décisions clés (Nico, 2026-11-13)
- D1 Curseur = l'outil qui agit, images précuites qui décomposent le geste ; monde = la
  conséquence. D2/D8 Sol = canvas (gestes + événements), ce sprint pose le canvas + traces
  de gestes + pluie + sécheresse ; D108 remplira le reste.
- D3 Registre `traces_sol` côté MOTEUR (état joueur, hors tick) : **la vue n'invente rien**.
- D5 Quantités rééquilibrées **à l'excès** pour tester ; aucun chiffre dans les messages.
- Q8 **On ne touche à rien des outils** (arrosoir, sécateur, Atelier) avant leur sprint ;
  `arroser` reste de base.
- D7/D10 Automate : actif fenêtre fermée + mode testeur (plan `(verbe, cible)` déroulé
  par le chemin du clic joueur). L'« âme » de l'automate = sprint à part.
- Décidé seul, à confirmer au F5 : déraciné = cadavre `couchee` au moteur ; volants
  épargnés par `ecraser` via un attribut `vole` ; gestes de l'automate joués en sprite
  monde avec les images du curseur.

## Golden
**INTACT sur tout le sprint** (`b4a921f8…`, `data/code/tests/golden_hash.txt`). Aucun
re-figeage prévu : un rééquilibrage qui le bougerait passe par une constante côté geste.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_moteur_pont.md` — traces, volants, couché, pot, mots, rééquilibrage, pont 0.6.14 | **FAIT** (golden intact) |
| ② | `02_animations_curseur.md` — images précuites, rotation, icônes inversées | **FAIT** (golden intact, build vert, planche regardée) |
| ③ | `03_sol_canvas.md` — couche de traces, paillis, cuvette, pile, pluie, craquelé | **FAIT** (golden intact, build vert, captures regardées) |
| ④ | `04_objet_en_main_ergonomie.md` — objet en main, coccinelle, catalogue, fruit | à faire |
| ⑤ | `05_automate.md` — actif fenêtre fermée, gestes visibles, mode testeur | à faire (après ②) |
| ⑥ | `06_banc_recette.md` — banc `gestes_lisibles`, oracle, recette F5, clôture | à faire (après tous) |

## Interdits communs
Jamais `tests/test_epaisseur_500ans` ; pas de `ps aux` / `pgrep -f` ; GDScript interdit ;
aucune couleur brute (`Palette16`) ; ne supprimer aucun code ; > 300 LDC → scinder
(`tools/compte_ldc.py`) ; `WorldView.cs` est à 300 LDC, n'y rien ajouter ; regarder les
PNG de capture avant de conclure un tronçon de vue.

## Constats d'exécution
### ① moteur + pont (2026-11-13)
- **Clés de pont 0.6.14** (optionnelles côté vue, tout au snapshot) :
  `traces_sol` = `{tuile: [[r, c, x_cm, y_cm, sorte, age], …]}` (tuiles marquées seules ;
  x/y **tuile-locaux** = point cliqué, sinon centre du plot ; `age` en semaines) ;
  `sol_sec` = `{tuile: [[r, c, humidite], …]}` (toutes les tuiles, plots sous **0.5** = seuil
  où naît le `drought_stress` moteur ; l'hystérésis reste à la vue) ;
  `volants` = liste triée des clés d'espèce qui volent (5 pollinisateurs + merle, geai,
  rapace, moustique, libellule). Registre moteur `sim/traces_sol.py` (table
  `DUREE_SEMAINES`, `PLAFOND_TRACES = 400`) ; écriture à la route (`cmd_action`, après
  `applied`) via `tools/simserver/sol_canvas_pont.py` — signatures `sim/actions` intactes.
- **Règles** : `TrophicSpec.vole` (donnée, jamais lue au tick) ; `ecraser` d'un volant
  refusé en amont (façade + pont, « ça s'envole… », coût 0). `deraciner` → `couchee`
  (décompo/lumière/perchoir/C# gèrent déjà `couchee`). **Bug du pot : côté PONT** — le pont
  acceptait toute coordonnée (pot posé en (-800, 5000) appliqué) ; refus hors `[0, MONDE_CM]²`
  pour `poser_pot`/`poser_bac_culture`/`deplacer_pot`. À revoir au ④ si la vue envoie
  encore une mauvaise coordonnée (le refus le dira).
- **Mots** : `tools/simserver/mots.py` (`quantite_en_mots` en doses de `PAILLAGE_DOSE`,
  `vigueur_en_mots`). Aucune phrase de geste APPLIQUÉ ne porte de chiffre (coordonnées,
  `#idx`, numéro de segment, %, cm compris) ; seuls des refus de désignation (erreurs de
  protocole) en gardent.
- **Mesure** `mesures/mesure_quantites.py` (seed 42, full) AVANT → APRÈS :
  glaner plot médian fin d'été 1,07 → **2,13 doses** (printemps 0,14 → 0,27 [13 plots
  seulement ont de la litière tendre]) via `GLANAGE_RENDEMENT = 2.0` (geste) ;
  compost : bac plein après une saison `compost_mur` 9,7, un épandage `om_stable` 0,15 →
  5,97 → **déjà franc, inchangé** ; miel d'une ruche printanière après une saison
  0,05 → **4,6** (Vigueur sans équipement 0,04 → **8,4**) via `MIEL_RATE` 0,30 → 30
  (**constante lue au tick**, golden identique : aucune ruche au smoke) +
  `MIEL_VIGUEUR_RATIO` 3 → 6 (geste).
- **Écarts au kickoff** : `MIEL_RATE` est au tick (le miel venait du nectar LOCAL au
  plot, ~0,05 : aucune constante côté geste ne pouvait le rendre visible dans la ruche) ;
  `serialize.py` passe de 405 à **409 LDC** (déjà > 400 avant, 4 lignes d'appel) — à
  scinder au `/refactor` de fin de sprint. Pour ⑤ : l'automate (`tools/jardinier_auto/
  execution.py`) appelle les façades directement → il n'écrit PAS de traces ; à câbler
  au ⑤ (`ecrire_trace`, `eco.tile_id`, `plant.position`). Tests adaptés : `test_alarme`
  (abeille refusée ; déterminisme par le miel nu), `test_ravitaillement_mulch` (×
  rendement), suite pont (version, pot déplacé à 1900 au lieu de 2500, segment sans
  numéro, déraciné `couchee`). Test neuf : `tests/test_gestes_lisibles.py` (34 checks).

### ② animations du curseur (2026-11-13)
- **Moteur d'images** : `visuals/EtapeGeste.cs` (81 LDC) — une image = `Etape` (grille
  dessinée OU icône ; rotation autour d'un pivot, angle + = horaire ; décalage ; effets aux
  coordonnées ABSOLUES, derrière le dessin sauf `.Dessus()`, où '.' efface). Fabriques
  `T`/`R`/`D`, patron partagé `Poser(bas)`, `Puis(...)`. **Rotation échantillonnée 4×4 à vote
  majoritaire** (`K` pèse 1,5) : le voisin le plus proche simple dédoublait les contours
  (vu à la planche) ; à `K`×2 tout noircissait.
- **Suites** : 46/46 gestes, 4 à 6 images, un fichier par famille `visuals/icones/Anims*.cs`
  (registre `AnimationGeste.Suites`). Grilles dessinées : coccinelle mi-ouverte/ouverte,
  sécateur ouvert, main ouverte sur la touffe, trogne nue. Les recettes par mouvement
  (`IconesMouvements.cs`) restent le REPLI d'un geste sans suite (aucun aujourd'hui).
- **Icônes** : `tailler` = sécateur, `couper` = scie (grilles + points chauds échangés) ;
  `pincer` redessiné (main gantée entière, pouce + index sur le bourgeon) ; `glaner`
  redessiné (main d'en haut, manchette, feuille pincée au-dessus d'un tas de feuilles).
- **Refus** : ±2 px de grille, 3 images (−2, +2, −2).
- **API monde (pour ⑤)** : `AnimationGeste.TexturesMonde(string verbe, int echelle) →
  Texture2D[]` (images d'exécution, même cache que le curseur — ne pas les libérer ;
  null sans icône). Durée d'une image : `AnimationGeste.DureeImageMs` (80 ms).
- **Vérification** : `IconeGeste.Defauts` exige une suite par grille ; `DefautsSuites`
  contrôle 4-6 images, grilles 16×16 dans l'alphabet (`IconeGeste.Valide`), effets dans la
  grille. Journal au banc : `[Icones] 45 gestes vérifiés, 0 défaut(s).`
- **Planche** (`tools/capture_vm.sh -W -n 4`) : `PlancheAnimations.cs` réécrite — tous les
  gestes + refus + tap, pages ALTERNÉES ×4 (frames 1/3) et ×2 (frames 0/2). Finales :
  `planche/planche_02_animations_x4.png`, `planche/planche_02_animations_x2.png`.
- **Écarts** : `grelinette`, `retourner`, `pailler` ont perdu leur rotation (outils ajourés
  ou paille : brouillés même au vote) → décalages + mottes/brins ; `retourner` montre une
  motte qui se RETOURNE (herbe dessus → dessous). `arroser` doit pencher jusqu'à 55° (l'icône
  est déjà inclinée ~30°) et descend de 5 px vers la cible.
- **Encore faibles à la planche (F5)** : `glaner` et `pincer` (icônes mieux mais encore
  chargées à ×2) ; `arroser` penché un peu « bouilli » ; effets d'un pixel peu visibles à ×2
  (rejets d'`eteter`, reflets de `drainer`/`deriver`, vapeur de `composter`, miel) ; tous les
  `poser_*` partagent la même chute ; `palisser` (pelote qui tourne) reste une balle.
- Aucun fichier de `world/` touché (`WorldView.cs` toujours à 300 LDC) ; déclenchement inchangé.

### ③ sol-canvas (2026-11-13)
- **Clés lues** : `traces_sol`, `sol_sec`, `paillage`, `structures`, `weather` — conformes au ① (vérifié
  au code). Branché par `world/WorldView.SolCanvas.cs` (couches créées au 1er snapshot, remises à zéro
  à un nouveau monde) + 1 ligne dans `WorldView.Snapshot.cs` (295 LDC). `WorldView.cs` intact (300).
- **Traces** : `visuals/TracesSolLayer.cs` (un nœud + un LotTriangles par tuile, redessiné seulement si
  la signature de la tuile change : contenu + relief des plots marqués ; pivot/palier ×1) +
  `visuals/TracesSolMotifs.cs` (bêche = mottes sur terre sombre, grelinette = raies claires, pas = botte
  au point cliqué, épandre = voile de compost, arroser = auréole, creuser = couronne de mottes).
  Estompage : −0,16 d'opacité/semaine, plancher 0,25 ; la vue ignore la durée de vie (le moteur purge).
  Sous le paillis (même ZIndex 1, ordre d'enfant avant `Mulch`).
- **Craquelé** : même couche ; apparaît sous **0,35**, s'efface quand le plot quitte `sol_sec` (0,5).
- **Paillis** : `MulchLayer.cs` réécrit + `visuals/MulchMotifs.cs` — losange plein du plot (opacité ∝
  profondeur), paille en brins, BRF en copeaux, aiguilles en traits, feuilles en taches ; posé sur le
  relief ; chute de brins 0,9 s quand la profondeur d'un plot monte entre deux snapshots. Teintes
  rangées dans `Palette16` (hex inchangés) + bloc sol-canvas (entrées de la palette maître).
- **Cuvette** : le creux EST le relief (altitude −15 cm → marche de ~3 px à ×1) ; rien d'ajouté. Sur un
  plot déjà à altitude 0 le moteur borne à 0 → pas de creux (le banc vise des plots hauts).
- **Couché** : NE se couchait pas (écrasement ×0,18 = moignon debout) → `PlantRenderer.Iso` bascule
  l'axe vertical au sol (direction par hash d'individu), `CoucheeFlatten` = 1, ombre réduite ; l'état
  est copié au pinceau de cuisson (`Bake.cs`, sinon l'image cuite restait debout).
- **Tas** : la quantité était déjà exportée (`contenu`, `compost_mur`) → pas de pont touché. Bac =
  surface de compost à hauteur ∝ masse ; pile = 1 à 10 rondins en pyramide.
- **Pluie** : `visuals/EclaboussuresLayer.cs`, ≤ 90 gouttes ∝ `MeteoPlantes.Pluie`, un lot, dort hors pluie.
- **Banc** `sol_canvas` (`data/code/bancs/sol_canvas.py`, + post-init) : gestes joués par leurs façades,
  traces antidatées. Capture : `tools/capture_vm.sh -b sol_canvas -w 0 -z 2 -c 1650,1550`
  (`-m "Orage,2.0,60"` pour la pluie). Planches : `planche/planche_03_*.png`.
- **Perf** : FPS non mesuré (`perf_vm.sh` pas lancé) ; coût par construction = 1 envoi par tuile marquée,
  1 pour le paillis, 1 pour la pluie.
- **Encore faibles (F5)** : cuvette peu lisible (marche de relief seule) ; empreintes de botte petites à
  ×2 ; ombre-ellipse encore large sous le gisant (étalement inchangé) ; l'info-bulle d'un mort dit
  « feuillage ferme » (pré-existant, hors ③).

## §REPRISE
① FAIT et commité (`52d2c02`) ; ② commité (`40110a7`) ; ③ FAIT, non commité (golden `b4a921f8…` intact).
Prochain : ④ `04_objet_en_main_ergonomie.md` ; ⑤ peut utiliser `AnimationGeste.TexturesMonde(verbe, echelle)`.
