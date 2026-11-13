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
| ④ | `04_objet_en_main_ergonomie.md` — objet en main, coccinelle, catalogue, fruit | **FAIT** (golden intact, build vert, pont 0.6.15, captures regardées) |
| ⑤ | `05_automate.md` — actif fenêtre fermée, gestes visibles, mode testeur | **FAIT** (golden intact, build vert, pont 0.6.16, captures regardées) |
| ⑥ | `06_banc_recette.md` — banc `gestes_lisibles`, oracle, recette F5, clôture | **FAIT** (golden intact, build vert, oracle 26/26, captures regardées) |

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

### ④ objet en main et ergonomie (2026-11-13)
- **Pont 0.6.15** : clé `habitats_auxiliaires` = `{tuile: [[slot_id, n], …]}` (tiges portant des
  rondelles `auxiliaire`, toutes tuiles) — `sol_canvas_pont.habitats_auxiliaires`, lecture pure ;
  `serialize.py` reste à 409 LDC (même ligne). Tests : version 0.6.15 (4 suites pont) + 2 checks
  dans `test_gestes_lisibles` (36/36) ; `test_sim_server` 349/349.
- **Deux temps** sortis de `ActionDispatch` (394 → 283 LDC) vers `world/WorldView.DeuxTemps.cs` :
  phrases sans numéro (« pelletée prise », « pot soulevé », « bouture prélevée », « greffon
  prélevé ») ; un 2e clic hors cible REFUSE en gardant l'objet ; le pot ne se pose que sur une
  tuile (comme `poser_pot`). HUD : « pot #N saisi » → « pot soulevé ».
- **Objet en main** (`world/WorldView.ObjetEnMain.cs`, grilles `visuals/icones/ObjetsEnMain.cs`) :
  bouture / greffon / pelletée = image ×2 portée en bas à droite de la pointe (calque 110) ; le
  POT lui-même (et ses plantes) suit la souris au sol. Cibles : `visuals/ZoneCible.cs` éclaire les
  plots de la tuile source (bouturer, épandre, greffer). Hors cible : silhouette d'une teinte
  (pot à demi transparent). Échap (en tête de la chaîne) et clic droit reposent l'objet.
- **Écart** : `composter` est à UN clic (la litière cliquée part au bac le plus proche de la
  tuile) → aucun temps où l'on « tient » la brassée, pas d'objet en main ; ordre inchangé.
- **Habitat** : `visuals/HabitatAuxiliaire.cs` + `world/WorldView.Habitats.cs` — une tige rouge
  pointée de noir, 1 à 3 rondelles (nombre moteur). Placement = CONVENTION vue : `slot_id`
  0..9 réparti le long du bord nord de la tuile (la rondelle est au niveau tuile, sans plot).
- **Volants** : `volants` lu (SolCanvas) ; `MacroLife.SpeciesNear/Near` prennent des espèces
  exclues → sous `ecraser`, un volant n'est pas désigné (le clic retombe sur le plot, défaut
  serveur). Pas de surlignage propre à `ecraser` à éteindre. `MacroLife.cs` 314 → 315 LDC.
- **Catalogue** : trié sur le nom affiché (clé sans soulignés, accents ignorés) — il l'était déjà
  par clé ordinale, sans accent au catalogue actuel ; ouvert à l'armement de `planter` /
  `planter_conteneur`, il se referme au choix sur la graine choisie (un clic la rouvre).
- **`planter_conteneur`** était déjà à un clic : la réduction faite = `planter` armé + clic sur un
  pot (rayon 30 cm) y sème la graine choisie (verbe envoyé `planter_conteneur`). Le geste
  `planter (pot)` reste en palette (rien jeté).
- **Récolter** (`world/WorldView.Recolte.cs`, `visuals/PlantRenderer.FruitMur.cs`) : fruit MÛR
  (maturité moteur ≥ 1) dessiné sous le clic → récolte ; clic sur une plante qui porte des
  fruits mais pas sur un mûr → refus en mots (« visez un fruit mûr, pas la plante » / « ses
  fruits ne sont pas encore mûrs »). **Décidé seul, à confirmer au F5** : une plante SANS
  fruit au snapshot (lavande, salade, trèfle à quatre feuilles) se récolte entière comme avant
  — sinon le trèfle à quatre feuilles deviendrait incueillable.
- **Pot hors du jardin** : ① a conclu « côté pont » ; côté vue, le 2e clic exige une tuile.
- **Banc** `objet_en_main` (`data/code/bancs/objet_en_main.py`) + `-E VERBE[@X,Y]` au banc VM
  (`world/WorldView.BancObjetEnMain.cs`). Verdicts : récolte fruit mûr → « récolté : Pommier »,
  collet et fruit vert → refus en mots ; catalogue 6 graines → 1 pastille après choix ; `planter`
  sur le pot → « … planté dans le pot ». Captures regardées : bouturer (zone éclairée), pot qui
  suit (posé / grisé hors tuile), épandre, greffer grisé, catalogue, habitat ×2 et ×4.
  `tools/capture_vm.sh -b objet_en_main -w 0 -z 2 -c 1650,1650 -E bouturer@1475,1475 -s 1000,560 -n 80`.
- **Points F5** : lisibilité des objets ×2 (pelletée petite et sombre, bouture fine) ; voile de
  zone discret sur terre claire ; habitat (tige + rondelles) lu comme un hôtel à insectes ?
  objet en main décalé d'une image (sprite du jeu, pas curseur OS) ; pot porté dessiné sur la
  pointe ; une graine dont le lot se vide fait glisser le choix sur la suivante (pré-existant,
  index) ; volants non testés à l'image (aucun volant à portée au banc) ; repli « plante entière »
  de `recolter`.

### ⑤ automate (2026-11-13)
- **Traces de l'automate (note du ①) : traitées.** `jardinier_auto/execution.executer` enveloppe
  l'ancien corps (`_jouer`) et écrit la trace (`ecrire_trace`, `eco.tile_id`) d'un geste qui a porté
  et qui marque le sol ; `point_vise(plant, plan)` = position continue de la plante touchée
  (`cible_obj` pour broyer/recolter_paille/deraciner/tailler), centre du plot d'un `planter` créatif,
  None sinon. Logique de décision intacte.
- **Pont 0.6.16** : les lignes `geste` du journal gagnent `point` = [x_cm, y_cm] TUILE-LOCAL ou null
  (`trace.entree(..., point=)`) ; commande `plan_test {banc}` → `plan` = [{verbe, geste, maj, cible,
  clics}] (lecture, `automate_cmd.cmd_plan_test`). 4 suites pont passées à 0.6.16.
- **Format du plan de test** : `bancs/plan_test.py` — un banc déclare `PLAN_TEST = ((verbe, cible[,
  cible2]), …)`, inscrit dans `bancs.BANC_PLAN_TEST` ; cibles `plot(tuile, r, c)`, `plante(clé
  catalogue[, tuile])` (1ʳᵉ vivante), `structure(tuile, kind)`, résolues à la demande en points MONDE ;
  deux cibles = geste à deux temps ; `_PALETTE` mappe `grelinette` → case `becher` + Maj. Seul
  `sol_canvas` a un plan (bêcher, arroser, épandre bac→plot, écraser, rangée 2).
- **Vue** : touche **A** = seul interrupteur (fermer l'onglet le laisse tourner ; onglet fermé, la sim
  suit phase/pause habituelles). `world/WorldView.AutomateGestes.cs` : gestes du DERNIER tick
  (résultat ≠ échec, point non nul) joués en `visuals/GesteMonde.cs` (Sprite2D dans `Objects`,
  `TexturesMonde(verbe, 1)`, point chaud sur le point, 2 passages + tenue 0,35 s), ≤ 6 vivants, départs
  espacés de 0,45 s ; témoin = icône du dernier geste ×2 en haut à droite, visible si branché ; journal
  `[Automate] semaine N : k geste(s)…`. **Touche B** = mode testeur (`world/WorldView.Testeur.cs`) :
  geste armé, souris posée sur la cible, `TryAction` (même chemin qu'un clic), un geste / 3 s
  (1 s entre deux clics), verdict lu sur la réponse (`_verdictGeste`, posé par
  `JouerAnimationCurseur`) ou refus de la vue ; rapport `[Testeur]` + onglet Automate (présent aussi
  automate débranché quand un rapport existe, ouvert en fin de plan). Aide F1 mise à jour.
- **Capture** : `tools/capture_vm.sh -b sol_canvas -w 0 -z 2 -c 1650,1550 -R -n 230` (4/4 appliqués,
  traces nées sur la rangée 2, rapport à l'image) ; nouvelle option `-U ouvert|ferme` (automate branché
  au montage) : `-b full -w 2 -z 2 -c 1000,1300 -U ferme -T 6 -n 120` (sécateurs joués au pied des
  plantes taillées, témoin visible).
- Tests : `tests/test_automate_visible.py` (10/10, neuf) ; automate ×6 verts ; `test_gestes_lisibles`
  36/36 ; `test_sim_server` 349/349. `SimBridge.cs` 348 → 349 LDC (déjà en vigilance, +1 méthode).
- **Points F5** : taille des outils au monde (16 px de grille à ×1 de caméra) et durée (≈ 1 s) ; lisible
  en Turbo ? témoin discret assez visible ? le testeur déplace la souris du joueur (voulu, à confirmer) ;
  gestes sans icône ni point (achat magazine, rondelle) non joués ; un tick à > 6 gestes n'en montre que 6.

### ⑥ banc, recette, clôture (2026-11-13)
- **Banc `gestes_lisibles`** (`data/code/bancs/gestes_lisibles.py`, inscrit dans `BANCS`, `BANC_POST_INIT`,
  `BANC_PLAN_TEST`) : tuile 10×10 au coin sud-est ; trois tournesols, deux lavandes, un pommier à fruits
  mûrs et verts, litière tendre + bois mort, bac (compost mûr), pile, ruche peuplée (miel), limaces et
  MOUSTIQUES sur deux plots, plot détrempé, coin sec, pot posé, banque de graines. Gestes gatés ouverts
  par forçage (`init_gestes_debloques().update`), paille + feuilles en stock. Plan : 25 gestes dans
  l'ordre du kickoff (écraser deux fois : la limace, puis le moustique → refus attendu).
- **`plan_test.py`** : cibles neuves `plante_en(tuile, r, c)` (le pied au plot — plusieurs pieds d'une
  espèce), `bete(tuile, r, c, espece)` (le plot + la bête que la vue y voit, pour l'oracle), `pot(i)` ;
  `_PALETTE["planter_conteneur"] = ("planter", False)` (chemin ④ : planter armé + clic sur le pot).
- **Oracle** `tests/bancs/test_gestes_lisibles.py` : **26/26** — chaque geste du plan joué au pont dans
  la forme de cible de la vue (`cible_vue`, miroir des Kinds de `WorldView.Actions.cs`) : verdict
  attendu, +1 trace exactement pour arroser/bêcher/grelinette/écraser/creuser/épandre, 0 sinon,
  aucune phrase appliquée à chiffre. Golden intact ; `test_automate_visible` 10/10,
  `test_gestes_lisibles` 36/36, `test_sim_server` 349/349.
- **Défauts trouvés et corrigés** (petits, dans le périmètre) :
  1. **Grelinette cassée depuis la vue** : Maj+clic partait SANS cible (commentaire « global »
     périmé), le pont la refusait « tuile introuvable ». `ActionDispatch` case `'a'` envoie le plot
     cliqué dans les deux cas (283 LDC, inchangé).
  2. **Écraser un volant** : la vue excluait les volants (④) → aucune `espece` → défaut pont
     `puceron` → « écrasé un puceron » sur un plot sans puceron (Vigueur dépensée pour rien, vu à la
     1ʳᵉ capture). Désormais un rampant passe d'abord, un volant seul est désigné et le pont répond
     « ça s'envole… » sans dépense. **Décidé seul, à confirmer au F5.**
  3. **Testeur et récolte** : le plan donne le pied, la vue refusait (« visez un fruit mûr ») ; le
     testeur lève la visée sur le premier fruit mûr DESSINÉ de la plante
     (`PlantRenderer.IndexFruitMur`, `PointFruitCanvas`).
- **Écart** : l'**abeille** ne peut pas servir de volant au banc : les butineurs sont des agents des
  fleurs (`ForagerLayer`), pas des sprites `MacroLife` de plot — la 1ʳᵉ capture l'a montré (aucune
  désignation possible) ; le banc prend le **moustique**.
- **Capture** : `tools/capture_vm.sh -b gestes_lisibles -w 0 -z 2 -c 1700,1700 -R -n 920 -f 10` —
  24 appliqués + 1 refus attendu, rapport à l'image. Planches : `planche/planche_06_couper_x2.png`
  (sécateur au pied, info-bulle par-dessus), `planche_06_recolte_fruit_x2.png` (panier sur un fruit
  du houppier), `planche_06_traces_x2.png` (mottes, raies, cuvette, voile, paillis feuilles, pile
  grossie, couché), `planche_06_rapport_testeur_x2.png`.
- **Perf** (`perf_vm.sh -b gestes_lisibles -z 2 -c 1700,1700 -w 0`, VM llvmpipe, charge ~2) : **21,2 FPS
  [VM logicielle, n=8 relevés de 1 s]**, 84 draw calls, pire image 55 ms, 0 gel > 250 ms.
- Fichiers C# : `ActionDispatch.cs` 283, `Testeur.cs` 112, `PlantRenderer.FruitMur.cs` 35 LDC ;
  `WorldView.cs` 300 intact.

## Recette F5 (Nico)
**Lancer** : au sélecteur de monde, le banc **`gestes_lisibles`** (catégorie `gestes_lisibles`), zoom ×2 sur la
tuile du coin sud-est (devant la maison). **Appuyer sur B** : le testeur joue les 25 gestes, un toutes
les ~3 s (la souris bouge toute seule — voulu) ; le rapport s'ouvre à la fin (onglet Automate), B le
relance (sur un monde déjà touché : relancer le banc pour repartir propre).

Pour chaque geste, regarder **l'outil au curseur** (4 à 6 images), **la trace au sol**, **la phrase** :
| # | Geste | Curseur | Au monde | Phrase (sans chiffre) |
|---|---|---|---|---|
| 1 | arroser | arrosoir penché jusqu'à 55° | auréole mouillée | « arrosé au pied, la terre boit » |
| 2 | pincer | main gantée, pouce + index | tournesol (1,0) pincé | « pincé : Tournesol » |
| 3 | couper | scie | branche du pommier en moins | « branche coupée : Pommier » |
| 4 | tailler | sécateur ouvert/fermé | apex du pommier | « taillé (apex) : Pommier » |
| 5 | glaner | main + feuille pincée | litière (0,1) partie | « … une pleine charretée de feuilles » |
| 6 | drainer | bêche/rigole | plot (8,9) qui sèche | « drainé : le sol s'assèche » |
| 7 | bouturer | 2 clics : bouture EN MAIN puis plot éclairé | petite lavande en (6,3) | « bouture de Lavande mise en terre » |
| 8 | arracher | main qui saisit la touffe | tournesol (3,0) écimé | « branche arrachée à la main » |
| 9 | déraciner | traction vers le haut | tournesol (5,0) COUCHÉ au sol | « déraciné : Tournesol » |
| 10 | retourner | fourche, motte qui se retourne | bac | « compost retourné… » |
| 11 | écraser (limace) | le pied descend | botte au point, limace en moins | « écrasé un limace » ⚠ genre |
| 12 | écraser (moustique) | secousse de REFUS | rien | « ça s'envole avant que le pied ne retombe » |
| 13 | favoriser aux. | coccinelle qui ouvre les ailes | tige + rondelles au bord nord | « habitat auxiliaire posé… » |
| 14 | bêcher | bêche | mottes sombres (6,5) | « bêché, la terre est retournée » |
| 15 | grelinette | (Maj) grelinette | raies claires (6,6) | « sol ameubli à la grelinette » |
| 16 | creuser | pelle | couronne de mottes + creux (8,7) | « une cuvette se creuse… » |
| 17 | épandre | 2 clics : PELLETÉE en main, plots éclairés | voile de compost (6,7), bac vidé | « compost épandu : une pleine charretée — le tas est vide » |
| 18 | empiler bois | bûche | bois (0,5) parti, pile plus haute | « bois empilé sur la pile » |
| 19 | pailler | brassée | plot (8,4) couvert de feuilles | « le sol se couvre de feuilles » |
| 20 | composter | brassée | litière (0,3) partie, bac plus haut | « litière tendre versée au bac » |
| 21 | récolter | panier SUR un fruit mûr | — | « récolté : Pommier » |
| 22 | récolter miel | pot de miel | ruche | « miel récolté : la force revient… » |
| 23 | planter | graine | rien (graine en terre) | « graine déposée (ail)… » |
| 24 | planter (pot) | graine sur le pot | — | « ail planté dans le pot » |
| 25 | déplacer pot | 2 clics : le POT suit la souris | pot en (4,8) | « pot déplacé… » |

**À voir seulement au F5** (le banc VM ne les montre pas) :
- **Curseur OS** : l'animation joue-t-elle sur le vrai curseur (pas un sprite en retard) ? taille ×2 lisible ?
  info-bulle de la plante qui recouvre l'outil (vu à la capture, `planche_06_couper_x2.png`) ?
- **Objet en main** à la main : bouturer / épandre / déplacer pot ; Échap et clic droit reposent l'objet.
- **Catalogue** de `planter` : trié, se referme au choix ; `planter` armé + clic sur le pot.
- **Récolte au fruit** à la main : tronc → refus en mots ; fruit vert → « pas encore mûrs ». ⚠ les fruits
  récoltés RESTENT dessinés sur l'arbre (le moteur ne les retire pas : D137).
- **Écraser** : un volant seul sous le pied → « ça s'envole » (décision ⑥ à confirmer) ; les abeilles
  (butineurs des fleurs) ne sont jamais désignées.
- **Fenêtre automate fermée** : A branche l'automate, fermer l'onglet le laisse jouer, gestes en sprite
  monde au pied des plantes, témoin en haut à droite ; Turbo lisible ?
- **Pluie et sécheresse** sur le canvas : coin sec (9,0) craquelé ; lancer la saison sous la pluie →
  éclaboussures ; en sécheresse, le craquelé gagne.
- Reprendre les points F5 de ①-⑤ ci-dessus (glaner/pincer chargés à ×2, arroser « bouilli », effets d'un
  pixel, cuvette peu lisible, botte petite, objets en main petits à ×2, habitat lu comme un hôtel à insectes ?,
  repli « plante entière » de `recolter`, outils au monde 16 px, > 6 gestes par tick).
- **Limites connues** : « écrasé UN limace » (phrase sans genre, pré-existant) ; Vigueur en chiffres au HUD
  (pré-existant).

## §REPRISE
**Sprint CLOS côté code** (①→⑥, golden `b4a921f8…` intact, pont 0.6.16) ; ⑥ non commité. Prochain =
**F5 de Nico** : suivre §Recette F5 ci-dessus. `/refactor` FAIT le 2026-11-13 (`aab5c01`) :
`serialize.py` 409 → 302 LDC (cartes de sol → `cartes_sol_pont.py`), snapshot identique octet pour
octet. Restent en vigilance, non scindés : `SimBridge.cs` 349, `MacroLife.cs` 315 ; hors sprint,
`tests/test_croissance.py` 424 (dette ancienne). D136 (g)(h) et D137 restent ouverts.
